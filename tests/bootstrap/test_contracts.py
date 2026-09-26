"""Independent negative controls for ownership, pin integrity and developer failures."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_boundaries
import change_scope
import nf


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for path in ["Cargo.toml", "core/rust/bootstrap/Cargo.toml", "core/rust/bootstrap/src/lib.rs", "tools/ownership.json"]:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)

    def append_manifest(self, text):
        with (self.root / "core/rust/bootstrap/Cargo.toml").open("a") as stream:
            stream.write(text)

    def rejects(self, code):
        with self.assertRaisesRegex(check_boundaries.BoundaryError, code):
            check_boundaries.check(self.root)

    def test_actual_dependency_free_core_is_accepted(self):
        check_boundaries.check(self.root)

    def test_core_cannot_import_application_device_or_adapter(self):
        original = (self.root / "core/rust/bootstrap/Cargo.toml").read_text()
        for target in ["apps/rust/tool", "devices/reference/nf-tiny", "adapters/circt", "frontend/scala"]:
            with self.subTest(target=target):
                (self.root / "core/rust/bootstrap/Cargo.toml").write_text(original)
                self.append_manifest(f'\n[dependencies]\nforbidden = {{ path = "../../../{target}" }}\n')
                self.rejects("NF-OWN-DEPENDENCY")

    def test_renamed_optional_target_dependency_is_not_hidden(self):
        self.append_manifest('\n[target.\'cfg(target_os = "linux")\'.dependencies]\ninnocent = { package = "llvm-sys", version = "191", optional = true }\n')
        self.rejects("NF-OWN-DEPENDENCY")

    def test_dev_dependency_cannot_bypass_ownership(self):
        self.append_manifest('\n[dev-dependencies]\nnextpnr = "0.1"\n')
        self.rejects("NF-OWN-DEPENDENCY")

    def test_build_script_is_rejected(self):
        (self.root / "core/rust/bootstrap/build.rs").write_text('fn main() {}\n')
        self.rejects("NF-OWN-NATIVE")

    def test_unregistered_core_manifest_is_rejected(self):
        other = self.root / "core/rust/unreviewed/Cargo.toml"
        other.parent.mkdir(parents=True)
        other.write_text('[package]\nname="other"\nversion="0.1.0"\n')
        self.rejects("NF-OWN-UNREGISTERED")

    def test_symlink_to_device_source_is_rejected(self):
        outside = self.root / "device.rs"
        outside.write_text('pub const DEVICE: u32 = 1;\n')
        (self.root / "core/rust/bootstrap/src/device.rs").symlink_to(outside)
        self.rejects("NF-OWN-SOURCE")

    def test_include_or_native_link_requires_review(self):
        source = self.root / "core/rust/bootstrap/src/lib.rs"
        original = source.read_text()
        for extra in ['include!("../../../devices/device.rs");', '#[path = "../../../adapters/adapter.rs"] mod adapter;', '#[link(name = "MLIR")] unsafe extern "C" {}']:
            with self.subTest(extra=extra):
                source.write_text(original + '\n' + extra + '\n')
                self.rejects("NF-OWN-INCLUDE")

    def test_publishing_is_disabled(self):
        path = self.root / "Cargo.toml"
        path.write_text(path.read_text().replace('publish = false', 'publish = true'))
        self.rejects("NF-OWN-PUBLISH")

    def test_unsafe_policy_cannot_be_removed(self):
        path = self.root / "core/rust/bootstrap/src/lib.rs"
        path.write_text(path.read_text().replace('#![forbid(unsafe_code)]', ''))
        self.rejects("NF-OWN-UNSAFE")


class CommandTests(unittest.TestCase):
    def test_document_changes_only_select_contracts(self):
        self.assertEqual(change_scope.lanes(["AGENTS.md", "docs/roadmap/tracks/00-foundation.md"]), ["contracts"])

    def test_workflow_or_unknown_change_selects_both_languages(self):
        for path in [".github/workflows/fnd-01-bootstrap.yml", "tools/nf.py", "Cargo.lock", "new-unknown-config"]:
            with self.subTest(path=path):
                self.assertEqual(change_scope.lanes([path]), ["contracts", "rust", "scala"])

    def test_invalid_scope_path_is_rejected(self):
        for path in ["../outside", "/absolute"]:
            with self.assertRaisesRegex(ValueError, "NF-SCOPE-PATH"):
                change_scope.lanes([path])

    def test_missing_rust_prerequisite_has_actionable_failure(self):
        result = subprocess.run([sys.executable, str(ROOT / "nf"), "doctor", "rust"],
                                env={**os.environ, "PATH": ""}, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NF-TOOL-MISSING: rustc", result.stderr)

    def test_invalid_command_fails(self):
        result = subprocess.run([sys.executable, str(ROOT / "nf"), "check", "hardware"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_corrupt_cached_launcher_is_never_executed_or_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NF_TOOL_CACHE": directory}):
            target = Path(directory) / "sbt-launch.jar"
            target.write_bytes(b"intentionally corrupt launcher")
            with self.assertRaisesRegex(nf.BootstrapError, "NF-CHECKSUM-MISMATCH"):
                nf.obtain("sbt-launch.jar", nf.pins()["sbt_launcher"])
            self.assertEqual(target.read_bytes(), b"intentionally corrupt launcher")

    def test_missing_offline_launcher_is_reported(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"NF_TOOL_CACHE": directory, "NF_OFFLINE": "1"}):
            with self.assertRaisesRegex(nf.BootstrapError, "NF-OFFLINE-MISSING"):
                nf.obtain("sbt-launch.jar", nf.pins()["sbt_launcher"])

    def test_source_identity_mismatch_is_rejected(self):
        with patch.dict(os.environ, {"NF_EXPECT_SHA": "0" * 40}):
            with self.assertRaisesRegex(nf.BootstrapError, "NF-SOURCE-MISMATCH"):
                nf.metadata()

    def test_declared_tool_pins_match_build_files(self):
        nf.validate_pins()

    def test_toolchain_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "toolchains").mkdir()
            (root / "toolchains/versions.json").write_text(json.dumps(nf.pins()))
            (root / "rust-toolchain.toml").write_text('[toolchain]\nchannel="stable"\n')
            with self.assertRaisesRegex(nf.BootstrapError, "NF-PIN-DRIFT"):
                nf.validate_pins(root)


if __name__ == "__main__":
    unittest.main()
