use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::marker::PhantomData;

use crate::diagnostics::identity_error;
use crate::{Code, Diagnostic};

pub const MAX_COMPONENT_BYTES: usize = 128;
pub const MAX_SCOPE_COMPONENTS: usize = 64;
pub const MAX_KEY_BYTES: usize = 4096;
/// A table can contain every `u32` index, including `u32::MAX`.
pub const MAX_TABLE_COUNT: u64 = 1_u64 << 32;

/// Exact, nonempty UTF-8 name of at most [`MAX_COMPONENT_BYTES`] bytes.
/// No characters are interpreted as separators, traversal, or normalization.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Name(String);

impl Name {
    pub fn new(value: impl Into<String>) -> Result<Self, Diagnostic> {
        let value = value.into();
        if value.is_empty() {
            return Err(
                identity_error(Code::InvalidName, "semantic name must not be empty")
                    .with_actual("0 bytes")
                    .with_expected("1..=128 UTF-8 bytes")
                    .with_remedy("Provide an explicit nonempty semantic name."),
            );
        }
        if value.len() > MAX_COMPONENT_BYTES {
            return Err(identity_error(
                Code::Limit,
                "semantic name exceeds the component byte limit",
            )
            .with_actual(value.len().to_string())
            .with_expected(MAX_COMPONENT_BYTES.to_string())
            .with_remedy(
                "Use a shorter explicit key component without changing its intended identity.",
            ));
        }
        Ok(Self(value))
    }
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl AsRef<str> for Name {
    fn as_ref(&self) -> &str {
        self.as_str()
    }
}
impl fmt::Display for Name {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

/// Runtime counterpart of the nominal marker types. Its discriminants are not
/// a serialization format; portable identity includes the explicit kind.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum Kind {
    Wire,
    Pip,
    Bel,
    Pin,
    Node,
    Site,
    Field,
    Template,
    ResourceType,
    Domain,
    ModeGroup,
    Storage,
}

mod sealed {
    pub trait Sealed {}
}

/// Closed set of nominal identity markers. External code cannot add a marker
/// that claims an existing kind and thereby weakens the typed boundary.
pub trait ResourceMarker:
    sealed::Sealed + Clone + Copy + fmt::Debug + Eq + Ord + std::hash::Hash
{
    const KIND: Kind;
}

macro_rules! markers {
    ($(($marker:ident, $id:ident, $key:ident)),+ $(,)?) => {$ (
        #[doc = concat!("Nominal ", stringify!($marker), " identity marker.")]
        #[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
        pub enum $marker {}
        impl sealed::Sealed for $marker {}
        impl ResourceMarker for $marker { const KIND: Kind = Kind::$marker; }
        pub type $id = DenseId<$marker>;
        pub type $key = Key<$marker>;
    )+};
}

markers!(
    (Wire, WireId, WireKey),
    (Pip, PipId, PipKey),
    (Bel, BelId, BelKey),
    (Pin, PinId, PinKey),
    (Node, NodeId, NodeKey),
    (Site, SiteId, SiteKey),
    (Field, FieldId, FieldKey),
    (Template, TemplateId, TemplateKey),
    (ResourceType, ResourceTypeId, ResourceTypeKey),
    (Domain, DomainId, DomainKey),
    (ModeGroup, ModeGroupId, ModeGroupKey),
    (Storage, StorageId, StorageKey),
);

/// A typed portable key with exact namespace, ordered scope, and local name.
/// Names containing separators remain a single component. Provenance and
/// display labels are deliberately absent from equality and ordering.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Key<K: ResourceMarker> {
    namespace: Name,
    scope: Vec<Name>,
    local: Name,
    marker: PhantomData<K>,
}

