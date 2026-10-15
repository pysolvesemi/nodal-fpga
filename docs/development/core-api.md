# FND-04 core API: structural and selection validation

The `structural-selection` profile is a finite Rust-builder model and validator.
It checks declarations, references, ownership, modes and logical configuration
selections. It does not execute a primitive or a configured circuit.

The public crates are [`nf-types`](../../core/rust/types/src/lib.rs) and
[`nf-arch-ir`](../../core/rust/arch-ir/src/lib.rs). `nf-types` has no dependencies;
`nf-arch-ir` depends only on `nf-types`. Neither imports a concrete device,
primitive library, Scala runtime, adapter or separately installed LLVM/MLIR/CIRCT
SDK. The ordinary pinned Rust toolchain remains required to build them. Both
crates forbid unsafe code. Follow the [readiness boundary](../implementation/fnd-04-readiness.md),
[architecture](../architecture.md) and [Foundation contracts](../contracts/foundation.md).

This increment does not affect generated Verilog.

## Checked types and separate identities

`Name::new` accepts a nonempty, exact UTF-8 component of at most 128 bytes.
`Key<K>::new(namespace, scope, local)` retains the namespace, ordered scope
components, local component and nominal resource kind separately. The maximum
scope length is 64 components and the maximum complete key is 4,096 UTF-8 data
bytes, counting namespace, scope and local bytes without invented separators.
There is no case folding, Unicode normalization, path normalization or
delimiter-concatenated identity. A slash or `..` inside a component has no
traversal meaning. `erase()` yields a `SemanticKey` that retains the kind.

The sealed marker set supplies distinct `Wire`, `Pip`, `Bel`, `Pin`, `Node`,
`Site`, `Field`, `Template`, `ResourceType`, `Domain`, `ModeGroup` and `Storage`
identities. Each has a
typed key and dense-ID alias, such as `WireKey` and `WireId`. A `WireId` cannot be
assigned to a `PipId`; the compile-fail doctests exercise that public boundary.
These identity layers are deliberately different:

- `Key<K>` is a portable semantic key, without provenance or display labels.
- `DenseId<K>` is a `u32` local index. Constructing one does not prove an entry
  exists or establish its build or partition.
- `DenseRef<K>` carries an exact `BuildId`, `PartitionId` and typed local ID.
  `UntypedDenseRef` retains a runtime kind for checked mixed-kind boundaries.
- `PartitionTable<K>` describes actual table entries without allocating the
  table. `resolve`/`resolve_erased` check build, partition, kind and entry bounds
  before a checked conversion to `usize`. The returned number is not a pointer.
- `BuildId::new([u8; 32])` stores a caller-supplied identity. It neither computes
  a canonical hash nor authenticates a package.

`TableCount` admits `2^32` entries even though the greatest local ID is
`u32::MAX`. Counts are populated entries, not reserved capacity.
`DenseId::try_from_u64`, `TableCount::new` and table resolution reject truncation
and out-of-range use. The current platform must represent a resolved index.

`validate_correspondence(expected, entries, tables)` checks an explicitly
supplied total, one-to-one correspondence for one kind and one exact build.
Every expected portable key and every populated dense slot must appear once;
partition tables must be unique. Equal names, equal numbers, equal counts or
similar declarations never infer correspondence. Cardinality and checked `u64`
table-count sums are checked before constructing indexes. A huge declared count
with a tiny mapping fails without iterating or allocating over that count.
Retained correspondence indexes scale with supplied entries, keys and partitions;
this API has no `ValidationLimits` argument. Its caller must bound supplied input
collections at an external parsing boundary.

`BitCount`, `BitOffset`, `ByteLength` and `ByteOffset` are distinct `u64` units.
Their checked additions, multiplications and conversions return diagnostics on
overflow. Byte-to-bit conversion checks multiplication by eight; bit-to-byte
conversion is exact and rejects a remainder rather than rounding.
`BitRange`/`ByteRange` are checked half-open intervals: adjacent ranges do not
overlap, empty ranges are permitted and reversed or overflowing bounds reject.
`Width::new` supports logical values of 1 through 64 bits stored in `u64`.
`Width::fits` handles 64 without shifting by 64. A feature's value width is
separate from the `u64` position and capacity of its storage.

