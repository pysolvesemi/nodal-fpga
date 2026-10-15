//! Minimal, target-bound mapped-design checks; no placement or bus expansion.
//!
//! The document layer verifies the exact target build before calling this module.
//! Design-only accounting is independent of the target's architecture validation:
//! declarations count the body and each cell, port, net and terminal record;
//! references count each cell's type and mode, each cell terminal's cell and pin,
//! and each port terminal's port. Constants do not reference a declaration.
//! Work charges one per declaration/reference, provenance visit, index insertion,
//! lookup and traversed target entry, plus UTF-8 bytes + 1 for every visited
//! name/provenance string. Ordered-map and borrowed-index sort comparisons are
//! not separate work units. Target type keys and searched mode/pin names are
//! metered too. Numeric widths and bit indices never control allocation or iteration.

use crate::{
    architecture as adapter,
    error::{ExchangeError, Result},
    limits::Limits,
    wire as w,
};
use nf_arch_ir as a;
use nf_types as t;
use std::cmp::Ordering;
use std::collections::BTreeMap;

struct Budget<'a> {
    limits: &'a a::ValidationLimits,
    declarations: u64,
    references: u64,
    work: u64,
}

impl<'a> Budget<'a> {
    fn new(limits: &'a a::ValidationLimits) -> Self {
        Self {
            limits,
            declarations: 0,
            references: 0,
            work: 0,
        }
    }

    fn exceeded(path: &str, name: &str, actual: u64, maximum: u64) -> ExchangeError {
        ExchangeError::new(
            "limit",
            "semantic",
            path,
            format!("mapped-design {name} budget exceeded"),
        )
        .bounds(actual, maximum)
    }

    fn charge(total: &mut u64, amount: u64, maximum: u64, path: &str, name: &str) -> Result<()> {
        let next = total
            .checked_add(amount)
            .ok_or_else(|| Self::exceeded(path, name, u64::MAX, maximum))?;
        if next > maximum {
            return Err(Self::exceeded(path, name, next, maximum));
        }
        *total = next;
        Ok(())
    }

    fn tick(&mut self, amount: u64, path: &str) -> Result<()> {
        Self::charge(&mut self.work, amount, self.limits.max_work, path, "work")
    }

    fn record(&mut self, path: &str) -> Result<()> {
        Self::charge(
            &mut self.declarations,
            1,
            self.limits.max_declarations,
            path,
            "declarations",
        )?;
        self.tick(1, path)
    }

    fn references(&mut self, amount: u64, path: &str) -> Result<()> {
        Self::charge(
            &mut self.references,
            amount,
            self.limits.max_references,
            path,
            "references",
        )?;
        self.tick(amount, path)
    }

    fn collection(&self, length: usize, path: &str) -> Result<()> {
        if length > self.limits.max_collection {
            return Err(Self::exceeded(
                path,
                "collection",
                length as u64,
                self.limits.max_collection as u64,
            ));
        }
        Ok(())
    }

    fn text(&mut self, value: &str, path: &str) -> Result<()> {
        let length = u64::try_from(value.len()).unwrap_or(u64::MAX);
        self.tick(length.saturating_add(1), path)
    }

    fn name(&mut self, value: &str, path: &str) -> Result<()> {
        // Keep the original checked-constructor diagnostic, including its stage.
        adapter::name(value.to_owned(), path)?;
        self.text(value, path)?;
        if value.len() > self.limits.max_key_component_bytes {
            return Err(Self::exceeded(
                path,
                "name bytes",
                value.len() as u64,
                self.limits.max_key_component_bytes as u64,
            ));
        }
        Ok(())
    }

    fn key(&mut self, value: &w::Key, path: &str) -> Result<t::ResourceTypeKey> {
        let key = adapter::key::<t::ResourceType>(value.clone(), path)?;
        if key.scope().len() > self.limits.max_depth {
            return Err(Self::exceeded(
                &format!("{path}/scope"),
                "key depth",
                key.scope().len() as u64,
                self.limits.max_depth as u64,
            ));
        }
        self.name(key.namespace().as_str(), &format!("{path}/namespace"))?;
        let mut bytes = key.namespace().as_str().len();
        for (index, part) in key.scope().iter().enumerate() {
            self.name(part.as_str(), &format!("{path}/scope/{index}"))?;
            bytes += part.as_str().len();
        }
        self.name(key.local().as_str(), &format!("{path}/local"))?;
        bytes += key.local().as_str().len();
        // The public Key constructor has already bounded all additions above.
        if bytes > self.limits.max_key_bytes {
            return Err(Self::exceeded(
                path,
                "key bytes",
                bytes as u64,
                self.limits.max_key_bytes as u64,
            ));
        }
        Ok(key)
    }

