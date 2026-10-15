use super::*;

pub(super) struct Report {
    pub(super) limits: ValidationLimits,
    pub(super) stage: Stage,
    pub(super) stats: ValidationStats,
    pub(super) errors: Diagnostics,
}
impl Report {
    pub(super) fn new(limits: ValidationLimits, stage: Stage) -> Checked<Self> {
        let ceiling = ValidationLimits::default();
        let pairs = [
            (limits.max_declarations, ceiling.max_declarations),
            (limits.max_references, ceiling.max_references),
            (limits.max_collection as u64, ceiling.max_collection as u64),
            (limits.max_depth as u64, ceiling.max_depth as u64),
            (
                limits.max_key_component_bytes as u64,
                ceiling.max_key_component_bytes as u64,
            ),
            (limits.max_key_bytes as u64, ceiling.max_key_bytes as u64),
            (
                limits.max_provenance_bytes as u64,
                ceiling.max_provenance_bytes as u64,
            ),
            (
                limits.max_diagnostics as u64,
                ceiling.max_diagnostics as u64,
            ),
            (limits.max_work, ceiling.max_work),
        ];
        if pairs
            .iter()
            .any(|(actual, max)| *actual == 0 || actual > max)
        {
            return Err(limit(
                stage,
                "caller limits must be positive and at most the documented ceiling",
                "safe defaults",
            ));
        }
        Ok(Self {
            limits,
            stage,
            stats: ValidationStats::default(),
            errors: vec![],
        })
    }
    pub(super) fn tick(&mut self, amount: u64) -> Checked<()> {
        self.stats.work = self
            .stats
            .work
            .checked_add(amount)
            .ok_or_else(|| limit(self.stage, "work", self.limits.max_work))?;
        if self.stats.work > self.limits.max_work {
            return Err(limit(self.stage, "work", self.limits.max_work));
        }
        Ok(())
    }
    pub(super) fn collection(&mut self, length: usize, reference: bool) -> Checked<()> {
        if length > self.limits.max_collection {
            return Err(limit(
                self.stage,
                "collection entries",
                self.limits.max_collection,
            ));
        }
        let count = u64::try_from(length)
            .map_err(|_| limit(self.stage, "collection entries", self.limits.max_collection))?;
        if reference {
            self.stats.references = self
                .stats
                .references
                .checked_add(count)
                .ok_or_else(|| limit(self.stage, "references", self.limits.max_references))?;
        } else {
            self.stats.declarations =
                self.stats.declarations.checked_add(count).ok_or_else(|| {
                    limit(self.stage, "declarations", self.limits.max_declarations)
                })?;
        }
        if self.stats.declarations > self.limits.max_declarations {
            return Err(limit(
                self.stage,
                "declarations",
                self.limits.max_declarations,
            ));
        }
        if self.stats.references > self.limits.max_references {
            return Err(limit(self.stage, "references", self.limits.max_references));
        }
        self.tick(count)
    }
    pub(super) fn emit(&mut self, mut error: Diagnostic) -> Checked<()> {
        error.related.sort();
        if self.errors.len() == self.limits.max_diagnostics {
            return Err(limit(
                self.stage,
                "diagnostics",
                self.limits.max_diagnostics,
            ));
        }
        self.errors.push(error);
        Ok(())
    }
    pub(super) fn name(&mut self, name: &Name) -> Checked<()> {
        self.tick(
            u64::try_from(name.as_str().len())
                .unwrap_or(u64::MAX)
                .saturating_add(1),
        )?;
        if name.as_str().len() > self.limits.max_key_component_bytes {
            return Err(limit(
                self.stage,
                "key component bytes",
                self.limits.max_key_component_bytes,
            ));
        }
        Ok(())
    }
    pub(super) fn path(&mut self, path: &[Name]) -> Checked<()> {
        if path.len() > self.limits.max_depth {
            return Err(limit(self.stage, "reference depth", self.limits.max_depth));
        }
        for part in path {
            self.name(part)?;
        }
        if path.iter().map(|p| p.as_str().len()).sum::<usize>() > self.limits.max_key_bytes {
            return Err(limit(self.stage, "key bytes", self.limits.max_key_bytes));
        }
        Ok(())
    }
    pub(super) fn key(&mut self, key: &SemanticKey) -> Checked<()> {
        self.name(key.namespace())?;
        self.path(key.scope())?;
        self.name(key.local())?;
        let bytes = key.namespace().as_str().len()
            + key.local().as_str().len()
            + key.scope().iter().map(|p| p.as_str().len()).sum::<usize>();
        if bytes > self.limits.max_key_bytes {
            return Err(limit(self.stage, "key bytes", self.limits.max_key_bytes));
        }
        Ok(())
    }
    pub(super) fn provenance(&mut self, p: &Provenance) -> Checked<()> {
        self.tick(1)?;
        if p.display()
            .is_some_and(|s| s.len() > self.limits.max_provenance_bytes)
            || p.span()
                .is_some_and(|s| s.source().len() > self.limits.max_provenance_bytes)
        {
            return Err(limit(
                self.stage,
                "provenance bytes",
                self.limits.max_provenance_bytes,
            ));
        }
        Ok(())
    }
    pub(super) fn resource_ref(&mut self, value: &ResourceRef) -> Checked<()> {
        self.collection(1, true)?;
        self.path(&value.path)?;
        self.name(&value.name)?;
        self.provenance(&value.provenance)
    }
    pub(super) fn field_ref(&mut self, value: &FieldRef) -> Checked<()> {
        self.collection(1, true)?;
        self.path(&value.path)?;
        self.name(&value.name)?;
        self.provenance(&value.provenance)
    }
    pub(super) fn domains(&mut self, values: &[DomainRef]) -> Checked<()> {
        self.collection(values.len(), true)?;
        for value in ordered(values) {
            self.key(&value.key.erase())?;
            self.provenance(&value.provenance)?;
        }
        Ok(())
    }
    pub(super) fn connection(&mut self, c: &Connection) -> Checked<()> {
        self.name(&c.name)?;
        self.provenance(&c.provenance)?;
        self.collection(c.sources.len(), true)?;
        for endpoint in c.sources.iter().chain(std::iter::once(&c.destination)) {
            self.resource_ref(&endpoint.resource)?;
            self.name(&endpoint.pin)?;
            self.provenance(&endpoint.provenance)?;
        }
        if let Some(reference) = &c.selector {
            self.field_ref(reference)?;
        }
        Ok(())
    }
    pub(super) fn instance(&mut self, i: &Instance) -> Checked<()> {
        self.name(&i.name)?;
        self.key(&i.template.erase())?;
        self.provenance(&i.provenance)?;
        self.collection(1, true)?;
        self.domains(&i.domains)
    }
}