## Building and validating ArchIR

Construct `Architecture::new(Name)` and `Template::new(Key<Template>)`, then add
their public declaration fields. Public fields permit constructing an invalid
model for diagnostics; an `Architecture` alone is not a validity witness.

`validate_architecture(&architecture, &limits)` returns either ordered
`Diagnostics` or a `ValidatedArchitecture<'_>` borrowing the input immutably.
`architecture()`, `limits()` and `stats()` expose the original declarations,
effective limits and architecture-validation counters. The witness owns no
second model, and the borrow prevents mutating the input while it remains live.
`validate_selection(&validated, &selection)` checks a separate transient
selection and returns `Result<(), Diagnostics>`; it changes neither declarations
nor the selection and embeds no customer-job state in the architecture.

### Definitions, paths, interfaces and connections

`ResourceType` declares a `ResourceKind`, ordered `Pin` interfaces and available
mode names. A pin has `Direction::Input` or `Direction::Output` and positive
`BitCount` width. A `Resource` names an exact type and kind in its template.
Resource names are unique within a template even across resource kinds in this
profile; references still check the requested kind. Resource types, templates,
roots, domains and other named declaration tables are keyed collections: duplicates reject rather than using first/last-writer wins.
Ordered pin vectors and connection source vectors are never reordered by
validation. A `ResourceKind::Field` resource and a feature cannot share the same
template-local name: both would denote the same portable field identity. The
same restriction applies to a `ResourceKind::Pip` resource and connection.

`Instance` refers to a reusable template. Roots have an explicit declared
partition; children may inherit it or name another declared partition. Instance
identity uses the entire root/child path and the template-local resource name.
Three roots of one template are three independent resource/configuration owners.
Template definitions retain their own structured keys; definition identity and
instance identity are not interchangeable.

`ResourceRef.path` and `FieldRef.path` are explicit child-instance paths relative
to the containing template, or absolute paths beginning at a root when used in
architecture connections or selections. An empty relative path means the current
template. Resolution has no parent traversal, global name search or inferred
boundary bypass. Recursive template containment rejects, including unused cycles.
A routing cycle is a different concept and may be structurally legal.

`Endpoint` names an exact resource and pin. A named architecture-level
`Connection` has a `Pip` key with the architecture namespace and empty scope;
its namespace plus local name obey the same whole-key byte limit as a
template-qualified connection key. `Connection` supports buffered, directed
point-to-point wiring only:

- Fixed connection: exactly one source, no selector.
- Selectable mux: two or more ordered sources and one explicit selector feature.
  Value `i` selects `sources[i]`; changing source order changes that meaning.
- Sources must be output pins, the destination an input pin, and all widths must
  match. Multiple declarations cannot drive the same canonical destination,
  including through resource aliases or different containment scopes.
- Connections are always present. A mux requires an unguarded selector name and
  an exact legal value domain of `0..=N-1` for `N` sources. For a three-source mux,
  a two-bit `Any` domain is invalid because it admits reserved value 3.

There is no bidirectional/pass-switch, tri-state, electrical contention solver,
connection guard or hardware timing behavior in this profile. Validation does
not infer missing edges, simulate signal values or prove a circuit safe.

### Modes, storage and declared sharing

`ModeGroup` is a nonempty single-selection group with nonempty declared modes,
all supported by each referenced resource type. Its resource references must be
template-local. One canonical owned resource can belong to at most one group;
referencing its alias cannot evade that rule, and duplicate membership rejects.

`Storage` declares positive logical bit capacity and a directly owned local
resource. It is a logical owner object, not an allocated physical address space.
Separate storage objects remain independent even when their offsets and resource
owners match. `Feature` specifies the same direct local owner as its storage,
an in-bounds slice whose length equals its positive width, and a legal domain:

