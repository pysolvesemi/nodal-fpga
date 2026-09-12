# FPGA-on-FPGA emulation track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `verify/emulation`, board-specific wrappers and programmer adapters. Board/tool access is an external dependency to record, not presume. Emulation checks function and configuration, not target ASIC timing, PLL analog behavior or manufacturing reliability.

- [ ] EMU-01 — First board implementation
  Depends on: CAD-04, VER-04, RTL-04.
  - [ ] EMU-01.a Select a board and pin a host-FPGA toolchain; document available clocks, I/O, resource limits and reset behavior.
  - [ ] EMU-01.b Build the tiny fabric with a fixed test configuration and an observable scoreboard/debug interface.
  - [ ] EMU-01.c Keep host FPGA primitives isolated from the target architecture and identify emulation-only substitutions.
  - [ ] EMU-01.d Run the simulation reference corpus on hardware and investigate mismatches using retained traces.
  - [ ] EMU-01.e Record actual board/tool versions, bitstreams, traces and final-head hardware evidence.

- [ ] EMU-02 — Runtime configuration and recovery on hardware
  Depends on: EMU-01, CFG-05.
  - [ ] EMU-02.a Exercise the real target configuration path rather than synthesis-time constant configuration only.
  - [ ] EMU-02.b Add host transport tools and repeatable reset/configure/start/readback or observation sequences.
  - [ ] EMU-02.c Preserve user-clock/configuration-clock separation and document host limitations on metastability/timing observation.
  - [ ] EMU-02.d Test repeated reconfiguration, interruption, corrupted/wrong-device inputs and recovery into safe state.
  - [ ] EMU-02.e Record loader functionality, failure containment and final-head runtime-emulation evidence.

- [ ] EMU-03 — Emulation release corpus
  Depends on: EMU-02, VER-07.
  - [ ] EMU-03.a Automate board leasing, programming, timeouts, result capture and reproducible test selection.
  - [ ] EMU-03.b Reuse verification corpus identities across RTL, netlist and hardware tests.
  - [ ] EMU-03.c Document board availability/failure handling so missing hardware is never reported as a passing run.
  - [ ] EMU-03.d Execute the frozen release corpus and classify host-wrapper versus target-fabric failures.
  - [ ] EMU-03.e Publish final-head hardware qualification and explicit limits before using emulation as tapeout-readiness evidence.

Main risk: assuming a successful host FPGA implementation proves ASIC electrical behavior. Do not use host timing numbers as advertised NF1 performance.
