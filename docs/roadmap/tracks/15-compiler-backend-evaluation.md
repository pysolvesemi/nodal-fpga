# Optional compiler-backend evaluation track

[Roadmap index](../README.md) · [Progress rules](../progress.md) · [ADR 0001](../../adr/0001-optional-circt-backend.md)

Global blocker: FND-08. This is an optional evaluation/adoption track, not a requirement to add MLIR/CIRCT. The default remains Scala construction, language-neutral ArchIR and Rust compilation/emission. Existing M0–M6 milestones acquire no dependency on this track.

Potential modules: `adapters/circt/`, `verify/differential/circt/`, `bench/compiler-backends/` and the public fabric-backend boundary. Create them only for an active experiment. Core, DeviceDB, configuration tooling and default libraries must not import LLVM/MLIR/CIRCT. No changes to `nodal-hdl` are implied by this roadmap entry.

Start the CIR-01 review after the minimal emitter exists and before proposing a general HDL parsing/lowering/optimization framework inside `nodal-fpga`. The review may conclude that no experiment is justified. Do not wait for CIR-02/CIR-03 to ship the focused baseline. Assessment completion is not backend implementation or adoption.

- [ ] CIR-01 — Review need, alternatives and a bounded backend contract
  Depends on: FND-08, RTL-01.
  - [ ] CIR-01.a Identify a concrete emitter-maintenance, transformation or verification need; compare the focused Rust emitter, verified module generation through existing `nodal-hdl`, and an external CIRCT adapter.
  - [ ] CIR-01.b Specify the minimal hierarchical hardware-emission/verification contract, capability negotiation, diagnostics and provenance; keep ArchIR, DeviceDB and mapped-customer-design contracts independent of MLIR objects.
  - [ ] CIR-01.c Select a bounded fixture corpus and pin candidate tools; set correctness, memory/runtime, output-quality and maintenance acceptance criteria before benchmarking, using FND-07 measurement policy.
  - [ ] CIR-01.d Review no-LLVM/no-JVM default operation, explicit opt-in, process isolation, missing-tool behavior and configuration preservation; record checks needed for each alternative without claiming they have run.
  - [ ] CIR-01.e Record an evidence-backed proceed-with-experiment, retain-default or defer decision, scope and final-head review report; close only the assessment and leave unperformed prototype/adoption items open.

- [ ] CIR-02 — Prototype and compare without replacing the default
  Depends on: CIR-01, DSL-04, RTL-04, VER-03.
  - [ ] CIR-02.a After a proceed-with-experiment decision, implement the isolated adapter for a declared subset with pinned executable inputs/outputs; retain the baseline and independent reference model, and reject unsupported constructs explicitly.
  - [ ] CIR-02.b Compare primitive/tile behavior across symbolic legal configurations and configuration-loading/reset assumptions; verify widths, signedness, sequential priority, hierarchy/provenance and configuration correspondence rather than only one fixed bitstream.
  - [ ] CIR-02.c Run runtime-loaded boundary/odd-sized fabrics and mutation tests, including swapped config fields, lost programmable state and missing backend; document formal bounds and unsupported/X/Z cases without counting them as passes.
  - [ ] CIR-02.d Measure cold/warm time, peak memory, artifact size, hierarchy expansion and build/maintenance burden on identical pinned inputs; report any downstream area/timing only under matched physical-flow conditions.
  - [ ] CIR-02.e Archive actual Scala input, both generated RTL outputs, hashes, commands, correctness/benchmark results and limitations; record adopt, retain-default or defer against predeclared criteria, without claiming production qualification.

- [ ] CIR-03 — Qualify an adopted adapter as an opt-in backend
  Depends on: CIR-02, RTL-05, VER-07.
  - [ ] CIR-03.a Require the recorded CIR-02 adopt decision; define the supported profile/version matrix and separately packaged adapter/toolchain, with no implicit default or core dependency changes.
  - [ ] CIR-03.b Run default build/runtime tests with LLVM/MLIR/CIRCT and the JVM absent, plus selected-adapter positive/negative tests; audit transitive dependencies, installation and reproducible manifests.
  - [ ] CIR-03.c Apply the existing formal/differential/runtime-configuration and synthesis-equivalence obligations to each advertised profile; assess configuration-map identity and trigger affected physical/timing requalification for changed implementations.
  - [ ] CIR-03.d Test explicit backend selection, failure/cancellation, unavailable/unsupported versions and upgrade/rollback compatibility; require selected-adapter CI for releases that advertise it and retain an independently checked default path.
  - [ ] CIR-03.e Publish exact final-head/profile evidence, actual generation examples, artifact identities and support limits; activate only the qualified opt-in profiles, never blanket MLIR/CIRCT adoption.

A retain-default or defer decision is a valid completed assessment, not a completed adapter. CIR-02 requires CIR-01's proceed decision; CIR-03 requires CIR-02's adopt decision as well as their checkbox dependencies. Dormant items remain `[ ]`; implementation children cannot be checked by writing this plan. Each parent remains open until every required child and closure gate is complete.

Main risks: duplicating the existing HDL compiler, correlated backend bugs, accidental specialization of configurable silicon, and introducing a mandatory heavyweight dependency through an optional adapter. Do not replace the canonical device database with MLIR, add live cross-language object handles to core, or treat a bounded check or a speed benchmark as commercial qualification.
