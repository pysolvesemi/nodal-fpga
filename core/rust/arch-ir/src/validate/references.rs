use super::*;

#[derive(Default)]
pub(super) struct Index<'a> {
    pub(super) types: BTreeMap<TypeKey, &'a ResourceType>,
    pub(super) templates: BTreeMap<TemplateKey, &'a Template>,
    pub(super) domains: BTreeMap<DomainKey, &'a Domain>,
}
pub(super) fn duplicate(
    r: &mut Report,
    key: Option<SemanticKey>,
    name: &str,
    p: &Provenance,
    other: &Provenance,
) -> Checked<()> {
    let mut d = diagnostic(
        Code::Duplicate,
        r.stage,
        format!("duplicate declaration: {name}"),
        p,
    );
    d.key = key.clone();
    r.emit(d.with_related(other.clone(), key))
}
pub(super) fn unique_names<'a>(
    r: &mut Report,
    names: impl Iterator<Item = (&'a Name, &'a Provenance)>,
    key: Option<SemanticKey>,
) -> Checked<()> {
    unique_keyed_names(r, names, |_| key.clone())
}
fn unique_keyed_names<'a>(
    r: &mut Report,
    names: impl Iterator<Item = (&'a Name, &'a Provenance)>,
    key: impl Fn(&Name) -> Option<SemanticKey>,
) -> Checked<()> {
    let mut groups: BTreeMap<&Name, Vec<&Provenance>> = BTreeMap::new();
    for (name, provenance) in names {
        r.tick(1)?;
        groups.entry(name).or_default().push(provenance);
    }
    for (name, mut sources) in groups {
        if sources.len() > 1 {
            sources.sort();
            for (i, p) in sources.iter().enumerate() {
                let other = sources.get((i + 1) % sources.len()).copied().unwrap_or(p);
                duplicate(r, key(name), name.as_str(), p, other)?;
            }
        }
    }
    Ok(())
}
pub(super) fn indexes<'a>(a: &'a Architecture, r: &mut Report) -> Checked<Index<'a>> {
    let mut index = Index::default();
    let mut types: BTreeMap<_, Vec<_>> = BTreeMap::new();
    let mut templates: BTreeMap<_, Vec<_>> = BTreeMap::new();
    let mut domains: BTreeMap<_, Vec<_>> = BTreeMap::new();
    for v in &a.resource_types {
        r.tick(1)?;
        types.entry(v.key.clone()).or_default().push(v);
    }
    for v in &a.templates {
        r.tick(1)?;
        templates.entry(v.key.clone()).or_default().push(v);
    }
    for v in &a.domains {
        r.tick(1)?;
        domains.entry(v.key.clone()).or_default().push(v);
    }
    for (key, mut values) in types {
        if values.len() != 1 {
            values.sort_by_key(|v| &v.provenance);
            for (i, v) in values.iter().enumerate() {
                let other = values
                    .get((i + 1) % values.len())
                    .map(|v| &v.provenance)
                    .unwrap_or(&v.provenance);
                duplicate(
                    r,
                    Some(key.erase()),
                    key.local().as_str(),
                    &v.provenance,
                    other,
                )?;
            }
        } else if let Some(v) = values.first() {
            index.types.insert(key, *v);
        }
    }
    for (key, mut values) in templates {
        if values.len() != 1 {
            values.sort_by_key(|v| &v.provenance);
            for (i, v) in values.iter().enumerate() {
                let other = values
                    .get((i + 1) % values.len())
                    .map(|v| &v.provenance)
                    .unwrap_or(&v.provenance);
                duplicate(
                    r,
                    Some(key.erase()),
                    key.local().as_str(),
                    &v.provenance,
                    other,
                )?;
            }
        } else if let Some(v) = values.first() {
            index.templates.insert(key, *v);
        }
    }
    for (key, mut values) in domains {
        if values.len() != 1 {
            values.sort_by_key(|v| &v.provenance);
            for (i, v) in values.iter().enumerate() {
                let other = values
                    .get((i + 1) % values.len())
                    .map(|v| &v.provenance)
                    .unwrap_or(&v.provenance);
                duplicate(
                    r,
                    Some(key.erase()),
                    key.local().as_str(),
                    &v.provenance,
                    other,
                )?;
            }
        } else if let Some(v) = values.first() {
            index.domains.insert(key, *v);
        }
    }
    Ok(index)
}
pub(super) fn definition_key(t: &Template, name: &Name, kind: ResourceKind) -> Option<SemanticKey> {
    let mut scope: Vec<String> = t
        .key
        .scope()
        .iter()
        .map(|n| n.as_str().to_owned())
        .collect();
    scope.push(t.key.local().as_str().to_owned());
    semantic_key(t.key.namespace(), &scope, name, kind)
}
pub(super) fn definition_aux_key<K: nf_types::ResourceMarker>(
    t: &Template,
    name: &Name,
) -> Option<SemanticKey> {
    let mut scope: Vec<_> = t
        .key
        .scope()
        .iter()
        .map(|n| n.as_str().to_owned())
        .collect();
    scope.push(t.key.local().as_str().to_owned());
    Key::<K>::new(t.key.namespace().as_str(), scope, name.as_str())
        .ok()
        .map(|key| key.erase())
}
pub(super) fn absolute_group_key(
    a: &Architecture,
    path: &[Name],
    name: &Name,
) -> Option<SemanticKey> {
    Key::<nf_types::ModeGroup>::new(
        a.namespace.as_str(),
        path.iter().map(|n| n.as_str().to_owned()).collect(),
        name.as_str(),
    )
    .ok()
    .map(|key| key.erase())
}