    fn provenance(&mut self, value: &w::Provenance, path: &str) -> Result<t::Provenance> {
        let provenance = adapter::provenance(value.clone(), path)?;
        self.tick(1, path)?;
        for (value, suffix) in [
            (provenance.display(), "display"),
            (provenance.span().map(t::SourceSpan::source), "span/source"),
        ] {
            if let Some(value) = value {
                let path = format!("{path}/{suffix}");
                self.text(value, &path)?;
                if value.len() > self.limits.max_provenance_bytes {
                    return Err(Self::exceeded(
                        &path,
                        "provenance bytes",
                        value.len() as u64,
                        self.limits.max_provenance_bytes as u64,
                    ));
                }
            }
        }
        Ok(provenance)
    }
}

fn diagnostic(code: t::Code, message: &str, provenance: &t::Provenance) -> t::Diagnostic {
    t::Diagnostic::new(code, t::Stage::Architecture, message, provenance.clone())
        .with_remedy("Correct the mapped-design declaration under the target's structural profile.")
}

fn semantic(path: &str, diagnostic: t::Diagnostic) -> ExchangeError {
    ExchangeError::core(path, vec![diagnostic])
}

fn terminal_preflight(value: &w::Terminal, path: &str, budget: &mut Budget<'_>) -> Result<()> {
    budget.record(path)?;
    let provenance = match value {
        w::Terminal::Cell {
            cell,
            pin,
            provenance,
            ..
        } => {
            budget.references(2, path)?;
            budget.name(cell, &format!("{path}/cell"))?;
            budget.name(pin, &format!("{path}/pin"))?;
            provenance
        }
        w::Terminal::Port {
            port, provenance, ..
        } => {
            budget.references(1, path)?;
            budget.name(port, &format!("{path}/port"))?;
            provenance
        }
        w::Terminal::Constant { value, provenance } => {
            budget.text(value, &format!("{path}/value"))?;
            if value != "0" && value != "1" {
                return Err(ExchangeError::new(
                    "invalid_enum",
                    "decode",
                    format!("{path}/value"),
                    "unsupported scalar constant",
                )
                .bounds(value, "0|1"));
            }
            provenance
        }
    };
    budget.provenance(provenance, &format!("{path}/provenance"))?;
    Ok(())
}

/// Check shape, all scalar adapters and counters before semantic indexes exist.
fn preflight(value: &w::Design, budget: &mut Budget<'_>) -> Result<()> {
    budget.record("/body")?;
    budget.name(&value.namespace, "/body/namespace")?;
    budget.name(&value.name, "/body/name")?;
    budget.provenance(&value.provenance, "/body/provenance")?;
    budget.collection(value.cells.len(), "/body/cells")?;
    budget.collection(value.ports.len(), "/body/ports")?;
    budget.collection(value.nets.len(), "/body/nets")?;
    for (index, cell) in value.cells.iter().enumerate() {
        let path = format!("/body/cells/{index}");
        budget.record(&path)?;
        budget.references(2, &path)?;
        budget.name(&cell.name, &format!("{path}/name"))?;
        budget.key(&cell.resource_type, &format!("{path}/resource_type"))?;
        budget.name(&cell.mode, &format!("{path}/mode"))?;
        budget.provenance(&cell.provenance, &format!("{path}/provenance"))?;
    }
    for (index, port) in value.ports.iter().enumerate() {
        let path = format!("/body/ports/{index}");
        budget.record(&path)?;
        budget.name(&port.name, &format!("{path}/name"))?;
        adapter::direction(&port.direction, &format!("{path}/direction"))?;
        budget.provenance(&port.provenance, &format!("{path}/provenance"))?;
    }
    for (index, net) in value.nets.iter().enumerate() {
        let path = format!("/body/nets/{index}");
        budget.record(&path)?;
        budget.name(&net.name, &format!("{path}/name"))?;
        budget.provenance(&net.provenance, &format!("{path}/provenance"))?;
        budget.collection(net.loads.len(), &format!("{path}/loads"))?;
        terminal_preflight(&net.driver, &format!("{path}/driver"), budget)?;
        for (index, load) in net.loads.iter().enumerate() {
            terminal_preflight(load, &format!("{path}/loads/{index}"), budget)?;
        }
    }
    Ok(())
}

