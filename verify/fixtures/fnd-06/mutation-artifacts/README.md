# FND-06 portable mutation patches

These twelve exact unified patches and their parent/derivative byte bindings were
captured from the successful development reference run. Headers are relative to
`baseline/` and `derived/`; generated trees and execution logs are not archived.
The inventory records exact target bytes, source locations, frozen manifest hash,
and the required failure witnesses/category. It is an execution deliverable,
not a semantic oracle or a replacement for fresh baseline and mutant execution.

`tools/reference_mutations.py::verify_published_mutations(root, results)` compares
freshly materialized execution bindings with this exact archive, checks the
closed file/identity roster and patch hashes, and rejects unsafe target paths.
The runner must still compile and detect each intended semantic failure using
the independent frozen manifest before this replay binding check can pass.

Do not normalize patch bytes or update hashes to accommodate a failing replay.
A source change requires independently reviewed regeneration and execution.
