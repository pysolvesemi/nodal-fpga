# FND-01 — Repository bootstrap and ownership boundaries

The build-only implementation is qualified and integrated into `dev`. This
documentation closure records the evidence and reconciles the authoritative
[Foundation checklist](../roadmap/tracks/00-foundation.md). Its final source,
document-check run and integration identity are recorded in the closure PR;
the implementation identities below are immutable and do not claim that its
tests ran on a later documentation or merge commit.

## Source, qualification and integration

| Identity | Value |
| --- | --- |
| Tested implementation | `c3e2a789db06c90bc1534f0483b100810b4e7a8b` |
| Tested tree | `31ad3cf3767020c584066d9d133b606ea91b6826` |
| Original integration target | `cd6ec64e7f25e60ac4277159b76279c08d5d8210` |
| Actual implementation merge | [PR #1](https://github.com/pysolvesemi/nodal-fpga/pull/1), `15485fbf1a90c56ecc574d18e389e9c65de86347` |
| Actual merge parents | Original target, then tested implementation, in the order above |
| Actual merge tree | `31ad3cf3767020c584066d9d133b606ea91b6826`, equal to the tested tree |
| Qualification workflow | ID `367539769`, `.github/workflows/fnd-01-bootstrap.yml` |
| Workflow Git blob | `a721884b8daa6fa16f7867988a2273fc02288c96` |
| Post-merge CI | `skipped`, reason `qualified-identical-tree-merge`; actual merge message contains `[skip ci]`, zero merge-head runs observed |

Every run below is attempt 1, event `workflow_dispatch`, branch
`increment/fnd-01-bootstrap`, and the exact tested implementation above.
Downloaded artifacts independently confirmed clean checkout/tree and UID 1001.

| Lane | Run | Executed jobs | Archive SHA-256 |
| --- | --- | --- | --- |
| Contracts | [36226115767](https://github.com/pysolvesemi/nodal-fpga/actions/runs/36226115767) | `contracts` 108360377245; `required` 108360398511 | `ce0913b514ff29b903eecf4fb06525bc3da2e98ff944c953ff19055d90d30a86` |
| Rust | [36226119663](https://github.com/pysolvesemi/nodal-fpga/actions/runs/36226119663) | `rust` 108360388761; `required` 108360503725 | `52700057dc1a8c732bc6b6b1ae4dc27a097d2a2273eb32c431ee5d9273fe9040` |
| Scala | [36226124675](https://github.com/pysolvesemi/nodal-fpga/actions/runs/36226124675) | `scala` 108360403431; `required` 108360533608 | `3cec3b52fe7229dc7875037887719caa0c70f3498734b219a75917569c6898d1` |

Targeted qualification finished before the full-scope inventory. That inventory
found one implemented qualification workflow, all three applicable lanes and
their aggregates. These same-head successes satisfy the full set; no duplicate
`all` invocation was launched. All 12 latest check records were inspected: six
executed successes and six intentional unselected-lane skips with no test credit.
There were no status records, requested reviews or discussion blockers. The live
`dev` branch reported protection disabled and no required contexts. Its separate
protection endpoint returned 403; no protection was changed or bypassed.

The [evidence index](evidence/fnd-01/index.json) records artifact IDs, source
identities and individual file hashes. The small raw artifact files are retained
verbatim beside it, so their evidence does not depend on GitHub's archive expiry
of 2026-12-25. In particular, inspect the [contract controls](evidence/fnd-01/contracts/contracts.log),
[Rust commands/metadata/linkage](evidence/fnd-01/rust/rust.log),
[Scala build](evidence/fnd-01/scala/scala.log) and
[Scala clean repeats](evidence/fnd-01/scala/scala-reproduce.log).

## Commands, tools and results

From a clean checkout, as an ordinary user, run the commands in
[the developer guide](../development/bootstrap.md):

```sh
./nf identity
./nf check contracts
./nf bootstrap rust
./nf check rust
./nf reproduce rust
./nf bootstrap scala
./nf check scala
./nf reproduce scala
```

CI runs the Rust commands in the separate container defined by
`ci/rust.Dockerfile`, with dropped capabilities, no-new-privileges, UID 1001 and
fresh writable Rustup/Cargo homes. It records both base and resulting image
identities. Base digest:
`sha256:93ce27a88655056a51dbdd8f5f2d7ddc071c7b0070fb288a37b5a285fc83971e`.
The qualified built image was
`sha256:06cb05a7d046fa6a916deb209d1f40a308a929b8857ca80efda1c3e4573a683f`.
The version tag and OS packages are not claimed immutable across future rebuilds;
the retained image identities describe this execution.

Rust/Cargo 1.98.1, rustfmt 1.9.0-stable and clippy 0.1.98 were observed after the
unprivileged installation. Formatter and warning-denying lint passed. All-target
test execution has zero unit cases; the separate public-consumer doctest executed
one real passing assertion. Two actual executable runs independently matched the
declared Rust smoke output. Offline locked Cargo metadata reports exactly one
crate, zero dependencies and no native links. `ldd` reports only ordinary system
runtime libraries. The container guard found no Java, Scala, build frontend,
MLIR/CIRCT tools, standalone `llvm-config` or installed JDK; normal LLVM internals
inside the Rust compiler remain allowed. This is build-only isolation, not the
saved-package runtime qualification owned by FND-05.

Scala used Temurin `21.0.12.1+1-LTS` from Eclipse Adoptium, Scala 3.3.8, sbt
1.12.11, scalafmt 3.11.5 and sbt-scalafmt 2.5.5. Setup verified the exact archive
and launcher SHA-256 before use. Format checks, clean compilation and two clean
working-directory rebuilds/runs passed. No optional compiler SDK was required.
The exact download hashes and URLs remain in
[versions.json](../../toolchains/versions.json), SHA-256
`c07b5abd45439ecee724e96a866d86e869d704f2cf2119f9553f73dca426aea3`.
Cargo.lock SHA-256 is
`2e35294914fc70ccd60dab228e8a9900184bd595fd575a8cb749a2a09d55c943`.

Twenty Python contract cases passed, including deliberate application/device/
adapter dependencies, renamed optional target dependencies, dev dependencies,
build scripts, includes/native links, symlink escapes, publication and unsafe
policy removal, pin drift, corrupted/offline downloads, missing tools and source
identity mismatch. Each negative case requires its intended diagnostic. The
check is independent of the smoke programs and was also invoked before the
actual Rust build. Documentation checked 30 files/127 local links at the tested
implementation. Documentation-only scope selects contracts, automatic workflow
paths exclude docs, and skip annotations produced no automatic broad candidate
or merge runs. No absent hardware job receives execution credit.

## Review, determinism and limits

Codex reviewed source and evidence against the architecture and ADR 0001,
independently of the smoke-output assertion. This is an agent review; it does
not claim external human approval. Manifest inspection, negative controls,
isolated tool checks and actual Cargo/linkage output agree on the core boundary.
The conservative source guard is not a hostile-code sandbox or a general future
dependency analyzer. Extending its initially empty dependency allowlist needs
explicit ownership review. No future crates, schemas or generator stubs were
introduced. One small Rust crate, one Scala source and one command interface
are proportionate; no optimization transformation or wider framework is needed.

Two clean Rust builds each took 0.111 seconds; the Scala clean/compile/run
invocations took 11.596 and 11.618 seconds. Dependency caches may be warm; setup
is measured separately. Both repeated lockfiles and declared stdout matched.
This is a tiny bootstrap reproducibility observation, not a cold-download,
byte-identical executable or production-scale performance claim. Linux x86_64
is the qualified platform. Rust container Python was 3.11; hosted Scala/contracts
Python was 3.12.3. There is no device/configuration package, schema version,
random seed or backend-emission identity in this build-only profile.

The license policy grants no project distribution license and disables package
publication. External tool notices remain upstream; no third-party binary or
restricted PDK/IP is vendored. FND-07 owns the fuller dependency/license inventory.
FND-02 owns architecture semantics, FND-05 exchange/runtime isolation, FND-06
independent reference/simulation/formal execution, and later RTL/VER tracks own
production fabric comparisons. None of those required future gates is waived
or counted as executed by this increment. All later parents remain open.

Historical failures are preserved in the [implementation checkpoint](../implementation/fnd-01-checkpoint.md):
Rust run 36225646893 exposed missing local image-tag inspection; run 36225891888
exposed rustup's installer self-update lookup. The fixes explicitly pull/inspect
the image and use the documented `--no-self-update` install option. Every original
build/isolation check remains. Controller title delay was reconciled without
duplicate dispatch. Registration/controller runs never count as qualification.

## Actual executable demonstration

The compiled [Scala source](../../frontend/scala/src/main/scala/nodalfpga/bootstrap/BootstrapSmoke.scala),
SHA-256 `e28741e2e8f91df6d06a908fb77a7af178141925194256d72c3d6c777928e4de`, is:

```scala
package nodalfpga.bootstrap

/** Compiled Scala 3 witness only; no architecture DSL or generated hardware. */
object BootstrapSmoke:
  def main(args: Array[String]): Unit =
    require(args.isEmpty, "The bootstrap smoke program takes no arguments")
    println("nodal-fpga/bootstrap/1")
    println("frontend=scala3")
    println("profile=build-only")
```

Actual output of `./nf reproduce scala`'s pinned sbt `clean compile run`:

```text
nodal-fpga/bootstrap/1
frontend=scala3
profile=build-only
```

Output SHA-256:
`74056aabefdbbe5d906f6a6b5c31a19ed841402d43b05461e847ca4aaffdd02a`.
The Rust example outputs the same identity and `profile=build-only`; its stdout
SHA-256 is `60a627efa85a969c4628f3a7f13820e8f96c00d65bffb492029f707d5529faab`.

This increment does not affect generated Verilog.

There is no HDL generator in the bootstrap. The Scala output above is the actual
smoke program result, not an architecture DSL or generated RTL demonstration.

## Acceptance mapping and documentation closure

| Checklist leaves | Evidence |
| --- | --- |
| a.1–a.2 | Minimal locked workspace; actual non-root install, formatter/linter/test commands and Rust run |
| b.1–b.2 | One pinned Scala/sbt/Temurin set; checksum setup, actual compile/run and repeats |
| c.1–c.3 | Developer ownership/license policy; forbidden controls; isolated Rust tools, graph and linkage |
| d.1–d.3 | Clean profiles; prerequisite diagnostics; exact-head dispatch/aggregate; doc-only paths and explicit skipped-lane limits |
| f.1–f.2 | Independent evidence predicates and source review; preserved Foundation/RTL/VER applicability owners |
| g.1–g.2 | Proportionate workspace review; clean repeats, matching lock/output hashes, costs and limits |
| e.1–e.3 | This retained report/artifacts, exact qualification and actual implementation merge, complete mapping and executable demonstration |

The documentation closure changes only README and `docs/` content; the entire
implementation/workflow/toolchain tree remains byte-for-byte equal to the tested
source through the verified identical-tree merge. The immediately preceding
implementation source anchor is therefore the tested commit identified above.
The closure PR records the explicit unchanged-file comparison, its own targeted
contracts result and full-scope reuse decision, document review, actual final
candidate/merge/tree and suppressed post-merge CI. It does not relabel the Rust
or Scala runs as execution on the documentation head. The checklist becomes the
accepted `dev` status only after that documentation qualification and integration.
