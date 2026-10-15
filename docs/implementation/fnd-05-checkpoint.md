# FND-05 development verification checklist

Status: implementation and development-local checks passed on an uncommitted
candidate. Publication, exact clean-head qualification, integration and accepted
checklist closure remain pending. The authoritative Foundation leaves stay open.

## Source and evidence boundary

- Accepted predecessor: `c508401afb3bc172a28163b84375157e1ce2ac2d`.
- Readiness commit and development HEAD: `4895bcc96f527049ad1b22a206987959b11b9878`
  (draft PR 9). HEAD alone does not identify the tested uncommitted implementation.
- The [43-entry development source vector](fnd-05-development-source.sha256),
  SHA-256 `39728b58f179b0624cb306d3a96dd97fc9ed62c99cb6bc6d0b515efea05868fe`,
  preserves the original exact conformance inputs. The
  [28-entry independent review vector](fnd-05-review-source.sha256) separately
  binds the reviewed exchange/runtime/dependency source.
- Reader SHA-256: `2ccf48d3d54b005d23064a827394b227fb8e94891c2223d4051885ea25a2b920`.
- These summaries replace publication of raw execution logs and host snapshots.
  Originals were preserved locally outside the candidate with a verified hash
  inventory. Raw records and generated observation copies are not repository
  artifacts or prerequisites for reading this checklist. Functional fixtures,
  source manifests and actual executable tests remain required and unchanged.
- Future accepted records use concise summary evidence: format_version 2 and
  evidence_mode summary. Actual tests, source/tool/corpus identities, independent
  review and verified source integration remain mandatory.
- The evidence-format/policy edits are later changes. Historical development
  results do not qualify those edits or a future clean commit.

## Actual development checks, 2026-10-15 UTC

These checkmarks summarize observed local results only; they do not change the
roadmap or claim source integration.

- [x] Contracts: 74 bootstrap, 43 Foundation and 92 roadmap tests, documentation
  links and ownership/evidence guards passed.
- [x] Rust: locked/offline graph/archive/source validation before and after build,
  formatting, warnings-denied workspace/all-target Clippy, workspace tests and
  doctests passed. Exchange: 8 unit and 12 independent public-API tests.
- [x] Scala: 17 executable writer groups, exact source binding and separate
  compiler/runtime classpath checks passed; repeated authoring was byte-identical.
- [x] Exchange: 83 independent Python groups passed against fixed hand-authored
  literals and actual Scala bytes. Coordinator elapsed: 4.747 seconds;
  independent replay: 4.964 seconds with unchanged reader hash before/after.
- [x] Saved runtime: four positive consumers, intended invalid-package rejection
  and x32 denial passed in the same reviewed boundary; four harness controls passed.
- [x] Independent exact-source/corpus/runtime review: no unresolved blocking
  finding in the stated scope. See [source review](fnd-05-implementation-review.md),
  [corpus review](fnd-05-corpus-review.md) and [runtime summary](fnd-05-runtime.md).
- [x] The [three actual Scala examples](fnd-05-example.md) were independently
  compared byte-for-byte with the successful reader output; they are not goldens.
- [ ] Qualify the final clean published commit/tree and all affected summary
  policy, documentation and receipt controls.
- [ ] Verify integration and produce a separately reviewed accepted completion
  record before changing authoritative acceptance checkboxes.

## Reproduction

With the pinned caches prepared, the development commands were:

```sh
source .cache/toolchains/env.sh
NF_OFFLINE=1 ./nf check contracts
NF_OFFLINE=1 ./nf check rust
NF_OFFLINE=1 ./nf check scala
NF_OFFLINE=1 ./nf check exchange
./nf saved-runtime --binary target/debug/nf-exchange \
  --scala-artifacts ACTUAL_SCALA_DIRECTORY --output FRESH_LOCAL_OUTPUT \
  --observation-profile loader-procfs
python3 -m unittest discover -s tests/runtime -v
```

The directory placeholders select fresh local results, not published files.
Plain sbt test is not a substitute for executable WriterChecks. Missing actual
Scala outputs or the prebuilt Rust executable fail conformance setup. A probe,
partial untraced run, old-head success or passing example is not qualification.

## Evidence-format conversion checks

After removing published observation copies, the existing six fixture-integrity
tests and all 83 prebuilt-reader conformance groups passed again (5.072 seconds).
The four literal manifests, all bound bytes and all three actual example JSON
blocks remained unchanged. Both historical source vectors still match current
files. Independent editorial/cleanup review verified the preserved findings/limits, the
43/28-entry source vectors, all four manifests and 121 literal artifacts, with no
blocking cleanup finding. No Rust or Scala build, runtime replay, remote CI or acceptance closure
was performed by this conversion check. Final exact clean-head qualification
remains required.

## Scope and retained limits

Implemented: bounded closed DTO parsing, FND-04 architecture adaptation,
schema-aware canonicalization, flat immutable digest-resolver packages,
exact-target structural mapped designs, explicit-file CLI, independent corpus,
actual Scala authoring, dependency inventories and saved-runtime harness.

The public API tests include 128 invalid lower-only limit configurations across
four entry points, zero pre-admission I/O, exact manifest counters, resolver
read/reuse limits and public Selection. Root-count, hierarchy and payload axes
establish bounded finite behavior, not production throughput or peak memory.
No literal golden was regenerated or replaced by candidate output.

The loader/procfs observation establishes the scoped saved-package dependency
profile. It is not exhaustive file-syscall/exec tracing, a network namespace or
hostile-code sandbox certification. Earlier failed tracer/probe observations
receive no consumer credit. Runtime execution retains its independent review
requirement; the local machine report's qualification_complete remains false.

The build environment included Scala/JDK. The reviewed 22-package graph and
actual Rust build are not a newly JVM-absent build-root replay. FND-01's accepted
historical build evidence is not relabeled; FND-08 must independently replay
all three ADR profiles on its release candidate and wire the full required CI.
No remote CI was launched for these development results.

[Dependency review](fnd-05-dependencies.md) retains the bounded generator-only
Jackson 2.21.5 advisory disposition and FND-07 review triggers. No broad security,
DeviceDB, RTL, CAD, programming, timing, hardware or silicon qualification follows.
This increment does not affect generated Verilog.
