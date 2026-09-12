# Configuration and bitstream track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `core/rust/config-schema`, `compiler/rust/config-compiler`, `apps/rust/bitgen`, loader RTL and independent vectors. Security features are profile-dependent; checksums are not authentication.

- [ ] CFG-01 — Logical configuration semantics
  Depends on: FND-08.
  - [ ] CFG-01.a Define LUT contents, mux selections, register modes, defaults and reserved encodings independently of physical bit addresses.
  - [ ] CFG-01.b Model declared aliases/shared bits, exclusion groups and legal-mode constraints with explicit ownership.
  - [ ] CFG-01.c Define configuration regions, activation policy and the distinction between runtime state and persistent configuration.
  - [ ] CFG-01.d Test illegal combinations, undeclared overlap, missing required settings and equivalent canonical configurations.
  - [ ] CFG-01.e Record independently reviewed feature semantics and final-head validator evidence.

- [ ] CFG-02 — Physical allocation and encoding map
  Depends on: CFG-01, DB-03.
  - [ ] CFG-02.a Allocate fields into parameterized addresses/frames/words without hard-coded device-size limits in core.
  - [ ] CFG-02.b Specify bit order, byte order, packing, defaults and legal shared-field behavior in a versioned map.
  - [ ] CFG-02.c Emit matching loader/fabric metadata from the resolved map with exact device-build identity.
  - [ ] CFG-02.d Compare against hand-calculated vectors and independently decoded locations; test boundaries and sparse addresses.
  - [ ] CFG-02.e Record allocation coverage, conflict detection and final-head independent mapping checks.

- [ ] CFG-03 — Hardware configuration controller
  Depends on: CFG-02, RTL-02.
  - [ ] CFG-03.a Implement the initial declared transport and write-address decoder with reset/restart, completion and error handling.
  - [ ] CFG-03.b Define configuration/user-clock crossing, quiescence, commit/activation and power-up assumptions explicitly.
  - [ ] CFG-03.c Prevent unsupported/out-of-range writes and maintain safe outputs until the required configuration sequence completes.
  - [ ] CFG-03.d Verify write isolation, transaction interruption, reset and activation ordering using simulation and applicable formal properties.
  - [ ] CFG-03.e Record actual loader RTL, assumptions, proof scope and final-head protocol evidence.

- [ ] CFG-04 — Bitstream packer, parser and integrity checks
  Depends on: CFG-03.
  - [ ] CFG-04.a Implement logical-config-to-bitstream conversion, bounded parsing, inspection and a clearly specified integrity mechanism.
  - [ ] CFG-04.b Bind bitstreams to device/configuration-map revision and reject unsupported versions before activation.
  - [ ] CFG-04.c Define how checksums cover payload/header fields and specify invalid, truncated and duplicated transaction behavior.
  - [ ] CFG-04.d Test round trips, known vectors, bit corruption and wrong-device packages through the actual hardware loader.
  - [ ] CFG-04.e Record software/RTL agreement and final-head failures-as-expected; do not claim cryptographic authentication.

- [ ] CFG-05 — Routed-design configuration qualification
  Depends on: CFG-04, CAD-04, VER-02.
  - [ ] CFG-05.a Convert a validated routed design into legal resource features, including shared-control and unused-resource defaults.
  - [ ] CFG-05.b Independently reconstruct selected connectivity and resource modes from encoded configuration for comparison to routing results.
  - [ ] CFG-05.c Define semantic field-isolation tests that allow documented checksum/header changes and declared bit aliases only.
  - [ ] CFG-05.d Test adversarial legal/illegal routes, alias conflicts, wrong maps and reset/reconfiguration between different user designs.
  - [ ] CFG-05.e Record complete configuration-obligation coverage and final-head end-to-end evidence.

Main risk: encoder and decoder sharing the same wrong mapping. Use independent expected vectors plus RTL readback/observable behavior. Defer encryption, partial reconfiguration and nonvolatile provisioning until architecture, threat model and silicon support exist.
