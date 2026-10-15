use serde::Serialize;
use std::{
    fmt,
    ops::{Deref, DerefMut},
};

/// Structured failures are data; none represent a partially accepted document.
#[derive(Clone, Debug, Serialize)]
pub struct ExchangeError(Box<ExchangeErrorData>);

/// Diagnostic data retained behind one small error handle, like nf_types::Diagnostic.
#[derive(Clone, Debug, Serialize)]
pub struct ExchangeErrorData {
    pub code: String,
    pub stage: String,
    pub pointer: String,
    pub message: String,
    pub actual: Option<String>,
    pub expected: Option<String>,
    pub remedy: String,
    pub contract: Option<String>,
    pub line: Option<usize>,
    pub column: Option<usize>,
    #[serde(serialize_with = "serialize_core")]
    pub core: Vec<nf_types::Diagnostic>,
}
impl ExchangeError {
    pub fn new(
        code: &str,
        stage: &str,
        pointer: impl Into<String>,
        message: impl Into<String>,
    ) -> Self {
        Self(Box::new(ExchangeErrorData { code: code.into(), stage: stage.into(), pointer: pointer.into(), message: bounded_text(&message.into()), actual: None, expected: None, remedy: "Correct the named input under the declared supported contract; no partial result is valid.".into(), contract: None, line: None, column: None, core: vec![] }))
    }
    pub(crate) fn bounds(mut self, actual: impl ToString, expected: impl ToString) -> Self {
        self.actual = Some(bounded_text(&actual.to_string()));
        self.expected = Some(bounded_text(&expected.to_string()));
        self
    }
    pub(crate) fn at_contract(mut self, contract: &str) -> Self {
        self.contract = Some(bounded_text(contract));
        self
    }
    pub(crate) fn core(pointer: &str, diagnostics: Vec<nf_types::Diagnostic>) -> Self {
        let mut e = Self::new(
            "semantic",
            "semantic",
            pointer,
            "public FND-04 validation rejected the declaration",
        );
        if let Some(d) = diagnostics.first() {
            e.message = bounded_text(&d.to_string());
            e.actual = d.actual.clone();
            e.expected = d.expected.clone();
            e.remedy = d.remedy.clone();
        }
        e.core = diagnostics;
        e
    }
}
impl Deref for ExchangeError {
    type Target = ExchangeErrorData;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
impl DerefMut for ExchangeError {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}
impl fmt::Display for ExchangeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}:{} at {}: {}",
            self.stage,
            self.code,
            bounded_text(&self.pointer),
            self.message
        )
    }
}
impl std::error::Error for ExchangeError {}
#[derive(Clone, Debug, Serialize)]
pub struct Notice {
    pub code: String,
    pub pointer: String,
    pub message: String,
}
pub(crate) fn pointer_part(s: &str) -> String {
    s.replace('~', "~0").replace('/', "~1")
}
pub(crate) type Result<T> = std::result::Result<T, ExchangeError>;

fn serialize_core<S: serde::Serializer>(
    diagnostics: &[nf_types::Diagnostic],
    serializer: S,
) -> std::result::Result<S::Ok, S::Error> {
    fn provenance(p: &nf_types::Provenance) -> serde_json::Value {
        serde_json::json!({"display":p.display(),"span":p.span().map(|s|serde_json::json!({"source":s.source(),"source_bytes":s.source_bytes().get().to_string(),"start":s.start().get().to_string(),"end":s.end().get().to_string()}))})
    }
    fn key(k: &nf_types::SemanticKey) -> serde_json::Value {
        serde_json::json!({"kind":crate::architecture::kind_name(k.kind()),"namespace":k.namespace().as_str(),"scope":k.scope().iter().map(|s|s.as_str()).collect::<Vec<_>>(),"local":k.local().as_str()})
    }
    diagnostics.iter().map(|d|serde_json::json!({"code":d.code.as_str(),"stage":d.stage.as_str(),"message":d.message,"primary":provenance(&d.primary),"key":d.key.as_ref().map(key),"related":d.related.iter().map(|r|serde_json::json!({"key":r.key.as_ref().map(key),"provenance":provenance(&r.provenance)})).collect::<Vec<_>>(),"actual":d.actual,"expected":d.expected,"remedy":d.remedy})).collect::<Vec<_>>().serialize(serializer)
}

/// Human presentation is capped independently of the exact RFC6901 pointer.
/// The pointer remains structured and exact (at most twice input bytes plus
/// bounded depth); it is never interpolated into a parser error copy.
pub(crate) fn bounded_text(value: &str) -> String {
    const MAX: usize = 1024;
    if value.len() <= MAX {
        return value.into();
    }
    let mut end = MAX - 3;
    while !value.is_char_boundary(end) {
        end -= 1;
    }
    format!("{}...", &value[..end])
}
