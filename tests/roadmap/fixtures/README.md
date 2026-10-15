# Independent roadmap controls

These fixtures and their literal expectations were hand-authored from the
progress rules and FND-03 checklist, independently of the production parser and
renderer. They are synthetic software validation inputs, never project status
or historical completion evidence. Tests feed their contents under synthetic
owning-track paths, rather than scanning this directory as a real roadmap.

The positive cases intentionally cover partial progress, reopened ancestors,
numeric children out of display order, multiple nesting levels, final `.e`
after independent review groups, and fenced examples containing invalid state,
duplicate IDs and unknown dependencies. Structure-only tests disable evidence
checks explicitly; passing one does not qualify a real completion claim.

Each negative case changes one intended invariant. Tests assert the stable
error code and the relevant source/ID context, rather than accepting any crash.
Evidence validation controls use temporary repositories and synthetic records;
no fabricated evidence is installed in the actual completion directory.
