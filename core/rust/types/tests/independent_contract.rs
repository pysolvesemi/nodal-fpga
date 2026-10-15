//! Public API tests with independently calculated expectations.
use nf_types::*;

fn key<K: ResourceMarker>(name: &str) -> Key<K> {
    Key::new("fixture", vec![], name).unwrap()
}

#[test]
fn checked_arithmetic_matches_wider_integer_oracle() {
    let values = [
        0,
        1,
        2,
        63,
        64,
        u32::MAX as u64,
        (u32::MAX as u64) + 1,
        (u64::MAX / 2),
        (u64::MAX / 2) + 1,
        u64::MAX - 1,
        u64::MAX,
    ];
    for a in values {
        for b in values {
            let sum = u128::from(a) + u128::from(b);
            let product = u128::from(a) * u128::from(b);
            let actual = BitCount::new(a).checked_add(BitCount::new(b));
            assert_eq!(actual.is_ok(), sum <= u128::from(u64::MAX), "add {a}+{b}");
            if let Ok(value) = actual {
                assert_eq!(u128::from(value.get()), sum);
            } else {
                assert_eq!(actual.unwrap_err().code, Code::Overflow);
            }
            let actual = ByteLength::new(a).checked_mul(b);
            assert_eq!(
                actual.is_ok(),
                product <= u128::from(u64::MAX),
                "mul {a}*{b}"
            );
            if let Ok(value) = actual {
                assert_eq!(u128::from(value.get()), product);
            } else {
                assert_eq!(actual.unwrap_err().code, Code::Overflow);
            }
            let actual = BitOffset::new(a).checked_add(BitCount::new(b));
            assert_eq!(actual.is_ok(), sum <= u128::from(u64::MAX));
            let actual = ByteOffset::new(a).checked_add(ByteLength::new(b));
            assert_eq!(actual.is_ok(), sum <= u128::from(u64::MAX));
        }
        assert_eq!(BitCount::new(a).to_u32().is_ok(), a <= u64::from(u32::MAX));
        assert_eq!(
            ByteLength::new(a).to_usize().is_ok(),
            u128::from(a) <= usize::MAX as u128
        );
    }
}

#[test]
fn half_open_ranges_match_independent_tiny_sets_and_huge_bounds() {
    for start in 0..=8u64 {
        for length in 0..=8u64 {
            let a = BitRange::new(BitOffset::new(start), BitCount::new(length)).unwrap();
            let a_bits: Vec<_> = (0..16)
                .filter(|bit| *bit >= start && *bit < start + length)
                .collect();
            for b_start in 0..=8u64 {
                for b_length in 0..=8u64 {
                    let b =
                        BitRange::new(BitOffset::new(b_start), BitCount::new(b_length)).unwrap();
                    let b_bits: Vec<_> = (0..16)
                        .filter(|bit| *bit >= b_start && *bit < b_start + b_length)
                        .collect();
                    let expected = a_bits.iter().any(|bit| b_bits.contains(bit));
                    assert_eq!(
                        a.overlaps(b),
                        expected,
                        "[{start},{length}] vs [{b_start},{b_length}]"
                    );
                }
            }
            for bit in 0..=16 {
                assert_eq!(a.contains(BitOffset::new(bit)), a_bits.contains(&bit));
            }
        }
    }
    let last = BitRange::new(BitOffset::new(u64::MAX - 3), BitCount::new(3)).unwrap();
    assert_eq!(last.end().get(), u64::MAX);
    assert_eq!(
        BitRange::new(BitOffset::new(u64::MAX - 3), BitCount::new(4))
            .unwrap_err()
            .code,
        Code::Overflow
    );
    let empty = ByteRange::new(ByteOffset::new(u64::MAX), ByteLength::new(0)).unwrap();
    assert_eq!(empty.length().get(), 0);
    assert!(!empty.overlaps(empty));
    assert_eq!(
        BitRange::from_bounds(BitOffset::new(3), BitOffset::new(2))
            .unwrap_err()
            .code,
        Code::InvalidRange
    );
}

