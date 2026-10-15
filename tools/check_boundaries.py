"""Fail-closed ownership checks for the reviewed, dependency-free-of-SDK core DAG.

Static checks run without Cargo in the contracts lane. The Rust lane additionally
checks Cargo's actual package identities, manifest paths and resolved graph.
Adding a crate or edge requires an explicit change to tools/ownership.json.
"""
from pathlib import Path, PurePosixPath
import json
import os
import re
import tomllib


class BoundaryError(ValueError):
    pass


def reject(code: str, detail: str) -> None:
    raise BoundaryError(f"{code}: {detail}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            reject("NF-OWN-POLICY", f"duplicate policy key {key}")
        result[key] = value
    return result


def _relative(value: object) -> bool:
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and not PurePosixPath(value).is_absolute()
            and str(PurePosixPath(value)) == value)


def _plain_path(path: Path, root: Path, code: str) -> None:
    if not path.is_relative_to(root):
        reject(code, "path outside repository")
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            reject(code, f"symlink at {current.relative_to(root)}")
    if not path.exists() or path.resolve() != path:
        reject(code, f"missing or noncanonical path {path}")


def _acyclic(packages: dict, edges: set) -> None:
    remaining = set(packages)
    while remaining:
        leaves = {name for name in remaining
                  if not any(edge[0] == name and edge[1] in remaining for edge in edges)}
        if not leaves:
            reject("NF-OWN-CYCLE", "reviewed core dependencies must form a DAG")
        remaining -= leaves


def _policy(root: Path) -> tuple[dict, set]:
    path = root / "tools/ownership.json"
    _plain_path(path, root, "NF-OWN-POLICY")
    try:
        policy = json.loads(path.read_text(), object_pairs_hook=_unique_object)
        if (set(policy) != ({"schema", "core_packages", "core_dependencies", "scope"}
                                   | ({"registry_dependencies"} if policy.get("schema") == 3 else set()))
                or policy["schema"] not in {2, 3} or not isinstance(policy["scope"], str)
                or not isinstance(policy["core_packages"], list)
                or not isinstance(policy["core_dependencies"], list)):
            reject("NF-OWN-POLICY", "expected ownership registry schema 2 or 3")
        packages = {}
        paths = set()
        for record in policy["core_packages"]:
            if (set(record) != {"name", "path", "version"}
                    or not isinstance(record["name"], str)
                    or not re.fullmatch(r"[a-z][a-z0-9-]*", record["name"])
                    or not _relative(record["path"])
                    or ".." in PurePosixPath(record["path"]).parts
                    or not record["path"].startswith("core/rust/")
                    or not isinstance(record["version"], str)
                    or record["name"] in packages or record["path"] in paths):
                reject("NF-OWN-POLICY", "duplicate or invalid package registration")
            packages[record["name"]] = record
            paths.add(record["path"])
        if not packages:
            reject("NF-OWN-POLICY", "empty package registry")
        edges = set()
        for record in policy["core_dependencies"]:
            if (set(record) != {"from", "to", "kind", "target", "alias", "path"}
                    or record["from"] not in packages or record["to"] not in packages
                    or record["kind"] not in {"normal", "dev", "build"}
                    or (record["target"] is not None and not isinstance(record["target"], str))
                    or not isinstance(record["alias"], str) or not record["alias"]
                    or not _relative(record["path"])):
                reject("NF-OWN-POLICY", "invalid dependency registration")
            edge = tuple(record[key] for key in ["from", "to", "kind", "target", "alias", "path"])
            source = root / packages[record["from"]]["path"]
            target = root / packages[record["to"]]["path"]
            if Path(os.path.abspath(source / record["path"])) != target or edge in edges:
                reject("NF-OWN-POLICY", "duplicate or mismatched dependency path")
            edges.add(edge)
        _acyclic(packages, edges)
        if policy["schema"] == 3:
            registry = policy["registry_dependencies"]
            seen = set()
            if not isinstance(registry, list):
                reject("NF-OWN-POLICY", "registry dependencies must be a list")
            for edge in registry:
                if (set(edge) != {"from", "to", "kind", "target", "alias", "declaration"}
                        or edge["from"] != "nf-exchange" or edge["from"] not in packages
                        or edge["to"] not in {"serde", "serde_json", "serde_path_to_error", "sha2"}
                        or edge["kind"] != "normal" or edge["target"] is not None
                        or edge["alias"] != edge["to"] or edge["to"] in seen
                        or not isinstance(edge["declaration"], dict)
                        or not set(edge["declaration"]) <= {"version", "default-features", "features"}
                        or not re.fullmatch(r"=\d+\.\d+\.\d+", edge["declaration"].get("version", ""))):
                    reject("NF-OWN-POLICY", "invalid registry dependency registration")
                seen.add(edge["to"])
        return packages, edges
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        reject("NF-OWN-POLICY", f"malformed ownership registry: {exc}")


