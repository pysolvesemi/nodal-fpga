# Roadmap and completion-evidence validation

Run `./nf roadmap` or `./nf check contracts`. The latter includes the existing
bootstrap and Foundation contract checks plus every roadmap fixture. No HDL tool
is needed for these document checks; passing does not qualify hardware semantics.
The validator uses Python's standard library and the checkout's Git history.
The contracts CI checkout therefore fetches full history. A shallow clone with
missing source objects fails explicitly; no network fetch is hidden in validation.

## Authoritative status and supported Markdown

Each `docs/roadmap/tracks/*.md` owns one track prefix. Increment and descendant
IDs are unique and explicit; order never generates their identity. Use exactly
two spaces per nested checkbox level and `- [ ]` or `- [x]`. Dotted alphabetic
and positive-integer components must name their immediate parent. Uppercase `X`
is accepted. A declared depth limit is a supported boundary, not truncation.

Backtick/tilde fenced examples are ignored, including nested indentation, longer
opening fences, shorter delimiter runs and mismatched marker types. Only a same-
marker closing run at least as long, with no trailing content, closes a fence.
This is a bounded roadmap subset, not a general CommonMark implementation.

Every increment has exactly one `Depends on:` declaration. Only that declaration
creates explicit edges; prose about later consumers creates none. Every non-FND
increment also inherits FND-08. Unknown references and cycles fail before status
checks. Any checked descendant needs complete dependencies. Checked ancestors
need all direct children checked, recursively. The final direct child is closure;
Foundation specifically preserves its historical `.e` after review groups.
Existing DFT `.f` gates stay unchanged. Open ancestors can retain evidenced
checked children. Reopened regressions keep unaffected work while invalidated
ancestors and downstream claims must reopen.

Required actual-execution leaves carry `<!-- requires: execution -->`; a review
cannot substitute for execution. Other supported requirements are `delivery`
(default), `review`, and `artifact`. An optional `profile: name/version` clause
binds the node and descendants, including checked descendants under an open
ancestor. Duplicate/conflicting declarations fail. These annotations express the
existing obligations; removing them is a qualification-contract change requiring
review and new affected checks. They never waive a prose obligation.

## Evidence receipts, not a second task ledger

For any increment with checked work, `docs/completion/ID.evidence.json` maps
stable leaf IDs to source-bound observations. Its `docs/completion/ID.md` report links
the receipt. Every checked leaf needs evidence; a group aggregates descendants.
Checked explicit execution/review/artifact requirements also need that kind of
observation. There is no checkbox state in the receipt. Retained observations
for reopened items can remain historical, but cannot re-check Markdown.

### Retained receipts (version 1)

The [report template](../completion/templates/report.md) and adjacent
`evidence.json` template bind:

- Exact tested source commit/tree and declared profile
- A hashed report, artifacts and clean execution source record (`head`, `tree`,
  `dirty: false`, and preferably `profile`), retained with each execution
- Commands, tools and hashes, seeds, results, coverage and limitations
- Actual device/configuration/schema identities or explicit reasoned absence
- Assumption IDs, immutable reference/correspondence hashes, mutation outcomes,
  configuration-loading mode and actual applicable examples
- Agent/human review identity without claiming unperformed human approval
- Actual integration commit/tree/parents and separate CI/post-merge dispositions

Source commits/trees must exist and agree with the actual Git objects. Execution
source records must match; stale or dirty records cannot be relabelled. Artifacts
are SHA-256 checked. A merged receipt must identify a real source-parent merge
with exactly two distinct parents (tested source second), the same tested tree,
and already ancestral to current HEAD. A prospective PR
merge object or a successful request alone is insufficient. This v1 receipt
supports the project's ordinary source-parent merge method; a different approved
merge method needs an explicit reviewed contract evolution, not dummy parents.

A result of not-run, N/A, failed, skipped or timeout cannot satisfy a checked
obligation. Genuine applicability review is a `review` observation and cannot
satisfy a `requires: execution` node. Later required FND-06 receipts reference the
accepted FND-02 assumption/corpus identities; they do not overwrite FND-02's
historical not-run hardware claims. Historical FND-01 remote CI and FND-02 local
qualification are retained distinctly. Added sidecars describe their existing
reports/raw records and are not new historical execution.

