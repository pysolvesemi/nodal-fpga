use crate::Limits;
use crate::error::{ExchangeError, Result, pointer_part};
use serde::de::{self, DeserializeSeed, IntoDeserializer, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer};
use std::{collections::BTreeSet, fmt, io::Read};

/// Input-ordered objects survive until closed-schema decoding. Duplicate keys
/// cannot have been discarded by a map before this representation is built.
#[derive(Debug)]
pub(crate) enum Value {
    Null,
    Bool(bool),
    Integer(i64),
    String(String),
    Array(Vec<Value>),
    Object(Vec<(String, Value)>),
}
impl Value {
    pub(crate) fn into_json(self) -> serde_json::Value {
        match self {
            Self::Null => serde_json::Value::Null,
            Self::Bool(v) => v.into(),
            Self::Integer(v) => v.into(),
            Self::String(v) => v.into(),
            Self::Array(v) => {
                serde_json::Value::Array(v.into_iter().map(Self::into_json).collect())
            }
            Self::Object(v) => {
                serde_json::Value::Object(v.into_iter().map(|(k, v)| (k, v.into_json())).collect())
            }
        }
    }
}
#[derive(Clone, Copy, Debug, serde::Serialize)]
pub struct JsonStats {
    pub nodes: u64,
    pub depth: usize,
}
struct Budget<'a> {
    limits: &'a Limits,
    stats: JsonStats,
    depth: usize,
    path: Vec<String>,
    error: Option<ExchangeError>,
}
impl Budget<'_> {
    fn pointer(&self) -> String {
        self.path
            .iter()
            .map(|p| format!("/{}", pointer_part(p)))
            .collect()
    }
    fn fail<E: de::Error>(
        &mut self,
        code: &str,
        message: impl Into<String>,
        actual: impl ToString,
        expected: impl ToString,
    ) -> E {
        let error =
            ExchangeError::new(code, "parse", self.pointer(), message).bounds(actual, expected);
        self.error = Some(error);
        E::custom("bounded JSON admission failed")
    }
    fn node<E: de::Error>(&mut self) -> std::result::Result<(), E> {
        self.stats.nodes += 1;
        if self.stats.nodes > self.limits.nodes {
            return Err(self.fail(
                "limit",
                "JSON node budget exceeded",
                self.stats.nodes,
                self.limits.nodes,
            ));
        }
        Ok(())
    }
    fn string<E: de::Error>(&mut self, s: &str) -> std::result::Result<(), E> {
        if s.len() > self.limits.string_bytes {
            return Err(self.fail(
                "limit",
                "decoded UTF-8 string budget exceeded",
                s.len(),
                self.limits.string_bytes,
            ));
        }
        Ok(())
    }
    fn enter<E: de::Error>(&mut self) -> std::result::Result<(), E> {
        self.depth += 1;
        if self.depth > self.limits.nesting {
            return Err(self.fail(
                "limit",
                "JSON container nesting budget exceeded",
                self.depth,
                self.limits.nesting,
            ));
        }
        self.stats.depth = self.stats.depth.max(self.depth);
        Ok(())
    }
}
struct Seed<'a, 'b> {
    budget: &'a mut Budget<'b>,
    entry: Option<usize>,
}
impl<'de> DeserializeSeed<'de> for Seed<'_, '_> {
    type Value = Value;
    fn deserialize<D: Deserializer<'de>>(self, d: D) -> std::result::Result<Value, D::Error> {
        if let Some(n) = self.entry
            && n >= self.budget.limits.collection
        {
            return Err(self.budget.fail(
                "limit",
                "immediate collection budget exceeded",
                n + 1,
                self.budget.limits.collection,
            ));
        }
        self.budget.node()?;
        d.deserialize_any(DataVisitor(self.budget))
    }
}
struct KeySeed<'a, 'b> {
    budget: &'a mut Budget<'b>,
    entry: usize,
}
impl<'de> DeserializeSeed<'de> for KeySeed<'_, '_> {
    type Value = String;
    fn deserialize<D: Deserializer<'de>>(self, d: D) -> std::result::Result<String, D::Error> {
        if self.entry >= self.budget.limits.collection {
            return Err(self.budget.fail(
                "limit",
                "immediate collection budget exceeded",
                self.entry + 1,
                self.budget.limits.collection,
            ));
        }
        self.budget.node()?;
        let key = String::deserialize(d)?;
        self.budget.string(&key)?;
        Ok(key)
    }
}
struct DataVisitor<'a, 'b>(&'a mut Budget<'b>);
impl<'de> Visitor<'de> for DataVisitor<'_, '_> {
    type Value = Value;
    fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("bounded JSON with i32 integer literals")
    }
    fn visit_unit<E: de::Error>(self) -> std::result::Result<Value, E> {
        Ok(Value::Null)
    }
    fn visit_none<E: de::Error>(self) -> std::result::Result<Value, E> {
        Ok(Value::Null)
    }
    fn visit_bool<E: de::Error>(self, v: bool) -> std::result::Result<Value, E> {
        Ok(Value::Bool(v))
    }
    fn visit_i64<E: de::Error>(self, v: i64) -> std::result::Result<Value, E> {
        if i32::try_from(v).is_err() {
            return Err(self.0.fail(
                "overflow",
                "JSON integer literal exceeds i32 annotation ceiling",
                v,
                "i32",
            ));
        }
        Ok(Value::Integer(v))
    }
    fn visit_u64<E: de::Error>(self, v: u64) -> std::result::Result<Value, E> {
        if v > i32::MAX as u64 {
            return Err(self.0.fail(
                "overflow",
                "JSON integer literal exceeds i32 annotation ceiling",
                v,
                "i32",
            ));
        }
        Ok(Value::Integer(v as i64))
    }
    fn visit_f64<E: de::Error>(self, v: f64) -> std::result::Result<Value, E> {
        Err(self.0.fail(
            "invalid_json",
            "non-admitted or unrepresentable numeric literal (including fraction, exponent or negative zero)",
            v,
            "0|-?[1-9][0-9]* within i32",
        ))
    }
    fn visit_str<E: de::Error>(self, v: &str) -> std::result::Result<Value, E> {
        self.0.string(v)?;
        Ok(Value::String(v.into()))
    }
    fn visit_string<E: de::Error>(self, v: String) -> std::result::Result<Value, E> {
        self.0.string(&v)?;
        Ok(Value::String(v))
    }
    fn visit_seq<A: SeqAccess<'de>>(self, mut a: A) -> std::result::Result<Value, A::Error> {
        self.0.enter()?;
        let mut out = Vec::new();
        loop {
            self.0.path.push(out.len().to_string());
            let value = a.next_element_seed(Seed {
                budget: self.0,
                entry: Some(out.len()),
            })?;
            self.0.path.pop();
            match value {
                Some(v) => out.push(v),
                None => break,
            }
        }
        self.0.depth -= 1;
        Ok(Value::Array(out))
    }
    fn visit_map<A: MapAccess<'de>>(self, mut a: A) -> std::result::Result<Value, A::Error> {
        self.0.enter()?;
        let mut out = Vec::new();
        let mut seen = BTreeSet::new();
        while let Some(key) = a.next_key_seed(KeySeed {
            budget: self.0,
            entry: out.len(),
        })? {
            self.0.path.push(key.clone());
            if !seen.insert(key.clone()) {
                return Err(self.0.fail(
                    "duplicate_key",
                    "duplicate decoded object key",
                    &key,
                    "one occurrence",
                ));
            }
            let value = a.next_value_seed(Seed {
                budget: self.0,
                entry: None,
            })?;
            self.0.path.pop();
            out.push((key, value));
        }
        self.0.depth -= 1;
        Ok(Value::Object(out))
    }
}

