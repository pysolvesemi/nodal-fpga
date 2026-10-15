//! Strict, bounded Foundation exchange. No execution, networking, DeviceDB or RTL.
#![forbid(unsafe_code)]

mod architecture;
mod canonical;
mod design;
mod document;
mod error;
mod limits;
mod package;
mod parser;
mod wire;

pub use document::{
    CheckedArchitecture, CheckedDesign, SavedPackage, read_architecture, read_design, read_package,
};
pub use error::{ExchangeError, Notice};
pub use limits::Limits;
pub use parser::{JsonStats, parse_json};
pub use wire::Digest;
