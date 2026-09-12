# Scale, performance and CAD quality track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `bench/{scale,qor}`, memory/query instrumentation and concurrency tests. All numerical profiles below are proposed test workloads, not measured performance or device announcements.

- [ ] PERF-01 — Reproducible workload and measurement harness
  Depends on: FND-08.
  - [ ] PERF-01.a Define hashed small, medium and large synthetic architectures with both repeated regular structure and sparse irregular exceptions.
  - [ ] PERF-01.b Include nominal 1K/100K/1M logic-resource profiles and staged logical routing-graph workloads reaching 100M PIPs.
  - [ ] PERF-01.c Measure compiler time, package size, peak RSS, cold/warm load and query throughput separately; record hardware and toolchain identity.
  - [ ] PERF-01.d Test benchmark repeatability, reporting of resource counts and schema-limit cases without requiring enormous allocations.
  - [ ] PERF-01.e Freeze baseline procedures and explicitly label unavailable large-run capacity; no unmeasured scale claim may be marked passed.

- [ ] PERF-02 — Database representation and loading scale
  Depends on: PERF-01, DB-04.
  - [ ] PERF-02.a Compare flat, template-shared and partitioned representations with total bytes per resource and reverse-adjacency overhead.
  - [ ] PERF-02.b Measure construction scratch memory, validated mmap/portable loading and sequential/random/localized queries.
  - [ ] PERF-02.c Freeze reviewed memory/runtime budgets from measurements; establish bounded regression thresholds on identical runners, not universal promises.
  - [ ] PERF-02.d Exercise progressive scale and irregular graphs; reject overflow, unbounded expansion and accidental per-instance duplicated strings/timing tables.
  - [ ] PERF-02.e Record actual completed sizes, query rates, RSS and limiting factors with final-head evidence.

- [ ] PERF-03 — End-to-end quality and throughput benchmarks
  Depends on: PERF-02, CAD-04.
  - [ ] PERF-03.a Build a representative user-design suite and measure synthesis/P&R time, peak memory, routability, utilization and timing quality.
  - [ ] PERF-03.b Sweep architecture/seed choices reproducibly and compare normalized quality at declared constraints, not just fastest runtime.
  - [ ] PERF-03.c Separate estimated logical area/timing from physical implementation and characterized results; account for benchmark licensing.
  - [ ] PERF-03.d Detect regressions that trade correctness or timing feasibility for speed; preserve failing and unroutable examples.
  - [ ] PERF-03.e Publish measured baselines and explicit external-engine bottlenecks as input to, not justification assumed for, native CAD.

- [ ] PERF-04 — Concurrency, cache and large-package qualification
  Depends on: PERF-03, DB-06.
  - [ ] PERF-04.a Stress concurrent read-only DeviceDB consumers and per-job mutable overlays without hidden shared mutable state.
  - [ ] PERF-04.b Measure incremental invalidation, bounded parallelism, working-set size and optional partition/lazy-loading paths.
  - [ ] PERF-04.c Define deterministic and performance modes with worker/seed/platform constraints; record intentional nondeterminism explicitly.
  - [ ] PERF-04.d Run large stress profiles and compare cached/full and single/multiworker outputs within the declared reproducibility contract.
  - [ ] PERF-04.e Record scale budgets, completed workloads and final-head concurrency/replay evidence; larger DBs alone do not prove high-end CAD quality.

Main risk: selecting Rust or mmap and assuming scalability is solved. Measure both representation costs and algorithmic quality. Defer distributed orchestration and out-of-core routing until recorded bottlenecks require them.
