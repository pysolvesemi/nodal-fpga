"""Fail-closed dependency guard for the actual FND-01 core, not future stubs."""
from pathlib import Path
import json
import re
import tomllib


class BoundaryError(ValueError):
    pass


def reject(code: str, detail: str) -> None:
    raise BoundaryError(f"{code}: {detail}")


def check(root: Path) -> None:
    root = root.resolve()
    policy = json.loads((root / "tools/ownership.json").read_text())
    workspace = tomllib.loads((root / "Cargo.toml").read_text())["workspace"]
    members = workspace["members"]
    if members != policy["core_members"] or len(set(members)) != len(members):
        reject("NF-OWN-MEMBERS", "workspace membership requires an explicit ownership review")
    if workspace.get("exclude") or workspace.get("dependencies"):
        reject("NF-OWN-WORKSPACE", "unreviewed workspace exclusions/dependency inheritance")
    observed = sorted(str(p.parent.relative_to(root)) for p in (root / "core/rust").rglob("Cargo.toml"))
    if observed != sorted(members):
        reject("NF-OWN-UNREGISTERED", "core manifest outside reviewed membership")
    for member in members:
        directory = (root / member).resolve()
        if not directory.is_relative_to(root / "core/rust"):
            reject("NF-OWN-PATH", member)
        manifest = tomllib.loads((directory / "Cargo.toml").read_text())
        package = manifest["package"]
        if package.get("links") or package.get("build") or (directory / "build.rs").exists():
            reject("NF-OWN-NATIVE", member + " uses an unreviewed native/build-script boundary")
        if package.get("publish") != {"workspace": True} or workspace["package"].get("publish") is not False:
            reject("NF-OWN-PUBLISH", "bootstrap packages must not be publishable")
        tables = [manifest, *manifest.get("target", {}).values()]
        for table in tables:
            for kind in ["dependencies", "dev-dependencies", "build-dependencies"]:
                for name, dep in table.get(kind, {}).items():
                    if isinstance(dep, dict) and dep.get("path"):
                        destination = (directory / dep["path"]).resolve()
                        if not destination.is_relative_to(root / "core/rust"):
                            reject("NF-OWN-DEPENDENCY", f"{member} -> {destination}")
                    # FND-01 has no dependencies, including renamed and target-specific entries.
                    if name not in policy["core_registry_allowlist"]:
                        reject("NF-OWN-DEPENDENCY", f"{member}: unreviewed {kind} {name}")
        source = directory / "src/lib.rs"
        if "#![forbid(unsafe_code)]" not in source.read_text():
            reject("NF-OWN-UNSAFE", "core must retain forbid(unsafe_code)")
        for path in sorted(directory.rglob("*.rs")):
            if path.is_symlink() or not path.resolve().is_relative_to(directory):
                reject("NF-OWN-SOURCE", "source escapes the core crate")
            text = path.read_text()
            # Source-level external include/link hooks require a separate ownership review.
            if re.search(r"\binclude(?:_str|_bytes)?\s*!|#\s*\[\s*(?:path\s*=|link\s*\()", text):
                reject("NF-OWN-INCLUDE", str(path.relative_to(root)))
    print(f"ownership_members={len(members)} core_external_dependencies=0")


if __name__ == "__main__":
    check(Path(__file__).resolve().parents[1])
