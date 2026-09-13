# Architecture and repository boundaries

## Core decision

Use a Scala architecture-construction frontend and a Rust architecture/device compiler. Exchange a versioned, language-neutral description rather than live Scala, Rust or MLIR objects. Scala performs typed construction, reusable generation and source-aware elaboration. Rust independently validates the exchange format and owns lowering, large-resource processing and compiled artifacts.

The canonical contract is the schema and its conformance tests, not one language's private object layout. Scala and Rust frontends must describe identical semantics. Scala must preserve repeated templates and hierarchy rather than expanding millions of resources before handoff.

```text
Scala architecture DSL ----> ArchIR package <---- Rust builder
                                    |
                         Rust device compiler
                                    |
                   resolved semantic device model
                    /              |              
              fabric RTL       DeviceDB       configuration map
                  |                |                |
         external ASIC flow        +-----+----------+
                  |                      |
                 GDS              FPGA implementation
                                         ^
nodal-hdl (existing MLIR) --> mapped-design contract
Yosys / other qualified synthesis --> same contract
```

Keep generic HDL compilation and MLIR in `nodal-hdl`. MLIR is not required by `nodal-fpga`; Rust can interoperate with other languages, so this is an ownership decision, not a claim of language incompatibility. Initial Yosys/nextpnr adapters implement the customer flow. `nodal-eda` owns projects, UI and whole-product orchestration; this repository provides headless APIs and commands, not a second IDE.

## Optional compiler backends

[ADR 0001](adr/0001-optional-circt-backend.md) records the selected Scala/Rust core and the evidence-gated CIRCT option. Default architecture compilation, fabric RTL emission and device tooling require no additional LLVM/MLIR/CIRCT SDK or application linkage. This does not exclude LLVM components used internally by the ordinary Rust compiler toolchain.

Keep the initial emitter focused and structured. A separate adapter may consume a bounded hierarchical hardware-emission contract and invoke CIRCT for RTL generation or supplemental verification. It must not replace ArchIR, DeviceDB, the configuration model or the mapped-customer-design handoff, nor expose live MLIR objects through core APIs. Preserve templates rather than forcing full routing-graph expansion.

The [CIR track](roadmap/tracks/15-compiler-backend-evaluation.md) separates alternatives review, comparative prototype and conditional opt-in qualification. Review alternatives before extending the emitter into a general HDL compiler; do not make the optional experiment a prerequisite for the initial fabric or existing milestones. Adoption requires configuration-preserving correctness, measured benefit and dependency isolation. A selected backend must retain provenance and declared configuration semantics; an unavailable or unsupported backend fails explicitly rather than silently falling back.

## Proposed directory structure

These are intended boundaries, not a claim that the directories or implementations already exist. Start with only the modules needed for the active increment.

```text
core/rust/
  types/                   typed units, IDs, diagnostics
  arch-ir/                 portable semantic architecture model
  device-db/               immutable compiled device queries
  design-db/               mapped cells/nets and separate CAD state
  config-schema/           logical configuration contracts
  timing-schema/           timing/clock model contracts
compiler/rust/
  arch-compiler/           validation, lowering, partition compilation
  fabric-rtl/              structured Verilog generation
  config-compiler/         semantic features to physical addresses
frontend/scala/
  api/                     typed architecture construction API
  elaboration/             templates, hierarchy, provenance
  emit/                    ArchIR serialization, not RTL generation
  cli/                     architecture author commands
library/
  scala/primitives/        reusable primitive constructors
  scala/tiles/             reusable tile/routing generators
  scala/regions/           reusable region/clock generators
  rtl/                     reviewed primitive implementations
  contracts/               primitive/mode/configuration specifications
adapters/
  yosys/                   models, techmaps, scripts and importer
  nextpnr/                 exporter plus necessary C++/Python bridge
  fabulous/                reference conversion/comparison harness
  vtr/                     architecture exploration adapter
  circt/                   optional isolated RTL/verification adapter
  physical/                external ASIC synthesis/P&R/signoff drivers
  macros/                  hard-macro view and capability adapters
cad/rust/                  optional later pack/place/route/STA engines
apps/rust/                 CLI, bitgen, inspector, programmer service
schemas/                   versioned interchange and package schemas
verify/
  spec-model/              independent slow reference model
  formal/                  properties, assumptions and proof manifests
  differential/            cross-tool/cross-representation checks
  simulation/              RTL and gate-level end-to-end harnesses
  coverage/                obligations and justified exclusions
  fixtures/                fixed valid and malformed examples
bench/scale/               representation and query scale fixtures
bench/qor/                 routability, timing, power/area experiments
bench/compiler-backends/   optional emitter/framework comparisons
devices/reference/nf-tiny/  public/test device profile
devices/experimental/nf1/   later candidate, not frozen now
technology/schema/         PDK/macro binding contracts
technology/open/           redistributable bindings only
docs/roadmap/              controlling nested checklists
docs/completion/           evidence summaries for completed increments
docs/adr/                  architecture decision records
```

