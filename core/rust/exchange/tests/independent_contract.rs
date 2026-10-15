//! Independent public API contract tests. Expected bytes and semantics were
//! authored before candidate output. No production canonicalizer/hash output is
//! used to generate expectations; package mutations are independently signed
//! Python-stdlib literals under verify/fixtures/exchange/package-cases.
use std::cell::{Cell, RefCell};
use std::collections::BTreeMap;
use std::io::{self, Cursor, Read};
use std::rc::Rc;
use std::sync::OnceLock;

use nf_arch_ir::{
    FeatureSetting, FieldRef, ModeSetting, Selection, validate_architecture, validate_selection,
};
use nf_exchange::{
    Digest, ExchangeError, Limits, parse_json, read_architecture, read_design, read_package,
};
use nf_types::{Code, Name, Provenance};

fn fixture_bytes(name: &str) -> Vec<u8> {
    let root =
        std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../verify/fixtures/exchange");
    std::fs::read(root.join(name)).expect("independent literal fixture must exist")
}

fn arch() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("goldens/architecture.raw.json"))
        .as_slice()
}

fn arch_canon() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("goldens/architecture.canonical.json"))
        .as_slice()
}

fn arch_projection() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("goldens/architecture.projection.json"))
        .as_slice()
}

fn package() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("goldens/package.raw.json"))
        .as_slice()
}

fn design() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("goldens/design.raw.json"))
        .as_slice()
}

fn same() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("package-cases/same-digest.json"))
        .as_slice()
}

fn conflict() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("package-cases/conflicting-length.json"))
        .as_slice()
}

fn two() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("package-cases/two-artifacts.json"))
        .as_slice()
}

fn opaque() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("package-cases/opaque-reused.json"))
        .as_slice()
}

fn huge() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("package-cases/oversized-declared.json"))
        .as_slice()
}

fn leaf() -> &'static [u8] {
    static DATA: OnceLock<Vec<u8>> = OnceLock::new();
    DATA.get_or_init(|| fixture_bytes("package-cases/opaque-leaf.bin"))
        .as_slice()
}

const ARCH_SHA: &str = "432171ad8cfc32c3a684584c6af990f8a665a89fcd7c74a03f421490a44601f5";

fn failure<T>(result: Result<T, ExchangeError>) -> ExchangeError {
    match result {
        Ok(_) => panic!("an independently invalid input was accepted"),
        Err(error) => error,
    }
}

fn expect_code(error: &ExchangeError, code: &str) {
    assert_eq!(error.code, code, "{error:?}");
    assert!(!error.remedy.is_empty());
}

fn name(value: &str) -> Name {
    Name::new(value).expect("independent literal Name fits")
}
fn setting(root: &str, field: &str, value: u64) -> FeatureSetting {
    FeatureSetting {
        field: FieldRef {
            path: vec![name(root)],
            name: name(field),
            provenance: Provenance::default(),
        },
        value,
        provenance: Provenance::default(),
    }
}
fn mode(root: &str, value: &str) -> ModeSetting {
    ModeSetting {
        path: vec![name(root)],
        group: name("operation"),
        mode: name(value),
        provenance: Provenance::default(),
    }
}

