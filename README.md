# nodal-fpga

A planned FPGA architecture compiler and fabric-generation platform: a Scala architecture frontend, a Rust backend, and a versioned language-neutral interface between them.

The objective is to start with a small, verifiable programmable fabric and grow toward commercial FPGA families. The implementation language alone does not establish silicon quality, tool quality, or commercial readiness.

## Start here

- [Incremental roadmap and track dependencies](docs/roadmap/README.md)
- [Nested-checkbox progress and completion rules](docs/roadmap/progress.md)
- [Architecture and proposed core/library directory structure](docs/architecture.md)
- [Verification and FABulous comparison strategy](docs/verification.md)
- [Research sources and limits of the evidence](docs/sources.md)
- [Scala/Rust core and optional CIRCT decision](docs/adr/0001-optional-circt-backend.md)

## Project boundaries

`nodal-hdl` owns the existing Scala/MLIR hardware-language compiler. `nodal-fpga` owns FPGA architecture compilation, fabric RTL, device/configuration data, and device implementation adapters. Initially, Yosys and nextpnr provide synthesis and packing/place-and-route. Native CAD engines are a later, evidence-gated track. `nodal-eda` remains the separate customer-facing orchestration/UI project.

Scala is a first-class architecture-construction frontend, not a per-resource JNI wrapper. Rust validates the exchanged architecture and performs device compilation. Running the resulting device tools must not require Scala, the JVM, or MLIR.

MLIR/CIRCT is not a foundational dependency. A separate [optional evaluation track](docs/roadmap/tracks/15-compiler-backend-evaluation.md) may assess CIRCT for fabric RTL generation or supplemental verification. Adoption requires demonstrated correctness, useful measured benefit and dependency isolation; it does not replace ArchIR or DeviceDB and does not block the initial FPGA milestones.

## Current status

FND-01's build-only Rust/Scala bootstrap is qualified and integrated on `dev`.
See the [completion evidence](docs/completion/FND-01.md) and authoritative
Foundation checklist. No production frontend, backend, fabric or silicon
implementation is claimed.

Development planning is on `dev`. Do not modify or merge into `main` without explicit authorization.

## Bootstrap development

FND-01 provides a minimal Rust/Scala build baseline. See
[developer bootstrap](docs/development/bootstrap.md) for pinned tools, commands,
ownership checks and qualification boundaries. Its smoke programs do not
generate FPGA hardware or implement the production architecture DSL.
