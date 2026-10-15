//! Independent public-boundary validation; expected answers never call production helpers.
use nf_arch_ir::*;
use nf_types as ty;
use ty::{
    BitCount, BitOffset, BitRange, Code, Diagnostic, Key, Name, PartitionId, Provenance, Width,
};

mod corpus {
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
}

fn name(s: &str) -> Name {
    Name::new(s).unwrap()
}
fn origin(offset: u64) -> Provenance {
    Provenance::new(
        Some(
            ty::SourceSpan::new(
                "independent.nf",
                ty::ByteLength::new(1000),
                ty::ByteOffset::new(offset),
                ty::ByteOffset::new(offset + 1),
            )
            .unwrap(),
        ),
        None,
    )
    .unwrap()
}
fn reference(path: &[&str], local: &str) -> ResourceRef {
    ResourceRef {
        path: path.iter().map(|x| name(x)).collect(),
        name: name(local),
        kind: ResourceKind::Bel,
        provenance: origin(10),
    }
}
fn endpoint(path: &[&str], local: &str, pin: &str) -> Endpoint {
    Endpoint {
        resource: reference(path, local),
        pin: name(pin),
        provenance: origin(20),
    }
}
fn field(path: &[&str], local: &str) -> FieldRef {
    FieldRef {
        path: path.iter().map(|x| name(x)).collect(),
        name: name(local),
        provenance: origin(30),
    }
}
fn root(local: &str, partition: u32) -> Instance {
    Instance {
        name: name(local),
        template: Key::new("independent", vec![], "T").unwrap(),
        partition: Some(PartitionId::new(partition)),
        domains: vec![],
        provenance: origin(40),
    }
}
fn feature(local: &str, start: u64, width: u64) -> Feature {
    Feature {
        name: name(local),
        owner: reference(&[], "r"),
        storage: name("s"),
        range: BitRange::new(BitOffset::new(start), BitCount::new(width)).unwrap(),
        width: Width::new(width).unwrap(),
        domain: ValueDomain::Any,
        guard: vec![],
        alias_of: None,
        provenance: origin(50),
    }
}
fn base() -> Architecture {
    let mut a = Architecture::new(name("independent"));
    a.partitions = vec![PartitionId::new(0)];
    let type_key = Key::new("independent", vec![], "R").unwrap();
    a.resource_types.push(ResourceType {
        key: type_key.clone(),
        kind: ResourceKind::Bel,
        pins: vec![
            Pin {
                name: name("I"),
                direction: Direction::Input,
                width: BitCount::new(1),
                provenance: origin(1),
            },
            Pin {
                name: name("O"),
                direction: Direction::Output,
                width: BitCount::new(1),
                provenance: origin(2),
            },
        ],
        modes: vec![name("a"), name("b")],
        provenance: origin(3),
    });
    let mut t = Template::new(Key::new("independent", vec![], "T").unwrap());
    t.resources.push(Resource {
        name: name("r"),
        kind: ResourceKind::Bel,
        resource_type: type_key,
        alias_of: None,
        domains: vec![],
        provenance: origin(4),
    });
    t.storage.push(Storage {
        name: name("s"),
        owner: reference(&[], "r"),
        bits: BitCount::new(128),
        provenance: origin(5),
    });
    t.features.push(feature("owner", 4, 2));
    a.templates.push(t);
    a.roots.push(root("t0", 0));
    a
}
fn fixed(local: &str, source: &str, destination: &str) -> Connection {
    Connection {
        name: name(local),
        sources: vec![endpoint(&[source], "r", "O")],
        destination: endpoint(&[destination], "r", "I"),
        selector: None,
        provenance: origin(60),
    }
}
fn setting(path: &[&str], local: &str, value: u64, offset: u64) -> FeatureSetting {
    FeatureSetting {
        field: field(path, local),
        value,
        provenance: origin(offset),
    }
}
fn require_code(result: Result<(), Vec<Diagnostic>>, expected: Code) -> Vec<Diagnostic> {
    let diagnostics = result.expect_err("single-defect witness must reject");
    assert!(
        diagnostics.iter().any(|d| d.code == expected),
        "expected {expected:?}; got {diagnostics:?}"
    );
    for d in &diagnostics {
        assert!(!d.message.is_empty());
        assert!(!d.remedy.is_empty());
    }
    diagnostics
}
fn architecture_code(a: &Architecture, expected: Code) -> Vec<Diagnostic> {
    require_code(
        validate_architecture(a, &ValidationLimits::default()).map(|_| ()),
        expected,
    )
}
fn line(owners: &[&str], edges: &[(&str, &str)]) -> Architecture {
    let mut a = base();
    a.roots = owners.iter().map(|n| root(n, 0)).collect();
    a.connections = edges
        .iter()
        .enumerate()
        .map(|(i, (from, to))| fixed(&format!("edge{i}"), from, to))
        .collect();
    a
}
fn graph(a: &Architecture) -> Vec<(String, String)> {
    a.connections
        .iter()
        .map(|e| {
            (
                e.sources[0].resource.path[0].as_str().to_string(),
                e.destination.resource.path[0].as_str().to_string(),
            )
        })
        .collect()
}
fn expected_graph(edges: &[(&str, &str)]) -> Vec<(String, String)> {
    edges
        .iter()
        .map(|(a, b)| (a.to_string(), b.to_string()))
        .collect()
}

#[test]
fn independently_enumerated_line_sparse_and_partitioned_ownership() {
    for (owners, edges) in [
        (corpus::LINE_ONE_OWNERS, corpus::SPARSE_EDGES),
        (corpus::LINE_THREE_OWNERS, corpus::LINE_THREE_EDGES),
        (corpus::SPARSE_OWNERS, corpus::SPARSE_EDGES),
        (corpus::SPARSE_OWNERS, corpus::EXPLICIT_BYPASS),
    ] {
        let a = line(owners, edges);
        let validated = validate_architecture(&a, &ValidationLimits::default()).unwrap();
        assert_eq!(validated.architecture(), &a);
        assert_eq!(validated.architecture().templates.len(), 1);
        assert_eq!(
            validated
                .architecture()
                .roots
                .iter()
                .map(|i| i.name.as_str())
                .collect::<Vec<_>>(),
            owners
        );
        assert_eq!(graph(validated.architecture()), expected_graph(edges));
        let selection = Selection {
            modes: vec![],
            features: owners
                .iter()
                .enumerate()
                .map(|(i, n)| setting(&[n], "owner", (i % 4) as u64, 100 + i as u64))
                .collect(),
        };
        validate_selection(&validated, &selection).unwrap();
    }
    let mut partitioned = line(corpus::LINE_THREE_OWNERS, corpus::LINE_THREE_EDGES);
    partitioned.partitions.push(PartitionId::new(1));
    partitioned.roots[2].partition = Some(PartitionId::new(1));
    let validated = validate_architecture(&partitioned, &ValidationLimits::default()).unwrap();
    assert_eq!(
        graph(validated.architecture()),
        expected_graph(corpus::LINE_THREE_EDGES)
    );
    let mut dangling = partitioned.clone();
    dangling.roots.remove(1);
    architecture_code(&dangling, Code::Missing);
    let mut lost_edge = partitioned.clone();
    lost_edge.connections.pop();
    assert_ne!(graph(&lost_edge), expected_graph(corpus::LINE_THREE_EDGES));
    let invented_bypass = line(corpus::SPARSE_OWNERS, corpus::EXPLICIT_BYPASS);
    assert_ne!(
        graph(&invented_bypass),
        expected_graph(corpus::SPARSE_EDGES)
    );
}

