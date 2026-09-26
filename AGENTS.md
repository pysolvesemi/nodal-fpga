# Nodal-FPGA project instructions

These instructions apply to the whole repository. A more specific `AGENTS.md`
may narrow them for its subtree. A direct user instruction for the current task
takes precedence. Read [the roadmap index](docs/roadmap/README.md),
[progress rules](docs/roadmap/progress.md), the selected track,
[architecture](docs/architecture.md), [verification policy](docs/verification.md)
and its linked ADRs before implementing or completing an increment.

## Branch and scope

- Planning and development target `dev`; do not modify, merge into, or force-update `main` without explicit authorization.
- A roadmap entry is not permission to implement every track or to tape out, purchase IP, publish releases, or access restricted PDK material.
- Preserve existing changes and check the current remote head before committing. Never replace concurrent work with a stale tree.

## Progress

- Each increment is a parent Markdown checkbox; independently completable tasks are nested checkboxes with stable IDs.
- Mark a sub-item `[x]` only when its own acceptance condition has evidence. Other sub-items and the parent remain `[ ]` while incomplete.
- A parent becomes `[x]` only after every required descendant is `[x]`, dependencies are complete, and final-head verification and completion evidence are recorded.
- All non-Foundation tracks are blocked by `FND-08`. Foundation bootstraps its own tests and must not depend on a blocked track.
- Documentation, generated stubs, a passing example, a draft PR, and historical chat claims are not proof of implementation completion.
- Never silently remove, waive, or weaken a required sub-item to close an increment. Reopen affected items when a regression invalidates evidence.