pub(super) fn semantic_key(
    namespace: &Name,
    scope: &[String],
    name: &Name,
    kind: ResourceKind,
) -> Option<SemanticKey> {
    macro_rules! key {
        ($marker:ty) => {
            Key::<$marker>::new(namespace.as_str(), scope.to_vec(), name.as_str())
                .ok()
                .map(|k| k.erase())
        };
    }
    match kind {
        ResourceKind::Wire => key!(nf_types::Wire),
        ResourceKind::Pip => key!(nf_types::Pip),
        ResourceKind::Bel => key!(nf_types::Bel),
        ResourceKind::Pin => key!(nf_types::Pin),
        ResourceKind::Node => key!(nf_types::Node),
        ResourceKind::Site => key!(nf_types::Site),
        ResourceKind::Field => key!(nf_types::Field),
    }
}
pub(super) fn scoped_error(
    code: Code,
    message: impl Into<String>,
    t: &Template,
    name: &Name,
    kind: ResourceKind,
    p: &Provenance,
) -> Diagnostic {
    let mut d = diagnostic(code, Stage::Architecture, message, p);
    d.key = definition_key(t, name, kind);
    d
}

#[derive(Default)]
pub(super) struct Locals<'a> {
    pub(super) resources: BTreeMap<Name, &'a Resource>,
    pub(super) children: BTreeMap<Name, &'a Instance>,
    pub(super) groups: BTreeMap<Name, &'a ModeGroup>,
    pub(super) storage: BTreeMap<Name, &'a Storage>,
    pub(super) features: BTreeMap<Name, &'a Feature>,
}
pub(super) struct Context<'a> {
    pub(super) architecture: &'a Architecture,
    pub(super) index: Index<'a>,
    pub(super) locals: BTreeMap<TemplateKey, Locals<'a>>,
    pub(super) roots: BTreeMap<Name, &'a Instance>,
}
impl<'a> Context<'a> {
    pub(super) fn new(a: &'a Architecture, r: &mut Report) -> Checked<Self> {
        let index = indexes(a, r)?;
        unique_names(r, a.roots.iter().map(|v| (&v.name, &v.provenance)), None)?;
        let mut partitions = BTreeSet::new();
        for p in &a.partitions {
            if !partitions.insert(*p) {
                r.emit(diagnostic(
                    Code::Duplicate,
                    r.stage,
                    format!("duplicate partition {}", p.get()),
                    &a.provenance,
                ))?;
            }
        }
        for ty in index.types.values() {
            unique_names(
                r,
                ty.pins.iter().map(|v| (&v.name, &v.provenance)),
                Some(ty.key.erase()),
            )?;
            unique_names(
                r,
                ty.modes.iter().map(|v| (v, &ty.provenance)),
                Some(ty.key.erase()),
            )?;
        }
        let mut locals = BTreeMap::new();
        for t in index.templates.values() {
            let k = Some(t.key.erase());
            unique_names(
                r,
                t.resources.iter().map(|v| (&v.name, &v.provenance)),
                k.clone(),
            )?;
            unique_names(
                r,
                t.children.iter().map(|v| (&v.name, &v.provenance)),
                k.clone(),
            )?;
            unique_keyed_names(
                r,
                t.mode_groups.iter().map(|v| (&v.name, &v.provenance)),
                |name| definition_aux_key::<nf_types::ModeGroup>(t, name),
            )?;
            unique_keyed_names(
                r,
                t.storage.iter().map(|v| (&v.name, &v.provenance)),
                |name| definition_aux_key::<nf_types::Storage>(t, name),
            )?;
            unique_keyed_names(
                r,
                t.features.iter().map(|v| (&v.name, &v.provenance)),
                |name| definition_key(t, name, ResourceKind::Field),
            )?;
            unique_keyed_names(
                r,
                t.connections.iter().map(|v| (&v.name, &v.provenance)),
                |name| definition_key(t, name, ResourceKind::Pip),
            )?;
            for g in ordered(&t.mode_groups) {
                unique_names(r, g.modes.iter().map(|v| (v, &g.provenance)), k.clone())?;
            }
            locals.insert(
                t.key.clone(),
                Locals {
                    resources: t.resources.iter().map(|v| (v.name.clone(), v)).collect(),
                    children: t.children.iter().map(|v| (v.name.clone(), v)).collect(),
                    groups: t.mode_groups.iter().map(|v| (v.name.clone(), v)).collect(),
                    storage: t.storage.iter().map(|v| (v.name.clone(), v)).collect(),
                    features: t.features.iter().map(|v| (v.name.clone(), v)).collect(),
                },
            );
        }
        unique_keyed_names(
            r,
            a.connections.iter().map(|v| (&v.name, &v.provenance)),
            |name| semantic_key(&a.namespace, &[], name, ResourceKind::Pip),
        )?;
        Ok(Self {
            architecture: a,
            index,
            locals,
            roots: a.roots.iter().map(|v| (v.name.clone(), v)).collect(),
        })
    }
    pub(super) fn local(&self, t: &Template) -> Option<&Locals<'a>> {
        self.locals.get(&t.key)
    }
    pub(super) fn template_at(
        &self,
        initial: Option<&'a Template>,
        path: &[Name],
        p: &Provenance,
        r: &mut Report,
    ) -> Checked<Option<&'a Template>> {
        let mut current = initial;
        for step in path {
            r.tick(1)?;
            let instance = match current {
                Some(t) => self.local(t).and_then(|l| l.children.get(step).copied()),
                None => self.roots.get(step).copied(),
            };
            let Some(instance) = instance else {
                r.emit(diagnostic(
                    Code::Missing,
                    r.stage,
                    format!("instance path component {} does not exist", step.as_str()),
                    p,
                ))?;
                return Ok(None);
            };
            let Some(t) = self.index.templates.get(&instance.template).copied() else {
                r.emit(
                    diagnostic(
                        Code::Missing,
                        r.stage,
                        "instance template does not exist",
                        &instance.provenance,
                    )
                    .with_key(instance.template.erase()),
                )?;
                return Ok(None);
            };
            current = Some(t);
        }
        if current.is_none() {
            r.emit(diagnostic(
                Code::WrongScope,
                r.stage,
                "architecture-level reference requires a root instance path",
                p,
            ))?;
        }
        Ok(current)
    }
    pub(super) fn resource(
        &self,
        initial: Option<&'a Template>,
        reference: &ResourceRef,
        r: &mut Report,
    ) -> Checked<Option<(&'a Template, &'a Resource)>> {
        let Some(t) = self.template_at(initial, &reference.path, &reference.provenance, r)? else {
            return Ok(None);
        };
        r.tick(1)?;
        let Some(resource) = self
            .local(t)
            .and_then(|l| l.resources.get(&reference.name).copied())
        else {
            r.emit(scoped_error(
                Code::Missing,
                "resource reference does not exist",
                t,
                &reference.name,
                reference.kind,
                &reference.provenance,
            ))?;
            return Ok(None);
        };
        if resource.kind != reference.kind {
            r.emit(
                scoped_error(
                    Code::WrongKind,
                    "resource reference kind differs from declaration",
                    t,
                    &reference.name,
                    reference.kind,
                    &reference.provenance,
                )
                .with_actual(format!("{:?}", reference.kind))
                .with_expected(format!("{:?}", resource.kind))
                .with_related(
                    resource.provenance.clone(),
                    definition_key(t, &resource.name, resource.kind),
                ),
            )?;
            return Ok(None);
        }
        Ok(Some((t, resource)))
    }
    pub(super) fn field(
        &self,
        initial: Option<&'a Template>,
        reference: &FieldRef,
        r: &mut Report,
    ) -> Checked<Option<(&'a Template, &'a Feature)>> {
        let Some(t) = self.template_at(initial, &reference.path, &reference.provenance, r)? else {
            return Ok(None);
        };
        r.tick(1)?;
        let Some(feature) = self
            .local(t)
            .and_then(|l| l.features.get(&reference.name).copied())
        else {
            let mut error = scoped_error(
                Code::Missing,
                "feature reference does not exist",
                t,
                &reference.name,
                ResourceKind::Field,
                &reference.provenance,
            );
            error.stage = r.stage;
            if r.stage == Stage::Selection {
                error.key = absolute_field_key(self.architecture, &reference.path, &reference.name);
            }
            r.emit(error)?;
            return Ok(None);
        };
        Ok(Some((t, feature)))
    }
    pub(super) fn endpoint(
        &self,
        initial: Option<&'a Template>,
        e: &Endpoint,
        wanted: Direction,
        r: &mut Report,
    ) -> Checked<Option<BitCount>> {
        let Some((t, resource)) = self.resource(initial, &e.resource, r)? else {
            return Ok(None);
        };
        let Some(ty) = self.index.types.get(&resource.resource_type) else {
            return Ok(None);
        };
        r.tick(u64::try_from(ty.pins.len()).unwrap_or(u64::MAX))?;
        let Some(pin) = ty.pins.iter().find(|p| p.name == e.pin) else {
            r.emit(scoped_error(
                Code::Missing,
                format!("pin {} does not exist", e.pin.as_str()),
                t,
                &resource.name,
                resource.kind,
                &e.provenance,
            ))?;
            return Ok(None);
        };
        if pin.direction != wanted {
            r.emit(
                scoped_error(
                    Code::Direction,
                    "connection endpoint direction mismatch",
                    t,
                    &resource.name,
                    resource.kind,
                    &e.provenance,
                )
                .with_actual(format!("{:?}", pin.direction))
                .with_expected(format!("{wanted:?}"))
                .with_related(pin.provenance.clone(), None),
            )?;
        }
        Ok(Some(pin.width))
    }
    pub(super) fn domain_refs(&self, values: &[DomainRef], r: &mut Report) -> Checked<()> {
        let mut seen: BTreeMap<DomainKey, &DomainRef> = BTreeMap::new();
        let mut ordered: Vec<_> = values.iter().collect();
        ordered.sort_by_key(|d| (&d.key, d.kind, &d.provenance));
        for d in ordered {
            r.tick(1)?;
            if let Some(previous) = seen.insert(d.key.clone(), d) {
                r.emit(
                    diagnostic(
                        Code::Duplicate,
                        r.stage,
                        "duplicate domain membership",
                        &d.provenance,
                    )
                    .with_key(d.key.erase())
                    .with_related(previous.provenance.clone(), Some(previous.key.erase())),
                )?;
            }
            match self.index.domains.get(&d.key) {
                None => r.emit(
                    diagnostic(
                        Code::Missing,
                        r.stage,
                        "domain does not exist",
                        &d.provenance,
                    )
                    .with_key(d.key.erase()),
                )?,
                Some(target) if target.kind != d.kind => r.emit(
                    diagnostic(
                        Code::WrongKind,
                        r.stage,
                        "domain kind mismatch",
                        &d.provenance,
                    )
                    .with_key(d.key.erase())
                    .with_actual(format!("{:?}", d.kind))
                    .with_expected(format!("{:?}", target.kind))
                    .with_related(target.provenance.clone(), Some(target.key.erase())),
                )?,
                Some(_) => (),
            }
        }
        Ok(())
    }
}