impl<K: ResourceMarker> Key<K> {
    pub fn new(
        namespace: impl Into<String>,
        scope: Vec<String>,
        local: impl Into<String>,
    ) -> Result<Self, Diagnostic> {
        if scope.len() > MAX_SCOPE_COMPONENTS {
            return Err(identity_error(Code::Limit, "portable key has too many scope components")
                .with_actual(scope.len().to_string()).with_expected(MAX_SCOPE_COMPONENTS.to_string())
                .with_remedy("Use a supported finite scope depth without joining or dropping components."));
        }
        let namespace = Name::new(namespace)?;
        let local = Name::new(local)?;
        let mut bytes = namespace.as_str().len() + local.as_str().len();
        // Scope length and each component are bounded before allocating a
        // second vector. Total counts UTF-8 data bytes, not invented delimiters.
        for component in &scope {
            if component.is_empty() {
                return Err(identity_error(
                    Code::InvalidName,
                    "portable key has an empty scope component",
                )
                .with_actual("0 bytes")
                .with_expected("1..=128 UTF-8 bytes")
                .with_remedy("Provide every scope component explicitly."));
            }
            if component.len() > MAX_COMPONENT_BYTES {
                return Err(identity_error(
                    Code::Limit,
                    "portable key scope component is too long",
                )
                .with_actual(component.len().to_string())
                .with_expected(MAX_COMPONENT_BYTES.to_string())
                .with_remedy("Use a shorter explicit scope component."));
            }
            // At most 66 components of 128 bytes makes this addition bounded.
            bytes += component.len();
        }
        if bytes > MAX_KEY_BYTES {
            return Err(identity_error(
                Code::Limit,
                "portable key exceeds its total UTF-8 byte limit",
            )
            .with_actual(bytes.to_string())
            .with_expected(MAX_KEY_BYTES.to_string())
            .with_remedy("Reduce the complete structured key to the supported byte limit."));
        }
        Ok(Self {
            namespace,
            scope: scope.into_iter().map(Name).collect(),
            local,
            marker: PhantomData,
        })
    }
    pub fn namespace(&self) -> &Name {
        &self.namespace
    }
    pub fn scope(&self) -> &[Name] {
        &self.scope
    }
    pub fn local(&self) -> &Name {
        &self.local
    }
    pub const fn kind(&self) -> Kind {
        K::KIND
    }
    pub fn erase(&self) -> SemanticKey {
        SemanticKey {
            kind: K::KIND,
            namespace: self.namespace.clone(),
            scope: self.scope.clone(),
            local: self.local.clone(),
        }
    }
}

/// A checked portable key retaining its runtime kind for mixed-kind diagnostics.
/// Construction is through typed keys; there is no unchecked string parser.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct SemanticKey {
    kind: Kind,
    namespace: Name,
    scope: Vec<Name>,
    local: Name,
}

impl SemanticKey {
    pub const fn kind(&self) -> Kind {
        self.kind
    }
    pub fn namespace(&self) -> &Name {
        &self.namespace
    }
    pub fn scope(&self) -> &[Name] {
        &self.scope
    }
    pub fn local(&self) -> &Name {
        &self.local
    }
}

/// Opaque, explicitly supplied build identity. This type neither computes a
/// canonical hash nor asserts that a digest authenticates any package.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct BuildId([u8; 32]);

impl BuildId {
    pub const fn new(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }
    pub const fn bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

/// Partition number within a build; the context verifies that it exists.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct PartitionId(u32);
impl PartitionId {
    pub const fn new(value: u32) -> Self {
        Self(value)
    }
    pub const fn get(self) -> u32 {
        self.0
    }
}

/// A nominal `u32` table index, not a portable key or a verified local pointer.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct DenseId<K: ResourceMarker> {
    local: u32,
    marker: PhantomData<K>,
}

impl<K: ResourceMarker> DenseId<K> {
    pub const fn new(local: u32) -> Self {
        Self {
            local,
            marker: PhantomData,
        }
    }
    pub const fn get(self) -> u32 {
        self.local
    }
    pub fn try_from_u64(value: u64) -> Result<Self, Diagnostic> {
        u32::try_from(value).map(Self::new).map_err(|_| {
            identity_error(Code::Overflow, "dense local index exceeds u32")
                .with_actual(value.to_string())
                .with_expected(u32::MAX.to_string())
                .with_remedy(
                    "Use a supported partition-local index and explicit partition reference.",
                )
        })
    }
}

/// A typed reference that carries exact build and partition qualification.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct DenseRef<K: ResourceMarker> {
    build: BuildId,
    partition: PartitionId,
    local: DenseId<K>,
}

impl<K: ResourceMarker> DenseRef<K> {
    pub const fn new(build: BuildId, partition: PartitionId, local: DenseId<K>) -> Self {
        Self {
            build,
            partition,
            local,
        }
    }
    pub const fn build(self) -> BuildId {
        self.build
    }
    pub const fn partition(self) -> PartitionId {
        self.partition
    }
    pub const fn local(self) -> DenseId<K> {
        self.local
    }
    pub const fn erase(self) -> UntypedDenseRef {
        UntypedDenseRef::new(self.build, self.partition, K::KIND, self.local.get())
    }
}

/// Untrusted mixed-kind reference at a public boundary. A partition table must
/// validate every qualification before its index can be used locally.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct UntypedDenseRef {
    build: BuildId,
    partition: PartitionId,
    kind: Kind,
    local: u32,
}
impl UntypedDenseRef {
    pub const fn new(build: BuildId, partition: PartitionId, kind: Kind, local: u32) -> Self {
        Self {
            build,
            partition,
            kind,
            local,
        }
    }
    pub const fn build(self) -> BuildId {
        self.build
    }
    pub const fn partition(self) -> PartitionId {
        self.partition
    }
    pub const fn kind(self) -> Kind {
        self.kind
    }
    pub const fn local(self) -> u32 {
        self.local
    }
}

