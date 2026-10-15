//! Small explicit file adapter. Identity components never become filesystem paths.
use nf_exchange::{
    Digest, ExchangeError, Limits, parse_json, read_architecture, read_design, read_package,
};
use std::{
    collections::BTreeMap,
    fs::File,
    io::{self, Read, Write},
    path::PathBuf,
};

fn error(code: &str, message: impl Into<String>) -> ExchangeError {
    ExchangeError::new(code, "operation", "", message)
}
fn open(path: &str) -> Result<File, ExchangeError> {
    File::open(path).map_err(|e| error("io", e.to_string()))
}
fn limit_overrides(text: &str, limits: &mut Limits) -> Result<(), ExchangeError> {
    let (value, _) = parse_json(text.as_bytes(), &Limits::default())?;
    let object = value
        .as_object()
        .ok_or_else(|| error("invalid_limits", "--limits must be a JSON object"))?;
    fn number(v: &serde_json::Value) -> Result<u64, ExchangeError> {
        v.as_u64().ok_or_else(|| {
            error(
                "invalid_limits",
                "limit overrides require positive integer literals",
            )
        })
    }
    fn small(v: &serde_json::Value) -> Result<usize, ExchangeError> {
        usize::try_from(number(v)?).map_err(|_| error("invalid_limits", "limit does not fit usize"))
    }
    for (k, v) in object {
        match k.as_str() {
            "input_bytes" => limits.input_bytes = small(v)?,
            "nesting" => limits.nesting = small(v)?,
            "nodes" => limits.nodes = number(v)?,
            "collection" => limits.collection = small(v)?,
            "string_bytes" => limits.string_bytes = small(v)?,
            "artifacts" => limits.artifacts = small(v)?,
            "artifact_bytes" => limits.artifact_bytes = number(v)?,
            "core" => {
                for (k, v) in v
                    .as_object()
                    .ok_or_else(|| error("invalid_limits", "core limits must be an object"))?
                {
                    match k.as_str() {
                        "max_declarations" => limits.core.max_declarations = number(v)?,
                        "max_references" => limits.core.max_references = number(v)?,
                        "max_work" => limits.core.max_work = number(v)?,
                        "max_collection" => limits.core.max_collection = small(v)?,
                        "max_depth" => limits.core.max_depth = small(v)?,
                        "max_key_component_bytes" => {
                            limits.core.max_key_component_bytes = small(v)?
                        }
                        "max_key_bytes" => limits.core.max_key_bytes = small(v)?,
                        "max_provenance_bytes" => limits.core.max_provenance_bytes = small(v)?,
                        "max_diagnostics" => limits.core.max_diagnostics = small(v)?,
                        _ => return Err(error("invalid_limits", "unknown core limit")),
                    }
                }
            }
            _ => return Err(error("invalid_limits", "unknown limit field")),
        }
    }
    Ok(())
}
fn run() -> Result<Vec<u8>, ExchangeError> {
    let mut args = std::env::args().skip(1);
    let command = args
        .next()
        .ok_or_else(|| error("unsupported_operation", "an operation is required"))?;
    if !matches!(command.as_str(), "parse" | "arch" | "package" | "design") {
        return Err(error(
            "unsupported_operation",
            "operation is unsupported by this software-only exchange profile",
        ));
    }
    let input = args
        .next()
        .ok_or_else(|| error("io", "an explicit input file is required"))?;
    let mut output = "summary".to_owned();
    let mut artifacts: BTreeMap<Digest, PathBuf> = BTreeMap::new();
    let mut package = None;
    let mut limits = Limits::default();
    while let Some(option) = args.next() {
        let value = args
            .next()
            .ok_or_else(|| error("wrong_type", "option requires an argument"))?;
        match option.as_str() {
            "--output" => output = value,
            "--package" => package = Some(value),
            "--limits" => limit_overrides(&value, &mut limits)?,
            "--artifact" => {
                let (digest, path) = value
                    .split_once('=')
                    .ok_or_else(|| error("wrong_type", "artifact requires DIGEST=PATH"))?;
                let digest = Digest::from_hex(digest)?;
                if artifacts.insert(digest, PathBuf::from(path)).is_some() {
                    return Err(error("duplicate", "duplicate caller digest binding"));
                }
            }
            _ => return Err(error("unsupported_operation", "unknown option")),
        }
    }
    if !matches!(output.as_str(), "canonical" | "projection" | "summary") {
        return Err(error("unsupported_operation", "unknown output mode"));
    }
    let mut resolver = |digest: &Digest| -> io::Result<Box<dyn Read>> {
        let path = artifacts.get(digest).ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::NotFound,
                "no caller binding for required digest",
            )
        })?;
        Ok(Box::new(File::open(path)?))
    };
    macro_rules! emit {
        ($value:expr) => {{
            let value = $value?;
            match output.as_str() {
                "canonical" => value.canonical_bytes(),
                "projection" => value.semantic_bytes(),
                _ => serde_json::to_vec(&value.summary()).map_err(|e| error("io", e.to_string())),
            }
        }};
    }
    match command.as_str() {
        "parse" => {
            let (value, _) = parse_json(open(&input)?, &limits)?;
            serde_json::to_vec(&value).map_err(|e| error("io", e.to_string()))
        }
        "arch" => emit!(read_architecture(open(&input)?, &limits)),
        "package" => emit!(read_package(open(&input)?, &mut resolver, &limits)),
        "design" => {
            let target = package
                .ok_or_else(|| error("artifact_missing", "design requires --package MANIFEST"))?;
            let package = read_package(open(&target)?, &mut resolver, &limits)?;
            emit!(read_design(open(&input)?, &package, &limits))
        }
        _ => Err(error("unsupported_operation", "unsupported operation")),
    }
}
fn main() {
    match run() {
        Ok(bytes) => {
            if let Err(e) = io::stdout().lock().write_all(&bytes) {
                let _ = serde_json::to_writer(io::stderr().lock(), &error("io", e.to_string()));
                std::process::exit(1);
            }
        }
        Err(e) => {
            let mut stderr = io::stderr().lock();
            let _ = serde_json::to_writer(&mut stderr, &e);
            let _ = stderr.write_all(b"\n");
            std::process::exit(1);
        }
    }
}
