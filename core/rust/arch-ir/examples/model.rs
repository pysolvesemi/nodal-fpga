//! Executable structural/selection example. No hardware is emitted or simulated.
use nf_arch_ir::{
    Architecture, Connection, Direction, Endpoint, Feature, FeatureSetting, FieldRef, Instance,
    ModeGroup, ModeSetting, Pin, Resource, ResourceKind, ResourceRef, ResourceType, Selection,
    Storage, Template, ValidationLimits, ValueDomain, validate_architecture, validate_selection,
};
use nf_types::{
    BitCount, BitOffset, BitRange, ByteLength, ByteOffset, Code, Key, Name, PartitionId,
    Provenance, SourceSpan, Width,
};

fn name(value: &str) -> Name {
    Name::new(value).expect("example names fit the public bounds")
}

fn origin(source: &str, start: u64) -> Provenance {
    // Synthetic source coordinates: no source bytes are supplied to SourceSpan.
    // The constructor checks numeric bounds, not an external file's contents.
    Provenance::new(
        Some(
            SourceSpan::new(
                source,
                ByteLength::new(256),
                ByteOffset::new(start),
                ByteOffset::new(start + 1),
            )
            .expect("example spans fit the declared source length"),
        ),
        None,
    )
    .expect("example provenance fits the public bounds")
}

fn resource(path: &[&str]) -> ResourceRef {
    ResourceRef {
        path: path.iter().map(|part| name(part)).collect(),
        name: name("cell"),
        kind: ResourceKind::Bel,
        provenance: origin("architecture-input", 10),
    }
}

fn endpoint(root: &str, pin: &str) -> Endpoint {
    Endpoint {
        resource: resource(&[root]),
        pin: name(pin),
        provenance: origin("architecture-input", 11),
    }
}

fn architecture() -> Architecture {
    let mut architecture = Architecture::new(name("example"));
    architecture.partitions.push(PartitionId::new(0));
    let resource_type = Key::new("example", vec![], "generic-cell").unwrap();
    architecture.resource_types.push(ResourceType {
        key: resource_type.clone(),
        kind: ResourceKind::Bel,
        // Pin order belongs to the declaration and is preserved by validation.
        pins: vec![
            Pin {
                name: name("I"),
                direction: Direction::Input,
                width: BitCount::new(1),
                provenance: origin("architecture-input", 1),
            },
            Pin {
                name: name("O"),
                direction: Direction::Output,
                width: BitCount::new(1),
                provenance: origin("architecture-input", 2),
            },
        ],
        modes: vec![name("normal"), name("alternate")],
        provenance: origin("architecture-input", 3),
    });

    let mut tile = Template::new(Key::new("example", vec![], "tile").unwrap());
    tile.resources.push(Resource {
        name: name("cell"),
        kind: ResourceKind::Bel,
        resource_type,
        alias_of: None,
        domains: vec![],
        provenance: origin("architecture-input", 20),
    });
    tile.mode_groups.push(ModeGroup {
        name: name("operation"),
        resources: vec![resource(&[])],
        modes: vec![name("normal"), name("alternate")],
        provenance: origin("architecture-input", 21),
    });
    tile.storage.push(Storage {
        name: name("config"),
        owner: resource(&[]),
        bits: BitCount::new(2),
        provenance: origin("architecture-input", 30),
    });
    tile.features.push(Feature {
        name: name("setting"),
        owner: resource(&[]),
        storage: name("config"),
        range: BitRange::new(BitOffset::new(0), BitCount::new(2)).unwrap(),
        width: Width::new(2).unwrap(),
        domain: ValueDomain::Range {
            minimum: 0,
            maximum: 2,
        },
        guard: vec![],
        alias_of: None,
        provenance: origin("architecture-input", 40),
    });

    // Three distinct instance paths share one definition, never writable state.
    for root in ["t0", "t1", "t2"] {
        architecture.roots.push(Instance {
            name: name(root),
            template: tile.key.clone(),
            partition: Some(PartitionId::new(0)),
            domains: vec![],
            provenance: origin("architecture-input", 50),
        });
    }
    architecture.templates.push(tile);
    for (edge, source, destination) in [("edge0", "t0", "t1"), ("edge1", "t1", "t2")] {
        architecture.connections.push(Connection {
            name: name(edge),
            sources: vec![endpoint(source, "O")],
            destination: endpoint(destination, "I"),
            selector: None,
            provenance: origin("architecture-input", 60),
        });
    }
    architecture
}

fn selection() -> Selection {
    let mut selection = Selection::default();
    for (root, mode, value, offset) in [
        ("t0", "normal", 0, 60),
        ("t1", "alternate", 1, 61),
        ("t2", "normal", 2, 62),
    ] {
        selection.modes.push(ModeSetting {
            path: vec![name(root)],
            group: name("operation"),
            mode: name(mode),
            provenance: origin("selection-input", offset),
        });
        selection.features.push(FeatureSetting {
            field: FieldRef {
                path: vec![name(root)],
                name: name("setting"),
                provenance: origin("selection-input", offset),
            },
            value,
            provenance: origin("selection-input", offset),
        });
    }
    selection
}

fn main() {
    let architecture = architecture();
    let validated = validate_architecture(&architecture, &ValidationLimits::default())
        .expect("the declared example is structurally valid");
    let selection = selection();
    validate_selection(&validated, &selection)
        .expect("each instance has a complete legal selection");

    println!("nodal-fpga/arch-ir/1");
    println!("profile=structural-selection");
    println!(
        "templates={} instances={} connections={}",
        validated.architecture().templates.len(),
        validated.architecture().roots.len(),
        validated.architecture().connections.len()
    );
    for ((root, mode), feature) in architecture
        .roots
        .iter()
        .zip(&selection.modes)
        .zip(&selection.features)
    {
        println!(
            "instance={} template={} partition={} mode={} setting={}",
            root.name,
            root.template.local(),
            root.partition.unwrap().get(),
            mode.mode,
            feature.value
        );
    }
    for connection in &architecture.connections {
        let source = &connection.sources[0];
        let destination = &connection.destination;
        println!(
            "link={} source={}/{}.{} destination={}/{}.{}",
            connection.name,
            source.resource.path[0],
            source.resource.name,
            source.pin,
            destination.resource.path[0],
            destination.resource.name,
            destination.pin
        );
    }
    println!("selection=valid");

    // 3 fits two bits but is outside the explicitly declared 0..=2 domain.
    let mut invalid = selection.clone();
    invalid.features[1].value = 3;
    let diagnostics = validate_selection(&validated, &invalid)
        .expect_err("the out-of-domain value must be rejected");
    let rejected = diagnostics
        .iter()
        .find(|diagnostic| diagnostic.code == Code::Value)
        .expect("rejection includes the intended value diagnostic");
    let key = rejected.key.as_ref().expect("rejection names its field");
    let primary = rejected.primary.span().expect("setting origin is retained");
    let related = rejected.related[0]
        .provenance
        .span()
        .expect("declaration origin is retained");
    println!("rejected={}", rejected.code.as_str());
    println!(
        "stage={} namespace={} scope={} field={}",
        rejected.stage.as_str(),
        key.namespace(),
        key.scope()[0],
        key.local()
    );
    println!(
        "primary={}:{}..{} actual={}",
        primary.source(),
        primary.start().get(),
        primary.end().get(),
        rejected.actual.as_deref().unwrap()
    );
    println!(
        "related={}:{}..{}",
        related.source(),
        related.start().get(),
        related.end().get()
    );
    println!("message={}", rejected.message);
    println!("This increment does not affect generated Verilog.");
}
