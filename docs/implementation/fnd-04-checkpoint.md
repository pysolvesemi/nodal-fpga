# FND-04 implementation checkpoint

Phase: implementation, independent fixtures and hash-bound source review are
complete and frozen. Required development checks have passed; publication, clean exact-head
qualification, verified integration and accepted-evidence closure remain with the
integration coordinator. No FND-04 checkbox is changed by this checkpoint.

Readiness source: `6d3c429950fc401ef351defb3efa871a994db0b7`, branch
`increment/fnd-04-core`, draft [PR #7](https://github.com/pysolvesemi/nodal-fpga/pull/7).
The completed FND-03 closure base is
`d4948096e16e7299ef02a90363f90491ebe9790d`. All results below are uncommitted
working-tree development results, not clean published-source acceptance.

## Delivered contracts and leaf coverage

- **FND-04.a.1–a.2:** `core/rust/types` implements distinct nominal resource IDs,
  checked quantities/ranges, source spans, provenance and structured diagnostics.
  Public integration tests use these APIs without device/adapter dependencies;
  compile-fail doctests reject cross-kind and cross-unit substitutions.
- **FND-04.b.1–b.2:** structured portable keys remain separate from dense u32 IDs,
  exact build/partition contexts and explicit total one-to-one correspondence.
  Capacities up to 2^32 and u64 offsets are checked without offset-sized arrays.
- **FND-04.c.1–c.2:** `core/rust/arch-ir` preserves resource interfaces, reusable
  finite templates, independent instances, explicit references, ordered mux
  sources, legal modes, typed domain memberships and logical configuration.
  Direct aliases, ownership, complete selections and canonical destination
  constraints are validated through immutable borrowed witnesses.
- **FND-04.d.1–d.2, f.1:** independently authored fixtures and public tests live in
  `verify/fixtures/fnd-04/` and both crates' `tests/independent_contract.rs`.
  Preparation-time expectations were frozen before production implementation;
  their hash is retained in the corpus README. Tests enumerate 6,561 tiny
  interval pairs, 2,304 guard/value selections (172 accepted, 516 conflicts,
  1,616 inactive writes), 64 ownership-overlap pairs and 128 seeded mutations.
  Another 6,000 comparisons sweep work budgets under mode-name, mode-group and
  owner/alias membership permutations with a competing diagnostic cap.
- **FND-04.d.3:** selected interaction rationale is below; source/profile-bound
  acceptance remains a coordinator obligation, not inferred from Rust tests.
- **FND-04.f.2, g.1:** [API contract](../development/core-api.md) and
  [independent architecture review](fnd-04-independent-review.md) describe the
  structural/type profile, module boundaries, traversal/duplication analysis,
  repaired defects and later DB/CFG/RTL consumers.
- **FND-04.g.2:** bounded independent axes cover 1/16/256/4,096 repeated resources,
  depth 1/8/32/64 and rejected 65, partition counts 1/2/4, huge scalar offsets,
  and compact high-fanout work exhaustion. Measurements are observations, not
  production-scale thresholds or PERF/PPA qualification.
- **FND-04.e.1:** the actual Rust-builder example is
  `core/rust/arch-ir/examples/model.rs`; it runs three independent instances,
  two links, complete legal selections and a source-aware illegal value.
  Documentation includes the actual output, supported/rejected semantics and
  reproduction commands. Exact development source hashes are in the review.
- **FND-04.e.2–e.3:** local correctness/regression and independent review are
  prepared here. Clean-source qualification, actual verified merge and accepted
  evidence remain open. Parent completion requires every descendant and FND-03.

The ownership guard is now an exact three-package name/path/version DAG with one
normal, non-target-specific edge `nf-arch-ir -> nf-types`. It rejects registry,
renamed/dev/build/target dependencies, path/symlink escapes, cycles, configuration
injection, native/build/source-inclusion hooks and relaxed unsafe/publishing
policy. Both static manifests and Cargo's actual resolved graph are checked.
There are no concrete device, Scala, adapter or external crate imports in core.

## Review findings and repairs

Independent source review and hand-authored regressions found and repaired:

- Drivers declared in distinct hierarchy scopes or through aliases could denote
  the same destination. A bounded streamed ownership pass now rejects them.
- One canonical resource could acquire incompatible mode-group ownership through
  an alias. This profile explicitly rejects more than one group membership.
- Definition/instance-qualified keys needed the lowered whole-key limit, and
  Field-resource/feature or PIP-resource/connection names could collide. All
  derived names are bounded, including architecture-level connection Pip keys
  with empty scope. Exact-bound/one-byte-overflow and reordered-declaration
  controls cover that top-level case; same-kind identity collisions reject. Mode groups
  and storage have distinct nominal diagnostic key kinds.
- Cycle detection could name an acyclic descendant; an iterative back-edge
  witness now retains the actual offending child origin and both template keys.
- Duplicate domain and contradictory guard diagnostics needed both original
  sources and permutation-stable ordering. Selection errors needed Selection
  stage and absolute instance identity. Set-domain error text is now canonical.
- Before comparing nested records, bounded allocation-free shape inspection now
  checks vectors and reference paths. Caller ceilings cannot disable safety.
  Competing path/key/diagnostic/work exhaustion yields deterministic failures.
- Repeated finite-domain alias/mux scans and guards are budgeted. The work counter
  is conservative logical accounting, not an exact CPU or hard memory quota.

The validator is split into `bounds`, `references`, `declarations`, `connections`
and `selection`, with one public model and transient borrowed indexes. No second
normalized model, eager hierarchy expansion, native-layout API or unsafe code is
introduced. The review binds the final module/test/tool hashes and records limits.

## Selected predecessor interactions

The fixture inventory selects ASM-0003/0004 sharing and mode activation,
ASM-0008 unit/identity bounds, ASM-0009/0010 graph/ownership and ASM-0011 independent
domain membership. ASM-0002 is exercised only by unsupported declared-mode
rejection; no LUT/register behavior is executed. This selects the boundaries the
new APIs actually expose, rather than an all-features Cartesian product.

The contracts gate executes FND-03's independently authored controls including
`test_hand_authored_negative_evidence` (stale source, artifact hash and profile),
`test_explicit_expected_candidate_rejects_stale_receipt`,
`test_authoritative_profile_required`,
`test_stale_raw_execution_identity_cannot_be_relabelled` and
`test_dirty_execution_cannot_qualify` in `tests/roadmap/test_evidence.py`.
A separate development invocation of these five selected methods also passed:

```sh
PYTHONPATH=tests/roadmap python3 -m unittest -v \
  test_evidence.EvidenceTests.test_hand_authored_negative_evidence \
  test_evidence.EvidenceTests.test_explicit_expected_candidate_rejects_stale_receipt \
  test_evidence.EvidenceTests.test_authoritative_profile_required \
  test_evidence.EvidenceTests.test_stale_raw_execution_identity_cannot_be_relabelled \
  test_evidence.EvidenceTests.test_dirty_execution_cannot_qualify
```

The coordinator will bind the actual model stdout, including source-aware
rejection, to a clean-head FND-04 receipt and retain these selected controls.
The diagnostic's semantic correctness and its receipt integrity are separate
checks; neither grants hardware execution credit.

## Local commands and observations

Commands use `source .cache/toolchains/env.sh`, selecting the installed pins
in `toolchains/versions.json`: Rust 1.98.1, Scala 3.3.8, sbt 1.12.11 and Temurin
JDK 21.0.12.1+1. Final accepted captures must also set `TZ=UTC`; the retained
development Scala log accurately contains the host-timezone display. No remote CI
was launched.

- `./nf check contracts`: 60 bootstrap/ownership tests, 43 Foundation contract
  tests and 92 roadmap/evidence tests, plus documentation links and real roadmap.
- `./nf check rust`: rustfmt, clippy with warnings denied, 49 unit/integration
  tests, four doctests (three compile-fail), and locked/offline actual Cargo DAG.
- `./nf check scala`: formatting, clean compilation, Scala/sbt version checks.
- `./nf reproduce rust`: two clean builds; bootstrap and actual model stdout
  match byte-for-byte. Model SHA-256:
  `1615356294a3728c68d2bb9fe76c296dfd5c4ecd3daa73340cdc76ccd4868bd2`.
- `cargo build --locked --offline -p nf-arch-ir --example model`, then direct
  `target/debug/examples/model` execution twice with byte-identical stdout.
- The prebuilt `nf-arch-ir` independent integration-test executable runs
  `bounded_count_depth_partition_observations_preserve_compact_declarations
  --exact --nocapture` directly twice. Stable observations/counters match after
  removing only the explicitly unstable `elapsed_ns` fields. Original timing
  logs remain intact. The test itself compares repeated model/stats equality.
- `git diff --check` and whitespace inspection of all new authored source/docs
  pass after final review/checkpoint writes; raw original logs retain
  their bytes, including the known JVM property-output whitespace.

Raw logs, direct-binary timings, stdout/stable projections and dirty-source
metadata are under ignored `artifacts/fnd04-development/`. Their original bytes
are development evidence only. The direct-binary Bash timings exclude Cargo and
compilation; no peak-RSS claim is made from those timings. Shallow vector capacity
and string payload observations exclude allocator overhead and other allocations.
The independent review separately labels any process-RSS observation it measured.

### Direct prebuilt observations

On the development Linux x86_64 runner, the first direct example process took
0.002 s wall time; the entire scale-test process took 0.099 s. Both are Bash
`time` observations with millisecond reporting, not validator-only timings.
Within the test, architecture validation at 4,096 instances took 15,191,529 ns,
and complete selection took 48,708,225 ns. The declarations retained one template
and one resource declaration, with 4,096 root occurrences: shallow root-vector
capacity 819,200 bytes and root-name payload 31,658 bytes. Architecture counters
were 4,106 declarations, 4,099 references and 209,839 work units.

Depth 64 retained 64 templates, validating in 1,522,847 ns with 36,886 work units;
depth 65 rejected. Eight-instance partition fixtures retained seven links, with
zero crossings for one partition and seven crossings for two/four partitions.
The stable scale projection from two executions has SHA-256
`c151341afef02fdd58babf954c003485e7e8367d90ffcc35411bb6e797bff948`.
Elapsed-time values are deliberately excluded only from that projection, not from
the original logs. These observations were captured on the frozen development source. The prebuilt
scale runner was `target/debug/deps/independent_contract-d6be13293ea652fa`; its
source is the ArchIR independent integration test. Clean-head measurements remain
coordinator-owned.

## Affected workflow inventory and remaining acceptance

One repository workflow is defined: `.github/workflows/fnd-01-bootstrap.yml`,
recorded workflow ID `367539769` in accepted FND-01 evidence. Its current definition
SHA-256 is `6cb05112e8ecc1c69ff6125ee71b270ac6dd4ea8786582ce6887f57c9d32f7f3`.
Jobs are `contracts`, `rust`, `scala`, and aggregate `required`; no matrix exists.
The dispatch input `lane` selects `contracts`, `rust`, `scala` or `all`.
Contracts and Rust are directly affected; Scala is a shared-`tools/nf.py`
regression lane and was checked locally. Workflow triggers/permissions/definitions
were not changed. A workflow ID from historical evidence is not a claim of live
remote registration or current branch-protection state.

Latest explicit user cadence defers pre/post-merge remote CI until full combined
Foundation qualification, unless actual protection requires it. No absent run or
skipped lane counts as executed. The coordinator must refresh live source/target,
PR and protection, publish the clean candidate, rerun and retain exact-head local
qualification, verify the actual merge parents/message/tree, then close evidence
with the narrow final-documentation anchor. Full combined remote CI remains due
at final Foundation. No main-branch change or protection bypass is authorized.

This increment does not affect generated Verilog.

The actual frontend here is the Rust builder. No Scala architecture frontend,
fabric generator, RTL simulator/formal result, production DeviceDB, physical
allocator, bitstream loader or hardware equivalence claim follows from this work.
