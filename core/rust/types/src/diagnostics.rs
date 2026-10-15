use std::cmp::Ordering;
use std::fmt;
use std::ops::{Deref, DerefMut};

use crate::{ByteLength, ByteOffset, ByteRange, SemanticKey};

/// Maximum UTF-8 byte length of a source identifier or display annotation.
pub const MAX_PROVENANCE_BYTES: usize = 1024;

/// Stable categories. Their string spelling, rather than enum discriminants,
/// is the public diagnostic identifier.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum Code {
    Limit,
    InvalidName,
    Overflow,
    InvalidRange,
    Bounds,
    Width,
    BuildMismatch,
    PartitionMismatch,
    WrongKind,
    WrongScope,
    Duplicate,
    Missing,
    Correspondence,
    Direction,
    TemplateCycle,
    AliasCycle,
    AliasChain,
    AliasMismatch,
    Overlap,
    Guard,
    Mode,
    Domain,
    Value,
    Conflict,
    Inactive,
    MissingSelection,
    Connection,
}

impl Code {
    /// Stable, language-neutral spelling; this does not define a wire envelope.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Limit => "limit",
            Self::InvalidName => "invalid_name",
            Self::Overflow => "overflow",
            Self::InvalidRange => "invalid_range",
            Self::Bounds => "bounds",
            Self::Width => "width",
            Self::BuildMismatch => "build_mismatch",
            Self::PartitionMismatch => "partition_mismatch",
            Self::WrongKind => "wrong_kind",
            Self::WrongScope => "wrong_scope",
            Self::Duplicate => "duplicate",
            Self::Missing => "missing",
            Self::Correspondence => "correspondence",
            Self::Direction => "direction",
            Self::TemplateCycle => "template_cycle",
            Self::AliasCycle => "alias_cycle",
            Self::AliasChain => "alias_chain",
            Self::AliasMismatch => "alias_mismatch",
            Self::Overlap => "overlap",
            Self::Guard => "guard",
            Self::Mode => "mode",
            Self::Domain => "domain",
            Self::Value => "value",
            Self::Conflict => "conflict",
            Self::Inactive => "inactive",
            Self::MissingSelection => "missing_selection",
            Self::Connection => "connection",
        }
    }
}

/// Operation that rejected an input.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum Stage {
    Types,
    Identity,
    Architecture,
    Selection,
}

impl Stage {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Types => "types",
            Self::Identity => "identity",
            Self::Architecture => "architecture",
            Self::Selection => "selection",
        }
    }
}

/// A half-open byte span in a declared UTF-8 source.
///
/// This retains a source identifier and declared byte length, not source text.
/// It verifies numeric bounds but cannot verify code-point boundaries or that
/// the declared length matches an external file. A reader with source bytes
/// must verify those properties itself before slicing text.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct SourceSpan {
    source: String,
    source_bytes: ByteLength,
    range: ByteRange,
}

impl SourceSpan {
    pub fn new(
        source: impl Into<String>,
        source_bytes: ByteLength,
        start: ByteOffset,
        end: ByteOffset,
    ) -> Result<Self, Diagnostic> {
        let source = source.into();
        check_provenance_text(&source)?;
        let range = ByteRange::from_bounds(start, end)?;
        if end.get() > source_bytes.get() {
            return Err(
                type_error(Code::Bounds, "source span exceeds declared source bytes")
                    .with_actual(end.get().to_string())
                    .with_expected(format!("end <= {}", source_bytes.get()))
                    .with_remedy("Use byte positions within the declared source length."),
            );
        }
        Ok(Self {
            source,
            source_bytes,
            range,
        })
    }

    pub fn source(&self) -> &str {
        &self.source
    }
    pub const fn source_bytes(&self) -> ByteLength {
        self.source_bytes
    }
    pub const fn range(&self) -> ByteRange {
        self.range
    }
    pub const fn start(&self) -> ByteOffset {
        self.range.start()
    }
    pub const fn end(&self) -> ByteOffset {
        self.range.end()
    }
}

/// Cold, nonsemantic origin metadata; never part of a portable key's identity.
#[derive(Clone, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Provenance {
    span: Option<SourceSpan>,
    display: Option<String>,
}

impl Provenance {
    pub fn new(span: Option<SourceSpan>, display: Option<String>) -> Result<Self, Diagnostic> {
        if let Some(text) = &display {
            check_provenance_text(text)?;
        }
        Ok(Self { span, display })
    }

