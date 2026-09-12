# Optional native Rust CAD track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `cad/rust/{pack,place,route,sta}` only when justified. This is an optional replacement path, not an inevitable rewrite. A qualified external backend may remain the production engine, including for advanced devices.

- [ ] NAT-01 — Evidence-based native-engine decision and contracts
  Depends on: CAD-06, PERF-04, PROD-01.
  - [ ] NAT-01.a Identify measured external-engine limitations and compare adapter/upstream improvement against a native replacement.
  - [ ] NAT-01.b Define an accepted business/technical case, target workload and required correctness/runtime/quality thresholds.
  - [ ] NAT-01.c Freeze backend-neutral mapped/packed/placed/routed checkpoints, legality APIs and incremental timing interfaces.
  - [ ] NAT-01.d Test interchange and reference-engine replay so a replacement can be evaluated against identical workloads.
  - [ ] NAT-01.e Record the decision and final-head contract evidence; if native work is not adopted, leave this optional track deferred and unchecked.

- [ ] NAT-02 — Native packing and placement prototype
  Depends on: NAT-01, TMC-03.
  - [ ] NAT-02.a Implement supported packing/control/mode legality and a simple baseline placer before advanced optimization.
  - [ ] NAT-02.b Add macro/clock/carry constraints, legalization and checkpoint-compatible placement results.
  - [ ] NAT-02.c Reuse qualified timing/legality contracts without duplicating device semantics inside heuristics.
  - [ ] NAT-02.d Compare to the qualified external engine on legality, routability, quality, runtime and memory across fixed seeds.
  - [ ] NAT-02.e Record final-head results and unsupported architectures; do not promote a faster but lower-correctness prototype.

- [ ] NAT-03 — Native routing and incremental analysis prototype
  Depends on: NAT-02.
  - [ ] NAT-03.a Implement a deterministic baseline route search and congestion management over the public DeviceDB query API.
  - [ ] NAT-03.b Handle shared/exclusive resources, dedicated paths, clock constraints and route-commit/rollback semantics.
  - [ ] NAT-03.c Add incremental timing integration and controlled parallelism only with independent correctness checks.
  - [ ] NAT-03.d Run adversarial congestion, unroutability, incremental reroute and timing/hold regressions against external results.
  - [ ] NAT-03.e Record benchmark distributions and final-head route-checker/equivalence evidence, not only best-case speedups.

- [ ] NAT-04 — Native backend production qualification
  Depends on: NAT-03, VER-07.
  - [ ] NAT-04.a Freeze the supported native backend/device matrix and reproducibility envelope.
  - [ ] NAT-04.b Qualify complete synthesis-to-bitstream flows against independent legality, configuration, formal and simulation tests.
  - [ ] NAT-04.c Meet the approved memory/runtime/routability/timing-quality thresholds without changing reference obligations to fit results.
  - [ ] NAT-04.d Repeat applicable emulation/physical/silicon checks for affected product profiles and retain fallback compatibility.
  - [ ] NAT-04.e Record a scoped production-backend decision with final-head evidence before switching defaults.

Main risk: turning a fabric-generator project into an unbounded EDA rewrite. Native generic RTL synthesis remains outside this track and would need its own separate decision.