pub(crate) fn read_bounded(mut reader: impl Read, maximum: usize) -> Result<Vec<u8>> {
    let limit = u64::try_from(maximum).map_err(|_| {
        ExchangeError::new(
            "invalid_limits",
            "read",
            "",
            "input ceiling does not fit u64",
        )
    })?;
    let mut bytes = Vec::new();
    reader
        .by_ref()
        .take(limit + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| ExchangeError::new("io", "read", "", e.to_string()))?;
    if bytes.len() > maximum {
        return Err(
            ExchangeError::new("limit", "read", "", "actual input byte budget exceeded")
                .bounds(bytes.len(), maximum),
        );
    }
    Ok(bytes)
}
pub(crate) fn parse_bytes(bytes: &[u8], limits: &Limits) -> Result<(Value, JsonStats)> {
    limits.check()?;
    if bytes.len() > limits.input_bytes {
        return Err(
            ExchangeError::new("limit", "read", "", "actual input byte budget exceeded")
                .bounds(bytes.len(), limits.input_bytes),
        );
    }
    std::str::from_utf8(bytes)
        .map_err(|e| ExchangeError::new("invalid_utf8", "parse", "", e.to_string()))?;
    if bytes.starts_with(&[0xef, 0xbb, 0xbf]) {
        return Err(ExchangeError::new(
            "invalid_json",
            "parse",
            "",
            "leading UTF-8 BOM is unsupported",
        ));
    }
    let mut budget = Budget {
        limits,
        stats: JsonStats { nodes: 0, depth: 0 },
        depth: 0,
        path: vec![],
        error: None,
    };
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    let parsed = Seed {
        budget: &mut budget,
        entry: None,
    }
    .deserialize(&mut deserializer);
    let value = parsed.map_err(|e| {
        let mut error = budget.error.take().unwrap_or_else(|| {
            ExchangeError::new("invalid_json", "parse", budget.pointer(), e.to_string())
        });
        error.line = Some(e.line());
        error.column = Some(e.column());
        error
    })?;
    deserializer.end().map_err(|e| {
        let mut error = ExchangeError::new(
            "trailing_document",
            "parse",
            "",
            "trailing data after the single JSON document",
        );
        error.line = Some(e.line());
        error.column = Some(e.column());
        error
    })?;
    Ok((value, budget.stats))
}
/// Pure bounded parser surface; a successful result is not an accepted envelope.
/// Returned objects may be sorted only AFTER duplicate detection. Production
/// schema decoding instead retains the private input-ordered representation.
pub fn parse_json(reader: impl Read, limits: &Limits) -> Result<(serde_json::Value, JsonStats)> {
    limits.check()?;
    let bytes = read_bounded(reader, limits.input_bytes)?;
    let (v, s) = parse_bytes(&bytes, limits)?;
    Ok((v.into_json(), s))
}

