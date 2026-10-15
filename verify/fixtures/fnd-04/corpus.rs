// Independent literal expectations frozen before production implementation.
// Input names are generic fixture data, never special cases in core.
pub const MODE_MASKS: [u8; 6] = [0b1111, 0b0011, 0b1100, 0b0101, 0b1010, 0b0010];
pub const LINE_ONE_OWNERS: &[&str] = &["t0"];
pub const LINE_THREE_OWNERS: &[&str] = &["t0", "t1", "t2"];
pub const LINE_THREE_EDGES: &[(&str, &str)] = &[("t0", "t1"), ("t1", "t2")];
pub const SPARSE_OWNERS: &[&str] = &["t0", "t2"];
pub const SPARSE_EDGES: &[(&str, &str)] = &[];
pub const EXPLICIT_BYPASS: &[(&str, &str)] = &[("t0", "t2")];
pub const ORDERED_MUX: &[&str] = &["A", "B", "C"];
pub const MUTATION_SEED: u64 = 0xF004_1D3E_5EED;

// Enumerating individual bits is deliberately independent of production masks,
// interval overlap predicates, alias resolution and mode guard evaluation.
pub fn tiny_bits(start: u8, length: u8) -> Vec<u8> {
    (0..16)
        .filter(|bit| *bit >= start && u16::from(*bit) < u16::from(start) + u16::from(length))
        .collect()
}
pub fn writes_agree(left: u64, right: u64, width: u8) -> bool {
    (0..width).all(|bit| (left >> bit) % 2 == (right >> bit) % 2)
}
