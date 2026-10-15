//! Admission witnesses own immutable, validated state. No resolver is retained.
use crate::{
    Limits, architecture, canonical,
    error::{ExchangeError, Notice, Result, pointer_part},
    parser, wire as w,
};
use std::{collections::BTreeSet, io::Read};

pub struct CheckedArchitecture {
    pub(crate) header: w::Header,
    pub(crate) model: nf_arch_ir::Architecture,
    pub(crate) id: w::Digest,
    pub(crate) raw: w::Digest,
    pub(crate) notices: Vec<Notice>,
    pub(crate) limits: Limits,
}
pub struct CheckedDesign {
    header: w::Header,
    body: w::Design,
    raw: w::Digest,
    notices: Vec<Notice>,
    limits: Limits,
}
pub struct SavedPackage {
    pub(crate) header: w::Header,
    pub(crate) body: w::Package,
    pub(crate) architecture: CheckedArchitecture,
    pub(crate) raw: w::Digest,
    pub(crate) notices: Vec<Notice>,
    pub(crate) limits: Limits,
}
impl CheckedArchitecture {
    pub fn architecture(&self) -> &nf_arch_ir::Architecture {
        &self.model
    }
    pub fn id(&self) -> &w::Digest {
        &self.id
    }
    pub fn raw_digest(&self) -> &w::Digest {
        &self.raw
    }
    pub fn notices(&self) -> &[Notice] {
        &self.notices
    }
    fn output(&self, projection: bool) -> Result<Vec<u8>> {
        let body =
            canonical::architecture(architecture::from_core(&self.model, &self.id), projection)?;
        canonical::bytes(
            &canonical::envelope(&self.header, body, projection)?,
            self.limits.input_bytes,
        )
    }
    pub fn canonical_bytes(&self) -> Result<Vec<u8>> {
        self.output(false)
    }
    pub fn semantic_bytes(&self) -> Result<Vec<u8>> {
        self.output(true)
    }
    pub fn summary(&self) -> serde_json::Value {
        serde_json::json!({"id":self.id,"raw_digest":self.raw,"notices":self.notices,"templates":self.model.templates.len(),"roots":self.model.roots.len(),"connections":self.model.connections.len()})
    }
}
impl CheckedDesign {
    pub fn id(&self) -> &w::Digest {
        &self.body.semantic_id
    }
    pub fn raw_digest(&self) -> &w::Digest {
        &self.raw
    }
    pub fn notices(&self) -> &[Notice] {
        &self.notices
    }
    fn output(&self, projection: bool) -> Result<Vec<u8>> {
        canonical::bytes(
            &canonical::envelope(
                &self.header,
                canonical::design(&self.body, projection)?,
                projection,
            )?,
            self.limits.input_bytes,
        )
    }
    pub fn canonical_bytes(&self) -> Result<Vec<u8>> {
        self.output(false)
    }
    pub fn semantic_bytes(&self) -> Result<Vec<u8>> {
        self.output(true)
    }
    pub fn summary(&self) -> serde_json::Value {
        serde_json::json!({"id":self.body.semantic_id,"raw_digest":self.raw,"notices":self.notices,"cells":self.body.cells.len(),"ports":self.body.ports.len(),"nets":self.body.nets.len()})
    }
}
impl SavedPackage {
    pub fn architecture(&self) -> &CheckedArchitecture {
        &self.architecture
    }
    pub fn id(&self) -> &w::Digest {
        &self.body.build_id
    }
    pub fn raw_digest(&self) -> &w::Digest {
        &self.raw
    }
    pub fn notices(&self) -> &[Notice] {
        &self.notices
    }
    fn output(&self, projection: bool) -> Result<Vec<u8>> {
        canonical::bytes(
            &canonical::envelope(
                &self.header,
                canonical::package(&self.body, projection)?,
                projection,
            )?,
            self.limits.input_bytes,
        )
    }
    pub fn canonical_bytes(&self) -> Result<Vec<u8>> {
        self.output(false)
    }
    pub fn semantic_bytes(&self) -> Result<Vec<u8>> {
        self.output(true)
    }
    pub fn summary(&self) -> serde_json::Value {
        serde_json::json!({"id":self.body.build_id,"raw_digest":self.raw,"notices":self.notices,"architecture":self.architecture.summary()})
    }
}

