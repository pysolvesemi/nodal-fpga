"""Exact actual-RTL deliverable comparison; never a semantic oracle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

try:
    from .reference_results import require, portable_rtl_inventory
except ImportError:
    from reference_results import require, portable_rtl_inventory

SHAPES = ('one', 'square', 'odd', 'sparse')
ARCHIVE = 'verify/fixtures/fnd-06/generated'
REFERENCE = 'verify/fixtures/nf-tiny/reference.json'
GENERATORS = {
    'historical': 'verify/fixtures/nf-tiny/fabulous/generate.py',
    'adapter': 'verify/fixtures/fnd-06/generate.py',
}


def _bytes(base: Path, name: str) -> bytes:
    require(isinstance(name, str) and bool(name) and '\\' not in name
            and str(PurePosixPath(name)) == name and not name.startswith('/')
            and all(p not in ('.', '..') for p in PurePosixPath(name).parts),
            'unsafe archive relative path')
    path = base
    require(base.is_dir() and not base.is_symlink(), 'unsafe archive base')
    for part in PurePosixPath(name).parts:
        path = path / part
        require(not path.is_symlink(), 'symlink in archive path')
    require(path.is_file() and path.stat().st_size <= 8 * 1024 * 1024,
            'missing, special or oversized archive file')
    return path.read_bytes()


def _identity(base: Path, name: str) -> dict:
    data = _bytes(base, name)
    return {'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def _json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate archive metadata key')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def archive_manifest(root: Path, shape: str, generated: Path, inventory: dict) -> dict:
    """Produce only portable identities after checking fresh generation bytes."""
    require(shape in SHAPES, 'unknown archive shape')
    identities = {key: {'path': path, 'sha256': _identity(root, path)['sha256']}
                  for key, path in GENERATORS.items()}
    actual = portable_rtl_inventory(generated, shape, expected_generators=identities)
    require(actual == inventory, 'fresh inventory differs from supplied inventory')
    reference = _json(_bytes(root, REFERENCE))
    require(actual['upstream_commit'] == reference['upstream']['commit']
            and actual['upstream_tree'] == reference['upstream']['tree'], 'archive upstream differs')
    inputs = []
    for item in reference['input_files']:
        identity = _identity(root, 'verify/fixtures/nf-tiny/' + item['path'])
        require(identity['sha256'] == item['sha256'], 'immutable archive input differs')
        inputs.append(identity)
    license_identity = _identity(generated, 'LICENSE.FABulous')
    require(license_identity['sha256'] == _identity(root, 'verify/fixtures/nf-tiny/fabulous/LICENSE.FABulous')['sha256'],
            'archive license differs')
    return {'format_version': 1, 'shape': shape,
            'upstream': {key: reference['upstream'][key] for key in ('repository', 'commit', 'tree', 'license')},
            'generator_sources': identities,
            'execution_adjustments': actual['execution_adjustments'],
            'original_input_manifest': _identity(root, REFERENCE),
            'original_inputs': sorted(inputs, key=lambda row: row['path']),
            'rtl': actual['artifacts'],
            'sources': _identity(generated, 'sources.f'), 'license': license_identity,
            'scope': 'Actual external reference RTL bytes; not independent expected semantics or Nodal-emitted RTL.'}


def verify_archive(root: Path, shape: str, generated: Path, inventory: dict) -> dict:
    """Require exact archived deliverables and compare them with fresh actual RTL."""
    expected = archive_manifest(root, shape, generated, inventory)
    relative = ARCHIVE + '/' + shape
    metadata = _json(_bytes(root, relative + '/manifest.json'))
    require(metadata == expected, 'archive manifest or identities differ')
    archive = root / relative
    rows = expected['rtl'] + [expected['sources'], expected['license']]
    names = {row['path'] for row in rows} | {'manifest.json'}
    directories = {str(parent) for name in names for parent in PurePosixPath(name).parents if str(parent) != '.'}
    actual_files, actual_dirs = set(), set()
    for path in archive.rglob('*'):
        require(not path.is_symlink(), 'symlink in archive tree')
        name = path.relative_to(archive).as_posix()
        if path.is_dir():
            actual_dirs.add(name)
        else:
            require(path.is_file(), 'special file in archive tree')
            actual_files.add(name)
    require(actual_files == names and actual_dirs == directories, 'missing or extra archive entries')
    for row in rows:
        data = _bytes(archive, row['path'])
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'],
                'archive bytes differ from fresh generation')
        require(data == _bytes(generated, row['path']), 'archive actual bytes differ')
    return {'shape': shape, 'category': 'passed', 'rtl_files': len(expected['rtl']),
            'manifest_sha256': _identity(archive, 'manifest.json')['sha256'],
            'scope': expected['scope']}
