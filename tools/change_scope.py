"""Conservative bootstrap lane selection; docs-only changes receive contracts checks."""
from pathlib import PurePosixPath


def lanes(paths: list[str]) -> list[str]:
    if not paths:
        return []
    for path in paths:
        value = PurePosixPath(path)
        if value.is_absolute() or ".." in value.parts or not path:
            raise ValueError("NF-SCOPE-PATH: require repository-relative paths")
    if all(path.endswith(".md") and (path.startswith("docs/") or path in {"AGENTS.md", "README.md"}) for path in paths):
        return ["contracts"]
    # Tooling/policy/workflow changes can affect both languages; unknown files fail conservative.
    return ["contracts", "rust", "scala"]
