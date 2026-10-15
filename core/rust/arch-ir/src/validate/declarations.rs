use super::*;

pub(super) fn hierarchy(c: &Context<'_>, r: &mut Report) -> Checked<()> {
    let mut indegree: BTreeMap<TemplateKey, usize> =
        c.index.templates.keys().map(|k| (k.clone(), 0)).collect();
    let mut depth: BTreeMap<TemplateKey, usize> =
        c.index.templates.keys().map(|k| (k.clone(), 1)).collect();
    for t in c.index.templates.values() {
        for child in &t.children {
            r.tick(1)?;
            if let Some(count) = indegree.get_mut(&child.template) {
                *count += 1;
            }
        }
    }
    let mut ready: BTreeSet<_> = indegree
        .iter()
        .filter(|(_, count)| **count == 0)
        .map(|(k, _)| k.clone())
        .collect();
    let mut visited = 0usize;
    while let Some(key) = ready.pop_first() {
        visited += 1;
        r.tick(1)?;
        let value = depth.get(&key).copied().unwrap_or(1);
        r.stats.hierarchy_depth = r.stats.hierarchy_depth.max(value);
        if value > r.limits.max_depth {
            return Err(limit(r.stage, "hierarchy depth", r.limits.max_depth));
        }
        if let Some(t) = c.index.templates.get(&key) {
            for child in &t.children {
                r.tick(1)?;
                if let Some(d) = depth.get_mut(&child.template) {
                    *d = (*d).max(value + 1);
                }
                if let Some(count) = indegree.get_mut(&child.template) {
                    *count -= 1;
                    if *count == 0 {
                        ready.insert(child.template.clone());
                    }
                }
            }
        }
    }
    if visited != c.index.templates.len() {
        report_cycle_witness(c, r)?;
    }
    Ok(())
}

pub(super) fn validate_instance(
    c: &Context<'_>,
    instance: &Instance,
    root: bool,
    r: &mut Report,
) -> Checked<()> {
    r.tick(1)?;
    if !c.index.templates.contains_key(&instance.template) {
        r.emit(
            diagnostic(
                Code::Missing,
                r.stage,
                "instance template does not exist",
                &instance.provenance,
            )
            .with_key(instance.template.erase()),
        )?;
    }
    if root && instance.partition.is_none() {
        r.emit(diagnostic(
            Code::PartitionMismatch,
            r.stage,
            "root instance needs an explicit partition",
            &instance.provenance,
        ))?;
    }
    if let Some(partition) = instance.partition {
        r.tick(u64::try_from(c.architecture.partitions.len()).unwrap_or(u64::MAX))?;
        if !c.architecture.partitions.contains(&partition) {
            r.emit(
                diagnostic(
                    Code::PartitionMismatch,
                    r.stage,
                    "instance partition is not declared",
                    &instance.provenance,
                )
                .with_actual(partition.get().to_string())
                .with_expected("a declared partition"),
            )?;
        }
    }
    c.domain_refs(&instance.domains, r)
}
pub(super) fn same_resource(a: &ResourceRef, b: &ResourceRef) -> bool {
    a.path == b.path && a.name == b.name && a.kind == b.kind
}
pub(super) fn owned_local(
    c: &Context<'_>,
    t: &Template,
    owner: &ResourceRef,
    r: &mut Report,
) -> Checked<()> {
    if !owner.path.is_empty() {
        r.emit(scoped_error(
            Code::WrongScope,
            "storage ownership must be template-local",
            t,
            &owner.name,
            owner.kind,
            &owner.provenance,
        ))?;
        return Ok(());
    }
    if let Some(resource) = c.local(t).and_then(|l| l.resources.get(&owner.name)) {
        if resource.kind != owner.kind {
            r.emit(scoped_error(
                Code::WrongKind,
                "owner kind mismatch",
                t,
                &owner.name,
                owner.kind,
                &owner.provenance,
            ))?;
        }
        if resource.alias_of.is_some() {
            r.emit(scoped_error(
                Code::AliasMismatch,
                "an alias cannot independently own storage",
                t,
                &owner.name,
                owner.kind,
                &owner.provenance,
            ))?;
        }
    } else {
        r.emit(scoped_error(
            Code::Missing,
            "owner does not exist",
            t,
            &owner.name,
            owner.kind,
            &owner.provenance,
        ))?;
    }
    Ok(())
}
pub(super) fn domain_contains(domain: &ValueDomain, value: u64) -> bool {
    match domain {
        ValueDomain::Any => true,
        ValueDomain::Range { minimum, maximum } => *minimum <= value && value <= *maximum,
        ValueDomain::Set(values) => values.contains(&value),
    }
}
pub(super) fn equal_domains(a: &ValueDomain, b: &ValueDomain) -> bool {
    match (a, b) {
        (ValueDomain::Set(a), ValueDomain::Set(b)) => {
            a.iter().copied().collect::<BTreeSet<_>>() == b.iter().copied().collect::<BTreeSet<_>>()
        }
        _ => a == b,
    }
}
pub(super) fn feature_domain(t: &Template, f: &Feature, r: &mut Report) -> Checked<()> {
    let valid = match &f.domain {
        ValueDomain::Any => true,
        ValueDomain::Range { minimum, maximum } => minimum <= maximum && f.width.fits(*maximum),
        ValueDomain::Set(values) => {
            r.tick(u64::try_from(values.len()).unwrap_or(u64::MAX))?;
            !values.is_empty()
                && values.iter().all(|v| f.width.fits(*v))
                && values.iter().collect::<BTreeSet<_>>().len() == values.len()
        }
    };
    if !valid {
        r.emit(scoped_error(
            Code::Domain,
            "feature domain is empty, duplicated or outside its width",
            t,
            &f.name,
            ResourceKind::Field,
            &f.provenance,
        ))?;
    }
    Ok(())
}

