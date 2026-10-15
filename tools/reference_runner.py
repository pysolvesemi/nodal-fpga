"""Bounded, local-only child capture for the independent reference profile.

This is orchestration, never an oracle. Raw logs remain in the caller's private
output directory. Aggregate storage/process limits are sampled guardrails (with
possible between-sample overshoot), not filesystem quotas or hostile-code claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
import os
from pathlib import Path
import resource
import selectors
import signal
import stat
import subprocess
import time


@dataclass(frozen=True)
class Limits:
    wall_seconds: float = 120
    cpu_seconds: int = 120
    address_bytes: int = 4 * 1024**3
    output_bytes: int = 16 * 1024**2
    storage_bytes: int = 256 * 1024**2
    file_bytes: int = 128 * 1024**2
    files: int = 4096
    processes: int = 64
    open_files: int = 256
    poll_seconds: float = 0.02

    def validate(self):
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError("NF-REFERENCE-LIMIT: invalid " + name)
        if self.poll_seconds > 1 or self.wall_seconds > 3600:
            raise ValueError("NF-REFERENCE-LIMIT: polling/wall bound exceeds profile")
        for name in set(asdict(self)) - {"wall_seconds", "poll_seconds"}:
            if not isinstance(getattr(self, name), int):
                raise ValueError("NF-REFERENCE-LIMIT: integer required")


@dataclass(frozen=True)
class ProcessResult:
    category: str
    returncode: int
    wall_seconds: float
    user_seconds: float
    system_seconds: float
    max_rss_kib: int
    stdout_bytes: int
    stderr_bytes: int
    stdout_sha256: str
    stderr_sha256: str
    storage_bytes: int
    file_count: int
    peak_processes: int
    stdout_path: Path
    stderr_path: Path
    accounting_scope: str = 'launched-process-and-waited-children'

    def portable(self):
        return {k: v for k, v in asdict(self).items() if not k.endswith("_path")}


def storage_usage(root: Path, limits: Limits):
    """lstat only: never follow child-created symlinks or special files."""
    size = count = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                item = entry.stat(follow_symlinks=False)
                count += 1
                if stat.S_ISLNK(item.st_mode) or not (stat.S_ISDIR(item.st_mode) or stat.S_ISREG(item.st_mode)):
                    raise ValueError("unsafe-output")
                if stat.S_ISDIR(item.st_mode):
                    pending.append(Path(entry.path))
                else:
                    size += item.st_size
                if count > limits.files or size > limits.storage_bytes:
                    return size, count
    return size, count


def descendants(pid):
    # Some supported kernels omit task/PID/children. Read ancestry metadata,
    # then inspect only our own launched descendants (same approach as FND-05).
    children = {}
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            fields = (entry / 'stat').read_text().rpartition(')')[2].split()
            children.setdefault(int(fields[1]), []).append(int(entry.name))
        except (FileNotFoundError, ProcessLookupError):
            pass
    pending, seen = [pid], set()
    while pending:
        current = pending.pop()
        if current not in seen:
            seen.add(current)
            pending.extend(children.get(current, []))
    return seen


def run_bounded(argv, *, output_dir: Path, work_dir: Path, limits=Limits(),
                env=None, pass_fds=(), cwd=None) -> ProcessResult:
    """Run one invocation; output_dir must not exist; never print raw output.

    Caller supplies namespace isolation. start_new_session and group termination
    complement its PID namespace. wait4 accounts for the reaped process tree.
    """
    limits.validate()
    if not argv or any(not isinstance(x, str) or '\0' in x for x in argv):
        raise ValueError("NF-REFERENCE-COMMAND: nonempty string argv required")
    output_dir, work_dir = Path(output_dir), Path(work_dir)
    if not work_dir.is_dir() or work_dir.is_symlink():
        raise ValueError("NF-REFERENCE-WORK: regular directory required")
    output_dir.mkdir(parents=True, exist_ok=False)
    stdout_path, stderr_path = output_dir / 'stdout.log', output_dir / 'stderr.log'

    def restrict():
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        for kind, bound in [(resource.RLIMIT_CPU, limits.cpu_seconds),
                            (resource.RLIMIT_AS, limits.address_bytes),
                            (resource.RLIMIT_FSIZE, limits.file_bytes),
                            (resource.RLIMIT_NOFILE, limits.open_files),
                            (resource.RLIMIT_NPROC, limits.processes)]:
            resource.setrlimit(kind, (bound, bound))

    start = time.monotonic()
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env={} if env is None else env,
                               cwd=cwd, close_fds=True, pass_fds=pass_fds,
                               start_new_session=True, preexec_fn=restrict)
    selector = selectors.DefaultSelector()
    hashes = [hashlib.sha256(), hashlib.sha256()]
    counts = [0, 0]
    status, usage, reason = None, None, None
    size = count = 0
    peak = 1
    try:
        with stdout_path.open('xb') as out, stderr_path.open('xb') as err:
            streams = [out, err]
            for index, pipe in enumerate([process.stdout, process.stderr]):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, index)
            while status is None or selector.get_map():
                elapsed = time.monotonic() - start
                if reason is None:
                    if elapsed > limits.wall_seconds:
                        reason = 'timeout'
                    try:
                        size, count = storage_usage(work_dir, limits)
                    except ValueError:
                        reason = 'unsafe-output'
                    except FileNotFoundError:
                        # A child may rename/remove its own scratch during scan.
                        pass
                    if size > limits.storage_bytes or count > limits.files:
                        reason = 'storage-limit'
                    peak = max(peak, len(descendants(process.pid)))
                    if peak > limits.processes:
                        reason = 'process-limit'
                if reason is not None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                for key, _ in selector.select(limits.poll_seconds):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    index = key.data
                    room = max(0, limits.output_bytes - sum(counts))
                    kept = chunk[:room]
                    streams[index].write(kept)
                    hashes[index].update(kept)
                    counts[index] += len(kept)
                    if len(chunk) > room:
                        reason = 'output-limit'
                if status is None:
                    pid, observed, observed_usage = os.wait4(process.pid, os.WNOHANG)
                    if pid:
                        status, usage = observed, observed_usage
                        process.returncode = os.waitstatus_to_exitcode(status)
                        # Kill lingering group children, including pipe holders.
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
            try:
                size, count = storage_usage(work_dir, limits)
                if size > limits.storage_bytes or count > limits.files:
                    reason = reason or 'storage-limit'
            except ValueError:
                reason = reason or 'unsafe-output'
    finally:
        selector.close()
        if status is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
        for pipe in [process.stdout, process.stderr]:
            if not pipe.closed:
                pipe.close()
    return ProcessResult(reason or ('passed' if process.returncode == 0 else 'tool-error'),
                         process.returncode, time.monotonic() - start, usage.ru_utime,
                         usage.ru_stime, usage.ru_maxrss, *counts,
                         *(h.hexdigest() for h in hashes), size, count, peak,
                         stdout_path, stderr_path)


def child_main(argv):
    """Inside-namespace child accounting, avoiding bwrap helper-only rusage."""
    import json
    process = subprocess.Popen(argv, close_fds=True)
    _, status, usage = os.wait4(process.pid, 0)
    process.returncode = os.waitstatus_to_exitcode(status)
    Path('/work/.child-usage.json').write_text(json.dumps({
        'returncode': process.returncode, 'user_seconds': usage.ru_utime,
        'system_seconds': usage.ru_stime, 'max_rss_kib': usage.ru_maxrss,
        'scope': 'wait4 of actual tool and its waited children; killed runs may lack record'}))
    return process.returncode if process.returncode >= 0 else 128 - process.returncode


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3 or sys.argv[1] != '--child':
        raise SystemExit('NF-REFERENCE-ENTRY: internal --child invocation required')
    raise SystemExit(child_main(sys.argv[2:]))
