//! Private version-0.1 DTOs. Native core layout is never serialized.
use crate::error::{ExchangeError, Result};
use serde::{Deserialize, Deserializer, Serialize, Serializer, de};
use sha2::{Digest as HashDigest, Sha256};
use std::{collections::BTreeMap, fmt, str::FromStr};

#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct Digest(String);
impl Digest {
    pub fn from_hex(value: &str) -> Result<Self> {
        if value.len() != 64
            || !value
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        {
            return Err(ExchangeError::new(
                "identity_mismatch",
                "decode",
                "",
                "digest must contain exactly 64 lowercase hexadecimal characters",
            ));
        }
        Ok(Self(value.into()))
    }
    pub fn as_str(&self) -> &str {
        &self.0
    }
    pub fn of_bytes(bytes: &[u8]) -> Self {
        let hash = Sha256::digest(bytes);
        Self(hash.iter().map(|b| format!("{b:02x}")).collect())
    }
    pub(crate) fn domain(prefix: &[u8], bytes: &[u8]) -> Self {
        let mut h = Sha256::new();
        h.update(prefix);
        h.update(bytes);
        Self(h.finalize().iter().map(|b| format!("{b:02x}")).collect())
    }
}
impl FromStr for Digest {
    type Err = ExchangeError;
    fn from_str(s: &str) -> Result<Self> {
        Self::from_hex(s)
    }
}
impl fmt::Display for Digest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}
impl Serialize for Digest {
    fn serialize<S: Serializer>(&self, s: S) -> std::result::Result<S::Ok, S::Error> {
        s.serialize_str(&self.0)
    }
}
impl<'de> Deserialize<'de> for Digest {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        Self::from_hex(&String::deserialize(d)?)
            .map_err(|e| de::Error::custom(format!("[identity_mismatch] {e}")))
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub(crate) struct U64(pub u64);
impl Serialize for U64 {
    fn serialize<S: Serializer>(&self, s: S) -> std::result::Result<S::Ok, S::Error> {
        s.serialize_str(&self.0.to_string())
    }
}
impl<'de> Deserialize<'de> for U64 {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        let s = String::deserialize(d)?;
        if s.is_empty()
            || (s.len() > 1 && s.starts_with('0'))
            || !s.bytes().all(|b| b.is_ascii_digit())
        {
            return Err(de::Error::custom(
                "[invalid_unsigned] expected decoded ASCII 0|[1-9][0-9]* string",
            ));
        }
        s.parse::<u64>()
            .map(Self)
            .map_err(|_| de::Error::custom("[overflow] decimal quantity exceeds u64"))
    }
}

