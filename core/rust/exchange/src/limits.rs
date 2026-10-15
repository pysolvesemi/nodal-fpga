use crate::error::{ExchangeError, Result};

/// Reviewed positive ceilings; callers may lower, never raise them.
#[derive(Clone, Copy, Debug)]
pub struct Limits {
    pub input_bytes: usize,
    pub nesting: usize,
    pub nodes: u64,
    pub collection: usize,
    pub string_bytes: usize,
    pub artifacts: usize,
    pub artifact_bytes: u64,
    pub core: nf_arch_ir::ValidationLimits,
}
impl Default for Limits {
    fn default() -> Self {
        Self {
            input_bytes: 8_388_608,
            nesting: 64,
            nodes: 200_000,
            collection: 16_384,
            string_bytes: 65_536,
            artifacts: 256,
            artifact_bytes: 33_554_432,
            core: nf_arch_ir::ValidationLimits::default(),
        }
    }
}
impl Limits {
    pub(crate) fn check(&self) -> Result<()> {
        let max = Self::default();
        let checks = [
            (
                "input_bytes",
                self.input_bytes as u64,
                max.input_bytes as u64,
            ),
            ("nesting", self.nesting as u64, max.nesting as u64),
            ("nodes", self.nodes, max.nodes),
            ("collection", self.collection as u64, max.collection as u64),
            (
                "string_bytes",
                self.string_bytes as u64,
                max.string_bytes as u64,
            ),
            ("artifacts", self.artifacts as u64, max.artifacts as u64),
            ("artifact_bytes", self.artifact_bytes, max.artifact_bytes),
            (
                "declarations",
                self.core.max_declarations,
                max.core.max_declarations,
            ),
            (
                "references",
                self.core.max_references,
                max.core.max_references,
            ),
            ("work", self.core.max_work, max.core.max_work),
            (
                "core_collection",
                self.core.max_collection as u64,
                max.core.max_collection as u64,
            ),
            (
                "core_depth",
                self.core.max_depth as u64,
                max.core.max_depth as u64,
            ),
            (
                "component",
                self.core.max_key_component_bytes as u64,
                max.core.max_key_component_bytes as u64,
            ),
            (
                "key",
                self.core.max_key_bytes as u64,
                max.core.max_key_bytes as u64,
            ),
            (
                "provenance",
                self.core.max_provenance_bytes as u64,
                max.core.max_provenance_bytes as u64,
            ),
            (
                "diagnostics",
                self.core.max_diagnostics as u64,
                max.core.max_diagnostics as u64,
            ),
        ];
        for (name, n, ceiling) in checks {
            if n == 0 || n > ceiling {
                return Err(ExchangeError::new(
                    "invalid_limits",
                    "read",
                    "",
                    format!("invalid {name} capability"),
                )
                .bounds(n, format!("1..={ceiling}")));
            }
        }
        Ok(())
    }
}