pub(super) fn alias_cycles(
    edges: &BTreeMap<Name, Name>,
    r: &mut Report,
) -> Checked<BTreeSet<Name>> {
    let mut finished = BTreeSet::new();
    let mut cycles = BTreeSet::new();
    for start in edges.keys() {
        let mut positions = BTreeMap::new();
        let mut path: Vec<Name> = Vec::new();
        let mut current = start.clone();
        while !finished.contains(&current) {
            r.tick(1)?;
            if let Some(position) = positions.get(&current).copied() {
                for name in path.iter().skip(position) {
                    cycles.insert(name.clone());
                }
                break;
            }
            positions.insert(current.clone(), path.len());
            path.push(current.clone());
            match edges.get(&current) {
                Some(next) => current = next.clone(),
                None => break,
            }
        }
        finished.extend(path);
    }
    Ok(cycles)
}
pub(super) fn check_template<'a>(c: &Context<'a>, t: &'a Template, r: &mut Report) -> Checked<()> {
    let Some(local) = c.local(t) else {
        return Ok(());
    };
    for (name, kind) in local
        .resources
        .values()
        .map(|v| (&v.name, v.kind))
        .chain(
            local
                .features
                .values()
                .map(|v| (&v.name, ResourceKind::Field)),
        )
        .chain(
            ordered(&t.connections)
                .into_iter()
                .map(|v| (&v.name, ResourceKind::Pip)),
        )
    {
        let key = definition_key(t, name, kind)
            .ok_or_else(|| limit(r.stage, "definition-qualified key", r.limits.max_key_bytes))?;
        r.key(&key)?;
    }
    for storage in local.storage.values() {
        let key = definition_aux_key::<nf_types::Storage>(t, &storage.name).ok_or_else(|| {
            limit(
                r.stage,
                "definition-qualified storage key",
                r.limits.max_key_bytes,
            )
        })?;
        r.key(&key)?;
    }
    for group in local.groups.values() {
        let key = definition_aux_key::<nf_types::ModeGroup>(t, &group.name).ok_or_else(|| {
            limit(
                r.stage,
                "definition-qualified mode-group key",
                r.limits.max_key_bytes,
            )
        })?;
        r.key(&key)?;
    }
    for feature in local.features.values() {
        if let Some(resource) = local
            .resources
            .get(&feature.name)
            .filter(|resource| resource.kind == ResourceKind::Field)
        {
            r.emit(
                scoped_error(
                    Code::Duplicate,
                    "resource and configuration feature share the same typed portable key",
                    t,
                    &feature.name,
                    ResourceKind::Field,
                    &feature.provenance,
                )
                .with_related(
                    resource.provenance.clone(),
                    definition_key(t, &resource.name, resource.kind),
                ),
            )?;
        }
    }
    for connection in ordered(&t.connections) {
        if let Some(resource) = local.resources.get(&connection.name)
            && resource.kind == ResourceKind::Pip
        {
            r.emit(
                scoped_error(
                    Code::Duplicate,
                    "resource and connection share the same typed portable key",
                    t,
                    &connection.name,
                    ResourceKind::Pip,
                    &connection.provenance,
                )
                .with_related(
                    resource.provenance.clone(),
                    definition_key(t, &resource.name, resource.kind),
                ),
            )?;
        }
    }
    check_resource_declarations(c, t, local, r)?;
    for child in local.children.values() {
        validate_instance(c, child, false, r)?;
    }
    check_modes_and_storage(c, t, local, r)?;
    check_feature_declarations(c, t, local, r)?;
    check_owner_overlaps(t, local, r)?;
    check_connections(c, Some(t), &t.connections, r)
}

