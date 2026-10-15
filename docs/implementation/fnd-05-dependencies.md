# FND-05 dependency inventory and ownership review

This record covers the acquired dependencies for exchange 0.1. It is not an
FND-05 completion or runtime qualification claim. The exact direct pins in the
reviewed readiness were retained; acquisition occurred after implementation GO.
The existing Rust, Scala, sbt, JDK and formatting pins are unchanged.

## Rust graph and integrity

`tools/ownership.json` schema 3 extends the existing path/package/DAG policy.
The local graph has four crates and three internal edges. Only `nf-exchange`
may depend directly on the four reviewed registry packages. `nf-types` and
`nf-arch-ir` retain no registry dependencies. Local library/build/native/unsafe
boundaries and predecessor adversarial controls remain enforced.

Direct declarations are exact: serde 1.0.229 (`std`, `derive`, defaults off),
serde_json 1.0.154 (`std`, defaults off), serde_path_to_error 0.1.20, and sha2
0.10.9 (`std`, `force-soft`, defaults off). All four were present and non-yanked
in the official crates.io sparse index at acquisition on 2026-10-15.

`tools/dependencies/rust-registry.json` freezes the actual 22-package resolved
graph, not a name-only allowlist. Each entry records name, version, source,
registry package ID, checksum, complete declared dependency metadata (including
normal/build/dev/target, optional/default-feature controls and aliases), feature
map, targets, licenses, rust-version, build-script/proc-macro entry hashes, and
complete extracted source-tree identity. Resolve nodes preserve actual activated
features and edge kind/target/alias. Cargo.lock's full identity/checksum/edge set
is checked against that inventory and the local DAG.

Acquired transitive versions are block-buffer 0.10.4, cfg-if 1.0.5, cpufeatures
0.2.17, crypto-common 0.1.7, digest 0.10.7, generic-array 0.14.7, itoa 1.0.18,
libc 0.2.190, memchr 2.8.3, proc-macro2 1.0.107, quote 1.0.47, serde_core
1.0.229, serde_derive 1.0.229, syn 3.0.9, typenum 1.20.1, unicode-ident 1.0.27,
version_check 0.9.5 and zmij 1.0.23, in addition to the four direct packages.

Official registry archive checksums matched the lock. Every extracted file's
bytes were compared with its checksum-verified archive entry, rejecting archive
symlinks and duplicate paths. The canonical source-tree hash is SHA-256 of compact
UTF-8 JSON pairs `[relative_posix_path, file_sha256]`, sorted lexicographically by
relative path; only Cargo's root `.cargo-ok` marker is excluded. The pre-build
metadata gate rechecks archive and extracted-tree hashes. It never regenerates
expected inventory during a check. `cargo metadata --locked --offline` and the
actual source/graph gate passed after acquisition; this is not a whole-workspace
build or conformance claim.

### Hooks, targets, and native boundaries

- generic-array's build script queries rustc through version_check and emits a
  compatibility cfg. version_check invokes rustc `--verbose --version`.
- proc-macro2's build script queries rustc and compiles fixed local feature probes
  into OUT_DIR, then removes those probe outputs. Its declared wrappers and
  compiler cfg behavior were inspected. This is a build-time Rust compiler use.
- quote and zmij query rustc and emit compatibility cfgs. serde and serde_core
  also write fixed versioned private modules under OUT_DIR. serde_json selects
  its arithmetic limb cfg from target architecture/pointer width.
- libc's target-dependent build script is inventoried even though its platform
  edges are inactive on the qualified x86_64 path. Its Rust-version, FreeBSD
  version and Emscripten version probes, and platform/environment cfg branches,
  are retained as reviewed build-time behavior, not runtime requirements.
- serde_derive is the one proc-macro package; its proc-macro2/quote/syn dependencies
  and features are frozen. No registry package declares a native `links` hook.
- sha2's `force-soft` branch selects its software SHA-256/SHA-512 modules before
  the CPU/assembly branches. It does not erase declared cpufeatures/libc target
  edges. `asm`, `asm-aarch64`, `loongarch64_asm`, and sha2-asm are not activated.
- Third-party optional and dev declarations remain recorded, including unused
  test/download dependencies. They are not activated or compiled as dependency
  tests by workspace testing. Changing activation requires a fresh graph review.

