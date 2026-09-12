# Reusable primitive, tile and macro libraries

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `library/{scala,rtl,contracts}`, reference devices and `adapters/macros`. Core must not import these libraries.

- [ ] LIB-01 — Primitive semantic contracts
  Depends on: FND-08.
  - [ ] LIB-01.a Specify LUT4, DFF, mux, constant and simple I/O behavior, including bit ordering, reset/initial state and invalid selections.
  - [ ] LIB-01.b Package abstract pins, modes, configuration features and independent expected-value vectors for each primitive.
  - [ ] LIB-01.c Define extension/version rules and distinguish configurability from physical realization as standard cells or hard macros.
  - [ ] LIB-01.d Test truth tables and transition contracts independently of the fabric generator and configuration encoder.
  - [ ] LIB-01.e Record reviewed specifications, independent vectors and final-head contract validation.

- [ ] LIB-02 — Reusable tiles, routing patterns and nf-tiny
  Depends on: LIB-01, DSL-02.
  - [ ] LIB-02.a Implement Scala library constructors for logic tiles, terminal/I/O tiles, routing patterns and reference regions.
  - [ ] LIB-02.b Compose nf-tiny profiles without adding device-specific branches to core.
  - [ ] LIB-02.c Provide explicit parameter limits, shared-control rules and expected boundary connectivity for each generator.
  - [ ] LIB-02.d Test 1x1, 2x2, odd dimensions, sparse holes and parameter variations through the frontend contract.
  - [ ] LIB-02.e Record reusable-library examples, generated ArchIR and final-head composition tests.

- [ ] LIB-03 — Carry, memories and DSP library contracts
  Depends on: LIB-02.
  - [ ] LIB-03.a Add carry-chain and DSP semantic models, signedness/width rules, cascade connectivity and configuration modes.
  - [ ] LIB-03.b Define RAM capacities, port modes, byte enables, latency, initialization and same-/mixed-port collision semantics.
  - [ ] LIB-03.c Separate simulation, FPGA-emulation and ASIC macro implementations with capability-checked binding.
  - [ ] LIB-03.d Verify arithmetic corners and memory collision/initialization modes; reject modes unsupported by the selected implementation.
  - [ ] LIB-03.e Publish qualified library contracts and final-head tests without claiming missing hard macros exist.

- [ ] LIB-04 — Hard digital and mixed-signal macro integration
  Depends on: LIB-03, TMC-03, PHY-01.
  - [ ] LIB-04.a Implement macro manifests for interface, legal settings, power/reset sequencing, clocks, footprint and configuration mapping.
  - [ ] LIB-04.b Bind simulation, LEF/GDS, timing and analog characterization views with exact revisions and access/redistribution constraints.
  - [ ] LIB-04.c Add a mock PLL integration fixture with legal-divider solving and lock/reset behavior; keep real analog-IP availability explicit.
  - [ ] LIB-04.d Test missing/mismatched views, illegal reference/VCO/output ranges and unsafe clock/startup use against declared macro contracts.
  - [ ] LIB-04.e Record integration evidence and limitations; a behavioral macro model alone cannot satisfy silicon qualification.

Main risk: treating every resource as an undifferentiated RTL black box. Do not develop transistor-level PLL/SERDES design or analog physical synthesis inside this track.