def _rust_code(text: str) -> str:
    """Mask comments and literals so examples cannot impersonate safety attributes.

This is a lexical boundary check, not a Rust parser. Cargo/rustc independently
validate syntax and enforce the inherited forbid(unsafe_code) lint for targets.
"""
    out = list(text)
    raw_string = re.compile(r'(?:br|cr|r)(#*)"')
    character = re.compile(r"'(?:\\(?:u\{[0-9a-fA-F_]+\}|x[0-9a-fA-F]{2}|.)|[^'\\\n])'")
    index = 0
    while index < len(text):
        end = index
        if text.startswith("//", index):
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
        elif text.startswith("/*", index):
            end, depth = index + 2, 1
            while end < len(text) and depth:
                if text.startswith("/*", end):
                    depth += 1
                    end += 2
                elif text.startswith("*/", end):
                    depth -= 1
                    end += 2
                else:
                    end += 1
        else:
            raw = raw_string.match(text, index)
            if raw:
                close = '"' + raw[1]
                end = text.find(close, index + len(raw[0]))
                end = len(text) if end < 0 else end + len(close)
            elif text[index] == '"':
                end = index + 1
                while end < len(text):
                    if text[end] == "\\":
                        end += 2
                    elif text[end] == '"':
                        end += 1
                        break
                    else:
                        end += 1
            elif text[index] == "'":
                char = character.match(text, index)
                if char:
                    end = index + len(char[0])
        if end > index:
            for pos in range(index, min(end, len(text))):
                if out[pos] != "\n":
                    out[pos] = " "
            index = end
        else:
            index += 1
    return "".join(out)


