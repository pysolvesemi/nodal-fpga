# Rust architecture compiler and DeviceDB track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `core/rust/{arch-ir,device-db,design-db}`, `compiler/rust/arch-compiler`, `schemas/`. The core remains independent of device/library choices and external EDA formats.

- [ ] DB-01 — Deterministic pass pipeline
  Depends on: FND-08.
  - [ ] DB-01.a Implement parsing, parameter resolution, semantic validation and explicit pass input/output contracts.
  - [ ] DB-01.b Provide reproducible intermediate dumps, structured errors and per-pass provenance without global mutable state.
  - [ ] DB-01.c Add a Rust builder that produces the same schema as external frontends, not a privileged alternate architecture model.
  - [ ] DB-01.d Test pass ordering, rejected illegal transitions, deterministic outputs and replay of saved intermediates.
  - [ ] DB-01.e Record final-head pass-contract tests and exact supported ArchIR features.

- [ ] DB-02 — Hierarchical resource tables and query API
  Depends on: DB-01.
  - [ ] DB-02.a Implement device/die/region/site/BEL/pin tables with separate type templates and instances.
  - [ ] DB-02.b Add legal-mode, occupancy, shared-control and pin-map constraints without hard-coding LUT-only resources.
  - [ ] DB-02.c Define immutable device queries and separate per-design cells/nets/state with package-qualified references.
  - [ ] DB-02.d Compare resource enumeration to independent fixtures; test cross-partition identities and invalid references.
  - [ ] DB-02.e Record deterministic semantic dumps and final-head query/API evidence.

- [ ] DB-03 — Scalable routing representation and legality
  Depends on: DB-02, LIB-01.
  - [ ] DB-03.a Implement wires/nodes/PIPs, direction and switch semantics, template-local connectivity and sparse nonlocal exceptions.
  - [ ] DB-03.b Add forward/reverse adjacency, routing-class queries and explicit mux exclusion/shared-feature constraints.
  - [ ] DB-03.c Distinguish fixed connectivity, selectable edges and resource contention; permit architectural graph cycles while rejecting illegal selected states.
  - [ ] DB-03.d Check small graphs against a deliberately simple expanded model and fuzz odd boundaries, holes and asymmetric routing.
  - [ ] DB-03.e Record topology equivalence and memory/query baselines with all supported legal-state constraints tested.

- [ ] DB-04 — Compiled package format and safe readers
  Depends on: DB-03.
  - [ ] DB-04.a Evaluate existing FPGA Interchange subsets and binary serialization options before freezing the public package format.
  - [ ] DB-04.b Implement sectioned immutable packages, explicit widths/endianness, checksums, feature negotiation and a portable reader.
  - [ ] DB-04.c Add validated mmap access where beneficial; never expose unchecked file bytes as native structs or references.
  - [ ] DB-04.d Test corrupt offsets/lengths, overflow, truncation, cross-version rejection, deterministic writes and mmap/portable-reader parity.
  - [ ] DB-04.e Publish schema/reader compatibility evidence and measured package/load costs on the final head.

- [ ] DB-05 — Bind configuration, timing, packages and technology
  Depends on: DB-04, CFG-01, TMC-01.
  - [ ] DB-05.a Bind logical configuration, timing references, clock resources, package pins and macro view manifests through explicit interfaces.
  - [ ] DB-05.b Record exact architecture/library/implementation revisions and reject mismatched timing or configuration identities.
  - [ ] DB-05.c Keep physical technology and legal device modes separate while declaring unsupported or uncharacterized combinations.
  - [ ] DB-05.d Test missing model views, mismatched pin maps, unknown timing and incompatible configuration packages.
  - [ ] DB-05.e Record complete tiny-package consistency reports and final-head validation evidence.

- [ ] DB-06 — Incremental compilation and stable publication
  Depends on: DB-05, PERF-02.
  - [ ] DB-06.a Add content-addressed pass/partition caches with explicit semantic dependency fingerprints.
  - [ ] DB-06.b Rebuild only affected sections while preserving deterministic final artifacts and safe invalidation of consumers.
  - [ ] DB-06.c Publish packages atomically with compatibility manifests; do not promise local dense IDs persist across changed builds.
  - [ ] DB-06.d Compare full versus incremental builds under template, library, timing and configuration edits; test stale-cache rejection.
  - [ ] DB-06.e Record reproducibility, invalidation and scale evidence before declaring incremental compilation supported.

Main risk: full graph expansion becoming the only representation or private struct layouts becoming a long-lived ABI. Do not put device-specific placement algorithms or Scala runtime dependencies into DeviceDB.
