# Timing and clocking track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `core/rust/timing-schema`, device clock-resource data, external timing adapters and characterization scripts. The first version may use external timing engines; a native STA implementation is not a prerequisite.

- [ ] TMC-01 — Timing and clock-resource contracts
  Depends on: FND-08.
  - [ ] TMC-01.a Define clock sources, buffers, muxes, capacity, region reach and legal dedicated connectivity separately from customer clock domains.
  - [ ] TMC-01.b Define arc kinds, units, min/max behavior, transitions, conditional modes and explicit unknown/uncharacterized values.
  - [ ] TMC-01.c Bind timing sets to device implementation revisions and corners; identify estimated values as estimates.
  - [ ] TMC-01.d Test illegal clock connectivity, missing clocks/arcs, unit errors and corner/revision mismatches on tiny fixtures.
  - [ ] TMC-01.e Record contract tests and supported single-clock assumptions with final-head evidence.

- [ ] TMC-02 — First-device timing and constraint validation
  Depends on: TMC-01, CAD-03.
  - [ ] TMC-02.a Feed declared timing into the selected P&R backend and implement basic clock/I/O constraints and path reporting.
  - [ ] TMC-02.b Check setup and hold/min paths, clock-to-Q, I/O paths and applicable recovery/removal rather than reporting only estimated Fmax.
  - [ ] TMC-02.c Diagnose unconstrained paths and unsupported exceptions; never interpret absent timing as zero delay or closure.
  - [ ] TMC-02.d Compare simple hand-calculated paths and independent engine results with stated model/rounding tolerances.
  - [ ] TMC-02.e Record timing coverage, violated constraints and final-head test evidence; label non-silicon-calibrated timing clearly.

- [ ] TMC-03 — Multiple clocks and heterogeneous resources
  Depends on: TMC-02, LIB-03.
  - [ ] TMC-03.a Add generated clocks, regional resources, clock enables and shared-control legality for memory/DSP/PLL interfaces.
  - [ ] TMC-03.b Define supported clock-domain relations, asynchronous boundaries and CDC/RDC handoff requirements.
  - [ ] TMC-03.c Validate clock placement/routing capacity, source eligibility and legal mux switching assumptions.
  - [ ] TMC-03.d Test multi-clock fixtures, missing generated-clock constraints, illegal region crossings and resource overcommit.
  - [ ] TMC-03.e Record supported clock/macro modes and final-head legality/timing evidence; analog lock/jitter characterization remains separate.

- [ ] TMC-04 — Physical and silicon-correlatable characterization
  Depends on: TMC-03, PHY-02.
  - [ ] TMC-04.a Extract or measure primitive, switch, wire and clock behavior for selected physical implementations and PVT corners.
  - [ ] TMC-04.b Generate versioned timing models with load/slew assumptions, min/max bounds and characterized-versus-estimated provenance.
  - [ ] TMC-04.c Build correlation circuits and a procedure for later silicon measurement, uncertainty and conservative model updates.
  - [ ] TMC-04.d Compare routed/STA predictions to extracted simulation; record tolerances, outliers and unsupported corners.
  - [ ] TMC-04.e Record final-head characterization coverage and model hashes; do not claim silicon correlation before PROD-02.

Main risk: synthetic nominal delays being mistaken for product timing guarantees. Do not freeze speed grades or claim STA proves analog jitter/CDC correctness.
