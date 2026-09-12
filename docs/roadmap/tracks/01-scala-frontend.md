# Scala architecture frontend track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `frontend/scala/{api,elaboration,emit,cli}`. Library content belongs in `library/scala`, not the frontend implementation.

- [ ] DSL-01 — Typed architecture construction API
  Depends on: FND-08.
  - [ ] DSL-01.a Implement typed devices, regions, ports, resource references, parameters and physical/electrical units against the frozen schema.
  - [ ] DSL-01.b Preserve user source locations and names for diagnostics while assigning separate semantic identities.
  - [ ] DSL-01.c Emit inspectable ArchIR through the shared envelope; avoid per-resource JNI/FFI calls to Rust.
  - [ ] DSL-01.d Test compile-time unit/type errors and elaboration-time range/connectivity errors with clear diagnostics.
  - [ ] DSL-01.e Record API examples, emitted IR and final-head conformance evidence; no generated Verilog claim is required yet.

- [ ] DSL-02 — Hierarchy, composition and reusable generation
  Depends on: DSL-01.
  - [ ] DSL-02.a Implement tile/region templates, repeated instances, sparse overrides and explicit connectivity bindings.
  - [ ] DSL-02.b Preserve repetition in exchanged IR so Scala does not allocate a full large-device resource graph.
  - [ ] DSL-02.c Add stable namespace/composition rules and deterministic architecture sweeps with explicit parameters and seeds.
  - [ ] DSL-02.d Test empty/odd/boundary shapes, nested reuse, name collisions, invalid overrides and repeated-template equivalence.
  - [ ] DSL-02.e Record structural compression and elaboration measurements plus final-head tests; reject unbounded accidental expansion.

- [ ] DSL-03 — Rust/Scala semantic parity and diagnostics
  Depends on: DSL-02, DB-02.
  - [ ] DSL-03.a Describe the same tiny architectures through the Scala DSL and Rust builder and compare normalized semantic results.
  - [ ] DSL-03.b Map Rust validation diagnostics back to Scala definition/instance locations without requiring a running JVM on the backend.
  - [ ] DSL-03.c Support version negotiation and explicit required-feature rejection across frontend/backend versions.
  - [ ] DSL-03.d Test parity for illegal modes, shared controls, constants, template overrides and malformed external ArchIR.
  - [ ] DSL-03.e Archive matching semantic hashes and intentional-difference reports on the final head.

- [ ] DSL-04 — Usable architecture-author package
  Depends on: DSL-03, DB-04, LIB-02.
  - [ ] DSL-04.a Package the API and CLI with examples composing reusable libraries into the nf-tiny family.
  - [ ] DSL-04.b Add dependency locking, deterministic library resolution and a complete architecture-to-device-package command.
  - [ ] DSL-04.c Document how external users add a library/device without editing core or backend sources.
  - [ ] DSL-04.d Test clean downstream consumption, offline locked builds and Rust-only consumption of the resulting package.
  - [ ] DSL-04.e Record executable Scala examples, generated IR/package evidence and final-head tests; show actual Verilog only if the tested flow emits it.

Main risk: duplicating authoritative semantics or expanding huge device graphs on the JVM. Do not implement timing analysis, a router, a second generic HDL compiler, or proprietary device assumptions here.
