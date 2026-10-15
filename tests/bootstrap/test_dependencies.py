"""Adversarial checks for reviewed exchange-only registry boundaries.

Metadata fixtures test the validator independently; actual archive/source hashes
are exercised against real Cargo metadata before builds in the Rust profile.
"""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_boundaries as boundary
import dependency_inventory as inventory


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for file in ["Cargo.toml", "Cargo.lock", "tools/ownership.json", "tools/dependencies/rust-registry.json"]:
            target = self.root / file
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / file, target)
        self.policy = json.loads((self.root / "tools/ownership.json").read_text())
        for package in self.policy["core_packages"]:
            shutil.copytree(ROOT / package["path"], self.root / package["path"])
        self.records = inventory.load(self.root)

    def replace(self, path, old, new):
        file = self.root / path
        original = file.read_text()
        self.assertIn(old, original)
        file.write_text(original.replace(old, new))

    def rejects(self, code):
        with self.assertRaisesRegex(boundary.BoundaryError, code):
            boundary.check(self.root)

    def test_exact_pins_and_lock_pass_static_gate(self):
        boundary.check(self.root)

    def test_registry_name_alone_does_not_authorize_version_source_or_feature(self):
        path = "core/rust/exchange/Cargo.toml"
        original = (self.root / path).read_text()
        for old, new in [('=1.0.229', '^1.0.229'), ('=1.0.229', '=1.0.228'),
                         ('["std", "derive"]', '["std", "derive", "rc"]'),
                         ('default-features = false', 'default-features = true'),
                         ('serde =', 'renamed ='), ('[dependencies]', '[dev-dependencies]'),
                         ('[dependencies]', '[target.\'cfg(unix)\'.dependencies]'),
                         ('version = "=1.0.229"', 'version = "=1.0.229", registry = "alternate"'),
                         ('version = "=1.0.229"', 'version = "=1.0.229", optional = true')]:
            with self.subTest(new=new):
                (self.root / path).write_text(original)
                self.replace(path, old, new)
                self.rejects("NF-OWN-DEPENDENCY")

    def test_types_and_archir_cannot_gain_reviewed_registry_name(self):
        for crate in ["types", "arch-ir"]:
            path = self.root / f"core/rust/{crate}/Cargo.toml"
            text = path.read_text()
            if "[dependencies]" in text:
                text = text.replace("[dependencies]", '[dependencies]\nserde = "=1.0.229"')
            else:
                text += '\n[dependencies]\nserde = "=1.0.229"\n'
            path.write_text(text)
            self.rejects("NF-OWN-DEPENDENCY")
            shutil.copyfile(ROOT / path.relative_to(self.root), path)

    def test_lock_checksum_version_source_and_graph_are_exact(self):
        file = self.root / "Cargo.lock"
        original = file.read_text()
        first = self.records["lock_packages"][0]
        for old, new in [(first["checksum"], "0" * 64),
                         ('version = "0.10.4"', 'version = "0.10.5"'),
                         (inventory.REGISTRY, 'registry+https://example.invalid'),
                         (' "generic-array",', ' "libc",')]:
            with self.subTest(new=new):
                file.write_text(original)
                self.replace("Cargo.lock", old, new)
                self.rejects("NF-OWN-LOCK")

    def test_inventory_duplicate_identity_is_rejected(self):
        data = copy.deepcopy(self.records)
        data["packages"][1] = copy.deepcopy(data["packages"][0])
        (self.root / "tools/dependencies/rust-registry.json").write_text(json.dumps(data))
        self.rejects("NF-OWN-POLICY")

    def fixture(self):
        # Full declarations/target/resolve fixture, without requiring a network
        # or Cargo cache in the contracts-only job. The two hash functions below
        # stand in ONLY for external files, never for metadata or graph decisions.
        data = {"packages": [], "resolve": {"nodes": copy.deepcopy(self.records["nodes"])}}
        paths = {}
        for record in self.records["packages"]:
            package = copy.deepcopy(record["metadata"])
            directory = self.root / "registry/src/test-cache" / (package["name"] + "-" + package["version"])
            directory.mkdir(parents=True)
            package["manifest_path"] = str(directory / "Cargo.toml")
            for target in package["targets"]:
                target["src_path"] = str(directory / target["src_path"])
            archive = self.root / "registry/cache/test-cache" / (directory.name + ".crate")
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive.write_bytes(b"independent fixture archive")
            paths[directory.name] = record
            data["packages"].append(package)
        for local in self.policy["core_packages"]:
            data["packages"].append({"name": local["name"], "id": local["name"], "source": None, "dependencies": []})
            data["resolve"]["nodes"].append({"id": local["name"], "features": [], "dependencies": [], "deps": []})
        package = next(p for p in data["packages"] if p["name"] == "nf-exchange")
        node = next(n for n in data["resolve"]["nodes"] if n["id"] == "nf-exchange")
        for name, version, features, defaults in [
                ("serde", "1.0.229", ["std", "derive"], False),
                ("serde_json", "1.0.154", ["std"], False),
                ("serde_path_to_error", "0.1.20", [], True),
                ("sha2", "0.10.9", ["std", "force-soft"], False)]:
            identifier = f"{inventory.REGISTRY}#{name}@{version}"
            package["dependencies"].append({"name": name, "source": inventory.REGISTRY,
                "req": "=" + version, "kind": None, "rename": None, "optional": False,
                "uses_default_features": defaults, "features": features, "target": None, "registry": None})
            node["dependencies"].append(identifier)
            node["deps"].append({"name": name, "pkg": identifier, "dep_kinds": [{"kind": None, "target": None}]})
        node["dependencies"].sort()
        return data, paths

    def check_fixture(self, data, paths):
        local = {p["name"]: p for p in self.policy["core_packages"]}
        with patch.object(inventory, "digest", side_effect=lambda path: paths[path.name.removesuffix(".crate")]["checksum"]), \
                patch.object(inventory, "source_tree", side_effect=lambda path: paths[path.name]["source_tree_sha256"]):
            return inventory.check_metadata(self.root, data, local, self.policy["registry_dependencies"], self.records)

    def test_exact_full_metadata_fixture_is_accepted(self):
        data, paths = self.fixture()
        result = self.check_fixture(data, paths)
        self.assertEqual(len(result["packages"]), 4)
        self.assertTrue(all(not n["dependencies"] for n in result["resolve"]["nodes"]))

    def test_transitive_declared_edges_features_build_hooks_cannot_drift(self):
        original, paths = self.fixture()
        mutations = [lambda p: p.update(source="registry+https://example.invalid"),
                     lambda p: p.update(version="99.0.0"),
                     lambda p: p.update(links="LLVM"),
                     lambda p: p["features"].update(hidden=[]),
                     lambda p: p["dependencies"].clear(),
                     lambda p: p["dependencies"][0].update(kind="build"),
                     lambda p: p["dependencies"][0].update(target="cfg(unix)"),
                     lambda p: p["dependencies"][0].update(rename="alias"),
                     lambda p: p["targets"][0].update(kind=["custom-build"])]
        for mutate in mutations:
            data = copy.deepcopy(original)
            mutate(data["packages"][0])
            with self.assertRaisesRegex(boundary.BoundaryError, "NF-CORE-GRAPH"):
                self.check_fixture(data, paths)

    def test_resolved_transitive_features_and_edges_cannot_drift(self):
        original, paths = self.fixture()
        for change in ["features", "dependencies", "deps", "duplicate"]:
            data = copy.deepcopy(original)
            node = data["resolve"]["nodes"][0]
            if change == "features": node["features"].append("asm")
            elif change == "duplicate": data["resolve"]["nodes"].append(copy.deepcopy(node))
            else: node[change].clear()
            with self.assertRaisesRegex(boundary.BoundaryError, "NF-CORE-GRAPH"):
                self.check_fixture(data, paths)

    def test_source_tree_detects_changed_extra_and_symlinked_files(self):
        path = self.root / "source"
        path.mkdir()
        (path / "lib.rs").write_text("initial")
        initial = inventory.source_tree(path)
        (path / ".cargo-ok").write_text("cargo marker")
        self.assertEqual(inventory.source_tree(path), initial)
        (path / "lib.rs").write_text("modified")
        self.assertNotEqual(inventory.source_tree(path), initial)
        (path / "outside").symlink_to(self.root / "Cargo.toml")
        with self.assertRaisesRegex(ValueError, "symlink"):
            inventory.source_tree(path)
