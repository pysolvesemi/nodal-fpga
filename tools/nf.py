"""Small bootstrap commands. No HDL, architecture or CAD implementation lives here."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


class BootstrapError(RuntimeError):
    pass


def pins(root: Path = ROOT) -> dict:
    return json.loads((root / "toolchains/versions.json").read_text())


def cache() -> Path:
    path = Path(os.environ.get("NF_TOOL_CACHE", str(ROOT / ".cache/toolchains"))).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(command: list[str], cwd: Path = ROOT, env: dict | None = None) -> str:
    print("+ " + " ".join(command), flush=True)
    started = time.monotonic()
    result = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    print(f"elapsed_seconds={time.monotonic() - started:.3f}", flush=True)
    if result.returncode:
        raise BootstrapError(f"command failed ({result.returncode}): {command[0]}")
    return result.stdout


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise BootstrapError(f"NF-TOOL-MISSING: {name}; see docs/development/bootstrap.md")
    return path


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def obtain(name: str, record: dict) -> Path:
    path = cache() / name
    if path.exists() and sha256(path) == record["sha256"]:
        return path
    if path.exists():
        raise BootstrapError(f"NF-CHECKSUM-MISMATCH: remove the corrupt cached file {path}")
    if os.environ.get("NF_OFFLINE") == "1":
        raise BootstrapError(f"NF-OFFLINE-MISSING: {name}")
    temporary = path.with_suffix(path.suffix + ".partial")
    try:
        with urllib.request.urlopen(record["url"], timeout=60) as source, temporary.open("wb") as dest:
            shutil.copyfileobj(source, dest, 1024 * 1024)
        if sha256(temporary) != record["sha256"]:
            raise BootstrapError(f"NF-CHECKSUM-MISMATCH: downloaded {name}")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def java(p: dict) -> Path:
    explicit = os.environ.get("NF_JAVA_HOME")
    return Path(explicit) / "bin/java" if explicit else cache() / "jdk" / "bin/java"


def bootstrap(profile: str, p: dict) -> None:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise BootstrapError("NF-ROOT-SETUP: run bootstrap as an ordinary user")
    if profile == "rust":
        run([require_tool("rustup"), "toolchain", "install", p["rust"], "--profile", "minimal",
             "--component", "rustfmt", "--component", "clippy", "--no-self-update"])
    else:
        if platform.system() != "Linux" or platform.machine() != "x86_64":
            raise BootstrapError("NF-PLATFORM: automated JDK setup currently qualifies Linux x86_64")
        if not os.environ.get("NF_JAVA_HOME") and not java(p).exists():
            archive = obtain("temurin-jdk.tar.gz", p["jdk"])
            with tempfile.TemporaryDirectory(dir=cache()) as staging:
                with tarfile.open(archive) as package:
                    if not hasattr(tarfile, "data_filter"):
                        raise BootstrapError("NF-PYTHON: safe JDK extraction requires tarfile.data_filter")
                    package.extractall(staging, filter="data")
                directories = list(Path(staging).iterdir())
                if len(directories) != 1 or not (directories[0] / "bin/java").is_file():
                    raise BootstrapError("NF-JDK-ARCHIVE: expected one complete JDK directory")
                directories[0].replace(cache() / "jdk")
        obtain("sbt-launch.jar", p["sbt_launcher"])
    doctor(profile, p)


def doctor(profile: str, p: dict) -> None:
    if profile == "rust":
        for name in ["rustc", "cargo", "rustfmt", "clippy-driver"]:
            output = run([require_tool(name), "--version"])
            if name in {"rustc", "cargo"} and not re.search(rf"\b{re.escape(p['rust'])}\b", output):
                raise BootstrapError(f"NF-VERSION: expected {name} {p['rust']}")
    else:
        path = java(p)
        if not path.is_file():
            raise BootstrapError("NF-JDK-MISSING: run ./nf bootstrap scala or set NF_JAVA_HOME")
        output = run([str(path), "-XshowSettings:properties", "-version"])
        runtime = re.search(r"^\s*java.runtime.version = (.+)$", output, re.M)
        vendor = re.search(r"^\s*java.vendor = (.+)$", output, re.M)
        if not runtime or runtime[1].strip() != p["jdk"]["runtime"]:
            raise BootstrapError(f"NF-VERSION: expected JDK runtime {p['jdk']['runtime']}")
        if not vendor or vendor[1].strip() != p["jdk"]["vendor"]:
            raise BootstrapError(f"NF-VENDOR: expected {p['jdk']['vendor']}")
        launcher = obtain("sbt-launch.jar", p["sbt_launcher"])
        print(f"sbt_launcher_sha256={sha256(launcher)}")


def sbt(tasks: list[str], root: Path = ROOT) -> str:
    p = pins(root)
    launcher = obtain("sbt-launch.jar", p["sbt_launcher"])
    return run([str(java(p)), "-XX:ActiveProcessorCount=4", "-Xmx2g",
                "-Dsbt.supershell=false", "-Dsbt.color=false", "-Dsbt.log.noformat=true",
                "-Dsbt.override.build.repos=true",
                f"-Dsbt.repository.config={root / 'tools/repositories'}",
                "-jar", str(launcher)] + (["set offline := true"] if os.environ.get("NF_OFFLINE") == "1" else []) + tasks, cwd=root / "frontend/scala")


def validate_pins(root: Path = ROOT) -> None:
    import tomllib
    p = pins(root)
    rust = tomllib.loads((root / "rust-toolchain.toml").read_text())["toolchain"]
    if rust != {"channel": p["rust"], "profile": "minimal", "components": ["rustfmt", "clippy"]}:
        raise BootstrapError("NF-PIN-DRIFT: rust-toolchain.toml")
    expected = {
        "frontend/scala/project/build.properties": f"sbt.version={p['sbt']}\n",
        "frontend/scala/project/plugins.sbt": f'addSbtPlugin("org.scalameta" % "sbt-scalafmt" % "{p["sbt_scalafmt"]}")\n',
    }
    for path, value in expected.items():
        if (root / path).read_text() != value:
            raise BootstrapError(f"NF-PIN-DRIFT: {path}")
    if f'scalaVersion := "{p["scala"]}"' not in (root / "frontend/scala/build.sbt").read_text():
        raise BootstrapError("NF-PIN-DRIFT: scalaVersion")
    if f'version = {p["scalafmt"]}\n' not in (root / "frontend/scala/.scalafmt.conf").read_text():
        raise BootstrapError("NF-PIN-DRIFT: scalafmt")
    if f'FROM rust:{p["rust"]}-bookworm\n' not in (root / "ci/rust.Dockerfile").read_text():
        raise BootstrapError("NF-PIN-DRIFT: Rust isolation image")


def docs_check(root: Path = ROOT) -> None:
    # Link/whitespace checks complement, rather than replace, the roadmap validator.
    files = [root / "README.md", root / "AGENTS.md", *sorted((root / "docs").rglob("*.md"))]
    count = 0
    for path in files:
        outside = []
        fence = None
        for line in path.read_text().splitlines():
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                marker = stripped[:3]
                fence = None if marker == fence else (marker if fence is None else fence)
                continue
            if fence is None:
                outside.append(line)
        text = "\n".join(outside)
        if re.search(r"[ \t]+$", text, re.M):
            raise BootstrapError(f"NF-DOC-WHITESPACE: {path.relative_to(root)}")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if re.match(r"[a-z]+://", target) or target.startswith("#"):
                continue
            file = target.partition("#")[0]
            if file and not (path.parent / file).exists():
                raise BootstrapError(f"NF-DOC-LINK: {path.relative_to(root)} -> {target}")
            count += 1
    print(f"documentation_files={len(files)} local_links={count}; no hardware test credit")


def metadata(root: Path = ROOT) -> dict:
    def git(*args: str) -> str:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    head, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    expected = os.environ.get("NF_EXPECT_SHA")
    if expected and head != expected:
        raise BootstrapError(f"NF-SOURCE-MISMATCH: expected {expected}, got {head}")
    dirty = bool(git("status", "--porcelain", "--untracked-files=all"))
    if expected and dirty:
        raise BootstrapError("NF-SOURCE-DIRTY: canonical qualification requires an unchanged checkout")
    return {"head": head, "tree": tree, "dirty": dirty,
            "platform": platform.platform(), "python": platform.python_version(),
            "uid": os.geteuid() if hasattr(os, "geteuid") else None,
            "scope": "Foundation contracts/build profiles; no Nodal fabric or Verilog qualification"}


def check(profile: str, root: Path = ROOT) -> None:
    validate_pins(root)
    if profile == "contracts":
        from check_boundaries import check as boundaries
        boundaries(root)
        from maven_inventory import check_static as scala_boundary
        scala_boundary(root)
        docs_check(root)
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests/bootstrap", "-v"], root)
        from check_foundation_contracts import check as foundation_contracts
        print(json.dumps(foundation_contracts(root, accepted=True), sort_keys=True))
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests/foundation", "-v"], root)
        from roadmap import check as roadmap_check
        print(json.dumps(roadmap_check(root), sort_keys=True))
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests/roadmap", "-v"], root)
    elif profile == "rust":
        doctor("rust", pins(root))
        from check_boundaries import check as boundaries
        boundaries(root)
        # Inspect locked graph and cached source identities before compiling any
        # reviewed third-party build script or proc macro.
        output = run(["cargo", "metadata", "--locked", "--offline", "--format-version", "1"], root)
        from check_boundaries import check_metadata
        check_metadata(root, json.loads(output))
        run(["cargo", "fmt", "--all", "--", "--check"], root)
        run(["cargo", "clippy", "--locked", "--offline", "--workspace", "--all-targets", "--", "-D", "warnings"], root)
        run(["cargo", "test", "--locked", "--offline", "--workspace", "--all-targets"], root)
        run(["cargo", "test", "--locked", "--offline", "--workspace", "--doc"], root)
        output = run(["cargo", "metadata", "--locked", "--offline", "--format-version", "1"], root)
        data = json.loads(output)
        from check_boundaries import check_metadata
        check_metadata(root, data)
    elif profile == "exchange":
        doctor("rust", pins(root))
        from check_boundaries import check as boundaries, check_metadata
        boundaries(root)
        output = run(["cargo", "metadata", "--locked", "--offline", "--format-version", "1"], root)
        check_metadata(root, json.loads(output))
        run(["cargo", "build", "--locked", "--offline", "-p", "nf-exchange", "--bin", "nf-exchange"], root)
        evidence = root / "artifacts/fnd05-exchange"
        evidence.mkdir(parents=True, exist_ok=True)
        run_directory = Path(tempfile.mkdtemp(prefix="run-", dir=evidence))
        scala_output = run_directory / "scala"
        run([sys.executable, str(root / "frontend/scala/write-fixtures.py"), str(scala_output),
             "--goldens", str(root / "verify/fixtures/exchange/goldens")], root)
        from maven_inventory import check_actual
        check_actual(root, (scala_output / "authoring.log").read_text())
        env = dict(os.environ, NF_EXCHANGE_BIN=str(root / "target/debug/nf-exchange"),
                   NF_EXCHANGE_SCALA_DIR=str(scala_output))
        result = run([sys.executable, "-m", "unittest", "discover", "-s", "tests/exchange", "-v"], root, env=env)
        (run_directory / "conformance.log").write_text(result)
        print(f"exchange_evidence={run_directory}")
    else:
        doctor("scala", pins(root))
        from maven_inventory import check_static, check_actual
        check_static(root)
        output = sbt(["scalafmtCheckAll", "scalafmtSbtCheck", "clean", "compile", "Test / compile",
                      f"Test / runMain nodalfpga.exchange.WriterChecks {root / 'verify/fixtures/exchange/goldens'}",
                      "show scalaVersion", "show sbtVersion", "show scalaInstance", "show Runtime / dependencyClasspath"], root)
        check_actual(root, output)


def rust_smoke(root: Path) -> dict[str, str]:
    """Build and execute both reviewed Rust examples; retain exact UTF-8 bytes."""
    outputs = {}
    for package, example in [("nf-bootstrap", "identity"), ("nf-arch-ir", "model")]:
        run(["cargo", "build", "--locked", "--offline", "-p", package, "--example", example], root)
        binary = root / "target/debug/examples" / example
        result = subprocess.run([str(binary)], cwd=root, capture_output=True, check=True)
        # Decode directly rather than text=True's universal-newline conversion:
        # deterministic output means identical bytes, including line endings.
        output = result.stdout.decode("utf-8")
        run(["ldd", str(binary)], root)
        if example == "identity":
            if output != "nodal-fpga/bootstrap/1\nprofile=build-only\n":
                raise BootstrapError("NF-SMOKE: unexpected Rust bootstrap output")
        elif (not output.startswith("nodal-fpga/arch-ir/1\n")
              or "profile=structural-selection\n" not in output.splitlines(keepends=True)
              or "rejected=value\n" not in output.splitlines(keepends=True)):
            raise BootstrapError("NF-SMOKE: missing ArchIR model identity/profile/rejection witness")
        outputs[example] = output
    return outputs


def reproduce(profile: str) -> None:
    outputs = []
    model_outputs = []
    p = pins()
    doctor(profile, p)
    with tempfile.TemporaryDirectory(prefix="nf-reproduce-") as temporary:
        for index in range(2):
            copy = Path(temporary) / f"checkout-{index}"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", ".cache", "target", "artifacts", "__pycache__"))
            if profile == "rust":
                examples = rust_smoke(copy)
                output = examples["identity"]
                model_outputs.append(examples["model"])
            else:
                raw = sbt(["clean", "compile", "run"], copy)
                lines = raw.splitlines()
                start = lines.index("nodal-fpga/bootstrap/1")
                output = "\n".join(lines[start:start + 3]) + "\n"
                if output != "nodal-fpga/bootstrap/1\nfrontend=scala3\nprofile=build-only\n":
                    raise BootstrapError("NF-SMOKE: unexpected Scala output")
            if (copy / "Cargo.lock").read_bytes() != (ROOT / "Cargo.lock").read_bytes():
                raise BootstrapError("NF-LOCK-DRIFT: clean build changed Cargo.lock")
            outputs.append(output)
    if outputs[0] != outputs[1]:
        raise BootstrapError("NF-NONDETERMINISTIC: repeated smoke output differs")
    report = {"profile": profile, "clean_builds": 2, "stdout": outputs[0],
              "stdout_sha256": hashlib.sha256(outputs[0].encode()).hexdigest()}
    if profile == "rust":
        if model_outputs[0] != model_outputs[1]:
            raise BootstrapError("NF-NONDETERMINISTIC: repeated ArchIR model output differs")
        report["model_stdout"] = model_outputs[0]
        report["model_stdout_sha256"] = hashlib.sha256(model_outputs[0].encode()).hexdigest()
    print(json.dumps(report, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["bootstrap", "doctor", "reproduce"]:
        sub.add_parser(name).add_argument("profile", choices=["rust", "scala"])
    sub.add_parser("check").add_argument("profile", choices=["contracts", "rust", "scala", "exchange"])
    runtime = sub.add_parser("saved-runtime", help="inspect actual saved Scala bytes with a prebuilt reader in an allowlisted root")
    runtime.add_argument("--binary", type=Path, default=ROOT / "target/debug/nf-exchange")
    runtime.add_argument("--scala-artifacts", type=Path, required=True)
    runtime.add_argument("--output", type=Path, required=True)
    runtime.add_argument("--allow-untraced-partial", action="store_true", help="record partial consumption evidence only; never full runtime qualification")
    runtime.add_argument("--observation-profile", choices=["strace", "loader-procfs"], default="strace",
                         help="exact profile still requires source/result review before acceptance")
    fmt = sub.add_parser("format")
    fmt.add_argument("profile", choices=["rust", "scala"])
    fmt.add_argument("--check", action="store_true")
    sub.add_parser("identity")
    roadmap = sub.add_parser("roadmap", help="validate authoritative nested progress and evidence")
    roadmap.add_argument("--write-view", type=Path, help="write a disposable deterministic derived JSON view")
    roadmap.add_argument("--check-view", type=Path, help="reject a conflicting previously generated view")
    roadmap.add_argument("--expect-source", action="append", default=[], metavar="ID=SHA")
    roadmap.add_argument("--check-anchor", action="append", default=[], metavar="ID=CANDIDATE_SHA")
    args = parser.parse_args()
    try:
        if args.command in {"bootstrap", "doctor"}:
            globals()[args.command](args.profile, pins())
        elif args.command == "check":
            check(args.profile)
        elif args.command == "reproduce":
            reproduce(args.profile)
        elif args.command == "saved-runtime":
            from saved_runtime import qualify
            result = qualify(ROOT, args.binary.resolve(), args.scala_artifacts.resolve(), args.output.resolve(),
                             trace=not args.allow_untraced_partial and args.observation_profile == "strace",
                             loader_observation=not args.allow_untraced_partial and args.observation_profile == "loader-procfs")
            print(json.dumps(result, indent=2))
        elif args.command == "roadmap":
            from roadmap import load, validate, check as roadmap_check, render, verify_derived, read_json, verify_source_anchor, write_view, validate_evidence
            expectations = {}
            for value in args.expect_source:
                identifier, separator, sha = value.partition("=")
                if not separator or identifier in expectations:
                    raise BootstrapError("RM-EVIDENCE-SOURCE: use unique ID=SHA expectations")
                expectations[identifier] = sha
            data = load(ROOT)
            validate(data, ROOT, expected_sources=expectations)
            for value in args.check_anchor:
                identifier, separator, candidate = value.partition("=")
                if not separator or identifier not in data.increments:
                    raise BootstrapError("RM-EVIDENCE-SOURCE: use known ID=CANDIDATE_SHA")
                validate_evidence(data, identifier, ROOT)
                receipt = read_json(ROOT / f"docs/completion/{identifier}.evidence.json")
                verify_source_anchor(ROOT, receipt["source"]["commit"], candidate)
            if args.check_view:
                verify_derived(data, args.check_view)
            if args.write_view:
                write_view(data, ROOT, args.write_view)
            print(json.dumps(roadmap_check(ROOT, expected_sources=expectations), sort_keys=True))
        elif args.command == "format":
            doctor(args.profile, pins())
            if args.profile == "rust":
                run(["cargo", "fmt", "--all"] + (["--", "--check"] if args.check else []))
            else:
                sbt(["scalafmtCheckAll", "scalafmtSbtCheck"] if args.check else ["scalafmtAll", "scalafmtSbt"])
        else:
            print(json.dumps(metadata(), indent=2))
        return 0
    except (BootstrapError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
