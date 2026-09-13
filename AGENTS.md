# Repository work rules

Read `docs/roadmap/README.md`, `docs/roadmap/progress.md`, and the selected track before implementation.

## Branch and scope

- Planning and development target `dev`; do not modify, merge into, or force-update `main` without explicit authorization.
- A roadmap entry is not permission to implement every track or to tape out, purchase IP, publish releases, or access restricted PDK material.
- Preserve existing changes and check the current remote head before committing. Never replace concurrent work with a stale tree.

## Progress

- Each increment is a parent Markdown checkbox; independently completable tasks are nested checkboxes with stable IDs.
- Mark a sub-item `[x]` only when its own acceptance condition has evidence. Other sub-items and the parent remain `[ ]` while incomplete.
- A parent becomes `[x]` only after every required descendant is `[x]`, dependencies are complete, and final-head verification and completion evidence are recorded.
- All non-Foundation tracks are blocked by `FND-08`. Foundation bootstraps its own tests and must not depend on a blocked track.
- Documentation, generated stubs, a passing example, a draft PR, and historical chat claims are not proof of implementation completion.
- Never silently remove, waive, or weaken a required sub-item to close an increment. Reopen affected items when a regression invalidates evidence.

## Completion reports

Record the source commit, tool/device/configuration hashes, commands, results, limitations, and evidence locations. Show actual executable Scala architecture source and corresponding generated Verilog when applicable; distinguish fabric RTL from mapped customer RTL. Never present illustrative pseudocode as generated output. When an increment does not affect Verilog, state: `This increment does not affect generated Verilog.` A schema-only increment may instead show its actual IR/database diff.

## Ownership

Reusable engine code must not depend on concrete device libraries, Scala, MLIR, nextpnr internals, or proprietary PDK files. Keep library generators, device definitions, external adapters, applications, and verification oracles separate. Do not turn `nodal-fpga` into the `nodal-eda` GUI or a second high-level Nodal compiler.

Follow `docs/adr/0001-optional-circt-backend.md`: CIRCT is an optional isolated adapter, not a core/default dependency. The ordinary Rust compiler toolchain is allowed; do not require a separately installed LLVM/MLIR/CIRCT SDK for default builds. Keep the focused emitter small and review alternatives before building a general HDL compiler. CIR proceed/adopt decisions are additional gates; dormant implementation checkboxes stay open. No selected backend may specialize the manufactured fabric to one test bitstream or bypass configuration-preservation verification.
