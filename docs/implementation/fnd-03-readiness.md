# FND-03 readiness audit and checkpoint

Integration target: `8902cf29b104e27c66ffbbb58f566eddbe33c1f1` (`dev`).
FND-01 and FND-02 are accepted with reports and verified integration. FND-03
through FND-08 remain open. One increment branch: `increment/fnd-03-progress`.
Read AGENTS.md, roadmap index/progress, complete Foundation checklist,
architecture, verification, ADRs and predecessor reports. No checklist amendment
is required; every FND-03 leaf is required now.

## Existing capability and acceptance boundary

Reuse Python bootstrap tooling and documentation validation. The existing
FND-02 checker validates only its reviewed contract corpus; it is not a roadmap
parser. There is no current executable nested-progress/evidence enforcement.
Do not add hardware-generation or blocked-track dependencies.

Required now: parse two-space hierarchical Markdown checkbox IDs and ignore
fenced examples; validate unique ownership/IDs, indentation, dependencies,
cycles, global FND-08 inheritance, parent/descendant and final-closure states;
validate linked evidence and declared source/profile applicability. Preserve
partial progress and reopened regression semantics. Markdown remains the sole
editable status authority; any generated view is a deterministic derivative.

Add completion templates with exact source/tree/artifact/tool identities,
commands/results, profile/assumption/reference/correspondence IDs, mutations,
loading mode, review and actual merge/post-merge disposition. Preserve historical
FND-01 remote-CI evidence and FND-02 user-authorized local evidence distinctly.
Do not invent executed runs or rewrite accepted history to fit a new schema.

Independent tests must include partial/open, valid closure, reopened regression,
fences, actual Foundation numeric nesting, duplicate IDs, bad nesting,
missing/stale evidence, invalid checked ancestors, unknown dependencies and
cycles. Reject attempts to substitute a non-applicability decision for required
execution or edit a conflicting derived status. Add independent hand-authored
expectations and bounded nested/many-increment scale/determinism observations.
Review traversal complexity, diagnostics and modularity; no fixture-specific
parser exceptions or general compiler framework.

## Current direction and remaining gates

Latest explicit user cadence: required local tests before merging increments;
no pre/post-merge CI unless actual branch protection requires it; full combined
Foundation CI after all implementation is complete. Preserve all tests and
protections. Final roadmap completion still requires that combined CI.

Current phase: readiness complete; draft PR creation then implementation and
independent review. No FND-03 implementation or test result is claimed yet.
Keep all FND-03 checkboxes open until their own deliverables and acceptance
conditions are evidenced. Record clean final source and actual merge tree;
archive completion evidence and close authoritative checklist only on verified
integration. Main remains untouched.

This increment does not affect generated Verilog.
