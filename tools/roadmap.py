"""Bounded Markdown progress validation. No HDL or hardware-semantic claims."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[A-Z][A-Z0-9]*-[0-9]{2,}(?:\.(?:[a-z]+|[1-9][0-9]*))*\Z")
INCREMENT = re.compile(r"[A-Z][A-Z0-9]*-[0-9]{2,}\Z")
CHECKBOX = re.compile(r"^([ \t]*)- \[([ xX])\] (\S+)(?:\s+(.*))?$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
SHA = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
JSON_BYTES = 4 * 1024 * 1024
ARTIFACT_BYTES = 128 * 1024 * 1024
TOTAL_ARTIFACT_BYTES = 512 * 1024 * 1024


class RoadmapError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def fail(code: str, message: str) -> None:
    raise RoadmapError(code, message)


@dataclass(frozen=True)
class Limits:
    bytes: int = 16 * 1024 * 1024
    nodes: int = 100_000
    depth: int = 256


@dataclass
class Node:
    id: str
    checked: bool
    path: str
    line: int
    parent: str | None
    children: list[str] = field(default_factory=list)
    requires: str = "delivery"
    profile: str | None = None


@dataclass
class Roadmap:
    nodes: dict[str, Node]
    increments: list[str]
    dependencies: dict[str, list[str]]


def parse_documents(documents: dict[str, str], limits: Limits = Limits()) -> Roadmap:
    """Single pass over lines, explicit stack; prose is never a dependency edge."""
    if sum(len(text.encode("utf-8")) for text in documents.values()) > limits.bytes:
        fail("RM-LIMIT", "document bytes exceed declared limit")
    nodes: dict[str, Node] = {}
    increments: list[str] = []
    dependencies: dict[str, list[str]] = {}
    owners: dict[str, str] = {}
    for path, text in sorted(documents.items()):
        stack: list[str] = []
        current = None
        track = None
        fence = None
        for line_number, line in enumerate(text.splitlines(), 1):
            location = f"{path}:{line_number}"
            marker = FENCE.match(line)
            if fence:
                if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                    fence = None
                continue
            if marker:
                fence = (marker[1][0], len(marker[1]))
                continue
            if line.lstrip().startswith("Depends on:"):
                if current is None or not line.startswith("  Depends on: ") or current in dependencies:
                    fail("RM-DEPENDENCY", f"{location}: misplaced or repeated dependency declaration")
                value = line.strip().removeprefix("Depends on: ").removesuffix(".")
                deps = [] if value == "none" else value.split(", ")
                if any(not INCREMENT.fullmatch(dep) for dep in deps) or len(set(deps)) != len(deps):
                    fail("RM-DEPENDENCY", f"{location}: use unique comma-separated increment IDs or none")
                dependencies[current] = deps
                continue
            match = CHECKBOX.match(line)
            if not match:
                if re.match(r"^\s*[-+*]\s*\[", line):
                    fail("RM-ID", f"{location}: malformed status checkbox")
                continue
            indent, state, identifier, body = match.groups()
            if "\t" in indent or len(indent) % 2:
                fail("RM-INDENT", f"{location}: use two spaces per level, no tabs")
            depth = len(indent) // 2
            if depth > limits.depth or len(nodes) >= limits.nodes:
                fail("RM-LIMIT", f"{location}: node/depth limit exceeded")
            if not ID.fullmatch(identifier):
                fail("RM-ID", f"{location}: malformed stable ID {identifier}")
            if identifier in nodes:
                fail("RM-DUPLICATE-ID", f"{location}: duplicate {identifier}")
            if depth > len(stack):
                fail("RM-INDENT", f"{location}: skipped hierarchy level")
            parent = stack[depth - 1] if depth else None
            if depth == 0:
                if not INCREMENT.fullmatch(identifier):
                    fail("RM-OWNERSHIP", f"{location}: descendant at increment level")
                prefix = identifier.split("-", 1)[0]
                if track is not None and track != prefix:
                    fail("RM-OWNERSHIP", f"{location}: one track prefix per owning file")
                if prefix in owners and owners[prefix] != path:
                    fail("RM-OWNERSHIP", f"{location}: track {prefix} already owned by {owners[prefix]}")
                track = prefix
                owners[prefix] = path
                current = identifier
                increments.append(identifier)
            elif identifier.rpartition(".")[0] != parent:
                fail("RM-OWNERSHIP", f"{location}: {identifier} is not a direct child of {parent}")
            node = Node(identifier, state.lower() == "x", path, line_number, parent)
            seen_annotations = set()
            annotations = re.findall(r"<!--\s*(.*?)\s*-->", body or "")
            for annotation in annotations:
                if not annotation.startswith(("requires:", "profile:")):
                    continue
                for clause in annotation.split(";"):
                    name, separator, value = clause.strip().partition(":")
                    value = value.strip()
                    if not separator or name not in {"requires", "profile"} or not value:
                        fail("RM-PROFILE", f"{location}: malformed evidence requirement")
                    if name in seen_annotations:
                        fail("RM-PROFILE", f"{location}: duplicate evidence requirement {name}")
                    seen_annotations.add(name)
                    if name == "requires":
                        if value not in {"delivery", "execution", "review", "artifact"}:
                            fail("RM-PROFILE", f"{location}: unsupported requirement {value}")
                        node.requires = value
                    else:
                        node.profile = value
            nodes[identifier] = node
            if parent:
                nodes[parent].children.append(identifier)
            stack[depth:] = [identifier]
    for identifier in increments:
        if identifier not in dependencies:
            fail("RM-DEPENDENCY", f"{identifier}: missing Depends on declaration")
        if not identifier.startswith("FND-") and "FND-08" not in dependencies[identifier]:
            dependencies[identifier].append("FND-08")
    return Roadmap(nodes, increments, dependencies)


def validate(roadmap: Roadmap, root: Path = ROOT, *, require_evidence: bool = True,
             expected_sources: dict[str, str] | None = None) -> None:
    nodes, deps = roadmap.nodes, roadmap.dependencies
    for identifier in roadmap.increments:
        for dep in deps[identifier]:
            if dep not in deps:
                fail("RM-DEPENDENCY", f"{identifier}: unknown dependency {dep}")
    # Iterative colour DFS avoids recursion limits and visits each edge once.
    colour: dict[str, int] = {}
    for start in roadmap.increments:
        if colour.get(start):
            continue
        colour[start] = 1
        stack = [(start, iter(deps[start]))]
        while stack:
            owner, edges = stack[-1]
            dep = next(edges, None)
            if dep is None:
                colour[owner] = 2
                stack.pop()
            elif colour.get(dep) == 1:
                fail("RM-CYCLE", f"dependency back edge {owner} -> {dep}")
            elif not colour.get(dep):
                colour[dep] = 1
                stack.append((dep, iter(deps[dep])))
    for node in nodes.values():
        if node.checked:
            for child in node.children:
                if not nodes[child].checked:
                    fail("RM-ANCESTOR", f"{node.id}: checked ancestor has open child {child}")
    checked_by_increment: dict[str, list[Node]] = {identifier: [] for identifier in roadmap.increments}
    for node in nodes.values():
        if node.checked:
            checked_by_increment[node.id.split(".", 1)[0]].append(node)
    for identifier in roadmap.increments:
        children = nodes[identifier].children
        if not children or (identifier.startswith("FND-") and children[-1] != identifier + ".e"):
            fail("RM-CLOSURE", f"{identifier}: require a final closure child; Foundation retains .e")
        if nodes[children[-1]].checked and any(not nodes[child].checked for child in children[:-1]):
            fail("RM-CLOSURE", f"{identifier}: closure checked before required work")
        if checked_by_increment[identifier]:
            for dep in deps[identifier]:
                if not nodes[dep].checked:
                    fail("RM-BLOCKED", f"{identifier}: checked work while dependency {dep} is open")
        if require_evidence and (checked_by_increment[identifier] or identifier in (expected_sources or {})):
            validate_evidence(roadmap, identifier, root, expected_source=(expected_sources or {}).get(identifier))
    unknown = set(expected_sources or {}) - set(roadmap.increments)
    if unknown:
        fail("RM-EVIDENCE-SOURCE", f"unknown source expectations: {sorted(unknown)}")


def read_json(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                fail("RM-EVIDENCE-FORMAT", f"{path}: duplicate JSON key {key}")
            result[key] = value
        return result
    try:
        if path.stat().st_size > JSON_BYTES:
            fail("RM-LIMIT", f"{path}: evidence JSON exceeds {JSON_BYTES} bytes")
        value = json.loads(path.read_text(), object_pairs_hook=unique)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        fail("RM-EVIDENCE-MISSING", f"{path}: {exc}")
    if not isinstance(value, dict):
        fail("RM-EVIDENCE-FORMAT", f"{path}: expected object")
    return value


def local_file(root: Path, name: str) -> Path:
    if not isinstance(name, str):
        fail("RM-EVIDENCE-PATH", "artifact path must be a string")
    if "\0" in name:
        fail("RM-EVIDENCE-PATH", "artifact path contains NUL")
    path = Path(name)
    try:
        contained = (root / path).resolve().is_relative_to(root.resolve())
    except (ValueError, RuntimeError, OSError) as exc:
        fail("RM-EVIDENCE-PATH", f"invalid artifact path: {exc}")
    if path.is_absolute() or ".." in path.parts or not name or not contained:
        fail("RM-EVIDENCE-PATH", f"unsafe repository path: {name}")
    if not (root / path).is_file():
        fail("RM-EVIDENCE-MISSING", f"missing artifact {name}")
    return root / path


def git(root: Path, *args: str, strip: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode:
        fail("RM-EVIDENCE-SOURCE", f"Git identity unavailable: {' '.join(args)}; use full source history")
    return result.stdout.strip() if strip else result.stdout


def source_identity(root: Path, source: dict) -> None:
    if not isinstance(source, dict) or set(source) != {"commit", "tree"} or any(not isinstance(value, str) or not SHA.fullmatch(value) for value in source.values()):
        fail("RM-EVIDENCE-SOURCE", "require exact commit and tree SHA-1 identities")
    if git(root, "cat-file", "-t", source["commit"]) != "commit":
        fail("RM-EVIDENCE-SOURCE", "source identity must name a commit object")
    actual = git(root, "rev-parse", source["commit"] + "^{tree}")
    if actual != source["tree"]:
        fail("RM-EVIDENCE-SOURCE", f"{source['commit']}: tree does not match recorded source")


def validate_artifacts(manifest: dict, identifier: str, root: Path, source: dict) -> dict:
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, dict) or not artifacts:
        fail("RM-EVIDENCE-MISSING", f"{identifier}: empty artifact inventory")
    total_bytes = 0
    if len(artifacts) > 10_000:
        fail("RM-LIMIT", f"{identifier}: artifact count exceeds 10000")
    for name, digest in sorted(artifacts.items()):
        path = local_file(root, name)
        size = path.stat().st_size
        total_bytes += size
        if size > ARTIFACT_BYTES or total_bytes > TOTAL_ARTIFACT_BYTES:
            fail("RM-LIMIT", f"{identifier}: evidence artifact byte limit exceeded")
        hasher = hashlib.sha256()
        read_bytes = 0
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                read_bytes += len(chunk)
                if read_bytes > ARTIFACT_BYTES:
                    fail("RM-LIMIT", f"{identifier}: growing artifact exceeds limit")
                hasher.update(chunk)
        total_bytes += read_bytes - size
        if total_bytes > TOTAL_ARTIFACT_BYTES:
            fail("RM-LIMIT", f"{identifier}: total artifact byte limit exceeded")
        actual = hasher.hexdigest()
        if not isinstance(digest, str) or not DIGEST.fullmatch(digest) or actual != digest:
            fail("RM-EVIDENCE-HASH", f"{identifier}: missing/stale digest for {name}")
    report = manifest["report"]
    if report != f"docs/completion/{identifier}.md" or report not in artifacts:
        fail("RM-EVIDENCE-MISSING", f"{identifier}: completion report must be hashed")
    if local_file(root, report).stat().st_size > JSON_BYTES:
        fail("RM-LIMIT", f"{identifier}: completion report too large")
    report_text = local_file(root, report).read_text()
    if f"]({identifier}.evidence.json)" not in report_text:
        fail("RM-EVIDENCE-MISSING", f"{identifier}: report must link its evidence metadata")
    for value in source.values():
        if value not in report_text:
            fail("RM-EVIDENCE-SOURCE", f"{identifier}: report/source identity disagreement")
    return artifacts


def validate_items(manifest: dict, roadmap: Roadmap, identifier: str, profile: str, observations: dict) -> None:
    items = manifest["items"]
    for item, references in items.items():
        if item not in roadmap.nodes or item.split(".", 1)[0] != identifier:
            fail("RM-EVIDENCE-ITEM", f"{identifier}: evidence for unknown/foreign ID {item}")
        if not isinstance(references, list) or not references or any(ref not in observations for ref in references):
            fail("RM-EVIDENCE-MISSING", f"{item}: unknown/missing observation")
    pending = [(identifier, None)]
    while pending:
        node_id, inherited_profile = pending.pop()
        node = roadmap.nodes[node_id]
        if node.profile and inherited_profile and node.profile != inherited_profile:
            fail("RM-EVIDENCE-PROFILE", f"{node.id}: conflicting ancestor profile")
        effective_profile = node.profile or inherited_profile
        pending.extend((child, effective_profile) for child in reversed(node.children))
        if not node.checked:
            continue
        if effective_profile and effective_profile != profile:
            fail("RM-EVIDENCE-PROFILE", f"{node.id}: authoritative profile mismatch")
        if not node.children or node.requires != "delivery":
            if node.id not in items:
                fail("RM-EVIDENCE-MISSING", f"{node.id}: checked obligation has no evidence")
            kinds = {observations[ref]["kind"] for ref in items[node.id]}
            if node.requires != "delivery" and node.requires not in kinds:
                fail("RM-EVIDENCE-EXECUTION", f"{node.id}: required {node.requires} cannot be replaced by applicability review")


def validate_context(manifest: dict, identifier: str) -> None:
    context = manifest["context"]
    required = {"tools", "device", "configuration", "schemas", "seeds", "assumptions", "reference_corpus", "correspondence", "mutations", "loading_mode", "coverage", "limitations", "examples"}
    if not isinstance(context, dict) or set(context) != required or any(not isinstance(value, (str, list, dict)) or not value or (isinstance(value, str) and not value.strip()) for value in context.values()):
        fail("RM-EVIDENCE-CONTEXT", f"{identifier}: complete explicit identities/applicability/limits required")


def validate_integration(manifest: dict, identifier: str, root: Path, source: dict, *, closed: bool) -> None:
    integration = manifest["integration"]
    if integration["state"] not in {"pending", "merged"}:
        fail("RM-EVIDENCE-INTEGRATION", f"{identifier}: invalid integration state")
    if closed and integration["state"] != "merged":
        fail("RM-EVIDENCE-INTEGRATION", f"{identifier}: closed increment must have actual merged evidence")
    if integration["state"] == "merged":
        source_identity(root, {"commit": integration["commit"], "tree": integration["tree"]})
        git(root, "merge-base", "--is-ancestor", integration["commit"], "HEAD")
        actual_parents = git(root, "show", "-s", "--format=%P", integration["commit"]).split()
        if len(actual_parents) != 2 or len(set(actual_parents)) != 2 or integration["parents"] != actual_parents or source["commit"] != actual_parents[1] or integration["tree"] != source["tree"]:
            fail("RM-EVIDENCE-INTEGRATION", f"{identifier}: actual merge parents/tree differ from qualified source")


def validate_ci(manifest: dict, identifier: str) -> None:
    ci = manifest["ci"]
    if ci["qualification"] not in {"executed", "not-run"} or not isinstance(ci.get("reason"), str) or not ci["reason"].strip():
        fail("RM-EVIDENCE-CI", f"{identifier}: explicit CI disposition/reason required")
    if not isinstance(ci["runs"], list) or any(not isinstance(run, str) or not run.startswith("https://") for run in ci["runs"]) or bool(ci["runs"]) != (ci["qualification"] == "executed"):
        fail("RM-EVIDENCE-CI", f"{identifier}: executed CI needs real run references; not-run has none")
    post = ci["post_merge"]
    if post["state"] not in {"executed", "skipped", "pending"} or not isinstance(post.get("reason"), str) or not post["reason"].strip() or not isinstance(post["runs"], list) or any(not isinstance(run, str) or not run.startswith("https://") for run in post["runs"]) or bool(post["runs"]) != (post["state"] == "executed"):
        fail("RM-EVIDENCE-CI", f"{identifier}: distinguish post-merge execution from suppression")
    if post["state"] == "skipped" and manifest["integration"]["state"] != "merged":
        fail("RM-EVIDENCE-CI", f"{identifier}: cannot verify suppression before merge")


def validate_evidence(roadmap: Roadmap, identifier: str, root: Path, *, expected_source: str | None = None) -> None:
    """Evidence maps IDs to observations, never stores a second checkbox state."""
    manifest_name = f"docs/completion/{identifier}.evidence.json"
    manifest = read_json(local_file(root, manifest_name))
    if type(manifest.get("format_version")) is int and manifest["format_version"] == 2:
        validate_summary_evidence(manifest, roadmap, identifier, root, expected_source=expected_source)
        return
    try:
        if type(manifest["format_version"]) is not int or manifest["format_version"] != 1 or manifest["increment"] != identifier:
            fail("RM-EVIDENCE-FORMAT", f"{identifier}: unsupported version or wrong owner")
        allowed = {"format_version", "increment", "source", "profile", "report", "artifacts", "observations", "items", "context", "review", "integration", "ci"}
        if set(manifest) != allowed:
            fail("RM-EVIDENCE-FORMAT", f"{identifier}: missing/unknown keys, including forbidden duplicate status")
        source = manifest["source"]
        source_identity(root, source)
        if expected_source is not None and source["commit"] != expected_source:
            fail("RM-EVIDENCE-SOURCE", f"{identifier}: stale source; expected {expected_source}")
        profile = manifest["profile"]
        if not isinstance(profile, str) or not profile.strip():
            fail("RM-EVIDENCE-PROFILE", f"{identifier}: explicit nonempty profile required")
        artifacts = validate_artifacts(manifest, identifier, root, source)
        observations = manifest["observations"]
        if not isinstance(observations, dict) or not observations:
            fail("RM-EVIDENCE-MISSING", f"{identifier}: no observations")
        for key, observation in observations.items():
            if set(observation) - {"source", "profile", "kind", "result", "artifacts", "command", "source_record"}:
                fail("RM-EVIDENCE-FORMAT", f"{identifier}/{key}: unknown observation fields")
            if observation["source"] != source:
                fail("RM-EVIDENCE-SOURCE", f"{identifier}/{key}: stale observation source")
            if observation["profile"] != profile:
                fail("RM-EVIDENCE-PROFILE", f"{identifier}/{key}: profile mismatch")
            kind = observation["kind"]
            if kind not in {"execution", "review", "artifact"} or observation["result"] != {"execution": "passed", "review": "accepted", "artifact": "inspected"}.get(kind):
                fail("RM-EVIDENCE-EXECUTION", f"{identifier}/{key}: N/A, not-run, skipped or failed is not completed evidence")
            if not isinstance(observation["artifacts"], list) or not observation["artifacts"] or any(not isinstance(path, str) or path not in artifacts for path in observation["artifacts"]):
                fail("RM-EVIDENCE-MISSING", f"{identifier}/{key}: observation must bind retained artifacts")
            if kind == "execution":
                if not isinstance(observation.get("command"), str) or not observation["command"].strip():
                    fail("RM-EVIDENCE-EXECUTION", f"{identifier}/{key}: execution command missing")
                record_path = observation.get("source_record")
                if record_path not in artifacts or record_path not in observation["artifacts"]:
                    fail("RM-EVIDENCE-SOURCE", f"{identifier}/{key}: retained execution source record missing")
                record = read_json(local_file(root, record_path))
                if record.get("head") != source["commit"] or record.get("tree") != source["tree"] or record.get("dirty") is not False:
                    fail("RM-EVIDENCE-SOURCE", f"{identifier}/{key}: execution source record is stale or dirty")
                if "profile" in record and record["profile"] != profile:
                    fail("RM-EVIDENCE-PROFILE", f"{identifier}/{key}: execution profile record disagrees")
        validate_items(manifest, roadmap, identifier, profile, observations)
        validate_context(manifest, identifier)
        if manifest["review"].get("artifact") not in artifacts or manifest["review"].get("kind") not in {"agent", "human"}:
            fail("RM-EVIDENCE-MISSING", f"{identifier}: retained review identity required")
        validate_integration(manifest, identifier, root, source, closed=roadmap.nodes[identifier].checked)
        validate_ci(manifest, identifier)
    except (KeyError, TypeError, AttributeError, UnicodeError, OSError) as exc:
        fail("RM-EVIDENCE-FORMAT", f"{identifier}: malformed evidence: {exc}")



def summary_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def summary_identity(value: object) -> bool:
    return summary_text(value) and value == value.strip()


def summary_limits(value: object) -> bool:
    return summary_text(value) or (isinstance(value, list) and bool(value)
                                   and all(summary_text(item) for item in value))


def summary_references(value: object, available: dict | set) -> bool:
    return (isinstance(value, list) and bool(value) and all(summary_text(item) for item in value)
            and len(set(value)) == len(value) and all(item in available for item in value))


def validate_summary_evidence(manifest: dict, roadmap: Roadmap, identifier: str, root: Path,
                              *, expected_source: str | None = None) -> None:
    """Validate a reviewed execution attestation, without requiring raw-log upload.

    This does not execute commands or authenticate assertions. The independent
    reviewer must inspect actual observations before accepting the summary.
    Source, artifact, obligation and integration guards are shared with v1.
    """
    try:
        allowed = {"format_version", "evidence_mode", "increment", "source", "profile", "report",
                   "artifacts", "observations", "items", "context", "review", "integration", "ci"}
        if (set(manifest) != allowed or type(manifest["format_version"]) is not int or manifest["format_version"] != 2
                or manifest["evidence_mode"] != "summary" or manifest["increment"] != identifier):
            fail("RM-EVIDENCE-FORMAT", f"{identifier}: explicit v2 summary mode and exact fields required")
        source = manifest["source"]
        source_identity(root, source)
        if expected_source is not None and source["commit"] != expected_source:
            fail("RM-EVIDENCE-SOURCE", f"{identifier}: stale source; expected {expected_source}")
        profile = manifest["profile"]
        if not summary_text(profile):
            fail("RM-EVIDENCE-PROFILE", f"{identifier}: explicit nonempty profile required")
        artifacts = validate_artifacts(manifest, identifier, root, source)
        observations = manifest["observations"]
        if not isinstance(observations, dict) or not observations:
            fail("RM-EVIDENCE-MISSING", f"{identifier}: no summary observations")
        if len(observations) > 10_000:
            fail("RM-LIMIT", f"{identifier}: observation count exceeds 10000")
        common = {"source", "profile", "kind", "result", "observer", "summary", "limitations"}
        additions = {"execution": {"command", "executed", "dirty", "exit_code", "checks"},
                     "review": set(), "artifact": {"artifacts"}}
        executed = False
        for key, observation in observations.items():
            location = f"{identifier}/{key}"
            if not summary_identity(key) or not isinstance(observation, dict):
                fail("RM-EVIDENCE-FORMAT", f"{location}: named observation object required")
            kind = observation.get("kind")
            if kind not in additions or set(observation) != common | additions[kind]:
                fail("RM-EVIDENCE-FORMAT", f"{location}: wrong summary observation fields")
            if observation["source"] != source:
                fail("RM-EVIDENCE-SOURCE", f"{location}: stale observation source")
            if observation["profile"] != profile:
                fail("RM-EVIDENCE-PROFILE", f"{location}: profile mismatch")
            if observation["result"] != {"execution": "passed", "review": "accepted", "artifact": "inspected"}[kind]:
                fail("RM-EVIDENCE-EXECUTION", f"{location}: incomplete/failed observations cannot close work")
            if not summary_identity(observation["observer"]) or not summary_text(observation["summary"]) or not summary_limits(observation["limitations"]):
                fail("RM-EVIDENCE-FORMAT", f"{location}: observer, concrete outcome and limits required")
            if kind == "execution":
                if observation["dirty"] is not False:
                    fail("RM-EVIDENCE-SOURCE", f"{location}: dirty or unverified source cannot qualify")
                checks = observation["checks"]
                if (not summary_text(observation["command"]) or observation["executed"] is not True
                        or type(observation["exit_code"]) is not int or observation["exit_code"] != 0
                        or not isinstance(checks, dict) or set(checks) != {"required", "executed", "passed", "failed", "skipped"}
                        or any(type(value) is not int for value in checks.values())
                        or not (checks["required"] == checks["executed"] == checks["passed"] > 0)
                        or checks["failed"] != 0 or checks["skipped"] != 0):
                    fail("RM-EVIDENCE-EXECUTION", f"{location}: actual complete passing checks and command required")
                executed = True
            elif kind == "artifact":
                deliverables = set(artifacts) - {manifest["report"]}
                if not summary_references(observation["artifacts"], deliverables):
                    fail("RM-EVIDENCE-MISSING", f"{location}: inspected hashed deliverables required")
        if not executed:
            fail("RM-EVIDENCE-EXECUTION", f"{identifier}: applicable source verification must actually run")
        items = manifest["items"]
        if not isinstance(items, dict) or any(not summary_references(refs, observations) for refs in items.values()):
            fail("RM-EVIDENCE-MISSING", f"{identifier}: unique known observation references required")
        validate_items(manifest, roadmap, identifier, profile, observations)
        validate_context(manifest, identifier)
        review = manifest["review"]
        fields = {"kind", "identity", "authors", "source", "result", "observations", "dimensions", "limitations"}
        if not isinstance(review, dict) or set(review) != fields:
            fail("RM-EVIDENCE-REVIEW", f"{identifier}: independent review summary required")
        authors = review["authors"]
        if (review["kind"] not in {"agent", "human"} or not summary_identity(review["identity"])
                or not isinstance(authors, list) or not authors or not all(summary_identity(author) for author in authors)
                or len(set(authors)) != len(authors) or review["identity"] in authors
                or review["result"] != "accepted" or not summary_limits(review["limitations"])):
            fail("RM-EVIDENCE-REVIEW", f"{identifier}: accepted review by an identified non-author required")
        if review["source"] != source:
            fail("RM-EVIDENCE-SOURCE", f"{identifier}: stale review source")
        if not summary_references(review["observations"], observations) or set(review["observations"]) != set(observations):
            fail("RM-EVIDENCE-REVIEW", f"{identifier}: review must cover every observation exactly once")
        dimensions = review["dimensions"]
        if not isinstance(dimensions, dict) or set(dimensions) != {"architecture", "independence", "quality"}:
            fail("RM-EVIDENCE-REVIEW", f"{identifier}: architecture, independence and quality review required")
        for dimension in dimensions.values():
            if (not isinstance(dimension, dict) or set(dimension) != {"result", "summary"}
                    or dimension["result"] != "accepted" or not summary_text(dimension["summary"])):
                fail("RM-EVIDENCE-REVIEW", f"{identifier}: every review dimension needs an accepted finding")
        integration = manifest["integration"]
        if not isinstance(integration, dict) or set(integration) != ({"state", "commit", "tree", "parents"}
                if integration.get("state") == "merged" else {"state"}):
            fail("RM-EVIDENCE-INTEGRATION", f"{identifier}: explicit integration identity/disposition required")
        closure = roadmap.nodes[identifier].children[-1]
        validate_integration(manifest, identifier, root, source,
                             closed=roadmap.nodes[identifier].checked or roadmap.nodes[closure].checked)
        ci = manifest["ci"]
        if (not isinstance(ci, dict) or set(ci) != {"qualification", "reason", "runs", "post_merge"}
                or not isinstance(ci["post_merge"], dict) or set(ci["post_merge"]) != {"state", "reason", "runs"}):
            fail("RM-EVIDENCE-CI", f"{identifier}: explicit qualification and post-merge dispositions required")
        validate_ci(manifest, identifier)
        if ci["post_merge"]["state"] != "pending" and integration["state"] != "merged":
            fail("RM-EVIDENCE-CI", f"{identifier}: post-merge execution/suppression requires actual integration")
    except (KeyError, TypeError, AttributeError, UnicodeError, OSError) as exc:
        fail("RM-EVIDENCE-FORMAT", f"{identifier}: malformed summary evidence: {exc}")


def verify_source_anchor(root: Path, source: str, candidate: str) -> None:
    """Narrow final-documentation exemption, never a qualification-contract waiver.

    Both commits must already exist. Normative docs, execution inputs and code
    require fresh checks. Roadmap changes may only change status or evidence links.
    This compares commits, not an uncommitted worktree, and gives no test credit.
    """
    if not SHA.fullmatch(source) or not SHA.fullmatch(candidate):
        fail("RM-EVIDENCE-SOURCE", "anchor and candidate require exact commit identities")
    for commit in (source, candidate):
        if git(root, "cat-file", "-t", commit) != "commit":
            fail("RM-EVIDENCE-SOURCE", "source anchor identities must be commit objects, not tags or trees")
    git(root, "merge-base", "--is-ancestor", source, candidate)
    changed = git(root, "diff", "--no-renames", "--name-only", "-z", source, candidate, strip=False).split("\0")
    def status_neutral(text: str) -> str:
        return "\n".join(re.sub(r"^(\s*- )\[[ xX]\]", r"\1[ ]", line)
                         for line in text.splitlines() if not line.lstrip().startswith("Evidence:"))
    for name in filter(None, changed):
        present = False
        for commit in (source, candidate):
            entry = git(root, "ls-tree", commit, "--", name, strip=False)
            present = present or bool(entry)
            if entry and entry.split()[0] != "100644":
                fail("RM-SOURCE-ANCHOR", f"{name}: non-regular or executable file mode is not a documentation-only anchor")
        if not present:
            fail("RM-SOURCE-ANCHOR", f"{name}: changed path missing from both compared trees")
        if name.startswith("docs/completion/") and Path(name).suffix in {".md", ".json", ".log", ".txt"}:
            continue
        if name.startswith("docs/implementation/") and name.endswith(("-checkpoint.md", "-local-review.md", "-independent-review.md")):
            continue
        if name.startswith("docs/roadmap/tracks/") and name.endswith(".md"):
            before = git(root, "show", f"{source}:{name}", strip=False)
            after = git(root, "show", f"{candidate}:{name}", strip=False)
            if status_neutral(before) == status_neutral(after):
                continue
        fail("RM-SOURCE-ANCHOR", f"{name}: qualification input changed; run affected checks on the new source")


def render(roadmap: Roadmap) -> str:
    """Status is a disposable deterministic derivative, never an editable ledger."""
    return json.dumps({"format_version": 1, "authority": "owning-track-markdown",
                       "nodes": [{key: getattr(node, key) for key in ("id", "checked", "parent", "children", "path", "line")}
                                 for _, node in sorted(roadmap.nodes.items())],
                       "dependencies": {key: sorted(value) for key, value in sorted(roadmap.dependencies.items())}},
                      sort_keys=True, indent=2) + "\n"


def write_view(roadmap: Roadmap, root: Path, path: Path) -> None:
    """Never overwrite authoritative tracks, source, or evidence with derived data."""
    destination = path.resolve()
    canonical_root = root.resolve()
    if not (destination.is_relative_to(canonical_root / "artifacts") or destination == canonical_root / "docs/roadmap/status.generated.json") or destination.suffix != ".json":
        fail("RM-DERIVED-PATH", "write views only to artifacts/*.json or docs/roadmap/status.generated.json")
    destination.write_text(render(roadmap))


def verify_derived(roadmap: Roadmap, path: Path) -> None:
    if not path.is_file() or path.read_text() != render(roadmap):
        fail("RM-DERIVED-CONFLICT", f"{path}: derived view differs; regenerate from authoritative Markdown")


def load(root: Path = ROOT) -> Roadmap:
    paths = sorted((root / "docs/roadmap/tracks").glob("*.md"))
    if not paths:
        fail("RM-EVIDENCE-MISSING", "no authoritative track files")
    return parse_documents({str(path.relative_to(root)): path.read_text() for path in paths})


def check(root: Path = ROOT, *, expected_sources: dict[str, str] | None = None) -> dict:
    roadmap = load(root)
    validate(roadmap, root, expected_sources=expected_sources)
    derived = root / "docs/roadmap/status.generated.json"
    if derived.exists():
        verify_derived(roadmap, derived)
    return {"increments": len(roadmap.increments), "nodes": len(roadmap.nodes),
            "checked_increments": sum(roadmap.nodes[item].checked for item in roadmap.increments),
            "checked_nodes": sum(node.checked for node in roadmap.nodes.values()),
            "derived_sha256": hashlib.sha256(render(roadmap).encode()).hexdigest(),
            "hardware_execution": "not-claimed"}