#[test]
fn widths_have_no_host_shift_or_truncation_shortcut() {
    for width in [0, 65, 256, u64::MAX] {
        assert_eq!(Width::new(width).unwrap_err().code, Code::Width);
    }
    for width in 1..=64u64 {
        let actual = Width::new(width).unwrap();
        let maximum = ((1u128 << width) - 1) as u64;
        assert!(actual.fits(0));
        assert!(actual.fits(maximum));
        assert_eq!(actual.get(), width as u8);
        assert_eq!(actual.bit_count().get(), width);
        if width != 64 {
            assert!(!actual.fits(maximum + 1));
        }
    }
    assert!(Width::new(64).unwrap().fits(u64::MAX));
}

#[test]
fn scoped_identity_is_structured_exact_and_typed() {
    let a = Key::<Wire>::new("n", vec!["a/b".into(), "c".into()], "d").unwrap();
    let b = Key::<Wire>::new("n", vec!["a".into(), "b/c".into()], "d").unwrap();
    assert_ne!(a, b);
    assert_ne!(key::<Wire>("x").erase(), key::<Bel>("x").erase());
    assert_ne!(key::<Wire>("X"), key::<Wire>("x"));
    assert_ne!(key::<Wire>("é"), key::<Wire>("e\u{301}"));
    assert_eq!(a.namespace().as_str(), "n");
    assert_eq!(
        a.scope().iter().map(Name::as_str).collect::<Vec<_>>(),
        vec!["a/b", "c"]
    );
    assert_eq!(Name::new("é".repeat(64)).unwrap().as_str().len(), 128);
    assert_eq!(Name::new("é".repeat(65)).unwrap_err().code, Code::Limit);
    assert_eq!(Name::new("").unwrap_err().code, Code::InvalidName);
    assert_eq!(
        Key::<Wire>::new("n", vec!["x".into(); 65], "y")
            .unwrap_err()
            .code,
        Code::Limit
    );
    assert_eq!(
        Key::<Wire>::new("n", vec!["x".repeat(128); 32], "y")
            .unwrap_err()
            .code,
        Code::Limit
    );
}

#[test]
fn source_spans_are_checked_half_open_utf8_bytes() {
    let source = "aéz";
    let valid = SourceSpan::new(
        "fixture.nf",
        ByteLength::new(source.len() as u64),
        ByteOffset::new(1),
        ByteOffset::new(3),
    )
    .unwrap();
    assert!(Provenance::new(Some(valid), Some("ordered pin".into())).is_ok());
    assert!(
        SourceSpan::new(
            "fixture.nf",
            ByteLength::new(4),
            ByteOffset::new(4),
            ByteOffset::new(4)
        )
        .is_ok()
    );
    assert_eq!(
        SourceSpan::new(
            "fixture.nf",
            ByteLength::new(4),
            ByteOffset::new(3),
            ByteOffset::new(2)
        )
        .unwrap_err()
        .code,
        Code::InvalidRange
    );
    assert_eq!(
        SourceSpan::new(
            "fixture.nf",
            ByteLength::new(4),
            ByteOffset::new(0),
            ByteOffset::new(5)
        )
        .unwrap_err()
        .code,
        Code::Bounds
    );
    assert!(Provenance::new(None, Some("x".repeat(1025))).is_err());
}

#[test]
fn dense_ids_require_build_partition_kind_and_bound_before_indexing() {
    let a = BuildId::new([0xA; 32]);
    let b = BuildId::new([0xB; 32]);
    let p = PartitionId::new(7);
    let max = TableCount::new(4_294_967_296).unwrap();
    assert_eq!(max.get(), 4_294_967_296);
    assert_eq!(
        TableCount::new(4_294_967_297).unwrap_err().code,
        Code::Bounds
    );
    assert_eq!(
        DenseId::<Wire>::try_from_u64(4_294_967_295).unwrap().get(),
        u32::MAX
    );
    assert_eq!(
        DenseId::<Wire>::try_from_u64(4_294_967_296)
            .unwrap_err()
            .code,
        Code::Overflow
    );
    let table = PartitionTable::<Wire>::new(a, p, max);
    let valid = DenseRef::new(a, p, DenseId::<Wire>::new(u32::MAX));
    assert_eq!(table.resolve(&valid).unwrap(), u32::MAX as usize);
    assert_eq!(
        table
            .resolve(&DenseRef::new(b, p, DenseId::new(0)))
            .unwrap_err()
            .code,
        Code::BuildMismatch
    );
    assert_eq!(
        table
            .resolve(&DenseRef::new(a, PartitionId::new(8), DenseId::new(0)))
            .unwrap_err()
            .code,
        Code::PartitionMismatch
    );
    assert_eq!(
        table
            .resolve_erased(&DenseRef::new(a, p, DenseId::<Bel>::new(0)).erase())
            .unwrap_err()
            .code,
        Code::WrongKind
    );
    let small = PartitionTable::<Wire>::new(a, p, TableCount::new(3).unwrap());
    assert_eq!(
        small
            .resolve(&DenseRef::new(a, p, DenseId::new(3)))
            .unwrap_err()
            .code,
        Code::Bounds
    );
    assert_eq!(
        small
            .resolve(&DenseRef::new(a, p, DenseId::new(2)))
            .unwrap(),
        2
    );
}

