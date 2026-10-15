//! Checked foundation types, independent of concrete devices and file layouts.
//!
//! Portable keys compare exact UTF-8 components; no path, Unicode or case
//! normalization is performed. Dense IDs have meaning only in a checked build,
//! partition and resource-kind context. None of these Rust layouts defines a
//! serialization format, pointer ABI or memory-mapped file contract.
//!
//! Resource kinds are nominal, including for keys and qualified references:
//! ```compile_fail
//! use nf_types::{WireId, PipId};
//! let wire = WireId::new(7);
//! let pip: PipId = wire;
//! ```
//! ```compile_fail
//! use nf_types::{WireKey, PipKey};
//! let wire = WireKey::new("example", vec!["tile".into()], "W").unwrap();
//! let pip: PipKey = wire;
//! ```
//! ```compile_fail
//! use nf_types::{BuildId, DenseRef, PartitionId, Pip, Wire, WireId};
//! let wire: DenseRef<Wire> = DenseRef::new(
//!     BuildId::new([1; 32]), PartitionId::new(0), WireId::new(7));
//! let pip: DenseRef<Pip> = wire;
//! ```

#![forbid(unsafe_code)]

mod diagnostics;
mod identity;
mod units;

pub use diagnostics::*;
pub use identity::*;
pub use units::*;
