"""Hand-authored roadmap oracles; no production-generated expected statuses.

These are document/graph/evidence controls, not HDL or hardware qualification.
Structure tests opt out of evidence explicitly; provenance tests use temporary
Git repositories and independently authored mutations over shared setup helpers.
"""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures")
sys.path.insert(0, str(ROOT / "tools"))
from roadmap import Limits, RoadmapError, parse_documents, render, validate, verify_source_anchor, write_view
import test_evidence as evidence_setup

FOUNDATION = "docs/roadmap/tracks/00-foundation.md"
SCALA = "docs/roadmap/tracks/01-scala-frontend.md"


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def projection(roadmap):
    """Observe the public parsed data, without using the production renderer."""
    return {
        node_id: {
            "checked": node.checked,
            "parent": node.parent,
            "children": node.children,
        }
        for node_id, node in roadmap.nodes.items()
    }


# These literals are authored from the fixture text, not captured from a run.
PARTIAL_NODES = {
    "FND-01": {"checked": False, "parent": None, "children": ["FND-01.a", "FND-01.b", "FND-01.f", "FND-01.g", "FND-01.e"]},
    "FND-01.a": {"checked": False, "parent": "FND-01", "children": ["FND-01.a.1", "FND-01.a.2"]},
    "FND-01.a.1": {"checked": True, "parent": "FND-01.a", "children": []},
    "FND-01.a.2": {"checked": False, "parent": "FND-01.a", "children": []},
    "FND-01.b": {"checked": True, "parent": "FND-01", "children": []},
    "FND-01.f": {"checked": True, "parent": "FND-01", "children": ["FND-01.f.1"]},
    "FND-01.f.1": {"checked": True, "parent": "FND-01.f", "children": []},
    "FND-01.g": {"checked": False, "parent": "FND-01", "children": []},
    "FND-01.e": {"checked": False, "parent": "FND-01", "children": ["FND-01.e.1"]},
    "FND-01.e.1": {"checked": False, "parent": "FND-01.e", "children": []},
    "FND-02": {"checked": False, "parent": None, "children": ["FND-02.a", "FND-02.e"]},
    "FND-02.a": {"checked": False, "parent": "FND-02", "children": []},
    "FND-02.e": {"checked": False, "parent": "FND-02", "children": []},
    "FND-08": {"checked": False, "parent": None, "children": ["FND-08.a", "FND-08.e"]},
    "FND-08.a": {"checked": False, "parent": "FND-08", "children": []},
    "FND-08.e": {"checked": False, "parent": "FND-08", "children": []},
    "DSL-01": {"checked": False, "parent": None, "children": ["DSL-01.a", "DSL-01.e"]},
    "DSL-01.a": {"checked": False, "parent": "DSL-01", "children": []},
    "DSL-01.e": {"checked": False, "parent": "DSL-01", "children": []},
}
PARTIAL_DEPENDENCIES = {
    "FND-01": [],
    "FND-02": ["FND-01"],
    "FND-08": ["FND-02"],
    "DSL-01": ["FND-02", "FND-08"],
}
CLOSED_NODES = {
    "FND-01": {"checked": True, "parent": None, "children": ["FND-01.a", "FND-01.e"]},
    "FND-01.a": {"checked": True, "parent": "FND-01", "children": ["FND-01.a.1", "FND-01.a.2"]},
    "FND-01.a.1": {"checked": True, "parent": "FND-01.a", "children": []},
    "FND-01.a.2": {"checked": True, "parent": "FND-01.a", "children": []},
    "FND-01.e": {"checked": True, "parent": "FND-01", "children": ["FND-01.e.1"]},
    "FND-01.e.1": {"checked": True, "parent": "FND-01.e", "children": []},
    "FND-02": {"checked": True, "parent": None, "children": ["FND-02.a", "FND-02.e"]},
    "FND-02.a": {"checked": True, "parent": "FND-02", "children": []},
    "FND-02.e": {"checked": True, "parent": "FND-02", "children": []},
}
REOPENED_NODES = {
    "FND-01": {"checked": False, "parent": None, "children": ["FND-01.a", "FND-01.e"]},
    "FND-01.a": {"checked": False, "parent": "FND-01", "children": ["FND-01.a.1", "FND-01.a.2"]},
    "FND-01.a.1": {"checked": True, "parent": "FND-01.a", "children": []},
    "FND-01.a.2": {"checked": False, "parent": "FND-01.a", "children": []},
    "FND-01.e": {"checked": False, "parent": "FND-01", "children": ["FND-01.e.1"]},
    "FND-01.e.1": {"checked": False, "parent": "FND-01.e", "children": []},
    "FND-02": {"checked": False, "parent": None, "children": ["FND-02.a", "FND-02.e"]},
    "FND-02.a": {"checked": False, "parent": "FND-02", "children": []},
    "FND-02.e": {"checked": False, "parent": "FND-02", "children": []},
}
NUMERIC_NODES = {
    "FND-03": {"checked": False, "parent": None, "children": ["FND-03.a", "FND-03.e"]},
    "FND-03.a": {"checked": False, "parent": "FND-03", "children": ["FND-03.a.2", "FND-03.a.1"]},
    "FND-03.a.2": {"checked": False, "parent": "FND-03.a", "children": ["FND-03.a.2.11"]},
    "FND-03.a.2.11": {"checked": False, "parent": "FND-03.a.2", "children": ["FND-03.a.2.11.3"]},
    "FND-03.a.2.11.3": {"checked": False, "parent": "FND-03.a.2.11", "children": ["FND-03.a.2.11.3.9", "FND-03.a.2.11.3.1"]},
    "FND-03.a.2.11.3.9": {"checked": True, "parent": "FND-03.a.2.11.3", "children": []},
    "FND-03.a.2.11.3.1": {"checked": False, "parent": "FND-03.a.2.11.3", "children": []},
    "FND-03.a.1": {"checked": True, "parent": "FND-03.a", "children": []},
    "FND-03.e": {"checked": False, "parent": "FND-03", "children": ["FND-03.e.1"]},
    "FND-03.e.1": {"checked": False, "parent": "FND-03.e", "children": []},
}


