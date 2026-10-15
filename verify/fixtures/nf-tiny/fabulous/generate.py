#!/usr/bin/env python3
"""Materialize the reviewed FABulous reference input using the pinned upstream.

This is a reference-input runner, not an oracle, verifier, Nodal generator, CAD
flow, or runtime-loader qualification. FND-06 owns toolchain pins and execution.
It intentionally never computes expected truth tables or correspondence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(upstream: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(upstream), *arguments], text=True
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--shape", required=True, choices=("one", "square", "odd", "sparse"))
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error("the pinned FABulous release requires Python 3.12 or later")
    here = Path(__file__).resolve().parent
    fixture = here.parent
    manifest = json.loads((fixture / "reference.json").read_text())
    upstream = args.upstream.resolve(strict=True)
    expected_commit = manifest["upstream"]["commit"]
    if git(upstream, "rev-parse", "HEAD") != expected_commit:
        parser.error(f"upstream HEAD must be {expected_commit}")
    if git(upstream, "status", "--porcelain", "--untracked-files=all"):
        parser.error("upstream checkout must have no tracked or untracked changes")
    for entry in manifest["upstream"]["source_files"]:
        if digest(upstream / entry["path"]) != entry["sha256"]:
            parser.error(f"upstream source hash mismatch: {entry['path']}")
    for entry in manifest["input_files"]:
        if digest(fixture / entry["path"]) != entry["sha256"]:
            parser.error(f"reference input hash mismatch: {entry['path']}")
    output = args.output.resolve()
    if output.exists():
        parser.error("output must be a new directory; existing output is never overwritten")
    output.mkdir(parents=True)
    shutil.copytree(here / "BEL", output / "BEL")
    shutil.copytree(here / "Tile", output / "Tile")
    shutil.copyfile(here / f"{args.shape}.csv", output / "fabric.csv")
    (output / "Fabric").mkdir()
    shutil.copyfile(here / "LICENSE.FABulous", output / "LICENSE.FABulous")
    for entry in manifest["upstream"]["source_files"]:
        if "materialize_as" in entry:
            destination = output / entry["materialize_as"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(upstream / entry["path"], destination)
    # Use this exact source checkout, rather than another installed FABulous.
    sys.path.insert(0, str(upstream))
    os.environ["FAB_PROJ_DIR"] = str(output)
    os.environ["FAB_MODELS_PACK"] = str(output / "Fabric/models_pack.v")
    os.environ["FAB_PROJ_LANG"] = "verilog"
    from fabulous.fabric_generator.code_generator.code_generator_Verilog import (
        VerilogCodeGenerator,
    )
    from fabulous.fabric_generator.gen_fabric.gen_configmem import generateConfigMem
    from fabulous.fabric_generator.gen_fabric.gen_fabric import generateFabric
    from fabulous.fabric_generator.gen_fabric.gen_switchmatrix import genTileSwitchMatrix
    from fabulous.fabric_generator.gen_fabric.gen_tile import generateTile
    from fabulous.fabric_generator.parser.parse_csv import parseFabricCSV
    from fabulous.fabulous_settings import init_context

    context = init_context(output)
    fabric = parseFabricCSV(str(output / "fabric.csv"))
    writer = VerilogCodeGenerator()
    for name, tile in sorted(fabric.tileDic.items()):
        directory = output / "Tile" / name
        writer.outFileName = directory / f"{name}_switch_matrix.v"
        genTileSwitchMatrix(
            writer,
            tile,
            False,
            config_bit_mode=fabric.configBitMode,
            multiplexer_style=fabric.multiplexerStyle,
            default_pip_delay=fabric.generateDelayInSwitchMatrix,
        )
        writer.outFileName = directory / f"{name}_ConfigMem.v"
        generateConfigMem(
            writer,
            name,
            tile.globalConfigBits,
            directory / f"{name}_ConfigMem.csv",
            fabric.frameBitsPerRow,
            fabric.maxFramesPerCol,
        )
        writer.outFileName = directory / f"{name}.v"
        generateTile(
            writer,
            tile,
            fabric.frameBitsPerRow,
            fabric.maxFramesPerCol,
            fabric.disableUserCLK,
            fabric.configBitMode,
        )
    writer.outFileName = output / "Fabric/eFPGA.v"
    generateFabric(writer, fabric)
    rtl = [output / "BEL/LUT4c_frame_config_dffesr.v", output / "BEL/nf_tiny_io.v"]
    rtl += [output / "Fabric/models_pack.v"]
    for name in sorted(fabric.tileDic):
        rtl += [output / "Tile" / name / f"{name}{suffix}.v"
                for suffix in ("_switch_matrix", "_ConfigMem", "")]
    rtl += [output / "Fabric/eFPGA.v"]
    (output / "sources.f").write_text("\n".join(str(p.relative_to(output)) for p in rtl) + "\n")
    versions = sorted(
        {f"{dist.metadata['Name']}=={dist.version}" for dist in importlib.metadata.distributions()
         if dist.metadata.get("Name")}
    )
    record = {
        "upstream_commit": expected_commit,
        "upstream_tree": git(upstream, "rev-parse", "HEAD^{tree}"),
        "shape": args.shape,
        "python": sys.version,
        "python_distributions": versions,
        "yosys": subprocess.check_output([str(context.yosys_path), "-V"], text=True).strip(),
        "command": sys.argv,
        "status": "generated; not simulated, proven or qualified",
        "generated_rtl": [
            {"path": str(p.relative_to(output)), "sha256": digest(p)}
            for p in rtl if "Tile" in p.relative_to(output).parts or p.name == "eFPGA.v"
        ],
        "source_rtl": [
            {"path": str(p.relative_to(output)), "sha256": digest(p)}
            for p in rtl if not ("Tile" in p.relative_to(output).parts or p.name == "eFPGA.v")
        ],
    }
    (output / "generation.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Generated reference RTL in {output}; simulation/proof are separate FND-06 work.")


if __name__ == "__main__":
    main()
