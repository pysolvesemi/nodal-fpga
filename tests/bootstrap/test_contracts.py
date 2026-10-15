"""Independent negative controls for ownership, pin integrity and developer failures."""
from pathlib import Path
import copy
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
        for path in ["Cargo.toml", "tools/ownership.json"]:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        # Every registered crate is copied, including its examples/tests/modules.
        # A one-crate fixture would hide interactions introduced by the real DAG.
        policy = json.loads((ROOT / "tools/ownership.json").read_text())
        for entry in policy["core_packages"]:
            shutil.copytree(ROOT / entry["path"], self.root / entry["path"])

    def append_manifest(self, text, crate="bootstrap"):
        with (self.root / f"core/rust/{crate}/Cargo.toml").open("a") as stream:
            stream.write(text)

    def replace(self, path, old, new):
        target = self.root / path
        original = target.read_text()
        self.assertIn(old, original)
        target.write_text(original.replace(old, new))

    def rejects(self, code):
        with self.assertRaisesRegex(check_boundaries.BoundaryError, code):
            check_boundaries.check(self.root)

    def update_policy(self, change):
        path = self.root / "tools/ownership.json"
        policy = json.loads(path.read_text())
        change(policy)
        path.write_text(json.dumps(policy))

    def test_exact_reviewed_core_dag_is_accepted(self):
        check_boundaries.check(self.root)

    def test_core_cannot_import_application_device_or_adapter(self):
        original = (self.root / "core/rust/bootstrap/Cargo.toml").read_text()
        for target in ["apps/rust/tool", "devices/reference/nf-tiny", "adapters/circt", "frontend/scala"]:
            with self.subTest(target=target):
                (self.root / "core/rust/bootstrap/Cargo.toml").write_text(original)
                self.append_manifest(f'\n[dependencies]\nforbidden = {{ path = "../../../{target}" }}\n')
                self.rejects("NF-OWN-DEPENDENCY")

    def test_renamed_optional_target_dependency_is_not_hidden(self):
        self.append_manifest("\n[target.'cfg(target_os = \"linux\")'.dependencies]\ninnocent = { package = \"llvm-sys\", version = \"191\", optional = true }\n")
        self.rejects("NF-OWN-DEPENDENCY")

    def test_dev_and_build_dependencies_cannot_bypass_ownership(self):
        original = (self.root / "core/rust/bootstrap/Cargo.toml").read_text()
        for kind in ["dev-dependencies", "build-dependencies", "dev_dependencies", "build_dependencies"]:
            with self.subTest(kind=kind):
                (self.root / "core/rust/bootstrap/Cargo.toml").write_text(original)
                self.append_manifest(f'\n[{kind}]\nnf-types = {{ path = "../types" }}\n')
                self.rejects("NF-OWN-DEPENDENCY")

    def test_allowed_name_cannot_impersonate_registry_or_git_package(self):
        path = "core/rust/arch-ir/Cargo.toml"
        original = (self.root / path).read_text()
        for dep in ['"0.1"', '{ version = "0.1" }', '{ git = "https://example.invalid/repo" }',
                    '{ path = "../types", version = "0.1" }', '{ path = "../types", registry = "other" }']:
            with self.subTest(dep=dep):
                (self.root / path).write_text(original)
                self.replace(path, '{ path = "../types" }', dep)
                self.rejects("NF-OWN-DEPENDENCY")

    def test_reviewed_edge_cannot_change_kind_target_alias_or_activation(self):
        path = "core/rust/arch-ir/Cargo.toml"
        original = (self.root / path).read_text()
        changes = [('[dependencies]', '[dev-dependencies]'),
                   ('[dependencies]', '[build-dependencies]'),
                   ('[dependencies]', "[target.'cfg(windows)'.dependencies]"),
                   ('nf-types =', 'innocent ='),
                   ('{ path = "../types" }', '{ path = "../types", package = "nf-types" }'),
                   ('{ path = "../types" }', '{ path = "../types", optional = true }'),
                   ('{ path = "../types" }', '{ path = "../types", default-features = false }'),
                   ('{ path = "../types" }', '{ path = "../types", features = ["hidden"] }')]
        for old, new in changes:
            with self.subTest(new=new):
                (self.root / path).write_text(original)
                self.replace(path, old, new)
                self.rejects("NF-OWN-DEPENDENCY")

    def test_reviewed_edge_is_required(self):
        self.replace("core/rust/arch-ir/Cargo.toml", 'nf-types = { path = "../types" }', '')
        self.rejects("NF-OWN-DEPENDENCY")

    def test_reverse_and_unreviewed_internal_edges_are_rejected(self):
        self.append_manifest('\n[dependencies]\nnf-arch-ir = { path = "../arch-ir" }\n', "types")
        self.rejects("NF-OWN-DEPENDENCY")

    def test_cycles_are_rejected_even_if_both_edges_are_registered(self):
        self.append_manifest('\n[dependencies]\nnf-arch-ir = { path = "../arch-ir" }\n', "types")
        self.update_policy(lambda p: p["core_dependencies"].append({
            "from": "nf-types", "to": "nf-arch-ir", "kind": "normal", "target": None,
            "alias": "nf-arch-ir", "path": "../arch-ir"}))
        self.rejects("NF-OWN-CYCLE")

    def test_duplicate_and_unknown_policy_fields_are_rejected(self):
        path = self.root / "tools/ownership.json"
        original = path.read_text()
        for text in [original.replace('"schema": 2', '"schema": 2, "schema": 2'),
                     original.replace('"schema": 2', '"schema": 2, "allow_all": true')]:
            with self.subTest(text=text[:50]):
                path.write_text(text)
                self.rejects("NF-OWN-POLICY")

    def test_duplicate_package_and_edge_registrations_are_rejected(self):
        path = self.root / "tools/ownership.json"
        original = path.read_text()
        for key in ["core_packages", "core_dependencies"]:
            with self.subTest(key=key):
                path.write_text(original)
                self.update_policy(lambda p: p[key].append(p[key][0]))
                self.rejects("NF-OWN-POLICY")

    def test_wrong_package_name_or_version_is_rejected(self):
        path = "core/rust/types/Cargo.toml"
        original = (self.root / path).read_text()
        for old, new in [('name = "nf-types"', 'name = "llvm-sys"'),
                         ('version.workspace = true', 'version = "0.1.0"')]:
            with self.subTest(new=new):
                (self.root / path).write_text(original)
                self.replace(path, old, new)
                self.rejects("NF-OWN-IDENTITY")

    def test_workspace_version_is_part_of_package_identity(self):
        self.replace("Cargo.toml", 'version = "0.1.0"', 'version = "0.2.0"')
        self.rejects("NF-OWN-IDENTITY")

    def test_noncanonical_or_external_dependency_paths_are_rejected(self):
        path = "core/rust/arch-ir/Cargo.toml"
        original = (self.root / path).read_text()
        for dependency in [str(self.root / "core/rust/types"), "../types/.", "../types/../types", "../../../outside"]:
            with self.subTest(dependency=dependency):
                (self.root / path).write_text(original)
                self.replace(path, '../types', dependency)
                self.rejects("NF-OWN-DEPENDENCY")

    def test_unregistered_core_manifest_is_rejected(self):
        other = self.root / "core/rust/unreviewed/Cargo.toml"
        other.parent.mkdir(parents=True)
        other.write_text('[package]\nname="other"\nversion="0.1.0"\n')
        self.rejects("NF-OWN-UNREGISTERED")

    def test_workspace_cannot_add_unreviewed_member(self):
        self.replace("Cargo.toml", '"core/rust/bootstrap",', '"apps/rust/tool", "core/rust/bootstrap",')
        self.rejects("NF-OWN-MEMBERS")

    def test_workspace_overrides_and_inheritance_are_rejected(self):
        path = self.root / "Cargo.toml"
        original = path.read_text()
        for text in ['\n[workspace.dependencies]\nnf-types = "0.1"\n',
                     '\n[patch.crates-io]\nnf-types = { path = "core/rust/types" }\n',
                     '\n[replace]\n"nf-types:0.1.0" = { path = "core/rust/types" }\n',
                     '\n[package]\nname = "root"\nversion = "0.1.0"\n']:
            with self.subTest(text=text):
                path.write_text(original + text)
                self.rejects("NF-OWN-WORKSPACE")

    def test_workspace_exclude_or_default_members_are_rejected(self):
        path = self.root / "Cargo.toml"
        original = path.read_text()
        for declaration in ['exclude = ["core/rust/types"]', 'default-members = ["core/rust/bootstrap"]']:
            with self.subTest(declaration=declaration):
                path.write_text(original.replace('[workspace]', '[workspace]\n' + declaration))
                self.rejects("NF-OWN-WORKSPACE")

    def test_crate_cannot_redirect_workspace(self):
        self.replace("core/rust/types/Cargo.toml", '[package]', '[package]\nworkspace = "../../.."')
        self.rejects("NF-OWN-WORKSPACE")

    def test_cargo_config_cannot_inject_build_or_link_hooks(self):
        for prefix in ["", "core/rust/types/"]:
            with self.subTest(prefix=prefix):
                path = self.root / prefix / ".cargo/config.toml"
                path.parent.mkdir()
                path.write_text('[build]\nrustflags = ["--cap-lints", "allow"]\n')
                self.rejects("NF-OWN-NATIVE")
                path.unlink()
                path.parent.rmdir()

    def test_non_rust_target_extension_cannot_hide_include(self):
        path = self.root / "core/rust/bootstrap/hidden.txt"
        path.write_text('include!("outside.rs");\n')
        self.append_manifest('\n[[example]]\nname = "hidden"\npath = "hidden.txt"\n')
        self.rejects("NF-OWN-SOURCE")

    def test_malformed_manifest_fails_with_boundary_diagnostic(self):
        self.append_manifest('\n[dependencies]\nbroken = {\n')
        self.rejects("NF-OWN-MANIFEST")

    def test_feature_activation_is_reviewed(self):
        self.append_manifest('\n[features]\ndefault = ["hidden"]\nhidden = []\n')
        self.rejects("NF-OWN-DEPENDENCY")

    def test_build_script_and_native_link_hooks_are_rejected(self):
        path = self.root / "core/rust/bootstrap/Cargo.toml"
        original = path.read_text()
        for declaration in ['build = "custom.rs"', 'links = "LLVM"']:
            with self.subTest(declaration=declaration):
                path.write_text(original.replace('[package]', '[package]\n' + declaration))
                self.rejects("NF-OWN-NATIVE")
        path.write_text(original)
        (path.parent / "build.rs").write_text('fn main() {}\n')
        self.rejects("NF-OWN-NATIVE")

    def test_native_or_custom_library_targets_are_rejected(self):
        path = self.root / "core/rust/bootstrap/Cargo.toml"
        original = path.read_text()
        for declaration in ['proc-macro = true', 'crate-type = ["cdylib"]', 'path = "../types/src/lib.rs"']:
            with self.subTest(declaration=declaration):
                path.write_text(original + '\n[lib]\n' + declaration + '\n')
                self.rejects("NF-OWN-NATIVE")

    def test_explicit_target_cannot_escape_crate(self):
        self.append_manifest('\n[[example]]\nname = "outside"\npath = "../../../../outside.rs"\n')
        self.rejects("NF-OWN-SOURCE")

    def test_symlink_to_device_source_is_rejected(self):
        outside = self.root / "device.rs"
        outside.write_text('pub const DEVICE: u32 = 1;\n')
        (self.root / "core/rust/bootstrap/src/device.rs").symlink_to(outside)
        self.rejects("NF-OWN-SOURCE")

    def test_symlinked_source_directory_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "core/rust/types/src/hidden").symlink_to(outside, target_is_directory=True)
        self.rejects("NF-OWN-PATH")

    def test_symlinked_member_is_rejected_even_inside_core(self):
        path = self.root / "core/rust/types"
        moved = self.root / "types-moved"
        path.rename(moved)
        path.symlink_to(moved, target_is_directory=True)
        self.rejects("NF-OWN-PATH")

    def test_symlinked_manifest_is_rejected(self):
        path = self.root / "core/rust/types/Cargo.toml"
        moved = self.root / "manifest.toml"
        path.rename(moved)
        path.symlink_to(moved)
        self.rejects("NF-OWN-PATH")

    def test_include_or_native_attributes_require_review(self):
        source = self.root / "core/rust/bootstrap/src/lib.rs"
        original = source.read_text()
        for extra in ['include!("../../../devices/device.rs");', 'include_str!("secret");', 'include_bytes!("secret");',
                      '#[path = "../../../adapters/adapter.rs"] mod adapter;',
                      '#[link(name = "MLIR")] unsafe extern "C" {}',
                      '#[cfg_attr(feature = "hidden", path = "secret.rs")] mod hidden;',
                      '#[unsafe(no_mangle)] pub extern "C" fn native() {}',
                      'use std::include as hidden; hidden!("outside.rs");',
                      'use std::{include_bytes as hidden}; hidden!("outside");']:
            with self.subTest(extra=extra):
                source.write_text(original + '\n' + extra + '\n')
                self.rejects("NF-OWN-INCLUDE")

    def test_source_comments_and_literals_are_not_executable_hooks(self):
        path = self.root / "core/rust/bootstrap/src/lib.rs"
        path.write_text(path.read_text() + '\n// include!("example");\n/* #[path = "example"] */\n'
                        + 'pub const NOTE: &str = r##"include!(\"example\");"##;\n')
        check_boundaries.check(self.root)

    def test_publishing_is_disabled_at_workspace_and_package(self):
        self.replace("Cargo.toml", 'publish = false', 'publish = true')
        self.rejects("NF-OWN-PUBLISH")
        self.replace("Cargo.toml", 'publish = true', 'publish = false')
        self.replace("core/rust/types/Cargo.toml", 'publish.workspace = true', 'publish = true')
        self.rejects("NF-OWN-PUBLISH")

    def test_unsafe_policy_cannot_be_removed_or_spoofed(self):
        path = self.root / "core/rust/bootstrap/src/lib.rs"
        original = path.read_text()
        for substitute in ['', '// #![forbid(unsafe_code)]', '/* #![forbid(unsafe_code)] */',
                           'pub const SPOOF: &str = r#"#![forbid(unsafe_code)]"#;']:
            with self.subTest(substitute=substitute):
                path.write_text(original.replace('#![forbid(unsafe_code)]', substitute))
                self.rejects("NF-OWN-UNSAFE")

    def test_workspace_unsafe_lint_and_inheritance_are_required(self):
        self.replace("Cargo.toml", 'unsafe_code = "forbid"', 'unsafe_code = "allow"')
        self.rejects("NF-OWN-UNSAFE")
        self.replace("Cargo.toml", 'unsafe_code = "allow"', 'unsafe_code = "forbid"')
        self.replace("core/rust/types/Cargo.toml", '[lints]\nworkspace = true', '[lints.rust]\nunsafe_code = "allow"')
        self.rejects("NF-OWN-UNSAFE")

    def metadata(self):
        # Hand-built Cargo schema fixture, independent of production DAG helpers.
        # Actual cargo metadata is checked in the Rust lane, never mocked there.
        crates = [("nf-bootstrap", "bootstrap"), ("nf-types", "types"), ("nf-arch-ir", "arch-ir")]
        data = {"version": 1, "workspace_root": str(self.root), "packages": [],
                "workspace_members": [name for name, _ in crates],
                "workspace_default_members": [name for name, _ in crates],
                "resolve": {"root": None, "nodes": []}}
        for name, directory in crates:
            path = self.root / "core/rust" / directory
            package = {"name": name, "id": name, "version": "0.1.0", "source": None,
                       "manifest_path": str(path / "Cargo.toml"), "publish": [], "links": None,
                       "features": {}, "dependencies": [],
                       "targets": [{"kind": ["lib"], "crate_types": ["lib"], "src_path": str(path / "src/lib.rs")}]}
            node = {"id": name, "dependencies": [], "deps": [], "features": []}
            if name == "nf-arch-ir":
                package["dependencies"] = [{"name": "nf-types", "source": None, "registry": None,
                    "req": "*", "path": str(self.root / "core/rust/types"), "kind": None, "target": None,
                    "rename": None, "optional": False, "uses_default_features": True, "features": []}]
                node["dependencies"] = ["nf-types"]
                node["deps"] = [{"name": "nf_types", "pkg": "nf-types", "dep_kinds": [{"kind": None, "target": None}]}]
            data["packages"].append(package)
            data["resolve"]["nodes"].append(node)
        return data

    def rejects_metadata(self, data):
        with self.assertRaisesRegex(check_boundaries.BoundaryError, "NF-CORE-GRAPH"):
            check_boundaries.check_metadata(self.root, data)

    def test_independent_metadata_fixture_matches_exact_graph(self):
        check_boundaries.check_metadata(self.root, self.metadata())

    def test_metadata_rejects_package_identity_path_and_registry_masquerades(self):
        changes = {"name": "llvm-sys", "version": "0.2.0", "source": "registry+https://example.invalid",
                   "manifest_path": str(self.root / "devices/Cargo.toml"), "id": "nf-bootstrap",
                   "publish": None, "links": "LLVM", "features": {"hidden": []}}
        for key, value in changes.items():
            with self.subTest(key=key):
                data = self.metadata()
                data["packages"][1][key] = value
                self.rejects_metadata(data)

    def test_metadata_rejects_missing_extra_and_duplicate_packages(self):
        for mode in ["missing", "extra", "duplicate"]:
            with self.subTest(mode=mode):
                data = self.metadata()
                if mode == "missing":
                    data["packages"].pop()
                elif mode == "extra":
                    data["packages"].append(copy.deepcopy(data["packages"][0]))
                else:
                    data["packages"][1] = copy.deepcopy(data["packages"][0])
                self.rejects_metadata(data)

    def test_metadata_rejects_dependency_declaration_identity_changes(self):
        changes = {"name": "nf-bootstrap", "source": "registry+crates.io", "registry": "other", "req": "^0.1",
                   "path": str(self.root / "core/rust/bootstrap"), "kind": "dev", "target": "cfg(windows)",
                   "rename": "innocent", "optional": True, "uses_default_features": False, "features": ["hidden"]}
        for key, value in changes.items():
            with self.subTest(key=key):
                data = self.metadata()
                data["packages"][2]["dependencies"][0][key] = value
                self.rejects_metadata(data)

    def test_metadata_requires_declared_edge_and_rejects_duplicate(self):
        for deps in [[], [0, 0]]:
            with self.subTest(deps=deps):
                data = self.metadata()
                original = data["packages"][2]["dependencies"]
                data["packages"][2]["dependencies"] = [original[i] for i in deps]
                self.rejects_metadata(data)

    def test_metadata_requires_exact_workspace_members_and_root(self):
        for key in ["workspace_members", "workspace_default_members"]:
            for values in [["nf-bootstrap"], ["nf-bootstrap", "nf-types", "nf-types"]]:
                with self.subTest(key=key, values=values):
                    data = self.metadata()
                    data[key] = values
                    self.rejects_metadata(data)
        data = self.metadata()
        data["workspace_root"] = str(self.root / "core")
        self.rejects_metadata(data)

    def test_metadata_requires_resolve_graph_and_exact_nodes(self):
        for mutation in ["none", "missing", "extra", "duplicate", "root"]:
            with self.subTest(mutation=mutation):
                data = self.metadata()
                if mutation == "none":
                    data["resolve"] = None
                elif mutation == "missing":
                    data["resolve"]["nodes"].pop()
                elif mutation == "extra":
                    data["resolve"]["nodes"].append(copy.deepcopy(data["resolve"]["nodes"][0]))
                elif mutation == "duplicate":
                    data["resolve"]["nodes"][1] = copy.deepcopy(data["resolve"]["nodes"][0])
                else:
                    data["resolve"]["root"] = "nf-bootstrap"
                self.rejects_metadata(data)

    def test_metadata_rejects_wrong_resolved_edges_and_cycles(self):
        for values in [[], ["nf-bootstrap"], ["nf-types", "nf-types"], ["nf-types", "outside"]]:
            with self.subTest(values=values):
                data = self.metadata()
                data["resolve"]["nodes"][2]["dependencies"] = values
                self.rejects_metadata(data)
        data = self.metadata()
        data["resolve"]["nodes"][1]["dependencies"] = ["nf-arch-ir"]
        data["resolve"]["nodes"][1]["deps"] = [{"name": "nf_arch_ir", "pkg": "nf-arch-ir", "dep_kinds": [{"kind": None, "target": None}]}]
        self.rejects_metadata(data)

    def test_metadata_rejects_resolved_kind_target_alias_and_feature_changes(self):
        for field, value in [("name", "innocent"), ("pkg", "nf-bootstrap"), ("kind", "build"), ("target", "cfg(windows)")]:
            with self.subTest(field=field):
                data = self.metadata()
                dep = data["resolve"]["nodes"][2]["deps"][0]
                if field in {"kind", "target"}:
                    dep["dep_kinds"][0][field] = value
                else:
                    dep[field] = value
                self.rejects_metadata(data)
        data = self.metadata()
        data["resolve"]["nodes"][2]["features"] = ["hidden"]
        self.rejects_metadata(data)

    def test_metadata_rejects_missing_empty_or_duplicate_resolved_edges(self):
        for mutation in ["missing", "empty-kind", "duplicate-kind", "duplicate-edge"]:
            with self.subTest(mutation=mutation):
                data = self.metadata()
                deps = data["resolve"]["nodes"][2]["deps"]
                if mutation == "missing":
                    deps.clear()
                elif mutation == "empty-kind":
                    deps[0]["dep_kinds"].clear()
                elif mutation == "duplicate-kind":
                    deps[0]["dep_kinds"].append({"kind": None, "target": None})
                else:
                    deps.append(copy.deepcopy(deps[0]))
                self.rejects_metadata(data)

    def test_metadata_rejects_native_missing_and_external_source_targets(self):
        for field, value in [("kind", ["custom-build"]), ("crate_types", ["proc-macro"]),
                             ("src_path", str(self.root / "outside.rs"))]:
            with self.subTest(field=field):
                data = self.metadata()
                data["packages"][0]["targets"][0][field] = value
                self.rejects_metadata(data)
        data = self.metadata()
        data["packages"][0]["targets"] = []
        self.rejects_metadata(data)


