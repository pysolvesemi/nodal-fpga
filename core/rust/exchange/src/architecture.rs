//! Consuming wire adapters use public checked constructors and the one core validator.
use crate::{
    error::{ExchangeError, Result},
    wire as w,
};
use nf_arch_ir as a;
use nf_types as t;

fn err(path: &str, e: t::Diagnostic) -> ExchangeError {
    ExchangeError::core(path, vec![e])
}
pub(crate) fn name(s: String, path: &str) -> Result<t::Name> {
    t::Name::new(s).map_err(|e| err(path, e))
}
fn names(v: Vec<String>, p: &str) -> Result<Vec<t::Name>> {
    v.into_iter()
        .enumerate()
        .map(|(i, s)| name(s, &format!("{p}/{i}")))
        .collect()
}
pub(crate) fn provenance(v: w::Provenance, p: &str) -> Result<t::Provenance> {
    let span = v
        .span
        .0
        .map(|v| {
            t::SourceSpan::new(
                v.source,
                t::ByteLength::new(v.source_bytes.0),
                t::ByteOffset::new(v.start.0),
                t::ByteOffset::new(v.end.0),
            )
            .map_err(|e| err(&format!("{p}/span"), e))
        })
        .transpose()?;
    t::Provenance::new(span, v.display.0).map_err(|e| err(p, e))
}
pub(crate) fn kind_name(k: t::Kind) -> &'static str {
    match k {
        t::Kind::Wire => "wire",
        t::Kind::Pip => "pip",
        t::Kind::Bel => "bel",
        t::Kind::Pin => "pin",
        t::Kind::Node => "node",
        t::Kind::Site => "site",
        t::Kind::Field => "field",
        t::Kind::Template => "template",
        t::Kind::ResourceType => "resource_type",
        t::Kind::Domain => "domain",
        t::Kind::ModeGroup => "mode_group",
        t::Kind::Storage => "storage",
    }
}
pub(crate) fn key<K: t::ResourceMarker>(v: w::Key, p: &str) -> Result<t::Key<K>> {
    if v.kind != kind_name(K::KIND) {
        return Err(ExchangeError::new(
            "invalid_enum",
            "decode",
            format!("{p}/kind"),
            "portable key has wrong declared kind",
        )
        .bounds(v.kind, kind_name(K::KIND)));
    }
    t::Key::new(v.namespace, v.scope, v.local).map_err(|e| err(p, e))
}
pub(crate) fn direction(s: &str, p: &str) -> Result<a::Direction> {
    match s {
        "input" => Ok(a::Direction::Input),
        "output" => Ok(a::Direction::Output),
        _ => Err(
            ExchangeError::new("invalid_enum", "decode", p, "unsupported pin direction")
                .bounds(s, "input|output"),
        ),
    }
}
fn kind(s: &str, p: &str) -> Result<a::ResourceKind> {
    match s {
        "wire" => Ok(a::ResourceKind::Wire),
        "pip" => Ok(a::ResourceKind::Pip),
        "bel" => Ok(a::ResourceKind::Bel),
        "pin" => Ok(a::ResourceKind::Pin),
        "node" => Ok(a::ResourceKind::Node),
        "site" => Ok(a::ResourceKind::Site),
        "field" => Ok(a::ResourceKind::Field),
        _ => Err(
            ExchangeError::new("invalid_enum", "decode", p, "unsupported resource kind")
                .bounds(s, "wire|pip|bel|pin|node|site|field"),
        ),
    }
}
fn domain_kind(s: &str, p: &str) -> Result<a::DomainClass> {
    match s {
        "clock" => Ok(a::DomainClass::Clock),
        "power" => Ok(a::DomainClass::Power),
        "configuration" => Ok(a::DomainClass::Configuration),
        "placement" => Ok(a::DomainClass::Placement),
        "routing" => Ok(a::DomainClass::Routing),
        _ => Err(
            ExchangeError::new("invalid_enum", "decode", p, "unsupported domain class")
                .bounds(s, "clock|power|configuration|placement|routing"),
        ),
    }
}
fn many<T, U>(v: Vec<T>, p: &str, mut f: impl FnMut(T, &str) -> Result<U>) -> Result<Vec<U>> {
    v.into_iter()
        .enumerate()
        .map(|(i, v)| f(v, &format!("{p}/{i}")))
        .collect()
}
pub(crate) fn pin(v: w::Pin, p: &str) -> Result<a::Pin> {
    Ok(a::Pin {
        name: name(v.name, &format!("{p}/name"))?,
        direction: direction(&v.direction, &format!("{p}/direction"))?,
        width: t::BitCount::new(v.width.0),
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn ty(v: w::ResourceType, p: &str) -> Result<a::ResourceType> {
    Ok(a::ResourceType {
        key: key(v.key, &format!("{p}/key"))?,
        kind: kind(&v.kind, &format!("{p}/kind"))?,
        pins: many(v.pins, &format!("{p}/pins"), pin)?,
        modes: names(v.modes, &format!("{p}/modes"))?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn domain(v: w::Domain, p: &str) -> Result<a::Domain> {
    Ok(a::Domain {
        key: key(v.key, &format!("{p}/key"))?,
        kind: domain_kind(&v.kind, &format!("{p}/kind"))?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn domain_ref(v: w::Domain, p: &str) -> Result<a::DomainRef> {
    let d = domain(v, p)?;
    Ok(a::DomainRef {
        key: d.key,
        kind: d.kind,
        provenance: d.provenance,
    })
}
fn resource_ref(v: w::ResourceRef, p: &str) -> Result<a::ResourceRef> {
    Ok(a::ResourceRef {
        path: names(v.path, &format!("{p}/path"))?,
        name: name(v.name, &format!("{p}/name"))?,
        kind: kind(&v.kind, &format!("{p}/kind"))?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn field_ref(v: w::FieldRef, p: &str) -> Result<a::FieldRef> {
    Ok(a::FieldRef {
        path: names(v.path, &format!("{p}/path"))?,
        name: name(v.name, &format!("{p}/name"))?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn resource(v: w::Resource, p: &str) -> Result<a::Resource> {
    Ok(a::Resource {
        name: name(v.name, &format!("{p}/name"))?,
        kind: kind(&v.kind, &format!("{p}/kind"))?,
        resource_type: key(v.resource_type, &format!("{p}/resource_type"))?,
        alias_of: v
            .alias_of
            .0
            .map(|v| resource_ref(v, &format!("{p}/alias_of")))
            .transpose()?,
        domains: many(v.domains, &format!("{p}/domains"), domain_ref)?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn instance(v: w::Instance, p: &str) -> Result<a::Instance> {
    Ok(a::Instance {
        name: name(v.name, &format!("{p}/name"))?,
        template: key(v.template, &format!("{p}/template"))?,
        partition: v
            .partition
            .0
            .map(|v| {
                u32::try_from(v.0).map(t::PartitionId::new).map_err(|_| {
                    ExchangeError::new(
                        "overflow",
                        "decode",
                        format!("{p}/partition"),
                        "partition exceeds u32",
                    )
                    .bounds(v.0, u32::MAX)
                })
            })
            .transpose()?,
        domains: many(v.domains, &format!("{p}/domains"), domain_ref)?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn endpoint(v: w::Endpoint, p: &str) -> Result<a::Endpoint> {
    Ok(a::Endpoint {
        resource: resource_ref(v.resource, &format!("{p}/resource"))?,
        pin: name(v.pin, &format!("{p}/pin"))?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn connection(v: w::Connection, p: &str) -> Result<a::Connection> {
    Ok(a::Connection {
        name: name(v.name, &format!("{p}/name"))?,
        sources: many(v.sources, &format!("{p}/sources"), endpoint)?,
        destination: endpoint(v.destination, &format!("{p}/destination"))?,
        selector: v
            .selector
            .0
            .map(|v| field_ref(v, &format!("{p}/selector")))
            .transpose()?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn group(v: w::ModeGroup, p: &str) -> Result<a::ModeGroup> {
    Ok(a::ModeGroup {
        name: name(v.name, &format!("{p}/name"))?,
        resources: many(v.resources, &format!("{p}/resources"), resource_ref)?,
        modes: names(v.modes, &format!("{p}/modes"))?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn choice(v: w::ModeChoice, p: &str) -> Result<a::ModeChoice> {
    Ok(a::ModeChoice {
        group: name(v.group, &format!("{p}/group"))?,
        mode: name(v.mode, &format!("{p}/mode"))?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn storage(v: w::Storage, p: &str) -> Result<a::Storage> {
    Ok(a::Storage {
        name: name(v.name, &format!("{p}/name"))?,
        owner: resource_ref(v.owner, &format!("{p}/owner"))?,
        bits: t::BitCount::new(v.bits.0),
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn feature(v: w::Feature, p: &str) -> Result<a::Feature> {
    if v.range.unit != "bit" {
        return Err(ExchangeError::new(
            "invalid_enum",
            "decode",
            format!("{p}/range/unit"),
            "logical range must use bit units",
        ));
    }
    let range = t::BitRange::new(
        t::BitOffset::new(v.range.start.0),
        t::BitCount::new(v.range.length.0),
    )
    .map_err(|e| err(&format!("{p}/range"), e))?;
    Ok(a::Feature {
        name: name(v.name, &format!("{p}/name"))?,
        owner: resource_ref(v.owner, &format!("{p}/owner"))?,
        storage: name(v.storage, &format!("{p}/storage"))?,
        range,
        width: t::Width::new(v.width.0).map_err(|e| err(&format!("{p}/width"), e))?,
        domain: match v.domain {
            w::ValueDomain::Any => a::ValueDomain::Any,
            w::ValueDomain::Range { minimum, maximum } => a::ValueDomain::Range {
                minimum: minimum.0,
                maximum: maximum.0,
            },
            w::ValueDomain::Set { values } => {
                a::ValueDomain::Set(values.into_iter().map(|v| v.0).collect())
            }
        },
        guard: many(v.guard, &format!("{p}/guard"), choice)?,
        alias_of: v
            .alias_of
            .0
            .map(|v| field_ref(v, &format!("{p}/alias_of")))
            .transpose()?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
fn template(v: w::Template, p: &str) -> Result<a::Template> {
    Ok(a::Template {
        key: key(v.key, &format!("{p}/key"))?,
        resources: many(v.resources, &format!("{p}/resources"), resource)?,
        children: many(v.children, &format!("{p}/children"), instance)?,
        mode_groups: many(v.mode_groups, &format!("{p}/mode_groups"), group)?,
        storage: many(v.storage, &format!("{p}/storage"), storage)?,
        features: many(v.features, &format!("{p}/features"), feature)?,
        connections: many(v.connections, &format!("{p}/connections"), connection)?,
        provenance: provenance(v.provenance, &format!("{p}/provenance"))?,
    })
}
pub(crate) fn into_core(v: w::Architecture) -> Result<a::Architecture> {
    Ok(a::Architecture {
        namespace: name(v.namespace, "/body/namespace")?,
        resource_types: many(v.resource_types, "/body/resource_types", ty)?,
        templates: many(v.templates, "/body/templates", template)?,
        roots: many(v.roots, "/body/roots", instance)?,
        partitions: many(v.partitions, "/body/partitions", |v, p| {
            u32::try_from(v.0).map(t::PartitionId::new).map_err(|_| {
                ExchangeError::new("overflow", "decode", p, "partition exceeds u32")
                    .bounds(v.0, u32::MAX)
            })
        })?,
        domains: many(v.domains, "/body/domains", domain)?,
        connections: many(v.connections, "/body/connections", connection)?,
        provenance: provenance(v.provenance, "/body/provenance")?,
    })
}

// Reverse adapters construct temporary wire data only for output. Accepted
// architecture documents retain one authoritative core model, not DTO + model.
fn pv(v: &t::Provenance) -> w::Provenance {
    w::Provenance {
        span: w::Nullable(v.span().map(|s| w::Span {
            source: s.source().into(),
            source_bytes: w::U64(s.source_bytes().get()),
            start: w::U64(s.start().get()),
            end: w::U64(s.end().get()),
        })),
        display: w::Nullable(v.display().map(str::to_owned)),
    }
}
fn ky<K: t::ResourceMarker>(v: &t::Key<K>) -> w::Key {
    w::Key {
        kind: kind_name(v.kind()).into(),
        namespace: v.namespace().to_string(),
        scope: v.scope().iter().map(ToString::to_string).collect(),
        local: v.local().to_string(),
    }
}
fn kn(v: a::ResourceKind) -> String {
    match v {
        a::ResourceKind::Wire => "wire",
        a::ResourceKind::Pip => "pip",
        a::ResourceKind::Bel => "bel",
        a::ResourceKind::Pin => "pin",
        a::ResourceKind::Node => "node",
        a::ResourceKind::Site => "site",
        a::ResourceKind::Field => "field",
    }
    .into()
}
fn dk(v: a::DomainClass) -> String {
    match v {
        a::DomainClass::Clock => "clock",
        a::DomainClass::Power => "power",
        a::DomainClass::Configuration => "configuration",
        a::DomainClass::Placement => "placement",
        a::DomainClass::Routing => "routing",
    }
    .into()
}
fn ns(v: &[t::Name]) -> Vec<String> {
    v.iter().map(ToString::to_string).collect()
}
fn wp(v: &a::Pin) -> w::Pin {
    w::Pin {
        name: v.name.to_string(),
        direction: match v.direction {
            a::Direction::Input => "input",
            a::Direction::Output => "output",
        }
        .into(),
        width: w::U64(v.width.get()),
        provenance: pv(&v.provenance),
    }
}
fn wd(v: &a::DomainRef) -> w::Domain {
    w::Domain {
        key: ky(&v.key),
        kind: dk(v.kind),
        provenance: pv(&v.provenance),
    }
}
fn wr(v: &a::ResourceRef) -> w::ResourceRef {
    w::ResourceRef {
        path: ns(&v.path),
        name: v.name.to_string(),
        kind: kn(v.kind),
        provenance: pv(&v.provenance),
    }
}
fn wf(v: &a::FieldRef) -> w::FieldRef {
    w::FieldRef {
        path: ns(&v.path),
        name: v.name.to_string(),
        provenance: pv(&v.provenance),
    }
}
fn wi(v: &a::Instance) -> w::Instance {
    w::Instance {
        name: v.name.to_string(),
        template: ky(&v.template),
        partition: w::Nullable(v.partition.map(|v| w::U64(u64::from(v.get())))),
        domains: v.domains.iter().map(wd).collect(),
        provenance: pv(&v.provenance),
    }
}
fn we(v: &a::Endpoint) -> w::Endpoint {
    w::Endpoint {
        resource: wr(&v.resource),
        pin: v.pin.to_string(),
        provenance: pv(&v.provenance),
    }
}
fn wc(v: &a::Connection) -> w::Connection {
    w::Connection {
        name: v.name.to_string(),
        sources: v.sources.iter().map(we).collect(),
        destination: we(&v.destination),
        selector: w::Nullable(v.selector.as_ref().map(wf)),
        provenance: pv(&v.provenance),
    }
}
fn wt(v: &a::Template) -> w::Template {
    w::Template {
        key: ky(&v.key),
        resources: v
            .resources
            .iter()
            .map(|v| w::Resource {
                name: v.name.to_string(),
                kind: kn(v.kind),
                resource_type: ky(&v.resource_type),
                alias_of: w::Nullable(v.alias_of.as_ref().map(wr)),
                domains: v.domains.iter().map(wd).collect(),
                provenance: pv(&v.provenance),
            })
            .collect(),
        children: v.children.iter().map(wi).collect(),
        mode_groups: v
            .mode_groups
            .iter()
            .map(|v| w::ModeGroup {
                name: v.name.to_string(),
                resources: v.resources.iter().map(wr).collect(),
                modes: ns(&v.modes),
                provenance: pv(&v.provenance),
            })
            .collect(),
        storage: v
            .storage
            .iter()
            .map(|v| w::Storage {
                name: v.name.to_string(),
                owner: wr(&v.owner),
                bits: w::U64(v.bits.get()),
                provenance: pv(&v.provenance),
            })
            .collect(),
        features: v
            .features
            .iter()
            .map(|v| w::Feature {
                name: v.name.to_string(),
                owner: wr(&v.owner),
                storage: v.storage.to_string(),
                range: w::BitRange {
                    unit: "bit".into(),
                    start: w::U64(v.range.start().get()),
                    length: w::U64(v.range.length().get()),
                },
                width: w::U64(u64::from(v.width.get())),
                domain: match &v.domain {
                    a::ValueDomain::Any => w::ValueDomain::Any,
                    a::ValueDomain::Range { minimum, maximum } => w::ValueDomain::Range {
                        minimum: w::U64(*minimum),
                        maximum: w::U64(*maximum),
                    },
                    a::ValueDomain::Set(v) => w::ValueDomain::Set {
                        values: v.iter().copied().map(w::U64).collect(),
                    },
                },
                guard: v
                    .guard
                    .iter()
                    .map(|v| w::ModeChoice {
                        group: v.group.to_string(),
                        mode: v.mode.to_string(),
                        provenance: pv(&v.provenance),
                    })
                    .collect(),
                alias_of: w::Nullable(v.alias_of.as_ref().map(wf)),
                provenance: pv(&v.provenance),
            })
            .collect(),
        connections: v.connections.iter().map(wc).collect(),
        provenance: pv(&v.provenance),
    }
}
pub(crate) fn from_core(v: &a::Architecture, id: &w::Digest) -> w::Architecture {
    w::Architecture {
        semantic_id: id.clone(),
        namespace: v.namespace.to_string(),
        resource_types: v
            .resource_types
            .iter()
            .map(|v| w::ResourceType {
                key: ky(&v.key),
                kind: kn(v.kind),
                pins: v.pins.iter().map(wp).collect(),
                modes: ns(&v.modes),
                provenance: pv(&v.provenance),
            })
            .collect(),
        templates: v.templates.iter().map(wt).collect(),
        roots: v.roots.iter().map(wi).collect(),
        partitions: v
            .partitions
            .iter()
            .map(|v| w::U64(u64::from(v.get())))
            .collect(),
        domains: v
            .domains
            .iter()
            .map(|v| w::Domain {
                key: ky(&v.key),
                kind: dk(v.kind),
                provenance: pv(&v.provenance),
            })
            .collect(),
        connections: v.connections.iter().map(wc).collect(),
        provenance: pv(&v.provenance),
    }
}