/// Preserve schema error tokens as data. User keys can contain any delimiter.
#[derive(Debug)]
pub(crate) struct DecodeError {
    message: String,
    field: Option<String>,
    append_field: bool,
    code: &'static str,
}
impl fmt::Display for DecodeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}
impl std::error::Error for DecodeError {}
impl de::Error for DecodeError {
    fn custom<T: fmt::Display>(message: T) -> Self {
        {
            let message = crate::error::bounded_text(&message.to_string());
            let code = if message.starts_with("[invalid_unsigned] ") {
                "invalid_unsigned"
            } else if message.starts_with("[overflow] ") {
                "overflow"
            } else if message.starts_with("[identity_mismatch] ") {
                "identity_mismatch"
            } else if message.starts_with("[invalid_enum] ") {
                "invalid_enum"
            } else {
                "wrong_type"
            };
            Self {
                message,
                field: None,
                append_field: false,
                code,
            }
        }
    }
    fn unknown_variant(_: &str, _: &'static [&'static str]) -> Self {
        Self {
            message: "unsupported tagged variant".into(),
            field: None,
            append_field: false,
            code: "invalid_enum",
        }
    }
    fn invalid_type(_value: de::Unexpected<'_>, expected: &dyn de::Expected) -> Self {
        Self {
            message: crate::error::bounded_text(&format!("wrong JSON type, expected {expected}")),
            field: None,
            append_field: false,
            code: "wrong_type",
        }
    }
    fn invalid_value(_value: de::Unexpected<'_>, expected: &dyn de::Expected) -> Self {
        Self {
            message: crate::error::bounded_text(&format!("invalid value, expected {expected}")),
            field: None,
            append_field: false,
            code: "wrong_type",
        }
    }
    fn unknown_field(field: &str, _: &'static [&'static str]) -> Self {
        Self {
            message: "unknown closed-schema field".into(),
            field: Some(field.into()),
            append_field: false,
            code: "unknown_field",
        }
    }
    fn missing_field(field: &'static str) -> Self {
        Self {
            message: "missing required schema field".into(),
            field: Some(field.into()),
            append_field: true,
            code: "missing_field",
        }
    }
}

