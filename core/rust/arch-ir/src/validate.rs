use crate::*;
use nf_types::{Code, Diagnostic, Diagnostics, SemanticKey, Stage};
use std::collections::{BTreeMap, BTreeSet};

/// Caller capabilities may be lowered, never raised beyond these safe ceilings.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ValidationLimits {
    pub max_declarations: u64,
    pub max_references: u64,
    pub max_collection: usize,
    pub max_depth: usize,
    pub max_key_component_bytes: usize,
    pub max_key_bytes: usize,
    pub max_provenance_bytes: usize,
    pub max_diagnostics: usize,
    pub max_work: u64,
}
impl Default for ValidationLimits {
    fn default() -> Self {
        Self {
            max_declarations: 100_000,
            max_references: 200_000,
            max_collection: 16_384,
            max_depth: 64,
            max_key_component_bytes: 128,
            max_key_bytes: 4096,
            max_provenance_bytes: 1024,
            max_diagnostics: 128,
            max_work: 1_000_000,
        }
    }
}
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ValidationStats {
    pub declarations: u64,
    pub references: u64,
    pub work: u64,
    pub hierarchy_depth: usize,
}
/// Immutable validation witness: the input cannot be mutated while this borrow lives.
#[derive(Debug)]
pub struct ValidatedArchitecture<'a> {
    architecture: &'a Architecture,
    limits: ValidationLimits,
    stats: ValidationStats,
}
impl<'a> ValidatedArchitecture<'a> {
    pub fn architecture(&self) -> &'a Architecture {
        self.architecture
    }
    pub fn stats(&self) -> ValidationStats {
        self.stats
    }
    pub fn limits(&self) -> ValidationLimits {
        self.limits
    }
}

type Checked<T> = Result<T, Diagnostic>;
type TemplateKey = Key<TemplateKind>;
type TypeKey = Key<ResourceTypeKind>;
type DomainKey = Key<DomainKind>;

fn diagnostic(
    code: Code,
    stage: Stage,
    message: impl Into<String>,
    provenance: &Provenance,
) -> Diagnostic {
    Diagnostic::new(code, stage, message, provenance.clone())
        .with_remedy("Correct the named declaration or use the documented supported profile.")
}
fn limit(stage: Stage, name: &str, maximum: impl ToString) -> Diagnostic {
    // Deliberately independent of input order or the offending declaration.
    Diagnostic::new(Code::Limit, stage, format!("validation capability exceeded: {name}"), Provenance::default())
        .with_actual("exceeded").with_expected(maximum.to_string())
        .with_remedy("Reduce the input or select a separately reviewed implementation profile; no partial result is valid.")
}
mod bounds;
mod connections;
mod declarations;
mod references;
mod selection;

use bounds::*;
use connections::*;
use declarations::*;
use references::*;
pub use selection::validate_selection;

/// Validate the declared model without flattening repeated template instances.
pub fn validate_architecture<'a>(
    architecture: &'a Architecture,
    limits: &ValidationLimits,
) -> Result<ValidatedArchitecture<'a>, Diagnostics> {
    let result = (|| -> Checked<(Report, bool)> {
        let mut r = Report::new(*limits, Stage::Architecture)?;
        shape_preflight(architecture, &mut r)?;
        preflight(architecture, &mut r)?;
        let c = Context::new(architecture, &mut r)?;
        // Ambiguous declarations cannot be resolved by first/last writer wins.
        if !r.errors.is_empty() {
            return Ok((r, false));
        }
        hierarchy(&c, &mut r)?;
        if r.errors.iter().any(|d| d.code == Code::TemplateCycle) {
            return Ok((r, false));
        }
        for ty in c.index.types.values() {
            for pin in &ty.pins {
                if pin.width.get() == 0 {
                    r.emit(
                        diagnostic(
                            Code::Width,
                            r.stage,
                            "pin width must be positive",
                            &pin.provenance,
                        )
                        .with_key(ty.key.erase()),
                    )?;
                }
            }
        }
        for root in c.roots.values() {
            validate_instance(&c, root, true, &mut r)?;
        }
        for template in c.index.templates.values() {
            check_template(&c, template, &mut r)?;
        }
        check_connections(&c, None, &architecture.connections, &mut r)?;
        if r.errors.is_empty() {
            check_qualified_connections(&c, &mut r)?;
        }
        let valid = r.errors.is_empty();
        Ok((r, valid))
    })();
    match result {
        Err(error) => Err(vec![error]),
        Ok((r, true)) => Ok(ValidatedArchitecture {
            architecture,
            limits: *limits,
            stats: r.stats,
        }),
        Ok((mut r, false)) => {
            r.errors.sort();
            Err(r.errors)
        }
    }
}