class CommandTests(unittest.TestCase):
    def test_rust_smoke_builds_both_exact_packages(self):
        identity = b"nodal-fpga/bootstrap/1\nprofile=build-only\n"
        model = b"nodal-fpga/arch-ir/1\nprofile=structural-selection\nrejected=value\n"
        with patch.object(nf, "run") as run, patch.object(nf.subprocess, "run", side_effect=[
                subprocess.CompletedProcess([], 0, stdout=identity),
                subprocess.CompletedProcess([], 0, stdout=model)]):
            result = nf.rust_smoke(Path("/independent-checkout"))
        self.assertEqual(result, {"identity": identity.decode(), "model": model.decode()})
        builds = [call.args[0] for call in run.call_args_list if call.args[0][0] == "cargo"]
        self.assertEqual(builds, [
            ["cargo", "build", "--locked", "--offline", "-p", "nf-bootstrap", "--example", "identity"],
            ["cargo", "build", "--locked", "--offline", "-p", "nf-arch-ir", "--example", "model"]])

    def test_model_smoke_requires_identity_profile_and_rejection(self):
        good = b"nodal-fpga/arch-ir/1\nprofile=structural-selection\nrejected=value\n"
        variants = [good.replace(b"nodal-fpga/arch-ir/1", b"wrong"),
                    good.replace(b"profile=structural-selection\n", b""),
                    good.replace(b"rejected=value\n", b""),
                    good.replace(b"rejected=value\n", b"prefix-rejected=value\n"),
                    good.replace(b"\n", b"\r\n")]
        for output in variants:
            with self.subTest(output=output), patch.object(nf, "run"), patch.object(nf.subprocess, "run", side_effect=[
                    subprocess.CompletedProcess([], 0, stdout=b"nodal-fpga/bootstrap/1\nprofile=build-only\n"),
                    subprocess.CompletedProcess([], 0, stdout=output)]):
                with self.assertRaisesRegex(nf.BootstrapError, "NF-SMOKE"):
                    nf.rust_smoke(Path("/independent-checkout"))

    def test_bootstrap_smoke_retains_its_exact_contract(self):
        with patch.object(nf, "run"), patch.object(nf.subprocess, "run", return_value=
                subprocess.CompletedProcess([], 0, stdout=b"nodal-fpga/bootstrap/1\nprofile=build-only\nextra\n")):
            with self.assertRaisesRegex(nf.BootstrapError, "NF-SMOKE"):
                nf.rust_smoke(Path("/independent-checkout"))

    def test_reproduce_detects_model_nondeterminism(self):
        identity = "nodal-fpga/bootstrap/1\nprofile=build-only\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Cargo.lock").write_text("independent-lock\n")
            with patch.object(nf, "ROOT", root), patch.object(nf, "pins", return_value={}), \
                    patch.object(nf, "doctor"), patch.object(nf, "rust_smoke", side_effect=[
                        {"identity": identity, "model": "first\n"},
                        {"identity": identity, "model": "second\n"}]):
                with self.assertRaisesRegex(nf.BootstrapError, "NF-NONDETERMINISTIC.*ArchIR"):
                    nf.reproduce("rust")

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
