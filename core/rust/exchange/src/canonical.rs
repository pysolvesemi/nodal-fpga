//! Versioned schema-aware normalization. Never filter arbitrary field names.
use crate::{
    error::{ExchangeError, Result},
    wire as w,
};
use serde_json::Value;

pub(crate) const ARCH_DOMAIN: &[u8] = b"nodal-fpga.arch.semantic.v1\n";
pub(crate) const DESIGN_DOMAIN: &[u8] = b"nodal-fpga.design.semantic.v1\n";
pub(crate) const PACKAGE_DOMAIN: &[u8] = b"nodal-fpga.package.build.v1\n";
fn domains(v: &mut [w::Domain]) {
    v.sort_by(|a, b| a.key.cmp_key(&b.key).then(a.kind.cmp(&b.kind)));
}
fn instance(v: &mut w::Instance) {
    domains(&mut v.domains)
}
pub(crate) fn architecture(mut v: w::Architecture, projection: bool) -> Result<Value> {
    v.resource_types.sort_by(|a, b| a.key.cmp_key(&b.key));
    for t in &mut v.resource_types {
        t.modes.sort();
    }
    v.templates.sort_by(|a, b| a.key.cmp_key(&b.key));
    v.roots.sort_by(|a, b| a.name.cmp(&b.name));
    for i in &mut v.roots {
        instance(i)
    }
    v.partitions.sort();
    domains(&mut v.domains);
    v.connections.sort_by(|a, b| a.name.cmp(&b.name));
    for t in &mut v.templates {
        t.resources.sort_by(|a, b| a.name.cmp(&b.name));
        for r in &mut t.resources {
            domains(&mut r.domains)
        }
        t.children.sort_by(|a, b| a.name.cmp(&b.name));
        for i in &mut t.children {
            instance(i)
        }
        t.mode_groups.sort_by(|a, b| a.name.cmp(&b.name));
        for g in &mut t.mode_groups {
            g.resources.sort_by(w::ResourceRef::cmp_ref);
            g.modes.sort();
        }
        t.storage.sort_by(|a, b| a.name.cmp(&b.name));
        t.features.sort_by(|a, b| a.name.cmp(&b.name));
        for f in &mut t.features {
            f.guard.sort_by(|a, b| a.group.cmp(&b.group));
            if let w::ValueDomain::Set { values } = &mut f.domain {
                values.sort();
            }
        }
        t.connections.sort_by(|a, b| a.name.cmp(&b.name));
    }
    let mut value = to_value(v)?;
    if projection {
        remove(&mut value, "semantic_id");
        strip_arch(&mut value);
    }
    Ok(value)
}
pub(crate) fn design(v: &w::Design, projection: bool) -> Result<Value> {
    let mut v = v.clone();
    v.cells.sort_by(|a, b| a.name.cmp(&b.name));
    v.ports.sort_by(|a, b| a.name.cmp(&b.name));
    v.nets.sort_by(|a, b| a.name.cmp(&b.name));
    for n in &mut v.nets {
        n.loads.sort_by(|a, b| a.sort_key().cmp(&b.sort_key()));
    }
    let mut value = to_value(v)?;
    if projection {
        remove(&mut value, "semantic_id");
        cold(&mut value);
        each(&mut value, "cells", cold);
        each(&mut value, "ports", cold);
        each(&mut value, "nets", |v| {
            cold(v);
            child(v, "driver", cold);
            each(v, "loads", cold)
        });
    }
    Ok(value)
}
pub(crate) fn package(v: &w::Package, projection: bool) -> Result<Value> {
    let mut v = v.clone();
    v.libraries.sort_by(|a, b| a.id.cmp(&b.id));
    for t in [&mut v.authoring, &mut v.compiler, &mut v.backend] {
        if let w::ToolBinding::Bound { options, .. } = t {
            options.sort_by(|a, b| a.name.cmp(&b.name));
        }
    }
    let mut value = to_value(v)?;
    if projection {
        remove(&mut value, "build_id");
    }
    Ok(value)
}
fn to_value(value: impl serde::Serialize) -> Result<Value> {
    serde_json::to_value(value).map_err(|e| {
        ExchangeError::new(
            "wrong_type",
            "operation",
            "",
            format!("canonical serialization failed: {e}"),
        )
    })
}
pub(crate) fn envelope(header: &w::Header, body: Value, projection: bool) -> Result<Value> {
    let mut h = header.clone();
    h.required_features.sort_by(|a, b| a.id.cmp(&b.id));
    h.optional_features.sort_by(|a, b| a.id.cmp(&b.id));
    let mut value = to_value(h)?;
    let object = value.as_object_mut().ok_or_else(|| {
        ExchangeError::new(
            "wrong_type",
            "operation",
            "",
            "internal header was not an object",
        )
    })?;
    object.insert("body".into(), body);
    if projection {
        object.remove("annotations");
        object.remove("optional_features");
    }
    Ok(value)
}
/// serde_json's ordered map comparator is Rust str's unsigned UTF-8 order. The
/// pinned serializer uses exactly the documented control escapes and no LF.
pub(crate) fn bytes(value: &Value, limit: usize) -> Result<Vec<u8>> {
    struct Sink {
        data: Vec<u8>,
        maximum: usize,
    }
    impl std::io::Write for Sink {
        fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
            if buf.len() > self.maximum.saturating_sub(self.data.len()) {
                return Err(std::io::Error::other("canonical byte ceiling exceeded"));
            }
            self.data.extend_from_slice(buf);
            Ok(buf.len())
        }
        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }
    let mut sink = Sink {
        data: vec![],
        maximum: limit,
    };
    serde_json::to_writer(&mut sink, value).map_err(|e| {
        ExchangeError::new("limit", "operation", "", e.to_string())
            .bounds("canonical output exceeded", limit)
    })?;
    Ok(sink.data)
}
fn remove(v: &mut Value, k: &str) {
    if let Some(o) = v.as_object_mut() {
        o.remove(k);
    }
}
fn cold(v: &mut Value) {
    remove(v, "provenance")
}
fn each(v: &mut Value, k: &str, f: fn(&mut Value)) {
    if let Some(values) = v.get_mut(k).and_then(Value::as_array_mut) {
        for value in values {
            f(value)
        }
    }
}
fn child(v: &mut Value, k: &str, f: fn(&mut Value)) {
    if let Some(v) = v.get_mut(k)
        && !v.is_null()
    {
        f(v)
    }
}
fn strip_instance(v: &mut Value) {
    cold(v);
    each(v, "domains", cold)
}
fn strip_resource(v: &mut Value) {
    cold(v);
    child(v, "alias_of", cold);
    each(v, "domains", cold)
}
fn strip_endpoint(v: &mut Value) {
    cold(v);
    child(v, "resource", cold)
}
fn strip_connection(v: &mut Value) {
    cold(v);
    each(v, "sources", strip_endpoint);
    child(v, "destination", strip_endpoint);
    child(v, "selector", cold)
}
fn strip_group(v: &mut Value) {
    cold(v);
    each(v, "resources", cold)
}
fn strip_storage(v: &mut Value) {
    cold(v);
    child(v, "owner", cold)
}
fn strip_feature(v: &mut Value) {
    cold(v);
    child(v, "owner", cold);
    child(v, "alias_of", cold);
    each(v, "guard", cold)
}
fn strip_template(v: &mut Value) {
    cold(v);
    each(v, "resources", strip_resource);
    each(v, "children", strip_instance);
    each(v, "mode_groups", strip_group);
    each(v, "storage", strip_storage);
    each(v, "features", strip_feature);
    each(v, "connections", strip_connection)
}
fn strip_type(v: &mut Value) {
    cold(v);
    each(v, "pins", cold)
}
fn strip_arch(v: &mut Value) {
    cold(v);
    each(v, "resource_types", strip_type);
    each(v, "templates", strip_template);
    each(v, "roots", strip_instance);
    each(v, "domains", cold);
    each(v, "connections", strip_connection)
}