def _review(root: Path) -> tuple[dict, set]:
    packages, expected = _policy(root)
    _plain_path(root / "Cargo.toml", root, "NF-OWN-PATH")
    for config in [root / ".cargo/config", root / ".cargo/config.toml"]:
        if config.exists() or config.is_symlink():
            reject("NF-OWN-NATIVE", "repository Cargo configuration requires ownership review")
    manifest = tomllib.loads((root / "Cargo.toml").read_text())
    workspace = manifest.get("workspace", {})
    members = workspace.get("members")
    registered = [package["path"] for package in packages.values()]
    if not isinstance(members, list) or members != registered:
        reject("NF-OWN-MEMBERS", "workspace membership requires an explicit ownership review")
    if (any(key in manifest for key in ["package", "patch", "replace"])
            or any(key in workspace for key in ["exclude", "dependencies", "default-members"])):
        reject("NF-OWN-WORKSPACE", "unreviewed root package, overrides or workspace inheritance")
    if workspace.get("package", {}).get("publish") is not False:
        reject("NF-OWN-PUBLISH", "core packages must not be publishable")
    if workspace.get("lints", {}).get("rust", {}).get("unsafe_code") != "forbid":
        reject("NF-OWN-UNSAFE", "workspace must forbid unsafe_code")
    _plain_path(root / "core/rust", root, "NF-OWN-PATH")
    observed = []
    for directory, dirs, files in os.walk(root / "core/rust", followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                code = "NF-OWN-PATH" if name == "Cargo.toml" or name in dirs else "NF-OWN-SOURCE"
                reject(code, f"core symlink {path.relative_to(root)}")
        if "Cargo.toml" in files:
            observed.append(str(Path(directory).relative_to(root)))
    if sorted(observed) != sorted(registered):
        reject("NF-OWN-UNREGISTERED", "core manifests differ from reviewed package membership")
    policy = json.loads((root / "tools/ownership.json").read_text())
    direct = policy.get("registry_dependencies", [])
    registry_actual = []
    actual = set()
    for name, registration in packages.items():
        member = registration["path"]
        directory = root / member
        _plain_path(directory / "Cargo.toml", root, "NF-OWN-PATH")
        for config in [directory / ".cargo/config", directory / ".cargo/config.toml"]:
            if config.exists() or config.is_symlink():
                reject("NF-OWN-NATIVE", f"{member} has unreviewed Cargo configuration")
        manifest = tomllib.loads((directory / "Cargo.toml").read_text())
        package = manifest.get("package", {})
        if (package.get("name") != name or package.get("version") != {"workspace": True}
                or workspace.get("package", {}).get("version") != registration["version"]):
            reject("NF-OWN-IDENTITY", f"package identity mismatch at {member}")
        if any(key in manifest for key in ["workspace", "patch", "replace"]) or "workspace" in package:
            reject("NF-OWN-WORKSPACE", f"{member} redirects the workspace")
        if "links" in package or "build" in package or (directory / "build.rs").exists():
            reject("NF-OWN-NATIVE", member + " uses an unreviewed native/build-script boundary")
        if package.get("publish") != {"workspace": True}:
            reject("NF-OWN-PUBLISH", "core packages must inherit publish=false")
        if manifest.get("lints") != {"workspace": True}:
            reject("NF-OWN-UNSAFE", f"{member} must inherit workspace lints")
        if manifest.get("features"):
            reject("NF-OWN-DEPENDENCY", "unreviewed feature-controlled core graph")
        tables = [(None, manifest), *manifest.get("target", {}).items()]
        for target, table in tables:
            for kind, table_name in [("normal", "dependencies"), ("dev", "dev-dependencies"), ("build", "build-dependencies")]:
                if table_name.replace("-", "_") != table_name and table_name.replace("-", "_") in table:
                    reject("NF-OWN-DEPENDENCY", "unreviewed legacy dependency section")
                for alias, dep in table.get(table_name, {}).items():
                    registry_edge = {"from": name, "to": alias, "kind": kind, "target": target,
                                     "alias": alias, "declaration": {"version": dep} if isinstance(dep, str) else dep}
                    if registry_edge in direct:
                        if registry_edge in registry_actual:
                            reject("NF-OWN-DEPENDENCY", "duplicate direct registry edge")
                        registry_actual.append(registry_edge)
                        continue
                    if not isinstance(dep, dict) or set(dep) != {"path"} or not _relative(dep["path"]):
                        reject("NF-OWN-DEPENDENCY", f"{member}: unreviewed {table_name} {alias}")
                    destination = (directory / dep["path"]).resolve()
                    matches = [entry["name"] for entry in packages.values()
                               if root / entry["path"] == destination]
                    if len(matches) != 1:
                        reject("NF-OWN-DEPENDENCY", f"{member}: dependency outside registered packages")
                    edge = (name, matches[0], kind, target, alias, dep["path"])
                    if edge not in expected or edge in actual:
                        reject("NF-OWN-DEPENDENCY", f"unreviewed dependency identity {edge}")
                    actual.add(edge)
        library = manifest.get("lib", {})
        if (library.get("proc-macro") or library.get("proc_macro")
                or "crate_type" in library or library.get("crate-type", ["lib"]) != ["lib"]
                or library.get("path", "src/lib.rs") != "src/lib.rs"):
            reject("NF-OWN-NATIVE", f"{member} has an unreviewed library target")
        for kind in ["bin", "example", "test", "bench"]:
            for target in manifest.get(kind, []):
                if "path" in target:
                    path = target["path"]
                    if not _relative(path) or ".." in PurePosixPath(path).parts or not path.endswith(".rs"):
                        reject("NF-OWN-SOURCE", f"{member}: target path escapes crate")
                    _plain_path(directory / path, directory, "NF-OWN-SOURCE")
                if "crate_type" in target or target.get("crate-type", ["bin"]) != ["bin"]:
                    reject("NF-OWN-NATIVE", f"{member}: unreviewed target crate type")
        source = directory / "src/lib.rs"
        _plain_path(source, directory, "NF-OWN-SOURCE")
        code = _rust_code(source.read_text())
        if not re.search(r"#!\s*\[\s*forbid\s*\(\s*unsafe_code\s*\)\s*\]", code):
            reject("NF-OWN-UNSAFE", f"{member} must retain forbid(unsafe_code)")
        for path in sorted(directory.rglob("*.rs")):
            code = _rust_code(path.read_text())
            attributes = re.findall(r"#\s*!?\s*\[[^\]]*\]", code)
            # Reserve these builtin macro names, including imports/renames that
            # could otherwise hide an external include behind a different name.
            if (re.search(r"\binclude(?:_str|_bytes)?\b", code)
                    or any(re.search(r"\b(?:path\s*=|link\s*\(|link_name\s*=|link_section\s*=|export_name\s*=|no_mangle\b)", attr)
                           for attr in attributes)):
                reject("NF-OWN-INCLUDE", str(path.relative_to(root)))
    if actual != expected:
        reject("NF-OWN-DEPENDENCY", "required reviewed dependency edge is missing")
    _acyclic(packages, actual)
    if registry_actual != direct:
        reject("NF-OWN-DEPENDENCY", "required registry dependency declaration is missing or reordered")
    if policy["schema"] == 3:
        from dependency_inventory import check_lock
        check_lock(root, packages, actual, direct)
    return packages, actual


def _checked_review(root: Path) -> tuple[dict, set]:
    try:
        return _review(root)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        if isinstance(exc, BoundaryError):
            raise
        reject("NF-OWN-MANIFEST", f"unreadable or malformed core manifest: {exc}")


def check(root: Path) -> None:
    packages, edges = _checked_review(root.resolve())
    policy = json.loads((root / "tools/ownership.json").read_text())
    print(f"ownership_members={len(packages)} core_internal_dependencies={len(edges)} core_external_dependencies={len(policy.get('registry_dependencies', []))}")


def check_metadata(root: Path, data: dict) -> None:
    """Check actual Cargo metadata, including resolve nodes, against the same DAG."""
    root = root.resolve()
    packages, edges = _checked_review(root)

    def require(condition: bool, detail: str) -> None:
        if not condition:
            reject("NF-CORE-GRAPH", detail)

    try:
        require(data["version"] == 1 and data["workspace_root"] == str(root), "metadata workspace identity")
        policy = json.loads((root / "tools/ownership.json").read_text())
        if policy["schema"] == 3:
            from dependency_inventory import check_metadata as registry_metadata, load
            data = registry_metadata(root, data, packages, policy["registry_dependencies"], load(root))
        items = data["packages"]
        require(len(items) == len(packages), "unreviewed or missing resolved package")
        ids = {}
        for item in items:
            name = item["name"]
            require(name in packages and name not in ids, "unknown or duplicate package name")
            entry = packages[name]
            require(item["version"] == entry["version"] and item["source"] is None,
                    "package version/source mismatch")
            require(item["manifest_path"] == str(root / entry["path"] / "Cargo.toml"), "noncanonical manifest identity")
            require(isinstance(item["id"], str) and item["id"] not in ids.values(), "duplicate package ID")
            ids[name] = item["id"]
            require(item["publish"] == [] and item["links"] is None, "publishing or native link metadata")
            require(item["features"] == {}, "unreviewed package features")
            required = {edge for edge in edges if edge[0] == name}
            observed = set()
            for dep in item["dependencies"]:
                candidates = [edge for edge in required if edge[1] == dep["name"]]
                require(len(candidates) == 1, "unreviewed manifest dependency")
                edge = candidates[0]
                require(dep["source"] is None and dep["registry"] is None and dep["req"] == "*",
                        "registry/version masquerading as reviewed core dependency")
                require(dep["path"] == str(root / packages[edge[1]]["path"]), "dependency canonical path mismatch")
                require(dep["kind"] == (None if edge[2] == "normal" else edge[2])
                        and dep["target"] == edge[3] and dep["rename"] is None
                        and edge[4] == dep["name"], "dependency kind, target or alias mismatch")
                require(dep["optional"] is False and dep["uses_default_features"] is True
                        and dep["features"] == [], "unreviewed dependency activation")
                require(edge not in observed, "duplicate manifest dependency")
                observed.add(edge)
            require(observed == required, "missing manifest dependency")
            library_count = 0
            for target in item["targets"]:
                kind = target["kind"]
                require(kind in [["lib"], ["bin"], ["example"], ["test"], ["bench"]], "unreviewed native/build target")
                require(target["crate_types"] == (["lib"] if kind == ["lib"] else ["bin"]), "unreviewed crate type")
                path = Path(target["src_path"])
                directory = root / entry["path"]
                require(path.is_relative_to(directory) and path.resolve() == path and path.is_file() and path.suffix == ".rs", "target source path mismatch")
                if kind == ["lib"]:
                    library_count += 1
                    require(path == directory / "src/lib.rs", "library source identity")
            require(library_count == 1, "missing or duplicate library target")
        required_ids = set(ids.values())
        for key in ["workspace_members", "workspace_default_members"]:
            require(len(data[key]) == len(required_ids) and set(data[key]) == required_ids, "workspace package membership mismatch")
        graph = data["resolve"]
        require(graph is not None and graph["root"] is None, "missing or non-workspace resolution")
        nodes = graph["nodes"]
        require(len(nodes) == len(required_ids) and {node["id"] for node in nodes} == required_ids,
                "missing, duplicate or external resolve node")
        for node in nodes:
            source = next(name for name, identifier in ids.items() if identifier == node["id"])
            required = {edge for edge in edges if edge[0] == source}
            target_ids = {ids[edge[1]] for edge in required}
            require(len(node["dependencies"]) == len(target_ids) and set(node["dependencies"]) == target_ids,
                    "resolved dependency IDs mismatch")
            require(node["features"] == [], "unreviewed resolved features")
            observed = set()
            for dep in node["deps"]:
                for kind in dep["dep_kinds"]:
                    record = (dep["pkg"], dep["name"], kind["kind"], kind["target"])
                    require(record not in observed, "duplicate resolved dependency identity")
                    observed.add(record)
            expected = {(ids[edge[1]], edge[4].replace("-", "_"), None if edge[2] == "normal" else edge[2], edge[3])
                        for edge in required}
            require(observed == expected and len(node["deps"]) == len(target_ids), "resolved edge kind, target or alias mismatch")
    except (KeyError, TypeError, ValueError, StopIteration) as exc:
        if isinstance(exc, BoundaryError):
            raise
        reject("NF-CORE-GRAPH", f"malformed Cargo metadata: {exc}")
    print(f"resolved_core_packages={len(packages)} resolved_core_edges={len(edges)} local_subgraph_only=true")


if __name__ == "__main__":
    check(Path(__file__).resolve().parents[1])
