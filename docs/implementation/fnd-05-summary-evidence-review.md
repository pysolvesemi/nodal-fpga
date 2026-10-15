# FND-05 independent summary-evidence review

Date: 2026-10-15 UTC. Reviewer: independent summary-evidence contract reviewer.

## Disposition

Accepted for the exact file identities below. No unresolved blocking finding
remains in the summary-receipt contract or editorial/publication cleanup.
This is independent source and local-test review of an unpublished candidate;
clean-commit qualification, actual integration and acceptance closure remain
separate coordinator gates. No authoritative checklist was changed by this review.

## Contract findings

- Version 2 explicitly selects summary mode. Execution requires a concrete command,
  clean matching source/tree/profile, actual-execution attestation, successful
  harness exit, positive equal required/executed/passed counts and zero failures
  or skipped checks. Expected nonzero negative-control exits remain distinct from
  successful harness status. Review cannot substitute for required execution.
- Identified non-author review must cover every observation exactly once and
  accept architecture, independence and quality with findings and limitations.
  Report hashes, real deliverables, path/size bounds and Git identities remain
  checked. No raw log, separate source-record file, private workspace path or
  host identifier is required for a summary.
- Actual source-parent merge, equal tree, two distinct parents and ancestry remain
  required for closure. The narrow documentation-source anchor is unchanged;
  the receipt alone does not qualify its later documentation head.
- Independent review found one metadata inconsistency: post-merge execution could
  be claimed while integration remained pending. A version-2-only guard now
  rejects this, including a plausible HTTPS run reference. Version-1 behavior
  was preserved rather than retroactively changing historical receipts.
- This format is an independently reviewed attestation, not retained raw proof or
  authentication of arbitrary claims. The validator does not execute receipt
  commands or verify remote CI truth from URLs. Actual testing and inspection
  remain mandatory; physical-measurement provenance and generated deliverables
  are not replaced by prose.

## Executed independent checks

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/roadmap -v`:
  **109 tests passed** after the final fix, including historical receipt cases,
  real altered-tree merge rejection and source-anchor regressions.
- A separately authored temporary Python runner passed **8 independent groups**.
  It covered raw-record-free acceptance, strict result/count/type/source binding,
  reviewer coverage, actual merge/closure and post-merge consistency, artifact
  hashes/paths, byte bounds and documentation anchors. Its **780 malformed or
  missing-field version-1 mutations** produced identical outcomes in the original
  validator and extracted shared-helper implementation. The runner is not a
  published project acceptance artifact; these are validator fixtures, not FPGA
  implementation results.
- AST comparison confirmed **12 existing non-evidence functions unchanged**,
  including source identities, authoritative status and source-anchor checks.
  **All 86 historical completion files remained byte-identical.**
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/exchange -p
  test_fixture_integrity.py -v`: **6 tests passed**. Independent hash/byte checks
  confirmed all four fixture manifests and **121 bound literal files** unchanged,
  all **43 development plus 28 review source-vector entries** matching, and all
  **3 actual example JSON blocks** preserved.
- `git diff --check`: passed. The new policy documentation was read alongside the
  code and publication summaries; its retention, actual-execution and final-head
  limits agree with the reviewed implementation.

## Publication and review limits

The removed 22 files were execution observations or preparation logs, not oracle
inputs. Functional fixtures, executable tests and actual examples remain. Edited
reports faithfully distinguish original review from editorial summaries, dirty
local development observations from clean-head qualification, and locally kept
raw records from published artifacts. No stale evidence-directory link or private
workspace path remains in the reviewed publication prose.

This reviewer did not rebuild Rust/Scala, replay the saved runtime, launch CI,
publish or merge. The cleanup owner's separate 83-group conformance replay is
not counted as this reviewer's execution. Existing loader/procfs, dependency,
scale, security and future FND-08 limits remain unchanged. Later relevant source
or qualification-contract changes require affected checks and review again.

This increment does not affect generated Verilog.

## Reviewed file identities

These SHA-256 values bind the reviewed snapshot, not a future commit.

| Repository path | SHA-256 |
| --- | --- |
| `tools/roadmap.py` | `371af088f149ae778ea268a8db1228486d4deecf608de2efbbdd4dc9fe705256` |
| `tests/roadmap/test_summary_evidence.py` | `2663a3fdd3801108916cff336fca9fc31e7c1becd52cf25ef8c10b785ea92f4a` |
| `tests/roadmap/evidence_fixtures/summary.json` | `877a95d53a85220529db4c2dce084c18724524df1459cb3197096f38ee9b718a` |
| `AGENTS.md` | `e753702d4c777bbd2a22b1db7de9b3085744189a94299de1681c64b68b5a5444` |
| `docs/roadmap/progress.md` | `6e9c70a855b202d8bb3d41df979870b254ff41097a6e1adc58a1b4a79ca40e8b` |
| `docs/development/roadmap-validator.md` | `e5b9b5e9c3fdb5f7269ff0fcd87034007b8d11f27f7ca93990156bfde562cc4d` |
| `docs/verification.md` | `7d40b2b10188a56dd88c12dbcd91574c5f3bd8d4788113178281251924b2797b` |
| `docs/implementation/fnd-05-checkpoint.md` | `98baf497e4553e279df551db36dfb6823909a6f466fc2a79ea9b2cd9f796f439` |
| `docs/implementation/fnd-05-corpus-review.md` | `df477bbeb19b49fd160be1d2f387e26d1a3604cb653e79275d068ac790fa5b3f` |
| `docs/implementation/fnd-05-dependencies.md` | `c27a71cfd4aea57be3dfaeb7c353b79b02bf915f431e68a5aa26f6a3265b0195` |
| `docs/implementation/fnd-05-example.md` | `dbd358ba1984e00d8dd6b5e8740844ca6b4702a95f81c9229a02f958693c58ce` |
| `docs/implementation/fnd-05-implementation-review.md` | `438d5f8f18fdd9755988c7dc47589bd5a2a274fee123bdff07d2fd89d49515f5` |
| `docs/implementation/fnd-05-runtime.md` | `a9c01fbf4388268779ebf29331d4ee549c6d9172f68b3aa225d832f28a95c7fd` |
| `docs/implementation/fnd-05-development-source.sha256` | `39728b58f179b0624cb306d3a96dd97fc9ed62c99cb6bc6d0b515efea05868fe` |
| `docs/implementation/fnd-05-review-source.sha256` | `ba2265f543f8debbd6844fb50ff5e2123b48b4f03a2a384dbd450664d2faa5f5` |
| `tests/exchange/README.md` | `878bbe5e8203845d14e2b4a0e2c595f5a2b2873471e8cba976e6c2864a60f388` |
| `tests/exchange/test_fixture_integrity.py` | `3fa2dadf9c8267ad57ab1d34337af3ba29158a6867f36aa569ad29313f74bc66` |
| `verify/fixtures/exchange/README.md` | `a67945c46a98e3d9e9f4424fdfa8d8ea2f492ebcdb24cdac2df3b226479707ff` |
| `verify/fixtures/exchange/preparation.md` | `bdf6ff54cec04a1a19a3050ff2f1ed7c8bd4520ee1022d8b5c6b7582042e7aa5` |
| `verify/fixtures/exchange/goldens/EXPECTED.md` | `87c35485cf0ff11a9dbfa1653c16804fb5b5292c590ed5f12faa69ab04e242dc` |
