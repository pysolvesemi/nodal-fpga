# Physical implementation and tapeout-readiness track

[Roadmap index](../README.md) · [Progress rules](../progress.md)

Global blocker: FND-08. Modules: `adapters/physical`, `technology/{schema,open}`, physical test fixtures and restricted external PDK stores. Passing this track prepares evidence; it does not authorize foundry submission or spending.

- [ ] PHY-01 — Technology binding and signoff plan
  Depends on: FND-08.
  - [ ] PHY-01.a Select an available process/tool flow for evaluation and record legal access, supported model/deck revisions and permitted artifact handling.
  - [ ] PHY-01.b Specify standard-cell, SRAM, I/O, clock, power, configuration-storage and hard-macro binding contracts.
  - [ ] PHY-01.c Define floorplan, test access, DFT/scan/MBIST, pad/ESD and top-level verification requirements before hardening.
  - [ ] PHY-01.d Validate mock/open bindings, missing views, supply-pin mismatches and separation of redistributable from restricted assets.
  - [ ] PHY-01.e Record process-specific signoff responsibilities and final-head adapter/binding evidence without claiming tapeout readiness.

- [ ] PHY-02 — Tile hardening and first assembled implementation
  Depends on: PHY-01, RTL-05.
  - [ ] PHY-02.a Implement repeatable synthesis/floorplanning/placement/routing for a small tile and assembled fabric using external engines.
  - [ ] PHY-02.b Integrate clock/power/reset/configuration/test structures, correct physical pins and declared macro abutment rules.
  - [ ] PHY-02.c Produce netlists, layout abstracts, GDS and extraction inputs with exact device/technology manifests.
  - [ ] PHY-02.d Run available DRC/LVS and structural/constraint checks; preserve failed experiments and report missing signoff coverage explicitly.
  - [ ] PHY-02.e Record actual physical artifacts, preliminary PPA and final-head implementation evidence for the selected process only.

- [ ] PHY-03 — Post-layout and electrical qualification
  Depends on: PHY-02, TMC-04, VER-07.
  - [ ] PHY-03.a Run qualified DRC/LVS, extraction, min/max STA and applicable clock/reset-domain checks for the selected implementation.
  - [ ] PHY-03.b Perform post-layout/gate-level checks with explicit SDF and black-box coverage; identify behavioral portions retained in mixed-level runs.
  - [ ] PHY-03.c Evaluate power, IR drop, electromigration, test coverage and relevant analog/macro integration requirements using suitable qualified tools.
  - [ ] PHY-03.d Exercise configuration and user-design regressions against implementation netlists and audit model/corner completeness.
  - [ ] PHY-03.e Record process-specific pass/fail evidence and unresolved waivers; an open-source GDS flow alone is not signoff.

- [ ] PHY-04 — Tapeout-readiness review
  Depends on: PHY-03, EMU-03, PROD-01.
  - [ ] PHY-04.a Freeze the exact fabric, macro, PDK, configuration, package and test revisions for the candidate submission.
  - [ ] PHY-04.b Assemble qualified signoff, DFT/ATE vectors, power/clock assumptions, bring-up plans and manufacturing deliverable checks.
  - [ ] PHY-04.c Independently review critical verification coverage, unresolved risks, physical exceptions and recovery/test access.
  - [ ] PHY-04.d Reproduce the release package and confirm all required final-head evidence corresponds to the frozen implementation.
  - [ ] PHY-04.e Record an explicit readiness decision and limitations; submit to fabrication only with separate authorization and foundry acceptance.

Main risk: conflating RTL correctness, DRC-clean geometry and production-qualified silicon. Do not claim analog characterization, ESD/reliability compliance or foundry approval from a generic tool success log.