- `ValueDomain::Any`: all values fitting the feature width
- `Range { minimum, maximum }`: inclusive bounds within the width
- `Set(Vec<u64>)`: a nonempty, duplicate-free set within the width; order is
  nonsemantic

A feature's `guard` is a conjunction of `ModeChoice` entries referring to local
groups and legal choices. Repeating one group, even with the same choice, rejects;
contradictory choices also reject. Different choices in one group are exclusive.
Choices in separate groups can coexist. There is no general Boolean/SAT guard
language or inferred default value.

There are two distinct alias contracts:

- A resource alias names a direct, same-template owned resource with the same
  kind and resource type. It cannot itself own storage or features.
- A feature alias names a direct, same-template owning feature and must have the
  identical resource owner, storage object, slice, width and declared value
  domain. Reordering a `Set` does not change that domain. Distinct domain forms
  are not automatically normalized into interchangeable declarations.

Alias chains, cycles, dangling owners, cross-template aliases, partial slices
and bit permutations reject. Independently owning feature intervals in the same
storage cannot overlap, even when their guards are mutually exclusive. Legal
overlap requires a direct explicit feature alias; modes alone never transfer
ownership. Adjacent intervals are legal.

A complete `Selection` supplies:

1. Exactly one declared `ModeSetting` for every instantiated mode group.
2. At least one explicit `FeatureSetting` through any active name in every active
   owner/alias storage class, qualified by its full instance path.
3. Equal values for any additional co-active names writing that same class.

An owner and its direct aliases form one class for one instance; each unrelated
feature is its own class. Supplying only an active alias is enough, even if the
owning feature's guard is inactive. Ownership remains declared independently of
the owning name's activation. A wholly inactive class requires no write, and a
supplied value through an inactive name rejects. An individual feature name may
not be supplied twice. Exclusive aliases can carry different values in their
separate legal selections; simultaneous active aliases must agree. Reuse of a
template never forces different instances to select the same value or mode.

### Independent domain memberships

`Domain` and `DomainRef` carry an exact typed key and `DomainClass`: clock, power,
configuration, placement or routing. Instance and resource membership lists may
overlap independently of containment. A declared reference must exist and its
class must match; duplicate membership rejects. Membership does not infer a
containment tree, propagate an electrical permission or prove CDC, power-state,
configuration-isolation, placement or routing-crossing legality. Those later
operation-specific checks remain separate from this structural reference check.

## Provenance and deterministic diagnostics

`SourceSpan::new(source, source_bytes, start, end)` stores a source identifier,
declared byte length and half-open byte coordinates. It checks only numeric
ordering and bounds. No source text is supplied: it cannot establish UTF-8
code-point boundaries, read a file or verify the declared length. A reader that
slices actual source text must check those properties itself. `Provenance` adds
an optional nonsemantic display annotation. Each source identifier/display
string is bounded to 1,024 UTF-8 bytes.

`Diagnostic` exposes `code`, `stage`, `message`, primary provenance, an optional
structured semantic key, related origins/keys, optional actual/expected values
and a remedy through `DiagnosticData`. `Code::as_str()` and `Stage::as_str()`
provide stable identifiers. `Display` is a short presentation, not a serialized
envelope. Callers needing source positions should inspect the structured fields.

Diagnostics order by stage, semantic key, code spelling, message, primary
provenance, related entries, actual, expected and remedy. Builders and validators
sort related entries; callers manually editing public diagnostic presentation
fields must preserve that order themselves. Keyed-declaration permutations do
not change validator results. Semantic sequences such as pins/mux sources retain
their input order. Provenance remains available for deterministic tie-breaking
but never becomes portable-key identity. Derived Rust equality/ordering of whole
declarations is structural, including provenance and stored vector order. It is
not a semantic-equivalence API, semantic fingerprint or promised canonical wire
format.

