# Foundation track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Purpose: establish executable contracts, minimal test infrastructure and a small trusted development baseline before dependent tracks start. This track has no dependency on any non-Foundation increment. All other tracks inherit the completion gate `FND-08`.

Modules: initial Rust workspace under `core/rust/`, a minimal Scala build under `frontend/scala/`, `schemas/`, `verify/fixtures/`, `docs/adr/` and development tooling. Do not scaffold every future crate.

Early verification follows [the baseline contract](../../verification-early-baseline.md). Foundation owns only reference specifications, a minimal external-fixture harness and bootstrap checks; it must not wait for the production generator, CAD flow or VER track. FABulous remains a test-environment dependency, never a reusable-core/default-runtime dependency.

## Foundation checklist and acceptance rules

This track uses the detailed parent/child approach adopted by Nodal, adapted to
the Scala architecture frontend and Rust device/fabric backend. The eight
increment parents and existing `FND-01.a` through `FND-08.e` identities retain
their original obligations and states. Numeric descendants such as
`FND-05.b.1` split independently verifiable deliverables; new `.f` and `.g`
groups cover independent validation and quality/scale review. IDs are stable
references, not execution order. The existing `.e` group remains the final
closure gate, after `.f` and `.g` in each checklist.

Follow [progress rules](../progress.md) and the centralized
[project instructions](../../../AGENTS.md): perform the pre-implementation
readiness review, publish necessary scope corrections before code, use one
increment branch/PR and hourly continuation, qualify targeted checks before
full CI, and verify integration and evidence before closure. This documentation
migration starts no implementation, CI, controller or monitor and completes no
checkbox.

Markdown in the owning track is the authoritative editable progress record.
Reports, future manifests and generated views reference these IDs; they must
not become a second independently editable status ledger. FND-03 owns executable
enforcement of nesting and evidence rules; this migration does not implement
that validator. Split work only when separate evidence is meaningful. Keep
large matrices and procedures in the linked architecture, verification and ADR
documents instead of copying them into every leaf.

### Required review dimensions

| Dimension | Application to Foundation |
| --- | --- |
| Architecture, scope and extensibility | Review existing contracts, actual prerequisites, ownership, reusable representations and unsupported cases before implementation. Keep core independent of concrete devices and optional adapters. |
| Implementation and integration | Deliver the feature at its owning Rust, Scala, schema, tooling or documentation boundary. A stub, compiled prototype or generated example alone does not establish integrated behavior. |
| Correctness, rejection and predecessor regression | Exercise valid, boundary, malformed and unsupported cases, with relevant negative/mutation controls and predecessor interactions selected for a stated reason. Avoid an unbounded cross-product of all future features. |
| Independent validation | Separate specification review, cross-language conformance, external RTL compilation, simulation, formal checks and reference comparisons. Retain actual artifacts, pinned tools, commands, results and limits for applicable execution. |
| Optimization and output quality | Review unnecessary expansion, duplication, materialization, unstable names and repeated traversal; preserve hierarchy, identities and configuration semantics. A justified no-change decision is valid; any introduced transformation needs preservation evidence. |
| Scale, determinism and compatibility | Use representative bounded inputs appropriate to each increment, measure relevant observations and document limits. Do not import the complete PERF program or claim production scale from tiny fixtures. |
| Evidence, documentation and acceptance | Retain reproducible source/artifact identities, capability limits, review, applicable actual Scala/generated-output demonstrations, final-head qualification, verified integration and completion records. |

These dimensions follow Nodal's A–G review model without renaming existing
Nodal-FPGA child IDs or turning every task into HDL generation. A child is
checked only with its own deliverable and applicable evidence; its parent stays
open while any required descendant, dependency or closure obligation remains.
No historical execution, new implementation or performance result is implied
by this breakdown.

### Applicability and independent validation ownership

Record each obligation as required now, blocked by a named dependency, owned
by a named later increment, explicitly optional, or genuinely non-applicable to
the declared profile, with rationale and the resulting claim limit. Reviewing
applicability is a separate deliverable from executing a test. A missing tool,
license, reference artifact or failed/timeout/skipped run cannot turn a required
execution into a pass or a non-applicable result. Follow the amendment policy
before removing or narrowing required scope; preserve IDs and evidence history.