class IndependentStructureTests(unittest.TestCase):
    def accepted(self, name, extra=None):
        documents = {FOUNDATION: fixture(name)}
        documents.update(extra or {})
        roadmap = parse_documents(documents)
        validate(roadmap, ROOT, require_evidence=False)
        return roadmap

    def rejected(self, name, code, context, documents=None):
        documents = documents or {FOUNDATION: fixture(name)}
        with self.assertRaises(RoadmapError) as caught:
            roadmap = parse_documents(documents)
            validate(roadmap, ROOT, require_evidence=False)
        self.assertEqual(caught.exception.code, code)
        self.assertIn(context, str(caught.exception))

    def test_literal_partial_state_ownership_and_dependencies(self):
        roadmap = self.accepted("partial.md", {SCALA: fixture("downstream-open.md")})
        self.assertEqual(projection(roadmap), PARTIAL_NODES)
        self.assertEqual({k: sorted(v) for k, v in roadmap.dependencies.items()}, PARTIAL_DEPENDENCIES)
        self.assertEqual(set(roadmap.increments), {"FND-01", "FND-02", "FND-08", "DSL-01"})

    def test_literal_valid_structural_closure(self):
        roadmap = self.accepted("closed.md")
        self.assertEqual(projection(roadmap), CLOSED_NODES)
        self.assertEqual(roadmap.dependencies, {"FND-01": [], "FND-02": ["FND-01"]})

    def test_reopened_regression_keeps_unaffected_progress(self):
        roadmap = self.accepted("reopened.md")
        self.assertEqual(projection(roadmap), REOPENED_NODES)
        self.assertEqual(roadmap.dependencies, {"FND-01": [], "FND-02": ["FND-01"]})

    def test_numeric_nesting_uses_stable_ownership_not_display_order(self):
        roadmap = self.accepted("numeric-depth.md")
        self.assertEqual(projection(roadmap), NUMERIC_NODES)
        self.assertEqual(roadmap.dependencies, {"FND-03": []})

    def test_fences_ignore_invalid_states_duplicates_and_dependency_text(self):
        roadmap = self.accepted("fences.md")
        self.assertEqual(projection(roadmap), {
            "FND-01": {"checked": False, "parent": None, "children": ["FND-01.a", "FND-01.e"]},
            "FND-01.a": {"checked": False, "parent": "FND-01", "children": []},
            "FND-01.e": {"checked": False, "parent": "FND-01", "children": []},
        })
        self.assertEqual(roadmap.dependencies, {"FND-01": []})

    def test_nonfoundation_preserves_existing_final_f_closure(self):
        roadmap = self.accepted("nonfoundation-f-closure-foundation.md", {
            "docs/roadmap/tracks/16-dft-manufacturing-test.md": fixture("nonfoundation-f-closure.md"),
        })
        self.assertEqual(projection(roadmap), {
            "FND-08": {"checked": True, "parent": None, "children": ["FND-08.a", "FND-08.e"]},
            "FND-08.a": {"checked": True, "parent": "FND-08", "children": []},
            "FND-08.e": {"checked": True, "parent": "FND-08", "children": []},
            "DFT-01": {"checked": True, "parent": None, "children": ["DFT-01.a", "DFT-01.e", "DFT-01.f"]},
            "DFT-01.a": {"checked": True, "parent": "DFT-01", "children": []},
            "DFT-01.e": {"checked": True, "parent": "DFT-01", "children": []},
            "DFT-01.f": {"checked": True, "parent": "DFT-01", "children": []},
        })
        self.assertEqual(roadmap.dependencies, {"FND-08": [], "DFT-01": ["FND-08"]})

    def test_distinct_requirement_and_profile_annotations(self):
        roadmap = self.accepted("annotations.md")
        self.assertEqual(roadmap.nodes["FND-01.a"].requires, "execution")
        self.assertEqual(roadmap.nodes["FND-01.a"].profile, "foundation/1")
        self.assertEqual(roadmap.nodes["FND-01.b"].requires, "review")
        self.assertEqual(roadmap.nodes["FND-01.b"].profile, "foundation/1")
        self.assertEqual(roadmap.nodes["FND-01.e"].requires, "delivery")
        self.assertIsNone(roadmap.nodes["FND-01.e"].profile)

    def test_duplicate_requires_in_single_annotation(self):
        self.rejected("duplicate-requires.md", "RM-PROFILE", FOUNDATION)

    def test_duplicate_requires_across_annotations(self):
        self.rejected("duplicate-requires-comments.md", "RM-PROFILE", FOUNDATION)

    def test_duplicate_profile_in_single_annotation(self):
        self.rejected("duplicate-profile.md", "RM-PROFILE", FOUNDATION)

    def test_duplicate_profile_across_annotations(self):
        self.rejected("duplicate-profile-comments.md", "RM-PROFILE", FOUNDATION)

    def test_literal_render_contract_and_source_locations(self):
        text = "- [ ] FND-01 Minimal\n  Depends on: none.\n  - [ ] FND-01.a Work\n  - [ ] FND-01.e Closure\n"
        roadmap = parse_documents({FOUNDATION: text})
        expected = {
            "format_version": 1,
            "authority": "owning-track-markdown",
            "nodes": [
                {"id": "FND-01", "checked": False, "parent": None, "children": ["FND-01.a", "FND-01.e"], "path": FOUNDATION, "line": 1},
                {"id": "FND-01.a", "checked": False, "parent": "FND-01", "children": [], "path": FOUNDATION, "line": 3},
                {"id": "FND-01.e", "checked": False, "parent": "FND-01", "children": [], "path": FOUNDATION, "line": 4},
            ],
            "dependencies": {"FND-01": []},
        }
        rendered = render(roadmap)
        self.assertEqual(json.loads(rendered), expected)
        self.assertTrue(rendered.endswith("\n"))
        self.assertEqual(rendered, render(parse_documents({FOUNDATION: text})))

    def test_document_mapping_insertion_order_does_not_change_output(self):
        first = {FOUNDATION: fixture("partial.md"), SCALA: fixture("downstream-open.md")}
        second = {SCALA: fixture("downstream-open.md"), FOUNDATION: fixture("partial.md")}
        self.assertEqual(render(parse_documents(first)), render(parse_documents(second)))

    def test_duplicate_id(self):
        self.rejected("duplicate-id.md", "RM-DUPLICATE-ID", "FND-01.a")

    def test_duplicate_increment_across_files(self):
        self.rejected("closed.md", "RM-DUPLICATE-ID", "FND-01", {
            FOUNDATION: fixture("closed.md"),
            "docs/roadmap/tracks/duplicate-foundation.md": fixture("closed.md"),
        })

    def test_wrong_increment_owner(self):
        self.rejected("wrong-owner.md", "RM-OWNERSHIP", "FND-02.a")

    def test_wrong_numeric_owner(self):
        self.rejected("wrong-numeric-owner.md", "RM-OWNERSHIP", "FND-01.b.1")

    def test_odd_indent(self):
        self.rejected("odd-indent.md", "RM-INDENT", FOUNDATION)

    def test_skipped_nesting_level(self):
        self.rejected("skipped-level.md", "RM-INDENT", FOUNDATION)

    def test_tab_indent(self):
        self.rejected("tab-indent.md", "RM-INDENT", FOUNDATION)

    def test_unindented_child(self):
        self.rejected("unindented-child.md", "RM-OWNERSHIP", FOUNDATION)

    def test_nested_increment(self):
        self.rejected("nested-increment.md", "RM-OWNERSHIP", "FND-02")

    def test_invalid_checkbox_state(self):
        self.rejected("invalid-checkbox.md", "RM-ID", FOUNDATION)

    def test_malformed_stable_id(self):
        self.rejected("invalid-id.md", "RM-ID", FOUNDATION)

    def test_unknown_dependency(self):
        self.rejected("unknown-dependency.md", "RM-DEPENDENCY", "FND-99")

    def test_dependency_cycle(self):
        self.rejected("dependency-cycle.md", "RM-CYCLE", "FND-01")

    def test_self_dependency_cycle(self):
        self.rejected("self-cycle.md", "RM-CYCLE", "FND-01")

    def test_inherited_global_blocker_participates_in_cycle_detection(self):
        self.rejected("global-cycle.md", "RM-CYCLE", "FND-08", {
            FOUNDATION: fixture("global-cycle.md"),
            SCALA: fixture("global-cycle-scala.md"),
        })

    def test_global_blocker_blocks_checked_leaf_under_open_parent(self):
        self.rejected("global-blocker-leaf.md", "RM-BLOCKED", "FND-08", {
            FOUNDATION: fixture("global-blocker-leaf.md"),
            SCALA: fixture("global-blocker-scala.md"),
        })

    def test_explicit_open_dependency_blocks_checked_increment(self):
        self.rejected("dependency-open.md", "RM-BLOCKED", "FND-01")

    def test_checked_root_cannot_have_open_descendants(self):
        self.rejected("checked-root-open-descendant.md", "RM-ANCESTOR", "FND-01")

    def test_checked_group_cannot_have_open_descendants(self):
        self.rejected("checked-group-open-descendant.md", "RM-ANCESTOR", "FND-01.a")

    def test_missing_final_closure_child(self):
        self.rejected("missing-closure.md", "RM-CLOSURE", "FND-01")

    def test_closure_child_must_follow_review_groups(self):
        self.rejected("nonfinal-closure.md", "RM-CLOSURE", "FND-01")

    def test_closure_cannot_be_checked_while_required_task_is_open(self):
        self.rejected("checked-closure-open-task.md", "RM-CLOSURE", "FND-01")


