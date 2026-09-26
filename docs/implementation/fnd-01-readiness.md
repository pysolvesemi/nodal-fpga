# FND-01 readiness review

Status: scope reviewed; implementation and qualification are open.
Integration baseline: `cd6ec64e7f25e60ac4277159b76279c08d5d8210`.
Branch: `increment/fnd-01-bootstrap`; target: `dev`.
Owning checklist: [Foundation FND-01](../roadmap/tracks/00-foundation.md).

## Live-state audit

The baseline has 26 Markdown files, no Rust/Scala workspace, no workflow files,
no earlier implementation evidence, and no existing increment branch or open PR.
Read AGENTS.md, the roadmap index/progress rules, architecture, verification,
early-baseline contract and ADR 0001 before this review. FND-01 has no predecessor.
No required leaf is removed, narrowed, deferred or marked complete by this review.

## Bounded implementation

Create one dependency-free Rust bootstrap crate under `core/rust/` and one tiny
Scala 3 executable under `frontend/scala/`. These demonstrate build/ownership
contracts only: no architecture DSL, ArchIR, DeviceDB, fabric emitter or customer
CAD flow. Use Python standard-library developer commands and a manifest/source
boundary check with deliberate violations. Do not scaffold future crates.

Pin Rust 1.98.1 (rustfmt/clippy), Scala 3.3.8 LTS, sbt 1.12.11 and Temurin
21.0.12.1+1. Pin the sbt launcher by SHA-256 and CI actions by commit. The separate
Rust build must not invoke Scala/JDK or any MLIR/CIRCT SDK. The Scala authoring
profile requires its own JDK; neither profile is a production package runtime.
Record and test unprivileged toolchain setup and exact versions. Keep the current
project licensing decision open: do not introduce a license grant or publish a
package; record third-party tool licenses and restricted-content boundaries.

## Obligation review

| Existing leaf | Classification and deliverable |
| --- | --- |
| FND-01.a.1 | Required now: minimal Cargo workspace, exact toolchain and lockfile. |
| FND-01.a.2 | Required now: formatting/lint/test commands and actual unprivileged setup/build evidence. |
| FND-01.b.1 | Required now: one pinned sbt/Scala/JDK combination and reproducible setup. |
| FND-01.b.2 | Required now: executable Scala smoke fixture without a compiler SDK. |
| FND-01.c.1 | Required now: dependency directions and license/proprietary-content policy. |
| FND-01.c.2 | Required now: boundary checks plus intentionally forbidden dependency/input cases. |
| FND-01.c.3 | Required now: actual isolated default Rust build and dependency/process observations. |
| FND-01.d.1 | Required now: separate clean Rust/Scala builds and missing-prerequisite diagnostics. |
| FND-01.d.2 | Required now: minimal CI and a legitimate exact-candidate targeted launch route. |
| FND-01.d.3 | Required now: docs-only trigger/skip handling; absent hardware checks get no credit. |
| FND-01.f.1 | Required now: independent review of build/ownership evidence and guard failures. |
| FND-01.f.2 | Required now: applicability record; generated-fabric tests are outside this bootstrap profile, with FND-06 and RTL/VER ownership preserved. |
| FND-01.g.1 | Required now: proportionate workspace/dependency/output-quality review. |
| FND-01.g.2 | Required now: repeated clean builds and deterministic smoke outputs, with measured costs and limits. |
| FND-01.e.1 | Required now: reproducible completion record and immutable source/tool/artifact identities. |
| FND-01.e.2 | Required now: targeted-first then full applicable qualification, review and verified integration. |
| FND-01.e.3 | Required now: reconcile every leaf and report actual Scala smoke output before parent closure. |

FND-02 owns the architecture/assumption contract, FND-03 the production roadmap
validator, FND-04 the typed semantic model, FND-05 interchange/runtime conformance,
and FND-06 external reference/formal infrastructure. These later capabilities are
not claimed by bootstrap smoke results or made prerequisites of FND-01.

## Qualification plan and current execution limits

Use focused contracts, Rust and Scala lanes. Each must bind logs and artifacts
to the actual checkout SHA/tree and exact tools. Include clean repeated builds,
stable outputs, boundary-mutation failures, locked dependency inspection and
profile isolation; actual executed checks are distinct from applicability review.
After all affected lanes pass, inventory the full applicable set and run only
missing requirements before review/integration.

The connected GitHub route can publish the branch and inspect Actions runs.
No direct workflow-dispatch tool is exposed. Inspect actual workflow registration
after candidate publication and use only the narrowly scoped repository dispatcher
allowed by AGENTS.md if available. Do not change main/default branch, expand
automatic triggers, create fake checks or substitute local tests for remote CI.
A dispatch registration/access failure remains an explicit open qualification
obligation; this review does not create an alternative permission.

The current interactive environment has Python and JDK 17, no Rust toolchain,
and Maven access. A direct Rust distribution probe timed out. These are local
execution constraints, not proof that a pinned bootstrap succeeds or fails.
Canonical Rust/JDK-21 qualification still requires actual execution. Retain any
noncanonical local observations separately and use remote jobs where available.

## Progress and evidence

Keep the single draft PR and [durable checkpoint](fnd-01-checkpoint.md) current.
Enable one hourly continuation after this commit and PR exist; it must avoid
competing with an active worker and retain source/evidence identity across sessions.
All FND-01 checkboxes remain open until their own evidence exists.

This increment does not affect generated Verilog.
