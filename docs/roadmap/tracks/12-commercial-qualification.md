# Silicon and commercial-product qualification track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: product profiles, characterization/test plans, release SDK metadata and compatibility tests. Commercial-grade is an evidence-backed claim for a specific device/process/package/tool combination.

[Track 16](16-dft-manufacturing-test.md) owns the pre-silicon manufacturing-test package and the DFT-06/07 external qualification gates. Reuse their immutable evidence rather than duplicate tests. These post-silicon gates consume real measurements from labs/manufacturing partners; instrument purchasing, facility booking, fabrication/package procurement and factory operation are not software implementation increments. Preparation and tester-interface feasibility must already be addressed before tapeout.

- [ ] PROD-01 — Freeze a measured first-product target
  Depends on: FND-08.
  - [ ] PROD-01.a Define customer workloads, acceptable cost/power/performance, lifetime, package/I/O and support requirements before choosing a product profile.
  - [ ] PROD-01.b Separate nf-tiny research fixtures from the candidate NF1 product and select density/resource mix using measured feasibility evidence.
  - [ ] PROD-01.c Identify hard-IP availability, supply/manufacturing/test dependencies, reliability objectives and configuration security threat model.
  - [ ] PROD-01.d Review requirement traceability, unsupported use cases and a realistic characterization/production-test matrix aligned with the DFT-01 fault/access and tester-capability contract; identify external evidence owners without authorizing equipment or manufacturing expenditure.
  - [ ] PROD-01.e Record an approved product requirements baseline with explicit unknowns; do not advertise guessed frequency, yield or cost.

- [ ] PROD-02 — Silicon bring-up and model correlation
  Depends on: PROD-01, PHY-04, DFT-06.
  - [ ] PROD-02.a On actual fabricated samples, establish power/reset/test access and verify configuration and basic resource functionality.
  - [ ] PROD-02.b Reuse simulation/emulation corpus IDs for logic, routing, memories, clocks and supported hard-macro tests, and consume DFT-06 actual-silicon scan/storage/fabric correlation and raw-result references. Retain separate scope for broader timing/power/PVT characterization.
  - [ ] PROD-02.c Measure relevant PVT, timing, power and failure behavior across a justified sample/test matrix.
  - [ ] PROD-02.d Correlate predictions with silicon, record uncertainty/outliers and revise models or errata without concealing failures.
  - [ ] PROD-02.e Record measured silicon evidence and qualified operating limits; this increment remains open until physical samples are actually tested.

- [ ] PROD-03 — Small commercial device and SDK release gate
  Depends on: PROD-02, TMC-04, CAD-06, PERF-04, DFT-07.
  - [ ] PROD-03.a Finalize characterized device/package/speed-grade datasets and production test/binning rules with manufacturing partners.
  - [ ] PROD-03.b Package supported device databases, bitstream/programmer libraries, models, constraints and documented interfaces for nodal-eda.
  - [ ] PROD-03.c Establish qualified tool/OS compatibility, distribution provenance, license/IP review and device errata/support documentation.
  - [ ] PROD-03.d Consume the DFT-07 device/process/package/tester-qualified production-test decision and independently validate broader reliability and release requirements against the approved evidence matrix. Modeled fault coverage, observed yield/escapes and reliability qualification remain separate claims.
  - [ ] PROD-03.e Record the exact commercial qualification scope and release decision; missing mandatory evidence blocks the commercial label.

- [ ] PROD-04 — Long-lived compatibility and field-support baseline
  Depends on: PROD-03.
  - [ ] PROD-04.a Establish archived device/toolchain packages, reproducible customer testcase capture and long-term bitstream compatibility tests.
  - [ ] PROD-04.b Add revision-aware programming safeguards, errata/model distribution and recovery procedures for supported devices.
  - [ ] PROD-04.c Define vulnerability, field-failure and regression-response processes without storing user secrets in shared artifacts.
  - [ ] PROD-04.d Exercise a model-update/rollback and historical-design rebuild through the supported release workflow.
  - [ ] PROD-04.e Record the tested support-process baseline; ongoing field operations continue after this finite setup increment completes.

Main risk: declaring a research tapeout a supported commercial product. Core software scalability does not establish yield, reliability, test coverage, IP rights or customer support capability.
