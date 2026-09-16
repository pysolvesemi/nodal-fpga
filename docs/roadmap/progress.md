# Increment and nested-checklist policy

## State model

An increment is represented once, in its owning track, as a parent `- [ ]` line. Its sub-items are indented two spaces and carry stable IDs, such as `FND-01.a`. More deeply nested tasks are allowed using a further two spaces per level.

A leaf may become `[x]` as soon as its own implementation or verification deliverable is genuinely complete. Its parent stays `[ ]` while any required descendant or acceptance gate is unfinished. Partial progress is intentional and must not be lost when work resumes.

Illustrative syntax only; this is not project status:

```markdown
- [ ] EXAMPLE-01 — Add a component
  - [x] EXAMPLE-01.a Implement the accepted API. Evidence: immutable commit/report.
  - [ ] EXAMPLE-01.b Add negative and boundary tests.
  - [ ] EXAMPLE-01.c Pass final-head verification and record completion evidence.
```

The same rule applies recursively. Do not use `[~]`, percentages, or prose saying done as a substitute for the checkboxes.

## Closing an increment

The parent may change to `[x]` only when all required descendants are `[x]`, every declared dependency is complete, applicable final-head checks pass, and a completion report exists. The report must identify the exact implementation commit/tree, device-package hash and schema versions, tool versions, seeds, commands, results, test coverage, unresolved limitations, and evidence artifact paths.

An implementation sub-item does not imply its later verification sub-item passed. Conversely, a passing test does not establish that undocumented requirements were implemented. A timeout, skipped job, unsupported model, stale green run or missing artifact is not a pass.

The final child of every increment in this plan is a closure gate. Until that child has evidence, the parent remains open even if all code-writing children are checked. Retain sub-item IDs when splitting work; append new IDs instead of renumbering completed history.

## Evidence locations

Use `docs/completion/<increment-id>.md` for small reports and a content-addressed external artifact store for large logs, generated RTL, databases and waveforms. The report links immutable artifact hashes and CI run IDs. Do not commit proprietary PDK/model content or secret configuration keys.

For a code-bearing increment, include executable Scala source and its actual generated fabric Verilog when applicable, with generation commands and hashes. Do not reuse illustrative examples as evidence. If Scala is not involved, report the actual frontend used. For an increment with no RTL effect, write: `This increment does not affect generated Verilog.`

A final documentation-only commit may refer to an immediately preceding tested implementation source anchor only if the report demonstrates the implementation tree is unchanged and all applicable documentation checks also pass. Otherwise rerun affected checks at the new head. Never claim all checks passed solely because a prior implementation commit was green.

## Blockers, changes and regressions

All non-Foundation tracks inherit `FND-08`. No checked child overrides that blocker. If completion evidence becomes invalid, reopen the affected leaf and every completed ancestor, describe the regression, and review dependent increment/release claims.

A required task cannot be silently deleted or marked done as not applicable. A genuine scope change requires an explicit roadmap amendment, rationale and impact review; it must not disguise missing verification. Keep optional experiments out of required closure checklists unless formally adopted.

## Optional-track decisions

Assessment, prototype and adoption are separate deliverables. A completed assessment may conclude retain-default or defer, but it cannot mark unperformed implementation or qualification items `[x]`. Keep those items unchecked and record their dormant reason. Explicit proceed/adopt conditions are additional blockers, not substitutes for checkbox dependencies. For the CIR track, CIR-02 requires CIR-01's proceed decision and CIR-03 requires CIR-02's adopt decision. An advertised optional backend must pass its own qualification; a default-only release need not implement dormant optional tracks.

## External silicon and production gates

[DFT-06/07](tracks/16-dft-manufacturing-test.md) and silicon/product gates require actual fabricated-device or selected-tester measurements, with sample, device/process/package, fixture, pattern, model and tool revisions plus raw-result provenance and uncertainty. A runnable adapter, mocked dataset, simulation, emulation or exported ATE file cannot stand in for those measurements. Preparatory test software/interface work belongs to the pre-silicon DFT increments and can be delivered without claiming silicon qualification.

Labs/manufacturing partners may produce the evidence externally. This repository records requirements, portable artifacts, correlation and qualification decisions; it does not require equipment ownership or factory operation. Missing samples, access or partner evidence keeps the affected gate open, but does not block earlier software/generator releases that do not depend on it. Per-profile absent hardware must be explicitly declared and its applicability checked; do not silently mark an unsupported required feature complete. The ordinary nested-checklist and regression rules still apply.

## Planned enforcement

FND-03 will add a roadmap validator that ignores fenced examples, checks unique increment/sub-item IDs, indentation, parent/descendant state consistency, dependency existence and cycles, and required completion evidence. It must include negative fixtures with an incorrectly closed parent. This planning commit does not claim that validator already exists.
