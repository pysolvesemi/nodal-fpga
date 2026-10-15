# Reference inputs and upstream attribution

`BEL/nf_tiny_io.v`, tile/matrix/configuration CSVs, shape CSVs and
`generate.py` are independently authored Nodal-FPGA reference inputs.
They are not generated output and are not derived from a Nodal emitter.

The generator runner copies, without modification, these files from FABulous
commit `d2fc49dade524a4f78062a3a38b213e9c08d6b04` (tag `v2.0.0`):

- `fabulous/fabric_files/FABulous_project_template_verilog/Tile/LUT4AB/LUT4c_frame_config_dffesr.v`
- `fabulous/fabric_files/FABulous_project_template_verilog/Fabric/models_pack.v`

The LUT source carries Copyright 2021 University of Manchester and Apache-2.0
notices. The repository license is retained here as `LICENSE.FABulous`; the
models pack has no file-specific license header and is covered by the upstream
repository Apache-2.0 license. No upstream NOTICE file exists at this revision.
Preserve these notices and identify any future modifications. Dependency
licenses still require FND-06/FND-07 inventory before redistribution.

`reference.json` records immutable source paths and SHA-256 values, along with
all authored-input hashes. Refer to `docs/contracts/nf-tiny.md` for intended
commands and the distinction between source inspection and execution.
