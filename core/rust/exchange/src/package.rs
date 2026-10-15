//! Flat digest admission. Declared lengths are checked before any resolver call.
use crate::{
    Limits, canonical,
    document::{self, Contract, SavedPackage},
    error::{ExchangeError, Result},
    parser, wire as w,
};
use std::{
    collections::{BTreeMap, BTreeSet},
    io::{self, Read},
};

fn text(value: &str, p: &str, maximum: usize, empty: bool) -> Result<()> {
    if (!empty && value.is_empty()) || value.len() > maximum {
        return Err(ExchangeError::new(
            "limit",
            "decode",
            p,
            "binding text is outside the admitted byte range",
        )
        .bounds(value.len(), format!("{}..={maximum}", usize::from(!empty))));
    }
    Ok(())
}
fn reason(value: &str, p: &str) -> Result<()> {
    if !matches!(value, "foundation-unimplemented" | "not-supplied") {
        return Err(ExchangeError::new(
            "invalid_enum",
            "decode",
            p,
            "unsupported explicit unbound reason",
        ));
    }
    Ok(())
}
fn tool(value: &w::ToolBinding, p: &str) -> Result<()> {
    match value {
        w::ToolBinding::Unbound { reason: r } => reason(r, &format!("{p}/reason")),
        w::ToolBinding::Bound {
            id,
            version,
            options,
            ..
        } => {
            text(id, &format!("{p}/id"), 128, false)?;
            text(version, &format!("{p}/version"), 128, false)?;
            let mut seen = BTreeSet::new();
            for (i, o) in options.iter().enumerate() {
                let p = format!("{p}/options/{i}");
                crate::architecture::name(o.name.clone(), &format!("{p}/name"))?;
                text(&o.value, &format!("{p}/value"), 1024, true)?;
                if !seen.insert(&o.name) {
                    return Err(ExchangeError::new(
                        "duplicate",
                        "decode",
                        p,
                        "duplicate option name",
                    ));
                }
            }
            Ok(())
        }
    }
}
/// Manifest accounting: one declaration for each body/binding/library/option/
/// descriptor record; one reference per descriptor or bound implementation ID.
/// Work charges each declaration/reference, text byte+1 and index insertion.
fn budget(value: &w::Package, limits: &Limits) -> Result<()> {
    struct B<'a> {
        limits: &'a Limits,
        declarations: u64,
        references: u64,
        work: u64,
    }
    impl B<'_> {
        fn charge(&mut self, d: u64, r: u64, w: u64) -> Result<()> {
            self.declarations = self.declarations.checked_add(d).ok_or_else(|| {
                ExchangeError::new(
                    "limit",
                    "semantic",
                    "/body",
                    "manifest declaration counter overflow",
                )
            })?;
            self.references = self.references.checked_add(r).ok_or_else(|| {
                ExchangeError::new(
                    "limit",
                    "semantic",
                    "/body",
                    "manifest reference counter overflow",
                )
            })?;
            self.work = self.work.checked_add(w + d + r).ok_or_else(|| {
                ExchangeError::new(
                    "limit",
                    "semantic",
                    "/body",
                    "manifest work counter overflow",
                )
            })?;
            for (label, n, max) in [
                (
                    "declarations",
                    self.declarations,
                    self.limits.core.max_declarations,
                ),
                (
                    "references",
                    self.references,
                    self.limits.core.max_references,
                ),
                ("work", self.work, self.limits.core.max_work),
            ] {
                if n > max {
                    return Err(ExchangeError::new(
                        "limit",
                        "semantic",
                        "/body",
                        format!("manifest {label} budget exceeded"),
                    )
                    .bounds(n, max));
                }
            }
            Ok(())
        }
        fn text(&mut self, s: &str) -> Result<()> {
            self.charge(0, 0, s.len() as u64 + 1)
        }
        fn collection(&self, n: usize) -> Result<()> {
            if n > self.limits.core.max_collection {
                return Err(ExchangeError::new(
                    "limit",
                    "semantic",
                    "/body",
                    "manifest collection budget exceeded",
                )
                .bounds(n, self.limits.core.max_collection));
            }
            Ok(())
        }
        fn artifact(&mut self) -> Result<()> {
            self.charge(1, 1, 1)
        }
    }
    let mut b = B {
        limits,
        declarations: 0,
        references: 0,
        work: 0,
    };
    b.charge(2, 1, 0)?;
    b.artifact()?;
    b.collection(value.libraries.len())?;
    for l in &value.libraries {
        b.charge(1, 0, 1)?;
        b.text(&l.id)?;
        b.text(&l.revision)?;
        b.artifact()?;
    }
    for t in [&value.authoring, &value.compiler, &value.backend] {
        b.charge(1, 0, 0)?;
        match t {
            w::ToolBinding::Bound {
                id,
                version,
                options,
                ..
            } => {
                b.charge(0, 1, 0)?;
                b.text(id)?;
                b.text(version)?;
                b.collection(options.len())?;
                for o in options {
                    b.charge(1, 0, 1)?;
                    b.text(&o.name)?;
                    b.text(&o.value)?;
                    if o.name.len() > limits.core.max_key_component_bytes {
                        return Err(ExchangeError::new(
                            "limit",
                            "semantic",
                            "/body",
                            "tool option name exceeds lowered name budget",
                        )
                        .bounds(o.name.len(), limits.core.max_key_component_bytes));
                    }
                }
            }
            w::ToolBinding::Unbound { reason } => b.text(reason)?,
        }
    }
    for (_, v) in value.views() {
        b.charge(1, 0, 0)?;
        match v {
            w::ViewBinding::Bound { revision, .. } => {
                b.text(revision)?;
                b.artifact()?;
            }
            w::ViewBinding::Unbound { reason } | w::ViewBinding::Absent { reason } => {
                b.text(reason)?
            }
        }
    }
    Ok(())
}
struct Admitted {
    length: u64,
    pointer: String,
}
fn preflight(value: &w::Package, limits: &Limits) -> Result<BTreeMap<w::Digest, Admitted>> {
    budget(value, limits)?;
    for (label, t) in [
        ("authoring", &value.authoring),
        ("compiler", &value.compiler),
        ("backend", &value.backend),
    ] {
        tool(t, &format!("/body/{label}"))?;
    }
    let mut libraries = BTreeSet::new();
    for (i, l) in value.libraries.iter().enumerate() {
        let p = format!("/body/libraries/{i}");
        text(&l.id, &format!("{p}/id"), 128, false)?;
        text(&l.revision, &format!("{p}/revision"), 128, false)?;
        if !libraries.insert(&l.id) {
            return Err(ExchangeError::new(
                "duplicate",
                "decode",
                p,
                "duplicate library ID",
            ));
        }
    }
    let mut descriptors = vec![(
        &value.architecture.artifact,
        "/body/architecture/artifact".to_owned(),
    )];
    descriptors.extend(
        value
            .libraries
            .iter()
            .enumerate()
            .map(|(i, l)| (&l.artifact, format!("/body/libraries/{i}/artifact"))),
    );
    for (label, v) in value.views() {
        let p = format!("/body/{label}");
        match v {
            w::ViewBinding::Bound { revision, artifact } => {
                text(revision, &format!("{p}/revision"), 128, false)?;
                descriptors.push((artifact, format!("{p}/artifact")));
            }
            w::ViewBinding::Unbound { reason: r } => reason(r, &format!("{p}/reason"))?,
            w::ViewBinding::Absent { reason } => {
                if label != "macro_bindings" || reason != "no-hard-macros" {
                    return Err(ExchangeError::new(
                        "invalid_enum",
                        "decode",
                        format!("{p}/reason"),
                        "only macro_bindings can be absent with no-hard-macros",
                    ));
                }
            }
        }
    }
    let mut admitted: BTreeMap<w::Digest, Admitted> = BTreeMap::new();
    let mut total = 0u64;
    for (a, p) in descriptors {
        if let Some(previous) = admitted.get(&a.sha256) {
            if previous.length != a.bytes.0 {
                return Err(ExchangeError::new(
                    "artifact_length",
                    "artifact",
                    format!("{p}/bytes"),
                    "same digest has conflicting declared lengths",
                )
                .bounds(a.bytes.0, previous.length));
            }
            continue;
        }
        if admitted.len() >= limits.artifacts {
            return Err(ExchangeError::new(
                "limit",
                "artifact",
                p,
                "unique artifact count exceeds capability",
            )
            .bounds(admitted.len() + 1, limits.artifacts));
        }
        if a.bytes.0 > limits.input_bytes as u64 {
            return Err(ExchangeError::new(
                "limit",
                "artifact",
                format!("{p}/bytes"),
                "declared artifact length exceeds per-artifact capability",
            )
            .bounds(a.bytes.0, limits.input_bytes));
        }
        total = total.checked_add(a.bytes.0).ok_or_else(|| {
            ExchangeError::new(
                "limit",
                "artifact",
                format!("{p}/bytes"),
                "aggregate declared length overflow",
            )
        })?;
        if total > limits.artifact_bytes {
            return Err(ExchangeError::new(
                "limit",
                "artifact",
                format!("{p}/bytes"),
                "aggregate declared artifact length exceeds capability",
            )
            .bounds(total, limits.artifact_bytes));
        }
        admitted.insert(
            a.sha256.clone(),
            Admitted {
                length: a.bytes.0,
                pointer: p,
            },
        );
    }
    Ok(admitted)
}
/// Resolve each unique digest once, under an actual-read bound. Only the
/// architecture role is parsed; opaque leaves are verified and then discarded.
/// The immutable result is sufficient for every supported operation and never
/// retains or reopens caller backing files.
pub fn read_package(
    reader: impl Read,
    resolver: &mut impl FnMut(&w::Digest) -> io::Result<Box<dyn Read>>,
    limits: &Limits,
) -> Result<SavedPackage> {
    let (header, body, raw, notices) = document::envelope(reader, limits, Contract::Package)?;
    let contract = header.contract();
    (|| {
        let body: w::Package = parser::decode(body, "/body")?;
        let admitted = preflight(&body, limits)?;
        let projection = canonical::bytes(
            &canonical::envelope(&header, canonical::package(&body, true)?, true)?,
            limits.input_bytes,
        )?;
        document::check_id(
            &body.build_id,
            w::Digest::domain(canonical::PACKAGE_DOMAIN, &projection),
            "/body/build_id",
        )?;
        let mut actual_total = 0u64;
        let mut architecture_bytes = None;
        for (digest, descriptor) in admitted {
            let mut source = resolver(&digest).map_err(|e| {
                ExchangeError::new(
                    if e.kind() == io::ErrorKind::NotFound {
                        "artifact_missing"
                    } else {
                        "io"
                    },
                    "artifact",
                    &descriptor.pointer,
                    e.to_string(),
                )
            })?;
            let ceiling = descriptor
                .length
                .min(limits.input_bytes as u64)
                .min(limits.artifact_bytes.saturating_sub(actual_total));
            let mut bytes = Vec::new();
            source
                .by_ref()
                .take(ceiling + 1)
                .read_to_end(&mut bytes)
                .map_err(|e| {
                    ExchangeError::new("io", "artifact", &descriptor.pointer, e.to_string())
                })?;
            actual_total = actual_total
                .checked_add(bytes.len() as u64)
                .ok_or_else(|| {
                    ExchangeError::new(
                        "limit",
                        "artifact",
                        &descriptor.pointer,
                        "actual aggregate byte counter overflow",
                    )
                })?;
            if bytes.len() as u64 != descriptor.length {
                return Err(ExchangeError::new(
                    "artifact_length",
                    "artifact",
                    format!("{}/bytes", descriptor.pointer),
                    "actual artifact length differs from declared length",
                )
                .bounds(bytes.len(), descriptor.length));
            }
            if actual_total > limits.artifact_bytes {
                return Err(ExchangeError::new(
                    "limit",
                    "artifact",
                    &descriptor.pointer,
                    "actual aggregate artifact byte ceiling exceeded",
                )
                .bounds(actual_total, limits.artifact_bytes));
            }
            let actual = w::Digest::of_bytes(&bytes);
            if actual != digest {
                return Err(ExchangeError::new(
                    "artifact_digest",
                    "artifact",
                    format!("{}/sha256", descriptor.pointer),
                    "artifact raw digest mismatch",
                )
                .bounds(actual, &digest));
            }
            if digest == body.architecture.artifact.sha256 {
                architecture_bytes = Some(bytes);
            }
        }
        let bytes = architecture_bytes.ok_or_else(|| {
            ExchangeError::new(
                "artifact_missing",
                "artifact",
                "/body/architecture/artifact",
                "admitted architecture artifact missing",
            )
        })?;
        let architecture = document::read_architecture(bytes.as_slice(), limits)?;
        if architecture.id() != &body.architecture.semantic_id {
            return Err(ExchangeError::new(
                "identity_mismatch",
                "identity",
                "/body/architecture/semantic_id",
                "verified architecture semantic ID differs from package binding",
            )
            .bounds(architecture.id(), &body.architecture.semantic_id));
        }
        Ok(SavedPackage {
            header,
            body,
            architecture,
            raw,
            notices,
            limits: *limits,
        })
    })()
    .map_err(|e: ExchangeError| e.at_contract(&contract))
}
