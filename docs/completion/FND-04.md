# FND-04 — Foundational types and semantic validation

The core implementation is locally qualified and integrated into `dev`. This
closure proposes accepted [Foundation checklist](../roadmap/tracks/00-foundation.md)
status for all 16 leaves (24 nodes). Final documentation qualification and closure
integration remain separate coordinator obligations; no future commit is asserted.

The acceptance receipt profile is `structural-selection/1`. The unchanged API and
example call this `structural-selection`; the independent fixture inventory uses
its narrower corpus label `structural-types-direct-alias-u64/1`. Those historical
labels are not rewritten or treated as wire-schema versions. The tested roadmap
has no profile annotation; closure changes only its checkboxes and Evidence line.

## Exact source, integration and retained evidence

| Identity | Value |
| --- | --- |
| Tested implementation | `bc6e3264d5ee8489b8a606d9e7de568ad0f99a7e` |
| Tested tree | `44474e04e37de6cfa293e5a580685edc1e3c1c16` |
| Integration base | `d4948096e16e7299ef02a90363f90491ebe9790d` |
| Actual implementation merge | [PR #7](https://github.com/pysolvesemi/nodal-fpga/pull/7), `f9fdd8cf8363104bfa0f4063fd851016eb462bec` |
| Actual merge parents | Integration base, then tested implementation, in that order |
| Actual merge tree | `44474e04e37de6cfa293e5a580685edc1e3c1c16`, identical to tested tree |
| Remote qualification | Not run under explicit user instruction: local tests before increments; final combined Foundation CI at FND-08 |
| Post-merge CI | Skipped, `user-directed-local-qualification-identical-tree-merge`; zero runs reported by coordinator |

The [source record](evidence/fnd-04/source.json) and
[after record](evidence/fnd-04/source-after.json) are byte-identical and record
`dirty=false`. The retained runner checks exact HEAD and clean tracked/untracked
status before and after execution. Local Git objects establish the merge tree and
ordered parents. The integration coordinator separately verified remote identity,
zero candidate/merge-head workflow runs, disabled protection and empty required
contexts. This author audit does not independently authenticate remote state.
No protection was bypassed. FND-08 remains open; historical evidence is unchanged.

The [machine-readable receipt](FND-04.evidence.json) maps every actual leaf to
observations. The [index](evidence/fnd-04/index.json) inventories 49 verbatim raw
files/runner captures, original and retained paths, SHA-256 values, 35 tested
source/tool/workflow identities, commands, limits and actual measurements.
Unsupported evidence extensions gain `.txt` without changing bytes. Retained
probe and runner source text is inert evidence, not installed executable tooling.
Existing capture manifests retain original names, resolved through the index.

## Exact-head local commands and results

The coordinator ran the [retained qualification script](evidence/fnd-04/qualify-fnd04.sh.txt)
with the tested commit above, `source .cache/toolchains/env.sh` and `TZ=UTC`:

| Command | Actual result |
| --- | --- |
| `./nf check contracts` | [195 tests](evidence/fnd-04/contracts.log): 60 bootstrap, 43 Foundation, 92 roadmap; 49 documentation files and 231 links at tested source |
| `./nf check rust` | [49 unit/integration tests and 4 doctests](evidence/fnd-04/rust.log): 40 ArchIR, 8 types integration, 1 types unit; 3 compile-fail types doctests and 1 bootstrap doctest; fmt, warning-denying clippy, locked/offline metadata passed |
| `./nf check scala` | [Format, clean compile and actual version checks](evidence/fnd-04/scala.log) passed |
| `./nf reproduce rust` | [Two clean Rust build repetitions](evidence/fnd-04/reproduce-rust.log) retained identity/model output; not fresh-container or saved-package-runtime qualification |
| Five selected FND-03 unittest controls | [Passed](evidence/fnd-04/receipt-controls.log): hand-authored negative evidence, explicit expected candidate, authoritative profile, stale raw source and dirty execution |
| Build model and integration-test executable | [Model build](evidence/fnd-04/model-build.log), [Cargo artifact records](evidence/fnd-04/test-build.jsonl.txt) and [stderr](evidence/fnd-04/test-build.stderr.txt) retained |
| Run prebuilt model twice | Byte-identical complete stdout, SHA-256 `1615356294a3728c68d2bb9fe76c296dfd5c4ecd3daa73340cdc76ccd4868bd2` |
| Run prebuilt bounded count/depth/partition test twice | Both passed; non-timing scale projections byte-identical, SHA-256 `c151341afef02fdd58babf954c003485e7e8367d90ffcc35411bb6e797bff948` |

The script retains [binary hashes](evidence/fnd-04/binaries.sha256.txt), direct
process timings, repeated outputs and clean source identities. Observed tools:
Python 3.12.14; Rust/Cargo 1.98.1, rustfmt 1.9.0-stable, clippy 0.1.98; Scala 3.3.8,
sbt 1.12.11, Eclipse Adoptium Temurin 21.0.12.1+1-LTS. The index binds the tested
version-pin source plus the recorded launcher/JDK distribution checksums; it does
not invent tool-executable hashes at execution time.

The unchanged affected workflow is `.github/workflows/fnd-01-bootstrap.yml`,
SHA-256 `6cb05112e8ecc1c69ff6125ee71b270ac6dd4ea8786582ce6887f57c9d32f7f3`,
historically registered ID 367539769, jobs `contracts`, `rust`, `scala`, `required`,
no matrix. Local results are not remote CI; no run URL is fabricated.

## Contract and independent correctness evidence

The [public API contract](../development/core-api.md) is the supported/rejected-case
reference. `nf-types` has no dependencies; `nf-arch-ir` depends only on `nf-types`.
The separate bootstrap makes three packages, one internal edge and zero external
dependencies. Both new crates forbid unsafe. Checked nominal IDs, explicit
build/partition correspondence, `u64` units/ranges and 1–64-bit values make no
pointer, file-layout or memory-image ABI promise. Only x86_64 was executed.

ArchIR retains reusable templates, ordered interfaces, explicit references,
independent domain memberships and source provenance. Containment cycles reject;
intentional routing cycles may be legal. Direct-to-owner aliases require exact
owner/type or storage/slice/width/domain agreement; chains, partial aliases and
undeclared overlap reject. One canonical resource belongs to at most one mode
group. Complete selections name every instantiated group and every active storage
class, with agreeing redundant active writes and no inferred defaults. These are
structural/selection constraints, not primitive or circuit execution.

The unchanged [independent agent review](../implementation/fnd-04-independent-review.md)
records repaired findings and no unresolved blocker. Its 28 reviewed source hashes
match the tested commit. Review and external probes were performed on uncommitted
source and remain **content-hash-bound development review**, never clean-source
execution observations in this receipt. Retained [probe captures](evidence/fnd-04/development-review/capture.sha256.txt)
include source, scripts, red/green top-level key output, measurements and metadata.
The report's source manifest and all raw capture hashes were rechecked unchanged.

The [hand-authored oracle](../../verify/fixtures/fnd-04/expectations.md) predates
production implementation, SHA-256
`b33d80f70272393474ec8583c479acdd488de39d43ee039ca2ab94a0aebd1581`.
The [fixture inventory](../../verify/fixtures/fnd-04/inventory.json) describes:
121 arithmetic pairs checked with wider arithmetic; 81 intervals/all 6,561 pairs;
2,304 sharing selections (172 accepted, 516 conflicts, 1,616 inactive writes);
64 independent owner-overlap pairs; 128 single-defect mutations, seed
`0xF0041D3E5EED`; and 6,000 work-budget/permutation comparisons. Diagnostic tests
check category, stage, scoped identity and literal provenance, not arbitrary errors.

Review-driven regressions cover cross-scope/alias competing drivers, repeated
resource mode membership, whole-key bounds, actual containment-cycle witnesses,
nominal key collisions, unknown selected field identity, finite-domain ordering,
and deterministic diagnostic/work exhaustion. The architecture-level Pip key
boundary accepts exactly 36 bytes and rejects limit 35 under declaration
permutation; the unchanged external limit-30 probe retains its red/green repair.

FND-02 interactions select ASM-0003/0004 sharing and modes, ASM-0008 bounds/identity,
ASM-0009/0010 topology/ownership and ASM-0011 typed domain membership. ASM-0002 is
only unsupported-mode rejection here. This risk-based selection avoids an
all-features Cartesian product; LUT/register behavior and FND-06 independent
hardware execution are not claimed. The five FND-03 receipt controls are separately
executed qualification controls, not Rust semantic tests.

## Complete acceptance mapping

| Leaf | Evidence |
| --- | --- |
| FND-04.a.1 | Checked public IDs, integer/unit bounds and provenance; Rust arithmetic/identity/interval fixtures |
| FND-04.a.2 | Public structured diagnostics and literal source-aware tests; dependency guard and review |
| FND-04.b.1 | Portable typed keys versus explicit build/partition-local dense identities and total one-to-one correspondence |
| FND-04.b.2 | Checked table/count/offset/length conversions, `u32::MAX` with `2^32` count, huge scalar ranges without giant allocation |
| FND-04.c.1 | Borrowed ArchIR resources/interfaces/hierarchy/modes/config declarations, API contract and actual model |
| FND-04.c.2 | Executed reference/type/ownership/sharing/selection tests and retained literal provenance |
| FND-04.d.1 | Independent valid/boundary arithmetic, graph, mode and generated single-defect tests |
| FND-04.d.2 | Independent bitset/sharing oracle, malformed ownership rejection and deterministic full diagnostics |
| FND-04.d.3 | Selected FND-02 semantic interactions and five separately executed FND-03 receipt controls above |
| FND-04.f.1 | Hand-stated preproduction oracle, public-API tests and wider arithmetic/tiny-bitset cross-checks |
| FND-04.f.2 | Explicit structural-selection acceptance and later DB/CFG/RTL/FND-05/06 boundaries |
| FND-04.g.1 | Independent module/dependency/complexity audit; borrowed model, streamed traversal, bounded transient state, preserved provenance |
| FND-04.g.2 | Executed count/depth/partition axes, repeat output equality, actual measured size/time and budget-permutation regressions |
| FND-04.e.1 | Published API, exact source/raw identities, reproduction script and actual full model/rejection stdout below |
| FND-04.e.2 | Clean exact-source contracts/Rust/Scala/repeats/receipt controls, independent review and actual identical-tree merge; CI disposition follows explicit user cadence |
| FND-04.e.3 | All 16 leaves mapped, FND-03 already accepted, closure-only checkbox changes and explicit limits; final closure publication/qualification/integration is coordinator-owned |

## Boundedness, scale and determinism

Default limits are also implementation ceilings: 100,000 declarations, 200,000
references, 16,384 entries per collection, depth 64, component/key bytes 128/4,096,
provenance bytes 1,024, 128 diagnostics and 1,000,000 charged work units. Lower
positive limits are supported; zero or raised ceilings reject. Limit exhaustion
returns one deterministic rejection, not an arbitrary partial diagnostic prefix.
Conservative logical work is not an instruction/time quota; input admission,
external correspondence collection sizes and process quotas remain caller duties.

The [first](evidence/fnd-04/scale-1.log) and [second](evidence/fnd-04/scale-2.log)
prebuilt debug runs vary instances 1/16/256/4,096, depth 1/8/32/64 (65 rejects), and
partitions 1/2/4. All instance cases retain one template. At 4,096 instances, shallow
instance-vector capacity is 819,200 bytes and name payload 31,658 bytes; first-run
architecture validation took 16,844,274 ns and selection 52,682,464 ns, with
4,106 declaration entries, 4,099 references and 209,839 work units. Depth 64 took
1,859,336 ns/36,886 work units. Seven explicit links cross partitions 0/7/7 times
for 1/2/4 partitions. Whole scale-test processes took 0.110 and 0.097 seconds;
model processes each took 0.002 seconds. Compilation is excluded.

Capacity/name bytes omit other allocations and allocator overhead; these qualified
runs did not measure peak RSS. Separately, the reviewer's
[development probe](evidence/fnd-04/development-review/probe-measurements.json)
measured 0.049886967001 seconds and 10,496 KiB peak RSS for the entire prebuilt
consumer. Its compact fanout input has 11 templates and 320 child declarations
(336 accounted entries); the hypothetical 1,162,219,258,676,257 occurrences are
not materialized or credited as validated. It rejects at the 1,000,000 work cap.
All measurements are single-machine observations, not production thresholds.

The reviewer found the split into bounds, references, declarations, connections
and selection coherent. No parallel model or generic optimization framework was
needed. Instance traversal remains work-bearing and bounded; it is not zero-cost
hierarchy expansion. Canonical transient traversal preserves keyed declaration
permutation invariance without rewriting stored interface or mux order. Repeated
renderer/stable-projection equality is not FND-05 semantic canonicalization.

## Actual model and rejected selection

Actual frontend: Rust builder. The complete [retained stdout](evidence/fnd-04/model-1.stdout.txt)
is identical on both qualified runs:

```text
nodal-fpga/arch-ir/1
profile=structural-selection
templates=1 instances=3 connections=2
instance=t0 template=tile partition=0 mode=normal setting=0
instance=t1 template=tile partition=0 mode=alternate setting=1
instance=t2 template=tile partition=0 mode=normal setting=2
link=edge0 source=t0/cell.O destination=t1/cell.I
link=edge1 source=t1/cell.O destination=t2/cell.I
selection=valid
rejected=value
stage=selection namespace=example scope=t1 field=setting
primary=selection-input:61..62 actual=3
related=architecture-input:40..41
message=feature value is outside its width or legal domain
This increment does not affect generated Verilog.
```

No Scala exchange, serializer, production DeviceDB, physical allocation, loader,
RTL simulation/formal, fabric equivalence, timing, power, PPA, board or PDK result
is implied. Typed clock/power/configuration/placement/routing memberships do not
prove CDC, isolation or crossing safety. Byte spans check numerical bounds against
a caller-declared length, not source-file existence or UTF-8 slicing boundaries.

## Closure boundary and raw whitespace

This closure changes only this report, receipt, retained evidence, the explicitly
labelled [author audit](../implementation/fnd-04-closure-local-review.md), and FND-04
checkbox/Evidence lines. Tested implementation, tests, API, review, checkpoint,
workflow and requirement/profile annotations remain unchanged. The coordinator
must verify the actual published closure candidate with the narrow source anchor,
rerun affected document/contracts checks and verify its actual merge. Worktree
checks do not invent that future commit or relabel closure execution as tested-source
execution. The independent review remains the original agent's source review;
the closure author's audit is not independent approval.

The verbatim JVM `scala.log` has trailing spaces on lines 6 (`java.class.path`)
and 36 (`line.separator`). They and their original SHA-256 are preserved. The two raw scale logs each also retain a blank line at EOF. An
unrestricted staged whitespace check therefore reports four warnings (two trailing
spaces, two blank-at-EOF) and is not a pass. The separate staged authored-file check covers the report, receipt,
index, author audit and roadmap; raw captures are excluded only from that scoped
check. All retained evidence bytes are checked separately against their originals.

This increment does not affect generated Verilog.
