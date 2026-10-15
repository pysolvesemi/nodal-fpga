// Template boundary for behavior.write_simulation: physical fabric ports only.
// LOCAL-A6D3 / SECONDARY-A6D3: literal A6D3 table, every instance/address.
// REG-R0 / REG-R1 / FF0-STATE-R0 / FF0-STATE-R1: exact accepted edge traces.
// INSTANCE-CONFIG-WORD / COLUMN-HOLD: real FrameData and FrameStrobe writes,
// hierarchical READS of ConfigBits, complement, actual consumers and LUT_flop.
// LINK: configure predecessor AAAA, downstream source1, local held opposite.
// No force/release, EMULATION, guessed initial q, or candidate-derived oracle.
// The generated concrete tb.sv and hash are retained for each shape/run.
