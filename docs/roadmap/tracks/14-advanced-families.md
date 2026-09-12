# Advanced heterogeneous and high-end families track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: new libraries/device profiles and required backend extensions, not conditional device hacks in core. These are future engineering increments, not high-end support already obtained by schema design. Before implementing a broad advanced increment, expand its children into device-specific bounded work packages while preserving its ID and requirements.

- [ ] ADV-01 — Qualified heterogeneous family
  Depends on: PROD-03, LIB-04, TMC-04.
  - [ ] ADV-01.a Select an evidence-backed family with larger memory/DSP resources, regional clocks, I/O banks and qualified hard-macro bindings.
  - [ ] ADV-01.b Extend mode/occupancy/timing/configuration libraries without making core depend on concrete macro/device types.
  - [ ] ADV-01.c Qualify the chosen external or native CAD backend on heterogeneous workload placement, routing and constraints.
  - [ ] ADV-01.d Run new resource/mode verification, physical characterization and applicable emulation/silicon correlation.
  - [ ] ADV-01.e Record family-specific qualification and final-head compatibility evidence before claiming commercial support.

- [ ] ADV-02 — Regional configuration and security capabilities
  Depends on: ADV-01, CFG-05.
  - [ ] ADV-02.a Define supported reconfiguration boundaries, isolation, shared-clock/state dependencies and legal update transactions.
  - [ ] ADV-02.b Design integrity/authentication/key-management requirements from a threat model and qualified security components, not custom cryptography.
  - [ ] ADV-02.c Bind bitstream operations to actual hardware support; define recovery, interrupted update and unsupported-operation behavior.
  - [ ] ADV-02.d Verify isolation, noninterference and adversarial update cases, including applicable side-channel/fault-injection assessments.
  - [ ] ADV-02.e Record hardware/software security and reconfiguration scope with independent review and final-head evidence.

- [ ] ADV-03 — Multi-region and multi-die implementation
  Depends on: ADV-02, PERF-04.
  - [ ] ADV-03.a Extend qualified profiles with explicit inter-region/inter-die bandwidth, latency, clock, power and package constraints.
  - [ ] ADV-03.b Implement hierarchical planning and interface legality in the selected qualified CAD backend; native CAD is not mandatory.
  - [ ] ADV-03.c Treat NoC, SERDES, memory PHYs and die links as protocol/capacity resources with suitable models rather than ordinary signal PIPs only.
  - [ ] ADV-03.d Evaluate representative full designs, partition crossings, thermal/power effects and physical integration feasibility.
  - [ ] ADV-03.e Record scale/quality and implementation evidence for the supported topology; a synthetic multi-die database is not completion.

- [ ] ADV-04 — High-end product qualification
  Depends on: ADV-03, PROD-04.
  - [ ] ADV-04.a Freeze the advanced product's actual workload, operating, package, reliability and software support requirements.
  - [ ] ADV-04.b Repeat product-specific DFT, signoff, manufacturing, security and silicon-characterization gates for all added capabilities.
  - [ ] ADV-04.c Qualify release compatibility and diagnostics across historical and new device families without weakening safety checks.
  - [ ] ADV-04.d Demonstrate required throughput, routability, timing, power and supported hard-IP operation using measured end-to-end results.
  - [ ] ADV-04.e Publish a precisely scoped commercial qualification decision and remaining limitations; language choice and representation size are not proof.

Main risk: promising high-end capability based on a flexible schema. Delay unneeded SERDES/HBM/PCIe/chiplet implementation until qualified IP, physical technology, customers and engineering evidence justify the profile.
