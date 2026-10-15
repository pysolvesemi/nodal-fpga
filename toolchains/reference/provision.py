#!/usr/bin/env python3
"""Acquire checked reference archives, or reconstruct an external cache offline.

No system installs, core environment changes, editable sync, or binary uploads.
The supplied Python must already be qualified CPython 3.12.14 with the required
ABI. This script does not claim to provision the pending final CI base image.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

LOCK = Path(__file__).with_name('sources.json')
MAX_ARCHIVE_BYTES = 256 * 1024**2
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from reference_runner import Limits, run_bounded


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check_archive(path, expected):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_ARCHIVE_BYTES or sha(path) != expected:
        raise ValueError('NF-REFERENCE-ARCHIVE: missing, unsafe or mismatched archive')


def fetch(lock, archives):
    """Explicit network acquisition only; verification always runs offline."""
    for kind, entries in [('downloads', lock['debian_packages']), ('python-wheels', lock['python_packages'])]:
        directory = archives / kind
        directory.mkdir(parents=True, exist_ok=True)
        for entry in entries:
            expected = entry.get('sha256', entry.get('prepared_wheel_sha256'))
            target = directory / entry['filename']
            if target.exists():
                check_archive(target, expected)
                continue
            if 'url' not in entry:
                # Never substitute PyPI release contents for the pinned git build.
                continue
            parsed = urllib.parse.urlsplit(entry['url'])
            if parsed.scheme != 'https' or parsed.hostname not in {'files.pythonhosted.org', 'deb.debian.org'}:
                raise ValueError('NF-REFERENCE-ORIGIN: unreviewed archive origin')
            partial = target.with_suffix(target.suffix + '.partial')
            try:
                with urllib.request.urlopen(entry['url'], timeout=60) as response, partial.open('xb') as stream:
                    final = urllib.parse.urlsplit(response.url)
                    if final.scheme != 'https' or final.hostname != parsed.hostname:
                        raise ValueError('NF-REFERENCE-ORIGIN: unexpected redirect')
                    count = 0
                    while chunk := response.read(1024 * 1024):
                        count += len(chunk)
                        if count > MAX_ARCHIVE_BYTES:
                            raise ValueError('NF-REFERENCE-ARCHIVE: download bound exceeded')
                        stream.write(chunk)
                check_archive(partial, expected)
                partial.rename(target)
            finally:
                partial.unlink(missing_ok=True)


def reconstruct(lock, archives, destination, python):
    for folder, entries in [('downloads', lock['debian_packages']), ('python-wheels', lock['python_packages'])]:
        for entry in entries:
            check_archive(archives / folder / entry['filename'], entry.get('sha256', entry.get('prepared_wheel_sha256')))
    destination.mkdir(parents=True, exist_ok=False)
    logs = destination / 'logs'
    logs.mkdir()
    environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'HOME': str(destination / 'home'),
                   'PIP_NO_INDEX': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1',
                   'PYTHONDONTWRITEBYTECODE': '1'}
    Path(environment['HOME']).mkdir()
    def run(name, command):
        # Use the same bounded capture/lifecycle plumbing as tool invocation.
        result = run_bounded(command, output_dir=logs / name, work_dir=destination,
                             cwd=destination, env=environment,
                             limits=Limits(wall_seconds=180, cpu_seconds=180,
                                           address_bytes=8 * 1024**3,
                                           storage_bytes=4 * 1024**3,
                                           file_bytes=1024**3, files=100000))
        if result.category != 'passed':
            raise ValueError('NF-REFERENCE-PROVISION: ' + name)
    run('python-version', [str(python), '-c', 'import sys; assert sys.version_info[:3] == (3,12,14)'])
    for folder, entries in [('downloads', lock['debian_packages']), ('python-wheels', lock['python_packages'])]:
        (destination / folder).mkdir()
        for entry in entries:
            shutil.copyfile(archives / folder / entry['filename'], destination / folder / entry['filename'])
    (destination / 'root').mkdir()
    for index, entry in enumerate(lock['debian_packages']):
        run('extract-' + str(index), ['/usr/bin/dpkg-deb', '-x', str(destination / 'downloads' / entry['filename']), str(destination / 'root')])
    run('venv', [str(python), '-m', 'venv', str(destination / 'fabulous-venv')])
    requirements = destination / 'requirements-hashed.txt'
    requirements.write_text(''.join(f"{p['name']}=={p['version']} --hash=sha256:{p.get('sha256', p.get('prepared_wheel_sha256'))}\n" for p in lock['python_packages']))
    vpython = destination / 'fabulous-venv/bin/python'
    run('offline-install', [str(vpython), '-m', 'pip', 'install', '--no-index', '--no-deps', '--require-hashes', '--find-links', str(destination / 'python-wheels'), '-r', str(requirements)])
    run('dependency-check', [str(vpython), '-m', 'pip', 'check'])
    # No installer distribution is part of the frozen eighty runtime packages.
    run('remove-installer', [str(vpython), '-m', 'pip', 'uninstall', '-y', 'pip', 'setuptools'])
    wrappers = destination / 'bin'
    wrappers.mkdir()
    for name in ['iverilog', 'vvp', 'yosys', 'yosys-abc', 'yosys-smtbmc', 'yosys-witness', 'z3']:
        options = ' -B "$r/root/usr/lib/x86_64-linux-gnu/ivl"' if name == 'iverilog' else ' -M "$r/root/usr/lib/x86_64-linux-gnu/ivl"' if name == 'vvp' else ''
        command = f'"$r/root/usr/bin/{name}"{options} "$@"'
        if name in {'yosys-smtbmc', 'yosys-witness'}:
            command = f'"$r/fabulous-venv/bin/python" "$r/root/usr/bin/{name}" "$@"'
        path = wrappers / name
        path.write_text('#!/bin/bash\nset -euo pipefail\nr="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"\nexport PYTHONDONTWRITEBYTECODE=1\nexport PYTHONPATH="$r/root/usr/share/yosys${PYTHONPATH:+:$PYTHONPATH}"\nexec ' + command + '\n')
        path.chmod(0o755)
    binaries = []
    for path in sorted((destination / 'root').rglob('*')):
        if path.is_file() and (os.access(path, os.X_OK) or path.suffix in {'.so', '.vpi', '.tgt'}):
            binaries.append({'path': str(path.relative_to(destination)), 'sha256': sha(path)})
    manifest = {'python': {'sha256': sha(python.resolve())}, 'binaries': binaries,
                'scope': 'separately reconstructed local cache; qualify imports/ELF/capabilities before corpus'}
    (destination / 'host-and-elf-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Runtime libraries are discovered by ReferenceEnvironment from exact ELF
    # dependencies; retain an empty import addition until actual imports replay.
    (destination / 'python-import-loaded-libraries.json').write_text('{"runtime_libraries": [], "scope": "imports not yet qualified"}\n')
    (destination / 'provision-summary.json').write_text(json.dumps({'profile': lock['profile'],
        'source_lock_sha256': sha(LOCK), 'archive_counts': {'debian': 4, 'python': 80},
        'status': 'reconstructed-not-qualified', 'python_sha256': sha(python.resolve())}, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', required=True, type=Path)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--python', type=Path)
    args = parser.parse_args()
    lock = json.loads(LOCK.read_text())
    if args.fetch:
        fetch(lock, args.archives.resolve())
    if args.destination:
        if args.python is None:
            parser.error('--destination requires a separately qualified --python')
        reconstruct(lock, args.archives.resolve(), args.destination.resolve(), args.python.resolve(strict=True))
    if not args.fetch and not args.destination:
        parser.error('choose explicit --fetch and/or offline --destination reconstruction')
    print(json.dumps({'profile': lock['profile'], 'status': 'acquisition-or-reconstruction-complete-not-qualification'}))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError):
        raise SystemExit('NF-REFERENCE-PROVISION: failed; inspect local logs; no qualification credit')
