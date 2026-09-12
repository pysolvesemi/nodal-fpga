# nodal-fpga

A planned FPGA architecture compiler and fabric-generation platform: a Scala architecture frontend, a Rust backend, and a versioned language-neutral interface between them.

The objective is to start with a small, verifiable programmable fabric and grow toward commercial FPGA families. The implementation language alone does not establish silicon quality, tool quality, or commercial readiness.

## Start here

- [Incremental roadmap and track dependencies](docs/roadmap/README.md)
- [Nested-checkbox progress and completion rules](docs/roadmap/progress.md)
- [Architecture and proposed core/library directory structure](docs/architecture.md)
- [Verification and FABulous comparison strategy](docs/verification.md)
- [Research sources and limits of the evidence](docs/sources.md)

## Project boundaries

`nodal-hdl` owns the existing Scala/MLIR hardware-language compiler. `nodal-fpga` owns FPGA architecture compilation, fabric RTL, device/configuration data, and device implementation adapters. Initially, Yosys and nextpnr provide synthesis and packing/place-and-route. Native CAD engines are a later, evidence-gated track. `nodal-eda` remains the separate customer-facing orchestration/UI project.

Scala is a first-class architecture-construction frontend, not a per-resource JNI wrapper. Rust validates the exchanged architecture and performs device compilation. Running the resulting device tools must not require Scala, the JVM, or MLIR.

## Current status

Planning only. All implementation increments and sub-items start unchecked. This documentation does not claim that a frontend, backend, fabric, passing verification suite, or silicon implementation already exists.

Development planning is on `dev`. Do not modify or merge into `main` without explicit authorization.
