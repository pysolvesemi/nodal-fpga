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
stable leaf IDs to retained observations. Its `docs/completion/ID.md` report links
the receipt. Every checked leaf needs evidence; a group aggregates descendants.
Checked explicit execution/review/artifact requirements also need that kind of
observation. There is no checkbox state in the receipt. Retained observations
for reopened items can remain historical, but cannot re-check Markdown.

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