fn duplicate(
    path: &str,
    name: &str,
    current: &w::Provenance,
    previous: &w::Provenance,
    budget: &mut Budget<'_>,
) -> Result<()> {
    let current = budget.provenance(current, &format!("{path}/provenance"))?;
    // Both values have passed preflight. Use the original origin as related data.
    let previous = budget.provenance(previous, path)?;
    Err(semantic(
        &format!("{path}/name"),
        diagnostic(
            t::Code::Duplicate,
            "name is declared more than once in its category",
            &current,
        )
        .with_actual(name)
        .with_expected("one declaration per name")
        .with_related(previous, None),
    ))
}

fn compare_provenance(left: &w::Provenance, right: &w::Provenance) -> Ordering {
    let left_span = left
        .span
        .0
        .as_ref()
        .map(|span| (&span.source, span.source_bytes.0, span.start.0, span.end.0));
    let right_span = right
        .span
        .0
        .as_ref()
        .map(|span| (&span.source, span.source_bytes.0, span.start.0, span.end.0));
    left_span
        .cmp(&right_span)
        .then_with(|| left.display.0.cmp(&right.display.0))
}

fn ordered_named<'a, T>(
    values: &'a [T],
    key: impl Fn(&'a T) -> (&'a str, &'a w::Provenance),
    path: &str,
    budget: &mut Budget<'_>,
) -> Result<Vec<(usize, &'a T)>> {
    let mut ordered = Vec::new();
    for (index, value) in values.iter().enumerate() {
        budget.tick(1, path)?;
        ordered.push((index, value));
    }
    ordered.sort_by(|(_, left), (_, right)| {
        let (left_name, left_provenance) = key(left);
        let (right_name, right_provenance) = key(right);
        left_name
            .cmp(right_name)
            .then_with(|| compare_provenance(left_provenance, right_provenance))
    });
    Ok(ordered)
}

fn terminal_provenance(value: &w::Terminal) -> &w::Provenance {
    match value {
        w::Terminal::Cell { provenance, .. }
        | w::Terminal::Port { provenance, .. }
        | w::Terminal::Constant { provenance, .. } => provenance,
    }
}

fn ordered_loads<'a>(
    values: &'a [w::Terminal],
    path: &str,
    budget: &mut Budget<'_>,
) -> Result<Vec<(usize, &'a w::Terminal)>> {
    let mut ordered = Vec::new();
    for (index, value) in values.iter().enumerate() {
        budget.tick(1, path)?;
        ordered.push((index, value));
    }
    ordered.sort_by(|(_, left), (_, right)| {
        left.sort_key()
            .cmp(&right.sort_key())
            .then_with(|| compare_provenance(terminal_provenance(left), terminal_provenance(right)))
    });
    Ok(ordered)
}

struct Cell<'a> {
    resource_type: &'a a::ResourceType,
}

#[derive(Eq, PartialEq, Ord, PartialOrd)]
enum TerminalKey<'a> {
    Cell(&'a str, &'a str, u64),
    Port(&'a str, u64),
}

struct Context<'a> {
    cells: BTreeMap<&'a str, Cell<'a>>,
    ports: BTreeMap<&'a str, (usize, &'a w::Pin)>,
    ownership: BTreeMap<TerminalKey<'a>, t::Provenance>,
}

