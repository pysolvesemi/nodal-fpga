# FND-03 independent parser and progress review

Review date: 2026-10-15. Reviewer: independent FND-03 validation reviewer.
Scope: the written progress/ownership contract, hand-authored parser and graph
expectations, malformed-input diagnostic controls, bounded traversal behavior,
evidence/path/profile binding, documentation-source anchors and source review
of the document validator. These are local software checks;
this report does not qualify HDL generation, simulation, formal proof, devices,
physical implementation, or silicon.

The review started over commit `3ccf9ff8cd74f3dfc72feb463e9d4f69a289448b`,
tree `22318830ec41ee491fca574dfbd1962a7a659cbe`. Implementation and test changes
were still uncommitted. These identities are a review base, not a final tested
candidate or an integration claim. The coordinator owns publication, final
qualification, integration verification and acceptance-state changes.

## Authority and architecture

Read the repository instructions, roadmap index/progress rules, complete FND-03
checklist and Foundation applicability rules, readiness checkpoint, architecture,
verification policy, ADRs 0001–0003, and predecessor completion reports.

- Owning-track Markdown is the editable status authority. A generated JSON view
  must be derived and checked against it; it cannot become a second status store.
- Explicit `Depends on:` declarations define edges. References to later evidence
  consumers in task descriptions or prose do not add reverse dependencies.
- Every non-Foundation increment inherits FND-08. A checked leaf under an open
  increment cannot bypass that dependency. Foundation must not acquire a reverse
  dependency on a blocked later track.
- Two-space hierarchy and stable dotted IDs establish immediate ownership.
  Numeric descendants need not appear in numeric order. Completed leaves remain
  complete under open ancestors when their own evidence remains valid.
- Every checked ancestor must have checked direct children; applying the same
  check at every level enforces the descendant rule. Regressions reopen affected
  ancestors and dependent claims without erasing unaffected work.
- Foundation retains its final direct `.e` closure child after its added review
  groups. Other existing tracks retain their actual final-child IDs, including
  DFT's `.f`; imposing `.e` everywhere would reject the authoritative plan.
- The Python tooling sits at the existing repository-document boundary. No Scala,
  Rust device model, optional compiler adapter, hardware generator or later-track
  implementation is needed to enforce this bounded document contract.

## Independently authored controls

The reviewer's [fixture corpus](../../tests/roadmap/fixtures/README.md) and
[test suite](../../tests/roadmap/test_independent.py) were written from the rules,
without generating expectations using the production parser or renderer.
Small positive cases have literal ID/state/parent/children/dependency objects.
A separate literal render contract checks IDs, source line numbers, ownership,
dependencies, schema fields and the trailing newline.

Positive cases cover:

- Partial nested completion and independently complete sibling/review groups.
- Valid structural closure and a reopened regression retaining an unaffected
  checked leaf.
- Numeric IDs displayed out of order, five descendant levels in the fixed
  fixture, and 192 levels in the bounded synthetic traversal test.
- Backtick and tilde fences, longer opening fences containing shorter runs,
  mismatched delimiters, closing-like text with a suffix, and indented examples.
  Ignored examples contain duplicate IDs, malformed states and unknown edges.
- Explicit dependencies plus inherited FND-08, with irrelevant future-consumer
  IDs in prose excluded from the graph.
- DFT's existing final `.f` closure, with a structurally complete FND-08 gate.
- Byte-identical output across repeat parsing and reversed document-map order.

Negative controls assert the intended stable `RoadmapError.code` and relevant
source location or identifier, rather than accepting an arbitrary exception:

| Condition | Expected diagnostic |
| --- | --- |
| Repeated leaf or increment across files | `RM-DUPLICATE-ID` |
| Foreign increment/numeric child, unindented descendant, nested increment | `RM-OWNERSHIP` |
| Odd spaces, skipped level, tab indentation | `RM-INDENT` |
| Malformed stable ID or unsupported checkbox glyph | `RM-ID` |
| Unknown declared dependency | `RM-DEPENDENCY` |
| Two-node cycle, self-cycle, inherited-FND-08 cycle | `RM-CYCLE` |
| Checked work with explicit or inherited open prerequisite | `RM-BLOCKED` |
| Checked root or intermediate group with open required descendants | `RM-ANCESTOR` |
| Missing/nonfinal Foundation closure or closure checked before work | `RM-CLOSURE` |
| Exceeded byte, node, or hierarchy bound | `RM-LIMIT` |
| Duplicate requirement or profile annotations | `RM-PROFILE` |

The synthetic checks use explicit structure-only mode. Their checked items have
no completion-evidence credit. Missing/stale evidence, execution-versus-review
applicability, and conflicting derived views are separately covered by the
coordinator's evidence suite, not asserted passed by these structural fixtures.
The later full-suite recheck is recorded separately below.

