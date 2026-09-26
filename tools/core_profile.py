"""Assert the separate Rust qualification container has no frontend/optional SDK tools."""
import os
from pathlib import Path
import shutil
import sys

from nf import BootstrapError


def main() -> int:
    if os.geteuid() == 0:
        raise BootstrapError("NF-PROFILE-ROOT: canonical toolchain setup must be unprivileged")
    names = ["java", "javac", "scala", "scalac", "sbt", "mill", "mlir-opt", "circt-opt", "llvm-config"]
    found = {name: shutil.which(name) for name in names if shutil.which(name)}
    if found:
        raise BootstrapError(f"NF-PROFILE-TOOLS: isolation image contains {found}")
    if Path("/usr/lib/jvm").exists() and list(Path("/usr/lib/jvm").iterdir()):
        raise BootstrapError("NF-PROFILE-JDK: unexpected installed JDK")
    print(f"unprivileged_uid={os.geteuid()} absent_frontend_and_sdk_tools={','.join(names)}")
    print("Ordinary Rust compiler internal LLVM components remain allowed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BootstrapError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
