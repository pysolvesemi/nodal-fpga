"""Bounded model/generic-API builds followed by isolated binary execution.

The standalone model is independent; generic production APIs are separate DUTs.
No Rust compiler, Cargo cache or linker is mounted into the hardware runtime.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil

try:
    from .reference_runner import Limits, run_bounded
    from .reference_results import require, verify_process
except ImportError:
    from reference_runner import Limits, run_bounded
    from reference_results import require, verify_process

MODEL_TESTS = {
    'exhaustive_lut_independent_bit_table', 'asymmetric_literals',
    'exhaustive_register_edges_and_modes', 'literal_register_traces',
    'mux_literal_cases_and_reserved_code', 'literal_config_and_all_bindings',
    'named_invalid_input_categories', 'independently_enumerated_tiny_reachability',
}
GENERIC_TESTS = {'exact_ff_source_alias_conflict_and_overlap', 'exact_threeway_reserved_three'}
MODEL_COUNTS = {'MODEL-LUT-CASES': 1048576, 'MODEL-REGISTER-CASES': 96, 'MODEL-GRAPH-SHAPES': 4}
MODEL_ERRORS = {
    'N-CARRY': 'UnsupportedMode', 'N-SOURCE-RANGE': 'MuxSelection',
    'N-INIT-WIDTH': 'Width', 'N-UNKNOWN-FEATURE': 'Unsupported',
    'N-MISSING-FEATURE': 'Missing', 'N-OVERLAP': 'Overlap',
    'N-SELECT-X': 'NonBinary', 'N-SELECT-Z': 'NonBinary',
    'N-PACKAGE': 'Package', 'N-PADDING-ADDRESS': 'Address',
    'N-ALIAS-CONFLICT': 'Alias', 'N-THREEWAY-3': 'MuxSelection',
}
GENERIC_ERRORS = {'M-FIELD-ALIAS': 'Overlap', 'M-ALIAS-CONFLICT': 'Conflict',
                  'N-ALIAS-CONFLICT': 'Conflict', 'N-THREEWAY-3': 'Value'}
GENERIC_BASELINES = {'independent-ff-source', 'alias-agree', 'threeway-legal'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verified_capture(result, stream='stdout'):
    require(stream in {'stdout', 'stderr'}, 'unknown model capture stream')
    path = Path(getattr(result, stream + '_path'))
    count = getattr(result, stream + '_bytes')
    require(type(count) is int and 0 <= count <= 16 * 1024**2,
            'invalid/excessive model capture size')
    require(path.is_file() and not path.is_symlink() and path.stat().st_size == count,
            'model capture length/type differs')
    data = path.read_bytes()
    require(len(data) == count and hashlib.sha256(data).hexdigest() == getattr(result, stream + '_sha256'),
            'model capture hash differs')
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        require(False, 'model capture is not UTF-8')


def copy_bound_source(path, relative, destination, expected):
    require(path.is_file() and not path.is_symlink(), 'nonregular Rust model input')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(expected.get(str(relative)) == digest, 'model source differs from session source binding')
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return digest


def verify_test_harness(output: str, expected: set[str]):
    require(len(output) <= 16 * 1024**2, 'excessive model output')
    names = re.findall(r'^test ([A-Za-z0-9_:]+) \.\.\. ', output, re.M)
    require(len(names) == len(set(names)) and set(names) == expected,
            'Rust fixture test identities missing, duplicate or unexpected')
    summaries = re.findall(r'^test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;', output, re.M)
    require(summaries == [(str(len(expected)), '0', '0', '0', '0')],
            'Rust fixture summary missing, zero, skipped or failed')
    require(not re.search(r'^test result: FAILED|\bpanicked at\b', output, re.M),
            'Rust fixture panicked or failed')


def marked_pairs(output: str, prefix: str, expected: dict[str, str]):
    rows = re.findall(r'\b' + re.escape(prefix) + r' ([A-Z0-9-]+) ([A-Za-z]+)\b', output)
    require(len(rows) == len(expected) and len({r[0] for r in rows}) == len(rows),
            prefix + ' missing/duplicate observations')
    require(dict(rows) == expected, prefix + ' wrong exact identity/diagnostic')
    require(len(re.findall(r'\b' + re.escape(prefix) + r'\b', output)) == len(rows),
            prefix + ' malformed marker')
    return dict(rows)


def parse_model(output: str, semantic_cases: dict, *, stage: str):
    verify_test_harness(output, MODEL_TESTS)
    counts = {}
    for marker, expected in MODEL_COUNTS.items():
        values = re.findall(r'\b' + re.escape(marker) + r' (\d+)\b', output)
        require(values == [str(expected)], marker + ' missing/duplicate/wrong count')
        counts[marker] = int(values[0])
    require(set(re.findall(r'\bMODEL-[A-Z0-9-]+', output)) == set(MODEL_COUNTS) | {'MODEL-NEGATIVE'},
            'unexpected model record type')
    errors = marked_pairs(output, 'MODEL-NEGATIVE', MODEL_ERRORS)
    oracle_rows = [row for row in semantic_cases['negative_cases'] if row['harness'] == 'model.rs']
    require(len(oracle_rows) == len(MODEL_ERRORS), 'model negative oracle count differs')
    oracle = {row['id']: row for row in oracle_rows}
    require(set(oracle) == set(MODEL_ERRORS), 'model negative oracle roster differs')
    negatives = []
    for identifier in sorted(errors):
        row = oracle[identifier]
        require(row['expected_category'] == 'invalid-input', 'unexpected model rejection category')
        negatives.append({'id': identifier, 'category': 'invalid-input', 'executed': True,
                          'stage': stage, 'diagnostic': row['diagnostic'],
                          'observed_model_diagnostic': errors[identifier]})
    return {'tests': len(MODEL_TESTS), 'counts': counts, 'negatives': negatives, 'stage': stage}


def parse_generic(output: str, *, stage: str):
    verify_test_harness(output, GENERIC_TESTS)
    errors = marked_pairs(output, 'GENERIC-NEGATIVE', GENERIC_ERRORS)
    baselines = re.findall(r'\bGENERIC-BASELINE ([a-z-]+)\b', output)
    require(len(re.findall(r'\bGENERIC-BASELINE\b', output)) == len(GENERIC_BASELINES),
            'malformed generic baseline marker')
    require(len(baselines) == len(GENERIC_BASELINES) and set(baselines) == GENERIC_BASELINES,
            'generic baseline observations missing/duplicate/unexpected')
    require(set(re.findall(r'\bGENERIC-[A-Z-]+', output)) == {'GENERIC-BASELINE', 'GENERIC-NEGATIVE'},
            'unexpected generic record type')
    return {'tests': len(GENERIC_TESTS), 'baseline': [
                {'id': name, 'category': 'passed', 'executed': True, 'stage': stage}
                for name in sorted(baselines)],
            'negatives': [{'id': name, 'category': 'invalid-input', 'executed': True,
                           'stage': stage, 'generic_diagnostic': 'Code::' + errors[name]}
                          for name in sorted(errors)], 'stage': stage}


def bind_generic_negatives(model, generic, semantic_cases):
    """Required generic API diagnoses supplement, never replace, model semantics."""
    mapping = {'N-OVERLAP': 'M-FIELD-ALIAS', 'N-ALIAS-CONFLICT': 'N-ALIAS-CONFLICT',
               'N-THREEWAY-3': 'N-THREEWAY-3'}
    expected = {row['id']: row['generic_diagnostic'] for row in semantic_cases['negative_cases']
                if 'generic_diagnostic' in row}
    require(set(expected) == set(mapping), 'generic semantic obligation roster differs')
    actual = {row['id']: row for row in generic['negatives']}
    verify_process(generic['process'])
    for row in model['negatives']:
        if row['id'] not in mapping:
            continue
        witness = actual.get(mapping[row['id']])
        require(witness is not None and witness.get('executed') is True
                and witness.get('category') == 'invalid-input'
                and witness.get('generic_diagnostic') == expected[row['id']],
                'missing actual required generic diagnostic')
        row['generic_diagnostic'] = witness['generic_diagnostic']
        row['generic_observation'] = {**witness, 'process': generic['process'],
                                      'source_sha256': generic['source_sha256'],
                                      'binary_sha256': generic['binary_sha256']}


def cargo_libraries(output: str, target: Path, source: Path):
    """Use actual compiler-artifact records, never glob an old target directory."""
    wanted = {'nf_arch_ir': source / 'core/rust/arch-ir/Cargo.toml',
              'nf_types': source / 'core/rust/types/Cargo.toml'}
    found = {}
    finished = []
    for line in output.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            require(False, 'malformed Cargo machine output')
        if row.get('reason') == 'compiler-artifact':
            name = row.get('target', {}).get('name')
            require(name in wanted and name not in found, 'unexpected/duplicate Cargo artifact')
            require(row['target']['kind'] == ['lib'] and row['target']['crate_types'] == ['lib'],
                    'nonlibrary/proc-macro build artifact')
            require(Path(row['manifest_path']).resolve() == wanted[name].resolve(),
                    'Cargo artifact source differs')
            require(row.get('fresh') is False, 'fresh target unexpectedly reused prior build')
            paths = [Path(p).resolve() for p in row.get('filenames', []) if p.endswith('.rlib')]
            require(len(paths) == 1 and paths[0].is_relative_to(target.resolve())
                    and paths[0].is_file() and not paths[0].is_symlink(),
                    'Cargo rlib absent or outside current build')
            found[name] = paths[0]
        elif row.get('reason') == 'build-finished':
            finished.append(row.get('success'))
        else:
            require(row.get('reason') == 'compiler-message'
                    and row.get('message', {}).get('level') != 'error',
                    'unexpected Cargo message or error')
    require(set(found) == set(wanted) and finished == [True], 'incomplete Cargo build closure')
    return found


def run_models(session):
    """Call only after coordinator execution GO; all input artifacts are bound."""
    root = Path(session.root)
    build = Path(session.output) / 'model-build'
    build.mkdir(parents=True, exist_ok=False)
    work = build / 'work'
    work.mkdir()
    source = work / 'source'
    source.mkdir()
    # Immutable narrow source snapshot. No workspace config/build caches copied.
    paths = [root / 'Cargo.toml', root / 'Cargo.lock', root / 'rust-toolchain.toml',
             root / 'toolchains/versions.json']
    paths += sorted((root / 'core/rust').rglob('*.rs'))
    paths += sorted((root / 'core/rust').rglob('Cargo.toml'))
    paths += [root / 'verify/fixtures/fnd-06' / name for name in ['model.rs', 'generic_api.rs', 'semantic_cases.json']]
    source_hashes = {}
    for path in paths:
        relative = path.relative_to(root)
        source_hashes[str(relative)] = copy_bound_source(
            path, relative, source, session.source['input_sha256'])
    version = json.loads((source / 'toolchains/versions.json').read_text())['rust']
    cache = Path(os.environ.get('NF_TOOL_CACHE', root / '.cache/toolchains')).resolve()
    rust = cache / 'rustup/toolchains' / (version + '-x86_64-unknown-linux-gnu')
    rustc, cargo = rust / 'bin/rustc', rust / 'bin/cargo'
    require(rustc.is_file() and cargo.is_file(), 'missing pinned model build toolchain')
    home = work / 'home'
    home.mkdir()
    tmp = work / 'tmp'
    tmp.mkdir()
    target = work / 'target'
    # Direct pinned binaries avoid rustup downloads, shell sourcing, and reference
    # or Scala PATH pollution. Cargo's existing cache is consumed offline only.
    env = {'PATH': str(rust / 'bin') + ':/usr/bin:/bin', 'HOME': str(home),
           'TMPDIR': str(tmp), 'LANG': 'C', 'LC_ALL': 'C',
           'CARGO_HOME': str(cache / 'cargo'), 'RUSTUP_HOME': str(cache / 'rustup'),
           'RUSTC': str(rustc), 'CARGO_NET_OFFLINE': 'true', 'CARGO_INCREMENTAL': '0',
           'CARGO_BUILD_JOBS': '1', 'CARGO_TARGET_DIR': str(target)}
    records = []
    def execute(name, argv):
        result = run_bounded(argv, output_dir=build / name, work_dir=work, cwd=source,
                             env=env, limits=Limits(wall_seconds=180, cpu_seconds=180,
                                                   storage_bytes=512 * 1024**2))
        records.append({'id': name, 'process': result.portable(), 'command': argv})
        (build / 'local-build.json').write_text(json.dumps({'source': session.source,
            'source_sha256': source_hashes, 'rustc_sha256': sha(rustc), 'cargo_sha256': sha(cargo),
            'profile': 'separate pinned Rust model build; offline Cargo; no reference PATH',
            'environment': env, 'records': records}, indent=2) + '\n')
        verified_capture(result, 'stdout')
        verified_capture(result, 'stderr')
        verify_process(result.portable())
        return result
    for name, executable in [('rustc', rustc), ('cargo', cargo)]:
        result = execute(name + '-identity', [str(executable), '--version'])
        require(re.match(re.escape(name + ' ' + version) + r'\b', verified_capture(result)) is not None,
                'model compiler version differs from pin')
    binary_dir = work / 'binaries'
    binary_dir.mkdir()
    fixture = source / 'verify/fixtures/fnd-06'
    execute('compile-model', [str(rustc), '--edition=2024', '--test', '-D', 'warnings',
                             str(fixture / 'model.rs'), '-o', str(binary_dir / 'model-tests')])
    cargo_result = execute('build-generic-dependencies', [str(cargo), 'build', '--locked', '--offline',
                             '--message-format=json', '-p', 'nf-arch-ir', '--lib'])
    libraries = cargo_libraries(verified_capture(cargo_result), target, source)
    execute('compile-generic', [str(rustc), '--edition=2024', '--test', '-D', 'warnings',
                               str(fixture / 'generic_api.rs'), '-L', 'dependency=' + str(target / 'debug/deps'),
                               '--extern', 'nf_arch_ir=' + str(libraries['nf_arch_ir']),
                               '--extern', 'nf_types=' + str(libraries['nf_types']),
                               '-o', str(binary_dir / 'generic-tests')])
    # Mount only the exact executables, never their compiler/rlib/cache roots.
    results = {}
    repeats = []
    for repeat in (1, 2):
        current = {}
        for kind, executable in [('model', 'model-tests'), ('generic', 'generic-tests')]:
            stage = f'run{repeat}-{kind}-execute'
            binary_hash = sha(binary_dir / executable)
            result, _ = session.execute(stage, ['/inputs/model/' + executable, '--nocapture', '--test-threads=1'],
                                        inputs={'/inputs/model': binary_dir})
            require(sha(binary_dir / executable) == binary_hash, 'executed model binary changed')
            verified_capture(result, 'stderr')
            parsed = (parse_model(verified_capture(result), json.loads((fixture / 'semantic_cases.json').read_text()), stage=stage)
                      if kind == 'model' else parse_generic(verified_capture(result), stage=stage))
            parsed.update({'process': result.portable(), 'source_sha256': source_hashes[
                'verify/fixtures/fnd-06/' + ('model.rs' if kind == 'model' else 'generic_api.rs')],
                'binary_sha256': binary_hash})
            current[kind] = parsed
        bind_generic_negatives(current['model'], current['generic'],
                               json.loads((fixture / 'semantic_cases.json').read_text()))
        repeats.append(current)
    def semantic(value):
        if isinstance(value, dict):
            return {key: semantic(item) for key, item in value.items() if key not in {'stage', 'process'}}
        if isinstance(value, list):
            return [semantic(item) for item in value]
        return value
    require(semantic(repeats[0]) == semantic(repeats[1]), 'model/generic repeated semantic observations differ')
    results.update(repeats[0])
    results['repeats'] = repeats
    results['determinism'] = {'executed_runs': 2, 'identical_semantic_observations': True,
                              'scope': 'same exact prebuilt binaries, fresh isolated runs; not a second compilation'}
    results['builds'] = [{'id': row['id'], 'process': row['process']} for row in records]
    results['build_source_sha256'] = source_hashes
    results['library_sha256'] = {name: sha(path) for name, path in libraries.items()}
    (Path(session.output) / 'model-results.json').write_text(json.dumps(results, indent=2) + '\n')
    results['alias_hook'] = lambda baseline_input=None, derived_input=None, binding=None: alias_hook(
        results, baseline_input, derived_input, binding)
    return results


def alias_hook(model_results, baseline_input=None, derived_input=None, binding=None):
    """Actual same-run alias witnesses for the semantic-mutation orchestrator."""
    if any(value is not None for value in (baseline_input, derived_input, binding)):
        require(all(value is not None for value in (baseline_input, derived_input, binding)),
                'incomplete fresh alias derivative binding')
        def encode(value):
            return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
        parent_bytes = baseline_input if isinstance(baseline_input, bytes) else encode(baseline_input)
        parent = json.loads(parent_bytes)
        expected = {'declarations': [{'feature': 'ff', 'bit': 16, 'alias': 'test-alias'},
                                     {'feature': 'source', 'bit': 16, 'alias': 'test-alias'}],
                    'requests': {'ff': 0, 'source': 0}}
        require(parent == expected, 'alias baseline does not match actual generic agreeing request')
        expected['requests']['source'] = 1
        require(derived_input == expected, 'alias derivative does not match actual generic conflict request')
        require(binding.get('id') == 'M-ALIAS-CONFLICT' and binding.get('target') == 'candidate.json'
                and binding.get('baseline_sha256') == hashlib.sha256(parent_bytes).hexdigest()
                and binding.get('derived_sha256') == hashlib.sha256(encode(derived_input)).hexdigest(),
                'fresh alias derivative bytes differ from binding')
    generic = model_results['generic']
    baseline = next((r for r in generic['baseline'] if r['id'] == 'alias-agree'), None)
    negative = next((r for r in generic['negatives'] if r['id'] == 'N-ALIAS-CONFLICT'), None)
    require(baseline is not None and negative is not None, 'missing executed generic alias witnesses')
    require(baseline['executed'] and negative['executed'] and baseline['stage'] == negative['stage'],
            'unbound generic alias witnesses')
    verify_process(generic['process'])
    return {'baseline': baseline, 'negative': {**negative, 'diagnostic': 'inconsistent-alias-requests'},
            'source_sha256': generic['source_sha256'], 'binary_sha256': generic['binary_sha256'],
            'stage': generic['stage'], 'process': generic['process']}
