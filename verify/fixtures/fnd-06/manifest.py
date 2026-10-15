"""Read the frozen, independently authored FND-06 contract, never DUT output.

This module validates input fixtures only. It neither runs tools nor qualifies
observations. Roster identities and expected categories are exposed to the
separate execution-receipt checker. Changing a frozen hash requires review.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


class ManifestError(ValueError):
    """A missing, changed, duplicate or inconsistent frozen contract."""


# Populated from reviewed candidate bytes at freeze; not regenerated at runtime.
FROZEN_SHA256 = {'obligations': '44e1dc683b9b25cb02818ff4d629adb0700ed7fe82321e1de6e603e35542a68d', 'semantic_cases': '838f762b80cdb021c8e3264cdbc87b948a9b57821df2c0e059a8ce856778741d', 'mutations': '3b3db216281c9179e2eee27a1b89d7629dae999d73bd52d6cbba45db2ac70ee9'}
FROZEN_CONTENT_SHA256 = {'obligations': '44bd9ecc93e5f61a4e761f5a85caa19298dbdb134e27680feaf16c95a13d2bc0', 'semantic_cases': '3e4322f31210d66c4a04fb52563597a3725040ab726805f20746063edc3546c1', 'mutations': 'f40ab10bfa6212f7fb1e9c0c50cdbe1e446ff4b0c3333aa6a497e2e6b39130d4'}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _unique(rows, context):
    ids = [row.get("id") for row in rows]
    if any(not isinstance(i, str) or not i for i in ids):
        raise ManifestError(f"{context}: missing stable ID")
    if len(ids) != len(set(ids)):
        raise ManifestError(f"{context}: duplicate stable ID")
    return set(ids)


def validate_bundle(bundle, repository_root=None):
    """Validate a parsed bundle; raise ManifestError on any changed contract.

    bundle keys are obligations, semantic_cases and mutations. Returns the
    bundle unchanged. A supplied root additionally checks immutable inputs.
    """
    if set(bundle) != {"obligations", "semantic_cases", "mutations"}:
        raise ManifestError("missing or unexpected manifest")
    ob, semantic, mutations = (bundle[k] for k in
                                ("obligations", "semantic_cases", "mutations"))
    for name, doc in bundle.items():
        if doc.get("format_version") != 1 or doc.get("status") != "planned-independent-oracle":
            raise ManifestError(f"{name}: unsupported version or execution-state claim")
    for section in ("inherited_obligations", "leaves", "formal", "structural", "simulation", "stages", "supplemental_simulation"):
        _unique(ob[section], section)
    for section in ("onehot", "negative_cases", "walking_storage", "instance_words"):
        _unique(semantic[section], section)
    for section in ("mutations", "controls"):
        _unique(mutations[section], section)
    formal_counts = Counter(row["kind"] for row in ob["formal"])
    if formal_counts != {"assert": 7, "assume": 1, "cover": 21}:
        raise ManifestError("formal: zero or wrong obligation count")
    if len({row["top"] for row in ob["formal"]}) != 6:
        raise ManifestError("formal: missing or extra top")
    expected_lengths = {"inherited_obligations": 15, "leaves": 17,
                        "instances": 17, "structural": 1035,
                        "simulation": 1847, "stages": 32, "supplemental_simulation": 36}
    for key, count in expected_lengths.items():
        if len(ob[key]) != count:
            raise ManifestError(f"{key}: zero or wrong obligation count")
    if len(semantic["onehot"]) != 256 or len(semantic["negative_cases"]) != 14:
        raise ManifestError("semantic: zero or wrong obligation count")
    if len(mutations["mutations"]) != 12 or len(mutations["controls"]) != 3:
        raise ManifestError("mutation/control: zero or wrong obligation count")
    all_obligations = _unique(ob["inherited_obligations"], "obligations") | set(ob["supplemental_obligations"])
    known_ids = set()
    for rows in (ob["formal"], ob["structural"], ob["simulation"], ob["supplemental_simulation"], semantic["negative_cases"], mutations["mutations"], mutations["controls"]):
        for row in rows:
            if row["id"] in known_ids:
                raise ManifestError("duplicate ID across execution rosters: " + row["id"])
            known_ids.add(row["id"])
            if row["obligation"] not in all_obligations or row["multiplicity"] != 1:
                raise ManifestError("unknown obligation or invalid multiplicity: " + row["id"])
    for row in mutations["mutations"]:
        if not set(row["required_failing_witnesses"]) <= known_ids:
            raise ManifestError("mutation refers to missing witness: " + row["id"])
    # Exact content comparison rejects substitutions even if all counts agree.
    for name, doc in bundle.items():
        if hashlib.sha256(_canonical(doc)).hexdigest() != FROZEN_CONTENT_SHA256[name]:
            raise ManifestError(name + ": frozen content mismatch; independent review required")
    if repository_root is not None:
        root = Path(repository_root)
        for binding in ob["immutable_bindings"]:
            path = root / binding["path"]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
                raise ManifestError("immutable input mismatch: " + binding["path"])
    return bundle


def load(repository_root=None):
    """Load exact frozen bytes from the repository, with immutable source checks."""
    root = Path(repository_root) if repository_root else Path(__file__).resolve().parents[3]
    directory = root / "verify/fixtures/fnd-06"
    bundle = {}
    for name, expected in FROZEN_SHA256.items():
        path = directory / (name + ".json")
        if not path.is_file():
            raise ManifestError("missing manifest: " + name)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ManifestError("frozen byte mismatch: " + name)
        bundle[name] = json.loads(data)
    return validate_bundle(bundle, root)


def expected_records(bundle, stage):
    """Expose exact IDs/categories for one execution stage; no results implied."""
    validate_bundle(bundle)
    ob = bundle["obligations"]
    choices = {"formal": ob["formal"], "structural": ob["structural"],
               "simulation": ob["simulation"],
               "supplemental_simulation": ob["supplemental_simulation"],
               "semantic": bundle["semantic_cases"]["negative_cases"],
               "mutations": bundle["mutations"]["mutations"],
               "controls": bundle["mutations"]["controls"],
               "stages": ob["stages"]}
    if stage not in choices:
        raise ManifestError("unknown stage: " + stage)
    return {row["id"]: row for row in choices[stage]}