The project's `forbid(unsafe_code)` is not a claim that every dependency is
unsafe-free. Reviewed dependencies include internal unsafe code (for example,
sha2's layout conversion and generic-array implementation). This inventory and
hook review do not claim a comprehensive cryptographic/security audit. No
custom JSON tokenizer or cryptographic primitive was substituted.

## Scala authoring graph

`tools/dependencies/scala-authoring.json` freezes actual sbt resolution across
all project configurations, the three-entry writer runtime JAR classpath and
twelve-entry Scala compiler/library JAR classpath, with 31 exact JAR/POM files
including parent POMs. The Maven repository is the existing explicit Maven
Central endpoint. Build.sbt, build.properties, plugins.sbt and repository-file
hashes are checked; existing sbt/bootstrap tooling remains separately pinned by
FND-01. This inventory covers the writer and its compiler instance, not every
unrelated artifact that happens to exist in a shared sbt cache.

The writer runtime contains scala3-library_3 3.3.8, scala-library 2.13.18 and
jackson-core 2.21.5. Jackson has no additional published runtime dependency;
its JAR includes shaded FastDoubleParser code/licenses and Schubfach licensing.
The published POM's Maven build plugins describe upstream artifact production;
sbt consuming the JAR does not execute those plugins. Its JsonFactory service
entry is recorded; the writer constructs JsonFactoryBuilder directly.

Compiler-instance JARs include the existing JLine terminal JNI/native artifacts;
their embedded native-library entries are recorded. They are authoring/compiler
inputs only. None is admitted to the saved Rust runtime root. There is no claim
that the Scala authoring profile is JVM-free or entirely native-code-free.

Jackson JAR SHA-256:
`b64b5874162b503a0e58a8f7758266e8dd9f91bf49e3a59ae0b5f47589a231b7`.
Published POM SHA-256:
`37620f59b78916d8be56301c73384d15d545c0e217431bc6d127a8d880df407d`.
The generator uses integer `writeNumber(Int)` and string `writeString`, never
numeric-string parsing, parser APIs, databind, reflection or code loading.
Static source controls reject those unreviewed APIs; inspection of actual
compiled writer classes also found no parser/databind/NumberInput/reflection/
process-builder references. These are review tripwires, not a hostile-source
security proof.

### Upstream status and limited advisory applicability

The official [2.21.5 release record](https://github.com/FasterXML/jackson/wiki/Jackson-Release-2.21.5)
identifies the July 2026 release. Upstream has since released 2.21.6/2.21.7.
The [official core advisory list](https://github.com/FasterXML/jackson-core/security/advisories)
was checked at acquisition. Three advisories include 2.21.5:

- [GHSA-7hhh-6rmp-j9qf](https://github.com/FasterXML/jackson-core/security/advisories/GHSA-7hhh-6rmp-j9qf):
  unbounded error-token handling in the DataInput parser; fixed in 2.21.7.
- [GHSA-p6pp-m3f8-5c89](https://github.com/FasterXML/jackson-core/security/advisories/GHSA-p6pp-m3f8-5c89):
  quadratic NumberInput numeric-string validation; fixed in 2.21.7.
- [GHSA-649p-m576-vr99](https://github.com/FasterXML/jackson-core/security/advisories/GHSA-649p-m576-vr99):
  late char-backed parser name-length checking; fixed in 2.21.6.

The parent explicitly retained the reviewed 2.21.5 pin for this generator-only,
bounded fixture writer. The affected parser/numeric-string paths are unused;
this is a scoped reachability decision, not a statement that 2.21.5 has no
vulnerabilities or is suitable for a general JSON reader. Any broadened use must
revisit the pin and advisories. FND-07 must re-review this decision on any new
parser, coercion, numeric-string, reflection or service-loading API use; untrusted
JSON consumption; source language, classpath or pin change; or relevant new
advisory. The regex guard is a tripwire, not a complete API allowlist or a
reachability proof. Saved-package consumption uses Rust and contains no
Jackson/JVM bytes.

## Reproduction and remaining evidence

Run `./nf check contracts`, `./nf check rust`, `./nf check scala`, then
`./nf check exchange` with acquired caches and `NF_OFFLINE=1`. The Rust profile
checks cached source identities before build scripts/proc macros run. The Scala
profile executes WriterChecks explicitly; plain sbt `test` is not credited for
those executable checks. Exchange runs produce actual Scala saved artifacts,
verify its Maven graph, and supply the real prebuilt reader plus actual emitted
artifacts to independent Python conformance tests.

Saved-runtime execution is a separate gate. The initial filter/probe control
is not acceptance. Host ptrace tracing was unavailable locally and an executor
setup failure also prevented an escalated tracer invocation. The permitted
loader/procfs alternative subsequently passed actual six-case reader execution
and independent exact-source/result review; see the
[saved-runtime report](fnd-05-runtime.md) for identities, verification results and
explicit observation limits. No remote CI or closure is implied by this report.

Final local qualification passed all four `nf check` profiles: contracts
(74 bootstrap, 43 Foundation and 92 roadmap tests), Rust (strict clippy, workspace
tests and doctests), Scala (17 explicit writer check groups and exact graph),
and exchange (fresh actual Scala output plus 83 conformance groups). Four runtime
harness/control tests passed separately. These are dirty-development results,
source-bound by the [development vector](fnd-05-development-source.sha256) and
[independent review vector](fnd-05-review-source.sha256). Raw logs were preserved
locally outside the candidate and are not published repository evidence. Exact
clean-head qualification and integration remain pending.

This increment does not affect generated Verilog.
