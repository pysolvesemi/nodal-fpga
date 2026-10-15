"""Orchestrate the finite independent Foundation reference corpus.

Expected semantics live in reviewed fixture manifests, never in generation or
normalization helpers. Raw tool captures stay local. This module joins distinct
generation, compilation, graph, simulation, formal and mutation observations;
none substitutes for another.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

from reference_results import ReferenceResultError, exact_roster, portable_rtl_inventory, require, verify_process

SHAPES = ("one", "square", "odd", "sparse")
PROFILE = "nf-tiny-foundation/1"


def fixture_module(root: Path, name: str):
    path = root / "verify/fixtures/fnd-06" / (name + ".py")
    spec = importlib.util.spec_from_file_location("fnd06_" + name, path)
    require(spec is not None and spec.loader is not None, "missing fixture module " + name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def source_identity(root: Path) -> dict:
    """Capture actual source bytes as well as HEAD; dirty work is never clean credit."""
    from nf import metadata
    state = metadata(root)
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root).decode().split("\0")
    prefixes = ("tools/", "toolchains/", "verify/fixtures/nf-tiny/",
                "verify/fixtures/assumptions/", "verify/fixtures/fnd-06/",
                "tests/foundation/", "core/rust/")
    files = {}
    for name in sorted(set(names)):
        if name and (name.startswith(prefixes) or name in {"nf", "Cargo.toml", "Cargo.lock", "rust-toolchain.toml"}):
            path = root / name
            require(path.is_file() and not path.is_symlink(), "nonregular source input " + name)
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"commit": state["head"], "tree": state["tree"], "dirty": state["dirty"],
            "profile": PROFILE, "input_sha256": files}


def sources(generated: Path, mount: str = "/inputs/generated") -> list[str]:
    rows = (generated / "sources.f").read_text().splitlines()
    require(rows and len(rows) == len(set(rows)), "missing or duplicate compile source")
    for row in rows:
        require(re.fullmatch(r"[A-Za-z0-9_./-]+", row) is not None
                and not Path(row).is_absolute() and ".." not in Path(row).parts,
                "unsafe compiler source path")
        require((generated / row).is_file(), "missing compiler source")
    return [mount + "/" + row for row in rows]


def input_inventory(inputs: dict | None) -> dict:
    """Bind every explicit stage input, including testbenches and derived RTL."""
    records, total = {}, 0
    for destination, source in sorted((inputs or {}).items()):
        source = Path(source)
        require(not source.is_symlink() and source.exists(), "unsafe stage input")
        paths = sorted(source.rglob("*")) if source.is_dir() else [source]
        files = {}
        for path in paths:
            require(not path.is_symlink(), "symlink in stage input")
            if path.is_dir():
                continue
            require(path.is_file(), "nonregular stage input")
            size = path.stat().st_size
            total += size
            require(total <= 512 * 1024**2 and len(files) < 8192, "stage input exceeds bound")
            name = str(path.relative_to(source)) if source.is_dir() else "."
            files[name] = {"bytes": size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        require(bool(files), "empty stage input")
        records[destination] = files
    return records


class Session:
    def __init__(self, root: Path, output: Path, environment):
        self.root, self.output, self.environment = root, output, environment
        self.processes = []
        contract = fixture_module(root, "manifest").load(root)["obligations"]
        self.contract_binding = {"profile": PROFILE,
            "immutable_inputs": contract["immutable_bindings"],
            "profile_assumptions": contract["assumptions"],
            "scope": "Whole-profile input dependencies; individual assumption execution is established only by named witness obligations"}
        self.source = source_identity(root)
        # Snapshot used by isolated tools must equal the actual source observed
        # by host-side parsers. No later edit may silently change either side.
        for name, digest in environment.source_inventory.items():
            path = root / name
            require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                    "source snapshot differs before execution: " + name)
        (output / "source-before.json").write_text(json.dumps(self.source, indent=2) + "\n")

    def execute(self, identifier: str, argv: list[str], *, inputs=None, expected_exit=0, limits=None):
        from reference_runner import Limits
        require(re.fullmatch(r"[A-Za-z0-9_.-]+", identifier) is not None,
                "unsafe stage name")
        require(source_identity(self.root) == self.source,
                "source changed during reference execution")
        bound_inputs = input_inventory(inputs)
        result = self.environment.run(argv, self.output / identifier,
                                      inputs=inputs, limits=limits or Limits())
        require(input_inventory(inputs) == bound_inputs, "stage input changed during execution")
        portable = result.portable()
        record = {"id": identifier, "command": argv, "process": portable, "input_inventory": bound_inputs,
                  "source": {k: self.source[k] for k in ("commit", "tree", "dirty")},
                  "contract": self.contract_binding,
                  "runtime_profile": self.environment.profile if hasattr(self.environment, "profile") else "fnd06-reference-linux-x86_64-cp312",
                  "runtime_inventory_sha256": self.environment.runtime_inventory_sha256}
        self.processes.append(record)
        (self.output / "processes.json").write_text(json.dumps(self.processes, indent=2) + "\n")
        verify_process(portable, expected_exit=expected_exit)
        for kind in ("stdout", "stderr"):
            capture = Path(getattr(result, kind + "_path"))
            require(capture.is_file() and not capture.is_symlink()
                    and capture.stat().st_size == portable[kind + "_bytes"]
                    and hashlib.sha256(capture.read_bytes()).hexdigest() == portable[kind + "_sha256"],
                    "captured process stream differs: " + kind)
        return result, self.output / identifier / "work"

    def generate(self, run: int, shape: str) -> tuple[Path, dict]:
        command = [self.environment.command("python"),
                   "/source/verify/fixtures/fnd-06/generate.py",
                   "--upstream", "/upstream", "--output", "/work/generated", "--shape", shape]
        _, work = self.execute(f"run{run}-generate-{shape}", command)
        generated = work / "generated"
        generators = {name: {"path": path, "sha256": self.source["input_sha256"][path]}
                      for name, path in {
                          "historical": "verify/fixtures/nf-tiny/fabulous/generate.py",
                          "adapter": "verify/fixtures/fnd-06/generate.py"}.items()}
        inventory = portable_rtl_inventory(generated, shape, expected_generators=generators)
        reference = json.loads((self.root / "verify/fixtures/nf-tiny/reference.json").read_text())
        require(inventory["upstream_commit"] == reference["upstream"]["commit"]
                and inventory["upstream_tree"] == reference["upstream"]["tree"],
                "generated reference revision changed")
        return generated, inventory

    def compile_structure(self, run: int, shape: str, generated: Path) -> tuple[dict, dict]:
        source_list = sources(generated)
        compile_result, compile_work = self.execute(f"run{run}-compile-{shape}",
            [self.environment.command("iverilog"), "-g2012", "-s", "eFPGA",
             "-o", "/work/fabric.vvp", *source_list], inputs={"/inputs/generated": generated})
        # Preserve the pre-process candidate graph separately; do not flatten,
        # synthesize, clean or infer a new correspondence from the candidate.
        script = ("read_verilog " + " ".join(source_list)
                  + "; hierarchy -check -top eFPGA; write_rtlil /work/preproc.il;"
                  " proc; write_json /work/structure.json")
        graph_result, work = self.execute(f"run{run}-structure-{shape}",
            [self.environment.command("yosys"), "-Q", "-T", "-p", script],
            inputs={"/inputs/generated": generated})
        structure = fixture_module(self.root, "structure")
        checked = structure.check_shape(shape, structure.read_json(work / "structure.json"),
            source_root=generated,
            source_hashes={name: hashlib.sha256((generated / name).read_bytes()).hexdigest()
                           for name in (generated / "sources.f").read_text().splitlines()},
            source_mount="/inputs/generated")
        (work / "checked.json").write_text(json.dumps(checked, indent=2) + "\n")
        def artifact(path):
            require(path.is_file() and not path.is_symlink() and path.stat().st_size > 0,
                    "missing or empty structural stage artifact: " + path.name)
            return {"name": path.name, "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        return checked, {
            "compile": {"process": compile_result.portable(),
                        "artifacts": [artifact(compile_work / "fabric.vvp")]},
            "graph": {"process": graph_result.portable(),
                      "artifacts": [artifact(work / name) for name in
                                    ("preproc.il", "structure.json", "checked.json")]}}



def observation(identifier: str, stage: str, detail=None, category="passed") -> dict:
    return {"id": identifier, "category": category, "executed": True,
            "stage": stage, "detail": detail if detail is not None else {}}


def validate_run(bundle: dict, results: dict) -> dict:
    """No missing identity or infrastructure error can become completed credit."""
    manifest = fixture_module(Path(__file__).resolve().parents[1], "manifest")
    return {section: exact_roster(list(manifest.expected_records(bundle, section).values()),
                                 results[section], section=section)
            for section in ("structural", "simulation", "supplemental_simulation", "formal")}


def compare_repeats(first: dict, second: dict) -> dict:
    require(set(first) == set(second) == set(SHAPES), "repeat shape set differs")
    for shape in SHAPES:
        require(first[shape] == second[shape], "actual generated RTL is not reproducible: " + shape)
    return {"shapes": len(SHAPES), "fresh_runs_per_shape": 2,
            "actual_rtl_and_source_lists_byte_identical": True}


def obligation_coverage(root: Path, bundle: dict, observations: list[dict]) -> dict:
    """Bind completed named witnesses to inherited obligations and ledger IDs."""
    rows = []
    for name in ("structural", "simulation", "supplemental_simulation", "formal"):
        rows.extend(bundle["obligations"][name])
    rows.extend(bundle["semantic_cases"]["negative_cases"])
    rows.extend(bundle["mutations"]["mutations"])
    rows.extend(bundle["mutations"]["controls"])
    planned = {row["id"]: row for row in rows}
    ledger = json.loads((root / "verify/fixtures/assumptions/ledger.json").read_text())
    by_obligation = {}
    for assumption in ledger["records"]:
        for obligation in assumption["required_obligations"]:
            by_obligation.setdefault(obligation["id"], []).append(assumption["id"])
    covered = {}
    for observed in observations:
        require(observed["id"] in planned and observed.get("executed") is True,
                "unknown or unexecuted coverage witness")
        plan = planned[observed["id"]]
        require(observed["category"] == plan["expected_category"], "invalid coverage category")
        obligation = plan["obligation"]
        covered.setdefault(obligation, []).append({"id": observed["id"],
            "stage": observed["stage"], "assumptions": by_obligation.get(obligation, [])})
    inherited = {row["id"] for row in bundle["obligations"]["inherited_obligations"]}
    require(inherited <= set(covered), "inherited obligation lacks executed witnesses")
    return {"inherited_required": len(inherited), "inherited_executed": len(inherited),
            "obligations": covered}


def check_reference(root: Path) -> dict:
    """Execute all independent finite stages; return only a concise summary.

    Detailed process and witness records stay in ignored local artifacts. A
    dirty source run is development evidence only; NF_EXPECT_SHA additionally
    enforces exact clean qualification via both source and environment checks.
    """
    from reference_environment import ReferenceEnvironment
    from reference_behavior_execution import run_behavior
    from reference_model_execution import run_models
    from reference_mutations import run_mutations, verify_published_mutations
    from reference_archive import verify_archive
    root = root.resolve(strict=True)
    bundle = fixture_module(root, "manifest").load(root)
    artifacts = root / "artifacts/fnd06-reference"
    artifacts.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="run-", dir=artifacts))
    cache = Path(os.environ.get("NF_REFERENCE_ROOT", str(root / ".cache/toolchains/reference")))
    upstream_value = os.environ.get("FABULOUS_UPSTREAM")
    require(bool(upstream_value), "FABULOUS_UPSTREAM must name the qualified pinned source")
    environment = ReferenceEnvironment(root, cache, Path(upstream_value))
    session = Session(root, output, environment)
    started = time.monotonic()
    runs, inventories, stages = [], [], []
    archived_rtl = []
    generated_runs = []
    try:
        for number in (1, 2):
            generated, inventory, structural = {}, {}, []
            for shape in SHAPES:
                generated[shape], inventory[shape] = session.generate(number, shape)
                archived_rtl.append({"run": number, "shape": shape,
                    **verify_archive(root, shape, generated[shape], inventory[shape])})
                stages.append(observation(f"G-{shape}/run-{number}",
                                          f"run{number}-generate-{shape}", inventory[shape]))
                checked, costs = session.compile_structure(number, shape, generated[shape])
                stages.append(observation(f"COMPILE-{shape}/run-{number}",
                                          f"run{number}-compile-{shape}", costs["compile"]))
                stages.append(observation(f"GRAPH-{shape}/run-{number}",
                                          f"run{number}-structure-{shape}", costs["graph"]))
                structural.extend(observation(identifier, f"run{number}-structure-{shape}", detail)
                                  for identifier, detail in checked["records"].items())
            behavior = run_behavior(session, number, generated)
            result = {"structural": structural, **behavior}
            result["counts"] = validate_run(bundle, result)
            stages.extend(behavior["stages"])
            runs.append(result)
            inventories.append(inventory)
            generated_runs.append(generated)
            (output / f"run{number}-results.json").write_text(json.dumps(result, indent=2) + "\n")
        repetition = compare_repeats(*inventories)
        # The same immutable witness roster is independently evaluated for each
        # fresh generated design, rather than doubling a cached result count.
        require(runs[0]["counts"] == runs[1]["counts"], "repeat coverage differs")
        first_graph = {row["id"]: row["detail"] for row in runs[0]["structural"]}
        second_graph = {row["id"]: row["detail"] for row in runs[1]["structural"]}
        require(first_graph == second_graph, "actual structural correspondence is not reproducible")
        for section in ("simulation", "supplemental_simulation"):
            def semantic_projection(rows):
                return {row["id"]: {key: row[key] for key in ("category", "expected", "observed", "time")
                                    if key in row} for row in rows}
            require(semantic_projection(runs[0][section]) == semantic_projection(runs[1][section]),
                    "actual repeated semantic observations differ: " + section)
        model = run_models(session)
        semantic = model["model"]["negatives"] + runs[0]["negative_cases"]
        semantic_counts = exact_roster(bundle["semantic_cases"]["negative_cases"], semantic,
                                       section="semantic")
        baseline = {row["id"]: row for section in
                    ("structural", "simulation", "supplemental_simulation", "mutation_baselines")
                    for row in runs[0][section]}
        mutations = run_mutations(session, generated_runs[0], baseline=baseline,
                                  alias_hook=model["alias_hook"])
        archived_mutations = verify_published_mutations(root, mutations)
        mutant_counts = exact_roster(bundle["mutations"]["mutations"], mutations,
                                     section="mutations")
        for run in runs:
            exact_roster(bundle["mutations"]["controls"], run["controls"], section="controls")
        stage_counts = exact_roster(bundle["obligations"]["stages"], stages, section="stages")
        coverage = obligation_coverage(root, bundle,
            [row for section in ("structural", "simulation", "supplemental_simulation", "formal")
             for row in runs[0][section]] + semantic + mutations + runs[0]["controls"])
        after = source_identity(root)
        require(session.source == after, "source changed during reference suite")
        (output / "source-after.json").write_text(json.dumps(after, indent=2) + "\n")
        details = {"source": session.source, "runs": runs, "stages": stages,
                   "semantic": semantic, "mutations": mutations,
                   "model": {k: v for k, v in model.items() if k != "alias_hook"},
                   "repetition": repetition, "coverage": coverage,
                   "portable_archive": {"rtl": archived_rtl, "mutations": archived_mutations}}
        (output / "results.json").write_text(json.dumps(details, indent=2) + "\n")
        summary = {"profile": PROFILE, "status": "passed", "source": session.source,
                   "counts_per_run": runs[0]["counts"], "semantic": semantic_counts,
                   "mutations": mutant_counts, "stages": stage_counts,
                   "inherited_obligations_executed": coverage["inherited_executed"],
                   "repetition": repetition,
                   "portable_archive": {"rtl": archived_rtl, "mutations": archived_mutations},
                   "wall_seconds": time.monotonic() - started,
                   "scope": "Finite reference corpus; no Nodal production fabric, PPA or hostile-code claim",
                   "raw_observations": "local-only; not repository evidence"}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        return summary
    except Exception as error:
        (output / "failure.json").write_text(json.dumps({"status": "failed",
            "error_type": type(error).__name__, "detail": str(error),
            "processes_completed": len(session.processes)}, indent=2) + "\n")
        raise
