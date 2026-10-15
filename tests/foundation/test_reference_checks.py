"""Coordinator rejects changed source, incomplete suites and fake repeats."""
import copy
import hashlib
from types import SimpleNamespace
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from reference_checks import compare_repeats, fixture_module, observation, source_identity, validate_run, input_inventory, obligation_coverage, Session
from reference_results import ReferenceResultError


class CoordinatorControls(unittest.TestCase):
    def test_repeat_compares_actual_artifact_identities(self):
        first = {shape: {'artifacts': [{'path': 'x.v', 'sha256': 'a'*64}]}
                 for shape in ('one', 'square', 'odd', 'sparse')}
        self.assertTrue(compare_repeats(first, copy.deepcopy(first))['actual_rtl_and_source_lists_byte_identical'])
        second = copy.deepcopy(first)
        second['odd']['artifacts'][0]['sha256'] = 'b'*64
        with self.assertRaises(ReferenceResultError): compare_repeats(first, second)
        second = copy.deepcopy(first); del second['odd']
        with self.assertRaises(ReferenceResultError): compare_repeats(first, second)

    def test_each_run_has_exact_identity_set(self):
        manifest = fixture_module(ROOT, 'manifest')
        bundle = manifest.load(ROOT)
        result = {section: [observation(row['id'], 'synthetic-control', category=row['expected_category'])
                            for row in manifest.expected_records(bundle, section).values()]
                  for section in ('structural', 'simulation', 'supplemental_simulation', 'formal')}
        self.assertEqual(validate_run(bundle, result)['simulation']['passed'], 1847)
        result['formal'][0]['id'] = 'substituted-with-equal-count'
        with self.assertRaises(ReferenceResultError): validate_run(bundle, result)

    def test_session_verifies_actual_capture_bytes_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            stdout, stderr = output / 'stdout', output / 'stderr'
            stdout.write_bytes(b'valid'); stderr.write_bytes(b'')
            portable = dict(category='passed', returncode=0, stdout_bytes=5, stderr_bytes=0,
                            stdout_sha256=hashlib.sha256(b'valid').hexdigest(),
                            stderr_sha256=hashlib.sha256(b'').hexdigest(), storage_bytes=0, file_count=0)
            result = SimpleNamespace(portable=lambda: portable, stdout_path=stdout, stderr_path=stderr)
            environment = SimpleNamespace(source_inventory={}, runtime_inventory_sha256='a'*64,
                                          run=lambda *args, **kwargs: result)
            session = Session(ROOT, output, environment)
            session.execute('valid', ['synthetic-control'])
            stdout.write_bytes(b'other')
            with self.assertRaises(ReferenceResultError):
                session.execute('tampered', ['synthetic-control'])

    def test_inherited_obligations_require_named_executed_witnesses(self):
        manifest = fixture_module(ROOT, 'manifest')
        bundle = manifest.load(ROOT)
        records = [observation(row['id'], 'synthetic-control', category=row['expected_category'])
                   for section in ('structural', 'simulation', 'supplemental_simulation', 'formal',
                                   'semantic', 'mutations', 'controls')
                   for row in manifest.expected_records(bundle, section).values()]
        coverage = obligation_coverage(ROOT, bundle, records)
        self.assertEqual(coverage['inherited_executed'], 15)
        self.assertTrue(any(row['assumptions'] for group in coverage['obligations'].values() for row in group))
        with self.assertRaises(ReferenceResultError): obligation_coverage(ROOT, bundle, [])
        records[0]['executed'] = False
        with self.assertRaises(ReferenceResultError): obligation_coverage(ROOT, bundle, records)

    def test_stage_inputs_bind_actual_bytes_and_reject_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'x.v').write_text('first')
            first = input_inventory({'/inputs/generated': root})
            (root / 'x.v').write_text('second')
            self.assertNotEqual(first, input_inventory({'/inputs/generated': root}))
            (root / 'alias.v').symlink_to(root / 'x.v')
            with self.assertRaises(ReferenceResultError):
                input_inventory({'/inputs/generated': root})

    def test_source_identity_includes_new_implementation(self):
        source = source_identity(ROOT)
        self.assertIn('tools/reference_checks.py', source['input_sha256'])
        self.assertIn('verify/fixtures/fnd-06/obligations.json', source['input_sha256'])
        self.assertNotIn('platform', source)
        self.assertNotIn('uid', source)

if __name__ == '__main__': unittest.main()