## Local results and traversal observations

Command:

```sh
python3 -m unittest discover -s tests/roadmap -p test_independent.py -v
```

Initial complete structural suite: 35 tests passed. The first test run exposed
three test-isolation/assertion errors, not production false passes: two fixtures
placed different track prefixes in the same file and failed ownership before
reaching the intended dependency gate; one expected an ID where the diagnostic
already supplied the exact source path/line. The fixtures were split by owning
track and that diagnostic assertion was corrected. No intended rejection was
weakened or accepted merely because another error occurred.

A structure-only pass over the actual roadmap accepted 17 owning files,
82 increments and 648 nodes, with 50 checked nodes. All 25 FND-03 nodes remained
open. This observation does not establish evidence qualification or close FND-03.

Bounded measurements used CPython 3.12.14 on Linux x86-64, with `tracemalloc`
enabled around parse, structural validation and render. They are single-run
local observations, not performance thresholds, process RSS, or production-scale
claims. The measured validator bytes had SHA-256
`2ea21048ccbbc55a7f3adf70043c36ca43bc52dc57e85ffe06769e5f28354be1`.

| Input | Input bytes | Nodes / increments | Elapsed with tracing | Peak traced Python allocation | Render bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Explicit dependency chain | 243,996 | 6,000 / 2,000 | 0.660977 s | 11,680,580 B | 1,283,255 |
| Nested hierarchy depth 192 | 78,995 | 194 / 1 | 0.018891 s | 604,520 B | 150,155 |

Both repeats were byte-identical. Observed render SHA-256 values:

- Chain: `bd9c1e28b351b2e903394347a8bb56dde9c4ea2c6e5135d5e4856c20a3b26b8d`
- Depth: `4d13818ed811cacd213ca9159c3f2a07eebd024a273c706741df60d6d4e68c53`

Reproduce these observations by using `BoundedTraversalTests.many_increments(2000)`
and `BoundedTraversalTests.nested_document(192)` from the test module; surround
`parse_documents`, `validate(..., require_evidence=False)` and `render` with
`time.perf_counter()` and `tracemalloc`, then compare a second render. These
arithmetic input generators do not produce the small fixture expectations.

Source review found an explicit line stack for parsing and iterative colour-DFS
for dependency cycles. Structural validation visits nodes/edges in bounded
passes rather than recursively rescanning every subtree. Rendering sorts keys
and stable IDs deliberately for deterministic output. It retains one string and
one object graph at this scale; there is no evidence that a streaming framework,
parallel traversal or another cache would justify its added complexity here.
Deep IDs and pretty JSON still have output-size costs; the stated byte/node/depth
limits are capabilities, not promises of constant memory.

## Review finding: duplicate obligation annotations, repaired

The initial annotation parser silently used the last repeated `requires` or
`profile` clause. A leaf containing both `requires: execution` and
`requires: delivery` could therefore downgrade its explicit execution obligation
without an ambiguity diagnostic. The coordinator repaired this by rejecting
duplicate clause keys across all annotations on the same node with `RM-PROFILE`,
rather than inventing precedence. Four independently authored rejection fixtures
now cover repeated requirements and profiles within one comment and across
comments; an additional positive control accepts distinct requirement/profile
clauses and verifies their exact parsed values. All five pass.

The first-stage independent recheck ran:

```sh
python3 -m unittest discover -s tests/roadmap -p 'test_*.py' -v
```

All 63 tests passed: 40 independent parser/graph/bounds controls plus 23
coordinator-authored evidence tests. The latter suite was also read during this
review: it uses temporary actual Git commits/merges and retained synthetic
source records, with literal malformed-evidence cases. Recheck includes missing
and stale evidence/source identities, dirty executions, incorrect report/profile
bindings, not-run/skipped/N/A/review substitutions, unsafe paths, duplicate JSON
keys, premature or unintegrated closure, and a conflicting generated status view.

A direct full-evidence `roadmap.check` pass accepted the current real roadmap
with 82 increments, 648 nodes, two checked increments and 50 checked nodes.
Its derived-view digest was
`491b806332efee68404103d7824eaa88758546c4ba99aaa5b87a5e3bbe5f46ab`.
FND-01 retains executed CI; FND-02 retains explicitly not-run CI. No FND-03
checkbox was changed. `git diff --check` also passed.

At that recheck, SHA-256 identities were:

- Validator: `165e6929ef1db5ea8670c38f740ed09a63a098d655cb281d2c152b8b01d6e789`
- Independent test module: `f40cacc7798bd8bd0e04eb6ce00bb91ffd4dd4970b57b7453e9562bdfe9b2d71`