Hashes and shape checks establish identity and consistency, not whether an
arbitrary log proves a prose requirement. Review remains necessary. The tool
cannot discover all semantic regressions from arbitrary code changes or validate
remote CI truth merely from a URL. Actual GitHub run/job/protection review stays
with qualification/integration; a local validator pass is never remote CI.

## Concise summary mode (version 2)

New receipts can explicitly select `format_version: 2` and
`evidence_mode: "summary"`. This changes publication form, not acceptance scope.
Version 1 remains validated with its original retained-artifact/source-record
requirements. Adding a mode to a v1 receipt, silently omitting raw records from
v1, or using an unknown mode/version fails. Do not migrate historical receipts
just to avoid their existing retention contract.

The v2 exact top-level keys are `format_version`, `evidence_mode`, `increment`,
`source`, `profile`, `report`, `artifacts`, `observations`, `items`, `context`,
`review`, `integration` and `ci`. Unknown fields and duplicate JSON keys fail.
The [literal test-only example](../../tests/roadmap/evidence_fixtures/summary.json)
shows every field, with placeholders replaced by real Git objects in tests.
It is not an accepted project receipt or a claim of project qualification.

Source remains an exact existing `{commit, tree}` pair. The hashed concise
report must name both identities and link its receipt. The artifact inventory
may consist of that report alone for execution/review summaries. An artifact
observation must instead reference actual hashed deliverables in the inventory;
the report itself cannot substitute for the deliverable being inspected.
Generated RTL and other required outputs remain real deliverables. Existing
artifact path, digest and byte bounds apply unchanged.

Every observation has exactly `source`, `profile`, `kind`, `result`, `observer`,
`summary` and `limitations`, plus its kind-specific fields below. All source and
profile values match the receipt. IDs are nonblank without surrounding
whitespace; use privacy-safe agent roles/IDs or actual human reviewer identities,
never fictitious human approval. Summaries state concrete observed outcomes.
Limitations are a nonblank string or nonempty list of nonblank strings, including
explicit reasoned non-applicability where appropriate.

- Execution adds `command`, `executed: true`, `dirty: false`, integer
  `exit_code: 0` and `checks`. Its result is `passed`. `checks` has exactly
  integer `required`, `executed`, `passed`, `failed`, `skipped`: the first three
  must be equal and positive, the last two zero. Booleans are not counts/status
  integers. Empty commands, zero checks, dirty/unverified sources, failures,
  skipped required checks and partial execution cannot close an obligation.
- A formatter/build/graph command or complete suite may count as one required
  check. Name its actual scope and meaningful subtest counts in `summary`;
  counting a suite as one cannot hide a missing required lane or skipped case.
  Passing negative controls mean that the verification harness asserted the
  intended diagnostic/status. `exit_code: 0` is the harness's status, not the
  expected nonzero child exit. An unrelated crash/timeout is not a pass.
- Review has result `accepted` and no extra fields. Artifact inspection has
  result `inspected` and adds `artifacts`, a nonempty unique list of actual
  hashed deliverables. Neither kind can replace required execution.

At least one execution must record actual applicable verification of the tested
source. This does not turn every delivered artifact or reviewed decision into
a test. `items` maps stable IDs to nonempty unique known observation IDs; every
checked obligation still requires its declared kind/profile. Partial work may
remain checked under open ancestors, but partial execution cannot satisfy a
checked execution obligation. `context` retains the v1 tool, schema, device,
configuration, seed, assumption/corpus/correspondence, mutation, loading,
coverage, limitation and example fields. No raw log, separate execution-source
file, hostname or private workspace path is required. Use reproducible
repository-relative commands or named environment wrappers, not private paths.

`review` has exactly `kind` (`agent` or `human`), `identity`, `authors`, `source`,
`result`, `observations`, `dimensions` and `limitations`. It must be accepted,
source-bound and identify a reviewer distinct from every nonblank, unique
implementation author. `observations` must cover every observation exactly
once, without unknown IDs. `dimensions` has exactly `architecture`,
`independence` and `quality`; each is `{result: "accepted", summary: "finding"}`.
All three need substantive findings and explicit limits, including source and
oracle independence, scope/ownership, unnecessary expansion/duplication and
applicable scale/compatibility concerns. A name or checked box alone is not a
review finding.

