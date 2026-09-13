# Fabric RTL generation track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `compiler/rust/fabric-rtl`, `library/rtl`, `devices/reference/nf-tiny` and simulation fixtures. Generated fabric RTL implements the programmable silicon; it is not the customer's mapped design RTL.

Backend policy: keep a focused structured Rust emitter behind a small hardware-emission interface, with no required MLIR/CIRCT dependency. [ADR 0001](../../adr/0001-optional-circt-backend.md) permits an isolated optional backend, controlled by the [CIR track](15-compiler-backend-evaluation.md). None of RTL-01–05 depends on that track. Perform CIR-01's alternatives review before expanding the emitter into a general HDL parser/compiler/optimizer; that scope review may retain the baseline without a CIRCT prototype. Both paths must preserve supported configuration semantics, not specialize the manufactured fabric to an example bitstream.

Early comparisons are required under [the baseline contract](../../verification-early-baseline.md); reuse Foundation fixtures without waiting for VER-05. Static unit checks in RTL-01–03 cannot satisfy the real-loader gate in RTL-04. No new dependency on the blocked VER track is introduced.

- [ ] RTL-01 — Structured primitive emission
  Depends on: LIB-01, DB-02.
  - [ ] RTL-01.a Implement a structured Verilog emission layer with explicit widths, signedness, identifier handling and deterministic ordering; expose a small backend-neutral interface without creating a second general HDL compiler.
  - [ ] RTL-01.b Generate LUT4, DFF and mux instances from primitive contracts, not ad-hoc textual reconstruction of source expressions.
  - [ ] RTL-01.c Preserve hierarchy and source/configuration correspondence in a sidecar manifest.
  - [ ] RTL-01.d Run lint, simulator checks and primitive assertions across parameter boundaries and invalid-mode rejection; compare actual emitted LUT/register/mux behavior to independent expected semantics and the pinned FABulous common subset, including configuration-index and control-priority mutations.
  - [ ] RTL-01.e Record source/IR, actual emitted Verilog, generation hashes and final-head test results, including reference revisions, assumption IDs, correspondence maps and mismatches. Missing required primitive comparisons block closure; do not defer them to VER-05.

- [ ] RTL-02 — Switch matrices and tile connectivity
  Depends on: RTL-01, DB-03.
  - [ ] RTL-02.a Generate tile interfaces, configurable mux networks, fixed links and declared shared-control logic from resolved connectivity.
  - [ ] RTL-02.b Handle edges, corners, unused resources and sparse exceptions without implicit zero-width or out-of-range constructs.
  - [ ] RTL-02.c Emit an auditable correspondence between resource IDs, RTL endpoints and logical configuration features.
  - [ ] RTL-02.d Compare actual generated switches/tile connectivity and configured behavior to independent small-graph fixtures and matched FABulous-generated resources; check endpoint/pin maps, fixed/configurable directions and mux exclusions, and require detection of port/mux swaps and faulty correspondence maps.
  - [ ] RTL-02.e Record tile-level simulation and structural consistency evidence with both actual generated RTL sets, common-subset/correspondence hashes and mutation outcomes; resolve matched-subset disagreements before closure, not merely equal resource counts.

- [ ] RTL-03 — Hierarchical fabric assembly
  Depends on: RTL-02, LIB-02, DB-04, CFG-02, TMC-01.
  - [ ] RTL-03.a Instantiate tile/region templates, global connections, user clocks and configuration interfaces hierarchically.
  - [ ] RTL-03.b Keep configuration and user-clock domains distinct and define safe quiescent behavior before configuration activation.
  - [ ] RTL-03.c Produce resource/RTL/configuration manifests bound to the same immutable device build.
  - [ ] RTL-03.d Simulate hand-configured tiny fabrics and boundary-heavy variants; check every declared endpoint and config reference against independent expectations, and compare both actual generated fabrics for the declared FABulous common subset. Exercise 1x1, 2x2 and odd/asymmetric cases where supported; disclose unmatched shapes and test them independently rather than silently dropping them.
  - [ ] RTL-03.e Record complete tiny-fabric outputs, configuration/state correspondence and final-head assembly comparisons; distinguish static unit setup from runtime loading, and retain counterexamples and unsupported-feature dispositions. No complete loader, synthesis/P&R or all-configurations-proof claim is made here.

- [ ] RTL-04 — Runtime configuration and top-level wrapper
  Depends on: RTL-03, CFG-03.
  - [ ] RTL-04.a Connect the real configuration loader to the fabric and add clock/reset/I/O wrappers for simulation and emulation.
  - [ ] RTL-04.b Specify activation, reset, partial-load interruption and safe output behavior without assuming SRAM powers up cleared.
  - [ ] RTL-04.c Separate test-only preload shortcuts from the real configuration-interface mode in build metadata.
  - [ ] RTL-04.d Load known configurations through the real interface and test reset during loading, malformed input and output containment; run a hand-configured differential corpus through each fabric's actual loader, compare after each declared activation/reset sequence, and switch between unrelated designs. Test unequal load latencies and declared unmatched startup behavior without hiding failures with forced initialization.
  - [ ] RTL-04.e Record runtime-loaded fabric behavior, both generated outputs, transport/configuration mappings and final-head wrapper/loader evidence. Hierarchical force, memory preload or hardwired-bitstream shortcuts cannot satisfy this gate; complete CAD-flow comparison remains VER-05.

- [ ] RTL-05 — Synthesis-safe fabric qualification
  Depends on: RTL-04, VER-03, TMC-02.
  - [ ] RTL-05.a Run the intended ASIC synthesis front end on the generated fabric with declared clock/reset/configuration constraints.
  - [ ] RTL-05.b Check unintended latch/loop inference, unsupported constructs and preservation of required programmable resources across supported legal configurations, not only a fixed customer design.
  - [ ] RTL-05.c Compare synthesized primitive/tile implementations to RTL with explicit initialization and black-box assumptions.
  - [ ] RTL-05.d Run representative post-synthesis configured-fabric tests and audit missing or unconstrained timing paths.
  - [ ] RTL-05.e Record netlist/RTL hashes, equivalence scope, timing limitations and final-head qualification evidence.

Main risk: an emitter and DeviceDB agreeing on the same incorrect source interpretation. Independent validation is mandatory. Do not flatten every device or preserve all resources blindly with synthesis directives without checking the physical consequences.
