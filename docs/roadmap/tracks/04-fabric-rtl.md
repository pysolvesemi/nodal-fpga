# Fabric RTL generation track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `compiler/rust/fabric-rtl`, `library/rtl`, `devices/reference/nf-tiny` and simulation fixtures. Generated fabric RTL implements the programmable silicon; it is not the customer's mapped design RTL.

- [ ] RTL-01 — Structured primitive emission
  Depends on: LIB-01, DB-02.
  - [ ] RTL-01.a Implement a structured Verilog emission layer with explicit widths, signedness, identifier handling and deterministic ordering.
  - [ ] RTL-01.b Generate LUT4, DFF and mux instances from primitive contracts, not ad-hoc textual reconstruction of source expressions.
  - [ ] RTL-01.c Preserve hierarchy and source/configuration correspondence in a sidecar manifest.
  - [ ] RTL-01.d Run lint, simulator checks and primitive assertions across parameter boundaries and invalid-mode rejection.
  - [ ] RTL-01.e Record source/IR, actual emitted Verilog, generation hashes and final-head test results.

- [ ] RTL-02 — Switch matrices and tile connectivity
  Depends on: RTL-01, DB-03.
  - [ ] RTL-02.a Generate tile interfaces, configurable mux networks, fixed links and declared shared-control logic from resolved connectivity.
  - [ ] RTL-02.b Handle edges, corners, unused resources and sparse exceptions without implicit zero-width or out-of-range constructs.
  - [ ] RTL-02.c Emit an auditable correspondence between resource IDs, RTL endpoints and logical configuration features.
  - [ ] RTL-02.d Compare generated connectivity to independent small-graph fixtures; inject port/mux swaps and check detection.
  - [ ] RTL-02.e Record tile-level simulation and structural consistency evidence with actual generated RTL.

- [ ] RTL-03 — Hierarchical fabric assembly
  Depends on: RTL-02, LIB-02, DB-04, CFG-02, TMC-01.
  - [ ] RTL-03.a Instantiate tile/region templates, global connections, user clocks and configuration interfaces hierarchically.
  - [ ] RTL-03.b Keep configuration and user-clock domains distinct and define safe quiescent behavior before configuration activation.
  - [ ] RTL-03.c Produce resource/RTL/configuration manifests bound to the same immutable device build.
  - [ ] RTL-03.d Simulate hand-configured tiny fabrics and boundary-heavy variants; check every declared endpoint and config reference.
  - [ ] RTL-03.e Record complete tiny-fabric outputs and final-head assembly checks; no synthesis/P&R-flow claim yet.

- [ ] RTL-04 — Runtime configuration and top-level wrapper
  Depends on: RTL-03, CFG-03.
  - [ ] RTL-04.a Connect the real configuration loader to the fabric and add clock/reset/I/O wrappers for simulation and emulation.
  - [ ] RTL-04.b Specify activation, reset, partial-load interruption and safe output behavior without assuming SRAM powers up cleared.
  - [ ] RTL-04.c Separate test-only preload shortcuts from the real configuration-interface mode in build metadata.
  - [ ] RTL-04.d Load known configurations through the interface and test reset during loading, malformed input and output containment.
  - [ ] RTL-04.e Record runtime-loaded fabric behavior, actual generated RTL and final-head wrapper/loader evidence.

- [ ] RTL-05 — Synthesis-safe fabric qualification
  Depends on: RTL-04, VER-03, TMC-02.
  - [ ] RTL-05.a Run the intended ASIC synthesis front end on the generated fabric with declared clock/reset/configuration constraints.
  - [ ] RTL-05.b Check unintended latch/loop inference, unsupported constructs and preservation of required programmable resources.
  - [ ] RTL-05.c Compare synthesized primitive/tile implementations to RTL with explicit initialization and black-box assumptions.
  - [ ] RTL-05.d Run representative post-synthesis configured-fabric tests and audit missing or unconstrained timing paths.
  - [ ] RTL-05.e Record netlist/RTL hashes, equivalence scope, timing limitations and final-head qualification evidence.

Main risk: an emitter and DeviceDB agreeing on the same incorrect source interpretation. Independent validation is mandatory. Do not flatten every device or preserve all resources blindly with synthesis directives without checking the physical consequences.
