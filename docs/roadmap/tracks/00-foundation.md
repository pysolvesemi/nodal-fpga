# Foundation track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Purpose: establish executable contracts, minimal test infrastructure and a small trusted development baseline before dependent tracks start. This track has no dependency on any non-Foundation increment. All other tracks inherit the completion gate `FND-08`.

Modules: initial Rust workspace under `core/rust/`, a minimal Scala build under `frontend/scala/`, `schemas/`, `verify/fixtures/`, `docs/adr/` and development tooling. Do not scaffold every future crate.

- [ ] FND-01 — Bootstrap the repository and ownership boundaries
  Depends on: none.
  - [ ] FND-01.a Create the minimal Rust workspace, pinned Rust toolchain and formatter/linter/test entrypoints; prove an unprivileged installation path.
  - [ ] FND-01.b Select and pin one Scala build tool/JDK/Scala combination; add a tiny frontend smoke build without requiring MLIR.
  - [ ] FND-01.c Document core/library/device/adapter/application dependency directions and license/proprietary-IP policy; add dependency-boundary checks, including no LLVM/MLIR/CIRCT dependency in reusable core or the default Rust compiler/emitter.
  - [ ] FND-01.d Test clean checkout builds and docs-only path handling; distinguish genuinely skipped hardware jobs from passed checks.
  - [ ] FND-01.e Record reproducible commands and final-head bootstrap evidence; confirm no application or concrete device is imported by core.

- [ ] FND-02 — Freeze the initial architecture and project contracts
  Depends on: FND-01.
  - [ ] FND-02.a Write ADRs for Scala-to-Rust exchange, ArchIR versus DeviceDB versus customer DesignDB, and external-CAD-first ownership; apply [ADR 0001](../../adr/0001-optional-circt-backend.md) without treating its optional backend as implemented.
  - [ ] FND-02.b Specify primitive/mode semantics, hierarchical templates, shared routing/configuration resources and the explicit unsupported-feature policy.
  - [ ] FND-02.c Specify overlapping clock/power/configuration domains, technology bindings and device-package identity without implementing advanced devices.
  - [ ] FND-02.d Define the nf-tiny profile and hand-calculated boundary fixtures, including legal and illegal configuration examples.
  - [ ] FND-02.e Review contracts against all later track boundaries; record accepted ADRs and unresolved nonblocking choices without claiming implementation.

- [ ] FND-03 — Enforce resumable nested progress and evidence
  Depends on: FND-02.
  - [ ] FND-03.a Implement a roadmap parser that ignores fenced examples and checks unique increment/leaf IDs and consistent nesting.
  - [ ] FND-03.b Validate dependency references, cycles, the global FND-08 blocker, and the rule that a completed parent has no open descendant.
  - [ ] FND-03.c Add completion-report templates for source head, tool/device hashes, commands, results, limitations and actual generated examples.
  - [ ] FND-03.d Test partial completion, reopened regressions, missing evidence, stale heads, invalid checked parents and a dependency-cycle fixture.
  - [ ] FND-03.e Run the validator on the repository and its negative fixtures; retain evidence that partial child completion is accepted correctly.

- [ ] FND-04 — Implement foundational types and semantic validation
  Depends on: FND-03.
  - [ ] FND-04.a Implement typed IDs, integer/unit bounds, structured diagnostics and source/provenance references in `core/rust/types`.
  - [ ] FND-04.b Define schema-level identities separately from package-local dense IDs; use checked conversions and extensible partition addressing.
  - [ ] FND-04.c Add an initial `arch-ir` model with resource types, interfaces, references, legal modes and configuration-feature declarations.
  - [ ] FND-04.d Property-test invalid references, overflow, illegal modes, undeclared shared-bit conflicts and deterministic diagnostics on tiny fixtures.
  - [ ] FND-04.e Publish the tested core contracts and final-head evidence; no unchecked pointer/file-layout assumptions may enter public APIs.

- [ ] FND-05 — Establish cross-language serialization and compatibility
  Depends on: FND-04.
  - [ ] FND-05.a Define initial versioned ArchIR, mapped-design and package-manifest envelopes with units, feature flags and explicit identity fields.
  - [ ] FND-05.b Implement a minimal Scala fixture writer and Rust reader plus canonical text dumps; retain hierarchy instead of fully expanding arrays.
  - [ ] FND-05.c Specify canonical hashing, unknown-version behavior, bounded reads, error paths and migration rules; do not serialize Rust memory layouts.
  - [ ] FND-05.d Test round trips, truncated/malformed inputs, unsupported required features, field ordering and cross-language semantic equality.
  - [ ] FND-05.e Record the conformance corpus and compatibility matrix; demonstrate Rust tools can consume saved packages with no JVM or LLVM/MLIR/CIRCT present.

- [ ] FND-06 — Bootstrap independent verification before generator development
  Depends on: FND-05.
  - [ ] FND-06.a Write independent truth-table, mux-selection and configuration-vector specifications for the tiny fixture; do not derive expected values from production emitters.
  - [ ] FND-06.b Wire minimal Rust property testing, RTL simulation and formal-tool smoke tests with pinned tool identities.
  - [ ] FND-06.c Define reset, initial-state, X/Z, legal-configuration and clock assumptions explicitly for the first profile.
  - [ ] FND-06.d Inject a wrong mux index, swapped LUT bit and bad config address and demonstrate the bootstrap tests detect each defect.
  - [ ] FND-06.e Archive executable fixtures, proof status and assumptions; distinguish bounded checks from unbounded proofs and coverage witnesses.

- [ ] FND-07 — Establish dependency, security and benchmark policy
  Depends on: FND-06.
  - [ ] FND-07.a Pin external tool revisions, build options and artifact checksums; record licenses and redistribution boundaries without vendoring restricted IP.
  - [ ] FND-07.b Define supported execution environments, resource limits, sandboxed untrusted inputs and nonsecret configuration handling.
  - [ ] FND-07.c Define benchmark metrics, runner identity, workload hashes, baseline update policy and the future small/medium/large synthetic profiles.
  - [ ] FND-07.d Test lockfile drift detection, missing-tool diagnostics, deterministic fixture hashes and oversized input rejection.
  - [ ] FND-07.e Record verified baseline commands and review exact adapter assumptions; no claim of full backend integration is made here.

- [ ] FND-08 — Release the Foundation gate
  Depends on: FND-07.
  - [ ] FND-08.a Audit completion evidence for FND-01 through FND-07 and confirm Foundation has no dependency on blocked tracks.
  - [ ] FND-08.b Run clean Rust/Scala builds, schema conformance, negative fixtures, roadmap validation and independent test smoke suites.
  - [ ] FND-08.c Confirm saved ArchIR loads without Scala/JVM/LLVM/MLIR/CIRCT and reusable core compiles without device libraries or external CAD tools; audit default runtime dependencies separately from the Rust build toolchain.
  - [ ] FND-08.d Freeze the initial contract baseline and explicitly list supported and rejected capabilities plus benchmark measurement procedures.
  - [ ] FND-08.e Record final-head evidence and open the downstream-track gate only after every required Foundation leaf is complete.

Main risk: replacing a tested foundation with a large paper-only abstraction framework. Exit requires executable minimal contracts, not a full fabric. Do not build native synthesis/P&R, analog IP, GUI or multi-die algorithms in Foundation.
