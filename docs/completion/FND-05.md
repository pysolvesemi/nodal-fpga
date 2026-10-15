# FND-05 — Cross-language serialization and compatibility

The implementation passed exact-source local qualification and independent review and was integrated with an identical tree. This concise checklist records verified results without uploading raw execution data. Final documentation qualification, source-anchor verification and closure integration remain separate; no future identity is asserted.

Tested commit: `546b869e38a5741407fe2a57934432a120ff221c`. Tested tree: `8682ec0d859610418c29273d08526bd2ae2a94d9`.
Actual implementation merge: `f3f26b895beb07da2255c9977213e929e35ae487`. Merge tree: `8682ec0d859610418c29273d08526bd2ae2a94d9`. Ordered parents: `c508401afb3bc172a28163b84375157e1ce2ac2d`, `546b869e38a5741407fe2a57934432a120ff221c`.

The [summary receipt](FND-05.evidence.json) binds all 17 required leaves under receipt profile `portable-exchange/0.1`. This groups the three real exchange-0.1 profiles; it does not add a wire profile.

## Verification checklist

- contracts: All 226 tests passed: bootstrap 74, Foundation 43, roadmap 109; documentation, ownership and evidence-policy checks also passed. Command: ./nf check contracts.
- rust: Complete Rust suite passed: locked/offline dependency/source gates, formatting, warnings-denied Clippy, 69 unit/integration tests and four doctests. Count is one complete required suite. Command: ./nf check rust.
- scala: All 17 executable writer groups passed with pinned authoring tools and reviewed dependency classpaths. Command: ./nf check scala.
- reproduce-rust: Two clean-copy Rust builds produced identical bootstrap/model outputs. Command: ./nf reproduce rust.
- exchange-1: Actual authoring run 1 and all 83 independent Rust-consumer conformance groups passed against authored expectations. Command: ./nf check exchange.
- exchange-2: Actual authoring run 2 and all 83 independent Rust-consumer conformance groups passed against authored expectations. Command: ./nf check exchange.
- authoring-repeat: All three full envelopes, all three projections and the identity record agree byte-for-byte; source binding was separately checked. Command: Python byte-comparison template in the summary receipt.
- saved-runtime: Verification harness exited 0 after checking six intended cases: four actual saved-package consumers exited 0, identity-mismatch rejection exited 1 with no output, and x32 denial exited 159/SIGSYS with no output. Actual reader and admitted dependencies were independently observed. Command: ./nf saved-runtime --binary "$PREBUILT_READER" --scala-artifacts "$SAVED_SCALA_FIXTURE" --output "$RUNTIME_OUTPUT" --observation-profile loader-procfs.
- runtime-controls: All four runtime harness/negative-control tests passed. Command: python3 -m unittest discover -s tests/runtime -v.
- receipt-controls: Negative evidence, expected-source freshness, authoritative profile, stale execution identity and dirty-source rejection controls passed; full summary-mode controls also ran in the contracts suite. Command: PYTHONPATH=tests/roadmap python3 -m unittest -v test_evidence.EvidenceTests.test_hand_authored_negative_evidence test_evidence.EvidenceTests.test_explicit_expected_candidate_rejects_stale_receipt test_evidence.EvidenceTests.test_authoritative_profile_required test_evidence.EvidenceTests.test_stale_raw_execution_identity_cannot_be_relabelled test_evidence.EvidenceTests.test_dirty_execution_cannot_qualify.
- review: Independent source and actual-result review accepted architecture, independent expectations and proportional quality/scale decisions; no blocking finding remains in the declared profile.
- deliverables: Inspected versioned compatibility/schema contract, actual executable Scala example, independent corpus and concise dependency/review conclusions.
- integration-record: Actual source-parent integration and identical tested/merge tree verified; required protection contexts were satisfied without bypass, under the authorized local-qualification cadence.

## Independent review

