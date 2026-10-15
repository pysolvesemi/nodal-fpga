"""Finite FND-06 result completeness checks, separate from its hand oracle.

This module does not run tools or derive expected semantics. It rejects missing,
substituted, duplicate and infrastructure-failure observations before a summary
can claim the independently frozen roster passed.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


class ReferenceResultError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferenceResultError("NF-REFERENCE-RESULT: " + message)


def exact_roster(expected: list[dict], observed: list[dict], *, section: str) -> dict:
    """Compare identities and intended categories, never aggregate counts alone."""
    require(isinstance(expected, list) and bool(expected), section + ": empty oracle")
    require(isinstance(observed, list), section + ": observations must be a list")
    wanted = {}
    for row in expected:
        require(isinstance(row, dict) and isinstance(row.get("id"), str)
                and bool(row["id"]), section + ": invalid oracle identity")
        require(row["id"] not in wanted, section + ": duplicate oracle identity")
        require(type(row.get("multiplicity", 1)) is int and row.get("multiplicity", 1) == 1,
                section + ": unsupported multiplicity")
        require(isinstance(row.get("expected_category"), str)
                and bool(row["expected_category"]), section + ": missing expected category")
        require(row["expected_category"] not in {
            "timeout", "crash", "compile-error", "tool-error", "output-limit",
            "storage-limit", "process-limit", "unsafe-output", "skipped", "not-run"},
            section + ": infrastructure failure cannot be an expected semantic result")
        wanted[row["id"]] = row["expected_category"]
    actual = {}
    for row in observed:
        require(isinstance(row, dict) and isinstance(row.get("id"), str),
                section + ": invalid observation identity")
        identifier = row["id"]
        require(identifier not in actual, section + ": duplicate observation " + identifier)
        require(identifier in wanted, section + ": unexpected observation " + identifier)
        require(row.get("category") == wanted[identifier],
                section + ": wrong result category for " + identifier)
        require(row.get("executed") is True, section + ": unexecuted " + identifier)
        require(isinstance(row.get("stage"), str) and bool(row["stage"]),
                section + ": missing actual stage binding " + identifier)
        actual[identifier] = row
    require(set(actual) == set(wanted), section + ": incomplete observation identities")
    return {"required": len(wanted), "executed": len(actual), "passed": len(actual),
            "failed": 0, "skipped": 0}


def verify_process(record: dict, *, expected_exit: int = 0) -> None:
    """Expected solver/simulator failure is valid only after semantic parsing."""
    require(isinstance(record, dict), "missing process result")
    require(type(expected_exit) is int and expected_exit in (0, 1), "invalid expected process status")
    require(record.get("category") == ("passed" if expected_exit == 0 else "tool-error"),
            "process did not complete normally")
    require(type(record.get("returncode")) is int
            and record["returncode"] == expected_exit, "unexpected process exit")
    for key in ("stdout_bytes", "stderr_bytes", "storage_bytes", "file_count"):
        require(type(record.get(key)) is int and record[key] >= 0,
                "invalid process measurement " + key)
    for key in ("stdout_sha256", "stderr_sha256"):
        value = record.get(key)
        require(isinstance(value, str) and len(value) == 64
                and all(c in "0123456789abcdef" for c in value),
                "invalid process capture identity " + key)


def portable_rtl_inventory(generated: Path, shape: str, *, expected_generators: dict | None = None) -> dict:
    """Bind actual output bytes without publishing the raw generation record."""
    generated = generated.resolve(strict=True)
    original = generated / "generation.json"
    require(original.is_file() and not original.is_symlink()
            and original.stat().st_size <= 8 * 1024 * 1024, "invalid generation metadata file")
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, "duplicate generation metadata key")
            value[key] = item
        return value
    record = json.loads(original.read_text(), object_pairs_hook=unique_object)
    for field in ("upstream_commit", "upstream_tree"):
        require(isinstance(record.get(field), str)
                and re.fullmatch(r"[0-9a-f]{40}", record[field]) is not None,
                "invalid upstream identity")
    require(record.get("shape") == shape, "generation shape differs")
    if expected_generators is not None:
        require(record.get("generator_sources") == expected_generators,
                "actual generator source identities differ")
        require(record.get("execution_adjustments") == ["create-official-project-marker-before-init-context"],
                "unexpected generation execution adjustment")
    roster = []
    seen = set()
    for category in ("source_rtl", "generated_rtl"):
        rows = record.get(category)
        require(isinstance(rows, list) and 0 < len(rows) <= 256, "missing or excessive actual RTL inventory")
        for row in rows:
            name = row.get("path")
            require(isinstance(name, str) and name and "\\" not in name
                    and not Path(name).is_absolute() and ".." not in Path(name).parts,
                    "unsafe portable RTL path")
            require(name not in seen, "duplicate RTL inventory entry")
            seen.add(name)
            path = generated / name
            require(all(not parent.is_symlink() for parent in path.parents
                        if parent != generated and parent.is_relative_to(generated)),
                    "symlink directory in RTL artifact")
            require(path.is_file() and not path.is_symlink()
                    and path.resolve().is_relative_to(generated), "unsafe RTL artifact")
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            require(digest == row.get("sha256"), "actual RTL inventory digest differs")
            roster.append({"path": name, "kind": category, "sha256": digest,
                           "bytes": len(data)})
    source_path = generated / "sources.f"
    require(source_path.is_file() and not source_path.is_symlink()
            and source_path.stat().st_size < 1024 * 1024, "invalid source list")
    sources = source_path.read_text().splitlines()
    require(len(sources) == len(set(sources)) and set(sources) == seen,
            "actual source list does not exactly cover RTL inventory")
    return {"shape": shape, "upstream_commit": record["upstream_commit"],
            "generator_sources": expected_generators,
            "execution_adjustments": record.get("execution_adjustments", []),
            "upstream_tree": record["upstream_tree"], "artifacts": sorted(roster, key=lambda x: x["path"]),
            "sources_sha256": hashlib.sha256((generated / "sources.f").read_bytes()).hexdigest(),
            "scope": "Portable inventory of actual bytes; original generation metadata stays local."}
