"""Source-only parser/identity controls; no Rust build or fixture execution."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.reference_model_execution import (
    MODEL_TESTS, GENERIC_TESTS, MODEL_COUNTS, MODEL_ERRORS, GENERIC_ERRORS,
    GENERIC_BASELINES, parse_model, parse_generic, cargo_libraries, alias_hook, bind_generic_negatives, verified_capture, copy_bound_source,
)
from tools.reference_results import ReferenceResultError


def transcript(tests, markers):
    return ('running ' + str(len(tests)) + ' tests\n' +
            ''.join('test ' + name + ' ... ok\n' for name in sorted(tests)) +
            '\n'.join(markers) + '\n' +
            f'test result: ok. {len(tests)} passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s\n')


def model_output():
    return transcript(MODEL_TESTS, [f'{k} {v}' for k, v in MODEL_COUNTS.items()] +
                      [f'MODEL-NEGATIVE {k} {v}' for k, v in MODEL_ERRORS.items()])


def generic_output():
    return transcript(GENERIC_TESTS, [f'GENERIC-BASELINE {name}' for name in sorted(GENERIC_BASELINES)] +
                      [f'GENERIC-NEGATIVE {k} {v}' for k, v in GENERIC_ERRORS.items()])


class ModelExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((ROOT / 'verify/fixtures/fnd-06/semantic_cases.json').read_text())

    def test_capture_tampering_rejected_before_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stdout'
            path.write_bytes(b'original')
            result = SimpleNamespace(stdout_path=path, stdout_bytes=8,
                                     stdout_sha256=hashlib.sha256(b'original').hexdigest())
            self.assertEqual(verified_capture(result), 'original')
            path.write_bytes(b'modified')
            with self.assertRaises(ReferenceResultError):
                verified_capture(result)
            path.write_bytes(b'short')
            with self.assertRaises(ReferenceResultError):
                verified_capture(result)
            path.unlink()
            path.symlink_to('/etc/passwd')
            with self.assertRaises(ReferenceResultError):
                verified_capture(result)

    def test_source_copy_requires_exact_session_hash_including_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'versions.json'
            source.write_bytes(b'{"rust":"1.98.1"}')
            relative = Path('toolchains/versions.json')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(copy_bound_source(source, relative, root / 'copy', {str(relative): digest}), digest)
            for expected in [{}, {str(relative): '0'*64}]:
                with self.assertRaises(ReferenceResultError):
                    copy_bound_source(source, relative, root / 'rejected', expected)
            self.assertFalse((root / 'rejected').exists())

    def test_exact_model_observations(self):
        result = parse_model(model_output(), self.cases, stage='run1-model-execute')
        self.assertEqual(result['tests'], 8)
        self.assertEqual(result['counts']['MODEL-LUT-CASES'], 1048576)
        self.assertEqual(len(result['negatives']), 12)
        self.assertTrue(all(row['executed'] and row['category'] == 'invalid-input' for row in result['negatives']))

    def test_marker_can_share_libtest_test_line(self):
        text = model_output().replace('test exhaustive_lut_independent_bit_table ... ok\n',
                                     'test exhaustive_lut_independent_bit_table ... MODEL-LUT-CASES 1048576\nok\n')
        text = text.replace('\nMODEL-LUT-CASES 1048576\n', '\n')
        self.assertEqual(parse_model(text, self.cases, stage='m')['counts']['MODEL-LUT-CASES'], 1048576)

    def test_model_zero_missing_extra_duplicate_count_rejected(self):
        for altered in [model_output().replace('MODEL-LUT-CASES 1048576', 'MODEL-LUT-CASES 0'),
                        model_output().replace('MODEL-GRAPH-SHAPES 4\n', ''),
                        model_output() + 'MODEL-GRAPH-SHAPES 4\n',
                        model_output() + 'MODEL-UNKNOWN 1\n']:
            with self.subTest(altered=altered[-80:]), self.assertRaises(ReferenceResultError):
                parse_model(altered, self.cases, stage='m')

    def test_model_wrong_or_missing_diagnostic_rejected(self):
        for altered in [model_output().replace('N-OVERLAP Overlap', 'N-OVERLAP Width'),
                        model_output().replace('MODEL-NEGATIVE N-SELECT-Z NonBinary\n', ''),
                        model_output() + 'MODEL-NEGATIVE N-CARRY UnsupportedMode\n']:
            with self.assertRaises(ReferenceResultError):
                parse_model(altered, self.cases, stage='m')

    def test_skipped_failed_missing_test_roster_rejected(self):
        for altered in [model_output().replace('8 passed; 0 failed', '7 passed; 1 failed'),
                        model_output().replace('0 ignored', '1 ignored'),
                        model_output().replace('test asymmetric_literals ... ok\n', ''),
                        model_output() + 'thread panicked at source.rs']:
            with self.assertRaises(ReferenceResultError):
                parse_model(altered, self.cases, stage='m')

    def test_duplicate_oracle_negative_rejected(self):
        cases = copy.deepcopy(self.cases)
        cases['negative_cases'].append(cases['negative_cases'][0])
        with self.assertRaises(ReferenceResultError):
            parse_model(model_output(), cases, stage='m')

    def test_exact_generic_baseline_and_diagnostics(self):
        result = parse_generic(generic_output(), stage='g')
        self.assertEqual(result['tests'], 2)
        self.assertEqual(len(result['baseline']), 3)
        self.assertEqual(len(result['negatives']), 4)
        self.assertEqual(next(r for r in result['negatives'] if r['id'] == 'N-ALIAS-CONFLICT')['generic_diagnostic'], 'Code::Conflict')

    def test_missing_positive_alias_baseline_rejected(self):
        for altered in [generic_output().replace('GENERIC-BASELINE alias-agree\n', ''),
                        generic_output() + 'GENERIC-BASELINE alias-agree\n',
                        generic_output() + 'GENERIC-BASELINE !invalid\n',
                        generic_output().replace('N-THREEWAY-3 Value', 'N-THREEWAY-3 Overlap')]:
            with self.assertRaises(ReferenceResultError):
                parse_generic(altered, stage='g')

    def test_alias_hook_requires_actual_process_and_same_stage(self):
        generic = parse_generic(generic_output(), stage='g')
        generic.update(source_sha256='a'*64, binary_sha256='b'*64,
                       process={'category': 'passed', 'returncode': 0,
                                'stdout_bytes': 1, 'stderr_bytes': 0, 'storage_bytes': 0, 'file_count': 1,
                                'stdout_sha256': 'c'*64, 'stderr_sha256': 'd'*64})
        hook = alias_hook({'generic': generic})
        self.assertEqual(hook['negative']['diagnostic'], 'inconsistent-alias-requests')
        generic['process']['category'] = 'timeout'
        with self.assertRaises(ReferenceResultError):
            alias_hook({'generic': generic})

    def test_required_generic_diagnoses_bind_actual_execution(self):
        model = parse_model(model_output(), self.cases, stage='m')
        generic = parse_generic(generic_output(), stage='g')
        generic.update(source_sha256='a'*64, binary_sha256='b'*64,
                       process={'category': 'passed', 'returncode': 0, 'stdout_bytes': 1,
                                'stderr_bytes': 0, 'storage_bytes': 0, 'file_count': 1,
                                'stdout_sha256': 'c'*64, 'stderr_sha256': 'd'*64})
        bind_generic_negatives(model, generic, self.cases)
        rows = {r['id']: r for r in model['negatives']}
        self.assertEqual(rows['N-OVERLAP']['generic_observation']['id'], 'M-FIELD-ALIAS')
        self.assertEqual(rows['N-THREEWAY-3']['generic_diagnostic'], 'Code::Value')
        generic['negatives'] = [r for r in generic['negatives'] if r['id'] != 'M-FIELD-ALIAS']
        with self.assertRaises(ReferenceResultError):
            bind_generic_negatives(model, generic, self.cases)

    def test_alias_hook_rejects_different_derived_requests(self):
        generic = parse_generic(generic_output(), stage='g')
        generic.update(source_sha256='a'*64, binary_sha256='b'*64,
                       process={'category': 'passed', 'returncode': 0, 'stdout_bytes': 1,
                                'stderr_bytes': 0, 'storage_bytes': 0, 'file_count': 1,
                                'stdout_sha256': 'c'*64, 'stderr_sha256': 'd'*64})
        parent = {'declarations': [{'feature': 'ff', 'bit': 16, 'alias': 'test-alias'},
                                   {'feature': 'source', 'bit': 16, 'alias': 'test-alias'}],
                  'requests': {'ff': 0, 'source': 0}}
        derived = copy.deepcopy(parent)
        derived['requests']['source'] = 1
        digest = lambda value: hashlib.sha256((json.dumps(value, indent=2, sort_keys=True)+'\n').encode()).hexdigest()
        binding = {'id': 'M-ALIAS-CONFLICT', 'target': 'candidate.json',
                   'baseline_sha256': digest(parent), 'derived_sha256': digest(derived)}
        self.assertEqual(alias_hook({'generic': generic}, parent, derived, binding)['stage'], 'g')
        for bad in [{**derived, 'requests': {'ff': 1, 'source': 0}},
                    {**derived, 'requests': {'ff': 0, 'source': 0}}]:
            with self.assertRaises(ReferenceResultError):
                alias_hook({'generic': generic}, parent, bad, binding)
        with self.assertRaises(ReferenceResultError):
            alias_hook({'generic': generic}, parent, derived, {**binding, 'derived_sha256': '0'*64})

    def test_cargo_records_bind_only_current_exact_rlibs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / 'source', root / 'target'
            target.mkdir()
            rows = []
            for name, folder in [('nf_arch_ir', 'arch-ir'), ('nf_types', 'types')]:
                manifest = source / 'core/rust' / folder / 'Cargo.toml'
                manifest.parent.mkdir(parents=True)
                manifest.touch()
                binary = target / ('lib' + name + '.rlib')
                binary.write_bytes(b'test fixture only')
                rows.append({'reason': 'compiler-artifact', 'target': {'name': name, 'kind': ['lib'], 'crate_types': ['lib']},
                             'manifest_path': str(manifest), 'fresh': False, 'filenames': [str(binary)]})
            rows.append({'reason': 'build-finished', 'success': True})
            encode = lambda value: '\n'.join(json.dumps(r) for r in value)
            self.assertEqual(set(cargo_libraries(encode(rows), target, source)), {'nf_arch_ir', 'nf_types'})
            for mutated in [rows[:-1], rows + [rows[0]], [{**rows[0], 'fresh': True}, *rows[1:]],
                            [{**rows[0], 'filenames': ['/outside/libbad.rlib']}, *rows[1:]]]:
                with self.assertRaises(ReferenceResultError):
                    cargo_libraries(encode(mutated), target, source)


if __name__ == '__main__':
    unittest.main()