impl<'de> IntoDeserializer<'de, DecodeError> for Value {
    type Deserializer = Self;
    fn into_deserializer(self) -> Self {
        self
    }
}
impl<'de> Deserializer<'de> for Value {
    type Error = DecodeError;
    fn deserialize_any<V: Visitor<'de>>(
        self,
        visitor: V,
    ) -> std::result::Result<V::Value, Self::Error> {
        match self {
            Self::Null => visitor.visit_unit(),
            Self::Bool(v) => visitor.visit_bool(v),
            Self::Integer(v) => visitor.visit_i64(v),
            Self::String(v) => visitor.visit_string(v),
            Self::Array(v) => visitor.visit_seq(de::value::SeqDeserializer::new(v.into_iter())),
            Self::Object(v) => visitor.visit_map(de::value::MapDeserializer::new(v.into_iter())),
        }
    }
    fn deserialize_option<V: Visitor<'de>>(
        self,
        visitor: V,
    ) -> std::result::Result<V::Value, Self::Error> {
        match self {
            Self::Null => visitor.visit_none(),
            other => visitor.visit_some(other),
        }
    }
    fn deserialize_enum<V: Visitor<'de>>(
        self,
        name: &'static str,
        _: &'static [&'static str],
        visitor: V,
    ) -> std::result::Result<V::Value, Self::Error> {
        let tag = match name {
            "ValueDomainInput" | "TerminalInput" => "kind",
            "ToolBindingInput" | "ViewBindingInput" => "state",
            _ => {
                return match self {
                    Self::String(v) => visitor.visit_enum(v.into_deserializer()),
                    other => other.deserialize_any(visitor),
                };
            }
        };
        let Self::Object(mut fields) = self else {
            return Err(de::Error::invalid_type(
                de::Unexpected::Other("non-object"),
                &"tagged object",
            ));
        };
        let Some(index) = fields.iter().position(|(k, _)| k == tag) else {
            return Err(de::Error::missing_field(tag));
        };
        let (_, value) = fields.remove(index);
        let Self::String(variant) = value else {
            return Err(DecodeError {
                message: "tag must be a string".into(),
                field: Some(tag.into()),
                append_field: true,
                code: "wrong_type",
            });
        };
        visitor
            .visit_enum(Tagged {
                variant,
                value: Value::Object(fields),
            })
            .map_err(|mut e: DecodeError| {
                if e.message == "unsupported tagged variant" {
                    e.field = Some(tag.into());
                    e.append_field = true;
                }
                e
            })
    }
    fn deserialize_newtype_struct<V: Visitor<'de>>(
        self,
        _: &'static str,
        visitor: V,
    ) -> std::result::Result<V::Value, Self::Error> {
        visitor.visit_newtype_struct(self)
    }
    serde::forward_to_deserialize_any! {bool i8 i16 i32 i64 u8 u16 u32 u64 f32 f64 char str string bytes byte_buf unit unit_struct seq tuple tuple_struct map struct identifier ignored_any}
}
// Variant payloads remain input-ordered Values. Unlike Serde's internally
// tagged Content buffer this keeps nested error paths and avoids a second tree.
struct Tagged {
    variant: String,
    value: Value,
}
impl<'de> de::EnumAccess<'de> for Tagged {
    type Error = DecodeError;
    type Variant = Value;
    fn variant_seed<S: DeserializeSeed<'de>>(
        self,
        seed: S,
    ) -> std::result::Result<(S::Value, Value), DecodeError> {
        Ok((
            seed.deserialize(self.variant.into_deserializer())?,
            self.value,
        ))
    }
}
impl<'de> de::VariantAccess<'de> for Value {
    type Error = DecodeError;
    fn unit_variant(self) -> std::result::Result<(), DecodeError> {
        match self {
            Value::Object(v) if v.is_empty() => Ok(()),
            Value::Object(v) => {
                let mut error: DecodeError = de::Error::unknown_field(&v[0].0, &[]);
                error.append_field = true;
                Err(error)
            }
            _ => Err(de::Error::custom("expected unit variant object")),
        }
    }
    fn newtype_variant_seed<S: DeserializeSeed<'de>>(
        self,
        seed: S,
    ) -> std::result::Result<S::Value, DecodeError> {
        seed.deserialize(self)
    }
    fn tuple_variant<V: Visitor<'de>>(
        self,
        len: usize,
        visitor: V,
    ) -> std::result::Result<V::Value, DecodeError> {
        self.deserialize_tuple(len, visitor)
    }
    fn struct_variant<V: Visitor<'de>>(
        self,
        fields: &'static [&'static str],
        visitor: V,
    ) -> std::result::Result<V::Value, DecodeError> {
        self.deserialize_struct("variant", fields, visitor)
    }
}
impl<'de> Deserialize<'de> for Value {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        struct V;
        impl<'de> Visitor<'de> for V {
            type Value = Value;
            fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("previously bounded JSON")
            }
            fn visit_unit<E: de::Error>(self) -> std::result::Result<Value, E> {
                Ok(Value::Null)
            }
            fn visit_bool<E: de::Error>(self, v: bool) -> std::result::Result<Value, E> {
                Ok(Value::Bool(v))
            }
            fn visit_i64<E: de::Error>(self, v: i64) -> std::result::Result<Value, E> {
                Ok(Value::Integer(v))
            }
            fn visit_u64<E: de::Error>(self, v: u64) -> std::result::Result<Value, E> {
                i64::try_from(v).map(Value::Integer).map_err(E::custom)
            }
            fn visit_string<E: de::Error>(self, v: String) -> std::result::Result<Value, E> {
                Ok(Value::String(v))
            }
            fn visit_str<E: de::Error>(self, v: &str) -> std::result::Result<Value, E> {
                Ok(Value::String(v.into()))
            }
            fn visit_seq<A: SeqAccess<'de>>(
                self,
                mut a: A,
            ) -> std::result::Result<Value, A::Error> {
                let mut out = vec![];
                while let Some(v) = a.next_element()? {
                    out.push(v)
                }
                Ok(Value::Array(out))
            }
            fn visit_map<A: MapAccess<'de>>(
                self,
                mut a: A,
            ) -> std::result::Result<Value, A::Error> {
                let mut out = vec![];
                while let Some(v) = a.next_entry()? {
                    out.push(v)
                }
                Ok(Value::Object(out))
            }
        }
        d.deserialize_any(V)
    }
}
pub(crate) fn decode<T: serde::de::DeserializeOwned>(value: Value, prefix: &str) -> Result<T> {
    serde_path_to_error::deserialize(value).map_err(|e| {
        let mut path = prefix.to_owned();
        for segment in e.path().iter() {
            match segment {
                serde_path_to_error::Segment::Seq { index } => path.push_str(&format!("/{index}")),
                serde_path_to_error::Segment::Map { key } => {
                    path.push_str(&format!("/{}", pointer_part(key)))
                }
                serde_path_to_error::Segment::Enum { .. } => {}
                serde_path_to_error::Segment::Unknown => {}
            }
        }
        let inner = e.inner();
        let message = inner.to_string();
        let code = inner.code;
        // Normal map keys are already in serde_path_to_error. Missing fields,
        // discriminator failures and unit-variant extra fields explicitly request
        // one additional token; never guess by matching pointer suffix text.
        if let Some(field) = &inner.field {
            let token = format!("/{}", pointer_part(field));
            if inner.append_field {
                path.push_str(&token);
            }
        }
        ExchangeError::new(code, "decode", path, message)
    })
}
