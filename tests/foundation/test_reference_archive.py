"""Archive byte/provenance controls; no hardware tools or semantic oracle use."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.reference_archive import ARCHIVE, GENERATORS, verify_archive
from tools.reference_results import ReferenceResultError, portable_rtl_inventory


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.archive = self.root / ARCHIVE / 'one'
        shutil.copytree(ROOT / 'verify/fixtures/nf-tiny', self.root / 'verify/fixtures/nf-tiny')
        shutil.copytree(ROOT / ARCHIVE / 'one', self.archive)
        adapter = self.root / GENERATORS['adapter']
        shutil.copyfile(ROOT / GENERATORS['adapter'], adapter)
        self.generated = Path(self.temp.name) / 'fresh'
        shutil.copytree(self.archive, self.generated)
        metadata = json.loads((self.archive / 'manifest.json').read_text())
        record = {'shape': 'one', 'upstream_commit': metadata['upstream']['commit'],
                  'upstream_tree': metadata['upstream']['tree'],
                  'generator_sources': metadata['generator_sources'],
                  'execution_adjustments': metadata['execution_adjustments']}
        for kind in ('source_rtl', 'generated_rtl'):
            record[kind] = [{'path': r['path'], 'sha256': r['sha256']} for r in metadata['rtl'] if r['kind'] == kind]
        (self.generated / 'generation.json').write_text(json.dumps(record))
        self.inventory = portable_rtl_inventory(self.generated, 'one', expected_generators=record['generator_sources'])

    def verify(self):
        return verify_archive(self.root, 'one', self.generated, self.inventory)

    def test_exact_bytes(self):
        self.assertEqual(self.verify()['rtl_files'], 7)

    def test_missing(self):
        (self.archive / 'Fabric/eFPGA.v').unlink()
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_extra(self):
        (self.archive / 'raw.log').write_text('forbidden')
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_extra_empty_directory(self):
        (self.archive / 'extra').mkdir()
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_modified(self):
        (self.archive / 'Fabric/eFPGA.v').write_text('modified')
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_symlink(self):
        path = self.archive / 'sources.f'
        path.unlink(); path.symlink_to(self.generated / 'sources.f')
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_symlink_parent(self):
        path = self.archive / 'Fabric'
        shutil.rmtree(path); path.symlink_to(self.generated / 'Fabric', target_is_directory=True)
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_manifest_tampering(self):
        path = self.archive / 'manifest.json'
        original = json.loads(path.read_text())
        for field in ('generator_sources', 'upstream', 'original_input_manifest', 'original_inputs'):
            with self.subTest(field=field):
                changed = copy.deepcopy(original); changed[field] = {}
                path.write_text(json.dumps(changed))
                with self.assertRaises(ReferenceResultError): self.verify()
        for name in ('../outside.v', '/absolute.v', 'Fabric//eFPGA.v'):
            with self.subTest(path=name):
                changed = copy.deepcopy(original); changed['rtl'][0]['path'] = name
                path.write_text(json.dumps(changed))
                with self.assertRaises(ReferenceResultError): self.verify()

    def test_fresh_inventory_tampering(self):
        self.inventory['artifacts'][0]['path'] = '../outside'
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_source_identity_changed(self):
        (self.root / GENERATORS['adapter']).write_text('substituted adapter')
        with self.assertRaises(ReferenceResultError): self.verify()

    def test_original_input_changed(self):
        (self.root / 'verify/fixtures/nf-tiny/fabulous/one.csv').write_text('substituted input')
        with self.assertRaises(ReferenceResultError): self.verify()


if __name__ == '__main__':
    unittest.main()