#[test]
fn explicit_correspondence_is_total_one_to_one_and_partition_qualified() {
    let build = BuildId::new([1; 32]);
    let expected = vec![key::<Bel>("t0"), key::<Bel>("t1"), key::<Bel>("t2")];
    let tables = vec![
        PartitionTable::<Bel>::new(build, PartitionId::new(0), TableCount::new(2).unwrap()),
        PartitionTable::new(build, PartitionId::new(1), TableCount::new(1).unwrap()),
    ];
    let entries = vec![
        (
            expected[0].clone(),
            DenseRef::new(build, PartitionId::new(0), DenseId::new(0)),
        ),
        (
            expected[1].clone(),
            DenseRef::new(build, PartitionId::new(0), DenseId::new(1)),
        ),
        (
            expected[2].clone(),
            DenseRef::new(build, PartitionId::new(1), DenseId::new(0)),
        ),
    ];
    validate_correspondence(&expected, &entries, &tables).unwrap();
    let mut reversed = entries.clone();
    reversed.reverse();
    validate_correspondence(&expected, &reversed, &tables).unwrap();
    assert_eq!(
        validate_correspondence(&expected, &entries[..2], &tables)
            .unwrap_err()
            .code,
        Code::Correspondence
    );
    let mut duplicated = entries.clone();
    duplicated[2].1 = duplicated[0].1;
    assert_eq!(
        validate_correspondence(&expected, &duplicated, &tables)
            .unwrap_err()
            .code,
        Code::Correspondence
    );
    let mut wrong_build = entries.clone();
    wrong_build[2].1 = DenseRef::new(BuildId::new([2; 32]), PartitionId::new(1), DenseId::new(0));
    assert_eq!(
        validate_correspondence(&expected, &wrong_build, &tables)
            .unwrap_err()
            .code,
        Code::BuildMismatch
    );
    let mut renamed = entries.clone();
    renamed[2].0 = key("same-count-wrong-meaning");
    assert_eq!(
        validate_correspondence(&expected, &renamed, &tables)
            .unwrap_err()
            .code,
        Code::Correspondence
    );
}

#[test]
fn all_seven_public_resource_id_families_remain_nominal() {
    use std::collections::BTreeSet;
    let keys = [
        WireKey::new("fixture", vec![], "same").unwrap().erase(),
        PipKey::new("fixture", vec![], "same").unwrap().erase(),
        BelKey::new("fixture", vec![], "same").unwrap().erase(),
        PinKey::new("fixture", vec![], "same").unwrap().erase(),
        NodeKey::new("fixture", vec![], "same").unwrap().erase(),
        SiteKey::new("fixture", vec![], "same").unwrap().erase(),
        FieldKey::new("fixture", vec![], "same").unwrap().erase(),
    ];
    assert_eq!(keys.into_iter().collect::<BTreeSet<_>>().len(), 7);
    let build = BuildId::new([42; 32]);
    let partition = PartitionId::new(9);
    let references = [
        DenseRef::new(build, partition, WireId::new(7)).erase(),
        DenseRef::new(build, partition, PipId::new(7)).erase(),
        DenseRef::new(build, partition, BelId::new(7)).erase(),
        DenseRef::new(build, partition, PinId::new(7)).erase(),
        DenseRef::new(build, partition, NodeId::new(7)).erase(),
        DenseRef::new(build, partition, SiteId::new(7)).erase(),
        DenseRef::new(build, partition, FieldId::new(7)).erase(),
    ];
    assert_eq!(
        references
            .into_iter()
            .map(|r| r.kind())
            .collect::<BTreeSet<_>>()
            .len(),
        7
    );
}
