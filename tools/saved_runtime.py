"""Qualify the actual prebuilt reader and actual Scala package in a minimal root.

Host gcc/bwrap/strace/readelf/ldd are evidence tools, not consumer dependencies.
No host /usr, home, checkout, build cache, JDK or compiler SDK is mounted.
The socket-denial policy deliberately does not claim a network namespace.
"""
from __future__ import annotations
import hashlib
import fcntl
import stat
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import time

POLICY = "NF-RUNTIME-POLICY: tool-free root; descriptors=0,1,2; socket4/socket6/socketpair/io_uring/fork/vfork/clone/clone3=EPERM; no network-namespace claim\n"
ALLOWED_LIBS = {"libc.so.6", "libgcc_s.so.1", "libm.so.6", "ld-linux-x86-64.so.2"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(command, **kwargs):
    result = subprocess.run(command, capture_output=True, timeout=120, **kwargs)
    if result.returncode:
        raise ValueError(f"NF-RUNTIME-SETUP: {command[0]} failed: {result.stderr.decode(errors='replace')}")
    return result.stdout.decode()


def libraries(binary: Path):
    dynamic = execute(["readelf", "-l", "-d", str(binary)])
    interpreter = re.findall(r"Requesting program interpreter: ([^\]]+)", dynamic)
    if len(interpreter) != 1 or Path(interpreter[0]).name != "ld-linux-x86-64.so.2":
        raise ValueError("NF-RUNTIME-ELF: unreviewed interpreter")
    if re.search(r"\((?:RPATH|RUNPATH)\)", dynamic):
        raise ValueError("NF-RUNTIME-ELF: search path requires review")
    needed = re.findall(r"\(NEEDED\).*\[([^\]]+)\]", dynamic)
    if not set(needed) <= ALLOWED_LIBS:
        raise ValueError("NF-RUNTIME-ELF: unreviewed library dependency")
    linked = execute(["ldd", str(binary)])
    paths = {Path(interpreter[0])}
    for line in linked.splitlines():
        if "linux-vdso" in line:
            continue
        match = re.search(r"(?:=>\s*)?(/[^ ]+)", line)
        if not match or Path(match[1]).name not in ALLOWED_LIBS:
            raise ValueError(f"NF-RUNTIME-ELF: unreviewed ldd line {line}")
        paths.add(Path(match[1]))
    return sorted(paths), {"readelf": dynamic, "ldd": linked}


def process_identity(pid: int) -> tuple[int, str]:
    # stat comm can contain spaces/parentheses; fields after its final ')' begin
    # with state (field 3), PPid (4), and starttime (22).
    fields = (Path("/proc") / str(pid) / "stat").read_text().rpartition(")")[2].split()
    return int(fields[1]), fields[19]


def descendant_identity(pid: int, ancestor: int, ancestor_start: str) -> list[dict] | None:
    chain, seen = [], set()
    while pid > 0 and pid not in seen and len(seen) < 64:
        seen.add(pid)
        parent, start = process_identity(pid)
        chain.append({"pid": pid, "ppid": parent, "starttime": start})
        if pid == ancestor:
            return chain if start == ancestor_start else None
        pid = parent
    return None


def observe_reader(process, root: Path, prefix: Path) -> dict:
    """Read only the launched process tree while canonical stdout is blocked.

    The 4096-byte stdout pipe is not drained until a real reader snapshot is
    acquired. No ptrace, preload library or reader instrumentation is used.
    """
    expected_exe = root / "bin/nf-exchange"
    expected_maps = {"/" + p.relative_to(root).as_posix() for p in root.rglob("*")
                     if p.is_file() and "/inputs/" not in str(p) and p.name != "runtime-probe"}
    ancestor_start = process_identity(process.pid)[1]
    deadline = time.monotonic() + 10
    observed_executables = {}
    while time.monotonic() < deadline and process.poll() is None:
        # Some kernels omit task/PID/children. Read only ancestry metadata for
        # discovery, then inspect only descendants of this invocation's helper.
        children = {}
        for candidate in Path("/proc").iterdir():
            if not candidate.name.isdecimal():
                continue
            try:
                parent, _ = process_identity(int(candidate.name))
                children.setdefault(parent, []).append(int(candidate.name))
            except (FileNotFoundError, ProcessLookupError):
                continue
        pending, seen = [process.pid], set()
        while pending:
            pid = pending.pop()
            if pid in seen or len(seen) >= 64:
                continue
            seen.add(pid)
            proc = Path("/proc") / str(pid)
            try:
                pending.extend(children.get(pid, []))
                chain = descendant_identity(pid, process.pid, ancestor_start)
                if chain is None:
                    continue
                exe_path = os.readlink(proc / "exe")
                observed_executables[pid] = exe_path
                if exe_path not in {str(expected_exe), "/bin/nf-exchange"}:
                    continue
                actual_stat, expected_stat = (proc / "exe").stat(), expected_exe.stat()
                if (actual_stat.st_dev, actual_stat.st_ino) != (expected_stat.st_dev, expected_stat.st_ino):
                    raise ValueError("NF-RUNTIME-EXE: reader executable inode/device differs")
                maps = (proc / "maps").read_text()
                files = {line.split(maxsplit=5)[5] for line in maps.splitlines()
                         if len(line.split(maxsplit=5)) == 6 and line.split(maxsplit=5)[5].startswith("/")}
                normalized = {"/" + str(Path(name).relative_to(root)) if Path(name).is_relative_to(root) else name for name in files}
                if normalized != expected_maps:
                    if not normalized <= expected_maps:
                        raise ValueError("NF-RUNTIME-MAPS: unexpected file-backed mapping")
                    continue
                environment = (proc / "environ").read_bytes().split(b"\0")
                values = {value.decode() for value in environment if value}
                if values != {"PATH=/bin", "LANG=C", "PWD=/tmp", "LD_DEBUG=files"}:
                    raise ValueError("NF-RUNTIME-ENV: actual reader environment differs")
                descriptors = {p.name: os.readlink(p) for p in (proc / "fd").iterdir()}
                if set(descriptors) != {"0", "1", "2"} or any("socket:" in v for v in descriptors.values()):
                    raise ValueError("NF-RUNTIME-FD: actual reader retained unexpected descriptor")
                status = (proc / "status").read_text()
                if "NoNewPrivs:\t1" not in status or "Seccomp:\t2" not in status or "Threads:\t1" not in status:
                    raise ValueError("NF-RUNTIME-PROCESS: expected single filtered reader process")
                executable_digest = sha(proc / "exe")
                if executable_digest != sha(expected_exe):
                    raise ValueError("NF-RUNTIME-EXE: actual process executable differs")
                if descendant_identity(pid, process.pid, ancestor_start) != chain:
                    raise ValueError("NF-RUNTIME-PROCESS: process ancestry changed during observation")
                for name, text in [("maps", maps), ("status", status), ("mountinfo", (proc / "mountinfo").read_text())]:
                    prefix.with_suffix("." + name).write_text(text)
                return {"host_pid": pid, "process_ancestry": chain, "exe_path": exe_path,
                        "exe_device": actual_stat.st_dev, "exe_inode": actual_stat.st_ino,
                        "exe_sha256": executable_digest, "file_backed_maps": sorted(files),
                        "normalized_root_files": sorted(normalized), "environment": sorted(values), "descriptors": descriptors,
                        "maps_sha256": sha(prefix.with_suffix(".maps")), "status_sha256": sha(prefix.with_suffix(".status")),
                        "mountinfo_sha256": sha(prefix.with_suffix(".mountinfo")),
                        "method": "actual reader blocked on 4096-byte stdout pipe; host procfs read, then drain exact canonical bytes"}
            except (FileNotFoundError, ProcessLookupError):
                continue
            except PermissionError as exc:
                raise ValueError("NF-RUNTIME-OBSERVATION: procfs access unavailable") from exc
        time.sleep(0.002)
    prefix.with_suffix(".observation-failure.json").write_text(json.dumps({"expected_exe": str(expected_exe), "observed_executables": observed_executables}, indent=2) + "\n")
    raise ValueError("NF-RUNTIME-OBSERVATION: no complete actual reader snapshot; no observation credit")


def launch(root: Path, filter_path: Path, args: list[str], prefix: Path, trace: bool = True,
           loader_observation: bool = False, observe: bool = False):
    # subprocess closes every inherited descriptor except our explicitly passed
    # filter FD. bwrap consumes/closes that FD; runtime_probe checks before exec.
    with filter_path.open("rb") as filter_file, prefix.with_suffix(".stdout").open("wb") as out, prefix.with_suffix(".stderr").open("wb") as err:
        tracer = ["strace", "-f", "-qq", "-s", "4096", "-yy", "-e", "trace=%file,%process,%network,close,close_range", "-o", str(prefix.with_suffix(".trace"))] if trace else []
        command = tracer + ["bwrap", "--unshare-user", "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--die-with-parent", "--new-session", "--clearenv",
                   "--ro-bind", str(root), "/", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--chdir", "/tmp", "--setenv", "PATH", "/bin", "--setenv", "LANG", "C"]
        if loader_observation:
            command += ["--setenv", "LD_DEBUG", "files"]
        command += ["--seccomp", str(filter_file.fileno()), "--", "/bin/runtime-probe", *args]
        snapshot = None
        if observe:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=err,
                                       env={"PATH": "/usr/bin:/bin", "LANG": "C"}, close_fds=True,
                                       pass_fds=(filter_file.fileno(),), pipesize=4096)
            try:
                capacity = fcntl.fcntl(process.stdout.fileno(), fcntl.F_GETPIPE_SZ)
                if capacity != 4096:
                    raise ValueError("NF-RUNTIME-OBSERVATION: stdout pipe capacity differs")
                snapshot = observe_reader(process, root, prefix)
                snapshot["stdout_pipe_capacity"] = capacity
                stdout, _ = process.communicate(timeout=120)
                out.write(stdout)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if process.stdout:
                    process.stdout.close()
            code = process.returncode
        else:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                    env={"PATH": "/usr/bin:/bin", "LANG": "C"}, close_fds=True,
                                    pass_fds=(filter_file.fileno(),), timeout=120)
            code = result.returncode
    return code, command, snapshot