#[test]
fn independent_primary_model_and_complete_selection() {
    let limits = Limits::default();
    let checked =
        read_architecture(Cursor::new(arch()), &limits).expect("independent valid architecture");
    assert_eq!(checked.canonical_bytes().unwrap(), arch_canon());
    assert_eq!(checked.semantic_bytes().unwrap(), arch_projection());
    assert_eq!(
        checked.id().as_str(),
        "0c5e51acf90f91981b7e3375e5ab58b05d20020aa51a594008f8d7a30e1c80a4"
    );
    assert_eq!(checked.raw_digest().as_str(), ARCH_SHA);
    let arch = checked.architecture();
    assert_eq!(arch.templates.len(), 1);
    assert_eq!(arch.roots.len(), 3);
    assert_eq!(arch.connections.len(), 2);
    assert_eq!(arch.templates[0].resources.len(), 4);
    let mux = &arch.templates[0].connections[0];
    let source_names: Vec<_> = mux
        .sources
        .iter()
        .map(|s| s.resource.name.as_str())
        .collect();
    assert_eq!(source_names, ["east", "local", "west"]);
    let validated =
        validate_architecture(arch, &limits.core).expect("same public FND-04 validator");
    let selection = Selection {
        modes: vec![
            mode("t0", "normal"),
            mode("t1", "alternate"),
            mode("t2", "normal"),
        ],
        features: vec![
            setting("t0", "route", 0),
            setting("t1", "route", 1),
            setting("t2", "route", 2),
        ],
    };
    validate_selection(&validated, &selection).expect("separate instance settings are valid");
    for (index, expected) in [(0, "east"), (1, "local"), (2, "west")] {
        assert_eq!(mux.sources[index].resource.name.as_str(), expected);
    }
    let mut invalid = selection.clone();
    invalid.features[1].value = 3;
    let errors = validate_selection(&validated, &invalid).expect_err("3 violates exact set 0,1,2");
    assert!(errors.iter().any(|d| d.code == Code::Value));
    let diagnostic = errors.iter().find(|d| d.code == Code::Value).unwrap();
    assert_eq!(diagnostic.actual.as_deref(), Some("3"));
    assert!(
        diagnostic
            .related
            .iter()
            .any(|r| r.provenance.span().is_some())
    );
    let mut missing = selection.clone();
    missing.features.remove(1);
    assert!(
        validate_selection(&validated, &missing)
            .unwrap_err()
            .iter()
            .any(|d| d.code == Code::MissingSelection)
    );
    let mut duplicate = selection.clone();
    duplicate.features.push(selection.features[1].clone());
    assert!(
        validate_selection(&validated, &duplicate)
            .unwrap_err()
            .iter()
            .any(|d| d.code == Code::Duplicate)
    );
}

#[test]
fn independent_alias_classes_and_missing_conflicting_settings() {
    let bytes = fixture_bytes("goldens/architecture-alias.raw.json");
    let limits = Limits::default();
    let checked = read_architecture(Cursor::new(bytes), &limits).unwrap();
    let validated = validate_architecture(checked.architecture(), &limits.core).unwrap();
    let one_per_class = Selection {
        modes: vec![],
        features: vec![setting("t0", "alias", 1), setting("t1", "F", 2)],
    };
    validate_selection(&validated, &one_per_class)
        .expect("one active alias write per independent instance class");
    let equal = Selection {
        modes: vec![],
        features: vec![
            setting("t0", "F", 1),
            setting("t0", "alias", 1),
            setting("t1", "F", 2),
        ],
    };
    validate_selection(&validated, &equal).expect("equal co-active aliases agree");
    let mut conflict = equal.clone();
    conflict.features[0].value = 0;
    assert!(
        validate_selection(&validated, &conflict)
            .unwrap_err()
            .iter()
            .any(|d| d.code == Code::Conflict)
    );
    let missing = Selection {
        modes: vec![],
        features: vec![setting("t0", "alias", 1)],
    };
    assert!(
        validate_selection(&validated, &missing)
            .unwrap_err()
            .iter()
            .any(|d| d.code == Code::MissingSelection)
    );
    let invalid = Selection {
        modes: vec![],
        features: vec![setting("t0", "alias", 4), setting("t1", "F", 2)],
    };
    assert!(
        validate_selection(&validated, &invalid)
            .unwrap_err()
            .iter()
            .any(|d| d.code == Code::Value)
    );
}

#[test]
fn independent_hierarchy_empty_selection_and_high_offsets() {
    let limits = Limits::default();
    let hierarchy = read_architecture(
        Cursor::new(fixture_bytes("goldens/architecture-hierarchy.raw.json")),
        &limits,
    )
    .unwrap();
    let validated = validate_architecture(hierarchy.architecture(), &limits.core).unwrap();
    validate_selection(&validated, &Selection::default()).unwrap();
    let children = &hierarchy.architecture().templates[1].children;
    assert_eq!(children[0].name.as_str(), "..");
    assert_eq!(children[1].name.as_str(), "a/b");
    assert!(children.iter().all(|c| c.partition.is_none()));
    let high = read_architecture(
        Cursor::new(fixture_bytes("goldens/architecture-high-u64.raw.json")),
        &limits,
    )
    .unwrap();
    let template = &high.architecture().templates[0];
    assert_eq!(template.storage[0].bits.get(), u64::MAX);
    assert_eq!(template.features[0].range.start().get(), u64::MAX - 1);
    assert_eq!(template.features[0].range.end().get(), u64::MAX);
    let validated = validate_architecture(high.architecture(), &limits.core).unwrap();
    for value in [0, 1] {
        validate_selection(
            &validated,
            &Selection {
                modes: vec![],
                features: vec![setting("t0", "last-bit", value)],
            },
        )
        .unwrap();
    }
    let errors = validate_selection(
        &validated,
        &Selection {
            modes: vec![],
            features: vec![setting("t0", "last-bit", 2)],
        },
    )
    .unwrap_err();
    assert!(errors.iter().any(|d| d.code == Code::Value));
}

