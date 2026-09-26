# FND-01 durable checkpoint

Phase: implementation prepared; canonical Rust/Scala qualification remains open.
Repository: `pysolvesemi/nodal-fpga`.
Target: `dev` at `cd6ec64e7f25e60ac4277159b76279c08d5d8210`.
Feature: `increment/fnd-01-bootstrap`.
Scope: [readiness review](fnd-01-readiness.md) and Foundation FND-01 only.

An interactive worker is currently implementing this increment. Before automated
writes, inspect the latest PR checkpoint and refs for current activity. Preserve
ancestry and do not create a second worker branch, PR or monitor.

The minimal Rust/Scala source, developer commands, ownership checks and focused
workflow are prepared. Twenty Python contract/negative-control tests pass locally;
29 documentation files/126 local links and workflow YAML/trigger structure were
checked. These local checks do not qualify the canonical toolchains. The initial
Scala probe hit an unavailable IPC socket. After using sbt's supported
`sbt.server.forcestart` fallback and disabling server autostart for that local
probe, pinned sbt/Scala/scalafmt compiled and ran the smoke program on ambient
JDK 17. That result is noncanonical; pinned JDK 21 and Rust execution remain
unverified. No remote CI has run. All checklist boxes remain open pending their
own evidence. See [local review](fnd-01-local-review.md).
Next: publish the clean source candidate and inspect actual workflow registration
before dispatching only contracts, Rust and Scala targeting. Retain initial failures
and qualify canonical JDK/Rust execution rather than counting local review as CI. Main and other increments remain
outside scope. This file will be refreshed with candidate identities and evidence
as work progresses.