fn check_resource_declarations<'a>(
    c: &Context<'a>,
    t: &'a Template,
    local: &Locals<'a>,
    r: &mut Report,
) -> Checked<()> {
    let resource_edges: BTreeMap<_, _> = local
        .resources
        .values()
        .filter_map(|v| {
            v.alias_of
                .as_ref()
                .filter(|a| a.path.is_empty())
                .map(|a| (v.name.clone(), a.name.clone()))
        })
        .collect();
    let resource_cycles = alias_cycles(&resource_edges, r)?;
    for resource in local.resources.values() {
        r.tick(1)?;
        if definition_key(t, &resource.name, resource.kind).is_none() {
            return Err(limit(
                r.stage,
                "definition-qualified key",
                r.limits.max_key_bytes,
            ));
        }
        match c.index.types.get(&resource.resource_type) {
            None => r.emit(
                scoped_error(
                    Code::Missing,
                    "resource type does not exist",
                    t,
                    &resource.name,
                    resource.kind,
                    &resource.provenance,
                )
                .with_related(
                    resource.provenance.clone(),
                    Some(resource.resource_type.erase()),
                ),
            )?,
            Some(ty) if ty.kind != resource.kind => r.emit(
                scoped_error(
                    Code::WrongKind,
                    "resource type kind mismatch",
                    t,
                    &resource.name,
                    resource.kind,
                    &resource.provenance,
                )
                .with_expected(format!("{:?}", ty.kind))
                .with_actual(format!("{:?}", resource.kind)),
            )?,
            Some(_) => (),
        }
        c.domain_refs(&resource.domains, r)?;
        if let Some(alias) = &resource.alias_of {
            if !alias.path.is_empty() {
                r.emit(scoped_error(
                    Code::WrongScope,
                    "resource aliases must name a local owner",
                    t,
                    &resource.name,
                    resource.kind,
                    &alias.provenance,
                ))?;
            } else if resource_cycles.contains(&resource.name) {
                r.emit(scoped_error(
                    Code::AliasCycle,
                    "resource alias cycle",
                    t,
                    &resource.name,
                    resource.kind,
                    &resource.provenance,
                ))?;
            } else if let Some(target) = local.resources.get(&alias.name) {
                if target.alias_of.is_some() {
                    r.emit(
                        scoped_error(
                            Code::AliasChain,
                            "resource alias must refer directly to an owner",
                            t,
                            &resource.name,
                            resource.kind,
                            &alias.provenance,
                        )
                        .with_related(
                            target.provenance.clone(),
                            definition_key(t, &target.name, target.kind),
                        ),
                    )?;
                }
                if alias.kind != target.kind
                    || resource.kind != target.kind
                    || resource.resource_type != target.resource_type
                {
                    r.emit(
                        scoped_error(
                            Code::AliasMismatch,
                            "resource alias type or kind differs from its owner",
                            t,
                            &resource.name,
                            resource.kind,
                            &resource.provenance,
                        )
                        .with_related(
                            target.provenance.clone(),
                            definition_key(t, &target.name, target.kind),
                        ),
                    )?;
                }
            } else {
                r.emit(scoped_error(
                    Code::Missing,
                    "resource alias owner does not exist",
                    t,
                    &resource.name,
                    resource.kind,
                    &alias.provenance,
                ))?;
            }
        }
    }
    Ok(())
}