pub(crate) enum Contract {
    Architecture,
    Package,
    Design,
}
impl Contract {
    fn properties(&self) -> (&'static str, &'static str, &'static str) {
        match self {
            Self::Architecture => (
                "nodal-fpga.arch",
                "structural-selection",
                "nodal-fpga/arch.structural-selection",
            ),
            Self::Package => (
                "nodal-fpga.package-manifest",
                "software-package",
                "nodal-fpga/package.software-inspection",
            ),
            Self::Design => (
                "nodal-fpga.mapped-design",
                "mapped-structural",
                "nodal-fpga/design.structural",
            ),
        }
    }
}
fn capability_id(s: &str) -> bool {
    if s.len() > 128 {
        return false;
    }
    let Some((namespace, local)) = s.split_once('/') else {
        return false;
    };
    fn part(s: &str, underscore: bool) -> bool {
        s.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
            && s.bytes().all(|b| {
                b.is_ascii_lowercase()
                    || b.is_ascii_digit()
                    || b == b'.'
                    || b == b'-'
                    || (underscore && b == b'_')
            })
    }
    part(namespace, false) && part(local, true)
}
pub(crate) fn envelope(
    reader: impl Read,
    limits: &Limits,
    contract: Contract,
) -> Result<(w::Header, parser::Value, w::Digest, Vec<Notice>)> {
    limits.check()?;
    let bytes = parser::read_bounded(reader, limits.input_bytes)?;
    let raw = w::Digest::of_bytes(&bytes);
    let (value, _) = parser::parse_bytes(&bytes, limits)?;
    let e: w::Envelope = parser::decode(value, "")?;
    let h = w::Header {
        format: e.format,
        version: e.version,
        profile: e.profile,
        required_features: e.required_features,
        optional_features: e.optional_features,
        annotations: e.annotations,
    };
    let result = (|| {
        let (format, profile, feature) = contract.properties();
        let mismatch = |code: &str, p: &str, actual: String, expected: &str| {
            ExchangeError::new(code, "envelope", p, "unsupported exchange contract")
                .bounds(actual, expected)
        };
        if h.format != format {
            return Err(mismatch(
                "unsupported_format",
                "/format",
                h.format.clone(),
                format,
            ));
        }
        if h.version.major != 0 {
            return Err(mismatch(
                "unsupported_version",
                "/version/major",
                h.version.major.to_string(),
                "0",
            ));
        }
        if h.version.minor != 1 {
            return Err(mismatch(
                "unsupported_version",
                "/version/minor",
                h.version.minor.to_string(),
                "1",
            ));
        }
        if h.profile.id != profile {
            return Err(mismatch(
                "unsupported_profile",
                "/profile/id",
                h.profile.id.clone(),
                profile,
            ));
        }
        if h.profile.revision != 1 {
            return Err(mismatch(
                "unsupported_profile",
                "/profile/revision",
                h.profile.revision.to_string(),
                "1",
            ));
        }
        // Detect duplicate IDs before examining their revision, so a duplicate
        // cannot evade uniqueness merely by changing the revision.
        for (label, features) in [
            ("required_features", &h.required_features),
            ("optional_features", &h.optional_features),
        ] {
            let mut ids = BTreeSet::new();
            for (i, f) in features.iter().enumerate() {
                let p = format!("/{label}/{i}");
                if !ids.insert(&f.id) {
                    return Err(ExchangeError::new(
                        "duplicate_feature",
                        "envelope",
                        p,
                        "feature ID appears more than once",
                    ));
                }
                if !capability_id(&f.id) {
                    return Err(ExchangeError::new(
                        "invalid_annotation",
                        "envelope",
                        format!("{p}/id"),
                        "invalid namespaced capability ID",
                    ));
                }
            }
        }
        for (i, f) in h.required_features.iter().enumerate() {
            let p = format!("/required_features/{i}");
            if f.id != feature {
                return Err(mismatch(
                    "unsupported_feature",
                    &format!("{p}/id"),
                    f.id.clone(),
                    feature,
                ));
            }
            if f.revision != 1 {
                return Err(mismatch(
                    "unsupported_feature",
                    &format!("{p}/revision"),
                    f.revision.to_string(),
                    "1",
                ));
            }
        }
        if !h.required_features.iter().any(|f| f.id == feature) {
            return Err(ExchangeError::new(
                "missing_feature",
                "envelope",
                "/required_features",
                "required semantic capability is absent",
            ));
        }
        let mut optional = BTreeSet::new();
        let mut notices = vec![];
        for (i, f) in h.optional_features.iter().enumerate() {
            let p = format!("/optional_features/{i}");
            if matches!(
                f.id.as_str(),
                "nodal-fpga/arch.structural-selection"
                    | "nodal-fpga/design.structural"
                    | "nodal-fpga/package.software-inspection"
            ) || h.required_features.iter().any(|r| r.id == f.id)
            {
                return Err(ExchangeError::new(
                    "unsupported_feature",
                    "envelope",
                    p,
                    "semantic capability cannot be declared optional",
                ));
            }
            optional.insert(f.id.as_str());
            notices.push(Notice {
                code: "unknown_annotation".into(),
                pointer: p,
                message: "Unknown optional annotation capability preserved without interpretation."
                    .into(),
            });
        }
        for key in h.annotations.keys() {
            if !capability_id(key) || !optional.contains(key.as_str()) {
                return Err(ExchangeError::new(
                    "invalid_annotation",
                    "envelope",
                    format!("/annotations/{}", pointer_part(key)),
                    "annotation namespace must have an optional capability declaration",
                ));
            }
        }
        Ok(notices)
    })()
    .map_err(|e| e.at_contract(&h.contract()))?;
    Ok((h, e.body, raw, result))
}
pub(crate) fn check_id(declared: &w::Digest, computed: w::Digest, p: &str) -> Result<()> {
    if declared != &computed {
        return Err(ExchangeError::new(
            "identity_mismatch",
            "identity",
            p,
            "declared digest differs from canonical semantic projection",
        )
        .bounds(declared, computed));
    }
    Ok(())
}
pub fn read_architecture(reader: impl Read, limits: &Limits) -> Result<CheckedArchitecture> {
    let (header, body, raw, notices) = envelope(reader, limits, Contract::Architecture)?;
    let contract = header.contract();
    (|| {
        let body: w::Architecture = parser::decode(body, "/body")?;
        let id = body.semantic_id.clone();
        let model = architecture::into_core(body)?;
        nf_arch_ir::validate_architecture(&model, &limits.core)
            .map_err(|e| ExchangeError::core("/body", e))?;
        let result = CheckedArchitecture {
            header,
            model,
            id,
            raw,
            notices,
            limits: *limits,
        };
        check_id(
            result.id(),
            w::Digest::domain(canonical::ARCH_DOMAIN, &result.semantic_bytes()?),
            "/body/semantic_id",
        )?;
        Ok(result)
    })()
    .map_err(|e: ExchangeError| e.at_contract(&contract))
}
pub fn read_design(
    reader: impl Read,
    package: &SavedPackage,
    limits: &Limits,
) -> Result<CheckedDesign> {
    let (header, body, raw, notices) = envelope(reader, limits, Contract::Design)?;
    let contract = header.contract();
    (|| {
        let body: w::Design = parser::decode(body, "/body")?;
        if &body.target_build_id != package.id() {
            return Err(ExchangeError::new(
                "target_build_mismatch",
                "identity",
                "/body/target_build_id",
                "mapped design targets a different exact package build",
            )
            .bounds(&body.target_build_id, package.id()));
        }
        crate::design::validate(&body, package.architecture().architecture(), limits)?;
        let result = CheckedDesign {
            header,
            body,
            raw,
            notices,
            limits: *limits,
        };
        check_id(
            result.id(),
            w::Digest::domain(canonical::DESIGN_DOMAIN, &result.semantic_bytes()?),
            "/body/semantic_id",
        )?;
        Ok(result)
    })()
    .map_err(|e: ExchangeError| e.at_contract(&contract))
}
pub use crate::package::read_package;