def reader_stderr(raw: bytes, loader_observation: bool) -> bytes:
    if loader_observation:
        lines = raw.decode().splitlines(keepends=True)
        raw = "".join(line for line in lines if line.strip() and not re.match(r"^\s*[0-9]+:", line)).encode()
    if not raw.startswith(POLICY.encode()):
        raise ValueError("NF-RUNTIME-POLICY: actual boundary probe failed")
    return raw[len(POLICY):]


def loader_records(raw: bytes, expected_libraries: set[str], files: dict) -> dict:
    text = raw.decode()
    if text.count(POLICY) != 1:
        raise ValueError("NF-RUNTIME-LOADER: missing or duplicate probe transition")
    reader = text.split(POLICY, 1)[1]
    programs = re.findall(r"(?:initialize program|transferring control): ([^\n]+)", reader)
    if programs != ["/bin/nf-exchange", "/bin/nf-exchange"]:
        raise ValueError("NF-RUNTIME-LOADER: actual reader initialization/entry not observed exactly")
    initialized = set(re.findall(r"calling init: ([^\n]+)", reader))
    if initialized != expected_libraries:
        raise ValueError(f"NF-RUNTIME-LOADER: unexpected actual initialized libraries: {initialized}")
    named = set(re.findall(r"file=([^ \n]+) \[", reader))
    if not named <= {Path(p).name for p in expected_libraries}:
        raise ValueError("NF-RUNTIME-LOADER: unexpected dynamic library request")
    return {"initialized_libraries": {name: files[name]["sha256"] for name in sorted(initialized)},
            "requested_sonames": sorted(named), "reader_entry": "/bin/nf-exchange",
            "raw_loader_stderr_sha256": hashlib.sha256(raw).hexdigest()}