impl<'a> Context<'a> {
    fn terminal(
        &mut self,
        value: &'a w::Terminal,
        driver: bool,
        path: &str,
        budget: &mut Budget<'_>,
    ) -> Result<()> {
        let (key, direction, width, provenance, declaration, resource_key) = match value {
            w::Terminal::Constant { provenance, .. } => {
                let provenance = budget.provenance(provenance, &format!("{path}/provenance"))?;
                if !driver {
                    return Err(semantic(
                        path,
                        diagnostic(
                            t::Code::Direction,
                            "a constant is permitted only as a driver",
                            &provenance,
                        )
                        .with_actual("constant load")
                        .with_expected("cell input or top-level output"),
                    ));
                }
                // Constant values are not terminals owned by any declaration.
                return Ok(());
            }
            w::Terminal::Cell {
                cell,
                pin,
                bit,
                provenance,
            } => {
                let provenance = budget.provenance(provenance, &format!("{path}/provenance"))?;
                budget.text(cell, &format!("{path}/cell"))?;
                budget.tick(1, &format!("{path}/cell"))?;
                let cell_declaration = self.cells.get(cell.as_str()).ok_or_else(|| {
                    semantic(
                        &format!("{path}/cell"),
                        diagnostic(
                            t::Code::Missing,
                            "terminal cell does not exist",
                            &provenance,
                        )
                        .with_actual(cell)
                        .with_expected("a declared cell"),
                    )
                })?;
                let resource_type = cell_declaration.resource_type;
                budget.text(pin, &format!("{path}/pin"))?;
                // Pins are ordered in the target. Search without materializing a bus.
                let mut found = None;
                for candidate in &resource_type.pins {
                    budget.tick(1, &format!("{path}/pin"))?;
                    budget.text(candidate.name.as_str(), &format!("{path}/pin"))?;
                    if candidate.name.as_str() == pin {
                        found = Some(candidate);
                        break;
                    }
                }
                let pin_declaration = found.ok_or_else(|| {
                    semantic(
                        &format!("{path}/pin"),
                        diagnostic(
                            t::Code::Missing,
                            "terminal pin does not exist on the cell type",
                            &provenance,
                        )
                        .with_key(resource_type.key.erase())
                        .with_actual(pin)
                        .with_expected("a declared pin of the cell type")
                        .with_related(
                            resource_type.provenance.clone(),
                            Some(resource_type.key.erase()),
                        ),
                    )
                })?;
                (
                    TerminalKey::Cell(cell, pin, bit.0),
                    pin_declaration.direction,
                    pin_declaration.width.get(),
                    provenance,
                    pin_declaration.provenance.clone(),
                    Some(resource_type.key.erase()),
                )
            }
            w::Terminal::Port {
                port,
                bit,
                provenance,
            } => {
                let provenance = budget.provenance(provenance, &format!("{path}/provenance"))?;
                budget.text(port, &format!("{path}/port"))?;
                budget.tick(1, &format!("{path}/port"))?;
                let (index, declaration) = self.ports.get(port.as_str()).ok_or_else(|| {
                    semantic(
                        &format!("{path}/port"),
                        diagnostic(
                            t::Code::Missing,
                            "terminal port does not exist",
                            &provenance,
                        )
                        .with_actual(port)
                        .with_expected("a declared top-level port"),
                    )
                })?;
                let direction = adapter::direction(
                    &declaration.direction,
                    &format!("/body/ports/{index}/direction"),
                )?;
                let origin = budget.provenance(
                    &declaration.provenance,
                    &format!("/body/ports/{index}/provenance"),
                )?;
                (
                    TerminalKey::Port(port, bit.0),
                    direction,
                    declaration.width.0,
                    provenance,
                    origin,
                    None,
                )
            }
        };
        let expected = match (&key, driver) {
            (TerminalKey::Cell(..), true) | (TerminalKey::Port(..), false) => a::Direction::Output,
            (TerminalKey::Cell(..), false) | (TerminalKey::Port(..), true) => a::Direction::Input,
        };
        if direction != expected {
            let mut error = diagnostic(
                t::Code::Direction,
                "terminal direction is incompatible with its net role",
                &provenance,
            )
            .with_actual(direction_name(direction))
            .with_expected(direction_name(expected))
            .with_related(declaration, resource_key.clone());
            if let Some(key) = resource_key {
                error = error.with_key(key);
            }
            return Err(semantic(path, error));
        }
        let bit = match &key {
            TerminalKey::Cell(_, _, bit) | TerminalKey::Port(_, bit) => *bit,
        };
        if bit >= width {
            let mut error = diagnostic(
                t::Code::Bounds,
                "terminal bit is outside its declared width",
                &provenance,
            )
            .with_actual(bit.to_string())
            .with_expected(format!("bit < {width}"))
            .with_related(declaration, resource_key.clone());
            if let Some(key) = resource_key {
                error = error.with_key(key);
            }
            return Err(semantic(&format!("{path}/bit"), error));
        }
        budget.tick(1, path)?;
        if let Some(previous) = self.ownership.insert(key, provenance.clone()) {
            return Err(semantic(
                path,
                diagnostic(
                    t::Code::Duplicate,
                    "terminal is claimed by more than one driver/load ownership record",
                    &provenance,
                )
                .with_expected("one ownership record per scalar terminal")
                .with_related(previous, resource_key),
            ));
        }
        Ok(())
    }
}

fn direction_name(value: a::Direction) -> &'static str {
    match value {
        a::Direction::Input => "input",
        a::Direction::Output => "output",
    }
}