#[test]
fn endpoint_single_defect_mutations_are_source_aware() {
    let original = line(corpus::LINE_THREE_OWNERS, corpus::LINE_THREE_EDGES);
    let mut wrong = original.clone();
    wrong.connections[0].sources[0].pin = name("I");
    let d = architecture_code(&wrong, Code::Direction);
    assert!(d.iter().any(|d| d.primary != Provenance::default()));
    assert!(
        d.iter()
            .filter(|d| d.code == Code::Direction)
            .all(|d| d.stage == ty::Stage::Architecture && d.key.is_some()),
        "direction diagnostics need a stable portable key and operation stage: {d:?}"
    );
    let mut wrong = original.clone();
    wrong.connections[0].destination.pin = name("O");
    architecture_code(&wrong, Code::Direction);
    let mut wrong = original.clone();
    wrong.connections[0].destination.resource.kind = ResourceKind::Wire;
    architecture_code(&wrong, Code::WrongKind);
    let mut wrong = original.clone();
    wrong.connections[0].destination.pin = name("missing");
    architecture_code(&wrong, Code::Missing);
    let mut wrong = original.clone();
    wrong.resource_types[0].pins[0].width = BitCount::new(2);
    architecture_code(&wrong, Code::Width);
    let mut wrong = original.clone();
    wrong.templates[0].resources[0].resource_type =
        Key::new("independent", vec![], "missing").unwrap();
    architecture_code(&wrong, Code::Missing);
    let mut wrong = original.clone();
    wrong.roots[0].partition = Some(PartitionId::new(99));
    architecture_code(&wrong, Code::PartitionMismatch);
    let mut wrong = original.clone();
    wrong.roots.push(wrong.roots[0].clone());
    architecture_code(&wrong, Code::Duplicate);
    let mut wrong = original.clone();
    let mut e = wrong.connections[0].clone();
    e.name = name("competing");
    wrong.connections.push(e);
    architecture_code(&wrong, Code::Connection);
}

#[test]
fn finite_template_hierarchy_is_distinct_from_legal_routing_cycle() {
    let routing = line(&["t0", "t1"], &[("t0", "t1"), ("t1", "t0")]);
    validate_architecture(&routing, &ValidationLimits::default()).unwrap();
    let mut recursive = base();
    let mut child = root("self", 0);
    child.partition = None;
    recursive.templates[0].children.push(child);
    architecture_code(&recursive, Code::TemplateCycle);
    let mut mutual = base();
    let a_key = mutual.templates[0].key.clone();
    let b_key = Key::new("independent", vec![], "B").unwrap();
    let mut b = Template::new(b_key.clone());
    let mut child = root("b", 0);
    child.partition = None;
    child.template = b_key;
    mutual.templates[0].children.push(child);
    let mut child = root("a", 0);
    child.partition = None;
    child.template = a_key;
    b.children.push(child);
    mutual.templates.push(b);
    architecture_code(&mutual, Code::TemplateCycle);
}

#[test]
fn ordered_three_way_mux_rejects_reserved_code_and_preserves_source_order() {
    let mut a = base();
    for n in corpus::ORDERED_MUX {
        let mut r = a.templates[0].resources[0].clone();
        r.name = name(n);
        a.templates[0].resources.push(r);
    }
    a.templates[0].features[0].domain = ValueDomain::Range {
        minimum: 0,
        maximum: 2,
    };
    a.templates[0].connections.push(Connection {
        name: name("mux"),
        sources: corpus::ORDERED_MUX
            .iter()
            .map(|n| endpoint(&[], n, "O"))
            .collect(),
        destination: endpoint(&[], "r", "I"),
        selector: Some(field(&[], "owner")),
        provenance: origin(61),
    });
    let validated = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    for select in 0..3 {
        validate_selection(
            &validated,
            &Selection {
                modes: vec![],
                features: vec![setting(&["t0"], "owner", select, 70)],
            },
        )
        .unwrap();
        assert_eq!(
            validated.architecture().templates[0].connections[0].sources[select as usize]
                .resource
                .name
                .as_str(),
            corpus::ORDERED_MUX[select as usize]
        );
    }
    require_code(
        validate_selection(
            &validated,
            &Selection {
                modes: vec![],
                features: vec![setting(&["t0"], "owner", 3, 71)],
            },
        ),
        Code::Value,
    );
    let mut order_mutation = a.clone();
    order_mutation.templates[0].connections[0]
        .sources
        .swap(0, 1);
    let changed = validate_architecture(&order_mutation, &ValidationLimits::default()).unwrap();
    assert_ne!(
        changed.architecture().templates[0].connections[0].sources[0]
            .resource
            .name
            .as_str(),
        corpus::ORDERED_MUX[0]
    );
    let mut illegal_domain = a.clone();
    illegal_domain.templates[0].features[0].domain = ValueDomain::Any;
    architecture_code(&illegal_domain, Code::Domain);
}

fn choice(group: &str, mode: &str) -> ModeChoice {
    ModeChoice {
        group: name(group),
        mode: name(mode),
        provenance: origin(80),
    }
}
fn guard(index: usize) -> Vec<ModeChoice> {
    match index {
        0 => vec![],
        1 => vec![choice("g0", "a")],
        2 => vec![choice("g0", "b")],
        3 => vec![choice("g1", "a")],
        4 => vec![choice("g1", "b")],
        5 => vec![choice("g0", "a"), choice("g1", "b")],
        _ => unreachable!(),
    }
}
fn sharing(left_guard: usize, right_guard: usize) -> Architecture {
    let mut a = base();
    let mut r = a.templates[0].resources[0].clone();
    r.name = name("r1");
    a.templates[0].resources.push(r);
    for (group, resource) in [("g0", "r"), ("g1", "r1")] {
        a.templates[0].mode_groups.push(ModeGroup {
            name: name(group),
            resources: vec![reference(&[], resource)],
            modes: vec![name("a"), name("b")],
            provenance: origin(81),
        });
    }
    for (n, g) in [("left", left_guard), ("right", right_guard)] {
        let mut alias = feature(n, 4, 2);
        alias.alias_of = Some(field(&[], "owner"));
        alias.guard = guard(g);
        a.templates[0].features.push(alias);
    }
    a
}
fn modes(index: usize) -> Vec<ModeSetting> {
    vec![
        ModeSetting {
            path: vec![name("t0")],
            group: name("g0"),
            mode: name(if index < 2 { "a" } else { "b" }),
            provenance: origin(82),
        },
        ModeSetting {
            path: vec![name("t0")],
            group: name("g1"),
            mode: name(if index.is_multiple_of(2) { "a" } else { "b" }),
            provenance: origin(83),
        },
    ]
}

#[test]
fn exhaustive_guard_masks_and_bit_writes_are_an_independent_oracle() {
    let mut cases = 0;
    let mut accepted = 0;
    let mut conflicts = 0;
    let mut inactive = 0;
    for left_guard in 0..6 {
        for right_guard in 0..6 {
            let a = sharing(left_guard, right_guard);
            let validated = validate_architecture(&a, &ValidationLimits::default()).unwrap();
            for mode in 0..4 {
                for left in 0..4u64 {
                    for right in 0..4u64 {
                        let selection = Selection {
                            modes: modes(mode),
                            features: vec![
                                setting(&["t0"], "left", left, 90),
                                setting(&["t0"], "right", right, 91),
                            ],
                        };
                        let result = validate_selection(&validated, &selection);
                        let both_active = corpus::MODE_MASKS[left_guard] & (1 << mode) != 0
                            && corpus::MODE_MASKS[right_guard] & (1 << mode) != 0;
                        if !both_active {
                            require_code(result, Code::Inactive);
                            inactive += 1;
                        } else if !corpus::writes_agree(left, right, 2) {
                            require_code(result, Code::Conflict);
                            conflicts += 1;
                        } else {
                            result.unwrap();
                            accepted += 1;
                        }
                        cases += 1;
                    }
                }
            }
        }
    }
    assert_eq!(cases, 2304);
    assert_eq!((accepted, conflicts, inactive), (172, 516, 1616));
}

