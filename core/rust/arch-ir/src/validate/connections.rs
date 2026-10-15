use super::*;

pub(super) fn mux_domain(f: &Feature, source_count: usize) -> bool {
    let Ok(last) = u64::try_from(source_count.saturating_sub(1)) else {
        return false;
    };
    match &f.domain {
        ValueDomain::Any => {
            f.width.get() < 64
                && (1_u64 << f.width.get()) == u64::try_from(source_count).unwrap_or(u64::MAX)
        }
        ValueDomain::Range { minimum, maximum } => *minimum == 0 && *maximum == last,
        ValueDomain::Set(values) => {
            values.len() == source_count
                && values
                    .iter()
                    .copied()
                    .collect::<BTreeSet<_>>()
                    .iter()
                    .copied()
                    .eq(0..=last)
        }
    }
}
pub(super) fn check_connections<'a>(
    c: &Context<'a>,
    initial: Option<&'a Template>,
    connections: &[Connection],
    r: &mut Report,
) -> Checked<()> {
    let ordered: BTreeMap<_, _> = connections.iter().map(|v| (&v.name, v)).collect();
    let mut destinations = BTreeMap::new();
    for connection in ordered.values() {
        r.tick(1)?;
        let destination = &connection.destination;
        // Resource aliases resolve to the same physical endpoint for contention.
        let owner_name = c
            .resource(initial, &destination.resource, r)?
            .map(|(_, resource)| {
                resource
                    .alias_of
                    .as_ref()
                    .map(|a| a.name.clone())
                    .unwrap_or_else(|| resource.name.clone())
            });
        if let Some(owner) = owner_name {
            let key = (
                destination.resource.path.clone(),
                owner,
                destination.pin.clone(),
            );
            if let Some(previous) = destinations.insert(key, *connection) {
                r.emit(
                    diagnostic(
                        Code::Connection,
                        r.stage,
                        "multiple declarations drive the same destination",
                        &connection.provenance,
                    )
                    .with_related(previous.provenance.clone(), None),
                )?;
            }
        }
        let destination_width = c.endpoint(initial, destination, Direction::Input, r)?;
        for source in &connection.sources {
            if let (Some(a), Some(b)) = (
                c.endpoint(initial, source, Direction::Output, r)?,
                destination_width,
            ) && a != b
            {
                r.emit(
                    diagnostic(
                        Code::Width,
                        r.stage,
                        "connection endpoint widths differ",
                        &source.provenance,
                    )
                    .with_actual(a.get().to_string())
                    .with_expected(b.get().to_string())
                    .with_related(destination.provenance.clone(), None),
                )?;
            }
        }
        match (&connection.selector, connection.sources.len()) {
            (None, 1) => (),
            (Some(reference), count) if count >= 2 => {
                if let Some((t, feature)) = c.field(initial, reference, r)? {
                    if let ValueDomain::Set(values) = &feature.domain {
                        r.tick(u64::try_from(values.len()).unwrap_or(u64::MAX))?;
                    }
                    if !mux_domain(feature, count) {
                        r.emit(
                            scoped_error(
                                Code::Domain,
                                "mux selector domain must be exactly its ordered source indexes",
                                t,
                                &feature.name,
                                ResourceKind::Field,
                                &reference.provenance,
                            )
                            .with_expected(format!("0..{}", count - 1)),
                        )?;
                    }
                    if !feature.guard.is_empty() {
                        r.emit(scoped_error(
                            Code::Guard,
                            "an always-present mux requires an unguarded selector name",
                            t,
                            &feature.name,
                            ResourceKind::Field,
                            &reference.provenance,
                        ))?;
                    }
                }
            }
            _ => r.emit(diagnostic(
                Code::Connection,
                r.stage,
                "use one source without a selector, or two or more ordered sources with a selector",
                &connection.provenance,
            ))?,
        }
    }
    Ok(())
}

/// Transient ownership constraints only: no flattened resources or edges are
/// constructed or retained. This catches drivers declared across scope boundaries.
pub(super) fn check_qualified_connections<'a>(c: &Context<'a>, r: &mut Report) -> Checked<()> {
    type EndpointIdentity = (Vec<Name>, Name, Name);
    let mut destinations: BTreeMap<EndpointIdentity, (&Provenance, Option<SemanticKey>)> =
        BTreeMap::new();
    let mut inspect = |prefix: &[Name],
                       initial: Option<&'a Template>,
                       connections: &'a [Connection],
                       r: &mut Report|
     -> Checked<()> {
        let ordered: BTreeMap<_, _> = connections
            .iter()
            .map(|connection| (&connection.name, connection))
            .collect();
        for connection in ordered.values() {
            r.tick(1)?;
            let endpoint = &connection.destination;
            if let Some((_, resource)) = c.resource(initial, &endpoint.resource, r)? {
                let mut path = prefix.to_vec();
                path.extend(endpoint.resource.path.iter().cloned());
                r.path(&path)?;
                let owner = resource
                    .alias_of
                    .as_ref()
                    .map(|a| &a.name)
                    .unwrap_or(&resource.name);
                let scope: Vec<_> = path.iter().map(|n| n.as_str().to_owned()).collect();
                let key = semantic_key(&c.architecture.namespace, &scope, owner, resource.kind);
                if let Some(ref key) = key {
                    r.key(key)?;
                } else {
                    return Err(limit(
                        r.stage,
                        "instance-qualified key",
                        r.limits.max_key_bytes,
                    ));
                }
                let identity = (path, owner.clone(), endpoint.pin.clone());
                if let Some((previous, previous_key)) = destinations.get(&identity) {
                    let mut error = diagnostic(
                        Code::Connection,
                        r.stage,
                        "different hierarchy scopes drive the same physical destination",
                        &connection.provenance,
                    )
                    .with_related((*previous).clone(), previous_key.clone());
                    error.key = key;
                    r.emit(error)?;
                } else {
                    destinations.insert(identity, (&connection.provenance, key));
                }
            }
        }
        Ok(())
    };
    inspect(&[], None, &c.architecture.connections, r)?;
    walk_instances(c, r, |path, template, r| {
        inspect(path, Some(template), &template.connections, r)
    })
}
