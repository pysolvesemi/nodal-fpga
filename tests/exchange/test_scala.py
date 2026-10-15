"""Consume real separately generated Scala artifacts against independent meanings.

Set NF_EXCHANGE_SCALA_DIR to the verified authoring harness output. Missing output
is an explicit prerequisite failure, never a skipped required conformance check.
This suite neither invokes Scala/build tools nor derives goldens from its output.
"""
from pathlib import Path
import hashlib
import json
import os
from support import (GOLDENS, ROOT, ExchangeCLI, architecture_projection, encoded,
                     fixture, package_projection, design_projection, PREFIXES)


class ScalaCrossLanguageConformance(ExchangeCLI):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        path=os.environ.get("NF_EXCHANGE_SCALA_DIR")
        if not path:
            raise AssertionError("NF_EXCHANGE_SCALA_DIR must identify actual verified Scala authoring output")
        cls.scala=Path(path)
        for name in ["architecture.json","package.json","design.json"]:
            if not (cls.scala/name).is_file():
                raise AssertionError("Missing required Scala artifact: "+str(cls.scala/name))

    def test_actual_scala_architecture_equals_independent_semantics(self):
        raw=(self.scala/"architecture.json").read_bytes()
        expected_projection=(GOLDENS/"architecture.projection.json").read_bytes()
        source=json.loads(raw)
        self.assertEqual(encoded(architecture_projection(source)),expected_projection)
        self.assertEqual(source["body"]["semantic_id"],"0c5e51acf90f91981b7e3375e5ab58b05d20020aa51a594008f8d7a30e1c80a4")
        self.accepts("arch",raw,expected_projection,output="projection")
        accepted=json.loads(self.accepts("arch",raw))
        self.assertEqual(accepted["body"]["provenance"],source["body"]["provenance"])
        self.assertEqual(accepted["annotations"],source["annotations"])
        self.assertEqual([r["name"] for r in accepted["body"]["roots"]],["t0","t1","t2"])
        self.assertEqual([s["resource"]["name"] for s in accepted["body"]["templates"][0]["connections"][0]["sources"]],["east","local","west"])

    def test_actual_scala_package_source_identity_and_exact_artifact(self):
        arch=(self.scala/"architecture.json").read_bytes()
        package_bytes=(self.scala/"package.json").read_bytes();package=json.loads(package_bytes)
        descriptor=package["body"]["architecture"]["artifact"]
        self.assertEqual(descriptor,{"bytes":str(len(arch)),"sha256":hashlib.sha256(arch).hexdigest()})
        author=package["body"]["authoring"]
        self.assertEqual(author["state"],"bound")
        self.assertEqual(author["id"],"nodal-fpga/scala-fixture-writer")
        self.assertEqual(author["version"],"0.1")
        options={o["name"]:o["value"] for o in author["options"]}
        self.assertEqual(options["scala_compiler"],"org.scala-lang:scala3-compiler_3")
        self.assertEqual(options["scala_version"],"3.3.8")
        # Writer-source path is explicitly agreed with the authoring owner; no
        # candidate output is treated as an expected source hash.
        writer=ROOT/"frontend/scala/src/main/scala/nodalfpga/exchange/FixtureWriter.scala"
        self.assertTrue(writer.is_file())
        self.assertEqual(author["implementation_sha256"],hashlib.sha256(writer.read_bytes()).hexdigest())
        expected=hashlib.sha256(PREFIXES["package"]+encoded(package_projection(package))).hexdigest()
        self.assertEqual(package["body"]["build_id"],expected)
        self.accepts("package",package_bytes,encoded(package),artifacts=[(descriptor["sha256"],arch)])

    def test_actual_scala_design_matches_hand_semantics_after_exact_rebinding(self):
        arch=(self.scala/"architecture.json").read_bytes()
        package_bytes=(self.scala/"package.json").read_bytes();package=json.loads(package_bytes)
        design_bytes=(self.scala/"design.json").read_bytes();design=json.loads(design_bytes)
        self.assertEqual(design["body"]["target_build_id"],package["body"]["build_id"])
        # Only the already expected target_build_id is rebound; all mapped design
        # semantic content must match the independent hand-authored projection.
        expected=design_projection(fixture("design"))
        expected["body"]["target_build_id"]=package["body"]["build_id"]
        self.assertEqual(design_projection(design),expected)
        expected_id=hashlib.sha256(PREFIXES["design"]+encoded(expected)).hexdigest()
        self.assertEqual(design["body"]["semantic_id"],expected_id)
        self.accepts("design",design_bytes,encoded(design),package=package_bytes,
                     artifacts=[(hashlib.sha256(arch).hexdigest(),arch)])