    pub fn span(&self) -> Option<&SourceSpan> {
        self.span.as_ref()
    }
    pub fn display(&self) -> Option<&str> {
        self.display.as_deref()
    }
}

fn check_provenance_text(text: &str) -> Result<(), Diagnostic> {
    if text.len() > MAX_PROVENANCE_BYTES {
        Err(type_error(
            Code::Limit,
            "provenance text exceeds the supported byte limit",
        )
        .with_actual(text.len().to_string())
        .with_expected(MAX_PROVENANCE_BYTES.to_string())
        .with_remedy("Shorten the nonsemantic source identifier or display annotation."))
    } else {
        Ok(())
    }
}

/// A related semantic resource and its original source metadata.
#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Related {
    pub key: Option<SemanticKey>,
    pub provenance: Provenance,
}

/// Inspectable diagnostic payload. Use [`Diagnostic::new`] to construct it.
///
/// Public fields are presentation data, not trusted architecture declarations.
/// Its native layout and the outer box are private implementation choices with
/// no serialized or native ABI meaning.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiagnosticData {
    pub code: Code,
    pub stage: Stage,
    pub message: String,
    pub primary: Provenance,
    pub key: Option<SemanticKey>,
    pub related: Vec<Related>,
    pub actual: Option<String>,
    pub expected: Option<String>,
    pub remedy: String,
}

/// A structured, source-aware rejection. The boxed payload keeps successful
/// checked operations small; ordinary field access works through `Deref`.
///
/// Ordering is stage, semantic key, stable code spelling, message, primary
/// provenance, related entries, actual, expected, and remedy. The final fields
/// are explicit deterministic tie-breakers. Builders sort related entries;
/// callers directly changing `related` must sort it before publishing results.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Diagnostic(Box<DiagnosticData>);

/// A validator's ordered diagnostic collection.
pub type Diagnostics = Vec<Diagnostic>;

impl Diagnostic {
    pub fn new(code: Code, stage: Stage, message: impl Into<String>, primary: Provenance) -> Self {
        Self(Box::new(DiagnosticData {
            code,
            stage,
            message: message.into(),
            primary,
            key: None,
            related: Vec::new(),
            actual: None,
            expected: None,
            remedy: "Correct the declaration to satisfy the reported constraint.".into(),
        }))
    }

    pub fn with_key(mut self, key: SemanticKey) -> Self {
        self.key = Some(key);
        self
    }
    pub fn with_related(mut self, provenance: Provenance, key: Option<SemanticKey>) -> Self {
        self.related.push(Related { key, provenance });
        self.related.sort();
        self
    }
    pub fn with_actual(mut self, actual: impl Into<String>) -> Self {
        self.actual = Some(actual.into());
        self
    }
    pub fn with_expected(mut self, expected: impl Into<String>) -> Self {
        self.expected = Some(expected.into());
        self
    }
    pub fn with_remedy(mut self, remedy: impl Into<String>) -> Self {
        self.remedy = remedy.into();
        self
    }
}

impl Deref for Diagnostic {
    type Target = DiagnosticData;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
impl DerefMut for Diagnostic {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}
impl Ord for Diagnostic {
    fn cmp(&self, other: &Self) -> Ordering {
        self.stage
            .cmp(&other.stage)
            .then_with(|| self.key.cmp(&other.key))
            .then_with(|| self.code.as_str().cmp(other.code.as_str()))
            .then_with(|| self.message.cmp(&other.message))
            .then_with(|| self.primary.cmp(&other.primary))
            .then_with(|| self.related.cmp(&other.related))
            .then_with(|| self.actual.cmp(&other.actual))
            .then_with(|| self.expected.cmp(&other.expected))
            .then_with(|| self.remedy.cmp(&other.remedy))
    }
}
impl PartialOrd for Diagnostic {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
impl fmt::Display for Diagnostic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}:{}: {}",
            self.stage.as_str(),
            self.code.as_str(),
            self.message
        )
    }
}
impl std::error::Error for Diagnostic {}

pub(crate) fn type_error(code: Code, message: impl Into<String>) -> Diagnostic {
    Diagnostic::new(code, Stage::Types, message, Provenance::default())
}

pub(crate) fn identity_error(code: Code, message: impl Into<String>) -> Diagnostic {
    Diagnostic::new(code, Stage::Identity, message, Provenance::default())
}