struct CountedRead {
    inner: Cursor<Vec<u8>>,
    count: Rc<Cell<usize>>,
}
impl Read for CountedRead {
    fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
        let n = self.inner.read(buffer)?;
        self.count.set(self.count.get() + n);
        Ok(n)
    }
}
struct EndlessRead {
    count: Rc<Cell<usize>>,
}
impl Read for EndlessRead {
    fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
        buffer.fill(b'x');
        self.count.set(self.count.get() + buffer.len());
        Ok(buffer.len())
    }
}

#[test]
fn descriptor_preflight_and_bad_build_make_zero_resolver_calls() {
    for (label, bytes, kind) in [
        ("conflicting lengths", conflict(), "artifact_length"),
        ("oversized declaration", huge(), "limit"),
    ] {
        let mut calls = 0;
        let mut resolver = |_: &Digest| -> io::Result<Box<dyn Read>> {
            calls += 1;
            panic!("{label}: resolver must not be invoked")
        };
        let error = failure(read_package(
            Cursor::new(bytes),
            &mut resolver,
            &Limits::default(),
        ));
        expect_code(&error, kind);
        assert_eq!(calls, 0);
    }
    for (name, value) in [
        ("artifacts", 1_u64),
        ("artifact_bytes", (arch().len() + leaf().len() - 1) as u64),
    ] {
        let mut limits = Limits::default();
        if name == "artifacts" {
            limits.artifacts = value as usize;
        } else {
            limits.artifact_bytes = value;
        }
        let mut calls = 0;
        let mut resolver = |_: &Digest| -> io::Result<Box<dyn Read>> {
            calls += 1;
            panic!("preflight must not resolve")
        };
        expect_code(
            &failure(read_package(Cursor::new(two()), &mut resolver, &limits)),
            "limit",
        );
        assert_eq!(calls, 0);
    }
    let original = std::str::from_utf8(package()).unwrap();
    let bad = original.replace(
        "0cbc4eb05c0f661740158587135aa55b4e03ab74f6a9e5e1dcfa95e3c42fbf9f",
        &"0".repeat(64),
    );
    let mut calls = 0;
    let mut resolver = |_: &Digest| -> io::Result<Box<dyn Read>> {
        calls += 1;
        panic!("bad build must not resolve")
    };
    let error = failure(read_package(
        Cursor::new(bad),
        &mut resolver,
        &Limits::default(),
    ));
    expect_code(&error, "identity_mismatch");
    assert_eq!(error.pointer, "/body/build_id");
    assert_eq!(calls, 0);
}

#[test]
fn repeated_digest_resolves_once_and_verified_bytes_are_not_reopened() {
    let calls = Rc::new(Cell::new(0));
    let reads = Rc::new(Cell::new(0));
    let backing = Rc::new(RefCell::new(arch().to_vec()));
    let mut resolver = {
        let calls = calls.clone();
        let reads = reads.clone();
        let backing = backing.clone();
        move |digest: &Digest| -> io::Result<Box<dyn Read>> {
            assert_eq!(digest.as_str(), ARCH_SHA);
            calls.set(calls.get() + 1);
            assert_eq!(
                calls.get(),
                1,
                "same admitted digest must never be reopened"
            );
            Ok(Box::new(CountedRead {
                inner: Cursor::new(backing.borrow().clone()),
                count: reads.clone(),
            }))
        }
    };
    let limits = Limits {
        artifacts: 1,
        artifact_bytes: arch().len() as u64,
        ..Limits::default()
    };
    let saved = read_package(Cursor::new(same()), &mut resolver, &limits).unwrap();
    assert_eq!(calls.get(), 1);
    assert_eq!(reads.get(), arch().len());
    *backing.borrow_mut() = b"modified untrusted backing".to_vec();
    assert_eq!(
        saved.architecture().canonical_bytes().unwrap(),
        arch_canon()
    );
    assert_eq!(
        saved.architecture().semantic_bytes().unwrap(),
        arch_projection()
    );
    assert_eq!(calls.get(), 1);
    assert_eq!(reads.get(), arch().len());
}