Rust Cargo and Scala build workspaces may each span these directories. Choose and pin one Scala build tool in FND-01; do not maintain both sbt and Mill builds without a reason. Core imports no library, device, adapter or application. Library generators use frontend/core APIs; concrete devices compose libraries; adapters depend on public contracts; applications invoke libraries/adapters. A fresh downstream package must be able to add a primitive or device without editing core. Do not create dozens of empty crates as a substitute for these boundaries.

## Representations

**ArchIR** retains hierarchy, parameterized templates, routing patterns, resource modes, logical configuration features and physical intent. Resolve units and parameter legality before backend lowering. Electrical/physical capability limits are profile data, not unchecked assumptions in the Scala API.

**DeviceDB** is read-only per immutable device build. Separate type/template tables from instances; represent common tile connectivity once, with local references, sparse exceptions and inter-region links. Preserve hierarchical/lazy queries so a flat 100-million-PIP expansion is not mandatory. A flat representation can be a backend export or benchmark reference, not the only database representation.

**MappedDesign and CAD state** describe customer cells, nets, constants, mode parameters, clock/constraint intent and source correspondence. Placement, routing, congestion and timing caches are mutable per-job overlays, never fields mutated in DeviceDB. Require exact target-package identity; reject mismatched device/configuration manifests before programming.

