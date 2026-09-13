# Verification, formal and differential validation track

[Roadmap index](../README.md) · [Progress rules](../progress.md) · [Verification policy](../../verification.md)

Global blocker: FND-08. Modules: `verify/{spec-model,formal,differential,simulation,coverage,fixtures}` and `adapters/fabulous`. Expected behavior must not be copied from the same emitter/encoder being checked. FABulous is one comparison source, not the sole oracle.

The [early-baseline contract](../../verification-early-baseline.md) puts reference preparation in FND-02/FND-06 and actual generated-resource/fabric comparisons in RTL-01–04. VER-05 extends that baseline to full toolchain qualification; it is not the first external check. Existing dependencies are unchanged, and this track does not retroactively become a Foundation prerequisite.

- [ ] VER-01 — Independent executable reference model
  Depends on: FND-08.
  - [ ] VER-01.a Implement a small slow model from primitive/configuration specifications and the reviewed Foundation assumption ledger, avoiding production lowering, configuration-allocation, topology-normalization and RTL-emission helpers.
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
  - [ ] VER-03.d Test edge/corner/sparse layouts and deliberate mismatches between DB, RTL and bitstream mapping; replay compact/expanded, partitioned/unpartitioned and permitted-renaming cases against independent expectations, including corrupted correspondence maps.
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
  - [ ] VER-05.a Carry forward and revalidate the pinned Foundation/RTL FABulous baseline; pin the complete synthesis/P&R/simulation toolchain and extend the independently reviewed common-subset and assumption/correspondence manifests. A changed upstream version requires differential requalification, not blind golden regeneration.
  - [ ] VER-05.b Build independently specified comparable small fabrics and retain both actual generated RTL sets; compare normalized connectivity, resource modes and observable behavior. Keep separate hand-configured generator tests and full user-RTL-through-toolchain tests, comparing each configured fabric to the original design or independent specification.
  - [ ] VER-05.c Compare bitstream bytes only where address/encoding contracts intentionally match; otherwise use independently checked semantic correspondence plus observable behavior through each real loader. Record reset/activation alignment and transport differences; decoder round trips, text equality and forced/preloaded state cannot substitute for runtime evidence.
  - [ ] VER-05.d Separate functional failures from differing legal placements or PPA trends; minimize disagreements and investigate against the independent model, vectors and assumption ledger. Test checker mutations and shared-tool blind spots; never alter the expected specification just to match either generator.
  - [ ] VER-05.e Archive both tool revisions, actual source/RTL/bitstreams, fixtures, correspondence and assumption hashes, and final-head results, including intentional incompatibilities and affected early-gate replays. Missing references or unresolved common-subset correctness mismatches block closure; Nodal-only capabilities retain independent obligations.

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
  - [ ] VER-07.c Produce immutable artifact manifests and trace requirements and assumption IDs to tests/proofs/coverage records, including Foundation/early-RTL baselines and representation-invariance evidence. Record shared dependencies between purportedly independent checkers.
  - [ ] VER-07.d Exercise clean reproduction and deliberately missing/stale evidence, changed assumptions, missing FABulous artifacts and invalid correspondence maps; block a release with unresolved critical correctness obligations and reopen affected gates when baseline semantics change.
  - [ ] VER-07.e Publish final-head verification evidence and supported scope; physical, emulation and silicon claims require their own later gates.

Main risk: correlated oracle bugs and overstated proof coverage. Do not attempt a monolithic all-configurations formal proof of a giant FPGA as the first verification milestone. [S1–S3](../../sources.md#s1), [S8/S9](../../sources.md#s8) motivate complementary checking strategies.