#[test]
fn selection_completeness_alias_only_values_and_exclusive_modes() {
    let a = sharing(1, 2);
    let validated = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    for (mode, active_name, value) in [(0, "left", 0), (2, "right", 3)] {
        validate_selection(
            &validated,
            &Selection {
                modes: modes(mode),
                features: vec![setting(&["t0"], active_name, value, 100)],
            },
        )
        .unwrap();
    }
    validate_selection(
        &validated,
        &Selection {
            modes: modes(0),
            features: vec![setting(&["t0"], "owner", 2, 100)],
        },
    )
    .unwrap();
    require_code(
        validate_selection(
            &validated,
            &Selection {
                modes: modes(0),
                features: vec![],
            },
        ),
        Code::MissingSelection,
    );
    require_code(
        validate_selection(
            &validated,
            &Selection {
                modes: vec![],
                features: vec![setting(&["t0"], "owner", 0, 100)],
            },
        ),
        Code::MissingSelection,
    );
    let mut duplicate = modes(0);
    let mut another = duplicate[0].clone();
    another.mode = name("b");
    duplicate.push(another);
    require_code(
        validate_selection(
            &validated,
            &Selection {
                modes: duplicate,
                features: vec![setting(&["t0"], "owner", 0, 100)],
            },
        ),
        Code::Mode,
    );
    let mut unsupported = modes(0);
    unsupported[0].mode = name("asynchronous-reset");
    require_code(
        validate_selection(
            &validated,
            &Selection {
                modes: unsupported,
                features: vec![setting(&["t0"], "owner", 0, 100)],
            },
        ),
        Code::Mode,
    );
    let mut owner_inactive = a.clone();
    owner_inactive.templates[0].features[0].guard = guard(2);
    let valid = validate_architecture(&owner_inactive, &ValidationLimits::default()).unwrap();
    validate_selection(
        &valid,
        &Selection {
            modes: modes(0),
            features: vec![setting(&["t0"], "left", 1, 100)],
        },
    )
    .unwrap();
}

#[test]
fn completely_inactive_owner_class_requires_no_default_or_write() {
    let mut a = sharing(2, 2);
    a.templates[0].features[0].guard = guard(2);
    let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    validate_selection(
        &valid,
        &Selection {
            modes: modes(0),
            features: vec![],
        },
    )
    .unwrap();
    require_code(
        validate_selection(
            &valid,
            &Selection {
                modes: modes(0),
                features: vec![setting(&["t0"], "owner", 0, 101)],
            },
        ),
        Code::Inactive,
    );
}

#[test]
fn undeclared_overlap_follows_tiny_bitsets_even_under_exclusive_guards() {
    for left_start in 0..8u8 {
        for right_start in 0..8u8 {
            let mut a = sharing(1, 2);
            a.templates[0].features.truncate(1);
            a.templates[0].features[0].range =
                BitRange::new(BitOffset::new(u64::from(left_start)), BitCount::new(2)).unwrap();
            a.templates[0].features[0].guard = guard(1);
            let mut other = feature("other", u64::from(right_start), 2);
            other.guard = guard(2);
            a.templates[0].features.push(other);
            let left = corpus::tiny_bits(left_start, 2);
            let right = corpus::tiny_bits(right_start, 2);
            let overlap = left.iter().any(|bit| right.contains(bit));
            let result = validate_architecture(&a, &ValidationLimits::default());
            if overlap {
                require_code(result.map(|_| ()), Code::Overlap);
            } else {
                result.unwrap();
            }
        }
    }
    let mut contained = base();
    contained.templates[0].features[0] = feature("owner", 4, 4);
    contained.templates[0].features.push(feature("inner", 5, 1));
    architecture_code(&contained, Code::Overlap);
}

#[test]
fn alias_and_guard_single_defect_mutations_require_the_intended_categories() {
    let original = sharing(0, 0);
    let mut a = original.clone();
    a.templates[0].features[1].alias_of = Some(field(&[], "missing"));
    architecture_code(&a, Code::Missing);
    let mut a = original.clone();
    a.templates[0].features[1].alias_of = Some(field(&[], "right"));
    architecture_code(&a, Code::AliasChain);
    let mut a = original.clone();
    a.templates[0].features[1].alias_of = Some(field(&[], "right"));
    a.templates[0].features[2].alias_of = Some(field(&[], "left"));
    architecture_code(&a, Code::AliasCycle);
    let mut a = original.clone();
    a.templates[0].features[1].alias_of = Some(field(&["other"], "owner"));
    architecture_code(&a, Code::WrongScope);
    let mut a = original.clone();
    a.templates[0].features[1].range = BitRange::new(BitOffset::new(5), BitCount::new(2)).unwrap();
    architecture_code(&a, Code::AliasMismatch);
    let mut a = original.clone();
    a.templates[0].features[1].width = Width::new(1).unwrap();
    architecture_code(&a, Code::AliasMismatch);
    let mut a = original.clone();
    a.templates[0].features[1].domain = ValueDomain::Set(vec![0, 1]);
    architecture_code(&a, Code::AliasMismatch);
    let mut a = original.clone();
    a.templates[0].features[1].guard = vec![choice("g0", "a"), choice("g0", "b")];
    architecture_code(&a, Code::Guard);
    let mut a = original.clone();
    a.templates[0].features[1].guard = vec![choice("g0", "missing")];
    architecture_code(&a, Code::Mode);
    let mut a = original.clone();
    a.templates[0].features[1].owner = reference(&[], "missing");
    architecture_code(&a, Code::Missing);
}

#[test]
fn independent_domain_memberships_overlap_without_conflating_kinds() {
    let mut a = line(&["t0", "t1"], &[]);
    for (n, kind) in [
        ("C0", DomainClass::Clock),
        ("P0", DomainClass::Power),
        ("P1", DomainClass::Power),
        ("Q0", DomainClass::Configuration),
    ] {
        a.domains.push(Domain {
            key: Key::new("independent", vec![], n).unwrap(),
            kind,
            provenance: origin(110),
        });
    }
    for index in 0..2 {
        a.roots[index].domains = [0, 1 + index, 3]
            .iter()
            .map(|i| DomainRef {
                key: a.domains[*i].key.clone(),
                kind: a.domains[*i].kind,
                provenance: origin(111),
            })
            .collect();
    }
    let validated = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    assert_eq!(
        validated.architecture().roots[0].domains[0].key,
        validated.architecture().roots[1].domains[0].key
    );
    assert_ne!(
        validated.architecture().roots[0].domains[1].key,
        validated.architecture().roots[1].domains[1].key
    );
    assert_eq!(
        validated.architecture().roots[0].domains[2].key,
        validated.architecture().roots[1].domains[2].key
    );
    let mut wrong = a.clone();
    wrong.roots[0].domains[0].kind = DomainClass::Power;
    architecture_code(&wrong, Code::WrongKind);
    let mut wrong = a.clone();
    wrong.roots[0].domains[0].key = Key::new("independent", vec![], "missing").unwrap();
    architecture_code(&wrong, Code::Missing);
}