#[test]
fn opaque_artifacts_are_flat_once_resolved_and_bounded() {
    let calls = Rc::new(RefCell::new(BTreeMap::<String, usize>::new()));
    let bytes = Rc::new(Cell::new(0));
    let mut resolver = {
        let calls = calls.clone();
        let bytes = bytes.clone();
        move |digest: &Digest| -> io::Result<Box<dyn Read>> {
            let mut seen = calls.borrow_mut();
            let count = seen.entry(digest.as_str().to_owned()).or_default();
            *count += 1;
            assert_eq!(*count, 1, "opaque reuse must not reread or recurse");
            let payload = if digest.as_str() == ARCH_SHA {
                arch()
            } else {
                leaf()
            };
            Ok(Box::new(CountedRead {
                inner: Cursor::new(payload.to_vec()),
                count: bytes.clone(),
            }))
        }
    };
    let limits = Limits {
        artifacts: 2,
        artifact_bytes: (arch().len() + leaf().len()) as u64,
        ..Limits::default()
    };
    let saved = read_package(Cursor::new(opaque()), &mut resolver, &limits).unwrap();
    assert_eq!(calls.borrow().len(), 2);
    assert_eq!(bytes.get(), arch().len() + leaf().len());
    assert_eq!(
        saved.architecture().canonical_bytes().unwrap(),
        arch_canon()
    );
}

#[test]
fn actual_reads_stop_at_one_overflow_probe_and_do_not_trust_metadata() {
    let count = Rc::new(Cell::new(0));
    let mut resolver = {
        let count = count.clone();
        move |_: &Digest| -> io::Result<Box<dyn Read>> {
            Ok(Box::new(EndlessRead {
                count: count.clone(),
            }))
        }
    };
    let limits = Limits {
        artifact_bytes: arch().len() as u64,
        ..Limits::default()
    };
    let error = failure(read_package(Cursor::new(package()), &mut resolver, &limits));
    expect_code(&error, "artifact_length");
    assert_eq!(
        count.get(),
        arch().len() + 1,
        "one probe beyond exact declared length, never an unbounded read"
    );

    for (payload, expected) in [
        (arch()[..arch().len() - 1].to_vec(), "artifact_length"),
        (
            {
                let mut p = arch().to_vec();
                p[0] = b'!';
                p
            },
            "artifact_digest",
        ),
    ] {
        let count = Rc::new(Cell::new(0));
        let mut resolver = {
            let count = count.clone();
            let payload = payload.clone();
            move |_: &Digest| -> io::Result<Box<dyn Read>> {
                Ok(Box::new(CountedRead {
                    inner: Cursor::new(payload.clone()),
                    count: count.clone(),
                }))
            }
        };
        let error = failure(read_package(
            Cursor::new(package()),
            &mut resolver,
            &Limits::default(),
        ));
        expect_code(&error, expected);
        assert_eq!(count.get(), payload.len());
    }
    let mut missing = |_: &Digest| -> io::Result<Box<dyn Read>> {
        Err(io::Error::new(
            io::ErrorKind::NotFound,
            "independent missing artifact",
        ))
    };
    expect_code(
        &failure(read_package(
            Cursor::new(package()),
            &mut missing,
            &Limits::default(),
        )),
        "artifact_missing",
    );
}