fn check_modes_and_storage<'a>(
    c: &Context<'a>,
    t: &'a Template,
    local: &Locals<'a>,
    r: &mut Report,
) -> Checked<()> {
    let mut mode_owners: BTreeMap<Name, &ModeGroup> = BTreeMap::new();
    for group in local.groups.values() {
        r.tick(1)?;
        if group.resources.is_empty() || group.modes.is_empty() {
            r.emit(
                diagnostic(
                    Code::Mode,
                    r.stage,
                    "mode group requires resources and legal modes",
                    &group.provenance,
                )
                .with_key(t.key.erase()),
            )?;
        }
        for reference in ordered(&group.resources) {
            if !reference.path.is_empty() {
                r.emit(
                    diagnostic(
                        Code::WrongScope,
                        r.stage,
                        "mode groups refer only to local resources in this profile",
                        &reference.provenance,
                    )
                    .with_key(t.key.erase()),
                )?;
                continue;
            }
            if let Some((_, resource)) = c.resource(Some(t), reference, r)? {
                let canonical = resource
                    .alias_of
                    .as_ref()
                    .filter(|a| a.path.is_empty())
                    .map(|a| &a.name)
                    .unwrap_or(&resource.name);
                if let Some(previous) = mode_owners.insert(canonical.clone(), group) {
                    r.emit(scoped_error(Code::Mode, "resource belongs to multiple single-selection mode groups or appears twice", t, &resource.name, resource.kind, &group.provenance).with_related(previous.provenance.clone(), None))?;
                }
                if let Some(ty) = c.index.types.get(&resource.resource_type) {
                    for mode in ordered(&group.modes) {
                        r.tick(1)?;
                        r.tick(u64::try_from(ty.modes.len()).unwrap_or(u64::MAX))?;
                        if !ty.modes.contains(mode) {
                            r.emit(
                                scoped_error(
                                    Code::Mode,
                                    format!(
                                        "resource type does not support mode {}",
                                        mode.as_str()
                                    ),
                                    t,
                                    &resource.name,
                                    resource.kind,
                                    &group.provenance,
                                )
                                .with_related(ty.provenance.clone(), Some(ty.key.erase())),
                            )?;
                        }
                    }
                }
            }
        }
    }
    for storage in local.storage.values() {
        r.tick(1)?;
        owned_local(c, t, &storage.owner, r)?;
        if storage.bits.get() == 0 {
            let mut error = diagnostic(
                Code::Width,
                r.stage,
                "logical storage must have positive bit capacity",
                &storage.provenance,
            );
            error.key = definition_aux_key::<nf_types::Storage>(t, &storage.name);
            r.emit(error)?;
        }
    }
    Ok(())
}