class BoundedTraversalTests(unittest.TestCase):
    """Bounded synthetic controls, independently described arithmetic oracles."""

    @staticmethod
    def many_increments(count):
        lines = []
        for number in range(1, count + 1):
            identifier = f"FND-{number:04d}"
            dependency = "none" if number == 1 else f"FND-{number - 1:04d}"
            lines.extend([
                f"- [ ] {identifier} Independent synthetic increment",
                f"  Depends on: {dependency}.",
                f"  - [ ] {identifier}.a Work",
                f"  - [ ] {identifier}.e Closure",
            ])
        return "\n".join(lines) + "\n"

    @staticmethod
    def nested_document(depth):
        lines = ["- [ ] FND-01 Deep synthetic hierarchy", "  Depends on: none."]
        identifier = "FND-01.a"
        for level in range(1, depth + 1):
            if level > 1:
                identifier += ".1"
            lines.append(f"{'  ' * level}- [ ] {identifier} Nested task")
        lines.append("  - [ ] FND-01.e Closure")
        return "\n".join(lines) + "\n"

    def test_many_increment_chain_and_determinism(self):
        documents = {FOUNDATION: self.many_increments(2000)}
        roadmap = parse_documents(documents)
        validate(roadmap, ROOT, require_evidence=False)
        self.assertEqual(len(roadmap.increments), 2000)
        self.assertEqual(len(roadmap.nodes), 6000)
        self.assertEqual(roadmap.dependencies["FND-0001"], [])
        self.assertEqual(roadmap.dependencies["FND-2000"], ["FND-1999"])
        self.assertFalse(any(node.checked for node in roadmap.nodes.values()))
        self.assertEqual(render(roadmap), render(parse_documents(documents)))

    def test_deep_supported_nesting(self):
        roadmap = parse_documents({FOUNDATION: self.nested_document(192)})
        validate(roadmap, ROOT, require_evidence=False)
        self.assertEqual(len(roadmap.nodes), 194)
        self.assertEqual(roadmap.nodes["FND-01.a" + ".1" * 191].children, [])

    def test_explicit_depth_limit_rejects_instead_of_truncating(self):
        with self.assertRaises(RoadmapError) as caught:
            parse_documents({FOUNDATION: self.nested_document(9)}, Limits(depth=8))
        self.assertEqual(caught.exception.code, "RM-LIMIT")

    def test_explicit_node_limit_rejects_instead_of_truncating(self):
        with self.assertRaises(RoadmapError) as caught:
            parse_documents({FOUNDATION: self.many_increments(2)}, Limits(nodes=5))
        self.assertEqual(caught.exception.code, "RM-LIMIT")

    def test_explicit_utf8_byte_limit_counts_bytes(self):
        # An ASCII encoding assumption would count this 13-byte text as 8 chars.
        with self.assertRaises(RoadmapError) as caught:
            parse_documents({FOUNDATION: "# ééééé\n"}, Limits(bytes=10))
        self.assertEqual(caught.exception.code, "RM-LIMIT")


