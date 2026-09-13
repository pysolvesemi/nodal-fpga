# ADR 0001 — Scala/Rust core with optional CIRCT adapters

Status: accepted architecture direction; implementation and evaluation remain unstarted.

## Decision

Keep the Scala architecture frontend and Rust architecture compiler. ArchIR is a versioned, language-neutral contract, not an MLIR dialect. Rust owns architecture validation, resolved device semantics, DeviceDB and configuration mapping. The default architecture compiler, RTL emitter and device tools must build and run without LLVM, MLIR or CIRCT. Saved packages must also remain usable without Scala or a JVM.

Keep the existing high-level Nodal compiler and its MLIR pipeline in `nodal-hdl`. That project and qualified synthesis tools hand off through the mapped-design contract. Sharing MLIR-based source compilation does not require a second MLIR dependency in the FPGA fabric generator.

Allow a separate, opt-in CIRCT adapter for fabric RTL generation or supplemental verification when an experiment demonstrates value. This is not a commitment to implement or adopt it. The [compiler-backend evaluation track](../roadmap/tracks/15-compiler-backend-evaluation.md) controls that work; all its increments inherit `FND-08` and none is a prerequisite for the existing M0–M6 milestones.

## Rationale and alternatives

MLIR supports graph regions, including cyclic relationships; the decision is not based on a claim that MLIR cannot represent hardware graphs. CIRCT provides hardware representations and Verilog/SystemVerilog export infrastructure. Those are credible options for avoiding a duplicated general RTL compiler. They do not establish Nodal-FPGA's device semantics, storage efficiency or silicon qualification. [1][2]

The default is a focused structured Rust emitter, not an arbitrary HDL parser, synthesis engine or general optimization framework. Before expanding that emitter into a general compiler, perform the CIR-01 scope review. Compare keeping it small, reusing verified module generation through existing `nodal-hdl`, and an isolated CIRCT backend. The review may retain the current emitter without waiting for an optional prototype. Do not delay the tiny-fabric flow or the first silicon path solely to evaluate a framework.

Rust/MLIR integration is possible; MLIR documents a C API but currently calls it unstable. Prefer an external executable with pinned inputs/outputs for the first experiment, rather than exposing MLIR handles or an LLVM ABI through core interfaces. Any later in-process integration requires a separate reviewed decision. [3]

## Boundary

```text
Scala DSL -> ArchIR -> Rust architecture compiler
                            |
                   resolved device semantics
                       /       |       \
                  DeviceDB   config    fabric backend contract
                                         /          \
                               Rust emitter       optional adapter
                                                     |
                                               CIRCT process
                                                     |
                                               generated RTL
```

The backend contract describes a bounded, hierarchical hardware-emission subset: modules, typed ports, instances, supported expressions/sequential behavior, configuration interfaces and provenance. Its exact executable schema is evaluated in CIR-01; this ADR does not introduce a second general-purpose hardware IR. Preserve reusable templates at handoff instead of expanding the whole routing graph into compiler operations.

Possible future locations are `adapters/circt/`, `verify/differential/circt/` and `bench/compiler-backends/`. They are adapter/test packages, not dependencies of reusable core or device libraries. Do not scaffold these directories or add an LLVM toolchain merely because they appear in this plan.

An explicitly requested unavailable backend must fail with a useful diagnostic. Do not silently substitute a different backend or claim its qualification. Default tool invocations must not discover, download or invoke CIRCT implicitly. Record backend/tool versions, options, input hashes and capability coverage in artifact manifests.

## Correctness and adoption gates

Both emission paths must preserve the programmable fabric across all supported legal configurations and declared configuration-loading, activation and reset behavior. Prove tractable primitive/tile contracts using symbolic configuration and independent expected semantics; combine structural checks, coverage, mutation testing and runtime-loaded end-to-end tests for larger assemblies. Never optimize the manufactured fabric for one example customer's bitstream.

Preserve widths, signedness, sequential priority, declared X/Z assumptions and configuration correspondence. Retain or explicitly map transformed resource endpoints and provenance. A changed physical implementation requires a new bound package revision and affected timing/physical requalification; equal RTL text or an unchanged architecture name is not sufficient.

A second compiler is not an independent golden model by itself. CIRCT bounded-model-checking experiments must disclose supported operations, assumptions and depth; a bounded result is not an unbounded all-configurations fabric proof. They supplement, not replace, the independent model and existing formal/simulation obligations. [4]

Measure cold/warm generation time, peak memory, hierarchy retention, artifact size, dependency/build burden and maintenance effort on pinned fixtures. Measure downstream area/timing only through the same physical flow and constraints. Set acceptance criteria before the comparison; neither Rust nor MLIR is assumed faster in advance.

CIR-02 records an evidence-backed adopt, retain-default or defer decision. Adoption requires correctness, useful measured benefit and isolated dependencies. Only an adopt decision activates CIR-03 production qualification. Otherwise leave it unchecked and record why it is dormant. A CIRCT-backed release, if later offered, requires its selected-profile tests; an optional adapter's failure must not be relabeled as a passing supported configuration.

## Sources

Primary documentation checked 2026-09-13. These moving pages describe upstream capabilities, not a pinned Nodal-FPGA implementation; evaluation must pin actual tool revisions.

1. LLVM/MLIR, [Language Reference — Graph Regions](https://mlir.llvm.org/docs/LangRef/#graph-regions). Supports graph/concurrent and cyclic semantics; not evidence of a specific DeviceDB performance result.
2. CIRCT, [HW Dialect Rationale](https://circt.llvm.org/docs/Dialects/HW/RationaleHW/). Hardware representation and RTL export context; not a complete FPGA fabric/configuration compiler.
3. LLVM/MLIR, [MLIR C API](https://mlir.llvm.org/docs/CAPI/). Cross-language integration and stated API stability limits.
4. CIRCT, [Bounded Model Checking](https://circt.llvm.org/docs/Tools/circt-bmc/). Supported proof flow and bounds must be checked for the selected version.
