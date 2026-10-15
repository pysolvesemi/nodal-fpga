"""Missing and forged reference results never receive semantic test credit."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from reference_results import ReferenceResultError, exact_roster, portable_rtl_inventory, verify_process


class ReferenceResultControls(unittest.TestCase):
    def setUp(self):
        self.expected = [{"id": "A", "expected_category": "passed", "multiplicity": 1},
                         {"id": "B", "expected_category": "cover-reached", "multiplicity": 1}]
        self.actual = [{"id": "A", "category": "passed", "executed": True, "stage": "proof"},
                       {"id": "B", "category": "cover-reached", "executed": True, "stage": "cover"}]

    def test_exact_complete_roster(self):
        self.assertEqual(exact_roster(self.expected, self.actual, section="formal")["passed"], 2)

    def test_missing_duplicate_extra_or_substituted_identity(self):
        cases = [self.actual[:1], self.actual + self.actual[:1],
                 [self.actual[0], dict(self.actual[1], id="C")], []]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ReferenceResultError):
                exact_roster(self.expected, case, section="formal")

    def test_same_counts_wrong_result_or_no_execution(self):
        for change in [{"category": "timeout"}, {"category": "passed"},
                       {"executed": False}, {"executed": 1}, {"stage": ""}]:
            case = copy.deepcopy(self.actual)
            case[1].update(change)
            with self.subTest(change=change), self.assertRaises(ReferenceResultError):
                exact_roster(self.expected, case, section="formal")

    def test_invalid_oracle_roster(self):
        for case in [[], self.expected + self.expected[:1],
                     [dict(self.expected[0], multiplicity=2)], [{"id": "A"}]]:
            with self.subTest(case=case), self.assertRaises(ReferenceResultError):
                exact_roster(case, self.actual, section="formal")

    def test_only_intended_normal_process_status(self):
        digest = hashlib.sha256(b"").hexdigest()
        record = dict(category="passed", returncode=0, stdout_bytes=0, stderr_bytes=0,
                      storage_bytes=0, file_count=0, stdout_sha256=digest, stderr_sha256=digest)
        verify_process(record)
        negative = dict(record, category="tool-error", returncode=1)
        verify_process(negative, expected_exit=1)
        for delta in [{"category": "timeout"}, {"category": "output-limit"},
                      {"returncode": -9}, {"returncode": True}, {"stdout_bytes": -1},
                      {"stdout_sha256": "missing"}]:
            with self.subTest(delta=delta), self.assertRaises(ReferenceResultError):
                verify_process(dict(record, **delta))
        with self.assertRaises(ReferenceResultError):
            verify_process(dict(record, category="tool-error", returncode=-9), expected_exit=-9)

    def test_actual_portable_inventory_and_failure_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.v").write_bytes(b"module source; endmodule\n")
            (root / "generated.v").write_bytes(b"module generated; endmodule\n")
            (root / "sources.f").write_text("source.v\ngenerated.v\n")
            record = {"shape": "one", "upstream_commit": "a" * 40,
                      "upstream_tree": "b" * 40,
                      "private_ignored_metadata": "/private/local-only",
                      "source_rtl": [{"path": "source.v", "sha256": hashlib.sha256((root / "source.v").read_bytes()).hexdigest()}],
                      "generated_rtl": [{"path": "generated.v", "sha256": hashlib.sha256((root / "generated.v").read_bytes()).hexdigest()}]}
            manifest = root / "generation.json"
            manifest.write_text(json.dumps(record))
            result = portable_rtl_inventory(root, "one")
            self.assertEqual(len(result["artifacts"]), 2)
            self.assertNotIn("private_ignored_metadata", result)
            generators = {"historical": {"path": "old.py", "sha256": "c" * 64},
                          "adapter": {"path": "new.py", "sha256": "d" * 64}}
            with self.assertRaises(ReferenceResultError):
                portable_rtl_inventory(root, "one", expected_generators=generators)
            adapter_record = dict(record, generator_sources=generators,
                execution_adjustments=["create-official-project-marker-before-init-context"])
            manifest.write_text(json.dumps(adapter_record))
            self.assertEqual(portable_rtl_inventory(root, "one", expected_generators=generators)
                             ["generator_sources"], generators)
            adapter_record["execution_adjustments"] = ["unexpected-adjustment"]
            manifest.write_text(json.dumps(adapter_record))
            with self.assertRaises(ReferenceResultError):
                portable_rtl_inventory(root, "one", expected_generators=generators)
            adapter_record["execution_adjustments"] = ["create-official-project-marker-before-init-context"]
            adapter_record["generator_sources"] = copy.deepcopy(generators)
            adapter_record["generator_sources"]["adapter"]["sha256"] = "e" * 64
            manifest.write_text(json.dumps(adapter_record))
            with self.assertRaises(ReferenceResultError):
                portable_rtl_inventory(root, "one", expected_generators=generators)
            for mutate in [lambda x: x.update(shape="other"),
                           lambda x: x["generated_rtl"][0].update(sha256="0" * 64),
                           lambda x: x["generated_rtl"][0].update(path="../escape"),
                           lambda x: x["generated_rtl"].extend(x["source_rtl"])]:
                changed = copy.deepcopy(record); mutate(changed)
                manifest.write_text(json.dumps(changed))
                with self.assertRaises(ReferenceResultError):
                    portable_rtl_inventory(root, "one")
            manifest.write_text(json.dumps(record))
            (root / "sources.f").write_text("source.v\n")
            with self.assertRaises(ReferenceResultError):
                portable_rtl_inventory(root, "one")


if __name__ == "__main__":
    unittest.main()