#[test]
fn keyed_reordering_keeps_diagnostics_and_original_declarations() {
    let mut a = line(corpus::LINE_THREE_OWNERS, corpus::LINE_THREE_EDGES);
    a.connections[0].sources[0].pin = name("missing-source");
    a.connections[1].destination.pin = name("missing-destination");
    let expected = validate_architecture(&a, &ValidationLimits::default()).unwrap_err();
    a.roots.reverse();
    a.connections.reverse();
    a.resource_types.reverse();
    a.templates.reverse();
    let actual = validate_architecture(&a, &ValidationLimits::default()).unwrap_err();
    assert_eq!(actual, expected);
    let a = sharing(0, 0);
    let validated = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    let mut selection = Selection {
        modes: modes(0),
        features: vec![
            setting(&["t0"], "left", 1, 120),
            setting(&["t0"], "right", 2, 121),
        ],
    };
    let expected = validate_selection(&validated, &selection).unwrap_err();
    assert!(expected.iter().any(|d| d.code == Code::Conflict
        && !d.related.is_empty()
        && d.primary != Provenance::default()
        && d.stage == ty::Stage::Selection
        && d.key.is_some()));
    selection.features.reverse();
    selection.modes.reverse();
    assert_eq!(
        validate_selection(&validated, &selection).unwrap_err(),
        expected
    );
}

#[test]
fn huge_storage_positions_do_not_materialize_bit_arrays() {
    let mut a = base();
    a.templates[0].storage[0].bits = BitCount::new(u64::MAX);
    a.templates[0].features[0] = feature("owner", u64::MAX - 64, 64);
    let validated = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    validate_selection(
        &validated,
        &Selection {
            modes: vec![],
            features: vec![setting(&["t0"], "owner", u64::MAX, 130)],
        },
    )
    .unwrap();
}

fn hierarchy(depth: usize) -> Architecture {
    assert!(depth > 0);
    let mut a = base();
    for level in 1..depth {
        let previous = a.templates.last().unwrap().key.clone();
        let mut wrapper =
            Template::new(Key::new("independent", vec![], format!("wrapper{level}")).unwrap());
        let mut child = root(&format!("child{level}"), 0);
        child.partition = None;
        child.template = previous;
        wrapper.children.push(child);
        a.templates.push(wrapper);
    }
    a.roots[0].template = a.templates.last().unwrap().key.clone();
    a
}

#[test]
fn bounded_count_depth_partition_observations_preserve_compact_declarations() {
    use std::time::Instant;
    for count in [1usize, 16, 256, 4096] {
        let mut a = base();
        a.roots = (0..count).map(|i| root(&format!("tile{i}"), 0)).collect();
        let start = Instant::now();
        let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
        let elapsed = start.elapsed();
        let repeat = validate_architecture(&a, &ValidationLimits::default()).unwrap();
        assert_eq!(valid.stats(), repeat.stats());
        assert_eq!(valid.architecture(), repeat.architecture());
        assert_eq!(valid.architecture().templates.len(), 1);
        assert_eq!(valid.architecture().templates[0].resources.len(), 1);
        assert_eq!(valid.architecture().roots.len(), count);
        let selection = Selection {
            modes: vec![],
            features: (0..count)
                .map(|i| setting(&[&format!("tile{i}")], "owner", (i % 4) as u64, 170))
                .collect(),
        };
        let selection_start = Instant::now();
        validate_selection(&valid, &selection).unwrap();
        println!(
            "FND04-SCALE selection_instances={count} elapsed_ns={}",
            selection_start.elapsed().as_nanos()
        );
        println!(
            "FND04-SCALE instances={count} templates=1 shallow_instance_capacity_bytes={} instance_name_payload_bytes={} elapsed_ns={} stats={:?}",
            a.roots.capacity() * std::mem::size_of::<Instance>(),
            a.roots.iter().map(|r| r.name.as_str().len()).sum::<usize>(),
            elapsed.as_nanos(),
            valid.stats()
        );
    }
    for depth in [1, 8, 32, 64] {
        let a = hierarchy(depth);
        let start = Instant::now();
        let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
        assert_eq!(valid.architecture().templates.len(), depth);
        println!(
            "FND04-SCALE hierarchy_depth={depth} templates={depth} elapsed_ns={} stats={:?}",
            start.elapsed().as_nanos(),
            valid.stats()
        );
        let mut path = vec![name("t0")];
        for level in (1..depth).rev() {
            path.push(name(&format!("child{level}")));
        }
        let selection = Selection {
            modes: vec![],
            features: vec![FeatureSetting {
                field: FieldRef {
                    path,
                    name: name("owner"),
                    provenance: origin(140),
                },
                value: 1,
                provenance: origin(141),
            }],
        };
        validate_selection(&valid, &selection).unwrap();
    }
    architecture_code(&hierarchy(65), Code::Limit);
    for partitions in [1u32, 2, 4] {
        let mut a = base();
        a.partitions = (0..partitions).map(PartitionId::new).collect();
        a.roots = (0..8)
            .map(|i| root(&format!("tile{i}"), i % partitions))
            .collect();
        a.connections = (0..7)
            .map(|i| {
                fixed(
                    &format!("edge{i}"),
                    &format!("tile{i}"),
                    &format!("tile{}", i + 1),
                )
            })
            .collect();
        let start = Instant::now();
        let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
        assert_eq!(valid.architecture().connections.len(), 7);
        let crossings = (0..7)
            .filter(|i| i % partitions != (i + 1) % partitions)
            .count();
        assert_eq!(crossings, if partitions == 1 { 0 } else { 7 });
        println!(
            "FND04-SCALE partitions={partitions} links=7 cross_partition_links={crossings} elapsed_ns={}",
            start.elapsed().as_nanos()
        );
    }
}

#[test]
fn caller_and_exhausted_limits_fail_closed_deterministically() {
    let a = base();
    for limits in [
        ValidationLimits {
            max_work: 1,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_declarations: 1,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_references: 1,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_collection: 1,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_depth: 0,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_work: 1_000_001,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_key_component_bytes: 1,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_key_bytes: 1,
            ..ValidationLimits::default()
        },
        ValidationLimits {
            max_provenance_bytes: 1,
            ..ValidationLimits::default()
        },
    ] {
        let errors = validate_architecture(&a, &limits).unwrap_err();
        assert_eq!(errors.len(), 1);
        assert_eq!(errors[0].code, Code::Limit);
    }
    let mut invalid = line(corpus::LINE_THREE_OWNERS, corpus::LINE_THREE_EDGES);
    invalid.connections[0].sources[0].pin = name("absent-a");
    invalid.connections[1].sources[0].pin = name("absent-b");
    let limits = ValidationLimits {
        max_diagnostics: 1,
        ..ValidationLimits::default()
    };
    let first = validate_architecture(&invalid, &limits).unwrap_err();
    assert_eq!(first.len(), 1);
    assert_eq!(first[0].code, Code::Limit);
    invalid.connections.reverse();
    invalid.roots.reverse();
    assert_eq!(validate_architecture(&invalid, &limits).unwrap_err(), first);
}

