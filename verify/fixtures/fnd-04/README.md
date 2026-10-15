# Independent FND-04 corpus

The preparation-time literal expectations in `expectations.md` were frozen
before production source existed. Original SHA-256:
`b33d80f70272393474ec8583c479acdd488de39d43ee039ca2ab94a0aebd1581`.
`corpus.rs` retains the pre-implementation snapshot of literal graph/activation
expectations and tiny independent bit enumerators. The independent integration
test contains the same literals directly: the core ownership guard prohibits
source-inclusion hooks even in tests. Neither version is used by production core.

The readiness contract subsequently resolved the explicitly pending details:

- Every instantiated mode group requires exactly one selection. Every active
  canonical owner/alias class requires one active-name value; additional active
  values must agree. Alias-only writes are supported. Inactive writes reject.
- Source spans are half-open UTF-8 byte offsets within declared byte length.
- Structured identity is exact kind, namespace, ordered scope and local key.
- Limits are those published in `docs/implementation/fnd-04-readiness.md`.
  Diagnostic/work exhaustion yields a deterministic singleton limit diagnostic.
- Abstract expectation categories map to the public `nf_types::Code` variants:
  missing references to `Missing`, wrong scope to `WrongScope`, recursive
  templates to `TemplateCycle`, mode errors to `Mode`, incomplete selections to
  `MissingSelection`, undeclared overlaps to `Overlap`, contradictory guards to
  `Guard`, alias inconsistency to `Conflict`, and unsupported chains to
  `AliasChain`. No expected legality changed to accommodate implementation.

The exhaustive oracle covers 6 x 6 guard pairs x 4 complete independent-group
choices x 4 x 4 two-bit values = 2,304 selections. Six activation masks are
literal hand-authored truth sets. Per-choice active guard counts are 3, 4, 3, 3,
so 43 guard-pair/choice combinations are co-active. Exactly 172 selections
accept, 516 conflict and 1,616 contain an inactive-name write. Shared-bit
consistency enumerates bits.
Arithmetic uses u128 as an independent wider domain; topology expectations list
all edges explicitly. Mutation controls assert the intended category or graph
mismatch, never merely an arbitrary error. Seed: `0xF0041D3E5EED`.

Primary assumption coverage is ASM-0003, ASM-0004, ASM-0008, ASM-0009,
ASM-0010 and ASM-0011. ASM-0002 is covered only by rejecting a mode that the
primitive did not declare. Actual register/LUT behavior, serialization,
physical allocation, PDK/timing/crossing safety, DeviceDB and hardware execution
remain outside this structural/type profile. FND-03 evidence interactions are
retained by the parent qualification suite with clean-source/profile receipts.

This increment does not affect generated Verilog.

Reproduce the independent Rust tests from the repository root:

```sh
source .cache/toolchains/env.sh
cargo test -p nf-types -p nf-arch-ir --test independent_contract --locked --offline -- --nocapture
cargo clippy -p nf-types -p nf-arch-ir --test independent_contract --locked --offline -- -D warnings
```

The scale test prints elapsed nanoseconds, immutable declaration counts, shallow
instance-vector capacity and name-payload bytes. Those byte observations exclude
other allocations, allocator overhead and process RSS. Repeated validation checks
same declarations and work counters, without asserting unstable elapsed times.
The instance axis also validates complete per-instance selections. Hierarchy and
partition axes are separate, avoiding an unbounded Cartesian product.

`inventory.json` records the fixture-to-assumption mapping, exact exhaustive
counts, mutation categories, seeds and claim limits. Reordering controls compare
full diagnostics, including both origins for duplicate/contradictory inputs.
Cross-scope driver controls cover local versus top-level, parent versus child,
and resource aliases denoting the same physical destination. The unknown-feature
selection control requires an instance-qualified portable key and Selection stage.

Review-driven additions retain the same profile: definition/instance complete-key
bounds, selection and architecture preflight ordering, actual cycle-edge origins,
duplicate declaration/membership origins, finite-set diagnostic ordering and
nominal Storage/ModeGroup diagnostics. Field-resource/Feature and Pip-resource/
Connection typed-identity collisions reject. A compact seven-template, 48-child
fixture represents 262,144 leaves and explicitly rejects under a 10,000-work
budget. It has no wall-clock threshold and creates no expanded expected model.

Mode-name and mode-group permutation regressions additionally sweep every work
budget from 1 through 2,000 with a one-diagnostic cap. Their 4,000 permutation
comparisons require identical complete results under competing work/diagnostic
limits. Normal bounds separately require the intended unsupported-mode and
mode-duplicate categories. These checks prevent declaration order from changing
which singleton resource-limit failure is reported.

A further 2,000 budget comparisons cover a mode group's membership list containing
both an owner and its direct resource alias. Both orders must reject the repeated
physical member with identical full diagnostics, including under competing caps.

The architecture-level connection whole-key regression uses the literal PIP key
`(independent, [], abcdefghijklmnopqrstuvwxy)`: 11 namespace bytes plus 25 local
bytes. A 36-byte bound accepts; a 35-byte bound rejects with one Architecture
limit diagnostic. Reversing connection/root declarations preserves both results.
Duplicate connection names expose the same top-level nominal key in diagnostics.