#[test]
fn streamed_json_limit_reads_only_max_plus_one_and_counts_keys() {
    let count = Rc::new(Cell::new(0));
    let reader = EndlessRead {
        count: count.clone(),
    };
    let limits = Limits {
        input_bytes: 7,
        ..Limits::default()
    };
    expect_code(&failure(parse_json(reader, &limits)), "limit");
    assert_eq!(count.get(), 8);
    let mut limits = Limits {
        nodes: 3,
        nesting: 1,
        ..Limits::default()
    };
    let (_, stats) = parse_json(Cursor::new(b"{\"a\":0}"), &limits).unwrap();
    assert_eq!(stats.nodes, 3);
    assert_eq!(stats.depth, 1);
    limits.nodes = 2;
    expect_code(
        &failure(parse_json(Cursor::new(b"{\"a\":0}"), &limits)),
        "limit",
    );
}

#[test]
fn verified_package_design_target_and_late_self_identity() {
    let mut resolver = |digest: &Digest| -> io::Result<Box<dyn Read>> {
        assert_eq!(digest.as_str(), ARCH_SHA);
        Ok(Box::new(Cursor::new(arch())))
    };
    let saved = read_package(Cursor::new(package()), &mut resolver, &Limits::default()).unwrap();
    let design = read_design(Cursor::new(design()), &saved, &Limits::default()).unwrap();
    assert_eq!(
        design.id().as_str(),
        "bae95cd16fc8ffa058248eb3b83ea91bd6963b62833c48f04abb7d961265cddd"
    );
    let other = fixture_bytes("goldens/design-cold-target.raw.json");
    let error = failure(read_design(Cursor::new(other), &saved, &Limits::default()));
    expect_code(&error, "target_build_mismatch");
    assert_eq!(error.pointer, "/body/target_build_id");
}

#[test]
fn decoded_guarded_aliases_preserve_owner_independence_and_inactivity() {
    let raw = fixture_bytes("semantic-cases/guarded-alias.json");
    let limits = Limits::default();
    let checked = read_architecture(Cursor::new(raw), &limits).unwrap();
    let validated = validate_architecture(checked.architecture(), &limits.core).unwrap();
    let valid = Selection {
        modes: vec![mode("t0", "normal"), mode("t1", "alternate")],
        features: vec![setting("t0", "F", 1), setting("t1", "alias", 2)],
    };
    validate_selection(&validated, &valid)
        .expect("active alias alone covers an inactive owner's class");
    let mut inactive = valid.clone();
    inactive.features.push(setting("t0", "alias", 1));
    assert!(
        validate_selection(&validated, &inactive)
            .unwrap_err()
            .iter()
            .any(|d| d.code == Code::Inactive)
    );
    let mut different_legal = valid.clone();
    different_legal.modes[0] = mode("t0", "alternate");
    different_legal.features[0] = setting("t0", "alias", 3);
    validate_selection(&validated, &different_legal)
        .expect("exclusive names may hold different legal values in separate selections");
    let mut missing_mode = valid.clone();
    missing_mode.modes.remove(1);
    assert!(
        validate_selection(&validated, &missing_mode)
            .unwrap_err()
            .iter()
            .any(|d| d.code == Code::MissingSelection)
    );
}

