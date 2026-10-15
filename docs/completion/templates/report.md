# Completion-report template

Copy this outline to `docs/completion/ID.md` only when preparing actual evidence.
The adjacent `evidence.json` is a schema-shape example with explicit placeholders;
it deliberately cannot validate until replaced with real identities and results.
Never use zero/dummy hashes, invented run IDs, or a prospective PR test merge.
Do not mark the increment closed while final review/integration remains pending.

## Scope and applicability

Name the increment, profile/version, implemented behavior and explicit limits.
List each required stable leaf and its own observation references. Identify
required-now, later-owned, blocked, optional and genuine applicability-review
results without turning absent required execution into an N/A pass.

## Source and immutable artifacts

Record full tested commit/tree, target/base, artifact paths and SHA-256, actual
commands, exact tool versions/build hashes, device/configuration/package hashes,
schema versions, options, seeds/workers, outcomes, coverage denominators and limits.
Link the matching `ID.evidence.json` receipt using an ordinary relative link.
Retain each execution's original clean source record and output/logs. Do not
rewrite it to look as if execution occurred on a later documentation candidate.

## Independent evidence and assumptions

Name assumption IDs and ledger revision/hash; reference-corpus source/input/output
hashes; total resource/pin/config correspondence hash; independent oracle origin;
formal scope/depth/solver/assumptions; simulation scope; cover witnesses; each
mutation's intended diagnostic and actual outcome. State exact loading mode
(static setup, unit shortcut, real loader, etc.) and qualify it accordingly.
An unperformed stage is explicitly not-run, never a successful skipped execution.

## Actual example

Show executable Scala source and actual generated Nodal fabric Verilog when
applicable, with source/output paths, commands, backend and hashes. Distinguish
fabric output from external reference RTL and mapped customer RTL. For a schema
increment show its real input/canonical output. Name the actual frontend if Scala
is absent. For a no-RTL increment retain the exact required statement:

This increment does not affect generated Verilog.

Explain why; do not invent a hardware example for a document validator.

## Review, integration and CI disposition

Name the actual reviewer/review artifact, findings and fixes; distinguish agent
review from external human approval. Record final tested source and any narrow
final-documentation anchor comparison, final documentation checks, actual
integration commit/tree/parents and repository/PR. Verify ancestry and tree
identity against the real target; record remaining blockers honestly.

Separate executed CI run/job/attempt and artifact identities from local checks.
For current local-first cadence say remote CI is not-run/deferred and identify
the user-directed final combined Foundation gate. Preserve older remote evidence.
Record post-merge executed results, verified identical-tree suppression with its
reason, or pending integration. Never invent a post-merge run for a skipped job.

## Determinism, scale and remaining work

Record repeated inputs/outputs and digest comparisons, measured elapsed/memory
scope, platform, bounded workload limits, compatibility, reviewed complexity and
why further optimization is or is not justified. State all unresolved limits and
later owners. A reference fixture is not production hardware qualification.