#[test]
fn reproducible_generated_single_defect_models_have_specific_mutation_witnesses() {
    let mut state = corpus::MUTATION_SEED;
    let mut mutation_counts = [0usize; 4];
    for trial in 0..128 {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        let count = 2 + (state as usize % 7);
        let owners: Vec<_> = (0..count).map(|i| format!("n{i}")).collect();
        let edges: Vec<_> = (0..count - 1)
            .map(|i| (owners[i].as_str(), owners[i + 1].as_str()))
            .collect();
        let names: Vec<_> = owners.iter().map(String::as_str).collect();
        let mut a = line(&names, &edges);
        validate_architecture(&a, &ValidationLimits::default()).unwrap();
        let index = (state as usize / 7) % (count - 1);
        let mutation = trial % 4;
        mutation_counts[mutation] += 1;
        let expected = match mutation {
            0 => {
                a.connections[index].destination.resource.path = vec![name("missing")];
                Code::Missing
            }
            1 => {
                a.connections[index].sources[0].pin = name("I");
                Code::Direction
            }
            2 => {
                a.connections[index].destination.resource.kind = ResourceKind::Wire;
                Code::WrongKind
            }
            3 => {
                a.roots[index].partition = Some(PartitionId::new(999));
                Code::PartitionMismatch
            }
            _ => unreachable!(),
        };
        architecture_code(&a, expected);
    }
    assert_eq!(mutation_counts, [32, 32, 32, 32]);
}

#[test]
fn a_resource_cannot_acquire_two_mode_owners_through_an_alias() {
    let mut a = sharing(0, 0);
    a.templates[0].mode_groups[1].resources = vec![reference(&[], "r")];
    architecture_code(&a, Code::Mode);
    let mut a = sharing(0, 0);
    let mut alias = a.templates[0].resources[0].clone();
    alias.name = name("r-alias");
    alias.alias_of = Some(reference(&[], "r"));
    a.templates[0].resources.push(alias);
    a.templates[0].mode_groups[1].resources = vec![reference(&[], "r-alias")];
    architecture_code(&a, Code::Mode);
}

#[test]
fn resource_aliases_require_direct_scoped_owners_and_do_not_own_storage() {
    let mut original = base();
    let mut alias = original.templates[0].resources[0].clone();
    alias.name = name("alias");
    alias.alias_of = Some(reference(&[], "r"));
    original.templates[0].resources.push(alias);
    validate_architecture(&original, &ValidationLimits::default()).unwrap();
    let mut a = original.clone();
    a.templates[0].resources[1].alias_of = Some(reference(&[], "missing"));
    architecture_code(&a, Code::Missing);
    let mut a = original.clone();
    a.templates[0].resources[1].alias_of = Some(reference(&["child"], "r"));
    architecture_code(&a, Code::WrongScope);
    let mut a = original.clone();
    a.templates[0].resources[0].alias_of = Some(reference(&[], "alias"));
    architecture_code(&a, Code::AliasCycle);
    let mut a = original.clone();
    let mut chain = a.templates[0].resources[1].clone();
    chain.name = name("chain");
    chain.alias_of = Some(reference(&[], "alias"));
    a.templates[0].resources.push(chain);
    architecture_code(&a, Code::AliasChain);
    let mut a = original.clone();
    a.templates[0].storage[0].owner = reference(&[], "alias");
    architecture_code(&a, Code::AliasMismatch);
}

#[test]
fn finite_value_sets_preserve_set_semantics_and_reject_out_of_domain_values() {
    let mut a = sharing(0, 0);
    for f in &mut a.templates[0].features {
        f.domain = ValueDomain::Set(vec![3, 1]);
    }
    a.templates[0].features[1].domain = ValueDomain::Set(vec![1, 3]);
    let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    for value in [1, 3] {
        validate_selection(
            &valid,
            &Selection {
                modes: modes(0),
                features: vec![setting(&["t0"], "left", value, 160)],
            },
        )
        .unwrap();
    }
    for value in [0, 2, 4, u64::MAX] {
        require_code(
            validate_selection(
                &valid,
                &Selection {
                    modes: modes(0),
                    features: vec![setting(&["t0"], "left", value, 161)],
                },
            ),
            Code::Value,
        );
    }
}

fn local_feedback() -> Connection {
    Connection {
        name: name("internal-driver"),
        sources: vec![endpoint(&[], "r", "O")],
        destination: endpoint(&[], "r", "I"),
        selector: None,
        provenance: origin(180),
    }
}

#[test]
fn qualified_destinations_reject_drivers_from_different_containment_scopes() {
    let mut local_and_top = line(&["t0", "t1"], &[("t1", "t0")]);
    local_and_top.templates[0]
        .connections
        .push(local_feedback());
    architecture_code(&local_and_top, Code::Connection);

    let mut parent_and_child = base();
    parent_and_child.templates[0]
        .connections
        .push(local_feedback());
    let leaf = parent_and_child.templates[0].key.clone();
    let mut parent = Template::new(Key::new("independent", vec![], "parent").unwrap());
    parent.resources = parent_and_child.templates[0].resources.clone();
    let mut child = root("inner", 0);
    child.partition = None;
    child.template = leaf;
    parent.children.push(child);
    parent.connections.push(Connection {
        name: name("parent-driver"),
        sources: vec![endpoint(&[], "r", "O")],
        destination: endpoint(&["inner"], "r", "I"),
        selector: None,
        provenance: origin(181),
    });
    parent_and_child.roots[0].template = parent.key.clone();
    parent_and_child.templates.push(parent);
    architecture_code(&parent_and_child, Code::Connection);

    let mut through_alias = line(&["t0", "t1"], &[("t1", "t0")]);
    let mut alias = through_alias.templates[0].resources[0].clone();
    alias.name = name("r-alias");
    alias.alias_of = Some(reference(&[], "r"));
    through_alias.templates[0].resources.push(alias);
    through_alias.templates[0]
        .connections
        .push(local_feedback());
    through_alias.connections[0].destination.resource.name = name("r-alias");
    architecture_code(&through_alias, Code::Connection);

    let mut two_top = line(&["t0", "t1", "t2"], &[("t1", "t0"), ("t2", "t0")]);
    let mut alias = two_top.templates[0].resources[0].clone();
    alias.name = name("r-alias");
    alias.alias_of = Some(reference(&[], "r"));
    two_top.templates[0].resources.push(alias);
    two_top.connections[1].destination.resource.name = name("r-alias");
    architecture_code(&two_top, Code::Connection);
}

#[test]
fn unknown_selected_feature_reports_selection_stage_and_instance_identity() {
    let a = base();
    let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    let selection = Selection {
        modes: vec![],
        features: vec![setting(&["t0"], "ghost", 0, 200)],
    };
    let errors = require_code(validate_selection(&valid, &selection), Code::Missing);
    let missing = errors.iter().find(|d| d.code == Code::Missing).unwrap();
    assert_eq!(missing.stage, ty::Stage::Selection);
    assert_eq!(
        missing.key,
        Some(
            Key::<ty::Field>::new("independent", vec!["t0".into()], "ghost")
                .unwrap()
                .erase()
        )
    );
}

#[test]
fn reordered_duplicate_domain_declarations_keep_both_origins() {
    let mut a = base();
    let domain_key = Key::new("independent", vec![], "clock").unwrap();
    a.domains.push(Domain {
        key: domain_key.clone(),
        kind: DomainClass::Clock,
        provenance: origin(210),
    });
    a.domains.push(Domain {
        key: domain_key,
        kind: DomainClass::Clock,
        provenance: origin(211),
    });
    let expected = architecture_code(&a, Code::Duplicate);
    assert!(
        expected
            .iter()
            .any(|d| d.code == Code::Duplicate && !d.related.is_empty())
    );
    a.domains.reverse();
    assert_eq!(architecture_code(&a, Code::Duplicate), expected);
    require_origins(&expected, Code::Duplicate, &[210, 211]);
}