fn check_feature_declarations<'a>(
    c: &Context<'a>,
    t: &'a Template,
    local: &Locals<'a>,
    r: &mut Report,
) -> Checked<()> {
    let feature_edges: BTreeMap<_, _> = local
        .features
        .values()
        .filter_map(|v| {
            v.alias_of
                .as_ref()
                .filter(|a| a.path.is_empty())
                .map(|a| (v.name.clone(), a.name.clone()))
        })
        .collect();
    let feature_cycles = alias_cycles(&feature_edges, r)?;
    for feature in local.features.values() {
        r.tick(1)?;
        if definition_key(t, &feature.name, ResourceKind::Field).is_none() {
            return Err(limit(
                r.stage,
                "definition-qualified key",
                r.limits.max_key_bytes,
            ));
        }
        owned_local(c, t, &feature.owner, r)?;
        if feature.range.length() != feature.width.bit_count() {
            r.emit(
                scoped_error(
                    Code::Width,
                    "feature slice length must equal its positive value width",
                    t,
                    &feature.name,
                    ResourceKind::Field,
                    &feature.provenance,
                )
                .with_actual(feature.range.length().get().to_string())
                .with_expected(feature.width.get().to_string()),
            )?;
        }
        match local.storage.get(&feature.storage) {
            None => r.emit(scoped_error(
                Code::Missing,
                "feature storage does not exist",
                t,
                &feature.name,
                ResourceKind::Field,
                &feature.provenance,
            ))?,
            Some(storage) => {
                if !same_resource(&feature.owner, &storage.owner) {
                    r.emit(
                        scoped_error(
                            Code::AliasMismatch,
                            "feature and storage owners differ",
                            t,
                            &feature.name,
                            ResourceKind::Field,
                            &feature.provenance,
                        )
                        .with_related(storage.provenance.clone(), None),
                    )?;
                }
                if feature.range.end().get() > storage.bits.get() {
                    r.emit(
                        scoped_error(
                            Code::Bounds,
                            "feature slice exceeds its logical storage",
                            t,
                            &feature.name,
                            ResourceKind::Field,
                            &feature.provenance,
                        )
                        .with_actual(feature.range.end().get().to_string())
                        .with_expected(storage.bits.get().to_string())
                        .with_related(storage.provenance.clone(), None),
                    )?;
                }
            }
        }
        feature_domain(t, feature, r)?;
        let mut choices: BTreeMap<&Name, &ModeChoice> = BTreeMap::new();
        let mut guard: Vec<_> = feature.guard.iter().collect();
        guard.sort_by_key(|choice| (&choice.group, &choice.mode, &choice.provenance));
        for choice in guard {
            r.tick(1)?;
            if let Some(previous) = choices.insert(&choice.group, choice) {
                let message = if previous.mode == choice.mode {
                    "guard repeats a mode group"
                } else {
                    "guard requires contradictory choices of one mode group"
                };
                r.emit(
                    scoped_error(
                        Code::Guard,
                        message,
                        t,
                        &feature.name,
                        ResourceKind::Field,
                        &choice.provenance,
                    )
                    .with_related(previous.provenance.clone(), Some(t.key.erase())),
                )?;
            }
            if let Some(group) = local.groups.get(&choice.group) {
                r.tick(u64::try_from(group.modes.len()).unwrap_or(u64::MAX))?;
            }
            match local.groups.get(&choice.group) {
                None => r.emit(scoped_error(
                    Code::Mode,
                    "guard mode group does not exist",
                    t,
                    &feature.name,
                    ResourceKind::Field,
                    &choice.provenance,
                ))?,
                Some(group) if !group.modes.contains(&choice.mode) => r.emit(
                    scoped_error(
                        Code::Mode,
                        "guard mode is not declared",
                        t,
                        &feature.name,
                        ResourceKind::Field,
                        &choice.provenance,
                    )
                    .with_related(group.provenance.clone(), None),
                )?,
                Some(_) => (),
            }
        }
        if let Some(alias) = &feature.alias_of {
            if !alias.path.is_empty() {
                r.emit(scoped_error(
                    Code::WrongScope,
                    "feature aliases must name a local owner",
                    t,
                    &feature.name,
                    ResourceKind::Field,
                    &alias.provenance,
                ))?;
            } else if feature_cycles.contains(&feature.name) {
                r.emit(scoped_error(
                    Code::AliasCycle,
                    "feature alias cycle",
                    t,
                    &feature.name,
                    ResourceKind::Field,
                    &feature.provenance,
                ))?;
            } else if let Some(target) = local.features.get(&alias.name) {
                if target.alias_of.is_some() {
                    r.emit(
                        scoped_error(
                            Code::AliasChain,
                            "feature alias must refer directly to an owning feature",
                            t,
                            &feature.name,
                            ResourceKind::Field,
                            &alias.provenance,
                        )
                        .with_related(
                            target.provenance.clone(),
                            definition_key(t, &target.name, ResourceKind::Field),
                        ),
                    )?;
                }
                for domain in [&feature.domain, &target.domain] {
                    if let ValueDomain::Set(values) = domain {
                        r.tick(u64::try_from(values.len()).unwrap_or(u64::MAX))?;
                    }
                }
                if feature.width != target.width
                    || feature.range != target.range
                    || feature.storage != target.storage
                    || !same_resource(&feature.owner, &target.owner)
                    || !equal_domains(&feature.domain, &target.domain)
                {
                    r.emit(
                        scoped_error(
                            Code::AliasMismatch,
                            "alias owner, storage, slice, width and domain must exactly match",
                            t,
                            &feature.name,
                            ResourceKind::Field,
                            &feature.provenance,
                        )
                        .with_related(
                            target.provenance.clone(),
                            definition_key(t, &target.name, ResourceKind::Field),
                        ),
                    )?;
                }
            } else {
                r.emit(scoped_error(
                    Code::Missing,
                    "feature alias owner does not exist",
                    t,
                    &feature.name,
                    ResourceKind::Field,
                    &alias.provenance,
                ))?;
            }
        }
    }
    Ok(())
}

