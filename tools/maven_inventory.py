"""Reviewed Scala authoring graph; no part of this graph is a Rust runtime input."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import zipfile
from check_boundaries import BoundaryError, _rust_code

CENTRAL = "https://repo.maven.apache.org/maven2/"
ALLOWED_IMPORTS = {
    "import com.fasterxml.jackson.core.{JsonEncoding, JsonFactoryBuilder}",
    "import com.fasterxml.jackson.core.io.{CharacterEscapes, SerializedString}",
    "import com.fasterxml.jackson.core.json.JsonWriteFeature",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(detail):
    raise BoundaryError("NF-SCALA-GRAPH: " + detail)


def load(root):
    data = json.loads((root / "tools/dependencies/scala-authoring.json").read_text())
    if data["schema"] != 1 or data["repository"] != CENTRAL:
        fail("unknown authoring inventory")
    return data


def check_static(root):
    data = load(root)
    for name, expected in data["build_inputs"].items():
        if sha(root / name) != expected:
            fail(f"reviewed build input changed: {name}")
    for source in (root / "frontend/scala/src").rglob("*.scala"):
        text = source.read_text()
        imports = {line.strip() for line in text.splitlines() if "com.fasterxml.jackson" in line and line.lstrip().startswith("import ")}
        if not imports <= ALLOWED_IMPORTS:
            fail("Jackson import exceeds generator-only boundary")
        code = _rust_code(text)
        if re.search(r"\b(?:createParser|JsonParser|JsonToken|ObjectMapper|NumberInput|looksLikeValidNumber|readTree|readValue|ClassLoader|ProcessBuilder)\b|\b(?:reflect|forName|loadLibrary)\b|java\.lang\.Runtime", code):
            fail("Scala generator-only source boundary changed")
        occurrences = len(re.findall(r"com\.fasterxml\.jackson", code))
        if occurrences != len(imports):
            fail("unreviewed fully qualified Jackson API")
    print("scala_authoring_static_boundary=generator-only build_inputs=pinned")


def classpaths(log):
    lines = log.splitlines()
    runtime = [match[1] for line in lines if (match := re.search(r"Attributed\(([^)]+\.jar)\)", line))]
    instances = [line for line in lines if "Scala instance {" in line]
    if len(instances) != 1:
        fail("missing or ambiguous actual Scala compiler classpath")
    compiler = re.findall(r"/[^ ,{}]+\.jar", instances[0])
    def relative(path):
        marker = "/https/repo.maven.apache.org/maven2/"
        if marker not in path:
            fail("classpath outside the reviewed Maven Central cache")
        return path.split(marker, 1)[1]
    return [relative(p) for p in runtime], [relative(p) for p in compiler]


def check_actual(root, log):
    check_static(root)
    data = load(root)
    runtime, compiler = classpaths(log)
    if runtime != data["runtime_classpath"] or compiler != data["compiler_classpath"]:
        fail("actual runtime/compiler classpath differs from reviewed graph")
    paths = re.findall(r"/[^ ,{}()]+\.jar", log)
    prefixes = {p.split("/https/repo.maven.apache.org/maven2/", 1)[0] for p in paths if "/https/repo.maven.apache.org/maven2/" in p}
    if len(prefixes) != 1:
        fail("ambiguous Maven cache")
    cache = Path(prefixes.pop()) / "https/repo.maven.apache.org/maven2"
    for name, expected in data["files"].items():
        file = cache / name
        if file.is_symlink() or not file.is_file() or sha(file) != expected["sha256"] or file.stat().st_size != expected["bytes"]:
            fail(f"JAR/POM checksum mismatch: {name}")
    report = root / "frontend/scala/target/scala-3.3.8/update/update_cache_3/output"
    update = json.loads(report.read_text())
    observed = {c["configuration"]["name"]: [m["module"] for m in c["modules"]] for c in update["configurations"]}
    if observed != data["resolved_configurations"]:
        fail("resolved Maven configurations changed")
    for configuration in update["configurations"]:
        for module in configuration["modules"]:
            if module["evicted"] or module["missingArtifacts"]:
                fail("evicted or missing Maven dependency")
    print(f"scala_runtime_jars={len(runtime)} compiler_jars={len(compiler)} pinned_jar_pom_files={len(data['files'])}")
