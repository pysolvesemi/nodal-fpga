//! Finite, generic architecture declarations and bounded structural validation.
//!
//! This crate does not simulate primitives, allocate physical configuration,
//! compile a DeviceDB, serialize native layouts, or emit hardware. Templates
//! remain shared declarations; [`ValidatedArchitecture`] borrows them immutably.
#![forbid(unsafe_code)]

mod validate;

use nf_types::{
    BitCount, BitRange, Domain as DomainKind, Key, Name, PartitionId, Provenance,
    ResourceType as ResourceTypeKind, Template as TemplateKind, Width,
};
pub use validate::{
    ValidatedArchitecture, ValidationLimits, ValidationStats, validate_architecture,
    validate_selection,
};

/// The kind of a local resource reference is checked independently of its name.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum ResourceKind {
    Wire,
    Pip,
    Bel,
    Pin,
    Node,
    Site,
    Field,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum Direction {
    Input,
    Output,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum DomainClass {
    Clock,
    Power,
    Configuration,
    Placement,
    Routing,
}

#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Pin {
    pub name: Name,
    pub direction: Direction,
    pub width: BitCount,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct ResourceType {
    pub key: Key<ResourceTypeKind>,
    pub kind: ResourceKind,
    /// Ordered, never sorted by validation.
    pub pins: Vec<Pin>,
    pub modes: Vec<Name>,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Domain {
    pub key: Key<DomainKind>,
    pub kind: DomainClass,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct DomainRef {
    pub key: Key<DomainKind>,
    pub kind: DomainClass,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct ResourceRef {
    /// Relative child-instance path in templates; absolute root path at architecture scope.
    pub path: Vec<Name>,
    pub name: Name,
    pub kind: ResourceKind,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Resource {
    pub name: Name,
    pub kind: ResourceKind,
    pub resource_type: Key<ResourceTypeKind>,
    /// Only a direct, same-template alias of an owned resource is supported.
    pub alias_of: Option<ResourceRef>,
    pub domains: Vec<DomainRef>,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Instance {
    pub name: Name,
    pub template: Key<TemplateKind>,
    /// Roots require an explicit partition; children inherit unless explicitly set.
    pub partition: Option<PartitionId>,
    pub domains: Vec<DomainRef>,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Endpoint {
    pub resource: ResourceRef,
    pub pin: Name,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct FieldRef {
    pub path: Vec<Name>,
    pub name: Name,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Connection {
    pub name: Name,
    /// A fixed connection has exactly one source and no selector. A mux has
    /// two or more ordered sources and one explicit selector feature.
    pub sources: Vec<Endpoint>,
    pub destination: Endpoint,
    pub selector: Option<FieldRef>,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct ModeGroup {
    pub name: Name,
    pub resources: Vec<ResourceRef>,
    pub modes: Vec<Name>,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct ModeChoice {
    pub group: Name,
    pub mode: Name,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Storage {
    pub name: Name,
    pub owner: ResourceRef,
    pub bits: BitCount,
    pub provenance: Provenance,
}
/// Exact legal values. Set order is nonsemantic; duplicates are errors.
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum ValueDomain {
    Any,
    Range { minimum: u64, maximum: u64 },
    Set(Vec<u64>),
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Feature {
    pub name: Name,
    pub owner: ResourceRef,
    pub storage: Name,
    pub range: BitRange,
    pub width: Width,
    pub domain: ValueDomain,
    pub guard: Vec<ModeChoice>,
    /// Direct same-template alias; identical owner/slice/width/domain required.
    pub alias_of: Option<FieldRef>,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Template {
    pub key: Key<TemplateKind>,
    pub resources: Vec<Resource>,
    pub children: Vec<Instance>,
    pub mode_groups: Vec<ModeGroup>,
    pub storage: Vec<Storage>,
    pub features: Vec<Feature>,
    pub connections: Vec<Connection>,
    pub provenance: Provenance,
}
impl Template {
    pub fn new(key: Key<TemplateKind>) -> Self {
        Self {
            key,
            resources: vec![],
            children: vec![],
            mode_groups: vec![],
            storage: vec![],
            features: vec![],
            connections: vec![],
            provenance: Provenance::default(),
        }
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct Architecture {
    pub namespace: Name,
    pub resource_types: Vec<ResourceType>,
    pub templates: Vec<Template>,
    pub roots: Vec<Instance>,
    pub partitions: Vec<PartitionId>,
    pub domains: Vec<Domain>,
    pub connections: Vec<Connection>,
    pub provenance: Provenance,
}
impl Architecture {
    pub fn new(namespace: Name) -> Self {
        Self {
            namespace,
            resource_types: vec![],
            templates: vec![],
            roots: vec![],
            partitions: vec![],
            domains: vec![],
            connections: vec![],
            provenance: Provenance::default(),
        }
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct ModeSetting {
    pub path: Vec<Name>,
    pub group: Name,
    pub mode: Name,
    pub provenance: Provenance,
}
#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct FeatureSetting {
    /// Absolute instance-qualified reference, never a template definition key.
    pub field: FieldRef,
    pub value: u64,
    pub provenance: Provenance,
}
/// Complete mode choices and one explicit value per active alias-equivalence class.
#[derive(Clone, Debug, Default, Eq, PartialEq, Ord, PartialOrd)]
pub struct Selection {
    pub modes: Vec<ModeSetting>,
    pub features: Vec<FeatureSetting>,
}