fn check_owner_overlaps(t: &Template, local: &Locals<'_>, r: &mut Report) -> Checked<()> {
    // One sweep per storage. Only independently owning features participate;
    // direct aliases have already been checked for exact owner-class equality.
    let mut intervals: BTreeMap<&Name, Vec<&Feature>> = BTreeMap::new();
    for f in local.features.values().filter(|f| f.alias_of.is_none()) {
        intervals.entry(&f.storage).or_default().push(f);
    }
    for fields in intervals.values_mut() {
        fields.sort_by_key(|f| (f.range.start(), f.range.end(), &f.name));
        let mut furthest: Option<&Feature> = None;
        for f in fields.iter().copied() {
            r.tick(1)?;
            if let Some(previous) = furthest {
                if f.range.overlaps(previous.range) {
                    r.emit(
                        scoped_error(
                            Code::Overlap,
                            "independently owning features overlap without a declared alias",
                            t,
                            &f.name,
                            ResourceKind::Field,
                            &f.provenance,
                        )
                        .with_related(
                            previous.provenance.clone(),
                            definition_key(t, &previous.name, ResourceKind::Field),
                        ),
                    )?;
                }
                if f.range.end() > previous.range.end() {
                    furthest = Some(f);
                }
            } else {
                furthest = Some(f);
            }
        }
    }
    Ok(())
}

// A Kahn remainder can contain acyclic descendants. Use a bounded iterative DFS
// only on rejection to identify an actual back edge and preserve both origins.
fn report_cycle_witness(c: &Context<'_>, r: &mut Report) -> Checked<()> {
    let mut color: BTreeMap<TemplateKey, u8> = BTreeMap::new();
    for start in c.index.templates.keys() {
        if color.get(start).copied().unwrap_or(0) != 0 {
            continue;
        }
        let mut stack = vec![(start.clone(), None::<(TemplateKey, &Provenance)>, false)];
        while let Some((key, parent, leaving)) = stack.pop() {
            r.tick(1)?;
            if leaving {
                color.insert(key, 2);
                continue;
            }
            match color.get(&key).copied().unwrap_or(0) {
                2 => continue,
                1 => {
                    if let Some((parent, edge_origin)) = parent {
                        let source = c.index.templates.get(&parent);
                        let target = c.index.templates.get(&key);
                        if let (Some(source), Some(target)) = (source, target) {
                            r.emit(
                                diagnostic(
                                    Code::TemplateCycle,
                                    r.stage,
                                    "recursive template instantiation is unsupported",
                                    edge_origin,
                                )
                                .with_key(parent.erase())
                                .with_related(source.provenance.clone(), Some(parent.erase()))
                                .with_related(target.provenance.clone(), Some(key.erase())),
                            )?;
                        }
                    }
                    return Ok(());
                }
                _ => (),
            }
            color.insert(key.clone(), 1);
            stack.push((key.clone(), None, true));
            if let Some(local) = c.locals.get(&key) {
                for child in local.children.values().rev() {
                    r.tick(1)?;
                    if c.index.templates.contains_key(&child.template) {
                        stack.push((
                            child.template.clone(),
                            Some((key.clone(), &child.provenance)),
                            false,
                        ));
                    }
                }
            }
        }
    }
    Ok(())
}
