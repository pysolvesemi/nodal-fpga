"""Independent test-input construction. Never imports production implementation.

Literal goldens remain expected byte outputs. json.dumps below constructs changed
inputs and small explicitly projected test cases, not candidate-derived goldens.
Python scalar-key order equals unsigned UTF-8 order for valid Unicode scalars.
All schema-declared set orders in dynamic accepted cases are authored explicitly.
"""
from pathlib import Path
import copy
import hashlib
import json
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "verify/fixtures/exchange"
GOLDENS = FIXTURES / "goldens"
ALGORITHM = FIXTURES / "algorithm"
BINARY = Path(os.environ.get("NF_EXCHANGE_BIN", str(ROOT / "target/debug/nf-exchange")))
P0 = {"span": None, "display": None}
PREFIXES = {"arch": b"nodal-fpga.arch.semantic.v1\n", "package": b"nodal-fpga.package.build.v1\n", "design": b"nodal-fpga.design.semantic.v1\n"}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def fixture(name="architecture"):
    return json.loads((GOLDENS / (name + ".canonical.json")).read_bytes())


def at(root, path):
    for part in path:
        root = root[part]
    return root


def pointer(path):
    return "".join("/" + str(x).replace("~", "~0").replace("/", "~1") for x in path)


def changed(doc, path, value):
    result = copy.deepcopy(doc)
    at(result, path[:-1])[path[-1]] = value
    return result


def architecture_projection(doc):
    """Explicit schema-directed omission for dynamic independent test inputs."""
    out = copy.deepcopy(doc)
    del out["annotations"]
    del out["optional_features"]
    body = out["body"]
    del body["semantic_id"]

    def provenance(record):
        del record["provenance"]

    def ref(record):
        provenance(record)

    def endpoint(record):
        provenance(record)
        ref(record["resource"])

    def connection(record):
        provenance(record)
        endpoint(record["destination"])
        for source in record["sources"]:
            endpoint(source)
        if record["selector"] is not None:
            provenance(record["selector"])

    def instance(record):
        provenance(record)
        for domain in record["domains"]:
            provenance(domain)

    provenance(body)
    for domain in body["domains"]:
        provenance(domain)
    for kind in body["resource_types"]:
        provenance(kind)
        for pin in kind["pins"]:
            provenance(pin)
    for root in body["roots"]:
        instance(root)
    for record in body["connections"]:
        connection(record)
    for template in body["templates"]:
        provenance(template)
        for child in template["children"]:
            instance(child)
        for resource in template["resources"]:
            provenance(resource)
            if resource["alias_of"] is not None:
                ref(resource["alias_of"])
            for domain in resource["domains"]:
                provenance(domain)
        for group in template["mode_groups"]:
            provenance(group)
            for member in group["resources"]:
                ref(member)
        for storage in template["storage"]:
            provenance(storage)
            ref(storage["owner"])
        for feature in template["features"]:
            provenance(feature)
            ref(feature["owner"])
            if feature["alias_of"] is not None:
                provenance(feature["alias_of"])
            for guard in feature["guard"]:
                provenance(guard)
        for record in template["connections"]:
            connection(record)
    return out


def resign_architecture(doc):
    out = copy.deepcopy(doc)
    out["body"]["semantic_id"] = hashlib.sha256(PREFIXES["arch"] + encoded(architecture_projection(out))).hexdigest()
    return out


def package_projection(doc):
    out = copy.deepcopy(doc)
    del out["annotations"]
    del out["optional_features"]
    del out["body"]["build_id"]
    return out


def resign_package(doc):
    out = copy.deepcopy(doc)
    out["body"]["build_id"] = hashlib.sha256(PREFIXES["package"] + encoded(package_projection(out))).hexdigest()
    return out


def design_projection(doc):
    out = copy.deepcopy(doc)
    del out["annotations"]
    del out["optional_features"]
    body = out["body"]
    del body["semantic_id"]
    del body["provenance"]
    for record in body["cells"] + body["ports"]:
        del record["provenance"]
    for net in body["nets"]:
        del net["provenance"]
        del net["driver"]["provenance"]
        for load in net["loads"]:
            del load["provenance"]
    return out


def resign_design(doc):
    out = copy.deepcopy(doc)
    out["body"]["semantic_id"] = hashlib.sha256(PREFIXES["design"] + encoded(design_projection(out))).hexdigest()
    return out


class ExchangeCLI(unittest.TestCase):
    """Run an already-built public executable; never starts concurrent builds."""
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file():
            raise AssertionError("Required nf-exchange binary missing: build through the designated coordinator, then set NF_EXCHANGE_BIN or use target/debug/nf-exchange")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nf-exchange-independent-")
        self.addCleanup(self.temporary.cleanup)
        self.temp = Path(self.temporary.name)
        self.serial = 0

    def invoke(self, operation, data, output="canonical", limits=None, package=None, artifacts=None, extra=()):
        self.serial += 1
        path = self.temp / ("input-" + str(self.serial) + ".json")
        path.write_bytes(encoded(data) if isinstance(data, dict) else data)
        args = [str(BINARY), operation, str(path)]
        if output is not None:
            args += ["--output", output]
        if limits is not None:
            args += ["--limits", json.dumps(limits, separators=(",", ":"))]
        if package is not None:
            manifest = self.temp / ("manifest-" + str(self.serial) + ".json")
            manifest.write_bytes(encoded(package) if isinstance(package, dict) else package)
            args += ["--package", str(manifest)]
        if artifacts is None and operation in ("package", "design"):
            artifact = (GOLDENS / "architecture.raw.json").read_bytes()
            artifacts = [(hashlib.sha256(artifact).hexdigest(), artifact)]
        for i, (digest, content) in enumerate(artifacts or []):
            artifact = self.temp / ("artifact-" + str(self.serial) + "-" + str(i))
            artifact.write_bytes(content)
            args += ["--artifact", digest + "=" + str(artifact)]
        args += list(extra)
        return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)

    def accepts(self, operation, data, expected=None, **kwargs):
        result = self.invoke(operation, data, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        if expected is not None:
            self.assertEqual(result.stdout, expected)
        return result.stdout

    def rejects(self, operation, data, code, path=None, stage=None, core=None, **kwargs):
        result = self.invoke(operation, data, **kwargs)
        self.assertNotEqual(result.returncode, 0, "invalid input was accepted")
        self.assertEqual(result.stdout, b"", "partial accepted output leaked on failure")
        error = json.loads(result.stderr)
        self.assertEqual(error["code"], code, error)
        self.assertIsInstance(error["pointer"], str)
        self.assertTrue(error["pointer"] == "" or error["pointer"].startswith("/"), error)
        if path is not None:
            self.assertEqual(error["pointer"], pointer(path), error)
        if stage is not None:
            self.assertEqual(error["stage"], stage, error)
        self.assertTrue(error["remedy"], error)
        if core is not None:
            self.assertIn(core, [d["code"] for d in error["core"]], error)
        return error
