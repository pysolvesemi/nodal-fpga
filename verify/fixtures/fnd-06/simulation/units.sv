// Concrete unit testbenches are materialized by behavior.write_lut_unit and
// behavior.write_units from the separately frozen semantic_cases.json literals.
// UNIT-LUT: 32 asymmetric vectors and 256 genuine one-hot identity vectors.
// UNIT-REG: both exact edge traces, both output modes, actual LUT_flop state.
// UNIT-MUX and UNIT-FIXED: actual generated switches, ordered inputs and fixed links.
// UNIT-CONFIG: physical latch writes, all Q/QN bits, hold/transparent/padding.
// Actual generated tb.sv source, exact observation lines and hashes are retained.
