# Verification and qualification strategy

## Independent evidence, not one golden generator

Verification must establish that the architecture semantics, device database, emitted fabric RTL, CAD adapter, logical configuration, physical bitstream and loader agree. A correct shared schema improves consistency but can propagate one bug into every generated view. Expected results therefore require independent fixtures, models and checking paths.

FABulous documents runtime-bitstream fabric simulation and a gate-level flow that can retain behavioral wrapper/controller portions. These are useful reference techniques, not a proof of every configuration or whole-chip signoff. [S1](sources.md#s1) [S2](sources.md#s2)

```text
Independent primitive/configuration specification
       |                         |
slow reference model      hand-calculated vectors
       |                         |
       +---------- compare ------+
                         |
ArchIR --> DeviceDB --> CAD route --> logical config --> bitstream
   |          |             |                              |
   +--> emitted fabric RTL <+------- real RTL loader -------+
                         |
                  observable behavior
                         |
        original customer RTL / mapped-design model
```

## What to compare with FABulous

A FABulous fixture must pin generator and toolchain revisions and define the same primitive truth tables, reset/clock semantics, routing subset and I/O behavior. An independent correspondence map names equivalent resources without relying on identical generated identifiers.

| Comparison | Acceptance basis |
| --- | --- |
| Primitive behavior | Identical declared logic/state behavior for the matched subset |
| Topology and resource counts | Exact correspondence only when the same architecture is intentionally specified |
| Routing | Connectivity/legality and configured function; different legal routes are acceptable |
| Configuration | Equivalent resource settings; byte equality only with an intentionally identical encoding/address contract |
| PPA and timing | Comparable experiment inputs/corners/constraints; trends are benchmarks, not correctness proofs |
| Gate-level and board runs | Same functional corpus, with all differing wrappers/macros/assumptions disclosed |

New Nodal-only modes, clocking, hard macros or configuration features require their own specifications and tests; no FABulous comparison is possible until a genuine common subset exists. If tools disagree, minimize the case and use independent semantics to decide which result is wrong. Do not change expected output merely to match the current generator.

## Early acceptance gates and assumptions

Follow [the early-baseline contract](verification-early-baseline.md). FND-02 owns a reviewed common-subset specification and stable-ID assumption ledger. FND-06 bootstraps independent expected vectors and pinned FABulous reference runs without requiring the production Nodal generator. RTL-01–03 must compare actual generated resources/fabrics before closure; RTL-04 must use the real configuration loaders. VER-05 extends, rather than starts, this work with complete toolchain comparison. The same artifact identities are replayed or explicitly requalified as implementations change.

Expected semantics, resource correspondence and comparison inputs require independent review; generating them all from production lowering would preserve common-mode bugs. A matched-subset claim must include exact behavior and connectivity, not just resource counts. Record unsupported modes and intentional differences without forcing future Nodal-only features to reproduce FABulous restrictions. Required reference failures or missing tools/artifacts block the owning gate; they do not become passes by being called optional comparisons.

Keep assumption decisions separate from their verification status. An accepted design convention is not a passed proof. Trace changes in assumptions, reference versions or correspondence maps to affected generators, encoders, databases, tests and device-package revisions; reopen invalidated evidence under the progress policy.

## Representation-invariance checks

DB-01–04 and DB-06 compare permitted declaration reordering/internal renaming, compact versus independently expanded tiny graphs, partitioned versus unpartitioned views, portable versus mmap readers, and full versus incremental builds. Check selected connectivity, legal modes, shared controls and configuration meaning, not only counts or hashes. VER-03 and VER-07 replay these obligations against generated-view behavior and release manifests.

Use explicit semantic identity mappings: dense IDs, section order and bitstream bytes need not survive a representation change. Preserve or rebind physical configuration addresses under a new package identity, rejecting incompatible prior bitstreams. The reference expander/checker must not call the production compression or partitioning transformations. Large-device performance tests do not substitute for these tiny semantic checks, and tiny exhaustive expansion must not become a mandatory large-device storage format.

## Proof and simulation layers

Primitive properties cover LUT indexing, mux selection, register control priorities and declared memory/arithmetic behavior. Legal configuration constraints are explicit. Many arbitrary raw bit patterns are unsafe or meaningless; do not prove only an overconstrained legal subset while claiming every possible bitstream is safe.

Tile/region verification composes proven resource contracts with separately checked wiring, mode exclusions and configuration ownership. Verify assumptions at composition boundaries; proving each primitive alone does not prove the assembled FPGA.

Configured-design equivalence compares the original or independently mapped customer design to the programmed fabric under a stated reset/initial-state relation and interface latency. Capture X/Z and four-state versus two-state differences. Use bounded runs, unbounded proofs and cover witnesses with their actual labels. SymbiYosys supports multiple formal workflows; EQY supports equivalence checking, but tool availability is not proof completion. [S8](sources.md#s8) [S9](sources.md#s9)

Runtime simulation must use the real configuration loader for at least the required release corpus. Hierarchical force/preload is permitted for isolated unit diagnostics only and must be identified as a shortcut. Test incomplete configuration, illegal addresses, reset/clock interruption, wrong-package identity and transition between unrelated user designs.

A parser/encoder round trip can hide a shared mapping error. Combine round trips with independently specified known vectors, RTL loader checks and observable configured behavior. Field isolation allows documented integrity/header updates and explicit aliases; it does not require an unchanged checksum after a payload edit.

## Coverage and mutation

Maintain a requirement/obligation ledger for resource types and modes, mux choices, interface transitions, field mappings, reset states, route legality, timing models and supported tool/device combinations. Record numerator and denominator plus unreachable/unsupported classifications. Release requires every required obligation to have a passing witness/proof or an explicitly reviewed non-applicability decision; unresolved critical correctness obligations block release. Never silently waive a required implementation leaf.

All reachable PIPs being exercised once is useful but does not prove all combinations, hazards, timing behavior or manufacturing faults. Include concurrency/shared-control combinations, decoder aliases, boundary shapes and rare configuration transitions. Add mutations for reversed LUT indexing, swapped endpoints, wrong configuration addresses, missing mode exclusions and reset-priority errors. Check that the intended verifier, not an unrelated crash, detects each mutation.

## CI and evidence tiers

| Tier | Required scope | Evidence |
| --- | --- | --- |
| Documentation change | Links, IDs, dependency graph, nested completion and evidence consistency | Documentation validation; no claim of hardware tests |
| Code PR | Affected Rust/Scala tests, schema conformance, negative tests, applicable primitive formal and tiny end-to-end tests | Exact head/tree, commands, logs and artifacts |
| Scheduled regression | Seeded random architectures/designs, differential baselines, fuzzing, scale and available board tests | Corpus/tool hashes, failures, minimized reproducers and coverage |
| Device release | All supported profiles, tool/version matrix, complete logical obligations and applicable emulation | Immutable verification dossier with limitations |
| Tapeout readiness | Process-specific DRC/LVS/PEX/STA, power/IR/EM, CDC/RDC, DFT/test, macro and package integration | Qualified signoff evidence and independent review |
| Product release | Silicon correlation, production test, reliability, supported limits and SDK compatibility | Measured product-specific qualification evidence |

Select exact schedules and budgets during Foundation; do not claim expensive suites have run simply because their workflow exists. Pin actual tools, containers/dependencies and formal solvers. Separate privileged board/PDK jobs from untrusted code execution. Missing licenses, hardware or supported models are blockers/limitations, not successful skips.

## Physical and silicon boundaries

RTL equivalence does not verify clock-tree quality, analog jitter, electrical I/O limits, electromigration or test coverage. Gate-level simulation may be mixed-level; record which controller/wrapper/macro regions remain behavioral and whether timing was annotated. Open tools can support implementation experiments, while actual foundry/process acceptance requires the applicable qualified decks, models and signoff procedure.

Reuse immutable corpus identities across original RTL, fabric RTL, gate netlists, FPGA emulation and fabricated silicon. Board emulation is not an ASIC frequency/power measurement. Correlate silicon timing/power/failure behavior before assigning supported operating limits or speed grades. Track any mismatch back to model/tool/device revisions and reopen invalidated completion evidence.

## Acceptance artifacts

Each completion report records source and generated-artifact hashes, architecture/library/technology identity, simulator/formal/CAD versions, solver/depth/assumptions, seeds and worker policy, exact commands, positive and negative results, coverage ledger and limits. Store large artifacts by content hash, not as unverifiable statements in a PR body. Archive enough information to reproduce historical device releases even after core/library refactoring. Include the applicable assumption-ledger revision, reference specification and correspondence hashes, both generated fabric artifacts, configuration-loading method and evidence of replay after relevant baseline changes.
