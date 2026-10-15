# FND-03 implementation checkpoint

Phase: local implementation and independent review complete; coordinator still
owns clean-source qualification, publication, actual integration and accepted
evidence/checklist closure. All FND-03 checkboxes remain open.

Review/development base: `3ccf9ff8cd74f3dfc72feb463e9d4f69a289448b`.
Development checks ran over an uncommitted tree; these are not clean final-head
acceptance evidence. Exact committed qualification must be retained separately.

## Deliverables

- `tools/roadmap.py`: bounded nested Markdown, dependency/global-gate/closure
  validation, source/profile-bound receipts and deterministic derived views
- `tools/nf.py`: normal contracts enforcement plus `nf roadmap` commands
- Completion report/JSON templates and accurate historical FND-01/02 sidecars
- Hand-authored independent Markdown/status and evidence rejection fixtures
- Narrow source-anchor verification and reproducible bounded scale observations
- Existing contracts workflow full-history checkout for ancestry verification;
  trigger/permission/lane behavior unchanged, no remote CI launched

See the [validator contract](../development/roadmap-validator.md) and
[independent review](fnd-03-independent-review.md) for diagnostics, limits,
findings and repairs. No original predecessor log/index was changed. Foundation
execution annotations implement existing requirements without changing status,
IDs, task text or historical remote-versus-local evidence.

## Local development checks

`source .cache/toolchains/env.sh` selected the installed pinned toolchains.

- `./nf check contracts`: passed 20 existing bootstrap, 43 Foundation and 92
  roadmap/evidence tests, plus real roadmap and documentation/link checks
- `./nf check rust`: format, clippy with warnings denied, all-target tests,
  one doctest and locked/offline dependency graph passed
- `./nf check scala`: format checks, clean compilation, Scala/sbt versions passed
- `./nf roadmap --write-view artifacts/fnd03-development/roadmap.json` and
  `--check-view` passed: 82 increments, 648 nodes, 50 checked nodes, two accepted
  parents; every FND-03 node remains open
- `python3 tools/roadmap_scale.py --increments 2000 --depth 192` passed repeated
  deterministic output, with observations below
- `git diff --check`: passed

Local raw development logs and dirty-source metadata are under the ignored
`artifacts/fnd03-development/` directory. They are deliberately not relabelled as
clean published-source acceptance. The coordinator will run and retain exact-head
commands on the candidate before merge under the user-directed cadence.

## Bounded observations

CPython 3.12.14 on Linux-6.18.44-x86_64-with-glibc2.41.
Timing includes tracemalloc overhead; memory is peak traced Python allocation,
not RSS. Results are observations, not performance thresholds or PERF claims.

- many_increments: 215604 input bytes, 6000 nodes, 2000 increments; 0.478391 s, 11358560 B peak; two byte-identical renders, SHA-256 `8aa903db399549526ad295425a82c6a31ecae2637d55eea523bfc8b00e8ac9f0`
- nested: 79178 input bytes, 194 nodes, 1 increments; 0.015642 s, 595272 B peak; two byte-identical renders, SHA-256 `6e1d6d161e781fd46dccefec61d008aed4aee9043e54479587d08a86cf779fd5`

## Reviewed source identities

These are development-byte hashes, not a commit or final acceptance claim.

- `tools/roadmap.py`: `e97709a5926d7447374fa2a1df0ed31e469b214e7fa90968d6817c64edccb704`
- `tools/roadmap_scale.py`: `3eff494975b3dba8385fe440b85e1731739d11691d736da1f0571e9af05a3ffc`
- `tools/nf.py`: `4fdf6871dfac233d1f0ff1742c0ee2d61d7b1ba4f76cc5015034ad17bda35330`
- `tests/roadmap/test_evidence.py`: `8bea26309ba0cb4e2ab02ae31d3b7503123a94541db69ccdeb6367ee53441a60`
- `tests/roadmap/test_independent.py`: `fa8caa02c37aee5ee808e2f24de74489597c9fe0c5b85be85893f0702ae72e5f`

## Remaining acceptance steps

Publish the reviewed candidate on the existing increment branch without remote
CI; run clean exact-source required local qualification and preserve source/tree,
commands/results and artifact hashes. Honor any actual branch-protection checks.
Verify ordinary two-parent merge into dev and identical tested tree. Then prepare
report/receipt and authoritative checkbox closure with the final-documentation
anchor and new documentation checks. Full combined Foundation CI remains due at
FND-08. Main and later increment implementations remain untouched here.

This increment does not affect generated Verilog.
