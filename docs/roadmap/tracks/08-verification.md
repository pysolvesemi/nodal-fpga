# Verification, formal and differential validation track

[Roadmap index](../README.md) · [Progress rules](../progress.md) · [Verification policy](../../verification.md)

Global blocker: FND-08. Modules: `verify/{spec-model,formal,differential,simulation,coverage,fixtures}` and `adapters/fabulous`. Expected behavior must not be copied from the same emitter/encoder being checked. FABulous is one comparison source, not the sole oracle.

- [ ] VER-01 — Independent executable reference model
  Depends on: FND-08.
  - [ ] VER-01.a Implement a small slow model from primitive/configuration specifications, avoiding production lowering and RTL-emission helpers.
  - [ ] VER-01.b Model legal selected connectivity, LUT truth tables, sequential state and declared reset/initial-state behavior.
  - [ ] VER-01.c Keep independent hand-authored fixtures and explicit abstraction limits for unsupported analog/timing behavior.
  - [ ] VER-01.d Validate the model with exhaustive tiny examples and mutation cases before using it as an oracle.
  - [ ] VER-01.e Record model independence review, expected vectors and final-head regression evidence.

- [ ] VER-02 — Primitive, switch and configuration proofs
  Depends on: VER-01, LIB-01, CFG-02.
  - [ ] VER-02.a Prove LUT truth-table selection, mux behavior and register contracts under explicit supported mode/reset assumptions.
  - [ ] VER-02.b Check logical-feature/physical-field correspondence against independent vectors, including declared aliases and illegal selections.
  - [ ] VER-02.c Add cover witnesses to detect vacuous constraints and distinguish arbitrary legal configuration from unsafe arbitrary bit patterns.
  - [ ] VER-02.d Inject indexing, endian, reset-priority and configuration-allocation mutations; require the relevant check to fail.
  - [ ] VER-02.e Archive proof manifests with depth, solver, assumptions, results and final-head identity; timeouts never count as proofs.

- [ ] VER-03 — Tile and generated-view consistency
  Depends on: VER-02, RTL-03.
  - [ ] VER-03.a Check DeviceDB endpoints and legal modes against generated RTL and configuration-map semantics.
  - [ ] VER-03.b Compose primitive/tile contracts with explicit assumptions; validate interface wiring and shared-control restrictions separately.
  - [ ] VER-03.c Compare configuration-driven RTL behavior with the independent model for small tiles and fabrics.
  - [ ] VER-03.d Test edge/corner/sparse layouts and deliberate mismatches between DB, RTL and bitstream mapping.
  - [ ] VER-03.e Record compositional proof scope, structural checks and final-head generated-view consistency evidence.

- [ ] VER-04 — End-to-end user-design equivalence
  Depends on: VER-03, CAD-04.
  - [ ] VER-04.a Generate bounded random combinational/sequential circuits and retain minimized counterexamples and reproducible seeds.
  - [ ] VER-04.b Compare original RTL, mapped design, reference model and runtime-configured fabric over defined reset/startup/latency semantics.
  - [ ] VER-04.c Add formal equivalence for tractable configured designs with explicit state correspondence, not unrelated arbitrary initial states.
  - [ ] VER-04.d Test multiple placements/routes/seeds and negative route/configuration mutations; classify unsupported cases rather than dropping them.
  - [ ] VER-04.e Record corpus hashes, simulation lengths, proof scope, failures and final-head end-to-end evidence.

- [ ] VER-05 — Pinned FABulous differential baseline
  Depends on: VER-04.
  - [ ] VER-05.a Pin FABulous and its complete toolchain and document a precisely matched architecture/primitive/configuration subset.
  - [ ] VER-05.b Build independently specified comparable small fabrics; compare normalized connectivity, resource modes and observable behavior.
  - [ ] VER-05.c Compare bitstream bytes only where address/encoding contracts intentionally match; otherwise decode semantic configuration before comparison.
  - [ ] VER-05.d Separate functional failures from differing legal placements or PPA trends; investigate disagreements against the independent model.
  - [ ] VER-05.e Archive both tool revisions, fixtures, correspondence maps and final-head results, including intentional incompatibilities.

- [ ] VER-06 — Coverage, fuzzing and fault containment
  Depends on: VER-04, CFG-05.
  - [ ] VER-06.a Track obligations for resource types/modes, reachable mux selections, configuration transitions, regions and malformed-input behavior.
  - [ ] VER-06.b Generate directed uncovered-resource tests, using test-only forced bindings when required and distinguishing them from normal mapper coverage.
  - [ ] VER-06.c Fuzz readers, configuration loaders and route checkers; inject corruption, clock/reset interruption and illegal sharing.
  - [ ] VER-06.d Record coverage denominators, reachable/unreachable classifications and reviewed exclusions; do not equate resource coverage with all-configuration proof.
  - [ ] VER-06.e Record mutation effectiveness, unresolved coverage gaps and final-head acceptance disposition for every required obligation.

- [ ] VER-07 — Release-level verification dossier
  Depends on: VER-05, VER-06, RTL-05.
  - [ ] VER-07.a Run the pinned cross-language, property, simulation, formal, differential and synthesis-equivalence suites for each released profile.
  - [ ] VER-07.b Check assumptions and tool independence; record mixed-level/black-box boundaries and confidence limitations explicitly.
  - [ ] VER-07.c Produce immutable artifact manifests and trace requirements to tests/proofs/coverage records.
  - [ ] VER-07.d Exercise clean reproduction and deliberately missing/stale evidence; block a release with unresolved critical correctness obligations.
  - [ ] VER-07.e Publish final-head verification evidence and supported scope; physical, emulation and silicon claims require their own later gates.

Main risk: correlated oracle bugs and overstated proof coverage. Do not attempt a monolithic all-configurations formal proof of a giant FPGA as the first verification milestone. [S1–S3](../../sources.md#s1), [S8/S9](../../sources.md#s8) motivate complementary checking strategies.
