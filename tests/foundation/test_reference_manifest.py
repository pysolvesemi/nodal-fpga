"""Manifest-only checks. These never execute reference HDL or a generator."""
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fnd06_manifest", ROOT / "verify/fixtures/fnd-06/manifest.py")
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)


class ReferenceManifestTests(unittest.TestCase):
    def setUp(self):
        self.bundle = manifest.load(ROOT)

    def test_exact_frozen_contract_and_counts(self):
        self.assertEqual(len(manifest.expected_records(self.bundle, "formal")), 29)
        self.assertEqual(len(manifest.expected_records(self.bundle, "simulation")), 1847)
        self.assertEqual(len(manifest.expected_records(self.bundle, "structural")), 1035)

    def test_literal_onehot_identity_and_frame_placement(self):
        for row in self.bundle["semantic_cases"]["onehot"]:
            self.assertEqual(row["expected"], int(row["init_hex"], 16) == 2 ** row["address"])
        for row in self.bundle["semantic_cases"]["instance_words"]:
            self.assertEqual(row["frame0_hex"], row["config_hex"] + "000")
        for row in self.bundle["semantic_cases"]["walking_storage"]:
            self.assertEqual([1 - bit for bit in row["q_lsb_first"]], row["qn_lsb_first"])
            self.assertEqual(row["frame0_hex"], row["config_hex"] + "000")

    def test_missing_duplicate_and_same_count_substitution_rejected(self):
        for change in ["missing", "duplicate", "substitute", "category", "literal"]:
            with self.subTest(change=change):
                b = copy.deepcopy(self.bundle)
                rows = b["obligations"]["formal"]
                if change == "missing": rows.pop()
                elif change == "duplicate": rows[-1] = rows[0]
                elif change == "substitute": rows[-1]["id"] = "C-INVENTED"
                elif change == "category": rows[-1]["expected_category"] = "compile-error"
                else: b["semantic_cases"]["onehot"][0]["expected"] = 0
                with self.assertRaises(manifest.ManifestError):
                    manifest.validate_bundle(b)

    def test_missing_mutant_or_shape_rejected(self):
        for key in ["mutant", "shape"]:
            b = copy.deepcopy(self.bundle)
            if key == "mutant": b["mutations"]["mutations"].pop()
            else: b["obligations"]["instances"].pop()
            with self.assertRaises(manifest.ManifestError): manifest.validate_bundle(b)

    def test_leaf_and_inherited_ids_remain_exact(self):
        expected = {"a.1", "a.2", "b.1", "b.2", "b.3", "c.1", "c.2", "d.1", "d.2", "d.3", "f.1", "f.2", "g.1", "g.2", "e.1", "e.2", "e.3"}
        self.assertEqual({r["id"] for r in self.bundle["obligations"]["leaves"]}, {"FND-06." + x for x in expected})
        import json
        original = json.loads((ROOT / "verify/fixtures/nf-tiny/specification.json").read_text())
        self.assertEqual(original["obligations"], self.bundle["obligations"]["inherited_obligations"])


if __name__ == "__main__": unittest.main()