No unresolved blocking parser/graph review finding remains in this reviewed
scope. This disposition accepts the independently tested implementation behavior,
not final-head qualification, integration or completion of the parent increment.

## Supplemental evidence and source-anchor review

The coordinator requested a second independent pass over evidence path/type
handling, execution-source binding, inherited profiles and the documentation-only
source anchor. The additional controls share temporary-Git setup helpers from the
companion suite, but their mutations and expected diagnostics were authored by
this reviewer. They neither subclass nor rerun the helper's test inventory.
No real repository refs or completion records are modified by these fixtures.

### R2 — Open-ancestor profile scope

The initial evidence traversal skipped an open node before checking its profile.
An open increment/group could declare one profile while a checked descendant was
accepted using another profile if the leaf lacked its own annotation. The reviewer
reproduced that false pass. The repaired traversal carries the effective ancestor
profile to descendants and rejects conflicts. Independent root and intermediate-
group controls now reject with `RM-EVIDENCE-PROFILE`; a mismatching retained
execution-record profile is also explicitly checked.

### R3 — Evidence scalar/container and path handling

The reviewer reproduced acceptance of `null`/array execution commands, a boolean
format version, dictionary-valued observation artifact lists, and entirely
boolean context values. A NUL-containing artifact path raised an unstructured
`ValueError`. These did not establish meaningful execution or identity metadata.

Repairs require the declared scalar/container types and a nonempty string
command. Independent controls check all these values, empty/whitespace commands,
and a symlink cycle; invalid paths now use `RM-EVIDENCE-PATH`. This is bounded
metadata validation, not authentication of arbitrary log content or a guarantee
that any nonempty string truthfully describes an executed command.

### R4 — Documentation source-anchor bypasses

Three independently reproduced defects affected the narrow source-anchor check:

- Git rename detection returned only the destination after moving `code.py` to
  `docs/completion/payload.txt`. The path allowlist accepted an implementation
  removal as documentation-only. Source and destination must be checked with
  rename collapsing disabled.
- Annotated tag object IDs were accepted as source/candidate commit identities
  because Git peeled them during ancestry/diff operations. Both supplied objects
  must themselves be commits.
- A regular roadmap file changed to a symlink with identical stored blob bytes
  passed content normalization even though filesystem reading semantics changed.
  File type/mode changes require explicit rejection before the content exemption.

A later recheck found that the generic Git helper stripped leading whitespace
from NUL-delimited filenames. A literal path ` docs/completion/payload.txt`
outside the documentation directory was therefore misclassified as an allowed
path. The anchor must retain raw Git path bytes/text rather than trim them.

Five independent controls retain these reproducers, including a tag in each of
the source and candidate positions. All five repairs pass. The anchor now checks actual commit object types,
uses untrimmed NUL-delimited changed paths with rename collapsing disabled,
requires each path in at least one compared tree, rejects non-regular/executable
modes and compares untrimmed source blobs. The final extended-scope recheck is
recorded below.

### R5 — Ordinary merge identity

A single-parent empty commit directly after the tested source was accepted as
`integration.state: merged` when its tree matched and it was ancestral to HEAD.
That is not an ordinary source-parent merge. The current receipt explicitly
supports ordinary merges; it must require the actual two-parent relationship,
rather than silently accepting another integration method. An independently
added fully checked closure fixture retains this false-pass reproduction. The
repair now requires two distinct actual parents, with the tested source in the
feature-parent position; the regression control passes. Final source recheck
remains separate below.

### R6 — Derived-output symlink aliases

The final CLI integration added a writer allowlist intended to protect source
and evidence from derived output. The first implementation resolved both the
requested destination and its allowed roots. A symlink at the designated
`docs/roadmap/status.generated.json` pointing to a completion receipt therefore
made the forbidden target equal the resolved allowlisted target. The reviewer
reproduced actual receipt overwrite in a temporary fixture repository only.
Resolving a symlinked `artifacts` directory similarly broadened the allowed root.

Two independent controls require `RM-DERIVED-PATH` and unchanged receipt bytes
for these aliases. Allowed roots must be canonical paths under the repository
root without following the allowlist paths themselves; the requested destination
is resolved and compared against those fixed boundaries. Both controls pass
after repair and verify that receipt bytes remain unchanged. No actual project
artifact was overwritten during this review.

## Final extended-scope disposition and frozen-source recheck

The coordinator identified the repaired implementation as frozen for this review.
The reviewer read the final engine/CLI integration, report and evidence templates,
validator documentation, scale driver, companion tests and all new regressions.
No unresolved blocking finding remains in the reviewed document/evidence scope.
The implementation is ready for coordinator-owned final-source qualification
and publication; this report does not itself close the increment or verify a
future integration.

