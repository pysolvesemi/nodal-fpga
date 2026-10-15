# FND-02 — Reviewed architecture and project contracts

FND-02's contracts are independently reviewed and integrated into `dev`.
This documentation-only closure retains actual local evidence and reconciles
the authoritative [checklist](../roadmap/tracks/00-foundation.md). The latest
explicit user direction is local tests before each increment merge, no pre- or
post-merge CI unless protection requires it, and full combined Foundation CI at
the end. This supersedes the older per-increment remote-CI cadence; no test or
branch-protection requirement was bypassed. FND-08 remains open.

## Exact source and integration

| Identity | Value |
| --- | --- |
| Qualified implementation | `d312b58ea53d62b5c396b8355c5f2bda8e2afe62` |
| Qualified tree | `1a3409535dd9de99619bcee47822ea9c544ef6dc` |
| Original target | `83394f265499c4158e22d9a2014552091db0eb1b` |
| Actual implementation merge | [PR #3](https://github.com/pysolvesemi/nodal-fpga/pull/3), `c8920b77f1d96d9cc47ab41047c9d6b353fadd0a` |
| Actual merge parents | Original target, then qualified implementation above |
| Actual merge tree | `1a3409535dd9de99619bcee47822ea9c544ef6dc`, exactly equal to tested tree |
| Remote CI | Not run, explicitly deferred by user instruction; no remote execution credit |
| Post-merge CI | `skipped`, reason `user-directed-local-qualification-identical-tree-merge`; actual merge title contains `[skip ci]` |

Source identity records `dirty=false`. Checks/statuses and review discussions
were empty before integration; `dev` reported protection disabled and no required
contexts. No protections were changed. Ordinary merge ancestry was retained and
`main` stayed at `1b28e5cbcc064455a73600ab311f6f9bf071e3fc`.
The documentation closure's final identity/check and actual integration are
recorded in its PR. This report anchors implementation checks to the exact source
above, not to a later documentation commit.

## Retained commands and results

[Evidence index](evidence/fnd-02/index.json) records SHA-256 identities for the
raw local logs and accepted contracts. [Source metadata](evidence/fnd-02/source.json)
binds those checks to the clean implementation head/tree.

- `./nf check contracts`: [actual log](evidence/fnd-02/contracts.log), 20 existing
  bootstrap controls plus 43 new Foundation controls passed. Checks cover
  ownership, local documentation links, 12 assumption records, 22 hashed input
  files, four shape graphs, 16 LUT-address rows, eight mux rows and 20 config bits.
- `./nf check rust`: [actual log](evidence/fnd-02/rust.log), format, warning-denying
  clippy, all-target tests, one doctest and locked/offline dependency metadata
  passed. Existing bootstrap remains one dependency-free crate.
- `./nf check scala`: [actual log](evidence/fnd-02/scala.log), both format checks,
  clean compile and explicit Scala/sbt version observations passed.
- `git diff --exit-code`: passed after execution; no tested-source modification.

Observed Python 3.12.14, Rust/Cargo 1.98.1, rustfmt 1.9.0-stable, clippy 0.1.98,
Scala 3.3.8, sbt 1.12.11, Temurin 21.0.12.1+1-LTS/Eclipse Adoptium. Tool pins and
checksums are unchanged from FND-01. Local setup used workspace-only caches;
Java used the environment's existing OS trust store without disabling TLS, and
sbt batch/no-server options avoided unavailable Unix socket creation. These are
local build-regression results, not a fresh isolated-container/runtime claim.
FND-01's prior isolated-build evidence remains separately identified.

## Deliverables and independent review

[Independent review](../implementation/fnd-02-independent-review.md) records
source inspection, exact pre-promotion artifact hashes, findings and repairs.
It is an independent agent review, not claimed human approval. Acceptance-only
state changes did not change semantics; final accepted hashes are in the index.

| Required leaves | Accepted evidence |
| --- | --- |
| a.1, a.2 | [ADR 0002](../adr/0002-portable-architecture-exchange.md), [ADR 0003](../adr/0003-device-design-ownership.md): strict exchange, immutable DeviceDB/per-job DesignDB, external-CAD-first; ADR 0001/default focused emitter retained; optional CIR not adopted |
| b.1–b.3 | [Foundation contracts](../contracts/foundation.md) and [12-record ledger](../../verify/fixtures/assumptions/ledger.json): precise primitive/mode/template/sharing semantics, owners/consumers, independent examples, stage-specific obligations and invalidation; decision acceptance separated from execution |
| c.1, c.2 | Overlapping domain sets, process-independent bindings, exact package-qualified identity and incompatible-change rejection; no advanced-device implementation claimed |
| d.1–d.3 | [nf-tiny contract](../contracts/nf-tiny.md), asymmetric truth/state/mux/config vectors, legal/illegal cases, independently enumerated 1x1/2x2/3x2/sparse3x3 graphs, source-pinned FABulous input and total resource/pin/config map |
| f.1, f.2 | Independent source/vector/map review, common-mode risks, specific FND-06 generation/simulation/formal/cover/mutation IDs; every execution state remains not-run |
| g.1, g.2 | No general compiler framework or premature flat expansion; finite reusable templates, typed identities, explicit domain/sharing/ordering boundaries; hand-calculated repeated/boundary examples with no measured compiler-scale claim |
| e.1 | All 16 later-track boundaries audited, accepted ADR/ledger/spec/reference/correspondence hashes retained; no blocked-track prerequisite added |
| e.2, e.3 | Critical ambiguities resolved, required local checks and independent review passed, actual implementation merge/tree verified; this evidence/checklist closure records accepted FND-02 completion under the latest user cadence |

Review found and corrected permissive output/pin/config mappings, empty coverage
inventories, missing acceptance/hash gates, and incomplete assumption-to-mutation
traceability. Negative controls now reject swapped LUT pins/bits, wrong reset
priority, mux polarity, omitted/reversed links, overlapping/wrong config
addresses, missing assumptions/input hashes and invented execution credit.
No expected vector was regenerated from production Nodal lowering.

## Actual example and limits

The actual hand-authored fixture stores LUT INIT `A6D3`; ascending address output
is `1 1 0 0 1 0 1 1 0 1 1 0 0 1 0 1`. With FF=1 and reset value 0, config
`1A6D3` maps to frame0 `1A6D3000`. EN=0/SR=1 holds q; EN=1/SR=1 on a rising
UserCLK loads the reset value. This is a reviewed reference contract and local
metadata/vector arithmetic check, not observed RTL behavior.

FABulous is pinned to `d2fc49dade524a4f78062a3a38b213e9c08d6b04` (v2.0.0).
The source LUT/register is not relabeled generated output. Its future generated
switch/config-memory/tile/fabric wrapper and actual simulation/formal witnesses
belong to FND-06. Static frame-memory setup is explicitly not runtime-loader
qualification. Carry, asynchronous reset, analog/pass-switch, multiclock and
physical/timing cases are outside this matched subset with named later owners.

The metadata checker validates this reviewed corpus, not arbitrary hostile
exchange JSON; FND-05 owns that parser and input-size/malformed-file contract.
No production Scala DSL, Rust architecture compiler, device database, generated
Nodal fabric, CAD, PPA, silicon or all-configuration proof is claimed.

This increment does not affect generated Verilog.
