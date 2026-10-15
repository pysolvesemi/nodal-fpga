# FND-02 readiness audit

Integration target inspected: `83394f265499c4158e22d9a2014552091db0eb1b`
(`dev`). FND-01 implementation and evidence are integrated; FND-02 through
FND-08 remain open. The remote had no open PRs at this audit. `main` is not a
development target and is unchanged. The sole working branch for this increment
is `increment/fnd-02-schema` (historical initial slug; scope is contracts).

## Acceptance boundary

Read AGENTS.md, roadmap index/progress, complete Foundation checklist,
architecture, verification, early baseline, ADR 0001 and FND-01 completion.
Existing executable capabilities are a dependency-free Rust bootstrap, Scala
smoke program, Python ownership/link controls and registered FND-01 workflow.
There is no ArchIR/schema reader, DSL, device generator or independent RTL
harness. Reuse the bootstrap checks; do not claim those later capabilities.
No checklist correction or scope amendment is needed. Every FND-02 leaf is
required now; this audit does not mark any leaf complete.

| IDs | Required deliverable and validation |
| --- | --- |
| a.1, a.2 | Portable exchange and ownership ADRs; external-CAD-first/default focused emitter; optional CIR remains dormant |
| b.1, b.2, b.3 | Primitive/template/sharing contracts and stable assumption ledger; resolve critical ambiguities; decisions separate from not-run executions |
| c.1, c.2 | Overlapping domains, technology binding and exact package identity/invalidation rules |
| d.1, d.2, d.3 | Asymmetric tiny legal/illegal examples; independently authored pinned FABulous input and total unambiguous resource/pin correspondence |
| f.1, f.2 | Separate independent contract/vector/correspondence review; name required FND-06 witnesses, explicitly not executed here |
| g.1, g.2 | Minimal reusable contracts and bounded/repeated-template walkthrough; compatibility limits without compiler-performance claims |
| e.1, e.2, e.3 | Later-track ownership audit, immutable contract hashes, required targeted checks and final combined Foundation CI, independent review, verified dev integration and completion report |

The parent and closure gate remain open until all obligations have actual
evidence. FND-03 status enforcement, FND-04 executable types/semantic model,
FND-05 schema writer/reader, and FND-06 reference generation/simulation/formal
are named later owners, not waived requirements of their increments. Production
fabric, CAD, loader, physical and silicon checks are outside FND-02, and no
blocked track becomes a reverse prerequisite.

## Independent review and qualification

Review the reference source independently of Nodal lowering (none exists), and
review vectors/maps independently of their author. Retain upstream revision,
input hashes, exact pin/config semantics and intentional differences. Unknown
critical reference behavior blocks acceptance rather than becoming an assumed
compatibility claim. Contract decisions were proposals until the [independent review](fnd-02-independent-review.md)
resolved them; future execution evidence remains `not-run`.

Local baseline `./nf check contracts` passed 20 controls with Python 3.12.14.
This is baseline local evidence only. No remote FND-02 run has occurred. Current
cloud filesystem has Python and Java but no Rust/Cargo, sbt, simulator or formal
executable on PATH; later required checks need pinned setup or isolated CI.

## Current checkpoint and user-directed qualification cadence

Draft [PR #3](https://github.com/pysolvesemi/nodal-fpga/pull/3) records the
readiness audit and initial source. Current phase: contract implementation and independent review complete;
preparing exact-head local qualification and verified integration.

Latest user instruction (2026-10-15): add and run required local tests for each
increment, then merge to dev when those pass. Do not run pre-merge or post-merge
remote CI. Run the full all-tests CI suite only after the complete Foundation is
implemented, then fix failures before claiming the roadmap done. This overrides
the older per-increment remote-CI cadence. Do not weaken assertions or bypass
branch protection. Flag missing local required execution or CI-required branch
protection before merging. Publish ordinary-ancestry `[skip ci]` candidates and
verify actual merge trees. No CI has been dispatched for this increment.

FND-02 is contract-only. Execute contract validation and bootstrap predecessor
checks locally, retain exact commands/results and independent review. Reference
RTL execution stays not-run until FND-06. Other required runtime/build profiles
need actual pinned tools at their owning increments.

Keep qualification and verified integration outstanding until actually done.

This increment does not affect generated Verilog.
