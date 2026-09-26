# FND-01 durable checkpoint

Phase: targeted CI repair; Rust qualification remains open.
Repository: `pysolvesemi/nodal-fpga`.
Target: `dev` at `cd6ec64e7f25e60ac4277159b76279c08d5d8210`.
Feature: `increment/fnd-01-bootstrap`.
Scope: [readiness review](fnd-01-readiness.md) and Foundation FND-01 only.

An interactive worker is currently qualifying this increment. Before automated
writes, inspect the latest PR checkpoint and refs for current activity. Preserve
ancestry and do not create a second worker branch, PR or monitor.

The first candidate was `5b13c40f820952434d406d3e4d9ed50e22dde772`, tree
`9ee303a536ac50aa81cbd758a26fc3dcfc4c127c`. Its exact-head remote targeting used
workflow ID `367539769`, path `.github/workflows/fnd-01-bootstrap.yml`, definition
blob `f0113e4cdefb72a759745e34ee2b2bd8754057a5`:

| Lane | Run / attempt | Result |
| --- | --- | --- |
| Contracts | [36225641325 / 1](https://github.com/pysolvesemi/nodal-fpga/actions/runs/36225641325) | Passed 20 controls and document checks; selected aggregate passed |
| Rust | [36225646893 / 1](https://github.com/pysolvesemi/nodal-fpga/actions/runs/36225646893) | Image built, then inspection failed because the base tag was not in Docker's local image store; Rust execution did not start |
| Scala | [36225651406 / 1](https://github.com/pysolvesemi/nodal-fpga/actions/runs/36225651406) | Exact Temurin 21.0.12.1+1, sbt 1.12.11 and Scala 3.3.8; format/compile and two clean repeats passed |

Rust repair: explicitly pull and inspect the base image, then build and inspect
the resulting image. Preserve the base digest/build logs and all existing checks.
The shared workflow definition changes, so fresh contracts, Rust and Scala
targeting is required on the repair head; prior successes remain historical.
No full qualification, integration or checklist closure is claimed.

Read-only registration run `36225216557` established the workflow after discovery
run `36225086334` found it unregistered. Isolated controller run `36225633141`
dispatched the three runs on the exact candidate; controllers are not test credit.
The single hourly continuation is enabled for CI monitoring. The live `dev`
branch reports protection disabled and no required contexts; the separate
protection API is inaccessible to the connector. Recheck live state before merge.

Next: publish this focused repair with `[skip ci]`, record its SHA/tree and workflow
blob in PR #1, and dispatch through a new controller identity pinned to that head.
After targeting passes, inventory the full required set and reuse only qualifying
same-head runs. Inspect artifacts, finish independent review and completion evidence,
then verify integration. Main and other increments remain outside scope.

The [local review](fnd-01-local-review.md) retains the earlier noncanonical JDK 17
probe and its limits. This increment does not affect generated Verilog.
