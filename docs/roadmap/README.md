# Nodal-FPGA incremental roadmap

This is the controlling implementation plan. Its target is a Scala architecture frontend plus a Rust device/fabric backend that can evolve from an experimental FPGA to qualified commercial families. High-end silicon remains a product-development objective, not a capability implied by this plan.

Baseline observed before this documentation change: `dev` and `main` both at `1b28e5cbcc064455a73600ab311f6f9bf071e3fc`, with only `README.md`. No implementation completion is inferred from earlier conversations.

## How to execute

Each track file contains the authoritative parent and child checkboxes. This index does not duplicate their status. Follow [progress rules](progress.md), [architecture contracts](../architecture.md), and [verification policy](../verification.md).

**Global blocker:** every non-Foundation increment requires `FND-08` complete. Other `Depends on:` entries are additional blockers. A track can proceed in parallel after its blockers clear; no track must wait for all unrelated tracks. Foundation includes minimal tests and schema fixtures so the dependency graph is not circular.

All 72 implementation increments start `[ ]`. Completing this planning commit does not complete Foundation.

## Tracks

| Track | File | Increments | Purpose |
| --- | --- | --- | --- |
| FND | [00 Foundation](tracks/00-foundation.md) | FND-01–08 | Ownership, schemas, semantics, build/test skeleton, compatibility and release gate |
| DSL | [01 Scala frontend](tracks/01-scala-frontend.md) | DSL-01–04 | Typed construction, hierarchy, portable elaboration and frontend conformance |
| DB | [02 Rust device compiler](tracks/02-device-compiler.md) | DB-01–06 | ArchIR lowering, compact database, connectivity, packaging and incremental compilation |
| LIB | [03 Reusable libraries](tracks/03-libraries.md) | LIB-01–04 | Primitive/tile/region libraries and hard-macro contracts outside core |
| RTL | [04 Fabric generation](tracks/04-fabric-rtl.md) | RTL-01–05 | Primitive RTL, routing, tiled fabric, wrappers and synthesis qualification |
| CFG | [05 Configuration](tracks/05-configuration.md) | CFG-01–05 | Logical features, physical bits, configuration loader and bitstream integrity |
| CAD | [06 External CAD integration](tracks/06-cad-integration.md) | CAD-01–06 | Yosys/nextpnr, Nodal handoff, routed-design validation and complete compilation flow |
| TMC | [07 Timing and clocking](tracks/07-timing-clocking.md) | TMC-01–04 | Clock-resource legality, timing models, multiple clocks and characterization |
| VER | [08 Verification](tracks/08-verification.md) | VER-01–07 | Independent model, formal, FABulous differential testing and coverage |
| PERF | [09 Scale and performance](tracks/09-scale-performance.md) | PERF-01–04 | Synthetic scale, memory/query budgets, CAD quality and concurrency |
| EMU | [10 FPGA emulation](tracks/10-emulation.md) | EMU-01–03 | FPGA-on-FPGA functional and runtime-configuration qualification |
| PHY | [11 Physical implementation](tracks/11-physical-implementation.md) | PHY-01–04 | PDK binding, macro hardening, physical verification and tapeout readiness |
| PROD | [12 Commercial qualification](tracks/12-commercial-qualification.md) | PROD-01–04 | Product requirements, silicon correlation, device SDK and production support |
| NAT | [13 Native CAD](tracks/13-native-cad.md) | NAT-01–04 | Optional native Rust pack/place/route, only after measured need |
| ADV | [14 Advanced families](tracks/14-advanced-families.md) | ADV-01–04 | Heterogeneous devices, regional configuration, multi-die and high-end qualification |

## Milestones, not duplicate task lists

| Milestone | Required increment completions | What the milestone establishes |
| --- | --- | --- |
| M0 Foundation release | FND-08 | Other tracks may begin |
| M1 Generated tiny fabric | DSL-04, DB-05, LIB-02, RTL-04, CFG-04, VER-03 | Scala-to-device/RTL/configuration works on a small supported profile |
| M2 Complete verified tool flow | CAD-06, CFG-05, VER-07, PERF-03 | Both supported HDL entry paths produce independently checked working configurations |
| M3 Hardware emulation | EMU-03 | Configured fabric works on the selected emulation board |
| M4 Tapeout readiness | PHY-04 | Frozen signoff/test evidence; not authorization to submit a tapeout |
| M5 Small commercial device | PROD-03 | Silicon-correlated, explicitly qualified product and supported SDK |
| M6 Advanced-family qualification | ADV-04 | Qualified advanced profile, not merely large database generation |

Milestones inherit every transitive dependency. A release cannot skip a dependency because its direct list is short.

## First-device scope

Use an illustrative `nf-tiny` reference profile: one die, one region, one user clock, LUT4 and DFF resources, a small island-style routing network, simple digital I/O wrappers, and a declared configuration protocol. Exercise 1x1, 2x2, odd-sized and boundary-heavy layouts before a nominal 16x16 profile. The 16x16 example with four LUT4s per tile has 1,024 LUT4s; it is a software test profile, not a frozen product specification or equivalent to a vendor's marketing logic-cell count.

Do not make a PLL, SERDES, analog synthesis, custom router, proprietary PDK, GUI, or commercial silicon a prerequisite for M1/M2. Product density, node, package, memory mix, I/O electrical limits and frequency targets are selected later using measured results in PROD-01.

## Dependency policy

The explicit graph in each file is authoritative. A dependency means its parent increment is fully complete, not merely that one convenient sub-item is done. Experiments on blocked tracks may be recorded as experiments, but cannot be checked off as completed production work. Changes to blockers require a documented rationale and cycle check.

The principal progression is Foundation → frontend/device/library work → fabric/configuration/CAD → independent verification → emulation and physical implementation → silicon/product qualification. Timing and performance begin early and feed this progression; they are not postponed until the device becomes large.

## Deliberately deferred work

Do not initially build another MLIR stack, arbitrary RTL synthesis, analog layout synthesis, a general GDS editor, a commercial IDE, multi-die routing, a custom crypto primitive, or a universal automatic PDK port. Define narrow contracts and explicit unsupported-feature diagnostics instead. Native CAD is optional; a production-qualified external engine may remain the backend.

## Evidence and research

The [source register](../sources.md) separates capabilities documented by FABulous, OpenFPGA, nextpnr, VTR and formal tools from this project's design proposals. Published tool features are not acceptance evidence for Nodal-FPGA. Pin and qualify the exact versions used for implementation.
