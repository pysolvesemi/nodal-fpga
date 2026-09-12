# Yosys, nextpnr and Nodal-HDL integration track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `adapters/{yosys,nextpnr}`, `core/rust/design-db`, headless CLI, mapped/routed interchange schemas. External engines provide initial synthesis/pack/place/route. No MLIR runtime dependency enters core.

- [ ] CAD-01 — Customer-design interchange and primitive models
  Depends on: LIB-01.
  - [ ] CAD-01.a Implement mapped cells/nets/ports/constants/modes with clock, constraint and source-provenance metadata.
  - [ ] CAD-01.b Define Yosys simulation/technology models for supported primitive modes and a strict capability manifest.
  - [ ] CAD-01.c Specify how Nodal-HDL and other producers identify target/device/library versions without sharing compiler internals.
  - [ ] CAD-01.d Test width/signedness/constants, unknown cells, illegal modes, multiple-driver handling and unsupported constraint rejection.
  - [ ] CAD-01.e Record interchange conformance and the exact supported HDL/netlist subset on the final head.

- [ ] CAD-02 — Yosys synthesis and technology mapping
  Depends on: CAD-01.
  - [ ] CAD-02.a Implement pinned synthesis scripts, primitive techmaps and netlist import for the initial logic/register profile.
  - [ ] CAD-02.b Preserve reset/enable/initialization semantics and report resources not inferable or supported.
  - [ ] CAD-02.c Add synthesis-stage functional/equivalence checks independent of later placement/routing.
  - [ ] CAD-02.d Test counters, muxes, arithmetic and register controls with boundary widths and deliberately unsupported constructs.
  - [ ] CAD-02.e Record mapped netlists, tool options and final-head synthesis evidence; do not claim complete SystemVerilog/VHDL support.

- [ ] CAD-03 — nextpnr architecture adapter
  Depends on: CAD-02, DB-04, RTL-03.
  - [ ] CAD-03.a Evaluate generic versus Himbächel/full-architecture integration and record a measured adapter decision.
  - [ ] CAD-03.b Implement required BEL/pin/wire/PIP queries, timing hooks, packing legality and device database translation.
  - [ ] CAD-03.c Contain necessary C++/Python glue under the adapter; preserve core schema independence and pin exact upstream revisions.
  - [ ] CAD-03.d Route tiny examples and check site modes, shared controls, pin maps, dedicated links and unroutable-case diagnostics.
  - [ ] CAD-03.e Record exported graph correspondence and successful/negative P&R evidence on the final head.

- [ ] CAD-04 — Independent route validation and complete Verilog path
  Depends on: CAD-03, CFG-04.
  - [ ] CAD-04.a Import placements/routes into a backend-neutral checkpoint bound to the correct device package.
  - [ ] CAD-04.b Independently check endpoint reachability, capacity, occupancy, mutually exclusive PIPs, legal modes and clock-resource use.
  - [ ] CAD-04.c Connect synthesis → nextpnr → route validation → logical configuration → bitstream → runtime-loaded fabric simulation.
  - [ ] CAD-04.d Compare supported reference designs to their original RTL and reject intentionally corrupted placement/route/configuration outputs.
  - [ ] CAD-04.e Record a reproducible end-to-end corpus, actual fabric/user outputs and final-head legality/functionality evidence.

- [ ] CAD-05 — Nodal-HDL producer integration
  Depends on: CAD-04, DSL-03.
  - [ ] CAD-05.a Implement the Nodal-HDL-to-mapped-design adapter through a versioned file/API boundary; leave MLIR ownership in nodal-hdl.
  - [ ] CAD-05.b Preserve source and hierarchy correspondence and define primitive binding/constraint semantics with the producer.
  - [ ] CAD-05.c Provide a qualified generated-Verilog-through-Yosys fallback when native mapping is unavailable; label the selected path explicitly.
  - [ ] CAD-05.d Compare equivalent Nodal and Verilog designs at mapped semantics and configured-fabric outputs; test version mismatches.
  - [ ] CAD-05.e Record real producer versions, supported paths and final-head integration evidence; a stub importer does not complete this increment.

- [ ] CAD-06 — Reproducible user-flow qualification
  Depends on: CAD-05, VER-04, TMC-02, PERF-02.
  - [ ] CAD-06.a Add structured commands/reports/checkpoints for both qualified frontend paths without introducing nodal-eda project/UI logic.
  - [ ] CAD-06.b Record dependency hashes, options, seed/worker policy, diagnostics, constraints and artifact lineage for every stage.
  - [ ] CAD-06.c Add clean replay and invalidation tests; reject timing or legality failures instead of quietly issuing a success bitstream.
  - [ ] CAD-06.d Qualify the regression corpus across supported toolchain/device combinations with routability and timing reports.
  - [ ] CAD-06.e Publish the exact support matrix and final-head evidence; identify any open quality or scalability limitations.

Main risk: assuming nextpnr automatically understands a new DeviceDB or assuming MLIR alone provides technology mapping. Defer generic native synthesis and GUI orchestration. See [S4/S5](../../sources.md#s4) for actual nextpnr architecture integration requirements.