#[test]
fn reordered_contradictory_guards_keep_both_origins() {
    let mut a = sharing(0, 0);
    let mut first = choice("g0", "a");
    first.provenance = origin(212);
    let mut second = choice("g0", "b");
    second.provenance = origin(213);
    a.templates[0].features[1].guard = vec![first, second];
    let expected = architecture_code(&a, Code::Guard);
    assert!(
        expected
            .iter()
            .any(|d| d.code == Code::Guard && !d.related.is_empty())
    );
    a.templates[0].features[1].guard.reverse();
    assert_eq!(architecture_code(&a, Code::Guard), expected);
    require_origins(&expected, Code::Guard, &[212, 213]);
}

#[test]
fn lowered_key_bound_applies_to_definition_qualified_resource_and_field_keys() {
    let a = base();
    // Each declared global key is 12 bytes: independent + T/R. The derived
    // template-qualified field is 17 bytes: independent + T + owner.
    let limits = ValidationLimits {
        max_key_bytes: 16,
        ..ValidationLimits::default()
    };
    let errors = validate_architecture(&a, &limits).unwrap_err();
    assert_eq!(errors.len(), 1);
    assert_eq!(errors[0].code, Code::Limit);
}

#[test]
fn malformed_feature_ranges_domains_and_storage_references_reject_specifically() {
    let mut a = base();
    a.templates[0].features[0].range = BitRange::new(BitOffset::new(4), BitCount::new(0)).unwrap();
    architecture_code(&a, Code::Width);
    let mut a = base();
    a.templates[0].features[0].domain = ValueDomain::Range {
        minimum: 3,
        maximum: 1,
    };
    architecture_code(&a, Code::Domain);
    let mut a = base();
    a.templates[0].features[0].domain = ValueDomain::Set(vec![0, 4]);
    architecture_code(&a, Code::Domain);
    let mut a = base();
    a.templates[0].features[0].domain = ValueDomain::Set(vec![]);
    architecture_code(&a, Code::Domain);
    let mut a = base();
    a.templates[0].features[0].domain = ValueDomain::Set(vec![0, 0]);
    architecture_code(&a, Code::Domain);
    let mut a = base();
    a.templates[0].features[0].storage = name("missing-storage");
    architecture_code(&a, Code::Missing);
    let mut a = base();
    a.templates[0].features[0].range =
        BitRange::new(BitOffset::new(127), BitCount::new(2)).unwrap();
    architecture_code(&a, Code::Bounds);
}

#[test]
fn separate_storage_objects_remain_independent_even_for_equal_offsets() {
    let mut a = base();
    let mut storage = a.templates[0].storage[0].clone();
    storage.name = name("second-storage");
    a.templates[0].storage.push(storage);
    let mut second = feature("independent-field", 4, 2);
    second.storage = name("second-storage");
    a.templates[0].features.push(second);
    let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    validate_selection(
        &valid,
        &Selection {
            modes: vec![],
            features: vec![
                setting(&["t0"], "owner", 0, 230),
                setting(&["t0"], "independent-field", 3, 231),
            ],
        },
    )
    .unwrap();
}

#[test]
fn duplicate_domain_memberships_keep_both_origins_under_permutation() {
    let mut a = base();
    let key = Key::new("independent", vec![], "C0").unwrap();
    a.domains.push(Domain {
        key: key.clone(),
        kind: DomainClass::Clock,
        provenance: origin(240),
    });
    a.roots[0].domains = vec![
        DomainRef {
            key: key.clone(),
            kind: DomainClass::Clock,
            provenance: origin(241),
        },
        DomainRef {
            key,
            kind: DomainClass::Clock,
            provenance: origin(242),
        },
    ];
    let expected = architecture_code(&a, Code::Duplicate);
    assert!(
        expected
            .iter()
            .any(|d| d.code == Code::Duplicate && !d.related.is_empty())
    );
    a.roots[0].domains.reverse();
    assert_eq!(architecture_code(&a, Code::Duplicate), expected);
    require_origins(&expected, Code::Duplicate, &[241, 242]);
}

#[test]
fn set_permutation_does_not_change_invalid_value_diagnostics() {
    let mut a = base();
    a.templates[0].features[0].domain = ValueDomain::Set(vec![0, 1]);
    let selection = Selection {
        modes: vec![],
        features: vec![setting(&["t0"], "owner", 2, 250)],
    };
    let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    let expected = require_code(validate_selection(&valid, &selection), Code::Value);
    a.templates[0].features[0].domain = ValueDomain::Set(vec![1, 0]);
    let valid = validate_architecture(&a, &ValidationLimits::default()).unwrap();
    assert_eq!(
        require_code(validate_selection(&valid, &selection), Code::Value),
        expected
    );
}

#[test]
fn competing_preflight_limits_do_not_depend_on_template_order() {
    let mut a = base();
    a.namespace = name("a");
    a.resource_types[0].key = Key::new("a", vec![], "R").unwrap();
    a.roots[0].template = Key::new("a", vec![], "T").unwrap();
    let long = Template::new(Key::new("a", vec![], "long").unwrap());
    let mut many = Template::new(Key::new("a", vec![], "b").unwrap());
    many.children = vec![a.roots[0].clone(); 3];
    a.templates = vec![long, many];
    let limits = ValidationLimits {
        max_key_component_bytes: 3,
        max_collection: 2,
        ..ValidationLimits::default()
    };
    let expected = validate_architecture(&a, &limits).unwrap_err();
    assert_eq!(expected.len(), 1);
    assert_eq!(expected[0].code, Code::Limit);
    a.templates.reverse();
    assert_eq!(validate_architecture(&a, &limits).unwrap_err(), expected);
}

#[test]
fn cycle_diagnostic_names_a_cycle_member_not_an_acyclic_descendant() {
    let mut a = base();
    let leaf = Template::new(Key::new("independent", vec![], "aa-leaf").unwrap());
    let mut cycle_a = Template::new(Key::new("independent", vec![], "mm-cycle-a").unwrap());
    cycle_a.provenance = origin(260);
    let mut cycle_b = Template::new(Key::new("independent", vec![], "zz-cycle-b").unwrap());
    cycle_b.provenance = origin(261);
    let mut edge = root("a-to-b", 0);
    edge.partition = None;
    edge.template = cycle_b.key.clone();
    edge.provenance = origin(262);
    cycle_a.children.push(edge.clone());
    edge.name = name("a-to-leaf");
    edge.template = leaf.key.clone();
    edge.provenance = origin(263);
    cycle_a.children.push(edge.clone());
    edge.name = name("b-to-a");
    edge.template = cycle_a.key.clone();
    edge.provenance = origin(264);
    cycle_b.children.push(edge);
    let cycle_keys = [cycle_a.key.erase(), cycle_b.key.erase()];
    a.roots[0].template = cycle_a.key.clone();
    a.templates = vec![leaf, cycle_a, cycle_b];
    let errors = architecture_code(&a, Code::TemplateCycle);
    let diagnostic = errors
        .iter()
        .find(|d| d.code == Code::TemplateCycle)
        .unwrap();
    assert!(
        diagnostic
            .key
            .as_ref()
            .is_some_and(|k| cycle_keys.contains(k)),
        "cycle primary must lie on the cycle: {diagnostic:?}"
    );
    assert!(
        [origin(262), origin(264)].contains(&diagnostic.primary),
        "cycle primary must identify an actual cycle edge: {diagnostic:?}"
    );
    let (target_origin, target_key, source_key) = if diagnostic.primary == origin(264) {
        (origin(260), &cycle_keys[0], &cycle_keys[1])
    } else {
        (origin(261), &cycle_keys[1], &cycle_keys[0])
    };
    assert_eq!(diagnostic.key.as_ref(), Some(source_key));
    assert!(
        diagnostic
            .related
            .iter()
            .any(|r| r.provenance == target_origin && r.key.as_ref() == Some(target_key)),
        "cycle target declaration must be retained: {diagnostic:?}"
    );
}

