# FND-04 readiness audit and implementation boundary

Integration target: d4948096e16e7299ef02a90363f90491ebe9790d (`dev`), with FND-01 through FND-03 accepted.
Branch: `increment/fnd-04-core`. All FND-04 descendants are required now; no
existing item is waived or genuinely non-applicable. All remain open until their
own evidence and final integration are complete. Read AGENTS.md, roadmap index,
progress rules, full Foundation checklist, architecture, verification/early
baseline, ADRs 0001–0003, accepted contracts and predecessor evidence. Refresh
live branch/PR state before publication. No checklist scope amendment is needed.

## Existing code and ownership

Only `nf-bootstrap` exists in Rust. Reuse pinned toolchains, `nf` checks,
Foundation contracts and roadmap/evidence validation. Add exactly two production
crates: `core/rust/types` and `core/rust/arch-ir`; the latter depends only on the
former. Retain bootstrap as its build witness. No registry dependencies, Scala,
concrete devices, adapters, optional SDKs, native hooks or unsafe code enter core.
Independent expectations live outside implementation logic in fixture/test data.

The bootstrap ownership guard currently permits one dependency-free package.
Evolve its explicit registry into a reviewed package-name/canonical-path DAG,
checking every dependency section and Cargo's resolved metadata. Preserve tests
for renamed dependencies, mismatched package names, target/dev/build sections,
path/symlink escapes, unregistered crates, registry impersonation, build/native/
include hooks and removed unsafe/publishing policy. Update bootstrap test fixture
copying and `nf` metadata checks; do not broadly allowlist dependency names.

## Public types, identity and model

Implement nominal resource identities (wires, PIPs, BELs, pins, nodes, sites,
fields), checked bit/byte quantities, provenance and stable source-aware
structured diagnostics. Keep portable keys, dense u32 IDs, partition-qualified
references and exact build contexts separate; explicit correspondence is never
inferred from equal names/numbers. Table capacities may be 2^32 while the greatest
local ID is u32::MAX. Checked u64 interval/conversion arithmetic must not allocate
storage proportional to a numerical offset or rely on pointer/native file layout.

Portable equality includes kind, exact namespace, ordered scope components and
local key, with no case/Unicode/path normalization or delimiter-concatenated
identity. Resource instances use full root/child instance paths and template-local
keys; sharing a definition does not alias writable state. Source spans are
half-open UTF-8 byte offsets bounded by declared source length; provenance is
retained but nonsemantic. Diagnostics retain primary/related origins and stable
codes and order under keyed declaration permutations.

The initial ArchIR preserves finite reusable templates, distinct instances,
resource interfaces and ordered pins, owned resources and explicit aliases,
fixed/selectable references with ordered mux sources, legal modes and logical
configuration features. References use explicit relative child paths in templates
or absolute root paths for architecture-level links, without parent traversal,
name search or implicit boundary bypass. Template recursion is rejected; legal
routing cycles are not confused with containment cycles.

Typed clock/power/configuration/placement/routing domains and memberships remain
independent of containment, covering ASM-0011's FND04-DOMAIN-REFERENCES obligation.
Reject wrong-kind/dangling membership without claiming physical crossing checks.
A validated immutable view borrows declarations; selections are separate inputs,
not mutable device or customer job state embedded in architecture definitions.

## Bounded configuration sharing profile

Use 1–64-bit feature values stored in u64, explicitly rejecting zero/wider widths
and out-of-domain values. Width 64 must avoid shifting by 64. Storage owners and
checked half-open slices use u64 independently of value width. Adjacent ranges do
not overlap. Overlapping writable declarations require a direct explicit alias
to the same owner; exclusivity alone does not authorize duplicate ownership.

Direct-to-owner aliases require identical scope, interval, width and value domain.
Alias chains, partial slices and bit permutations are unsupported and rejected;
cycles/dangling owners have explicit diagnostics. This is a narrow logical
ownership contract, not a physical allocator. Conjunctive guards name mode-group
choices: different choices in one single-selection group are exclusive, choices
in separate groups can coexist. Co-active aliases must agree on shared bits;
exclusive aliases may differ in their separate valid selections. Supplied values
for inactive aliases reject. Complete selection requires exactly one declared mode
per instantiated single-selection group and at least one explicit value per active
owner/alias storage class through any active name. Additional active writes must
agree. Ownership remains declared regardless of the owning name's activation
guard; there are no inferred defaults or redundant-write requirements. Preserve nf-tiny's existing no-alias profile and use
separate generic fixtures for sharing. No general Boolean/SAT language is needed.

## Limits and scale gates

Default capabilities: 100,000 total declarations; 200,000 references; 16,384
immediate collection entries; depth/path length 64; 128 UTF-8 bytes per key
component, 4,096 per complete key; provenance strings 1,024 bytes; 128 diagnostics;
1,000,000 charged validation work units. Validate caller bounds against safe
implementation ceilings; zero/invalid limits reject. Budget exhaustion is an
explicit deterministic resource-limit failure, never truncation into success.
Use canonical traversal where needed to preserve diagnostics under declaration
permutations. Document accounting and its limits without claiming hard real-time
or production scale. Avoid duplicate model storage and eager hierarchy expansion;
transient indexes are allowed, no normalization is necessary.

Measure independent axes: resources/repeated instances (including 4,096),
hierarchy/reference depth to supported/rejected bounds, partition boundaries,
and huge scalar offsets with tiny allocation. Retain counts, bytes, elapsed time,
seed/runner/tool/source identities and repeated deterministic model/diagnostic
outputs. Do not import later PERF/PPA obligations or construct a Cartesian matrix.

## Independent validation and acceptance

An independent worker authors literal fixtures and hand expectations before using
production validator output. Tests exercise public APIs and compile-fail ID misuse;
near-limit integer arithmetic; explicit partition/build correspondence; finite
hierarchy versus routing cycles; dangling/wrong-kind/direction/width references;
ordered three-input mux selection; legal/illegal modes; independent instance
state; declared equal/conflicting simultaneous aliases; exclusive modes and
inactive settings; undeclared/adjacent overlaps; domains and provenance.
Use small independent bitsets/enumeration and deterministic generated mutations,
not production resolution helpers to compute expected answers. Assert intended
stable diagnostics, not arbitrary errors. Record seeds and relevant FND-02
assumption interactions, including ASM-0011, plus FND-03 source/diagnostic receipt
checks. Independent architecture review covers modularity, traversal complexity,
duplication, provenance, deterministic scale and all public boundary assumptions.

Publish an executable Rust-builder model/diagnostic example, supported/rejected
API contract, exact source/artifact hashes, and required local regression checks.
FND-05 owns serialization/Scala interoperability; DB/CFG own production lowering
and allocation; RTL and FND-06 own their respective hardware/reference execution.
No current structural test proves LUT/register behavior, generated fabric,
physical domains, a production DeviceDB or configuration loader.

Latest explicit user cadence: add/run required local tests, then verified dev
merge; no pre/post-merge CI unless actual branch protection requires it. Full
combined remote CI remains required after Foundation implementation. Preserve
source ancestry, exact tested-tree merges and separate accepted-evidence closure.

This increment does not affect generated Verilog.