/// Newtype entry prevents Serde's missing-field deserializer from treating an
/// absent required field as Option::None. Explicit null remains legal.
#[derive(Clone, Debug, Serialize)]
#[serde(transparent)]
pub(crate) struct Nullable<T>(pub Option<T>);
impl<'de, T: Deserialize<'de>> Deserialize<'de> for Nullable<T> {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        struct V<T>(std::marker::PhantomData<T>);
        impl<'de, T: Deserialize<'de>> de::Visitor<'de> for V<T> {
            type Value = Nullable<T>;
            fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("a required, explicitly nullable field")
            }
            fn visit_newtype_struct<D: Deserializer<'de>>(
                self,
                d: D,
            ) -> std::result::Result<Self::Value, D::Error> {
                Option::<T>::deserialize(d).map(Nullable)
            }
        }
        d.deserialize_newtype_struct("RequiredNullable", V(std::marker::PhantomData))
    }
}
macro_rules! record {($name:ident {$($(#[$attr:meta])* $field:ident : $ty:ty),* $(,)?})=>{#[derive(Clone,Debug,Serialize,Deserialize)]#[serde(deny_unknown_fields)]pub(crate) struct $name{$($(#[$attr])* pub $field:$ty),*}}}
// Enum spellings are decoded while the input-ordered field is visited, before
// adapter lowering. Custom errors use fixed leading markers, never input text.
fn checked_string<'de, D: Deserializer<'de>>(
    d: D,
    allowed: &[&str],
) -> std::result::Result<String, D::Error> {
    let value = String::deserialize(d)?;
    if !allowed.contains(&value.as_str()) {
        return Err(de::Error::custom(
            "[invalid_enum] unsupported wire spelling",
        ));
    }
    Ok(value)
}
fn revision<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<u16, D::Error> {
    let value = i64::deserialize(d)?;
    u16::try_from(value).map_err(|_| de::Error::custom("[overflow] revision metadata exceeds u16"))
}
struct PartitionValue(U64);
impl<'de> Deserialize<'de> for PartitionValue {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        let v = U64::deserialize(d)?;
        if v.0 > u64::from(u32::MAX) {
            return Err(de::Error::custom("[overflow] partition exceeds u32"));
        }
        Ok(Self(v))
    }
}
fn partition<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<Nullable<U64>, D::Error> {
    Nullable::<PartitionValue>::deserialize(d).map(|v| Nullable(v.0.map(|v| v.0)))
}
fn partitions<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<Vec<U64>, D::Error> {
    Vec::<PartitionValue>::deserialize(d).map(|v| v.into_iter().map(|v| v.0).collect())
}
fn resource_kind<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<String, D::Error> {
    checked_string(d, &["wire", "pip", "bel", "pin", "node", "site", "field"])
}
fn direction<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<String, D::Error> {
    checked_string(d, &["input", "output"])
}
fn domain_class<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<String, D::Error> {
    checked_string(
        d,
        &["clock", "power", "configuration", "placement", "routing"],
    )
}
fn bit_unit<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<String, D::Error> {
    checked_string(d, &["bit"])
}
fn constant<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<String, D::Error> {
    checked_string(d, &["0", "1"])
}
fn unbound_reason<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<String, D::Error> {
    checked_string(d, &["foundation-unimplemented", "not-supplied"])
}
fn absent_reason<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<String, D::Error> {
    checked_string(d, &["no-hard-macros"])
}
struct CheckedKind<const K: u8>(String);
impl<'de, const K: u8> Deserialize<'de> for CheckedKind<K> {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        checked_string(
            d,
            &[match K {
                0 => "resource_type",
                1 => "template",
                _ => "domain",
            }],
        )
        .map(Self)
    }
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TypedKey<const K: u8> {
    kind: CheckedKind<K>,
    namespace: String,
    scope: Vec<String>,
    local: String,
}
fn typed_key<'de, D: Deserializer<'de>, const K: u8>(d: D) -> std::result::Result<Key, D::Error> {
    let key = TypedKey::<K>::deserialize(d)?;
    Ok(Key {
        kind: key.kind.0,
        namespace: key.namespace,
        scope: key.scope,
        local: key.local,
    })
}
fn resource_type_key<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<Key, D::Error> {
    typed_key::<D, 0>(d)
}
fn template_key<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<Key, D::Error> {
    typed_key::<D, 1>(d)
}
fn domain_key<'de, D: Deserializer<'de>>(d: D) -> std::result::Result<Key, D::Error> {
    typed_key::<D, 2>(d)
}
macro_rules! tagged {
    ($name:ident,$input:ident,$tag:literal,{$($variant:ident $( { $($(#[$attr:meta])* $field:ident:$ty:ty),* $(,)? } )?),* $(,)?})=>{
        #[derive(Clone,Debug,Serialize)]#[serde(tag=$tag,rename_all="snake_case")]
        pub(crate) enum $name{$($variant $({$($(#[$attr])* $field:$ty),*})?),*}
        #[derive(Deserialize)]#[serde(rename_all="snake_case",deny_unknown_fields)]
        enum $input{$($variant $({$($(#[$attr])* $field:$ty),*})?),*}
        impl<'de> Deserialize<'de> for $name{fn deserialize<D:Deserializer<'de>>(d:D)->std::result::Result<Self,D::Error>{Ok(match $input::deserialize(d)?{$($input::$variant $({$($field),*})?=>Self::$variant $({$($field),*})?),*})}}
    }
}
record!(Version {
    #[serde(deserialize_with = "revision")]
    major: u16,
    #[serde(deserialize_with = "revision")]
    minor: u16
});
record!(Profile {
    id: String,
    #[serde(deserialize_with = "revision")]
    revision: u16
});
record!(Capability {
    id: String,
    #[serde(deserialize_with = "revision")]
    revision: u16
});
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Envelope {
    pub format: String,
    pub version: Version,
    pub profile: Profile,
    pub required_features: Vec<Capability>,
    pub optional_features: Vec<Capability>,
    pub annotations: BTreeMap<String, serde_json::Value>,
    pub body: crate::parser::Value,
}
#[derive(Clone, Debug, Serialize)]
pub(crate) struct Header {
    pub format: String,
    pub version: Version,
    pub profile: Profile,
    pub required_features: Vec<Capability>,
    pub optional_features: Vec<Capability>,
    pub annotations: BTreeMap<String, serde_json::Value>,
}
impl Header {
    pub fn contract(&self) -> String {
        format!(
            "{} {}.{} {}/{}",
            self.format,
            self.version.major,
            self.version.minor,
            self.profile.id,
            self.profile.revision
        )
    }
}
record!(Key{kind:String,namespace:String,scope:Vec<String>,local:String});
impl Key {
    pub fn cmp_key(&self, other: &Self) -> std::cmp::Ordering {
        (&self.kind, &self.namespace, &self.scope, &self.local).cmp(&(
            &other.kind,
            &other.namespace,
            &other.scope,
            &other.local,
        ))
    }
}
record!(Span {
    source: String,
    source_bytes: U64,
    start: U64,
    end: U64
});
record!(Provenance{span:Nullable<Span>,display:Nullable<String>});
record!(Pin {
    name: String,
    #[serde(deserialize_with = "direction")]
    direction: String,
    width: U64,
    provenance: Provenance
});
record!(ResourceType{#[serde(deserialize_with="resource_type_key")] key:Key,#[serde(deserialize_with="resource_kind")] kind:String,pins:Vec<Pin>,modes:Vec<String>,provenance:Provenance});
record!(Domain {
    #[serde(deserialize_with = "domain_key")]
    key: Key,
    #[serde(deserialize_with = "domain_class")]
    kind: String,
    provenance: Provenance
});
record!(ResourceRef{path:Vec<String>,name:String,#[serde(deserialize_with="resource_kind")] kind:String,provenance:Provenance});
impl ResourceRef {
    pub fn cmp_ref(&self, other: &Self) -> std::cmp::Ordering {
        (&self.kind, &self.path, &self.name).cmp(&(&other.kind, &other.path, &other.name))
    }
}
record!(Resource{name:String,#[serde(deserialize_with="resource_kind")] kind:String,#[serde(deserialize_with="resource_type_key")] resource_type:Key,alias_of:Nullable<ResourceRef>,domains:Vec<Domain>,provenance:Provenance});
record!(Instance{name:String,#[serde(deserialize_with="template_key")] template:Key,#[serde(deserialize_with="partition")] partition:Nullable<U64>,domains:Vec<Domain>,provenance:Provenance});
record!(Endpoint {
    resource: ResourceRef,
    pin: String,
    provenance: Provenance
});
record!(FieldRef{path:Vec<String>,name:String,provenance:Provenance});
record!(Connection{name:String,sources:Vec<Endpoint>,destination:Endpoint,selector:Nullable<FieldRef>,provenance:Provenance});
record!(ModeGroup{name:String,resources:Vec<ResourceRef>,modes:Vec<String>,provenance:Provenance});
record!(ModeChoice {
    group: String,
    mode: String,
    provenance: Provenance
});
record!(Storage {
    name: String,
    owner: ResourceRef,
    bits: U64,
    provenance: Provenance
});
record!(BitRange {
    #[serde(deserialize_with = "bit_unit")]
    unit: String,
    start: U64,
    length: U64
});
tagged!(ValueDomain,ValueDomainInput,"kind",{Any,Range{minimum:U64,maximum:U64},Set{values:Vec<U64>}});
record!(Feature{name:String,owner:ResourceRef,storage:String,range:BitRange,width:U64,domain:ValueDomain,guard:Vec<ModeChoice>,alias_of:Nullable<FieldRef>,provenance:Provenance});
record!(Template{#[serde(deserialize_with="template_key")] key:Key,resources:Vec<Resource>,children:Vec<Instance>,mode_groups:Vec<ModeGroup>,storage:Vec<Storage>,features:Vec<Feature>,connections:Vec<Connection>,provenance:Provenance});
record!(Architecture{semantic_id:Digest,namespace:String,resource_types:Vec<ResourceType>,templates:Vec<Template>,roots:Vec<Instance>,#[serde(deserialize_with="partitions")] partitions:Vec<U64>,domains:Vec<Domain>,connections:Vec<Connection>,provenance:Provenance});
record!(Cell {
    name: String,
    #[serde(deserialize_with = "resource_type_key")]
    resource_type: Key,
    mode: String,
    provenance: Provenance
});
tagged!(Terminal,TerminalInput,"kind",{Cell{cell:String,pin:String,bit:U64,provenance:Provenance},Port{port:String,bit:U64,provenance:Provenance},Constant{#[serde(deserialize_with="constant")] value:String,provenance:Provenance}});
impl Terminal {
    pub fn sort_key(&self) -> (&str, &str, &str, u64) {
        match self {
            Self::Cell { cell, pin, bit, .. } => ("cell", cell, pin, bit.0),
            Self::Port { port, bit, .. } => ("port", port, "", bit.0),
            Self::Constant { value, .. } => ("constant", value, "", 0),
        }
    }
}
record!(Net{name:String,driver:Terminal,loads:Vec<Terminal>,provenance:Provenance});
record!(Design{semantic_id:Digest,namespace:String,name:String,target_build_id:Digest,cells:Vec<Cell>,ports:Vec<Pin>,nets:Vec<Net>,provenance:Provenance});
record!(Artifact {
    sha256: Digest,
    bytes: U64
});
record!(ArchitectureBinding {
    semantic_id: Digest,
    artifact: Artifact
});
record!(Library {
    id: String,
    revision: String,
    artifact: Artifact
});
record!(ToolOption {
    name: String,
    value: String
});
tagged!(ToolBinding,ToolBindingInput,"state",{Bound{id:String,version:String,implementation_sha256:Digest,options:Vec<ToolOption>},Unbound{#[serde(deserialize_with="unbound_reason")] reason:String}});
tagged!(ViewBinding,ViewBindingInput,"state",{Bound{revision:String,artifact:Artifact},Unbound{#[serde(deserialize_with="unbound_reason")] reason:String},Absent{#[serde(deserialize_with="absent_reason")] reason:String}});
record!(Package{build_id:Digest,architecture:ArchitectureBinding,libraries:Vec<Library>,authoring:ToolBinding,compiler:ToolBinding,backend:ToolBinding,device_db:ViewBinding,physical_implementation:ViewBinding,technology:ViewBinding,macro_bindings:ViewBinding,configuration_map:ViewBinding,transport:ViewBinding,activation:ViewBinding,timing_datasets:ViewBinding,external_pin_map:ViewBinding});
impl Package {
    pub fn views(&self) -> [(&str, &ViewBinding); 9] {
        [
            ("device_db", &self.device_db),
            ("physical_implementation", &self.physical_implementation),
            ("technology", &self.technology),
            ("macro_bindings", &self.macro_bindings),
            ("configuration_map", &self.configuration_map),
            ("transport", &self.transport),
            ("activation", &self.activation),
            ("timing_datasets", &self.timing_datasets),
            ("external_pin_map", &self.external_pin_map),
        ]
    }
}