fn require_origins(errors: &[Diagnostic], code: Code, offsets: &[u64]) {
    assert!(
        errors
            .iter()
            .filter(|d| d.code == code)
            .any(|d| offsets.iter().all(|offset| d.primary == origin(*offset)
                || d.related.iter().any(|r| r.provenance == origin(*offset)))),
        "missing original conflict source(s) {offsets:?}: {errors:?}"
    );
}

#[test]
fn selection_competing_path_and_component_limits_are_order_independent() {
    let mut a = base();
    a.namespace = name("a");
    a.resource_types[0].key = Key::new("a", vec![], "R").unwrap();
    a.templates[0].key = Key::new("a", vec![], "T").unwrap();
    a.templates[0].resources[0].resource_type = a.resource_types[0].key.clone();
    a.templates[0].mode_groups.push(ModeGroup {
        name: name("g"),
        resources: vec![reference(&[], "r")],
        modes: vec![name("a"), name("b")],
        provenance: origin(270),
    });
    a.roots[0].name = name("i");
    a.roots[0].template = a.templates[0].key.clone();
    let limits = ValidationLimits {
        max_depth: 1,
        max_key_component_bytes: 10,
        ..ValidationLimits::default()
    };
    let valid = validate_architecture(&a, &limits).unwrap();
    let mut selection = Selection {
        modes: vec![
            ModeSetting {
                path: vec![name("i"), name("i")],
                group: name("g"),
                mode: name("a"),
                provenance: origin(271),
            },
            ModeSetting {
                path: vec![name("i")],
                group: name("12345678901"),
                mode: name("a"),
                provenance: origin(272),
            },
        ],
        features: vec![],
    };
    let expected = validate_selection(&valid, &selection).unwrap_err();
    assert_eq!(expected.len(), 1);
    assert_eq!(expected[0].code, Code::Limit);
    selection.modes.reverse();
    assert_eq!(
        validate_selection(&valid, &selection).unwrap_err(),
        expected
    );
}

#[test]
fn oversized_reference_paths_reject_before_semantic_resolution() {
    let mut a = base();
    let mut connection = fixed("long-path", "t0", "t0");
    connection.sources[0].resource.path = vec![name("x"); 65];
    a.connections.push(connection);
    let errors = architecture_code(&a, Code::Limit);
    assert_eq!(errors.len(), 1);
}

#[test]
fn compact_high_fanout_hierarchy_obeys_declared_work_budget() {
    let mut a = base();
    for level in 1..=6 {
        let child_key = a.templates.last().unwrap().key.clone();
        let mut wrapper =
            Template::new(Key::new("independent", vec![], format!("fanout{level}")).unwrap());
        for index in 0..8 {
            let mut child = root(&format!("child{index}"), 0);
            child.template = child_key.clone();
            child.partition = None;
            wrapper.children.push(child);
        }
        a.templates.push(wrapper);
    }
    a.roots[0].template = a.templates.last().unwrap().key.clone();
    assert_eq!(a.templates.len(), 7);
    assert_eq!(
        a.templates.iter().map(|t| t.children.len()).sum::<usize>(),
        48
    );
    let limits = ValidationLimits {
        max_work: 10_000,
        ..ValidationLimits::default()
    };
    let errors = validate_architecture(&a, &limits).unwrap_err();
    assert_eq!(errors.len(), 1);
    assert_eq!(errors[0].code, Code::Limit);
    // There are 8^6 = 262144 leaf instances, described by just 48 child records.
    // No elapsed-time assertion or production-scale performance claim is made.
}

#[test]
fn field_resource_and_feature_cannot_share_one_typed_portable_identity() {
    let mut a = base();
    let field_type = Key::new("independent", vec![], "field-type").unwrap();
    a.resource_types.push(ResourceType {
        key: field_type.clone(),
        kind: ResourceKind::Field,
        pins: vec![],
        modes: vec![],
        provenance: origin(280),
    });
    a.templates[0].resources.push(Resource {
        name: name("owner"),
        kind: ResourceKind::Field,
        resource_type: field_type,
        alias_of: None,
        domains: vec![],
        provenance: origin(281),
    });
    let diagnostics = architecture_code(&a, Code::Duplicate);
    let expected = Key::<ty::Field>::new("independent", vec!["T".into()], "owner")
        .unwrap()
        .erase();
    assert!(
        diagnostics
            .iter()
            .any(|d| d.code == Code::Duplicate && d.key == Some(expected.clone())),
        "expected duplicate key {expected:?}, got {diagnostics:?}"
    );
}

#[test]
fn storage_and_mode_group_diagnostics_use_distinct_nominal_key_kinds() {
    let mut a = base();
    let mut second = a.templates[0].storage[0].clone();
    second.provenance = origin(290);
    a.templates[0].storage.push(second);
    let diagnostics = architecture_code(&a, Code::Duplicate);
    let expected = Key::<ty::Storage>::new("independent", vec!["T".into()], "s")
        .unwrap()
        .erase();
    assert!(
        diagnostics
            .iter()
            .any(|d| d.code == Code::Duplicate && d.key == Some(expected.clone())),
        "expected duplicate key {expected:?}, got {diagnostics:?}"
    );
    assert_eq!(expected.kind(), ty::Kind::Storage);
    let mut a = sharing(0, 0);
    let mut second = a.templates[0].mode_groups[0].clone();
    second.provenance = origin(291);
    a.templates[0].mode_groups.push(second);
    let diagnostics = architecture_code(&a, Code::Duplicate);
    let expected = Key::<ty::ModeGroup>::new("independent", vec!["T".into()], "g0")
        .unwrap()
        .erase();
    assert!(
        diagnostics
            .iter()
            .any(|d| d.code == Code::Duplicate && d.key == Some(expected.clone())),
        "expected duplicate key {expected:?}, got {diagnostics:?}"
    );
    assert_eq!(expected.kind(), ty::Kind::ModeGroup);
    assert_ne!(
        Key::<ty::Storage>::new("n", vec![], "same")
            .unwrap()
            .erase(),
        Key::<ty::ModeGroup>::new("n", vec![], "same")
            .unwrap()
            .erase()
    );
}

#[test]
fn pip_resource_and_connection_cannot_share_one_typed_portable_identity() {
    let mut a = base();
    let pip_type = Key::new("independent", vec![], "pip-type").unwrap();
    a.resource_types.push(ResourceType {
        key: pip_type.clone(),
        kind: ResourceKind::Pip,
        pins: vec![],
        modes: vec![],
        provenance: origin(300),
    });
    a.templates[0].resources.push(Resource {
        name: name("switch"),
        kind: ResourceKind::Pip,
        resource_type: pip_type,
        alias_of: None,
        domains: vec![],
        provenance: origin(301),
    });
    let mut connection = local_feedback();
    connection.name = name("switch");
    connection.provenance = origin(302);
    a.templates[0].connections.push(connection);
    let diagnostics = architecture_code(&a, Code::Duplicate);
    let expected = Key::<ty::Pip>::new("independent", vec!["T".into()], "switch")
        .unwrap()
        .erase();
    assert!(
        diagnostics
            .iter()
            .any(|d| d.code == Code::Duplicate && d.key == Some(expected.clone())),
        "expected collision key {expected:?}, got {diagnostics:?}"
    );
}