pub(super) fn ordered<T: Ord>(values: &[T]) -> Vec<&T> {
    let mut result: Vec<_> = values.iter().collect();
    result.sort();
    result
}

pub(super) fn preflight(a: &Architecture, r: &mut Report) -> Checked<()> {
    r.name(&a.namespace)?;
    r.provenance(&a.provenance)?;
    for n in [
        a.resource_types.len(),
        a.templates.len(),
        a.roots.len(),
        a.partitions.len(),
        a.domains.len(),
        a.connections.len(),
    ] {
        r.collection(n, false)?;
    }
    for t in ordered(&a.resource_types) {
        r.key(&t.key.erase())?;
        r.provenance(&t.provenance)?;
        r.collection(t.pins.len(), false)?;
        r.collection(t.modes.len(), false)?;
        for p in &t.pins {
            r.name(&p.name)?;
            r.provenance(&p.provenance)?;
        }
        for m in ordered(&t.modes) {
            r.name(m)?;
        }
    }
    for d in ordered(&a.domains) {
        r.key(&d.key.erase())?;
        r.provenance(&d.provenance)?;
    }
    for t in ordered(&a.templates) {
        r.key(&t.key.erase())?;
        r.provenance(&t.provenance)?;
        for n in [
            t.resources.len(),
            t.children.len(),
            t.mode_groups.len(),
            t.storage.len(),
            t.features.len(),
            t.connections.len(),
        ] {
            r.collection(n, false)?;
        }
        for resource in ordered(&t.resources) {
            r.name(&resource.name)?;
            r.key(&resource.resource_type.erase())?;
            r.collection(1, true)?;
            r.provenance(&resource.provenance)?;
            r.domains(&resource.domains)?;
            if let Some(target) = &resource.alias_of {
                r.resource_ref(target)?;
            }
        }
        for child in ordered(&t.children) {
            r.instance(child)?;
        }
        for group in ordered(&t.mode_groups) {
            r.name(&group.name)?;
            r.provenance(&group.provenance)?;
            r.collection(group.resources.len(), true)?;
            r.collection(group.modes.len(), false)?;
            for resource in ordered(&group.resources) {
                r.resource_ref(resource)?;
            }
            for mode in ordered(&group.modes) {
                r.name(mode)?;
            }
        }
        for storage in ordered(&t.storage) {
            r.name(&storage.name)?;
            r.resource_ref(&storage.owner)?;
            r.provenance(&storage.provenance)?;
        }
        for feature in ordered(&t.features) {
            r.name(&feature.name)?;
            r.name(&feature.storage)?;
            r.resource_ref(&feature.owner)?;
            r.provenance(&feature.provenance)?;
            r.collection(feature.guard.len(), true)?;
            for choice in ordered(&feature.guard) {
                r.name(&choice.group)?;
                r.name(&choice.mode)?;
                r.provenance(&choice.provenance)?;
            }
            if let ValueDomain::Set(values) = &feature.domain {
                r.collection(values.len(), false)?;
            }
            if let Some(target) = &feature.alias_of {
                r.field_ref(target)?;
            }
        }
        for connection in ordered(&t.connections) {
            r.connection(connection)?;
        }
    }
    for root in ordered(&a.roots) {
        r.instance(root)?;
    }
    for c in ordered(&a.connections) {
        r.connection(c)?;
        let key = semantic_key(&a.namespace, &[], &c.name, ResourceKind::Pip).ok_or_else(|| {
            limit(
                r.stage,
                "architecture connection key",
                r.limits.max_key_bytes,
            )
        })?;
        r.key(&key)?;
    }
    Ok(())
}