Reviewer: summary-contract-and-exact-head-reviewer. Implementation authors: exchange-implementation, runtime-implementation, summary-evidence-implementation, integration-coordinator.
- architecture: Published source matches the reviewed bounded exchange, checked FND-04 representations, flat immutable package admission, explicit compatibility and dependency ownership. Actual Scala output was consumed by the source-bound reader in the separate saved-package runtime; unsupported later operations remain explicit.
- independence: All original literal manifests and expected bytes remain independent of production outputs. Exact clean-source commands, local captures, repeated authoring, negative outcomes, actual reader, isolated-root, loader and process records and source hashes were independently inspected; source-bound prior production review and the separately reviewed summary validator remain unchanged.
- quality: Hierarchy and templates remain retained; positive caller-lowered budgets, bounded parser/resolver work, stable canonical identities and negative controls were exercised. Formatting, warnings-denied Clippy, predecessor regressions and measured finite scale axes passed without golden refresh, lint suppression or production-scale claims.

## Required leaf mapping

| Leaf | Observations |
| --- | --- |
| FND-05.a.1 | contracts, deliverables, review |
| FND-05.a.2 | deliverables, review |
| FND-05.b.1 | scala, exchange-1, exchange-2, review |
| FND-05.b.2 | exchange-1, exchange-2, authoring-repeat, review |
| FND-05.c.1 | exchange-1, exchange-2, deliverables, review |
| FND-05.c.2 | rust, exchange-1, exchange-2, review |
| FND-05.c.3 | rust, contracts, review |
| FND-05.d.1 | exchange-1, exchange-2, authoring-repeat, review |
| FND-05.d.2 | rust, exchange-1, exchange-2, review |
| FND-05.d.3 | rust, exchange-1, exchange-2, review |
| FND-05.f.1 | deliverables, review |
| FND-05.f.2 | saved-runtime, runtime-controls, review |
| FND-05.g.1 | review, deliverables |
| FND-05.g.2 | exchange-1, exchange-2, authoring-repeat, review |
| FND-05.e.1 | deliverables, authoring-repeat, saved-runtime |
| FND-05.e.2 | contracts, rust, scala, reproduce-rust, exchange-1, exchange-2, saved-runtime, runtime-controls, receipt-controls, review, integration-record |
| FND-05.e.3 | deliverables, integration-record, review |

## Actual example and limits

The [executable Scala source](../../frontend/scala/src/main/scala/nodalfpga/exchange/FixtureWriter.scala), [actual generated example](../implementation/fnd-05-example.md) and [versioned compatibility contract](../../schemas/exchange/0.1/README.md) are inspected deliverables.

CI disposition: User requested required local checks and independent review for incremental merges, with full combined remote CI after Foundation implementation. Live dev protection was disabled with no required contexts; candidate had zero workflow runs. No remote qualification is claimed. Post-merge disposition: Actual implementation merge includes skip-ci; live merge workflow inventory contains zero runs. Identical tested tree and ordered source-parent ancestry verified without bypass.

- Summary-only acceptance records verified outcomes; raw logs and machine/process observations are not included or claimed to be repository-retained.
- Loader/procfs/process-denial demonstrates scoped saved-package dependencies, not exhaustive file-syscall or same-process exec-attempt tracing, a network namespace or hostile-code sandbox certification.
- Local Rust compilation is not a fresh JVM-absent default-build-profile replay. FND-08 must replay all three release-candidate profiles and applicable full CI.
- Jackson 2.21.5 is accepted only for the reviewed bounded trusted-source generator APIs; known advisories and FND-07 re-review triggers remain.
- Bounded debug-process scale observations are not production throughput, exact peak-memory or real-time guarantees.
- No production DSL, DeviceDB/full-device inspection, RTL emission, physical configuration loader, CAD legality, timing, PDK or silicon result is claimed.
- Final documentation-candidate checks, narrow source-anchor verification, independent closure review and actual closure integration remain separate; no future identity is asserted.

This increment does not affect generated Verilog.