def qualify(root: Path, binary: Path, scala_dir: Path, output: Path, trace: bool = True, loader_observation: bool = False) -> dict:
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("NF-RUNTIME-PLATFORM: reviewed boundary requires Linux x86_64")
    output.mkdir(parents=True, exist_ok=True)
    for name in ["gcc", "bwrap", "ldd", "readelf"] + (["strace"] if trace else []):
        if not shutil.which(name):
            raise ValueError(f"NF-RUNTIME-TOOL: missing host evidence tool {name}")
    package = json.loads((scala_dir / "package.json").read_bytes())
    writer = root / "frontend/scala/src/main/scala/nodalfpga/exchange/FixtureWriter.scala"
    if package["body"]["authoring"]["implementation_sha256"] != sha(writer):
        raise ValueError("NF-RUNTIME-AUTHORING: actual writer source identity differs")
    if package["body"]["authoring"]["id"] != "nodal-fpga/scala-fixture-writer":
        raise ValueError("NF-RUNTIME-AUTHORING: package is not actual Scala demo")
    artifact = package["body"]["architecture"]["artifact"]
    if artifact["sha256"] != sha(scala_dir / "architecture.json"):
        raise ValueError("NF-RUNTIME-ARTIFACT: actual Scala architecture digest differs")
    with tempfile.TemporaryDirectory(prefix="nf-saved-runtime-") as temporary:
        stage = Path(temporary)
        # Retain the exact copied root, including inode identity, beside logs.
        # A fresh output directory is required; never merge with stale evidence.
        minimal = output / "minimal-root"
        minimal.mkdir()
        for directory in ["bin", "inputs", "proc", "dev", "tmp"]:
            (minimal / directory).mkdir(parents=True)
        filter_tool, probe = stage / "filter-gen", stage / "runtime-probe"
        sources = {"filter": root / "tools/runtime/socket_filter.c", "probe": root / "tools/runtime/runtime_probe.c"}
        compile_commands = [["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(target)]
                            for target, source in [(filter_tool, sources["filter"]), (probe, sources["probe"])]]
        for command in compile_commands:
            execute(command)
        filter_path = stage / "socket-denial.bpf"
        filter_path.write_bytes(subprocess.check_output([str(filter_tool)]))
        from runtime_filter import verify
        verify(filter_path.read_bytes())
        shutil.copyfile(filter_path, output / "socket-denial.bpf")
        files = {}
        elf = {}
        reader_libraries = set()
        for label, source in [("nf-exchange", binary), ("runtime-probe", probe)]:
            paths, report = libraries(source)
            elf[label] = report
            if label == "nf-exchange":
                reader_libraries = {str(path) for path in paths}
            shutil.copy2(source, minimal / "bin" / label)
            for path in paths:
                destination = minimal / str(path).lstrip("/")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path.resolve(), destination)
        for name in ["architecture.json", "package.json", "design.json"]:
            shutil.copyfile(scala_dir / name, minimal / "inputs" / name)
            (minimal / "inputs" / name).chmod(0o444)
        # Preserve a syntactically valid package and corrupt its declared build ID.
        # The required negative must hit identity_mismatch before any resolver use.
        bad = json.loads((scala_dir / "package.json").read_bytes())
        bad["body"]["build_id"] = "0" * 64
        (minimal / "inputs/invalid-package.json").write_text(json.dumps(bad, separators=(",", ":")))
        (minimal / "inputs/invalid-package.json").chmod(0o444)
        for path in sorted(minimal.rglob("*")):
            if path.is_symlink():
                raise ValueError("NF-RUNTIME-ROOT: symlinks are not permitted in the copied root")
            if path.is_file():
                mode = stat.S_IMODE(path.stat().st_mode)
                if path.is_relative_to(minimal / "inputs") and mode & 0o111:
                    raise ValueError("NF-RUNTIME-ROOT: input artifact must not be executable")
                files["/" + path.relative_to(minimal).as_posix()] = {"sha256": sha(path), "bytes": path.stat().st_size,
                                                                               "mode": oct(mode), "type": "regular", "symlink": False}
        common = ["--artifact", artifact["sha256"] + "=/inputs/architecture.json"]
        cases = {
            "package-summary": ["/bin/nf-exchange", "package", "/inputs/package.json", *common, "--output", "summary"],
            "package-canonical": ["/bin/nf-exchange", "package", "/inputs/package.json", *common, "--output", "canonical"],
            "architecture-canonical": ["/bin/nf-exchange", "arch", "/inputs/architecture.json", "--output", "canonical"],
            "design-canonical": ["/bin/nf-exchange", "design", "/inputs/design.json", "--package", "/inputs/package.json", *common, "--output", "canonical"],
            "invalid-package": ["/bin/nf-exchange", "package", "/inputs/invalid-package.json", *common, "--output", "summary"],
            "x32-denied": ["--x32"],
        }
        records = {}
        for name, args in cases.items():
            prefix = output / name
            observe = loader_observation and name == "architecture-canonical"
            if observe and (scala_dir / "architecture.json").stat().st_size <= 4096:
                raise ValueError("NF-RUNTIME-OBSERVATION: canonical output must exceed 4096-byte observation pipe")
            code, command, snapshot = launch(minimal, filter_path, args, prefix, trace=trace,
                                             loader_observation=loader_observation, observe=observe)
            stdout, stderr = prefix.with_suffix(".stdout").read_bytes(), prefix.with_suffix(".stderr").read_bytes()
            if name == "x32-denied":
                if code != 159: # bwrap reports 128 + SIGSYS.
                    raise ValueError(f"NF-RUNTIME-ABI: expected SIGSYS, got {code}")
            else:
                errors = reader_stderr(stderr, loader_observation)
                if name == "invalid-package":
                    error = json.loads(errors)
                    if code == 0 or stdout or error["code"] != "identity_mismatch":
                        raise ValueError("NF-RUNTIME-NEGATIVE: wrong rejection category or published output")
                else:
                    if code != 0 or errors:
                        raise ValueError(f"NF-RUNTIME-CONSUMPTION: {name} failed: {errors!r}")
                    if name == "package-summary":
                        if json.loads(stdout)["id"] != package["body"]["build_id"]:
                            raise ValueError("NF-RUNTIME-IDENTITY: package summary differs")
                    else:
                        expected_name = name.removesuffix("-canonical") + ".json"
                        if stdout != (scala_dir / expected_name).read_bytes():
                            raise ValueError(f"NF-RUNTIME-CANONICAL: {name} differs from emitted canonical bytes")
            loader = loader_records(stderr, reader_libraries, files) if loader_observation and name != "x32-denied" else None
            records[name] = {"exit_code": code, "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                             "stderr_sha256": hashlib.sha256(stderr).hexdigest(), "trace_sha256": sha(prefix.with_suffix(".trace")) if trace else None,
                             "command": command, "reader_observation": snapshot, "loader_observation": loader}
        report = {"schema": 1, "profile": "minimal-saved-package-runtime", "network_namespace": False,
                  "observations_complete": trace or loader_observation,
                  "qualification_complete": False,
                  "observation_profile": "ptrace-syscall-trace" if trace else ("loader-procfs-process-denial" if loader_observation else "untraced-partial"),
                  "trace_observation": "syscall tracing executed" if trace else "ptrace unavailable; no complete syscall trace claim",
                  "review_required": "exact source/results require independent disposition before acceptance",
                  "network_policy": "seccomp socket-family and io_uring denial; inherited descriptors closed",
                  "process_policy": "seccomp fork/vfork/clone/clone3 denial with actual EPERM controls; outer bwrap helpers are host evidence machinery",
                  "observation_limits": "same-process replacement attempts and complete file syscalls are not enumerated by loader/procfs observation",
                  "scope": "dependency isolation demonstration, not hostile-code sandbox security", "root_files": files,
                  "root_directory": str(minimal),
                  "elf": elf, "filter_sha256": sha(filter_path), "filter_generator_sha256": sha(filter_tool),
                  "source_sha256": {name: sha(path) for name, path in sources.items()}, "launcher_sha256": sha(Path(__file__)),
                  "filter_verifier_sha256": sha(root / "tools/runtime_filter.py"), "compile_commands": compile_commands,
                  "writer_sha256": sha(writer), "cases": records,
                  "host_tools": {name: execute(command).strip() for name, command in {
                      "gcc": ["gcc", "--version"], "bwrap": ["bwrap", "--version"],
                      "readelf": ["readelf", "--version"], "ldd": ["ldd", "--version"],
                      **({"strace": ["strace", "--version"]} if trace else {})}.items()}}
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        return report
