# FND-01 developer bootstrap

This is a build and ownership baseline: one dependency-free Rust crate and one
Scala smoke program. It does not implement the architecture DSL, exchange
schema, device database, fabric RTL or CAD flow. Follow [AGENTS.md](../../AGENTS.md)
and [the audited scope](../implementation/fnd-01-readiness.md).

## Pinned authoring tools

The source of version pins is [versions.json](../../toolchains/versions.json).
The Rust toolchain and Scala build files repeat those values for their native
tools; `./nf check contracts` rejects drift.

| Profile | Pinned tools | Boundary |
| --- | --- | --- |
| Rust bootstrap | Rust/Cargo 1.98.1 with matching rustfmt/clippy components | No Scala/JDK or separately installed LLVM/MLIR/CIRCT SDK/application dependency |
| Scala authoring | Scala 3.3.8 LTS, sbt 1.12.11, Temurin 21.0.12.1+1 | JDK belongs to this profile; output is a smoke message, not an ArchIR package |
| Source formatting | Toolchain rustfmt, scalafmt 3.11.5, sbt-scalafmt 2.5.5 | Format checks do not establish hardware correctness |

Use Python 3.11+ for developer commands. Automated JDK archive extraction also
requires `tarfile.data_filter` (Python 3.12 is used by the Scala CI lane).
Automated JDK setup currently supports Linux x86_64. Other environments are
unqualified until independently exercised; do not infer cross-platform support.

## Commands

Run from the repository root as an ordinary user. The Rust setup command requires
an existing [rustup installation](https://rust-lang.github.io/rustup/installation/index.html)
and installs the exact toolchain into the user's selected rustup home. It never
uses sudo or edits the shell startup files. Python and the ordinary host C linker
are prerequisites; they are not FPGA/MLIR SDKs.

```sh
./nf bootstrap rust
./nf doctor rust
./nf check contracts
./nf check rust
./nf reproduce rust
```

The separate Scala setup downloads the exact JDK archive and sbt launcher into a
user-writable cache, verifies the checked-in SHA-256 values before extraction or
execution, and checks the resulting JDK vendor/runtime. It does not install a
system JDK or use an ambient sbt executable.

```sh
./nf bootstrap scala
./nf doctor scala
./nf check scala
./nf reproduce scala
```

Use `./nf format rust` or `./nf format scala` to apply formatting; add `--check`
to inspect it. `./nf identity` reports the actual Git head/tree and source state.
`NF_EXPECT_SHA` makes a mismatch or dirty source a hard error in CI.

`NF_TOOL_CACHE` selects a writable tool-cache directory; its default is the
ignored repository `.cache/toolchains`. `NF_JAVA_HOME` may select an already
installed JDK with the exact pinned vendor/runtime. `NF_OFFLINE=1` forbids new
JDK/launcher downloads and fails usefully if they are missing. sbt itself still
needs its dependencies in the normal sbt/Coursier caches; this option is not a
claim that a cold Scala build is network-free. Rust checks use locked offline
Cargo resolution after toolchain setup because the bootstrap has no crate
dependencies.

Version/checksum errors remain failures. Remove a corrupt cache entry and obtain
the pinned artifact again; never change an expected digest merely to accept it.
Missing tools print a named diagnostic and this document's path. Setup refuses
root execution; this is how the unprivileged installation contract is exercised.

## Ownership and independent controls

Reusable core imports only reviewed core contracts. Library generators use
frontend/core APIs; devices compose libraries; adapters consume public contracts;
applications orchestrate them. See [architecture](../architecture.md) and
[ADR 0001](../adr/0001-optional-circt-backend.md). No future module directories
are scaffolded by this increment.

[ownership.json](../../tools/ownership.json) lists the actual bootstrap member.
[The boundary checker](../../tools/check_boundaries.py) examines workspace and
target-specific normal/dev/build dependencies, renamed dependencies, build hooks,
source includes/links and symlink escapes. The initial external-dependency
allowlist is empty. Extending the workspace or dependency policy requires the
owning increment's review; a future legitimate core dependency is not prohibited
forever. This conservative static guard is not a general hostile-code sandbox.

[Negative controls](../../tests/bootstrap/test_contracts.py) independently inject
application/device/adapter imports, hidden/renamed dependencies, build scripts,
external includes, native links and source escapes, and require the intended
diagnostic. Other controls cover pin drift, download corruption, missing tools,
source identity and conservative changed-path classification. Passing the smoke
program alone cannot satisfy these controls.

## CI and reproducibility

[The focused workflow](../../.github/workflows/fnd-01-bootstrap.yml) supports
`workflow_dispatch` lanes `contracts`, `rust`, `scala` and `all`. The first three
are the affected qualification set; `all` is reserved for a full invocation when
its work is not already qualified at the same head. Apply the targeted-first
and deduplication policy before dispatch. Registration/access must actually work;
the file's existence is not an executed check.

Automatic push/PR triggers are limited to `dev` and bootstrap implementation
paths. Documentation-only paths do not launch hardware/build jobs; authorized
documentation commits use `[skip ci]`. Explicit dispatch is not suppressed by
that annotation. The classifier treats unknown implementation paths as affecting
all bootstrap lanes. This classifier is a selection aid, not a substitute for
live workflow/job review or the later FND-03 roadmap validator.

The Rust lane builds a separate Rust/Debian image with Python, records its image
identity, checks absent Scala/JDK/SDK tools, and runs toolchain installation and
all builds as the non-root checkout owner. The image setup uses ordinary OS
packages; the qualified Rust build does not invoke Java or an optional SDK. It
records actual Cargo metadata and linked libraries. Ordinary LLVM components
inside the Rust compiler are expressly allowed.

Each language is rebuilt in two clean temporary source directories. Compare
the actual smoke output and lockfile, recording elapsed times and hashes.
Dependency caches may be warm and tool setup is separate; these observations
are not cold-download benchmarks, byte-identical executable claims or production
scale results. Container/runner identities and exact tool versions accompany CI
logs. FND-07/PERF own broader dependency and benchmark qualification.

Artifacts retain actual source identities, executed logs, isolation observations,
negative-control outcomes and repeated smoke output. The aggregate fails if any
selected lane fails, is cancelled or skipped. Unselected dispatch lanes are
explicitly outside that run's scope and receive no test credit. There is no
fabric simulation, synthesis, formal, board or physical qualification here.

## License and proprietary-content policy

This increment does not select or grant a project distribution license. Cargo
and sbt publication are disabled. Tool distributions remain external downloads
under their upstream license/notice files; no third-party implementation source
or binary is vendored. Rust, Scala/sbt/scalafmt and Temurin distributions must
retain their own notices if redistributed; the detailed inventory and review
belong to FND-07 before any distribution claim.

Keep restricted PDKs, vendor IP, license keys and customer designs out of source,
fixtures, CI logs and public artifacts. Concrete technology/device adapters stay
outside reusable core. A public repository or a checksum is not a substitute
for an explicit redistribution review.

This increment does not affect generated Verilog.