/// Actual number of entries in a dense table, including the possible count
/// `2^32`. This is distinct from the greatest representable `u32` index.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct TableCount(u64);
impl TableCount {
    pub fn new(value: u64) -> Result<Self, Diagnostic> {
        if value > MAX_TABLE_COUNT {
            return Err(
                identity_error(Code::Bounds, "table count exceeds local index capacity")
                    .with_actual(value.to_string())
                    .with_expected(MAX_TABLE_COUNT.to_string())
                    .with_remedy(
                        "Split the table into explicit partitions before assigning local IDs.",
                    ),
            );
        }
        Ok(Self(value))
    }
    pub const fn get(self) -> u64 {
        self.0
    }
}

/// Immutable typed table context. It describes actual populated entries, not
/// reserved allocation capacity, and never allocates memory for the table.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct PartitionTable<K: ResourceMarker> {
    build: BuildId,
    partition: PartitionId,
    count: TableCount,
    marker: PhantomData<K>,
}

impl<K: ResourceMarker> PartitionTable<K> {
    pub const fn new(build: BuildId, partition: PartitionId, count: TableCount) -> Self {
        Self {
            build,
            partition,
            count,
            marker: PhantomData,
        }
    }
    pub const fn build(self) -> BuildId {
        self.build
    }
    pub const fn partition(self) -> PartitionId {
        self.partition
    }
    pub const fn count(self) -> TableCount {
        self.count
    }
    pub fn resolve(&self, reference: &DenseRef<K>) -> Result<usize, Diagnostic> {
        self.resolve_erased(&reference.erase())
    }
    pub fn resolve_erased(&self, reference: &UntypedDenseRef) -> Result<usize, Diagnostic> {
        // All qualifications are checked before any platform-index conversion.
        if reference.build != self.build {
            return Err(identity_error(
                Code::BuildMismatch,
                "dense reference belongs to another build",
            )
            .with_actual(format!("{:?}", reference.build))
            .with_expected(format!("{:?}", self.build))
            .with_remedy("Supply an explicitly rebound reference for this exact build."));
        }
        if reference.partition != self.partition {
            return Err(identity_error(
                Code::PartitionMismatch,
                "dense reference belongs to another partition",
            )
            .with_actual(reference.partition.get().to_string())
            .with_expected(self.partition.get().to_string())
            .with_remedy("Resolve the reference against its declared partition table."));
        }
        if reference.kind != K::KIND {
            return Err(identity_error(
                Code::WrongKind,
                "dense reference has the wrong resource kind",
            )
            .with_actual(format!("{:?}", reference.kind))
            .with_expected(format!("{:?}", K::KIND))
            .with_remedy("Use a reference with the table's declared resource kind."));
        }
        if u64::from(reference.local) >= self.count.get() {
            return Err(identity_error(
                Code::Bounds,
                "dense local index is outside the declared table",
            )
            .with_actual(reference.local.to_string())
            .with_expected(format!("index < {}", self.count.get()))
            .with_remedy("Supply an index of an existing entry in this exact table."));
        }
        usize::try_from(reference.local).map_err(|_| {
            identity_error(
                Code::Overflow,
                "dense local index exceeds this platform's index width",
            )
            .with_actual(reference.local.to_string())
            .with_expected(usize::MAX.to_string())
            .with_remedy("Use a platform supporting the table's checked local index range.")
        })
    }
}

fn correspondence_error(message: &str) -> Diagnostic {
    identity_error(Code::Correspondence, message).with_remedy(
        "Provide an explicit, total, one-to-one portable-key to qualified-dense-reference map.",
    )
}