Ordinary failures may accumulate diagnostics; ambiguous declarations and
containment cycles can prevent further resolution. A capability failure returns
a single `limit` diagnostic instead of truncating errors into a successful or
partially valid model. No API promises to enumerate every possible defect.

## Limits, accounting and implementation shape

`ValidationLimits::default()` supplies the following defaults **and ceilings**.
Callers may lower any field to a positive value; zero or a larger value rejects.

| Field | Default / ceiling |
| --- | ---: |
| `max_declarations` | 100,000 |
| `max_references` | 200,000 |
| `max_collection` | 16,384 |
| `max_depth` | 64 |
| `max_key_component_bytes` | 128 |
| `max_key_bytes` | 4,096 |
| `max_provenance_bytes` | 1,024 |
| `max_diagnostics` | 128 |
| `max_work` | 1,000,000 |

The constructor bounds in `nf-types` remain in force independently. Architecture
validation also applies lowered limits to declared and derived qualified keys,
paths and provenance. A template-local resource key adds the template's local
name to its scope; an instance resource key includes the complete instance path.
Thus individually acceptable components can still exceed a qualified-key bound.

Accounting is intentionally conservative, not a unique-object count:

- Before sorting declarations, an allocation-free shape pass bounds every nested
  vector and reference path. The sum of vector entries and path components must
  fit `max_work` and is charged to that budget. Every shape failure uses the same
  bounded diagnostic, independent of which declaration first exposes it. Selection
  path lengths are likewise checked before comparing complete settings.
- Declaration entries include top-level types/templates/roots/partitions/domains/
  connections, pins, mode names, template-local records and finite-domain values.
- References include type/template targets, domain memberships, resource/field
  references, guards, group-member entries and connection source entries. A source
  entry and its nested resource reference are both charged. Selection entries
  and nested field references are similarly charged separately.
- Every charged collection entry adds one work unit. Visiting a name charges its
  UTF-8 byte length plus one; provenance checks, resolution steps and many
  declaration/selection visits add work. Explicit scans of pins, modes, guards
  and finite domains, and copied instance paths, are charged as well.
- Instance traversal has a separate occurrence counter and pending-stack cap,
  both bounded by `max_declarations`; repeated occurrences are not merely the
  number of template definitions. An otherwise compact hierarchy can exhaust
  occurrence, depth, key or work limits. Architecture validation walks instances
  for qualified destination ownership; selection checks every instance for
  completeness. Selection starts a new budget using the witness's limits.

`ValidationStats` reports charged declarations, references, work and maximum
template hierarchy depth for the successful architecture validation. These are
implementation counters, not CPU instructions, elapsed-time guarantees, allocated
bytes or wire-format fields. Sorting/tree comparisons, allocation overhead and
all host runtime costs are not individually metered. A work limit is therefore
not a hard real-time or exact memory quota; callers must also bound input bytes
and resource use in their own reader/service. A valid architecture can still
have a selection that exceeds its selection-validation budget.

The validator is split into private bounds, reference resolution, declaration,
connection and selection modules. Transient ordered indexes borrow declarations;
template definitions remain shared and no normalized model is emitted.
Independent owner intervals use per-storage sorted sweeps rather than a bit
array indexed by their largest offset. Cross-scope driver checks stream instance
occurrences and retain bounded destination-ownership constraints, not expanded
resources or connectivity. Selection likewise walks occurrences and maintains
transient settings/owner-class indexes. This is bounded structural processing,
not a production DeviceDB query engine or a claim that cost is independent of
the number of instances. No general optimization framework, cache or physical
allocation algorithm is part of this API.

## Executable model and reproduction

[`examples/model.rs`](../../core/rust/arch-ir/examples/model.rs) builds a generic
resource type and one shared template, instantiates it as `t0`, `t1`, `t2`, and
declares only `t0 -> t1` and `t1 -> t2`. Each instance has an explicit mode and a
different logical value. The validated view still contains one template. A
second selection changes `t1` to value 3, which fits two bits but violates the
declared inclusive domain `0..=2`. Its `value` diagnostic preserves both the
selection's origin and the feature declaration's origin. Source coordinates are
synthetic numeric examples, not claims about an external file's contents.