Keep the [early baseline](../../verification-early-baseline.md) and
[ADR 0001 profile matrix](../../adr/0001-optional-circt-backend.md#dependency-isolation-test-matrix)
as the acceptance boundaries:

- FND-02 owns independent contract, assumption-ledger and common-subset review.
  It does not claim executable Scala DSL, Nodal fabric or simulator results.
- FND-05 owns a minimal Scala writer/Rust reader conformance corpus and saved
  package runtime isolation. It does not implement production DeviceDB or RTL.
- FND-06 owns the minimal independent vectors, reference graph, pinned FABulous
  generated-resource comparisons, simulation/formal smoke checks and mutations.
  These are required Foundation executions, not deferred VER work.
- FND-08 replays the applicable Foundation evidence and releases the existing
  downstream gate only after all required Foundation descendants are complete.
- DSL/DB/RTL/CFG/CAD/VER/PERF retain their later implementation and qualification
  ownership. In particular, actual Nodal output comparisons belong to RTL-01–03,
  real-loader checks to RTL-04, and full toolchain comparison to VER-05. Optional
  CIR qualification and physical/silicon/DFT work remain separately gated.

References to later consumers are not new dependency edges. Foundation must
not depend on a blocked track; later owners consume retained witnesses and run
their own required checks. Required Foundation reference runs cannot be moved
to those owners merely because they are unavailable. Bootstrap profile results
must not claim later emission, loader, device inspection or physical validation.

## Increment checklists

- [x] FND-01 — Bootstrap the repository and ownership boundaries
  Depends on: none.
  Evidence: [FND-01 completion report](../../completion/FND-01.md), exact CI/artifacts and verified implementation integration; documentation closure qualified separately.
  - [x] FND-01.a Create the minimal Rust workspace, pinned Rust toolchain and formatter/linter/test entrypoints; prove an unprivileged installation path.
    - [x] FND-01.a.1 Create only the Rust workspace/crates needed for the bootstrap, with the selected Rust/Cargo versions and checked-in dependency lock.
    - [x] FND-01.a.2 Provide formatter, lint and test commands; run the installation/bootstrap path as an unprivileged user and retain the actual commands and results.
  - [x] FND-01.b Select and pin one Scala build tool/JDK/Scala combination; add a tiny frontend smoke build without requiring MLIR.
    - [x] FND-01.b.1 Select and record one compatible Scala/build-tool/JDK set and its reproducible bootstrap procedure; do not maintain parallel build systems without an approved reason.
    - [x] FND-01.b.2 Compile and run a tiny Scala frontend smoke fixture without requiring an LLVM/MLIR/CIRCT SDK; label it as bootstrap rather than the production architecture DSL.
  - [x] FND-01.c Document core/library/device/adapter/application dependency directions and license/proprietary-IP policy; add dependency-boundary checks for reusable core and the default Rust compiler/emitter, with no separately installed LLVM/MLIR/CIRCT SDK or application linkage to those frameworks. Apply the ADR 0001 dependency-isolation matrix; ordinary Rust compiler components are allowed.
    - [x] FND-01.c.1 Document one-way core, library, device, adapter and application dependencies plus license and proprietary-content boundaries against the architecture and ADR.
    - [x] FND-01.c.2 Implement dependency-boundary checks for the existing bootstrap modules; include an intentionally forbidden import/dependency that the intended check rejects.
    - [x] FND-01.c.3 Verify the default Rust-build profile without Scala/JDK or optional compiler SDK/application linkage; retain dependency and invoked-process evidence while allowing normal Rust toolchain components.
  - [x] FND-01.d Test clean checkout builds and docs-only path handling; distinguish genuinely skipped hardware jobs from passed checks.
    - [x] FND-01.d.1 Run clean-checkout Rust and Scala bootstrap checks in their separate declared environments, including useful failure diagnostics for missing prerequisites.
    - [x] FND-01.d.2 Establish the minimal CI checks/triggers needed for bootstrap qualification under AGENTS.md; verify targeted execution is available without changing main or launching unrelated suites.
    - [x] FND-01.d.3 Check documentation-only path/skip behavior and explicit not-yet-applicable hardware lanes; no absent or skipped lane receives execution credit.
  - [x] FND-01.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [x] FND-01.f.1 Review the build and ownership evidence independently of the smoke fixtures; verify that passing compilation did not bypass dependency checks.
    - [x] FND-01.f.2 Record why generated-fabric simulation, synthesis and formal qualification are outside this bootstrap profile, with FND-06 and the later RTL/VER owners retained.
  - [x] FND-01.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [x] FND-01.g.1 Review workspace size, dependency burden and command clarity; remove unnecessary scaffolding only when no required boundary or evidence is lost.
    - [x] FND-01.g.2 Repeat the bootstrap in clean working directories; compare lockfiles and declared outputs, recording reproducibility limits and observed build costs without a production-scale claim.
  - [x] FND-01.e Record reproducible commands and final-head bootstrap evidence; confirm no application or concrete device is imported by core.
    - [x] FND-01.e.1 Retain bootstrap commands, exact source/tree and tool identities, dependency evidence, positive/negative results and profile limitations in the completion report.
    - [x] FND-01.e.2 Complete applicable targeted-first/full-CI qualification, review and verified integration under AGENTS.md; distinguish executed checks from suppressed post-merge CI.
    - [x] FND-01.e.3 Confirm every required descendant and closure obligation is complete before checking FND-01; report the actual Scala smoke example and the absence of generated-Verilog effects.

- [ ] FND-02 — Freeze the initial architecture and project contracts
  Depends on: FND-01.
  - [ ] FND-02.a Write ADRs for Scala-to-Rust exchange, ArchIR versus DeviceDB versus customer DesignDB, and external-CAD-first ownership; apply [ADR 0001](../../adr/0001-optional-circt-backend.md) without treating its optional backend as implemented.
    - [ ] FND-02.a.1 Review and accept the Scala-to-Rust exchange and ownership ADRs, distinguishing ArchIR, immutable DeviceDB and per-job customer DesignDB/CAD state.
    - [ ] FND-02.a.2 Apply ADR 0001 to the external-CAD-first/default-emitter boundary; record optional CIR evaluation as future work rather than a Foundation dependency or adopted implementation.
  - [ ] FND-02.b Specify primitive/mode semantics, hierarchical templates, shared routing/configuration resources and the explicit unsupported-feature policy; create the stable-ID assumption ledger defined in the early-baseline contract, including owners, affected consumers and stage-specific verification obligations.
    - [ ] FND-02.b.1 Specify primitives, modes, hierarchy/templates, shared resources and explicit unsupported-feature diagnostics without depending on production generators.
    - [ ] FND-02.b.2 Create the stable-ID assumption ledger with claim/profile, owner/reviewer, consumers, independent expected examples, owning test/proof/mutation obligations and invalidation policy.
    - [ ] FND-02.b.3 Separate accepted contract decisions from not-run execution status; resolve critical semantic ambiguity rather than labeling it a harmless future test.
  - [ ] FND-02.c Specify overlapping clock/power/configuration domains, technology bindings and device-package identity without implementing advanced devices.
    - [ ] FND-02.c.1 Specify overlapping clock/power/configuration memberships and process-independent technology bindings, including identity/version rules.
    - [ ] FND-02.c.2 Define package identity and incompatible-change behavior without implementing advanced devices, physical signoff or PDK-specific algorithms.
  - [ ] FND-02.d Define the nf-tiny profile and hand-calculated boundary fixtures, including legal and illegal configuration examples; independently review a pinned FABulous-compatible subset, its reference input and the intended Nodal-side mapping, with explicit LUT/pin ordering, register controls, routing/configuration semantics and intentional differences. This contract review does not require the later executable Scala DSL.
    - [ ] FND-02.d.1 Define nf-tiny legal/illegal configurations and asymmetric hand-calculated boundary fixtures with explicit resource, pin, LUT and register-control semantics.
    - [ ] FND-02.d.2 Pin the intended FABulous reference subset and independently authored input/correspondence contract, including routing, configuration, aliases, exclusions and intentional differences.
    - [ ] FND-02.d.3 Review correspondence for totality and ambiguity over the matched subset; identify unsupported modes/shapes and their separate Nodal verification obligations.
  - [ ] FND-02.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [ ] FND-02.f.1 Independently review expected examples, assumptions and pin/resource correspondence against their written semantics; retain decisions and unresolved nonblocking questions.
    - [ ] FND-02.f.2 Assign FND-06 execution IDs/owners for the reference witnesses while explicitly recording that contract review has not run RTL simulation, formal proof or a production Nodal flow.
  - [ ] FND-02.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [ ] FND-02.g.1 Review contract duplication and unnecessary representation constraints; preserve hierarchy, semantic identity and reusable core ownership without adding a general compiler framework.
    - [ ] FND-02.g.2 Walk the contracts through small/boundary and repeated-template examples; document compatibility and expected scaling boundaries without claiming measured compiler performance.
  - [ ] FND-02.e Review contracts against all later track boundaries; record accepted ADRs, the assumption ledger and the common-subset correspondence contract. Resolve critical semantic ambiguities before closing; label scheduled execution evidence as not run and retain genuinely nonblocking choices without claiming implementation.
    - [ ] FND-02.e.1 Audit all later track boundaries and retain accepted ADRs, ledger revision, independent fixture specification and correspondence hashes with rationale.
    - [ ] FND-02.e.2 Resolve critical semantic ambiguities, qualify applicable contract/document checks, and complete review and verified integration under AGENTS.md; scheduled executions remain not run.
    - [ ] FND-02.e.3 Check FND-02 only after every required descendant and FND-01 are complete; deliver the bounded architecture-contract completion report without invented generated output.

- [ ] FND-03 — Enforce resumable nested progress and evidence
  Depends on: FND-02.
  - [ ] FND-03.a Implement a roadmap parser that ignores fenced examples and checks unique increment/leaf IDs and consistent nesting.
    - [ ] FND-03.a.1 Parse authoritative Markdown checkboxes at arbitrary supported nesting depth with two spaces per level, ignoring fenced examples and non-status prose.
    - [ ] FND-03.a.2 Recognize existing IDs and numeric descendants, reject duplicates/malformed ownership, and retain stable IDs rather than deriving status from display order.
  - [ ] FND-03.b Validate dependency references, cycles, the global FND-08 blocker, and the rule that a completed parent has no open descendant.
    - [ ] FND-03.b.1 Validate dependency existence and cycles, including the inherited FND-08 gate; references to future evidence consumers must not create implicit reverse edges.
    - [ ] FND-03.b.2 Enforce checked-parent/required-descendant consistency at every level and the final closure child, while allowing evidenced partial completion under open ancestors.
    - [ ] FND-03.b.3 Validate linked completion evidence and declared source/profile applicability; Markdown remains the sole editable status source for any generated view.
  - [ ] FND-03.c Add completion-report templates for source head, tool/device hashes, commands, results, limitations and actual generated examples, plus assumption IDs, reference-corpus/correspondence hashes, mutation outcomes and configuration-loading mode.
    - [ ] FND-03.c.1 Add completion templates for source/tree, artifacts, tool/device/configuration identity, commands, seeds, results, coverage, limitations and actual applicable examples.
    - [ ] FND-03.c.2 Include assumption IDs, reference/correspondence hashes, mutation outcomes, load mode, review and actual merge identity; distinguish executed CI from verified post-merge suppression.
  - [ ] FND-03.d Test partial completion, reopened regressions, missing evidence, stale heads, invalid checked parents and a dependency-cycle fixture.
    - [ ] FND-03.d.1 Create fixtures for nested partial completion, valid closure, reopened regressions, fenced examples and the Foundation document format introduced here.
    - [ ] FND-03.d.2 Reject duplicate IDs, bad nesting, missing/stale evidence, checked ancestors with open required descendants, unknown dependencies and dependency cycles.
    - [ ] FND-03.d.3 Verify the intended diagnostic for each negative case, including an attempt to treat not-applicable review as required execution or to maintain conflicting generated status.
  - [ ] FND-03.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [ ] FND-03.f.1 Compare parser output with a small hand-authored expectation independent of the parser and production roadmap renderer; do not generate expected status with the code under test.
    - [ ] FND-03.f.2 Review applicable document/evidence checks separately from HDL tools; this validator produces no fabric and cannot qualify generated-Verilog behavior.
  - [ ] FND-03.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [ ] FND-03.g.1 Review parsing/graph traversal for unnecessary repeated scans and clear, stable diagnostics; justify no additional optimization when appropriate.
    - [ ] FND-03.g.2 Exercise nested and many-increment synthetic documents within declared bounds; compare deterministic results and measure relevant time/memory without requiring the PERF track.
  - [ ] FND-03.e Run the validator on the repository and its negative fixtures; retain evidence that partial child completion is accepted correctly.
    - [ ] FND-03.e.1 Run the validator on the actual roadmap and independent positive/negative fixtures; retain proof that valid partial child completion is accepted.
    - [ ] FND-03.e.2 Publish reproducible source/artifact and diagnostic evidence, qualify affected checks, and complete review and verified integration under AGENTS.md.
    - [ ] FND-03.e.3 Check FND-03 only after every required descendant and FND-02 are complete; document enforcement limits and avoid claiming semantic validation of hardware.

- [ ] FND-04 — Implement foundational types and semantic validation
  Depends on: FND-03.
  - [ ] FND-04.a Implement typed IDs, integer/unit bounds, structured diagnostics and source/provenance references in `core/rust/types`.
    - [ ] FND-04.a.1 Implement distinct resource IDs, checked integer/unit bounds and source/provenance references in the minimal core types layer.
    - [ ] FND-04.a.2 Expose structured source-aware diagnostics and test their use through public core APIs without concrete-device or adapter imports.
  - [ ] FND-04.b Define schema-level identities separately from package-local dense IDs; use checked conversions and extensible partition addressing.
    - [ ] FND-04.b.1 Keep portable schema identities separate from package-local dense IDs, including explicit identity/correspondence rules.
    - [ ] FND-04.b.2 Implement checked local/cross-partition and length/offset conversions; exercise near-limit values without giant allocations or unchecked layout assumptions.
  - [ ] FND-04.c Add an initial `arch-ir` model with resource types, interfaces, references, legal modes and configuration-feature declarations.
    - [ ] FND-04.c.1 Implement the initial ArchIR resources, interfaces, references, legal modes and logical configuration-feature declarations needed by the Foundation fixtures.
    - [ ] FND-04.c.2 Verify ownership, type/reference legality and declared sharing/mode constraints while retaining hierarchy and source provenance.
  - [ ] FND-04.d Property-test invalid references, overflow, illegal modes, undeclared shared-bit conflicts and deterministic diagnostics on tiny fixtures.
    - [ ] FND-04.d.1 Property-test valid/boundary tiny models, invalid references, overflow and illegal modes against independently stated expectations.
    - [ ] FND-04.d.2 Reject undeclared shared-bit conflicts and malformed ownership with stable diagnostics; preserve legal explicitly declared sharing.
    - [ ] FND-04.d.3 Exercise selected FND-02 semantic and FND-03 evidence/diagnostic interactions, recording selection rationale rather than an all-features Cartesian product.
  - [ ] FND-04.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [ ] FND-04.f.1 Cross-check tiny model legality and conversions with hand-calculated expectations independent of the implementation validator.
    - [ ] FND-04.f.2 Record the structural/type-validation acceptance profile and later DB/RTL consumers; no RTL simulator, production DeviceDB or fabric-equivalence result is implied.
  - [ ] FND-04.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [ ] FND-04.g.1 Review unnecessary model duplication, hierarchy expansion and lost provenance; any normalization added must preserve declared resource/configuration meaning.
    - [ ] FND-04.g.2 Vary resource counts, reference depth and partition boundaries in bounded fixtures; retain deterministic diagnostics and measured size/time observations.
  - [ ] FND-04.e Publish the tested core contracts and final-head evidence; no unchecked pointer/file-layout assumptions may enter public APIs.
    - [ ] FND-04.e.1 Publish core API/contracts, supported/rejected cases, reproduction commands and exact source/artifact identities; show actual model/diagnostic examples.
    - [ ] FND-04.e.2 Complete affected correctness/regression checks, targeted/full CI, review and verified integration under AGENTS.md; audit pointer and file-layout assumptions at public boundaries.
    - [ ] FND-04.e.3 Check FND-04 only after every required descendant and FND-03 are complete; retain explicit limits on hardware-generation and device-compiler claims.

- [ ] FND-05 — Establish cross-language serialization and compatibility
  Depends on: FND-04.
  - [ ] FND-05.a Define initial versioned ArchIR, mapped-design and package-manifest envelopes with units, feature flags and explicit identity fields.
    - [ ] FND-05.a.1 Define versioned ArchIR, mapped-design and package-manifest envelopes with units, required/optional feature flags and explicit identity fields.
    - [ ] FND-05.a.2 Document compatibility and ownership of each envelope, keeping customer-design state distinct from immutable device identity.
  - [ ] FND-05.b Implement a minimal Scala fixture writer and Rust reader plus canonical text dumps; retain hierarchy instead of fully expanding arrays.
    - [ ] FND-05.b.1 Implement the minimal executable Scala fixture writer in the pinned authoring profile and a Rust reader over the same schema contract.
    - [ ] FND-05.b.2 Provide canonical inspectable dumps and semantic comparison without flattening repeated templates or hierarchy into production routing graphs.
  - [ ] FND-05.c Specify canonical hashing, unknown-version behavior, bounded reads, error paths and migration rules; do not serialize Rust memory layouts.
    - [ ] FND-05.c.1 Specify canonical hashing and semantic versus incidental ordering, excluding machine paths/timestamps from semantic identity.
    - [ ] FND-05.c.2 Implement bounded reads, version/feature negotiation and actionable errors for unsupported inputs; define explicit migration behavior.
    - [ ] FND-05.c.3 Keep the wire representation independent of Rust memory layout, endianness/alignment assumptions and unchecked integer conversions.
  - [ ] FND-05.d Test round trips, truncated/malformed inputs, unsupported required features, field ordering and cross-language semantic equality.
    - [ ] FND-05.d.1 Test Scala-to-Rust semantic equality, supported round trips and canonical field-order permutations against independent fixture expectations.
    - [ ] FND-05.d.2 Reject truncated/malformed inputs, excessive declared sizes, incompatible identities/versions and unsupported required features before unsafe allocation or interpretation.
    - [ ] FND-05.d.3 Exercise FND-04 ID/unit/diagnostic boundaries and preserve hierarchy/provenance across serialization.
  - [ ] FND-05.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [ ] FND-05.f.1 Retain hand-authored known inputs/semantic expectations so a shared writer/reader bug cannot be hidden by round-trip agreement alone.
    - [ ] FND-05.f.2 Generate the fixture with pinned Scala tools, then consume it with prebuilt Rust tools in the separate saved-package runtime profile without Scala/JVM, Rust build tools or optional compiler SDK/application dependencies.
  - [ ] FND-05.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [ ] FND-05.g.1 Review canonical dump readability, duplicate payload and premature expansion; record justified no-change decisions or preservation evidence for introduced transformations.
    - [ ] FND-05.g.2 Vary nesting, repeated-template count and bounded payload lengths; compare stable semantic hashes and supported compatibility behavior while recording size/time limits.
  - [ ] FND-05.e Record the conformance corpus and compatibility matrix; generate the Scala fixture in its pinned authoring environment, then demonstrate consumption by prebuilt Rust tools without Scala/JVM, Rust build tools or LLVM/MLIR/CIRCT application dependencies in the separate saved-package runtime profile.
    - [ ] FND-05.e.1 Publish the conformance corpus, compatibility matrix, source/schema/artifact hashes and actual Scala-input/canonical-output example with executable commands.
    - [ ] FND-05.e.2 Retain authoring and runtime isolation evidence as separate results, complete applicable qualification/review, and verify integration under AGENTS.md.
    - [ ] FND-05.e.3 Check FND-05 only after every required descendant and FND-04 are complete; do not claim later RTL emission or full device inspection from the bootstrap reader.

- [ ] FND-06 — Bootstrap independent verification before generator development
  Depends on: FND-05.
  - [ ] FND-06.a Write independent truth-table, mux-selection and configuration-vector specifications for the tiny fixture; create hand-calculated expected behavior and a simple reference tile graph without production emitters, configuration allocators or topology-normalization helpers.
    - [ ] FND-06.a.1 Author asymmetric LUT truth tables, mux selections and configuration vectors independently of production emitters, allocators and topology-normalization helpers.
    - [ ] FND-06.a.2 Build a simple independently enumerated tiny tile graph with hand-calculated behavior, legal/illegal configurations and explicit pin/resource correspondence.
  - [ ] FND-06.b Wire minimal Rust property testing, RTL simulation and formal-tool smoke tests with pinned tool identities; generate the declared FABulous LUT/register/switch/tiny-tile reference subset and run it against independent vectors in an isolated bootstrap harness, without requiring Nodal-generated RTL or Yosys/nextpnr integration.
    - [ ] FND-06.b.1 Integrate minimal Rust property testing and external RTL simulation/formal smoke tools with pinned executable/solver identities and reproducible commands.
    - [ ] FND-06.b.2 Generate the declared FABulous LUT/register/switch/tiny-tile subset from its independently authored input; preserve actual generated reference RTL and logs.
    - [ ] FND-06.b.3 Run the generated reference resources against the independent vectors/graph in the isolated bootstrap harness without requiring production Nodal RTL or integrated Yosys/nextpnr CAD.
  - [ ] FND-06.c Define reset, initial-state, X/Z, legal-configuration and clock assumptions explicitly for the first profile; bind each fixture and correspondence mapping to the assumption ledger, record unsupported cases, and label static configuration/unit shortcuts separately from future real-loader checks.
    - [ ] FND-06.c.1 Bind fixture/profile and correspondence records to explicit reset, initial-state, clock, X/Z and legal-configuration assumptions and ledger IDs.
    - [ ] FND-06.c.2 Document unsupported modes/shapes and exact result scope; distinguish static/unit setup from actual runtime-loader checks owned by RTL-04.
  - [ ] FND-06.d Inject a wrong mux index, swapped LUT bit and bad config address and demonstrate the intended bootstrap check detects each defect; include a faulty correspondence map and an overconstrained/vacuous-case witness so agreement or an unrelated crash cannot count as success.
    - [ ] FND-06.d.1 Inject wrong mux indexing, swapped LUT bits and bad configuration addresses; require the intended semantic/bootstrap check to reject each defect.
    - [ ] FND-06.d.2 Inject a faulty correspondence map and verify that independent mapping checks expose it rather than normalizing away the mismatch.
    - [ ] FND-06.d.3 Include an overconstrained/vacuous-case witness and useful cover checks; timeouts, unrelated crashes and agreement under invalid assumptions are not mutation-detection passes.
  - [ ] FND-06.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [ ] FND-06.f.1 Retain separate results for reference generation/compile, behavioral simulation, property/formal smoke checks and cover/mutation witnesses with tools, commands, bounds and artifacts.
    - [ ] FND-06.f.2 Review independent expectations and common-mode risks; missing required reference runs or unresolved critical subset mismatches keep this gate open, with no Nodal-fabric qualification claimed.
  - [ ] FND-06.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [ ] FND-06.g.1 Review harness reuse and oracle separation; never regenerate expected semantics from candidate lowering or specialize a programmable resource to the demonstration bitstream.
    - [ ] FND-06.g.2 Exercise supported boundary/asymmetric tiny cases and repeat pinned runs; record seeds, deterministic artifact/graph correspondence and observed resource costs without full-flow/PPA claims.
  - [ ] FND-06.e Archive executable fixtures, both hand-authored specifications and generated FABulous artifacts, pinned revisions, commands, correspondence hashes, mutation results and assumptions. Distinguish bounded checks, unbounded proofs and cover witnesses; missing reference runs block this gate and no Nodal-fabric qualification is claimed yet.
    - [ ] FND-06.e.1 Archive executable fixtures, both independently authored specifications, generated FABulous artifacts, tool/reference revisions, correspondence hashes, assumptions and mutation results.
    - [ ] FND-06.e.2 Distinguish bounded checks, unbounded proofs and cover witnesses; complete required targeted/full-CI qualification, review and verified integration under AGENTS.md.
    - [ ] FND-06.e.3 Check FND-06 only after every required descendant and FND-05 are complete; show actual reference input/output and clearly identify the absence of production Nodal fabric generation.

- [ ] FND-07 — Establish dependency, security and benchmark policy
  Depends on: FND-06.
  - [ ] FND-07.a Pin external tool revisions, build options and artifact checksums; record licenses and redistribution boundaries without vendoring restricted IP.
    - [ ] FND-07.a.1 Pin required external tools, build options and artifact checksums, identifying which belong only to the reference/test environment.
    - [ ] FND-07.a.2 Record license, redistribution and restricted-IP boundaries; verify no proprietary material or secret keys enter redistributable fixtures or default core dependencies.
  - [ ] FND-07.b Define supported execution environments, resource limits, sandboxed untrusted inputs and nonsecret configuration handling.
    - [ ] FND-07.b.1 Declare supported build/runtime/test profiles, host assumptions and resource/input-size limits consistent with ADR 0001.
    - [ ] FND-07.b.2 Define isolation of untrusted inputs and nonsecret configuration handling, keeping privileged board/PDK environments outside untrusted CI execution.
  - [ ] FND-07.c Define benchmark metrics, runner identity, workload hashes, baseline update policy and the future small/medium/large synthetic profiles.
    - [ ] FND-07.c.1 Define workload/corpus identity, runner/tool identity and separate time, memory, storage and throughput measurements with a reviewed baseline-update procedure.
    - [ ] FND-07.c.2 Describe future small/medium/large synthetic profiles and their PERF ownership; do not claim backend or production-scale measurements before those implementations exist.
  - [ ] FND-07.d Test lockfile drift detection, missing-tool diagnostics, deterministic fixture hashes and oversized input rejection.
    - [ ] FND-07.d.1 Detect altered lockfiles/checksums and missing required tools with the intended useful diagnostics rather than silent fallback.
    - [ ] FND-07.d.2 Repeat fixture hashing and reject oversized inputs within declared bounds; exercise the existing FND-05 reader and FND-06 tool assumptions.
  - [ ] FND-07.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [ ] FND-07.f.1 Independently verify a representative pinned artifact/checksum and input-limit expectation; retain failure evidence for deliberately mismatched metadata.
    - [ ] FND-07.f.2 Separate policy review, executed bootstrap checks and future adapter/performance qualifications; record genuine applicability without relabeling missing required tools as optional.
  - [ ] FND-07.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [ ] FND-07.g.1 Review unnecessary downloads/dependency duplication and cost of policy enforcement while preserving integrity and input-safety guarantees.
    - [ ] FND-07.g.2 Measure the bootstrap workloads under recorded runner/tool/input identities and repeat deterministic hashes; document the reproducibility envelope and limits of extrapolation.
  - [ ] FND-07.e Record verified baseline commands and review exact adapter assumptions; no claim of full backend integration is made here.
    - [ ] FND-07.e.1 Record verified commands, pin/license inventory, profile boundaries, benchmark procedures and exact adapter assumptions with reproducible source/artifact identities.
    - [ ] FND-07.e.2 Complete applicable policy/tooling/regression qualification, review and verified integration under AGENTS.md without claiming full backend integration.
    - [ ] FND-07.e.3 Check FND-07 only after every required descendant and FND-06 are complete; provide actual policy/check outputs and a bounded no-new-Verilog-effects statement.

- [ ] FND-08 — Release the Foundation gate
  Depends on: FND-07.
  - [ ] FND-08.a Audit completion evidence for FND-01 through FND-07 and confirm Foundation has no dependency on blocked tracks.
    - [ ] FND-08.a.1 Audit every FND-01–07 parent/descendant and its own accepted deliverables, review, source/artifact identity and evidence limits.
    - [ ] FND-08.a.2 Verify dependency direction and the unchanged global FND-08 gate; reject any circular reliance on blocked production, optional-backend or physical/silicon tracks.
  - [ ] FND-08.b Run clean Rust/Scala builds, schema conformance, negative fixtures, roadmap validation and independent test smoke suites; replay the pinned FND-06 reference corpus in its separate test environment and reject unresolved critical baseline mismatches.
    - [ ] FND-08.b.1 Run clean pinned Rust/Scala builds, schema conformance, malformed/negative fixtures and roadmap/evidence validation on the release candidate.
    - [ ] FND-08.b.2 Replay the required independent property/simulation/formal smoke and mutation checks plus the pinned FND-06 reference corpus in its separate test environment.
    - [ ] FND-08.b.3 Resolve critical baseline mismatches and missing required runs; preserve genuine non-applicable classifications and actual proof/simulation limits.
  - [ ] FND-08.c Run the default Rust-build, saved-package-runtime and Scala-authoring profiles from ADR 0001 separately; confirm reusable core has no concrete-device, external-CAD or optional-adapter dependency. Keep the ordinary Rust toolchain intact and distinguish its internal components from application SDK/runtime dependencies.
    - [ ] FND-08.c.1 Run default Rust-build, saved-package runtime and Scala-authoring profiles independently using the Foundation capabilities that actually exist.
    - [ ] FND-08.c.2 Retain dependency and process evidence that reusable core does not import concrete devices, external CAD or optional adapters; allow ordinary Rust compiler internal components.
    - [ ] FND-08.c.3 Identify later emission/inspection and opt-in-adapter checks by owning track, without claiming them passed or introducing a reverse Foundation dependency.
  - [ ] FND-08.d Freeze the initial contract baseline, assumption ledger and reference/correspondence manifests; explicitly list supported and rejected capabilities plus benchmark measurement procedures, and identify which later checks cannot run until their owning RTL/DB/VER increments exist.
    - [ ] FND-08.d.1 Freeze the reviewed contract, schema, assumption-ledger, reference/correspondence and toolchain manifests with immutable identity and change/invalidation rules.
    - [ ] FND-08.d.2 Publish supported/rejected capabilities, benchmark procedures, reproducible commands and exact later DSL/DB/RTL/CFG/CAD/VER/PERF ownership for unimplemented capabilities.
  - [ ] FND-08.f Independent validation and applicability. Keep independent review/execution results and current-profile limits separate from implementation claims.
    - [ ] FND-08.f.1 Independently review the release dossier against original contracts and retained expected vectors; verify that regenerated goldens or shared implementation helpers have not substituted for independent evidence.
    - [ ] FND-08.f.2 Keep clean-build, conformance, reference generation, simulation, formal, cover/mutation and dependency-isolation results distinct and bound to the qualified source/profile.
  - [ ] FND-08.g Optimization review, scale, determinism and compatibility. Apply proportionate feature-specific checks without importing later production or PERF obligations.
    - [ ] FND-08.g.1 Review remaining abstraction/dependency burden and output/diagnostic quality without pulling a full fabric, native CAD or general HDL compiler into Foundation.
    - [ ] FND-08.g.2 Repeat applicable bounded scale/determinism checks from prior increments; document measured baseline observations, compatibility limits and explicitly unqualified production behavior.
  - [ ] FND-08.e Record final-head evidence and open the downstream-track gate only after every required Foundation leaf is complete.
    - [ ] FND-08.e.1 Complete the exact final-head targeted-first/full-CI and review gates, then verify the actual integration/tree and post-merge suppression under AGENTS.md.
    - [ ] FND-08.e.2 Integrate the completion dossier and authoritative checklist consistently, retaining all required evidence and actual applicable Scala/schema/reference demonstrations.
    - [ ] FND-08.e.3 Check FND-08 and open downstream eligibility only after every required Foundation descendant, dependency and closure obligation is complete; stop its monitor only after the completion report is delivered.

Main risk: replacing a tested foundation with a large paper-only abstraction framework. Exit requires executable minimal contracts, not a full fabric. Do not build native synthesis/P&R, analog IP, GUI or multi-die algorithms in Foundation.