/// Bound every nested collection before canonical comparisons can inspect it.
/// This first pass is allocation-free and uses only lengths, never nested Ord.
pub(super) fn shape_preflight(a: &Architecture, r: &mut Report) -> Checked<()> {
    let mut total = 0_u64;
    let maximum = r.limits.max_work;
    let failure = || {
        limit(
            r.stage,
            "nested input shape",
            format!(
                "collections <= {}, paths <= {}, total records <= {}",
                r.limits.max_collection, r.limits.max_depth, maximum
            ),
        )
    };
    let mut length = |n: usize, cap: usize| -> Checked<()> {
        if n > cap {
            return Err(failure());
        }
        total = total
            .checked_add(u64::try_from(n).map_err(|_| failure())?)
            .ok_or_else(failure)?;
        if total > maximum {
            return Err(failure());
        }
        Ok(())
    };
    let list = r.limits.max_collection;
    let depth = r.limits.max_depth;
    for n in [
        a.resource_types.len(),
        a.templates.len(),
        a.roots.len(),
        a.partitions.len(),
        a.domains.len(),
        a.connections.len(),
    ] {
        length(n, list)?;
    }
    for ty in &a.resource_types {
        length(ty.pins.len(), list)?;
        length(ty.modes.len(), list)?;
    }
    for root in &a.roots {
        length(root.domains.len(), list)?;
    }
    let check_connection = |connection: &Connection,
                            length: &mut dyn FnMut(usize, usize) -> Checked<()>|
     -> Checked<()> {
        length(connection.sources.len(), list)?;
        for endpoint in connection
            .sources
            .iter()
            .chain(std::iter::once(&connection.destination))
        {
            length(endpoint.resource.path.len(), depth)?;
        }
        if let Some(selector) = &connection.selector {
            length(selector.path.len(), depth)?;
        }
        Ok(())
    };
    for t in &a.templates {
        for n in [
            t.resources.len(),
            t.children.len(),
            t.mode_groups.len(),
            t.storage.len(),
            t.features.len(),
            t.connections.len(),
        ] {
            length(n, list)?;
        }
        for resource in &t.resources {
            length(resource.domains.len(), list)?;
            if let Some(alias) = &resource.alias_of {
                length(alias.path.len(), depth)?;
            }
        }
        for child in &t.children {
            length(child.domains.len(), list)?;
        }
        for group in &t.mode_groups {
            length(group.resources.len(), list)?;
            length(group.modes.len(), list)?;
            for resource in &group.resources {
                length(resource.path.len(), depth)?;
            }
        }
        for storage in &t.storage {
            length(storage.owner.path.len(), depth)?;
        }
        for feature in &t.features {
            length(feature.owner.path.len(), depth)?;
            length(feature.guard.len(), list)?;
            if let ValueDomain::Set(values) = &feature.domain {
                length(values.len(), list)?;
            }
            if let Some(alias) = &feature.alias_of {
                length(alias.path.len(), depth)?;
            }
        }
        for connection in &t.connections {
            check_connection(connection, &mut length)?;
        }
    }
    for connection in &a.connections {
        check_connection(connection, &mut length)?;
    }
    r.tick(total)
}