The independent reviewer must inspect actual local execution observations and
source state before accepting this attestation. Keep required raw observations
locally, without claiming repository retention or remote accessibility. The
validator checks structure, identities and consistency; it cannot authenticate
arbitrary claimed results, just as hashes of fabricated logs cannot. It never
executes commands taken from a receipt. Review, actual tests and remote CI
inspection remain necessary. An internally consistent forgery is not legitimate
acceptance evidence merely because the local validator cannot detect it.

`integration` is either `{state: "pending"}` or the same actual
`{state: "merged", commit, tree, parents}` source-parent merge identity as v1.
The actual two distinct parents, second-parent tested source, equal source/merge
tree and merge ancestry to HEAD are checked. Checking either the increment or
its final closure group requires the actual merge; a prospective merge fails.
`ci` retains the explicit qualification/reason/run and post-merge dispositions;
`not-run` never grants test credit or changes the applicable CI policy.
Neither post-merge execution nor verified suppression can be recorded while
integration is pending.

There is deliberately no candidate/self-commit field. This receipt binds the
tested implementation and actual source merge. Final documentation candidates
still require the narrow `--check-anchor`, actual documentation checks and
verified closure integration. Record their distinct commit/tree/check identities
in the PR or coordinator's integration summary after publication, without a
self-referential receipt or invented future commit. V2 validation alone does
not establish final-documentation-head qualification.

## Candidate freshness and the narrow documentation anchor

For an intended tested source, run:

```sh
./nf roadmap --expect-source FND-03=EXACT_TESTED_COMMIT
./nf roadmap --check-anchor FND-03=EXACT_FINAL_DOCUMENTATION_COMMIT
```

The first requires an exact receipt source match; absent expectations, immutable
historical receipts are not incorrectly compared with today's moving HEAD.
The second verifies source ancestry and that all subsequent differences are
completion/evidence documents, named checkpoint/review documents, or roadmap
checkbox/Evidence-line changes. Renames cannot hide removed code; tag identities and symlink/executable modes
are rejected. Code, workflows, normative docs, requirements,
profiles, dependency declarations and obligation text changes reject the source
anchor and require fresh affected qualification. This check operates on committed
identities, not dirty files, and does not itself execute documentation checks.
Run those checks on the final documentation candidate and record both identities.
A current implementation/qualification-contract change cannot use old green runs.

## Derived view and bounds

```sh
./nf roadmap --write-view artifacts/roadmap.json
./nf roadmap --check-view artifacts/roadmap.json
python3 tools/roadmap_scale.py --increments 2000 --depth 192
```

The destination directory must exist. Writing is restricted to JSON below
`artifacts/` or the designated `docs/roadmap/status.generated.json`; source tracks
and evidence cannot be overwritten by the renderer. Generated JSON is deterministic, sorted
and disposable. Never edit it for progress. `--check-view` rejects any conflict;
if `docs/roadmap/status.generated.json` exists it is always checked by the normal
validator. No derived file is required or checked in. The authoritative Markdown
alone controls status. Rendering does not include a timestamp or machine path.

Default bounds: 16 MiB Markdown, 100,000 nodes, depth 256; 4 MiB per evidence JSON
or report; 10,000 artifact paths, 128 MiB per artifact and 512 MiB total artifacts
per increment. Larger evidence should be split with reviewed index/limits rather
than silently skipped. Artifact hashing streams bounded chunks. This is local
project-document validation, not the FND-05 hostile exchange reader.

Parsing and graph traversal are O(input bytes + nodes + edges); deterministic
sorting adds O(nodes log nodes) output work. Evidence hashing is linear in
retained bytes, with bounded metadata and Git checks per accepted increment.
There is no recursive graph traversal or repeated whole-roadmap scan per receipt.
Scale observations use elapsed time and traced Python allocations, not process
RSS or production compiler/P&R performance. Small independent literal fixtures
supply the expected statuses; synthetic workload generation never defines their
expected results.

This increment does not affect generated Verilog.
