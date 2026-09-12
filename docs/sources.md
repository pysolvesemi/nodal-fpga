# Research sources and evidence limits

Primary sources checked for this planning revision on 2026-09-13. Documentation using `latest`, `master` or `main` is moving evidence, not a reproducible toolchain pin. FND-07 and VER-05 must select immutable revisions before using tools as qualification references. The architecture choices and roadmap targets are recommendations, not claims of implemented Nodal-FPGA features.

## S1

FABulous project, [Simulation setup](https://fabulous.readthedocs.io/en/latest/user_guide/simulation/simulation.html). Documents compiling a test design through synthesis/P&R/bitstream generation and exercising the configured fabric RTL. This establishes a useful end-to-end validation pattern, not exhaustive proof of all configurations.

## S2

FABulous project, [Gate-level simulation](https://fabulous.readthedocs.io/en/v2.0.0/user_guide/simulation/gate_level_simulation.html). Describes replacing the inner fabric/tile models with post-P&R netlists while retaining behavioral wrapper/controller portions. Do not label such mixed-level simulation as whole-chip signoff or assume SDF timing coverage without inspecting the actual run.

## S3

OpenFPGA project, [Documentation index and design-flow/manual sections](https://openfpga.readthedocs.io/en/master/). Documents distinct fabric, bitstream, configuration-protocol, testbench and regression concepts. Used as another architecture/configuration reference, not as evidence that a generated Nodal device is correct.

## S4

YosysHQ, [nextpnr Architecture API](https://github.com/YosysHQ/nextpnr/blob/main/docs/archapi.md). Describes architecture-provided BEL/wire/PIP/pin and related query interfaces. Supports treating nextpnr integration as an explicit architecture adapter rather than assuming arbitrary JSON is sufficient.

## S5

YosysHQ, [nextpnr README](https://github.com/YosysHQ/nextpnr) and [Viaduct documentation](https://github.com/YosysHQ/nextpnr/blob/main/docs/viaduct.md). Documents generic and Himbächel architecture paths and the C++ Viaduct harness. Used for the staged adapter decision; no particular backend is assumed to meet Nodal's future scale target before benchmarking.

## S6

Verilog-to-Routing project, [Architecture Reference](https://docs.verilogtorouting.org/en/latest/arch/reference/). Describes resource models, timing annotations, hierarchy/layout, NoC and multi-die layout concepts. Used to avoid a LUT-only or single-grid schema. Description support is not a substitute for evaluating physical feasibility and CAD quality.

## S7

FPGA Interchange project, [Format documentation](https://fpga-interchange-schema.readthedocs.io/). A relevant existing boundary for device resources and logical/physical netlists. Assess coverage, licensing and version compatibility before adopting or extending its schema.

## S8

YosysHQ, [SymbiYosys documentation](https://yosyshq.readthedocs.io/projects/sby/en/latest/). Describes bounded/unbounded safety verification, cover and liveness workflows. Proof claims in this project must state assumptions, supported models and whether the result is bounded or unbounded.

## S9

YosysHQ, [EQY documentation](https://yosyshq.readthedocs.io/projects/eqy/en/latest/). Describes Yosys-based equivalence checking, partitioning and X-propagation considerations. Relevant to primitive/configured-fabric/netlist equivalence, not analog signoff.

## Interpretation rules

FABulous comparisons are differential evidence only. Cross-tool agreement can share bugs or assumptions. Exact bytes, placement, timing and resource counts are comparable only under an explicitly matched architecture and encoding contract. A configured fabric can be behaviorally equivalent with different routing and bitstream bytes.

No fixed tapeout count, maximum FABulous device size, guaranteed clock performance, universally synthesizable analog HDL, universal commercial SystemVerilog support, or automatic high-end FPGA capability is assumed by this plan. Physical verification, qualified models, silicon characterization, production test and product support remain separate acceptance obligations.