pub(super) fn walk_instances<'a>(
    c: &Context<'a>,
    r: &mut Report,
    mut visit: impl FnMut(&[Name], &'a Template, &mut Report) -> Checked<()>,
) -> Checked<()> {
    let mut stack = Vec::new();
    for root in c.roots.values().rev() {
        r.tick(
            u64::try_from(root.name.as_str().len())
                .unwrap_or(u64::MAX)
                .saturating_add(1),
        )?;
        if let Some(t) = c.index.templates.get(&root.template) {
            stack.push((vec![root.name.clone()], *t));
        }
    }
    let mut occurrences = 0_u64;
    while let Some((path, t)) = stack.pop() {
        r.tick(1)?;
        occurrences += 1;
        if occurrences > r.limits.max_declarations {
            return Err(limit(
                r.stage,
                "instance occurrences",
                r.limits.max_declarations,
            ));
        }
        r.path(&path)?;
        if let Some(local) = c.local(t) {
            for name in local
                .resources
                .values()
                .map(|v| &v.name)
                .chain(local.features.values().map(|v| &v.name))
                .chain(local.storage.values().map(|v| &v.name))
                .chain(local.groups.values().map(|v| &v.name))
                .chain(ordered(&t.connections).into_iter().map(|v| &v.name))
            {
                r.tick(1)?;
                let bytes = c.architecture.namespace.as_str().len()
                    + name.as_str().len()
                    + path.iter().map(|n| n.as_str().len()).sum::<usize>();
                if bytes > r.limits.max_key_bytes {
                    return Err(limit(
                        r.stage,
                        "instance-qualified key bytes",
                        r.limits.max_key_bytes,
                    ));
                }
            }
            visit(&path, t, r)?;
            for child in local.children.values().rev() {
                if let Some(target) = c.index.templates.get(&child.template) {
                    r.tick(
                        u64::try_from(
                            path.iter().map(|n| n.as_str().len() + 1).sum::<usize>()
                                + child.name.as_str().len()
                                + 1,
                        )
                        .unwrap_or(u64::MAX),
                    )?;
                    let mut child_path = path.clone();
                    child_path.push(child.name.clone());
                    // Stack growth is bounded by declared edges and the charged occurrence budget.
                    if stack.len() >= r.limits.max_declarations as usize {
                        return Err(limit(
                            r.stage,
                            "pending instance occurrences",
                            r.limits.max_declarations,
                        ));
                    }
                    stack.push((child_path, *target));
                }
            }
        }
    }
    Ok(())
}
pub(super) fn absolute_field_key(
    a: &Architecture,
    path: &[Name],
    name: &Name,
) -> Option<SemanticKey> {
    let scope: Vec<_> = path.iter().map(|n| n.as_str().to_owned()).collect();
    semantic_key(&a.namespace, &scope, name, ResourceKind::Field)
}
