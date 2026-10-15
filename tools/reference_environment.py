"""Explicit reference-only Linux environment; never modifies the default PATH.

Read-only selected roots, a fresh PID/user/IPC/UTS namespace, no inherited
network descriptors and a socket/io_uring syscall-denial policy. This is not a
network namespace, a generic hostile-code sandbox, or CI-image qualification.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

try:
    from .reference_runner import Limits, ProcessResult, run_bounded
except ImportError:
    from reference_runner import Limits, ProcessResult, run_bounded

PROFILE = 'fnd06-reference-linux-x86_64-cp312'
# x86_64 socket family, io_uring, namespace/mount manipulation and session escape.
# fork/clone remain available to reviewed tools and solver children. RLIMIT_NPROC
# and sampled descendant counts bound this profile; no hostile-process claim.
DENIED = set(range(41, 56)) | {288, 299, 307, 425, 426, 427, 165, 166, 272, 308, 112}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def socket_filter():
    instructions = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc000003e),
                    (0x06, 0, 0, 0x80000000), (0x20, 0, 0, 0),
                    (0x35, 0, 1, 0x40000000), (0x06, 0, 0, 0x80000000)]
    for syscall in sorted(DENIED):
        instructions += [(0x15, 0, 1, syscall), (0x06, 0, 0, 0x00050001)]
    instructions.append((0x06, 0, 0, 0x7fff0000))
    return b''.join(struct.pack('=HBBI', *i) for i in instructions)


def checked(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=30, env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
    if result.returncode:
        raise ValueError('NF-REFERENCE-SETUP: command failed')
    if len(result.stdout) > 8 * 1024**2:
        raise ValueError('NF-REFERENCE-SETUP: excessive inspection output')
    return result.stdout.decode()


def linked_libraries(path):
    """Inspect trusted, hash-qualified ELF files only; no arbitrary user binary."""
    with Path(path).open('rb') as stream:
        if stream.read(4) != b'\x7fELF':
            return []
    result = subprocess.run(['/usr/bin/ldd', str(path)], capture_output=True,
                            timeout=10, env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
    output = result.stdout.decode()
    if 'not found' in output or (result.returncode and 'not a dynamic executable' not in output and 'statically linked' not in output):
        raise ValueError('NF-REFERENCE-ABI: unresolved ELF dependency')
    return [Path(p) for p in re.findall(r'(?:=>\s*)?(/[^\s]+)', output)]


class ReferenceEnvironment:
    def __init__(self, repo: Path, cache: Path, upstream: Path, *, expected_sha=None):
        self.repo, self.cache, self.upstream = (Path(p).resolve(strict=True) for p in (repo, cache, upstream))
        if platform.system() != 'Linux' or platform.machine() != 'x86_64':
            raise ValueError('NF-REFERENCE-PLATFORM: Linux x86_64 required')
        self.bwrap = shutil.which('bwrap')
        if self.bwrap is None:
            raise ValueError('NF-REFERENCE-MISSING-TOOL: bwrap')
        self.lock = json.loads((self.repo / 'toolchains/reference/sources.json').read_text())
        self.python = (self.cache / 'fabulous-venv/bin/python').resolve(strict=True)
        self.python_base = self.python.parent.parent
        expected_sha = expected_sha or os.environ.get('NF_EXPECT_SHA')
        self.source_commit = checked(['git', '-C', str(self.repo), 'rev-parse', 'HEAD']).strip()
        self.source_tree = checked(['git', '-C', str(self.repo), 'rev-parse', 'HEAD^{tree}']).strip()
        self.source_dirty = bool(checked(['git', '-C', str(self.repo), 'status', '--porcelain', '--untracked-files=all']))
        if expected_sha and (self.source_commit != expected_sha or self.source_dirty):
            raise ValueError('NF-REFERENCE-SOURCE: final qualification requires exact clean source')
        self._snapshot = tempfile.TemporaryDirectory(prefix='nf-reference-source-')
        self.source_inventory = {}
        total = 0
        for name in ['tools', 'verify', 'toolchains']:
            for source in sorted((self.repo / name).rglob('*')):
                if '__pycache__' in source.parts or source.suffix == '.pyc':
                    continue
                if source.is_symlink():
                    raise ValueError('NF-REFERENCE-SOURCE: symlinks are not source inputs')
                if source.is_file():
                    total += source.stat().st_size
                    if total > 64 * 1024**2 or len(self.source_inventory) >= 8192:
                        raise ValueError('NF-REFERENCE-SOURCE: source snapshot bound exceeded')
                    relative = source.relative_to(self.repo)
                    target = Path(self._snapshot.name) / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
                    self.source_inventory[str(relative)] = digest(target)
        self.mounts = {}
        self.identities = {}
        self._prepare()
        self.runtime_inventory = self._runtime_inventory()
        self.runtime_inventory_sha256 = hashlib.sha256(
            (json.dumps(self.runtime_inventory, indent=2) + '\n').encode()).hexdigest()

    def _mount(self, source, destination):
        source = Path(source).resolve(strict=True)
        destination = str(destination)
        if not destination.startswith('/') or '..' in PurePosixPath(destination).parts:
            raise ValueError('NF-REFERENCE-MOUNT: invalid destination')
        if destination in self.mounts and self.mounts[destination] != source:
            raise ValueError('NF-REFERENCE-MOUNT: conflicting destination')
        self.mounts[destination] = source

    def _prepare(self):
        if checked(['git', '-C', str(self.upstream), 'rev-parse', 'HEAD']).strip() != self.lock['upstream']['commit']:
            raise ValueError('NF-REFERENCE-PROVENANCE: wrong upstream commit')
        if checked(['git', '-C', str(self.upstream), 'status', '--porcelain', '--untracked-files=all']):
            raise ValueError('NF-REFERENCE-PROVENANCE: dirty upstream')
        if digest(self.upstream / 'uv.lock') != self.lock['upstream']['uv_lock_sha256']:
            raise ValueError('NF-REFERENCE-PROVENANCE: upstream lock changed')
        for package in self.lock['debian_packages']:
            if digest(self.cache / 'downloads' / package['filename']) != package['sha256']:
                raise ValueError('NF-REFERENCE-PROVENANCE: package archive changed')
        for package in self.lock['python_packages']:
            expected = package.get('sha256', package.get('prepared_wheel_sha256'))
            if digest(self.cache / 'python-wheels' / package['filename']) != expected:
                raise ValueError('NF-REFERENCE-PROVENANCE: Python archive changed')
        site = self.cache / 'fabulous-venv/lib/python3.12/site-packages'
        installed = set()
        for metadata in site.glob('*.dist-info/METADATA'):
            text = metadata.read_text()
            name = re.search(r'^Name: (.+)$', text, re.M).group(1)
            version = re.search(r'^Version: (.+)$', text, re.M).group(1)
            installed.add((re.sub(r'[-_.]+', '-', name).lower(), version))
        expected = {(re.sub(r'[-_.]+', '-', p['name']).lower(), p['version'])
                    for p in self.lock['python_packages']}
        if installed != expected:
            raise ValueError('NF-REFERENCE-PROVENANCE: installed distribution closure differs')
        for package in self.lock['python_packages']:
            with zipfile.ZipFile(self.cache / 'python-wheels' / package['filename']) as wheel:
                for member in wheel.infolist():
                    if member.is_dir() or '.data/' in member.filename or member.filename.endswith('/RECORD'):
                        continue
                    parts = PurePosixPath(member.filename).parts
                    if '..' in parts or member.filename.startswith('/'):
                        raise ValueError('NF-REFERENCE-PROVENANCE: unsafe wheel path')
                    path = site / member.filename
                    if not path.is_file() or digest(path) != hashlib.sha256(wheel.read(member)).hexdigest():
                        raise ValueError('NF-REFERENCE-PROVENANCE: installed wheel content differs')
        prepared = json.loads((self.cache / 'host-and-elf-manifest.json').read_text())
        # Local executable identities are not substituted for upstream provenance.
        for item in prepared['binaries']:
            path = self.cache / item['path']
            if digest(path) != item['sha256']:
                raise ValueError('NF-REFERENCE-PROVENANCE: extracted executable changed')
        if digest(self.python) != prepared['python']['sha256']:
            raise ValueError('NF-REFERENCE-PROVENANCE: Python executable changed')
        for name in ['tools', 'verify', 'toolchains']:
            self._mount(Path(self._snapshot.name) / name, '/source/' + name)
        for name in ['bin', 'root', 'fabulous-venv']:
            self._mount(self.cache / name, '/reference/' + name)
        self._mount(self.upstream, '/upstream')
        self._mount(self.python, str(self.python))
        self._mount(self.python, str(self.python_base / 'bin/python3'))
        self._mount(self.python, str(self.python_base / 'bin/python'))
        # Keep venv's exact base path valid without mounting ambient site-packages.
        stdlib = self.python_base / 'lib/python3.12'
        for child in sorted(stdlib.iterdir()):
            if child.name not in {'site-packages', '__pycache__'}:
                self._mount(child, str(child))
        for child in sorted((self.python_base / 'lib').glob('*.so*')):
            self._mount(child, str(child))
        executables = [self.python]
        for name in ['bash', 'sh', 'env', 'dirname', 'git']:
            path = Path(shutil.which(name) or '/missing')
            self._mount(path, '/bin/' + name)
            executables.append(path)
        self._mount(Path(shutil.which('env')), '/usr/bin/env')
        # Yosys tooling /usr/bin/python3 shebang must select the qualified venv.
        self._mount(self.python, '/usr/bin/python3')
        executables.extend(self.cache / item['path'] for item in prepared['binaries'])
        # Tk is not part of this headless profile; the prepared CPython build's
        # optional Tk extension has unavailable Tcl9 dependencies.
        executables.extend(p for p in (stdlib / 'lib-dynload').glob('*.so')
                           if not p.name.startswith('_tkinter.'))
        libraries = set()
        for path in executables:
            libraries.update(linked_libraries(path))
        imported = json.loads((self.cache / 'python-import-loaded-libraries.json').read_text())
        libraries.update(Path(p['path']) for p in imported['runtime_libraries'])
        for path in sorted(libraries):
            if str(path).startswith(('/lib/', '/lib64/', '/usr/lib/')):
                self._mount(path, str(path))
            elif not (path.is_relative_to(self.cache) or path.is_relative_to(self.python_base)):
                raise ValueError('NF-REFERENCE-ABI: undeclared runtime library')
        for destination, source in self.mounts.items():
            if source.is_file():
                self.identities[destination] = digest(source)
        self.identities['source-lock'] = digest(self.repo / 'toolchains/reference/sources.json')
        self.identities['filter'] = hashlib.sha256(socket_filter()).hexdigest()

    def _runtime_inventory(self):
        """Exact local identity of every mounted byte and link, not provenance."""
        inventory = {}
        for destination, source in sorted(self.mounts.items()):
            paths = [source] if source.is_file() else sorted(source.rglob('*'))
            for path in paths:
                relative = '' if path == source else '/' + path.relative_to(source).as_posix()
                key = destination + relative
                if path.is_symlink():
                    inventory[key] = {'kind': 'symlink', 'target': os.readlink(path)}
                elif path.is_file():
                    item = path.stat()
                    inventory[key] = {'kind': 'file', 'bytes': item.st_size,
                                      'mode': item.st_mode & 0o777, 'sha256': digest(path)}
                elif not path.is_dir():
                    raise ValueError('NF-REFERENCE-RUNTIME: special file in mounted tree')
        inventory['host:bwrap'] = {'kind': 'executable', 'sha256': digest(self.bwrap),
                                    'version': checked([self.bwrap, '--version']).strip()}
        return inventory

    def command(self, name):
        if name == 'python':
            return '/reference/fabulous-venv/bin/python'
        if name not in {'iverilog', 'vvp', 'yosys', 'yosys-abc', 'yosys-smtbmc', 'yosys-witness', 'z3'}:
            raise ValueError('NF-REFERENCE-TOOL: unknown tool')
        return '/reference/bin/' + name

    def run(self, argv, output_dir: Path, *, limits=Limits(), inputs=None) -> ProcessResult:
        """Fresh output_dir/{work,logs}; inputs map sandbox absolute path to host.

        Allowed input destinations are /inputs/NAME, all readonly. Every stage
        gets fresh HOME/config/tmp, and /work is the sole regular writable root.
        Result paths and raw logs are local-only; portable() omits paths.
        """
        if self._runtime_inventory() != self.runtime_inventory:
            raise ValueError('NF-REFERENCE-RUNTIME: mounted runtime/source bytes changed')
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=False)
        work = output_dir / 'work'
        work.mkdir()
        for name in ['home', 'tmp', 'config', 'config/fabulous', 'config/matplotlib']:
            (work / name).mkdir(exist_ok=True)
        command = [self.bwrap, '--unshare-user', '--unshare-pid', '--unshare-ipc',
                   '--unshare-uts', '--die-with-parent', '--new-session', '--clearenv',
                   '--cap-drop', 'ALL']
        for destination, source in sorted(self.mounts.items()):
            command += ['--ro-bind', str(source), destination]
        for destination, source in sorted((inputs or {}).items()):
            parts = PurePosixPath(destination).parts
            if len(parts) != 3 or parts[:2] != ('/', 'inputs') or parts[2] in {'.', '..'}:
                raise ValueError('NF-REFERENCE-INPUT: expected /inputs/NAME')
            command += ['--ro-bind', str(Path(source).resolve(strict=True)), destination]
        command += ['--bind', str(work), '/work', '--symlink', '/work/tmp', '/tmp',
                    '--proc', '/proc', '--remount-ro', '/proc', '--dir', '/dev']
        for name in ['null', 'zero', 'random', 'urandom']:
            command += ['--dev-bind', '/dev/' + name, '/dev/' + name]
        environment = {'PATH': '/reference/bin:/reference/fabulous-venv/bin:/bin:/usr/bin',
                       'HOME': '/work/home', 'TMPDIR': '/work/tmp', 'LANG': 'C', 'LC_ALL': 'C',
                       'PYTHONPATH': '/upstream:/reference/root/usr/share/yosys',
                       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0',
                       'XDG_CONFIG_HOME': '/work/config', 'MPLCONFIGDIR': '/work/config/matplotlib',
                       'FAB_USER_CONFIG_DIR': '/work/config/fabulous',
                       'FAB_YOSYS_PATH': '/reference/bin/yosys',
                       'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
                       'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}
        for key, value in sorted(environment.items()):
            command += ['--setenv', key, value]
        with tempfile.TemporaryFile() as policy:
            policy.write(socket_filter())
            policy.flush()
            policy.seek(0)
            command += ['--remount-ro', '/', '--chdir', '/work', '--seccomp', str(policy.fileno()), '--',
                        self.command('python'), '/source/tools/reference_runner.py', '--child', *argv]
            result = run_bounded(command, output_dir=output_dir / 'logs', work_dir=work,
                                 limits=limits, pass_fds=(policy.fileno(),))
        result = replace(result, accounting_scope='launcher-only-incomplete')
        usage_path = work / '.child-usage.json'
        if usage_path.is_file():
            usage = json.loads(usage_path.read_text())
            result = replace(result, user_seconds=usage['user_seconds'],
                             system_seconds=usage['system_seconds'], max_rss_kib=usage['max_rss_kib'],
                             accounting_scope='tool-and-waited-children')
        elif result.category == 'passed':
            result = replace(result, category='missing-accounting')
        (output_dir / 'local-runtime-inventory.json').write_text(json.dumps(self.runtime_inventory, indent=2) + '\n')
        (output_dir / 'local-environment.json').write_text(json.dumps({
            'profile': PROFILE, 'source_commit': self.source_commit,
            'source_tree': self.source_tree, 'source_dirty': self.source_dirty,
            'source_snapshot_policy': 'explicit tools/verify/toolchains snapshot; dirty development is not final qualification',
            'source_inventory': self.source_inventory, 'mounts': {k: str(v) for k, v in self.mounts.items()},
            'identities': self.identities, 'runtime_inventory_sha256': self.runtime_inventory_sha256,
            'runtime_inventory_file': 'local-runtime-inventory.json', 'environment': environment,
            'limits': limits.__dict__, 'result': result.portable(),
            'scope': 'socket denial, not network namespace; sampled aggregate limits; one invocation'}, indent=2) + '\n')
        return result


def capability_smoke(environment: ReferenceEnvironment, output: Path):
    """Explicit tools-only capability controls; never generates reference RTL."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    def check(name, argv, expected='passed', limits=Limits(), contains=None):
        result = environment.run(argv, output / name, limits=limits)
        success = result.category == expected
        if contains is not None:
            success = success and contains in result.stdout_path.read_text()
        cases.append({'id': name, 'passed': success, **result.portable()})
        if not success:
            (output / 'smoke.json').write_text(json.dumps(cases, indent=2) + '\n')
            raise ValueError('NF-REFERENCE-CAPABILITY: ' + name)
    python = environment.command('python')
    controls = '''import os, socket, subprocess, sys
from pathlib import Path
import importlib.metadata
from fabulous.fabric_generator.code_generator.code_generator_Verilog import VerilogCodeGenerator
from fabulous.fabric_generator.gen_fabric.gen_configmem import generateConfigMem
from fabulous.fabric_generator.gen_fabric.gen_fabric import generateFabric
from fabulous.fabric_generator.gen_fabric.gen_switchmatrix import genTileSwitchMatrix
from fabulous.fabric_generator.gen_fabric.gen_tile import generateTile
from fabulous.fabric_generator.parser.parse_csv import parseFabricCSV
from fabulous.fabulous_settings import init_context
import fabulous
assert sys.version_info[:3] == (3,12,14)
assert importlib.metadata.version('FABulous-FPGA') == '2.0.0'
assert fabulous.__file__.startswith('/upstream/')
assert not Path('/source/.cache').exists()
assert not Path('/home').exists()
assert not Path('/usr/bin/cargo').exists()
assert not Path('/usr/bin/java').exists()
assert os.environ['FAB_YOSYS_PATH'] == '/reference/bin/yosys'
assert 'NoNewPrivs:\\t1' in Path('/proc/self/status').read_text()
assert 'Seccomp:\\t2' in Path('/proc/self/status').read_text()
fds=[]
for f in Path('/proc/self/fd').iterdir():
 try: fds.append((f.name,os.readlink(f)))
 except FileNotFoundError: pass
assert {name for name,_ in fds} == {'0','1','2'}
for family in [socket.AF_INET,socket.AF_INET6,socket.AF_UNIX]:
 try: socket.socket(family)
 except PermissionError: pass
 else: raise AssertionError('socket unexpectedly allowed')
try: socket.socketpair()
except PermissionError: pass
else: raise AssertionError('socketpair unexpectedly allowed')
for path in ['/escape', '/source/tools/escape', '/upstream/escape','/reference/bin/escape']:
 try: Path(path).write_text('must fail')
 except (PermissionError,OSError): pass
 else: raise AssertionError('readonly root writable')
subprocess.run([sys.executable,'-c','print("CHILD-PASS")'],check=True)
print('ISOLATION-PASS')
'''
    check('isolation-import', [python, '-c', controls], contains='ISOLATION-PASS')
    for name, args, version in [('iverilog', ['-V'], 'Icarus Verilog version 12.0'),
                                ('yosys', ['-V'], 'Yosys 0.52'),
                                ('z3', ['-version'], 'Z3 version 4.13.3')]:
        check(name, [environment.command(name), *args], contains=version)
    check('timeout', [python, '-c', 'import time; time.sleep(30)'], 'timeout',
          replace(Limits(), wall_seconds=.5))
    check('output-limit', [python, '-c', 'import os;\nwhile True: os.write(1,b"x"*65536)'],
          'output-limit', replace(Limits(), output_bytes=1024))
    check('storage-limit', [python, '-c', 'from pathlib import Path; import time; Path("large").write_bytes(b"x"*100000); time.sleep(3)'],
          'storage-limit', replace(Limits(), storage_bytes=1024))
    check('negative-exit', [python, '-c', 'raise SystemExit(7)'], 'tool-error')
    check('session-denial', [python, '-c', 'import os;\ntry: os.setsid()\nexcept PermissionError: print("SESSION-DENIED")\nelse: raise AssertionError()'], contains='SESSION-DENIED')
    (output / 'smoke.json').write_text(json.dumps(cases, indent=2) + '\n')
    return cases


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--upstream', required=True, type=Path)
    parser.add_argument('--smoke-output', required=True, type=Path)
    args = parser.parse_args()
    try:
        records = capability_smoke(ReferenceEnvironment(args.repo, args.cache, args.upstream), args.smoke_output)
    except (ValueError, OSError, subprocess.SubprocessError):
        raise SystemExit('NF-REFERENCE-CAPABILITY: failed; inspect local record')
    print(json.dumps({'profile': PROFILE, 'capability_checks': len(records), 'passed': len(records)}))