class IndependentEvidenceBoundaryTests(unittest.TestCase):
    """Independent malformed values over shared temporary-Git setup only."""

    @classmethod
    def setUpClass(cls):
        evidence_setup.EvidenceTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        evidence_setup.EvidenceTests.tearDownClass()

    def setUp(self):
        self.fixture = evidence_setup.EvidenceTests("test_positive_partial_execution")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def reject(self, code, **kwargs):
        with self.assertRaises(RoadmapError) as caught:
            self.fixture.check(**kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_open_root_profile_constrains_checked_leaf(self):
        md = self.fixture.markdown.replace(
            "<!-- requires: execution; profile: fixture/1 -->",
            "<!-- requires: execution -->",
        )
        lines = md.splitlines()
        lines[0] += " <!-- profile: incompatible-root/2 -->"
        self.reject("RM-EVIDENCE-PROFILE", markdown="\n".join(lines) + "\n")

    def test_open_intermediate_profile_constrains_checked_leaf(self):
        md = (
            "- [ ] FND-01 Partial result\n"
            "  Depends on: none.\n"
            "  - [ ] FND-01.a Group <!-- profile: incompatible-group/2 -->\n"
            "    - [x] FND-01.a.1 Executed leaf <!-- requires: execution -->\n"
            "  - [ ] FND-01.e Closure\n"
        )
        self.fixture.data["items"] = {"FND-01.a.1": ["run"]}
        self.reject("RM-EVIDENCE-PROFILE", markdown=md)

    def test_command_must_be_nonempty_string(self):
        for value in [None, [], {}, True, 1, "", "   "]:
            with self.subTest(command=value):
                self.fixture.data["observations"]["run"]["command"] = value
                self.reject("RM-EVIDENCE-EXECUTION")

    def test_format_version_boolean_is_not_integer_one(self):
        self.fixture.data["format_version"] = True
        self.reject("RM-EVIDENCE-FORMAT")

    def test_observation_artifacts_must_be_array(self):
        paths = self.fixture.data["observations"]["run"]["artifacts"]
        self.fixture.data["observations"]["run"]["artifacts"] = dict.fromkeys(paths, True)
        self.reject("RM-EVIDENCE-MISSING")

    def test_context_booleans_are_not_identity_or_applicability(self):
        self.fixture.data["context"] = dict.fromkeys(self.fixture.data["context"], True)
        self.reject("RM-EVIDENCE-CONTEXT")

    def test_embedded_nul_path_has_structured_rejection(self):
        self.fixture.data["artifacts"]["bad\x00name"] = "0" * 64
        self.reject("RM-EVIDENCE-PATH")

    def test_symlink_cycle_has_structured_rejection(self):
        (self.fixture.root / "loop").symlink_to("loop")
        self.fixture.data["artifacts"]["loop"] = "0" * 64
        self.reject("RM-EVIDENCE-PATH")

    def test_single_parent_commit_cannot_claim_actual_merge(self):
        root = self.fixture.root
        evidence_setup.git(root, "checkout", "--detach", self.fixture.commit)
        evidence_setup.git(root, "commit", "--allow-empty", "-m", "independent non-merge")
        commit = evidence_setup.git(root, "rev-parse", "HEAD")
        self.fixture.data["items"]["FND-01.e"] = ["review"]
        self.fixture.data["integration"] = {
            "state": "merged", "commit": commit, "tree": self.fixture.tree,
            "parents": [self.fixture.commit],
        }
        self.fixture.data["ci"]["post_merge"]["state"] = "skipped"
        self.reject("RM-EVIDENCE-INTEGRATION", markdown=self.fixture.markdown.replace("[ ]", "[x]"))

    def test_designated_view_symlink_cannot_overwrite_evidence(self):
        parsed = self.fixture.check()
        target = self.fixture.root / "docs/completion/FND-01.evidence.json"
        before = target.read_bytes()
        output = self.fixture.root / "docs/roadmap/status.generated.json"
        output.parent.mkdir(parents=True)
        output.symlink_to(target)
        with self.assertRaises(RoadmapError) as caught:
            write_view(parsed, self.fixture.root, output)
        self.assertEqual(caught.exception.code, "RM-DERIVED-PATH")
        self.assertEqual(target.read_bytes(), before)

    def test_artifacts_directory_symlink_cannot_broaden_output_scope(self):
        parsed = self.fixture.check()
        target = self.fixture.root / "docs/completion/FND-01.evidence.json"
        before = target.read_bytes()
        artifacts = self.fixture.root / "artifacts"
        artifacts.symlink_to(self.fixture.root / "docs/completion", target_is_directory=True)
        with self.assertRaises(RoadmapError) as caught:
            write_view(parsed, self.fixture.root, artifacts / "FND-01.evidence.json")
        self.assertEqual(caught.exception.code, "RM-DERIVED-PATH")
        self.assertEqual(target.read_bytes(), before)

    def test_retained_execution_profile_cannot_disagree(self):
        source_path = self.fixture.root / "source.json"
        source = json.loads(source_path.read_text())
        source["profile"] = "different-execution/2"
        source_path.write_text(json.dumps(source))
        self.fixture.data["artifacts"]["source.json"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        self.reject("RM-EVIDENCE-PROFILE")


class IndependentSourceAnchorTests(unittest.TestCase):
    """Reproductions of source-anchor bypasses using actual local Git objects."""

    def setUp(self):
        self.fixture = evidence_setup.SourceAnchorTests("test_status_and_evidence_link_only_anchor_is_accepted")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def reject(self, source, candidate, code="RM-SOURCE-ANCHOR"):
        with self.assertRaises(RoadmapError) as caught:
            verify_source_anchor(self.fixture.root, source, candidate)
        self.assertEqual(caught.exception.code, code)

    def commit(self):
        evidence_setup.git(self.fixture.root, "add", "-A")
        evidence_setup.git(self.fixture.root, "commit", "-m", "independent malformed candidate")
        return evidence_setup.git(self.fixture.root, "rev-parse", "HEAD")

    def test_leading_whitespace_path_is_not_reclassified_as_documentation(self):
        candidate = self.fixture.candidate(" docs/completion/payload.txt", "Outside the docs directory.\n")
        self.reject(self.fixture.source, candidate)

    def test_implementation_renamed_into_completion_is_not_docs_only(self):
        root = self.fixture.root
        evidence_setup.git(root, "config", "diff.renames", "true")
        (root / "docs/completion").mkdir()
        (root / "code.py").rename(root / "docs/completion/payload.txt")
        candidate = self.commit()
        self.reject(self.fixture.source, candidate)

    def test_tag_object_cannot_stand_in_for_exact_source_commit(self):
        root = self.fixture.root
        evidence_setup.git(root, "tag", "-a", "reviewed-source", "-m", "tag object", self.fixture.source)
        tag = evidence_setup.git(root, "rev-parse", "reviewed-source")
        candidate = self.fixture.candidate("docs/completion/FND-01.md", "Reviewed report.\n")
        self.reject(tag, candidate, "RM-EVIDENCE-SOURCE")

    def test_tag_object_cannot_stand_in_for_exact_candidate_commit(self):
        root = self.fixture.root
        candidate = self.fixture.candidate("docs/completion/FND-01.md", "Reviewed report.\n")
        evidence_setup.git(root, "tag", "-a", "reviewed-candidate", "-m", "tag object", candidate)
        tag = evidence_setup.git(root, "rev-parse", "reviewed-candidate")
        self.reject(self.fixture.source, tag, "RM-EVIDENCE-SOURCE")

    def test_roadmap_symlink_mode_change_is_not_status_only(self):
        path = self.fixture.root / self.fixture.path
        content = path.read_text()
        path.unlink()
        path.symlink_to(content)
        candidate = self.commit()
        self.reject(self.fixture.source, candidate)


if __name__ == "__main__":
    unittest.main()