fn resource_kind_name(value: a::ResourceKind) -> &'static str {
    match value {
        a::ResourceKind::Wire => "wire",
        a::ResourceKind::Pip => "pip",
        a::ResourceKind::Bel => "bel",
        a::ResourceKind::Pin => "pin",
        a::ResourceKind::Node => "node",
        a::ResourceKind::Site => "site",
        a::ResourceKind::Field => "field",
    }
}

/// The supplied architecture must belong to the verified target SavedPackage.
pub(crate) fn validate(
    value: &w::Design,
    architecture: &a::Architecture,
    limits: &Limits,
) -> Result<()> {
    let mut budget = Budget::new(&limits.core);
    preflight(value, &mut budget)?;

    let mut types = BTreeMap::new();
    // An empty cell set does not require even a target type index.
    if !value.cells.is_empty() {
        for resource_type in &architecture.resource_types {
            budget.tick(1, "/body/cells")?;
            budget.text(resource_type.key.namespace().as_str(), "/body/cells")?;
            for part in resource_type.key.scope() {
                budget.text(part.as_str(), "/body/cells")?;
            }
            budget.text(resource_type.key.local().as_str(), "/body/cells")?;
            budget.tick(1, "/body/cells")?;
            types.insert(&resource_type.key, resource_type);
        }
    }

    let mut cells = BTreeMap::<&str, (usize, &w::Cell)>::new();
    for (index, cell) in ordered_named(
        &value.cells,
        |cell| (cell.name.as_str(), &cell.provenance),
        "/body/cells",
        &mut budget,
    )? {
        let path = format!("/body/cells/{index}");
        budget.text(&cell.name, &format!("{path}/name"))?;
        budget.tick(1, &path)?;
        if let Some((_, previous)) = cells.insert(&cell.name, (index, cell)) {
            duplicate(
                &path,
                &cell.name,
                &cell.provenance,
                &previous.provenance,
                &mut budget,
            )?;
        }
    }
    let mut context = Context {
        cells: BTreeMap::new(),
        ports: BTreeMap::new(),
        ownership: BTreeMap::new(),
    };
    // Keyed traversal makes semantic checks independent of declaration ordering.
    for (name, (index, cell)) in cells {
        let path = format!("/body/cells/{index}");
        let provenance = budget.provenance(&cell.provenance, &format!("{path}/provenance"))?;
        let key = budget.key(&cell.resource_type, &format!("{path}/resource_type"))?;
        budget.tick(1, &format!("{path}/resource_type"))?;
        let resource_type = types.get(&key).copied().ok_or_else(|| {
            semantic(
                &format!("{path}/resource_type"),
                diagnostic(
                    t::Code::Missing,
                    "cell resource type does not exist in the target architecture",
                    &provenance,
                )
                .with_key(key.erase())
                .with_expected("a declared resource_type"),
            )
        })?;
        if resource_type.kind != a::ResourceKind::Bel {
            return Err(semantic(
                &format!("{path}/resource_type"),
                diagnostic(
                    t::Code::WrongKind,
                    "cell resource type must declare a BEL",
                    &provenance,
                )
                .with_key(key.erase())
                .with_actual(resource_kind_name(resource_type.kind))
                .with_expected("bel")
                .with_related(
                    resource_type.provenance.clone(),
                    Some(resource_type.key.erase()),
                ),
            ));
        }
        budget.text(&cell.mode, &format!("{path}/mode"))?;
        let mut mode_exists = false;
        // Mode order is nonsemantic: charge the complete list, including on success.
        for mode in &resource_type.modes {
            budget.tick(1, &format!("{path}/mode"))?;
            budget.text(mode.as_str(), &format!("{path}/mode"))?;
            mode_exists |= mode.as_str() == cell.mode;
        }
        if !mode_exists {
            return Err(semantic(
                &format!("{path}/mode"),
                diagnostic(
                    t::Code::Mode,
                    "cell mode is not declared by its resource type",
                    &provenance,
                )
                .with_key(key.erase())
                .with_actual(&cell.mode)
                .with_expected("a mode declared by the cell type")
                .with_related(
                    resource_type.provenance.clone(),
                    Some(resource_type.key.erase()),
                ),
            ));
        }
        budget.tick(1, &path)?;
        context.cells.insert(name, Cell { resource_type });
    }
    drop(types);

    for (index, port) in ordered_named(
        &value.ports,
        |port| (port.name.as_str(), &port.provenance),
        "/body/ports",
        &mut budget,
    )? {
        let path = format!("/body/ports/{index}");
        budget.text(&port.name, &format!("{path}/name"))?;
        budget.tick(1, &path)?;
        if let Some((_, previous)) = context.ports.insert(&port.name, (index, port)) {
            duplicate(
                &path,
                &port.name,
                &port.provenance,
                &previous.provenance,
                &mut budget,
            )?;
        }
    }
    for (index, port) in context.ports.values() {
        if port.width.0 == 0 {
            let path = format!("/body/ports/{index}");
            let provenance = budget.provenance(&port.provenance, &format!("{path}/provenance"))?;
            return Err(semantic(
                &format!("{path}/width"),
                diagnostic(
                    t::Code::Width,
                    "design port width must be positive",
                    &provenance,
                )
                .with_actual("0")
                .with_expected("1..=18446744073709551615"),
            ));
        }
    }

    let mut nets = BTreeMap::<&str, (usize, &w::Net)>::new();
    for (index, net) in ordered_named(
        &value.nets,
        |net| (net.name.as_str(), &net.provenance),
        "/body/nets",
        &mut budget,
    )? {
        let path = format!("/body/nets/{index}");
        budget.text(&net.name, &format!("{path}/name"))?;
        budget.tick(1, &path)?;
        if let Some((_, previous)) = nets.insert(&net.name, (index, net)) {
            duplicate(
                &path,
                &net.name,
                &net.provenance,
                &previous.provenance,
                &mut budget,
            )?;
        }
    }
    for (index, net) in nets.values() {
        let path = format!("/body/nets/{index}");
        budget.tick(1, &path)?;
        if net.loads.is_empty() {
            let provenance = budget.provenance(&net.provenance, &format!("{path}/provenance"))?;
            return Err(semantic(
                &format!("{path}/loads"),
                diagnostic(
                    t::Code::Connection,
                    "net must have at least one scalar load",
                    &provenance,
                )
                .with_actual("0")
                .with_expected("one or more loads"),
            ));
        }
        context.terminal(&net.driver, true, &format!("{path}/driver"), &mut budget)?;
        for (index, load) in ordered_loads(&net.loads, &format!("{path}/loads"), &mut budget)? {
            context.terminal(load, false, &format!("{path}/loads/{index}"), &mut budget)?;
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn provenance() -> w::Provenance {
        w::Provenance {
            span: w::Nullable(None),
            display: w::Nullable(None),
        }
    }

    fn cell(pin: &str, bit: u64) -> w::Terminal {
        w::Terminal::Cell {
            cell: "c/..".into(),
            pin: pin.into(),
            bit: w::U64(bit),
            provenance: provenance(),
        }
    }

    fn port(name: &str, bit: u64) -> w::Terminal {
        w::Terminal::Port {
            port: name.into(),
            bit: w::U64(bit),
            provenance: provenance(),
        }
    }

    fn constant(value: &str) -> w::Terminal {
        w::Terminal::Constant {
            value: value.into(),
            provenance: provenance(),
        }
    }

    fn fixture() -> (w::Design, a::Architecture) {
        let key = t::ResourceTypeKey::new("n", vec!["a/b".into(), "..".into()], "B").unwrap();
        let mut architecture = a::Architecture::new(t::Name::new("n").unwrap());
        architecture.resource_types.push(a::ResourceType {
            key,
            kind: a::ResourceKind::Bel,
            pins: vec![
                a::Pin {
                    name: t::Name::new("..").unwrap(),
                    direction: a::Direction::Input,
                    width: t::BitCount::new(2),
                    provenance: t::Provenance::default(),
                },
                a::Pin {
                    name: t::Name::new("/").unwrap(),
                    direction: a::Direction::Output,
                    width: t::BitCount::new(2),
                    provenance: t::Provenance::default(),
                },
            ],
            modes: vec![t::Name::new("m").unwrap()],
            provenance: t::Provenance::default(),
        });
        let digest = w::Digest::of_bytes(b"design module does not interpret identity");
        let design = w::Design {
            semantic_id: digest.clone(),
            namespace: "n".into(),
            name: "d".into(),
            target_build_id: digest,
            cells: vec![w::Cell {
                name: "c/..".into(),
                resource_type: w::Key {
                    kind: "resource_type".into(),
                    namespace: "n".into(),
                    scope: vec!["a/b".into(), "..".into()],
                    local: "B".into(),
                },
                mode: "m".into(),
                provenance: provenance(),
            }],
            ports: vec![
                w::Pin {
                    name: "p/a".into(),
                    direction: "input".into(),
                    width: w::U64(2),
                    provenance: provenance(),
                },
                w::Pin {
                    name: "q".into(),
                    direction: "output".into(),
                    width: w::U64(2),
                    provenance: provenance(),
                },
            ],
            nets: vec![
                w::Net {
                    name: "n1".into(),
                    driver: port("p/a", 0),
                    loads: vec![cell("..", 0)],
                    provenance: provenance(),
                },
                w::Net {
                    name: "n2".into(),
                    driver: cell("/", 0),
                    loads: vec![port("q", 0)],
                    provenance: provenance(),
                },
            ],
            provenance: provenance(),
        };
        (design, architecture)
    }

    fn core_error(
        design: &w::Design,
        architecture: &a::Architecture,
        expected: t::Code,
    ) -> ExchangeError {
        let error = validate(design, architecture, &Limits::default()).unwrap_err();
        assert_eq!(error.code, "semantic");
        assert_eq!(error.core.len(), 1);
        assert_eq!(error.core[0].code, expected);
        error
    }

    #[test]
    fn exact_components_and_u64_bus_widths_need_only_scalar_storage() {
        let (mut design, mut architecture) = fixture();
        a::validate_architecture(&architecture, &a::ValidationLimits::default()).unwrap();
        validate(&design, &architecture, &Limits::default()).unwrap();
        for pin in &mut architecture.resource_types[0].pins {
            pin.width = t::BitCount::new(u64::MAX);
        }
        for pin in &mut design.ports {
            pin.width = w::U64(u64::MAX);
        }
        for net in &mut design.nets {
            for terminal in std::iter::once(&mut net.driver).chain(&mut net.loads) {
                match terminal {
                    w::Terminal::Cell { bit, .. } | w::Terminal::Port { bit, .. } => {
                        *bit = w::U64(u64::MAX - 1)
                    }
                    w::Terminal::Constant { .. } => unreachable!(),
                }
            }
        }
        validate(&design, &architecture, &Limits::default()).unwrap();
        design.nets[0].driver = port("p/a", u64::MAX);
        assert_eq!(
            core_error(&design, &architecture, t::Code::Bounds).pointer,
            "/body/nets/0/driver/bit"
        );
    }

    #[test]
    fn cell_keys_types_and_modes_have_distinct_failures() {
        let (mut design, mut architecture) = fixture();
        design.cells[0].resource_type.kind = "bel".into();
        let error = validate(&design, &architecture, &Limits::default()).unwrap_err();
        assert_eq!(error.code, "invalid_enum");
        assert_eq!(error.pointer, "/body/cells/0/resource_type/kind");
        design.cells[0].resource_type.kind = "resource_type".into();
        architecture.resource_types[0].kind = a::ResourceKind::Wire;
        let error = core_error(&design, &architecture, t::Code::WrongKind);
        assert!(error.core[0].key.is_some());
        assert_eq!(error.core[0].related.len(), 1);
        architecture.resource_types[0].kind = a::ResourceKind::Bel;
        design.cells[0].resource_type.local = "absent".into();
        core_error(&design, &architecture, t::Code::Missing);
        design.cells[0].resource_type.local = "B".into();
        design.cells[0].mode = "absent".into();
        assert_eq!(
            core_error(&design, &architecture, t::Code::Mode).pointer,
            "/body/cells/0/mode"
        );
    }

    #[test]
    fn checked_name_and_provenance_diagnostics_are_retained() {
        let (mut design, architecture) = fixture();
        design.name.clear();
        let error = core_error(&design, &architecture, t::Code::InvalidName);
        assert_eq!(error.core[0].stage, t::Stage::Identity);
        assert_eq!(error.pointer, "/body/name");
        design.name = "d".into();
        design.provenance.span = w::Nullable(Some(w::Span {
            source: "../never-open-this".into(),
            source_bytes: w::U64(3),
            start: w::U64(0),
            end: w::U64(4),
        }));
        let error = core_error(&design, &architecture, t::Code::Bounds);
        assert_eq!(error.core[0].stage, t::Stage::Types);
        assert_eq!(error.pointer, "/body/provenance/span");
    }

    #[test]
    fn port_width_direction_and_endpoint_ownership_are_checked() {
        let (original, architecture) = fixture();
        let mut design = original.clone();
        design.ports[0].direction = "inout".into();
        let error = validate(&design, &architecture, &Limits::default()).unwrap_err();
        assert_eq!(error.code, "invalid_enum");
        assert_eq!(error.pointer, "/body/ports/0/direction");
        design = original.clone();
        design.ports[0].width = w::U64(0);
        core_error(&design, &architecture, t::Code::Width);
        design = original.clone();
        design.nets[0].driver = cell("..", 1);
        core_error(&design, &architecture, t::Code::Direction);
        design = original.clone();
        design.nets[0].loads[0] = cell("missing", 0);
        core_error(&design, &architecture, t::Code::Missing);
        design = original.clone();
        design.nets[1].loads.push(cell("..", 0));
        let error = core_error(&design, &architecture, t::Code::Duplicate);
        assert_eq!(error.pointer, "/body/nets/1/loads/1");
        assert_eq!(error.core[0].related.len(), 1);
        design = original;
        design.nets[1].driver = port("p/a", 0);
        core_error(&design, &architecture, t::Code::Duplicate);
    }

    #[test]
    fn names_are_unique_within_each_category_and_nets_need_loads() {
        let (original, architecture) = fixture();
        let mut design = original.clone();
        design.cells.push(design.cells[0].clone());
        core_error(&design, &architecture, t::Code::Duplicate);
        design = original.clone();
        design.ports.push(design.ports[0].clone());
        core_error(&design, &architecture, t::Code::Duplicate);
        design = original.clone();
        design.nets.push(design.nets[0].clone());
        core_error(&design, &architecture, t::Code::Duplicate);
        design = original;
        design.nets[0].loads.clear();
        core_error(&design, &architecture, t::Code::Connection);
    }

    #[test]
    fn repeated_constants_are_drivers_not_shared_owned_terminals() {
        let (mut design, architecture) = fixture();
        design.nets[0].driver = constant("0");
        design.nets[1].driver = constant("0");
        validate(&design, &architecture, &Limits::default()).unwrap();
        design.nets[0].loads[0] = constant("0");
        core_error(&design, &architecture, t::Code::Direction);
        design.nets[0].loads[0] = constant("2");
        let error = validate(&design, &architecture, &Limits::default()).unwrap_err();
        assert_eq!(error.code, "invalid_enum");
        assert_eq!(error.pointer, "/body/nets/0/loads/0/value");
    }

    #[test]
    fn semantic_load_failure_is_stable_under_set_permutation() {
        let (mut design, architecture) = fixture();
        design.nets[0].loads = vec![port("missing", 0), cell("missing", 0)];
        let first = core_error(&design, &architecture, t::Code::Missing);
        assert_eq!(first.pointer, "/body/nets/0/loads/1/pin");
        design.nets[0].loads.reverse();
        let second = core_error(&design, &architecture, t::Code::Missing);
        assert_eq!(second.pointer, "/body/nets/0/loads/0/pin");
        assert_eq!(first.core, second.core);
    }

    #[test]
    fn lowered_structural_limits_have_exact_boundaries() {
        let (mut design, architecture) = fixture();
        design.provenance.display = w::Nullable(Some("origin".into()));
        let mut limits = Limits::default();
        limits.core.max_declarations = 10;
        limits.core.max_references = 8;
        limits.core.max_collection = 2;
        limits.core.max_depth = 2;
        limits.core.max_key_component_bytes = 4;
        limits.core.max_key_bytes = 7;
        limits.core.max_provenance_bytes = 6;
        validate(&design, &architecture, &limits).unwrap();
        for which in 0..7 {
            let mut lowered = limits;
            match which {
                0 => lowered.core.max_declarations -= 1,
                1 => lowered.core.max_references -= 1,
                2 => lowered.core.max_collection -= 1,
                3 => lowered.core.max_depth -= 1,
                4 => lowered.core.max_key_component_bytes -= 1,
                5 => lowered.core.max_key_bytes -= 1,
                _ => lowered.core.max_provenance_bytes -= 1,
            }
            assert_eq!(
                validate(&design, &architecture, &lowered).unwrap_err().code,
                "limit"
            );
        }
        let mut low = 1;
        let mut high = limits.core.max_work;
        while low < high {
            let middle = low + (high - low) / 2;
            limits.core.max_work = middle;
            if validate(&design, &architecture, &limits).is_ok() {
                high = middle;
            } else {
                low = middle + 1;
            }
        }
        limits.core.max_work = high;
        validate(&design, &architecture, &limits).unwrap();
        limits.core.max_work -= 1;
        let error = validate(&design, &architecture, &limits).unwrap_err();
        assert_eq!(error.code, "limit");
        assert!(error.message.contains("work"));
    }
}
