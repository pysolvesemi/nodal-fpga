//! Minimal public crate used to qualify the Rust build boundary.
//!
//! This is not a device model, architecture compiler or fabric generator.
//!
//! A downstream Rust consumer can use the public bootstrap identity:
//! ```
//! assert_eq!(nf_bootstrap::IDENTITY, "nodal-fpga/bootstrap/1");
//! ```

#![forbid(unsafe_code)]

/// Stable marker for the build-only smoke demonstration.
pub const IDENTITY: &str = "nodal-fpga/bootstrap/1";