FPGA Interchange already distinguishes device resources, logical netlists and physical netlists. Evaluate its applicable subsets before inventing equivalent interchange fields; adopting it does not require adopting its in-memory representation. [S7](sources.md#s7)

## IDs, storage and file compatibility

Use distinct IDs for wires, PIPs, BELs, pins, nodes, sites and fields. Dense IDs are stable within one compiled package, not promised stable across arbitrary recompilations. Portable semantic keys and provenance support cross-version correspondence. Use partition-local 32-bit indexes where measured safe and 64-bit lengths/file offsets and cross-partition addressing; bounds-check conversions and test near-limit values without huge allocations.

Illustrative data-model shape, not implemented Rust:

```rust
struct WireId { partition: u32, local: u32 }
struct PipId  { partition: u32, local: u32 }
struct DeviceBuildId([u8; 32]);
struct Adjacency { offsets: Vec<u64>, pip_indices: Vec<u32> }
```

Hot query structures use measured packed AoS/SoA/CSR layouts. Do not mandate SoA for every table. Intern strings in cold symbol/provenance tables. Reuse timing, switch and resource-type records. Measure expanded versus compressed graph costs and reverse adjacency costs.

Prototype with inspectable versioned JSON for authoring exchange. Select binary database encoding using measured read/size/security requirements in DB-04. Define endianness, alignment, integer widths, section lengths, feature/version negotiation, checksums, limits and unknown-field behavior independently of Rust struct layout. Do not cast untrusted file bytes to arbitrary structs. Memory mapping is optional and must have a validated portable reader fallback.

A device package manifest binds architecture, resource libraries, physical implementation revision, configuration map, timing corner set, package/pin map, schema versions and toolchain identity. Incompatible features must fail closed, never be silently discarded. Sign trusted distribution manifests later; a checksum alone is not authentication.

## Resource semantics

Represent sites/BELs/pins plus legal modes, shared controls, occupancy/exclusion groups and pin permutations. A routing edge must describe direction, buffering/pass-switch behavior, fixed versus configurable connectivity, mux-selection exclusions and its owning configuration feature. A routing graph naturally contains cycles; do not reject every cycle. Reject illegal enabled configurations, electrical contention and unsupported customer combinational loops under an explicit profile policy.

Keep clock, power, configuration, placement and routing regions as overlapping domain memberships, not one forced hierarchy. Hard NoCs, SERDES and memory PHYs need protocol/bandwidth/clock contracts; they are not just arbitrary Wire/PIP edges. The chip hierarchy supports dies and regions, but high-end algorithms remain deferred. VTR's architecture model is a useful reference for block modes, timing, NoC and multi-die description. [S6](sources.md#s6)

## Configuration and timing

Separate semantic features (`LUT.INIT`, route selection, register mode) from their physical bit locations and transport framing. Shared bits and aliases must be declared with constraints; undeclared overlap is an error. Encode/decode agreement alone is insufficient: verify against independent known vectors and the actual RTL loader.

Clock resources have connectivity, capacity, source eligibility and region reach. User clock domains and generated-clock constraints are separate from those physical resources. Timing records require units, transitions, conditional arcs, min/max values or tables, setup/hold/recovery/removal as applicable, load/slew assumptions, corners and provenance. Missing timing is unknown, not zero. Separate topology from characterization, but bind each timing dataset to the exact physical implementation revision.

## Physical technology and macro boundary

Keep architecture intent separate from process-specific cells, SRAMs, I/O, PLLs and physical views. This enables reuse, not automatic PDK portability: a port requires electrical, timing and layout requalification. A macro package records interface, supported modes, supplies, placement/access constraints, simulation and physical views, characterization coverage and redistribution permissions. A behavioral PLL model is not analog silicon; consume qualified PLL IP rather than synthesizing it from fabric LUTs.

## Compilation and adapters

Architecture passes have explicit input/output contracts, diagnostics, provenance and invariants: parse → resolve types/parameters → validate semantic constraints → lower templates/partitions → build connectivity/configuration → bind timing/technology → publish package. Cache immutable intermediates by semantic inputs. Do not include local paths/timestamps in semantic content hashes.

nextpnr integration requires an architecture implementation, not merely emitting generic JSON. Evaluate the generic route for tiny bring-up and Himbächel or a full architecture backend for scale. The adapter may need C++ and database-generation tooling even though core is Rust; contain that dependency. The architecture API and Viaduct/Himbächel alternatives are documented upstream. [S4](sources.md#s4) [S5](sources.md#s5)

Unsupported frontend constructs, primitive modes, placement rules, timing exceptions or physical views must produce actionable errors. Do not silently downgrade SystemVerilog/VHDL support or imply a fully supported native Nodal mapping path until CAD-05 proves it.

## Determinism and scaling contracts

Require byte-identical architecture artifacts for identical semantic inputs and pinned toolchain. For CAD, define a reproducibility envelope including seeds, worker count, floating-point/toolchain/platform policy and external tool builds; identical seeds alone do not guarantee cross-platform deterministic parallel results. Use immutable database readers, per-job state and bounded task concurrency. Define backend checkpoints and structured diagnostics without committing to a distributed runtime on day one.

Benchmark measured bytes per resource, peak resident memory, cold/warm loading, indexed query throughput, compiler scaling and P&R quality separately. A large generated database is not proof of high-end routing quality or production silicon.