The final local recheck passed all 92 roadmap tests: 57 independently authored
controls and 35 companion evidence/anchor controls. `./nf roadmap` passed with
82 increments, 648 nodes, two accepted predecessor increments and 50 checked
nodes. All 25 FND-03 nodes remain open. `git diff --check` passed. The independent
reviewer did not dispatch CI, commit, publish, or merge. Coordinator-run Rust and
Scala checks are recorded separately rather than claimed as reviewer executions.

The receipt/template review confirms explicit source/tree/profile identities,
hashed report/artifacts, retained clean execution records, command/result and
applicability limits, assumptions/reference/correspondence IDs, mutations,
loading mode, coverage, reviewer identity, actual ordinary-merge identity, and
separate executed/not-run/skipped dispositions. Placeholders cannot serve as
actual commit/hash evidence. Current execution-source records may omit a profile
for historical compatibility; supplied profiles are checked, and authoritative
ancestor profiles still constrain completed work. This preserves old artifacts
without pretending an absent original field was recorded during the old run.

Additional final controls enforce explicit source expectations even for wholly
unchecked increments. CLI anchor requests validate the selected receipt before
using its source identity. Derived output is restricted to safe JSON destinations
under the canonical artifacts directory or the designated derived-view path.
Metadata consistency, Git-object/ancestry checks and artifact hashes do not
independently authenticate remote CI, certify prose semantics, or authorize a
new integration method. Those documented limits are accepted for this increment.

Reviewed SHA-256 identities after the final repairs:

| File | SHA-256 |
| --- | --- |
| `tools/roadmap.py` | `e97709a5926d7447374fa2a1df0ed31e469b214e7fa90968d6817c64edccb704` |
| `tools/nf.py` | `4fdf6871dfac233d1f0ff1742c0ee2d61d7b1ba4f76cc5015034ad17bda35330` |
| `tools/roadmap_scale.py` | `3eff494975b3dba8385fe440b85e1731739d11691d736da1f0571e9af05a3ffc` |
| `tests/roadmap/test_independent.py` | `fa8caa02c37aee5ee808e2f24de74489597c9fe0c5b85be85893f0702ae72e5f` |
| `tests/roadmap/test_evidence.py` | `8bea26309ba0cb4e2ab02ae31d3b7503123a94541db69ccdeb6367ee53441a60` |
| `docs/development/roadmap-validator.md` | `40f23f3840ecca44759ee8828edc72043e0a3b71956a4b16745b2ab9f267bb7f` |
| `docs/completion/templates/report.md` | `e580640232ba53f5a58ee3d7cca3aec75a5673ec4cd445a230ea899078f148b4` |
| `docs/completion/templates/evidence.json` | `1bdde166f83bcbfa66e9698b2c583f6e33325b478ca8d1fc06de38b4f189ae18` |

Final reproducible scale command:

```sh
python3 tools/roadmap_scale.py --increments 2000 --depth 192
```

The checked-in scale driver uses a different explicitly synthetic document text
and source-path label from the initial independent workload above. Its hashes
are therefore compared with its own repeats, not with that earlier corpus.
On the same CPython/platform, the final observations were:

| Input | Bytes | Nodes / increments | Traced elapsed | Peak traced allocation | Output bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chain | 215,604 | 6,000 / 2,000 | 0.483442 s | 11,358,496 B | 1,129,373 |
| Depth 192 | 79,178 | 194 / 1 | 0.015445 s | 595,272 B | 145,499 |

Both outputs matched two repeats byte-for-byte. Their SHA-256 values were:

- Chain: `8aa903db399549526ad295425a82c6a31ecae2637d55eea523bfc8b00e8ac9f0`
- Depth: `6e1d6d161e781fd46dccefec61d008aed4aee9043e54479587d08a86cf779fd5`

These measurements retain the single-machine/traced-allocation limitations
already stated. They give no hardware execution credit or production-scale claim.

## Retained limits

- This is a bounded roadmap Markdown subset, not a complete CommonMark engine.
  It deliberately treats fenced examples as non-status content.
- Structural agreement cannot establish that an artifact genuinely demonstrates
  a prose acceptance condition. Evidence provenance, source/profile applicability
  and independent review remain separate requirements.
- The small literal oracles avoid parser/renderer common-mode expected output.
  They do not exhaust every possible malformed document or coordinated malicious
  amendment. Stable IDs and required-scope changes still require reviewed policy.
- Bounded synthetic graphs establish traversal and deterministic-output behavior
  only. They do not measure compiler/device/P&R scale or import PERF obligations.
- Historical FND-01 remote-CI and FND-02 local-qualification evidence must retain
  their distinct actual claims. No local validator run becomes remote CI.
- No checklist state, branch, commit, remote ref, CI run or merge was changed by
  the independent reviewer.

This increment does not affect generated Verilog.
