use super::*;

fn selection_error(
    a: &Architecture,
    code: Code,
    path: &[Name],
    name: &Name,
    p: &Provenance,
    message: &str,
) -> Diagnostic {
    let mut d = diagnostic(code, Stage::Selection, message, p);
    d.key = absolute_field_key(a, path, name);
    d
}

pub(super) fn selection_group_error(
    a: &Architecture,
    code: Code,
    path: &[Name],
    name: &Name,
    p: &Provenance,
    message: &str,
) -> Diagnostic {
    let mut d = diagnostic(code, Stage::Selection, message, p);
    d.key = absolute_group_key(a, path, name);
    d
}

/// Check a complete transient selection. At least one active name writes each
/// active storage-owner class; no value is inferred for omitted fields.
pub fn validate_selection(
    validated: &ValidatedArchitecture<'_>,
    selection: &Selection,
) -> Result<(), Diagnostics> {
    let result = (|| -> Checked<Report> {
        let a = validated.architecture;
        let mut r = Report::new(validated.limits, Stage::Selection)?;
        r.collection(selection.modes.len(), true)?;
        r.collection(selection.features.len(), true)?;
        // Public path vectors are length-checked before derived comparison.
        for path in selection
            .modes
            .iter()
            .map(|s| &s.path)
            .chain(selection.features.iter().map(|s| &s.field.path))
        {
            if path.len() > r.limits.max_depth {
                return Err(limit(r.stage, "reference depth", r.limits.max_depth));
            }
        }
        for s in ordered(&selection.modes) {
            r.path(&s.path)?;
            r.name(&s.group)?;
            r.name(&s.mode)?;
            r.provenance(&s.provenance)?;
        }
        for s in ordered(&selection.features) {
            r.field_ref(&s.field)?;
            r.provenance(&s.provenance)?;
        }
        let c = Context::new(a, &mut r)?;
        let mut choices: BTreeMap<(Vec<Name>, Name), &ModeSetting> = BTreeMap::new();
        let mut ordered_modes: Vec<_> = selection.modes.iter().collect();
        ordered_modes.sort_by_key(|s| (&s.path, &s.group, &s.mode, &s.provenance));
        for setting in ordered_modes {
            let Some(t) = c.template_at(None, &setting.path, &setting.provenance, &mut r)? else {
                continue;
            };
            let Some(group) = c
                .local(t)
                .and_then(|l| l.groups.get(&setting.group).copied())
            else {
                r.emit(selection_group_error(
                    a,
                    Code::Mode,
                    &setting.path,
                    &setting.group,
                    &setting.provenance,
                    "selected mode group does not exist",
                ))?;
                continue;
            };
            r.tick(u64::try_from(group.modes.len()).unwrap_or(u64::MAX))?;
            if !group.modes.contains(&setting.mode) {
                r.emit(
                    selection_group_error(
                        a,
                        Code::Mode,
                        &setting.path,
                        &setting.group,
                        &setting.provenance,
                        "selected mode is not legal for this group",
                    )
                    .with_actual(setting.mode.as_str())
                    .with_related(group.provenance.clone(), Some(t.key.erase())),
                )?;
                continue;
            }
            let key = (setting.path.clone(), setting.group.clone());
            if let Some(previous) = choices.get(&key) {
                r.emit(
                    selection_group_error(
                        a,
                        Code::Mode,
                        &setting.path,
                        &setting.group,
                        &setting.provenance,
                        "single-selection group has multiple supplied choices",
                    )
                    .with_related(
                        previous.provenance.clone(),
                        absolute_group_key(a, &previous.path, &previous.group),
                    ),
                )?;
            } else {
                choices.insert(key, setting);
            }
        }
        let active = |path: &[Name], f: &Feature| -> bool {
            f.guard.iter().all(|choice| {
                choices
                    .get(&(path.to_vec(), choice.group.clone()))
                    .is_some_and(|s| s.mode == choice.mode)
            })
        };
        let mut settings: BTreeMap<(Vec<Name>, Name), &FeatureSetting> = BTreeMap::new();
        let mut supplied_names = BTreeSet::new();
        let mut ordered_features: Vec<_> = selection.features.iter().collect();
        ordered_features.sort_by_key(|s| (&s.field.path, &s.field.name, s.value, &s.provenance));
        for setting in ordered_features {
            let reference = &setting.field;
            let Some((t, feature)) = c.field(None, reference, &mut r)? else {
                continue;
            };
            if !supplied_names.insert((reference.path.clone(), reference.name.clone())) {
                r.emit(selection_error(
                    a,
                    Code::Duplicate,
                    &reference.path,
                    &reference.name,
                    &setting.provenance,
                    "feature name is supplied more than once",
                ))?;
            }
            r.tick(u64::try_from(feature.guard.len()).unwrap_or(u64::MAX))?;
            if !active(&reference.path, feature) {
                r.emit(
                    selection_error(
                        a,
                        Code::Inactive,
                        &reference.path,
                        &reference.name,
                        &setting.provenance,
                        "supplied feature name is inactive under the selected modes",
                    )
                    .with_related(
                        feature.provenance.clone(),
                        definition_key(t, &feature.name, ResourceKind::Field),
                    ),
                )?;
                continue;
            }
            r.tick(u64::try_from(feature.guard.len()).unwrap_or(u64::MAX))?;
            if let ValueDomain::Set(values) = &feature.domain {
                r.tick(u64::try_from(values.len()).unwrap_or(u64::MAX))?;
            }
            if !feature.width.fits(setting.value)
                || !domain_contains(&feature.domain, setting.value)
            {
                r.emit(
                    selection_error(
                        a,
                        Code::Value,
                        &reference.path,
                        &reference.name,
                        &setting.provenance,
                        "feature value is outside its width or legal domain",
                    )
                    .with_actual(setting.value.to_string())
                    .with_expected(format!(
                        "{} bits, {}",
                        feature.width.get(),
                        canonical_domain(&feature.domain)
                    ))
                    .with_related(
                        feature.provenance.clone(),
                        definition_key(t, &feature.name, ResourceKind::Field),
                    ),
                )?;
                continue;
            }
            let canonical = feature
                .alias_of
                .as_ref()
                .map(|x| &x.name)
                .unwrap_or(&feature.name);
            let key = (reference.path.clone(), canonical.clone());
            if let Some(previous) = settings.get(&key) {
                if previous.value != setting.value {
                    r.emit(
                        selection_error(
                            a,
                            Code::Conflict,
                            &reference.path,
                            &reference.name,
                            &setting.provenance,
                            "active names require conflicting values for one storage owner",
                        )
                        .with_actual(setting.value.to_string())
                        .with_expected(previous.value.to_string())
                        .with_related(
                            previous.provenance.clone(),
                            absolute_field_key(a, &previous.field.path, &previous.field.name),
                        ),
                    )?;
                }
            } else {
                settings.insert(key, setting);
            }
        }
        walk_instances(&c, &mut r, |path, t, r| {
            let Some(local) = c.local(t) else {
                return Ok(());
            };
            for group in local.groups.values() {
                r.tick(1)?;
                if !choices.contains_key(&(path.to_vec(), group.name.clone())) {
                    r.emit(selection_group_error(
                        a,
                        Code::MissingSelection,
                        path,
                        &group.name,
                        &group.provenance,
                        "every instantiated mode group needs one explicit choice",
                    ))?;
                }
            }
            let mut active_classes = BTreeMap::new();
            for f in local.features.values() {
                r.tick(1)?;
                if absolute_field_key(a, path, &f.name).is_none() {
                    return Err(limit(
                        r.stage,
                        "instance-qualified key",
                        r.limits.max_key_bytes,
                    ));
                }
                r.tick(u64::try_from(f.guard.len()).unwrap_or(u64::MAX))?;
                if active(path, f) {
                    let canonical = f.alias_of.as_ref().map(|a| &a.name).unwrap_or(&f.name);
                    active_classes.entry(canonical).or_insert(*f);
                }
            }
            for (owner, f) in active_classes {
                if !settings.contains_key(&(path.to_vec(), owner.clone())) {
                    r.emit(selection_error(a, Code::MissingSelection, path, owner, &f.provenance, "active storage-owner class needs one explicit value through an active name"))?;
                }
            }
            Ok(())
        })?;
        Ok(r)
    })();
    match result {
        Err(error) => Err(vec![error]),
        Ok(r) if r.errors.is_empty() => Ok(()),
        Ok(mut r) => {
            r.errors.sort();
            Err(r.errors)
        }
    }
}

pub(super) fn canonical_domain(domain: &ValueDomain) -> String {
    match domain {
        ValueDomain::Any => "any".to_owned(),
        ValueDomain::Range { minimum, maximum } => format!("range[{minimum},{maximum}]"),
        ValueDomain::Set(values) => {
            format!("set{:?}", values.iter().copied().collect::<BTreeSet<_>>())
        }
    }
}