From the repository root, with the [pinned toolchain](bootstrap.md) installed:

```sh
# In the prepared task environment, select its existing isolated tool cache.
source .cache/toolchains/env.sh
cargo run --quiet --locked --offline -p nf-arch-ir --example model
cargo test --locked --offline -p nf-types -p nf-arch-ir --all-targets
cargo test --locked --offline -p nf-types -p nf-arch-ir --doc
./nf check contracts
./nf check rust
./nf reproduce rust
```

The `source` line is specific to a prepared local tool cache, not a required
tracked file; otherwise use the bootstrap's supported toolchain setup.
The model's deterministic stdout is:

```text
nodal-fpga/arch-ir/1
profile=structural-selection
templates=1 instances=3 connections=2
instance=t0 template=tile partition=0 mode=normal setting=0
instance=t1 template=tile partition=0 mode=alternate setting=1
instance=t2 template=tile partition=0 mode=normal setting=2
link=edge0 source=t0/cell.O destination=t1/cell.I
link=edge1 source=t1/cell.O destination=t2/cell.I
selection=valid
rejected=value
stage=selection namespace=example scope=t1 field=setting
primary=selection-input:61..62 actual=3
related=architecture-input:40..41
message=feature value is outside its width or legal domain
This increment does not affect generated Verilog.
```

The slashes and dots in this small display are presentation only; the model uses
separate structured path/name/pin fields. The first line is the example-output
identifier, not a released ArchIR serialization version. The example does not
emit Verilog, assign physical bits, execute these links or simulate the mode names.

`./nf reproduce rust` builds both the bootstrap and this model in two clean
temporary source copies, compares exact output bytes and lockfiles, and reports
their SHA-256 identities. This does not claim byte-identical executable binaries.
The example source above has SHA-256
`5a1476aaa42dc4ef965778ee2091c191b46ce2fd992642b5fb84e8e49f50dd18`;
the displayed stdout, including its final newline, has SHA-256
`1615356294a3728c68d2bb9fe76c296dfd5c4ecd3daa73340cdc76ccd4868bd2`.
These identify the model example and its output, not the complete library build.
Capture source and output identities from the exact checkout under test:

```sh
./nf identity
rustc --version
cargo --version
sha256sum Cargo.lock core/rust/types/src/*.rs core/rust/arch-ir/src/*.rs \
  core/rust/arch-ir/src/validate/*.rs core/rust/arch-ir/examples/model.rs
cargo run --quiet --locked --offline -p nf-arch-ir --example model > /tmp/nf-model.txt
sha256sum /tmp/nf-model.txt
```

Commands and examples are reproduction instructions, not evidence of a final
accepted commit. The owning completion record must bind actual source/tree and
artifact hashes, command results and applicable review/integration evidence.
Independent public-API fixtures cover arithmetic/partition boundaries, aliases,
mode combinations, routing versus containment cycles, domains and deterministic
diagnostics. Their bounded scale axes include 4,096 repeated instances, depth
boundaries, partitions and huge scalar storage positions with tiny declarations;
recorded timings/size observations apply only to their exact runner and input.

## Later boundaries

FND-05 owns the versioned serialization, canonical bytes/hashes, strict reader
and Scala interoperability. DB owns production lowering and immutable compiled
queries; CFG owns physical bit allocation and transport/loader behavior. RTL
owns generated fabric; FND-06 owns its independent reference executions. This
profile establishes none of LUT/register behavior, runtime configuration loading,
fabric equivalence, physical domain-crossing legality, production-scale capacity,
timing/PPA, board execution or silicon qualification. No Rust layout, enum
discriminant, pointer width or memory image is a portable file/ABI contract.
