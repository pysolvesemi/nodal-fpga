#!/usr/bin/env python3
"""Run the pinned Scala writer and verify its bound single-file source identity.

This is an authoring harness, not an independent normalization or expected-answer
builder. It never changes the independently authored corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import nf  # noqa: E402

WRITER = ROOT / "frontend/scala/src/main/scala/nodalfpga/exchange/FixtureWriter.scala"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sbt_path(path: Path) -> str:
    # runMain uses an sbt command string, not a shell. Refuse command delimiters.
    value = str(path.resolve())
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        raise ValueError("authoring paths must use only ASCII letters, digits, _, ., / and -")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--goldens", type=Path, help="independent full-envelope corpus directory")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError("output must be a new directory; existing artifacts are not overwritten")
    sbt_path(output)
    goldens = " " + sbt_path(args.goldens) if args.goldens else ""
    nf.validate_pins()
    nf.doctor("scala", nf.pins())
    before = sha256(WRITER)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nf-scala-authoring-", dir=output.parent) as temporary:
        staged = Path(temporary)
        log = nf.sbt([
            "set offline := true", "scalafmtCheckAll", "scalafmtSbtCheck", "compile",
            "Test / compile", "Test / runMain nodalfpga.exchange.WriterChecks" + goldens,
            f"runMain nodalfpga.exchange.FixtureWriter {sbt_path(staged)} {before}",
            "show scalaVersion", "show sbtVersion", "show scalaInstance",
            "show Compile / scalacOptions", "show Runtime / dependencyClasspath",
        ])
        if before != sha256(WRITER):
            raise RuntimeError("writer source changed during compilation/generation; artifacts not published")
        package = json.loads((staged / "package.json").read_text(encoding="utf-8"))
        authoring = package["body"]["authoring"]
        expected_options = {
            "scala_compiler": "org.scala-lang:scala3-compiler_3",
            "scala_version": nf.pins()["scala"],
            "json_generator": "com.fasterxml.jackson.core:jackson-core",
            "json_generator_version": "2.21.5",
            "scalac_options": "-deprecation -feature -unchecked -Werror -Wunused:all",
        }
        options = {entry["name"]: entry["value"] for entry in authoring["options"]}
        if (authoring["state"], authoring["id"], authoring["version"], authoring["implementation_sha256"]) != (
            "bound", "nodal-fpga/scala-fixture-writer", "0.1", before
        ) or options != expected_options:
            raise RuntimeError("emitted authoring identity/options do not match the verified invocation")
        for name, identity, prefix in (
            ("architecture", "semantic_id", b"nodal-fpga.arch.semantic.v1\n"),
            ("package", "build_id", b"nodal-fpga.package.build.v1\n"),
            ("design", "semantic_id", b"nodal-fpga.design.semantic.v1\n"),
        ):
            document = json.loads((staged / f"{name}.json").read_text(encoding="utf-8"))
            observed = hashlib.sha256(prefix + (staged / f"{name}.projection.json").read_bytes()).hexdigest()
            if document["body"][identity] != observed:
                raise RuntimeError(f"{name} identity differs from standard-library SHA-256")
        artifact = package["body"]["architecture"]["artifact"]
        if artifact != {"sha256": sha256(staged / "architecture.json"), "bytes": str((staged / "architecture.json").stat().st_size)}:
            raise RuntimeError("package does not bind exact emitted architecture bytes")
        (staged / "authoring.log").write_text(log, encoding="utf-8")
        (staged / "source-identity.txt").write_text(
            f"{before}  frontend/scala/src/main/scala/nodalfpga/exchange/FixtureWriter.scala\n"
            f"{sha256(Path(__file__))}  frontend/scala/write-fixtures.py\n", encoding="utf-8"
        )
        # Publish only after the source and generated binding have been verified.
        shutil.copytree(staged, output)
    print(f"Verified actual Scala-generated fixtures: {output}")
    print("This increment does not affect generated Verilog.")


if __name__ == "__main__":
    main()
