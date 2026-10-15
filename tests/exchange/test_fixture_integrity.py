"""Independent literal corpus integrity, no candidate imports or regeneration."""
from pathlib import Path
import hashlib
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "verify/fixtures/exchange"
GOLDENS = FIXTURES / "goldens"
ALGORITHM = FIXTURES / "algorithm"


class FixtureIntegrity(unittest.TestCase):
    def test_full_golden_manifest_is_original(self):
        self.assertEqual(hashlib.sha256((GOLDENS / "SHA256SUMS").read_bytes()).hexdigest(),
                         "acfd21c1b776a3565796fad15186db4b0b0993585b1c480bc790841b398ff4b9")

    def test_all_literal_bytes_match_independent_manifests(self):
        for folder in [ALGORITHM, GOLDENS, FIXTURES / "package-cases", FIXTURES / "semantic-cases"]:
            for line in (folder / "SHA256SUMS").read_text().splitlines():
                expected, name = line.split("  ", 1)
                with self.subTest(folder=folder.name, name=name):
                    self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), expected)

    def test_algorithm_vectors_match_original_report(self):
        report = (FIXTURES / "preparation.md").read_text()
        entries = re.findall(r"### (C\d\d).*?Length: (\d+) bytes\. SHA-256: `([0-9a-f]{64})`", report, re.S)
        self.assertEqual(len(entries), 39)
        for name, size, digest in entries:
            with self.subTest(name=name):
                data = (ALGORITHM / (name + ".json")).read_bytes()
                self.assertEqual(len(data), int(size))
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)

    def test_primary_identity_chain_is_independent(self):
        architecture = json.loads((GOLDENS / "architecture.canonical.json").read_bytes())
        package = json.loads((GOLDENS / "package.canonical.json").read_bytes())
        design = json.loads((GOLDENS / "design.canonical.json").read_bytes())
        for name, domain, identity in [
            ("architecture", b"nodal-fpga.arch.semantic.v1\n", architecture["body"]["semantic_id"]),
            ("package", b"nodal-fpga.package.build.v1\n", package["body"]["build_id"]),
            ("design", b"nodal-fpga.design.semantic.v1\n", design["body"]["semantic_id"]),
        ]:
            projection = (GOLDENS / (name + ".projection.json")).read_bytes()
            self.assertEqual(hashlib.sha256(domain + projection).hexdigest(), identity)
        raw = (GOLDENS / "architecture.raw.json").read_bytes()
        self.assertEqual(len(raw), 6624)
        self.assertEqual(package["body"]["architecture"]["artifact"], {
            "bytes": "6624", "sha256": "432171ad8cfc32c3a684584c6af990f8a665a89fcd7c74a03f421490a44601f5"})
        self.assertEqual(package["body"]["architecture"]["artifact"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(package["body"]["architecture"]["semantic_id"], architecture["body"]["semantic_id"])
        self.assertEqual(design["body"]["target_build_id"], package["body"]["build_id"])

    def test_cold_order_and_target_distinctions(self):
        self.assertEqual((GOLDENS / "architecture.projection.json").read_bytes(),
                         (GOLDENS / "architecture-cold-edit.projection.json").read_bytes())
        self.assertNotEqual((GOLDENS / "architecture.raw.json").read_bytes(),
                            (GOLDENS / "architecture-cold-edit.raw.json").read_bytes())
        for prefix in ["package", "design"]:
            suffix = "cold-edit" if prefix == "package" else "cold-target"
            self.assertNotEqual((GOLDENS / (prefix + ".projection.json")).read_bytes(),
                                (GOLDENS / (prefix + "-" + suffix + ".projection.json")).read_bytes())

    def test_hand_declared_primary_semantics(self):
        body = json.loads((GOLDENS / "architecture.canonical.json").read_bytes())["body"]
        self.assertEqual([r["name"] for r in body["roots"]], ["t0", "t1", "t2"])
        self.assertEqual(len(body["templates"]), 1)
        template = body["templates"][0]
        self.assertEqual([r["name"] for r in template["resources"]], ["east", "local", "sink", "west"])
        self.assertEqual([e["resource"]["name"] for e in template["connections"][0]["sources"]], ["east", "local", "west"])
        self.assertEqual(template["features"][0]["domain"], {"kind": "set", "values": ["0", "1", "2"]})
        self.assertEqual([r["domains"][-1]["key"]["local"] for r in body["roots"]], ["power0", "power1", "power1"])
        self.assertEqual(len(body["connections"]), 2)
        self.assertEqual(body["connections"][0]["sources"][0]["resource"]["path"], ["t0"])
        self.assertEqual(body["connections"][0]["destination"]["resource"]["path"], ["t1"])
        self.assertEqual(body["connections"][1]["destination"]["resource"]["path"], ["t2"])


if __name__ == "__main__":
    unittest.main()