The Foundation track expands existing obligations into numeric descendants;
preserve its original IDs and the final `.e` closure gate. Its independent
validation and quality/scale groups supplement the existing work, not replace
it. Markdown in each owning track remains the authoritative editable status;
reports and future generated views must agree with it. Follow the
[Foundation acceptance rules](docs/roadmap/tracks/00-foundation.md#foundation-checklist-and-acceptance-rules)
for applicability and independently staged validation.

## Ownership

Reusable engine code must not depend on concrete device libraries, Scala, MLIR, nextpnr internals, or proprietary PDK files. Keep library generators, device definitions, external adapters, applications, and verification oracles separate. Do not turn `nodal-fpga` into the `nodal-eda` GUI or a second high-level Nodal compiler.

Follow `docs/adr/0001-optional-circt-backend.md`: CIRCT is an optional isolated adapter, not a core/default dependency. The ordinary Rust compiler toolchain is allowed; do not require a separately installed LLVM/MLIR/CIRCT SDK for default builds. Keep the focused emitter small and review alternatives before building a general HDL compiler. CIR proceed/adopt decisions are additional gates; dormant implementation checkboxes stay open. No selected backend may specialize the manufactured fabric to one test bitstream or bypass configuration-preservation verification.

## Bootstrap applicability

At adoption of this policy the repository contains planning documents, not an
implemented Rust/Scala workspace or CI suite. FND-01 owns the minimal executable
build/check/CI baseline; FND-03 owns roadmap-validator enforcement. Do not claim
these mechanisms exist because this file specifies them. Before qualification,
inspect live workflow availability, registration, triggers and job behavior.
An unavailable required route remains a precise blocker; it is not permission
to modify `main`, bypass restrictions, or claim local tests as remote CI.

Foundation validation uses only its implemented bootstrap capabilities. Follow
the [early baseline](docs/verification-early-baseline.md) and ADR 0001's separate
default-build, saved-package-runtime and Scala-authoring profiles. FND-06's
required independent reference runs stay in Foundation; later DSL/DB/RTL/CFG/
CAD/VER/PERF and optional CIR work must not become circular prerequisites.
Do not copy Nodal's mandatory MLIR pipeline or analog simulator gates into this
repository's default Rust architecture compiler.

## Pre-implementation increment readiness gate

Before modifying implementation source for an increment or sub-increment, audit
the proposed work against the live integration target. This gate establishes a
coherent scope and acceptance boundary before implementation; it is not
permission to weaken an increment or rewrite historical acceptance.

1. Refresh the integration target and read the applicable `AGENTS.md`, roadmap
   index/progress rules, complete parent/child checklist, linked plans and ADRs,
   predecessor evidence, open PR discussion, and live branch/ref state.
2. Inspect the relevant Scala frontend, exchange schemas, Rust types/ArchIR,
   device/configuration contracts, compiler/backend, adapters, tests, workflows,
   independent fixtures and known limitations.
   Determine what already exists, what is reusable, and which claimed
   dependencies or validation owners are real.
3. Classify every existing child obligation as required now, blocked by a named
   dependency, owned by a named later increment, explicitly optional, or
   genuinely non-applicable to the selected feature/profile. Record the
   rationale and the resulting acceptance limit; applicability review is not
   execution evidence.
4. Preserve stable IDs, original intent, parent state, historical evidence and
   required acceptance strength. Prefer correcting or clarifying an item under
   its existing ID. A genuinely non-applicable item should normally become an
   explicit applicability result with its rationale instead of disappearing.
   Never silently delete, waive, check, or defer required work merely to reduce
   the increment. Removing or narrowing an obligation requires an explicitly
   documented and approved roadmap amendment under
   [progress rules](docs/roadmap/progress.md#blockers-changes-and-regressions).
5. Add missing feature-specific obligations and correct inaccurate, duplicated
   or misplaced wording. Reuse established representations, infrastructure and
   validation owners; avoid fixture-specific exceptions, copied generic
   checklists, circular dependencies and unbounded interaction matrices.
6. For a new increment, create exactly one
   `increment/<increment-id>-<slug>` branch (for example,
   `increment/fnd-01-bootstrap`) from the refreshed `dev` integration target
   and one draft PR. For existing work, reuse its current branch and PR; do not
   create a replacement branch or parallel increment implicitly.
7. If the audit requires a checklist correction, publish that focused
   documentation update as the first branch commit with `[skip ci]`, create or
   update the draft PR/checkpoint, and verify the changed-file scope before
   implementation.
   Do not run CI merely for this authorized documentation-only scope commit. If
   no checklist edit is required, record the audit conclusion in the draft PR
   or durable checkpoint without creating an empty commit.
8. Start implementation only after the checklist, dependencies, implementation
   layers, rejection coverage, independent validation ownership and acceptance
   boundary are coherent. Keep the parent open until all required descendants
   and closure obligations are complete.

After the first durable increment commit and draft PR exist, create, re-enable
or update exactly one hourly continuation for that increment. Before targeted
CI, it tracks live refs, implementation progress, blockers and the durable
checkpoint, and may resume already-authorized work only when it will not compete
with an active worker. The same continuation transitions to CI monitoring after
the first targeted launch; never create a second monitor for the CI phase.

## Targeted CI before full CI

For every increment, sub-increment, repair and accepted-evidence closure, qualify
newly affected or repaired source with targeted CI before starting full CI.
Local tests are useful repair evidence, not a substitute for remote qualification.
Use the existing increment branch and PR against `dev` unless the task specifies
otherwise; do not start another increment or touch `main` implicitly.

1. Inspect the live target, candidate, PR and repository instructions. Publish a
   clean candidate with `[skip ci]` to prevent automatic broad push/PR CI during
   the targeted phase. Record the full candidate SHA, tree SHA and target SHA.
2. Determine the affected workflow set from changed source, tests, generated
   artifacts, manifests, toolchain pins, formal registries, source-review
   contracts and prior CI failures. Record workflow IDs, paths, definition
   hashes, required inputs, jobs and matrix lanes; names alone are not stable
   workflow identities. Include shared gates and affected predecessor coverage.
3. Confirm each workflow supports `workflow_dispatch`, is registered/dispatchable
   under GitHub's rules, and executes the intended checks for that event/ref.
   A successful dispatch cannot compensate for PR-only jobs silently skipping.
   Do not change the default branch or modify `main` to make dispatch available.
4. Launch each affected workflow on the exact candidate branch using the
   browserless route below. Do not duplicate queued, running or successful runs
   for the same workflow, head, inputs and qualification context. Verify the
   resulting workflow ID, event, ref, head and actual checkout/tree identity.
5. Treat a workflow as passing only after every applicable job and matrix lane
   succeeds. Enumerate all run, latest-attempt job, check and status pages, and
   inspect actual logs/artifacts. Missing lanes, zero-job greens, pending work,
   cancellations, timeouts, skipped applicable jobs and old-head successes are
   not passing evidence. Record legitimate non-applicable skips without giving
   them test credit. A prospective test-merge SHA is not an actual merge.
6. After the first targeted launch, confirm the increment's single hourly
   continuation is enabled and transition it to CI monitoring as specified
   below. If it was genuinely unavailable during implementation, enable it now.
   Do not create a duplicate monitor. Repair failures and repeat only the
   affected targeted set until all targeted requirements pass on the intended
   candidate.
7. Only then start one applicable full-CI qualification on that exact candidate.
   Inventory the complete required workflow/job set, including bootstrap/core,
   schema, boundary and applicable increment/compatibility checks; a single
   general workflow is not the full set when other gates apply. Reuse qualifying
   same-head targeted runs and launch only missing full-phase requirements
   through approved repository triggers. Verify branch-protection-required
   contexts as well as test results.
8. If full CI fails, return to failed-first diagnosis and targeted repair rather
   than repeatedly relaunching the full matrix. After repair targeting is green,
   complete full qualification for the repaired head. Keep successful independent
   same-head runs; results from a preceding SHA do not qualify a new source head.

Rerunning an existing job preserves the original run's source SHA/ref. Use a
specific-job or failed-job rerun only for a diagnosed unchanged-source transient
failure. After any source, test, workflow, manifest, registry or review-contract
repair, publish the corrected commit and dispatch fresh runs on the new head.
New job IDs can represent copied successes from an earlier attempt; verify step
execution times and checkout identities instead of assuming a fresh rebuild.

Retain the narrow final-documentation source-anchor rule in
[progress rules](docs/roadmap/progress.md#evidence-locations): a documentation-only
final commit may reference the immediately preceding tested implementation only
when unchanged implementation is demonstrated and applicable documentation
checks pass. Record both identities and their distinct checks; do not relabel
old runs as new-head execution. Any implementation or qualification-contract
change needs fresh affected qualification. Merge-tree verification still uses
the actual final candidate, including its reviewed documentation.

Skip annotations suppress push/PR triggers, not explicit dispatches, and can
leave required PR contexts pending. They never authorize bypassing protection,
posting fabricated success statuses or counting absent checks as passed. Plan
an approved full-CI route that supplies every required context. If a required
workflow/context cannot be qualified through available authorized mechanisms,
record the precise blocker; do not silently run broad CI during targeted repair.

## Browserless targeted dispatch

Do not require the user to run GitHub CLI commands. Do not depend on a browser,
devbox or external MCP server when an authorized repository route is available.
Use this launch order:

1. Use a connected GitHub `workflow_dispatch` operation when it is exposed.
2. Otherwise use the standing authorization below for a narrowly scoped,
   increment-specific repository dispatcher. Tool unavailability is not a reason
   to ask again for this permission. This does not override a safety denial,
   repository restriction or genuinely missing access.

### Standing authorization for a repository dispatcher

The agent may publish and trigger a controller on a dedicated non-target,
non-feature control branch, starting from the current integration target. This
is a targeted-CI mechanism, not a source publisher or a separate increment.
The controller may use the runner's automatic `${{ github.token }}` to call the
Actions workflow-dispatch REST endpoint. No personal token is required.

The controller must:

- Have a unique branch and controller identity bound to the increment, PR,
  target and candidate SHA. Never repurpose one pinned to different work.
- Have an exact `push` branch filter and path filters limited to its own workflow
  and reviewed controller files. Request only `contents: read` and
  `actions: write`; no personal token, extracted credentials, browser session,
  default-branch change, feature-trigger modification or unrelated workflow edit.
- Carry an explicit allowlist for repository, PR, base ref/SHA, candidate
  ref/SHA/tree, workflow IDs/definition hashes and exact dispatch payloads/inputs.
  Validate live identities, original failure evidence when applicable and
  workflow definitions before dispatch; recheck identities between dispatches.
- Use reads for validation and permit only the allowlisted write operation
  `POST /repos/OWNER/REPO/actions/workflows/WORKFLOW_ID/dispatches`, normally
  with `{"ref":"CANDIDATE_BRANCH"}`. Reject unexpected inputs or destinations.
- Enumerate existing same-workflow, same-head dispatch runs, with matching
  inputs/context, and retain queued, running or successful runs. Record intent
  before POST, reconcile an uncertain response before retrying, and retain an
  auditable ledger of requested and observed runs without logging tokens.
- Fail closed on ref movement or unexpected data, use bounded timeouts and
  serialize dispatch attempts. Do not execute candidate-controlled source or
  arbitrary scripts in the controller's privileged job.
- Dispatch only the affected workflow set. It must not update source refs,
  rerun old heads, launch full CI, merge, cancel unrelated work, broaden triggers
  or alter protections. Keep controller commits off feature/integration branches.

Before publication, inspect every workflow that can match the controller push.
That push must launch only the intended controller; otherwise select a safe
isolated route or stop without dispatching. Do not assume another repository's
workflow names, branch filters or dispatch registrations apply here. An
`increment/...` branch can match broad development CI; a `ci-control/...` name
is only a candidate until all live trigger filters have been checked. The
controller-launch commit must NOT contain `[skip ci]`.

After launch, verify each resulting run has the allowlisted workflow ID, event
`workflow_dispatch`, candidate branch and exact head SHA. An actor such as
`github-actions[bot]` is expected with the job token; neither that actor nor a
green controller job is qualification evidence. Only the dispatched checks count.

## Hourly monitoring from increment start through closure

After the first durable increment commit and draft PR exist, create, re-enable
or update one hourly continuation for that increment using the available
scheduling tool (`RRULE:FREQ=HOURLY`). Do not create it before there is a durable
branch/PR state to inspect. Reuse the same task throughout implementation,
targeted repair, full CI, review, merge and accepted-evidence closure instead of
creating competing monitors. Confirm scheduling actually succeeded before
reporting it as enabled; report an unavailable scheduler without claiming
background work.

Keep the durable checkpoint in the repository or PR with enough source/evidence
references for another session to resume. A private or offline session must not
be the only owner of the current scope, progress or next safe action.

Before the first targeted launch, each execution must:

1. Read the live target, feature ref, draft PR, checklist and durable checkpoint.
   If another worker has an active, current checkpoint or is publishing, avoid
   competing writes and end quietly unless coordination is required.
2. Continue only the already-authorized increment scope. Work from the audited
   checklist, run proportional local checks, preserve clean ancestry, and
   publish focused `[skip ci]` checkpoints when remote evidence or handoff is
   needed. Do not launch targeted or full CI before a clean candidate and
   affected-workflow inventory are ready.
3. Record completed children only with their own deliverables and applicable
   validation. Keep blocked, deferred and non-applicable classifications
   explicit, preserve parent state, and report real blockers rather than
   deleting work or manufacturing progress.
4. Update the durable checkpoint with the current phase, refs, completed work,
   local evidence, remaining checklist items, blockers and next safe action.
   Stay quiet when nothing actionable changed.

After the first targeted launch, each execution must:

1. Read live refs, PR/review state, the durable increment checkpoint and every
   applicable latest-attempt workflow/job/check/status page. Avoid competing
   writes with another resume; recheck refs before publishing or merging.
2. Inspect actual failed logs and artifacts. Repair generic causes within the
   authorized increment, run proportional local checks, publish a clean
   `[skip ci]` checkpoint, and dispatch only failed/newly affected targeting on
   the repaired head. Diagnose infrastructure failures, including rate limits,
   before bounded retries; never disable provenance or tests to make them pass.
3. Advance from targeted to full CI only when all targeted requirements pass;
   return full-CI failures to the same repair loop. Leave unrelated and
   still-running jobs intact, and do not restart successful independent checks.
4. Once all required full-CI checks and review pass on the exact final head,
   perform the already-authorized verified merge with post-merge CI suppressed
   as described below. Continue monitoring until acceptance records, roadmap
   and any required closure PR are complete, not merely until code is merged.
5. Update the durable checkpoint with the current phase, repo/increment/PR,
   candidate/base/tree SHAs, affected/full workflow inventories, run/attempt IDs,
   failures, fixes, evidence, merge identity and remaining closure obligations.
   Stay quiet for unchanged queued/running work; report meaningful failures,
   published repairs, blockers, merge verification and accepted completion.

Disable the hourly task only after the increment is legitimately closed:
required final-head qualification and review are complete, the actual merge is
verified, required evidence/closure records are integrated, the authoritative
roadmap and completion report (plus any applicable manifest) agree, and the
completion demonstration/report is delivered.
Keep it enabled while any of these remain outstanding, unless the user explicitly
pauses/cancels it. A persistent blocker must be reported, not treated as closure;
do not hammer failing services or repeatedly publish the same checkpoint.

## Verified merge with post-merge CI suppressed

Suppress duplicate post-merge CI for fully qualified, identical-tree increment
and closure merges. This does not remove pre-merge qualification, review, source
integrity, dependency gates or accepted-evidence closure.

- Require all applicable targeted/full-CI checks and review on the final head.
  Re-read candidate and target SHAs, required contexts and mergeability just
  before merging. Target movement, unresolved review or a different prospective
  tree requires reconciliation and qualification, not an unchecked merge.
- Merge into `dev` using the repository-approved method, respecting any
  explicit user merge policy. Supply the verified `expected_head_sha` and put
  `[skip ci]` in the actual integration commit message. Do not import Nodal
  compiler-specific squash requirements, add an untested feature commit merely
  to carry the annotation, rewrite published history or bypass protections.
- Verify GitHub's actual merged flag, merge commit, parent/target relationship,
  final target ref, commit message and tree. The merge tree must equal the
  qualified candidate tree. Retain these identities with pre-merge CI evidence;
  a prospective PR test-merge SHA or a successful merge request is insufficient.
- Check that the intended post-merge push workflows were suppressed. Do not
  dispatch duplicate post-merge CI. `[skip ci]` does not suppress every event
  type; inspect live `pull_request_target`, `workflow_run` and other relevant
  triggers before relying on it. Do not globally disable workflows or cancel
  unrelated runs to manufacture suppression. Report unexpected triggered runs
  and inspect them without counting a failed applicable check as success.
- Record `post_merge_ci: skipped` with reason `qualified-identical-tree-merge`,
  actual merge/tree identities and references to the executed qualification.
  Never invent a post-merge run ID, report skipped checks as executed/passed, or
  reuse old-head results as if they ran on the merge commit.
- Preserve historical accepted-evidence records, hashes and genuine post-merge
  results. Do not rewrite them for this policy. New records must distinguish
  executed qualification from merge verification and suppression; an old schema
  that requires a new post-merge run needs an explicit reviewed schema evolution,
  not dummy run IDs or weakened historical guards.
- Keep any required separate evidence-closure PR in scope. Validate its changed
  checks/docs using targeted-first/full-CI qualification, review and the same
  verified merge/suppression rule. Complete the roadmap and manifest according
  to the progress rules; do not delete unfinished acceptance tasks to claim
  closure.

If merge-tree verification fails or a mandatory check remains unsatisfied, keep
the increment open and monitoring active. Diagnose and qualify the discrepancy;
never classify it as a successful CI-skipped merge.

## Failure handling and publication

Preserve authoritative source ancestry and evidence. Do not rebase, force-push
or rewrite published candidate history. An approved integration method is not
permission to relabel tests from other commits. Never weaken tests, simulations,
formal proofs, mutation controls, source reviews, timeouts or workflow matrices
merely to obtain a pass.

For a user-authorized documentation-only instruction/roadmap update with CI
explicitly waived, use the existing requested branch and `[skip ci]`; do not
create a new branch, PR, controller or monitor merely to exercise these rules.
That exception is not a waiver for implementation changes or increment-closure
gates. Review links, stable IDs, dependencies and state/evidence consistency
locally without claiming hardware or implementation tests.

## Standing increment completion rule

Whenever an increment or sub-increment is completed and marked `[x]`, follow
[the completion/evidence rules](docs/roadmap/progress.md#evidence-locations).
Record the source commit/tree, tool/device/configuration hashes, commands,
results, limitations and immutable evidence locations. Show actual executable
Scala architecture source and corresponding actual generated Verilog when
applicable; distinguish fabric RTL, externally generated reference RTL and
mapped customer RTL. Identify the backend, source/output paths and generation
commands. Never present illustrative pseudocode or a test-status summary as the
generated-output demonstration.

If Scala is not involved, identify the actual frontend. A schema-only increment
may show its actual IR/database diff. When an increment does not affect Verilog,
retain the project's required statement:

> This increment does not affect generated Verilog.

Add a brief reason and an actual applicable example only when useful. This
includes documentation-only increments and does not waive implementation,
verification, review or integration requirements.

## GitHub CI mechanics references

- [Workflow dispatch and job-token triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [Dispatch event requirements](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch)
- [Rerun source identity](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
- [Commit-message skip annotations](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)