/// Invalid caller configuration must be rejected before touching any input or
/// resolver, on each public API independently (not merely at the CLI boundary).
#[test]
fn all_public_read_apis_reject_zero_and_raised_limits_before_io() {
    struct MustNotRead;
    impl Read for MustNotRead {
        fn read(&mut self, _: &mut [u8]) -> io::Result<usize> {
            panic!("invalid caller limits must fail before any input read")
        }
    }
    let mut resolver = |digest: &Digest| -> io::Result<Box<dyn Read>> {
        assert_eq!(digest.as_str(), ARCH_SHA);
        Ok(Box::new(Cursor::new(arch())))
    };
    let saved = read_package(Cursor::new(package()), &mut resolver, &Limits::default()).unwrap();
    type Setter = fn(&mut Limits, u64);
    // Literal ceilings are from accepted readiness/FND-04, not implementation
    // defaults. Every public capability gets zero and ceiling+1 controls.
    let cases: &[(&str, u64, Setter)] = &[
        ("input_bytes", 8_388_608, |l, n| l.input_bytes = n as usize),
        ("nesting", 64, |l, n| l.nesting = n as usize),
        ("nodes", 200_000, |l, n| l.nodes = n),
        ("collection", 16_384, |l, n| l.collection = n as usize),
        ("string_bytes", 65_536, |l, n| l.string_bytes = n as usize),
        ("artifacts", 256, |l, n| l.artifacts = n as usize),
        ("artifact_bytes", 33_554_432, |l, n| l.artifact_bytes = n),
        ("core.max_declarations", 100_000, |l, n| {
            l.core.max_declarations = n
        }),
        ("core.max_references", 200_000, |l, n| {
            l.core.max_references = n
        }),
        ("core.max_collection", 16_384, |l, n| {
            l.core.max_collection = n as usize
        }),
        ("core.max_depth", 64, |l, n| l.core.max_depth = n as usize),
        ("core.max_key_component_bytes", 128, |l, n| {
            l.core.max_key_component_bytes = n as usize
        }),
        ("core.max_key_bytes", 4096, |l, n| {
            l.core.max_key_bytes = n as usize
        }),
        ("core.max_provenance_bytes", 1024, |l, n| {
            l.core.max_provenance_bytes = n as usize
        }),
        ("core.max_diagnostics", 128, |l, n| {
            l.core.max_diagnostics = n as usize
        }),
        ("core.max_work", 1_000_000, |l, n| l.core.max_work = n),
    ];
    for (name, ceiling, set) in cases {
        for value in [0, ceiling + 1] {
            let mut limits = Limits::default();
            set(&mut limits, value);
            let mut forbidden = |_: &Digest| -> io::Result<Box<dyn Read>> {
                panic!("{name}={value}: invalid limits must precede resolution")
            };
            let errors = [
                failure(parse_json(MustNotRead, &limits)),
                failure(read_architecture(MustNotRead, &limits)),
                failure(read_package(MustNotRead, &mut forbidden, &limits)),
                failure(read_design(MustNotRead, &saved, &limits)),
            ];
            for error in errors {
                assert_eq!(error.code, "invalid_limits", "{name}={value}: {error:?}");
                assert_eq!(error.stage, "read");
                assert_eq!(error.pointer, "");
                assert!(!error.remedy.is_empty());
                assert!(error.actual.is_some());
                assert!(error.expected.is_some());
            }
        }
    }
}

#[test]
fn exact_manifest_counters_fail_before_resolution_not_inside_architecture() {
    // Hand count from the literal package: 12 role bindings + body + arch binding
    // + descriptor = 15 declarations; arch identity + descriptor = 2 references.
    // Ten 24-byte reasons, one 12-byte reason and one 14-byte reason each charge
    // byte length + 1: 278. Total work=15+2+one descriptor index insertion+278=296.
    type Setter = fn(&mut Limits, u64);
    let cases: &[(&str, u64, Setter)] = &[
        ("declarations", 15, |l, n| l.core.max_declarations = n),
        ("references", 2, |l, n| l.core.max_references = n),
        ("work", 296, |l, n| l.core.max_work = n),
    ];
    for (name, total, set) in cases {
        for bound in [total - 1, *total, total + 1] {
            let mut limits = Limits::default();
            set(&mut limits, bound);
            let mut calls = 0;
            let mut missing = |digest: &Digest| -> io::Result<Box<dyn Read>> {
                assert_eq!(digest.as_str(), ARCH_SHA);
                calls += 1;
                Err(io::Error::new(
                    io::ErrorKind::NotFound,
                    "counter boundary probe",
                ))
            };
            let error = failure(read_package(Cursor::new(package()), &mut missing, &limits));
            if bound < *total {
                assert_eq!(calls, 0, "{name}: preflight must precede resolution");
                expect_code(&error, "limit");
                assert_eq!(error.stage, "semantic");
                assert_eq!(error.pointer, "/body");
                assert_eq!(error.actual.as_deref(), Some(total.to_string().as_str()));
                assert_eq!(error.expected.as_deref(), Some(bound.to_string().as_str()));
            } else {
                // Resolver failure deliberately stops before architecture checks,
                // which have independent, larger counters for this same package.
                assert_eq!(calls, 1, "{name}: exact threshold must admit resolver");
                expect_code(&error, "artifact_missing");
                assert_eq!(error.stage, "artifact");
            }
        }
    }
}