#[test]
fn lowered_key_bound_checks_instance_path_plus_long_feature_name() {
    let mut a = base();
    a.namespace = name("a");
    a.resource_types[0].key = Key::new("a", vec![], "R").unwrap();
    a.templates[0].key = Key::new("a", vec![], "T").unwrap();
    a.templates[0].resources[0].resource_type = a.resource_types[0].key.clone();
    a.templates[0].features[0].name = name("feature");
    a.roots[0].name = name("instance");
    a.roots[0].template = a.templates[0].key.clone();
    // Definition key a/T/feature is 9 bytes and instance resource/storage keys
    // are 10 bytes. Only a/instance/feature exceeds the 10-byte whole-key bound.
    let limits = ValidationLimits {
        max_key_bytes: 10,
        ..ValidationLimits::default()
    };
    let diagnostics = validate_architecture(&a, &limits).unwrap_err();
    assert_eq!(diagnostics.len(), 1);
    assert_eq!(diagnostics[0].code, Code::Limit);
}

#[test]
fn mode_name_permutation_preserves_diagnostics_at_every_small_work_budget() {
    let mut original = base();
    original.resource_types[0].modes = vec![name("x"), name("y")];
    original.templates[0].mode_groups.push(ModeGroup {
        name: name("g"),
        resources: vec![reference(&[], "r")],
        modes: vec![name("x"), name("z1"), name("z2")],
        provenance: origin(310),
    });
    // x is supported; z1 and z2 are both unsupported. Reordering this keyed set
    // changes neither the defect nor the deterministic resource-limit result.
    architecture_code(&original, Code::Mode);
    let mut reversed = original.clone();
    reversed.templates[0].mode_groups[0].modes.reverse();
    for max_work in 1..=2000 {
        let limits = ValidationLimits {
            max_work,
            max_diagnostics: 1,
            ..ValidationLimits::default()
        };
        let first = validate_architecture(&original, &limits).map(|_| ());
        let second = validate_architecture(&reversed, &limits).map(|_| ());
        assert!(
            first.is_err(),
            "invalid modes cannot become legal at work budget {max_work}"
        );
        assert_eq!(first, second, "mode permutation at work budget {max_work}");
    }
}

#[test]
fn mode_group_permutation_preserves_duplicate_diagnostics_across_work_budgets() {
    let mut original = base();
    original.resource_types[0].modes = vec![name("x"), name("y")];
    let mut other = original.templates[0].resources[0].clone();
    other.name = name("r1");
    original.templates[0].resources.push(other);
    original.templates[0].mode_groups = vec![
        ModeGroup {
            name: name("g0"),
            resources: vec![reference(&[], "r")],
            modes: vec![name("x"), name("x")],
            provenance: origin(311),
        },
        ModeGroup {
            name: name("g1"),
            resources: vec![reference(&[], "r1")],
            modes: vec![name("x"), name("y")],
            provenance: origin(312),
        },
    ];
    architecture_code(&original, Code::Duplicate);
    let mut reversed = original.clone();
    reversed.templates[0].mode_groups.reverse();
    for max_work in 1..=2000 {
        let limits = ValidationLimits {
            max_work,
            max_diagnostics: 1,
            ..ValidationLimits::default()
        };
        let first = validate_architecture(&original, &limits).map(|_| ());
        let second = validate_architecture(&reversed, &limits).map(|_| ());
        assert!(
            first.is_err(),
            "duplicate mode cannot become legal at work budget {max_work}"
        );
        assert_eq!(first, second, "group permutation at work budget {max_work}");
    }
}

#[test]
fn owner_alias_mode_membership_order_preserves_full_diagnostics() {
    let mut original = sharing(0, 0);
    let mut alias = original.templates[0].resources[0].clone();
    alias.name = name("r-alias");
    alias.alias_of = Some(reference(&[], "r"));
    alias.provenance = origin(320);
    original.templates[0].resources.push(alias);
    let mut owner = reference(&[], "r");
    owner.provenance = origin(321);
    let mut alias_member = reference(&[], "r-alias");
    alias_member.provenance = origin(322);
    original.templates[0].mode_groups[0].resources = vec![owner, alias_member];
    let expected = architecture_code(&original, Code::Mode);
    let mut reversed = original.clone();
    reversed.templates[0].mode_groups[0].resources.reverse();
    assert_eq!(architecture_code(&reversed, Code::Mode), expected);
    for max_work in 1..=2000 {
        let limits = ValidationLimits {
            max_work,
            max_diagnostics: 1,
            ..ValidationLimits::default()
        };
        let first = validate_architecture(&original, &limits).map(|_| ());
        let second = validate_architecture(&reversed, &limits).map(|_| ());
        assert!(
            first.is_err(),
            "duplicate owner membership cannot become legal at budget {max_work}"
        );
        assert_eq!(
            first, second,
            "owner/alias membership permutation at work budget {max_work}"
        );
    }
}

#[test]
fn architecture_connection_whole_key_exact_bound_overflow_and_order() {
    const LONG_NAME: &str = "abcdefghijklmnopqrstuvwxy";
    let mut original = line(corpus::LINE_THREE_OWNERS, corpus::LINE_THREE_EDGES);
    original.connections[0].name = name(LONG_NAME);
    original.connections[1].name = name("short");
    assert_eq!(original.namespace.as_str().len(), 11);
    assert_eq!(LONG_NAME.len(), 25);
    // The complete architectural PIP key has no instance/template scope:
    // (kind=Pip, namespace=independent, scope=[], local=abcdefghijklmnopqrstuvwxy).
    // Its semantic components total exactly 36 UTF-8 bytes.
    let expected_key = Key::<ty::Pip>::new("independent", vec![], LONG_NAME)
        .unwrap()
        .erase();
    assert_eq!(expected_key.kind(), ty::Kind::Pip);
    assert!(expected_key.scope().is_empty());
    let exact = ValidationLimits {
        max_key_bytes: 36,
        ..ValidationLimits::default()
    };
    let valid = validate_architecture(&original, &exact).unwrap();
    assert_eq!(valid.architecture().connections[0].name.as_str(), LONG_NAME);
    let too_small = ValidationLimits {
        max_key_bytes: 35,
        ..ValidationLimits::default()
    };
    let expected = validate_architecture(&original, &too_small)
        .map(|_| ())
        .expect_err("36-byte top-level connection key exceeds the 35-byte bound");
    assert_eq!(expected.len(), 1);
    assert_eq!(expected[0].code, Code::Limit);
    assert_eq!(expected[0].stage, ty::Stage::Architecture);
    let mut reordered = original.clone();
    reordered.connections.reverse();
    reordered.roots.reverse();
    validate_architecture(&reordered, &exact).unwrap();
    assert_eq!(
        validate_architecture(&reordered, &too_small).unwrap_err(),
        expected
    );
    // A duplicate-name diagnostic exposes that same nominal top-level key.
    let mut duplicate = original.clone();
    duplicate.connections[1].name = name(LONG_NAME);
    let diagnostics = validate_architecture(&duplicate, &exact).unwrap_err();
    assert!(
        diagnostics
            .iter()
            .any(|d| d.code == Code::Duplicate && d.key == Some(expected_key.clone())),
        "expected top-level PIP key {expected_key:?}, got {diagnostics:?}"
    );
}
