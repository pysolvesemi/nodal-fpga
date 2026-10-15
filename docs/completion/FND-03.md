# FND-03 — Nested progress and source-bound evidence

The document validator is qualified and integrated into `dev`. This evidence
closure records the actual local results, implementation integration and proposed
accepted [Foundation checklist](../roadmap/tracks/00-foundation.md) status. Its
final documentation checks and actual closure integration are separate coordinator
obligations; no future closure commit or merge identity is invented here.

The selected profile is `foundation-progress/1`, as already declared by the
qualified authoritative roadmap. The latest explicit user cadence requires local
tests before each increment merge, no pre/post-merge CI unless protection requires
it, and full combined Foundation CI at the end. FND-08 remains open.

## Exact source and implementation integration

| Identity | Value |
| --- | --- |
| Tested implementation | `10c8e7f1304bc2ea06ca789e116c9555a029e371` |
| Tested tree | `2508b015fd671b78105d39ef479db4177ef1b2f4` |
| Actual integration base | `8902cf29b104e27c66ffbbb58f566eddbe33c1f1` |
| Actual implementation merge | [PR #5](https://github.com/pysolvesemi/nodal-fpga/pull/5), `d928c0009119728d87a6ca25a8487739a784bb4e` |
| Actual merge parents | Integration base, then tested implementation, in that order |
| Actual merge tree | `2508b015fd671b78105d39ef479db4177ef1b2f4`, exactly equal to the tested tree |
| Remote CI | Not run under the explicit local-first cadence; no remote execution credit |
| Post-merge CI | `skipped`, reason `user-directed-local-qualification-identical-tree-merge`; actual merge message contains `[skip ci]`, zero merge-head workflow runs reported by the integration coordinator |

The [source record](evidence/fnd-03/source.json) was retained verbatim and records
`dirty=false`. The actual merge object is present in local ancestry, with the
verified parent order and tree above. The coordinator verified the remote merge
and absence of merge-head workflow runs; the local validator checks ancestry and
identity, not GitHub truth from a URL. No branch protections were changed or
bypassed. `main` was untouched by this increment.

The [evidence metadata](FND-03.evidence.json) maps all 17 leaves to observations
without storing another checkbox status. The [retained index](evidence/fnd-03/index.json)
binds raw-file hashes, source-file/corpus identities, commands, results and merge
metadata. Original FND-01 remote evidence and FND-02 local evidence remain intact.

## Commands and actual results

The coordinator ran the following checks on the clean tested source above, using
`source .cache/toolchains/env.sh` to select the locally installed pinned tools
and `export TZ=UTC` for the execution environment:

- `./nf identity`: exact clean source/tree and runner record
- `./nf check contracts`: [raw log](evidence/fnd-03/contracts.log), 20 bootstrap,
  43 Foundation and 92 roadmap/evidence tests passed; 43 documentation files and
  205 local links checked at the implementation source
- `./nf check rust`: [raw log](evidence/fnd-03/rust.log), format, warning-denying
  clippy, all-target tests, one passing doctest and locked/offline dependency
  metadata passed; bootstrap remains one dependency-free crate
- `./nf check scala`: [raw log](evidence/fnd-03/scala.log), format checks, clean
  compile and explicit Scala/sbt version observations passed
- `./nf roadmap --write-view artifacts/fnd03-qualified/roadmap.json` and
  `./nf roadmap --check-view artifacts/fnd03-qualified/roadmap.json`:
  [raw results](evidence/fnd-03/roadmap.log), actual roadmap accepted and the
  deterministic derived view matched
- `python3 tools/roadmap_scale.py --increments 2000 --depth 192`:
  [actual measurements](evidence/fnd-03/scale.json), two identical renders for
  each bounded workload
- `git diff --exit-code`: passed after qualification; the coordinator also
  verified the working tree was clean

Observed Python 3.12.14; Rust/Cargo 1.98.1, rustfmt 1.9.0-stable and clippy 0.1.98;
Scala 3.3.8, sbt 1.12.11 and Eclipse Adoptium Temurin 21.0.12.1+1-LTS. The existing
JDK/launcher checksums and tool pins are bound by the index. These local Rust and
Scala commands are build regressions, not a new isolated-container or saved-package
runtime claim. Final combined Foundation CI has not run.

The archived [roadmap JSON](evidence/fnd-03/roadmap.json) is the tested source's
historical snapshot: 82 increments, 648 nodes, two checked increments and 50
checked nodes. It intentionally predates this documentation closure's FND-03
checkbox changes; it is neither an editable ledger nor a claim of later-head
execution. Normal validation of this closure derives three checked increments
and 75 checked nodes from its current Markdown.

## Implemented behavior and independent review

The [validator contract](../development/roadmap-validator.md) describes the
supported Markdown subset and evidence format. Implementation remains in Python
repository tooling, with no new core/device/adapter dependency.

Parsing preserves explicit stable IDs and two-space ownership through numeric
nesting, ignores fenced examples and rejects duplicate/malformed IDs. Explicit
`Depends on:` edges plus inherited FND-08 determine eligibility; future-consumer
prose creates no reverse edges. Iterative cycle and ancestor checks preserve
partial progress while rejecting premature closure and checked blocked work.
Foundation retains its final `.e`; DFT's actual `.f` closure remains supported.

Evidence binds source/tree, clean execution records, declared/inherited profiles,
artifacts and review. N/A, not-run, failed, skipped, timeout and applicability-only
review cannot replace required execution. Derived-view conflicts and attempts to
overwrite source/evidence through direct or symlinked output paths fail. The
narrow documentation anchor rejects changed code, workflows, requirement/profile/
dependency/task text, hidden rename removals, tag objects and unsafe file modes.

[Independent review](../implementation/fnd-03-independent-review.md) is an agent
review, not claimed external human approval. Its frozen source hashes match the
qualified candidate. Independent expectations were hand-authored rather than
produced by the parser/renderer. The final 92 tests comprise 57 independent and
35 companion tests; exact rejection diagnostics are required rather than any
exception. Review exposed and repaired six classes of false acceptance, including
ambiguous annotations, inherited-profile/type/path weaknesses, source-anchor
rename/tag/mode/path handling, non-merge integration claims and derived-output
symlink aliasing. All reported regressions passed after repair.

## Acceptance mapping

| Required leaves | Observations and deliverables |
| --- | --- |
| a.1, a.2 | Parser implementation and contracts controls: fences, stable IDs, numeric nesting, ownership and duplicate rejection |
| b.1 | Contracts and review: explicit/inherited dependency edges, unknown references and cycles |
| b.2 | Contracts and review: checked ancestors, final closure, valid partial progress and reopened regression |
| b.3 | Contracts and review: evidence/source/profile binding, actual merge checks and sole Markdown authority |
| c.1, c.2 | Actual completion templates and reviewed schema: identities, commands, assumptions/reference/maps, mutations/load mode, review and distinct integration/CI dispositions |
| d.1–d.3 | Executed contracts suite with hand-authored positive/negative inputs and intended diagnostics, including stale source, N/A substitution and conflicting derived views |
| f.1 | Executed independently hand-authored expected status/dependency/render controls and retained review |
| f.2 | Reviewed document-only applicability; no HDL tool or fabric-behavior credit |
| g.1 | Reviewed linear parse/graph traversal, bounded evidence hashing, deterministic sorting and proportionate no-further-optimization decision |
| g.2 | Actual 6,000-node and depth-192 repeated scale observations |
| e.1 | Actual roadmap/view and full positive/negative fixture execution on the qualified source |
| e.2 | Exact clean-source contracts/Rust/Scala qualification, retained artifacts, independent review and verified implementation merge |
| e.3 | This evidence/checklist closure, complete leaf mapping and explicit enforcement limits; acceptance on `dev` requires the coordinator's separate final-document qualification and integration |

## Determinism, complexity and bounds

The exact-source chain workload used 215,604 input bytes, 2,000 increments and
6,000 nodes; parse/structural validation/render took 0.517603 seconds with
11,358,496 bytes peak traced Python allocation. Depth 192 used 79,178 input bytes
and 194 nodes; it took 0.015708 seconds with 595,272 bytes peak traced allocation.
Both outputs matched repeated renders. These are single-machine observations
with tracing overhead, not process RSS, thresholds or compiler/P&R scale claims.

Parsing and structural graph traversal are linear in input/nodes/edges; sorted
rendering adds ordering cost and evidence hashing scales with retained bytes.
There is no recursive graph walk or whole-roadmap rescan per receipt. Default
bounds are 16 MiB Markdown, 100,000 nodes, depth 256; 4 MiB per evidence JSON/report;
10,000 artifacts, 128 MiB per artifact and 512 MiB per increment. Further caching,
parallel traversal or a general compiler framework is unjustified at these bounds.

## Actual applicable example and limitations

The real `./nf roadmap` implementation-source output was:

```json
{"checked_increments": 2, "checked_nodes": 50, "derived_sha256": "491b806332efee68404103d7824eaa88758546c4ba99aaa5b87a5e3bbe5f46ab", "hardware_execution": "not-claimed", "increments": 82, "nodes": 648}
```

The actual [partial-progress fixture](../../tests/roadmap/fixtures/partial.md)
keeps FND-01.a open while FND-01.a.1 is checked; the independently authored
`test_literal_partial_state_ownership_and_dependencies` passed in the retained
contracts log. `test_reopened_regression_keeps_unaffected_progress` likewise
preserves unaffected completed work. These are document-validator behaviors,
not illustrative generated hardware.

No Scala architecture frontend or generated fabric output is involved; the
frontend here is Markdown/JSON consumed by Python. Device/configuration package,
hardware schema, configuration load mode and hardware assumption/correspondence
execution are inapplicable to this document feature. Its templates retain those
fields for later applicable increments. The FND-02 ledger/reference decisions
remain accepted contracts with required FND-06 hardware execution still not-run.

The validator checks shape, identity and declared applicability; it cannot prove
that arbitrary log text establishes a prose requirement, authenticate remote CI
from a URL, discover every semantic regression, or replace independent review.
It is a bounded local roadmap tool, not a full CommonMark engine or the FND-05
hostile-input exchange parser. The v1 integration receipt supports the current
ordinary two-parent merge method; other approved methods need explicit evolution.

This increment does not affect generated Verilog.

## Documentation closure boundary

This closure changes only completion evidence, this report, the implementation
checkpoint and authoritative checkbox/Evidence lines. Implementation, tests,
workflows, requirement/profile annotations and normative contracts remain exactly
at the tested source. The coordinator must run the final-document source-anchor
comparison and affected document/contracts checks on the actual published closure
candidate, review it, and verify its actual merge. Those later checks are recorded
separately and are not relabelled as execution on the implementation source above.

Closure whitespace checks distinguish authored source/document changes from
verbatim command output. The earlier unstaged `git diff --check` covered only
tracked unstaged changes and did not inspect the then-untracked closure files.
After staging, unrestricted `git diff --cached --check` reports exactly two
trailing-whitespace warnings in retained `scala.log`: line 6 (`java.class.path`)
and line 36 (`line.separator`). These are benign raw JVM-property capture bytes;
the original log and its SHA-256 remain unchanged. The scoped authored-file check
`git diff --cached --check -- . ':!docs/completion/evidence/fnd-03/*.log'`
passes. This exception preserves raw evidence and does not relax source, test or
validator requirements; the unrestricted check is not claimed to pass.