/// Validate an explicit complete correspondence for one build and resource kind.
///
/// `expected` is the independently declared portable-key universe; `entries`
/// lists the supplied mappings. Each table's count is the number of actual
/// dense entries, not spare capacity. Every declared key and every dense slot
/// must occur exactly once. No mapping is inferred from name or numeric equality.
///
/// Cardinalities are checked against a checked `u64` sum before constructing
/// indexes, so a declared `2^32` count with a tiny input fails without giant
/// allocation. Work and retained indexes are O(n log n) / O(n) in supplied keys,
/// entries and partitions; no operation iterates over the numeric table range.
/// Errors are deterministic under permutations of these keyed collections.
pub fn validate_correspondence<K: ResourceMarker>(
    expected: &[Key<K>],
    entries: &[(Key<K>, DenseRef<K>)],
    tables: &[PartitionTable<K>],
) -> Result<(), Diagnostic> {
    let mut total = 0_u64;
    let build = tables.iter().map(|table| table.build).min();
    // Cardinality and build checks are independent of declaration order and
    // happen without index allocation, including the giant-count rejection.
    for table in tables {
        total = total.checked_add(table.count.get()).ok_or_else(|| {
            identity_error(Code::Overflow, "sum of dense table counts exceeds u64")
                .with_expected(u64::MAX.to_string())
                .with_remedy("Reduce the declared correspondence universe to supported counts.")
        })?;
    }
    if let Some(other) = tables
        .iter()
        .map(|table| table.build)
        .filter(|id| Some(*id) != build)
        .min()
    {
        return Err(identity_error(
            Code::BuildMismatch,
            "correspondence tables describe different builds",
        )
        .with_actual(format!("{other:?}"))
        .with_expected(format!("{build:?}"))
        .with_remedy("Validate each exact build separately with an explicit correspondence."));
    }
    let expected_count = u64::try_from(expected.len())
        .map_err(|_| correspondence_error("portable-key count exceeds u64"))?;
    let entry_count = u64::try_from(entries.len())
        .map_err(|_| correspondence_error("mapping count exceeds u64"))?;
    if expected_count != total || entry_count != total {
        return Err(correspondence_error(
            "portable keys, supplied mappings and dense tables are not total",
        )
        .with_actual(format!("keys={expected_count}, mappings={entry_count}"))
        .with_expected(format!("{total} keys and {total} mappings")));
    }

    let mut ordered_tables: Vec<_> = tables.iter().collect();
    ordered_tables.sort();
    let mut by_partition = BTreeMap::new();
    for table in ordered_tables {
        if by_partition.insert(table.partition, table).is_some() {
            return Err(
                correspondence_error("partition table is declared more than once")
                    .with_actual(table.partition.get().to_string())
                    .with_expected("one table per partition"),
            );
        }
    }
    let mut ordered_expected: Vec<_> = expected.iter().collect();
    ordered_expected.sort();
    for pair in ordered_expected.windows(2) {
        if pair[0] == pair[1] {
            return Err(
                correspondence_error("expected portable key is declared more than once")
                    .with_key(pair[0].erase()),
            );
        }
    }
    let expected_set: BTreeSet<_> = ordered_expected.into_iter().collect();
    let mut ordered_entries: Vec<_> = entries.iter().collect();
    ordered_entries.sort();
    let mut seen_keys = BTreeSet::new();
    let mut seen_dense = BTreeSet::new();
    for (key, reference) in ordered_entries {
        if !expected_set.contains(key) {
            return Err(
                correspondence_error("mapping names an undeclared portable key")
                    .with_key(key.erase()),
            );
        }
        if !seen_keys.insert(key) {
            return Err(
                correspondence_error("portable key has more than one dense mapping")
                    .with_key(key.erase()),
            );
        }
        if Some(reference.build) != build {
            return Err(identity_error(
                Code::BuildMismatch,
                "mapped reference belongs to another build",
            )
            .with_key(key.erase())
            .with_actual(format!("{:?}", reference.build))
            .with_expected(format!("{build:?}"))
            .with_remedy(
                "Explicitly rebind the portable key to a reference in the expected build.",
            ));
        }
        let table = by_partition.get(&reference.partition).ok_or_else(|| {
            identity_error(
                Code::PartitionMismatch,
                "mapping references an undeclared partition",
            )
            .with_key(key.erase())
            .with_actual(reference.partition.get().to_string())
            .with_expected("an explicitly declared partition")
            .with_remedy("Declare the referenced table or correct the partition-qualified mapping.")
        })?;
        table
            .resolve(reference)
            .map_err(|error| error.with_key(key.erase()))?;
        if !seen_dense.insert(reference) {
            return Err(correspondence_error(
                "dense entry is mapped by more than one portable key",
            )
            .with_key(key.erase()));
        }
    }
    // Equal cardinalities, unique expected keys and mappings, and in-bounds
    // unique dense slots prove totality without enumerating absent table slots.
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{FieldKey, Kind, ModeGroupKey, StorageKey};

    #[test]
    fn declaration_categories_have_distinct_portable_identity() {
        let field = FieldKey::new("fixture", vec![], "same").unwrap().erase();
        let group = ModeGroupKey::new("fixture", vec![], "same")
            .unwrap()
            .erase();
        let storage = StorageKey::new("fixture", vec![], "same").unwrap().erase();
        assert_eq!(group.kind(), Kind::ModeGroup);
        assert_eq!(storage.kind(), Kind::Storage);
        assert_ne!(field, group);
        assert_ne!(field, storage);
        assert_ne!(group, storage);
    }
}
