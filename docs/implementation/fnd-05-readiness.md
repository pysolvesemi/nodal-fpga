# FND-05 readiness: strict portable exchange

Status: revised readiness documentation, awaiting the original independent
reviewer's verification and the coordinating parent's explicit implementation GO.
The parent agreed to the five narrow R1–R5 dispositions recorded in the
[readiness review](fnd-05-readiness-review.md); incorporating them is not a claim
that re-review has passed. FND-04 accepted-evidence closure is complete. This
readiness document is not FND-05 implementation, execution, or acceptance evidence.
All FND-05 checklist descendants remain required and open until their own evidence.
No checklist amendment is needed or made.

## 1. Source state, prerequisites, and scope

Read-only inspection on 2026-10-15 observed the clean branch
`increment/fnd-05-exchange`, created from accepted dev commit
`c508401afb3bc172a28163b84375157e1ce2ac2d`, tree
`c5ebc61886eb5903d3ca654b118edf3bc4d63276`. The coordinator verified accepted-evidence
closure [PR #8](https://github.com/pysolvesemi/nodal-fpga/pull/8) merged at that
identity; local HEAD/tree and the authoritative checked FND-04 parent/all 16 leaves
agree. The [FND-04 completion report](../completion/FND-04.md) retains the historical
implementation and qualification evidence. Its original pre-closure wording is
not rewritten by this readiness update.

FND-04 tested implementation candidate is
`bc6e3264d5ee8489b8a606d9e7de568ad0f99a7e`, tree
`44474e04e37de6cfa293e5a580685edc1e3c1c16`, integrated through
[PR #7](https://github.com/pysolvesemi/nodal-fpga/pull/7) at
`f9fdd8cf8363104bfa0f4063fd851016eb462bec`. The earlier outside-repository proposal
and independent review observed that implementation merge while closure was still
pending. Their original claims and hashes remain historical evidence; neither
is retroactively described as having verified the later closure. No changes were
found between the tested implementation and inspected integration in
`core/rust/types`, `core/rust/arch-ir`, or `docs/development/core-api.md`.
Refresh live target/PR/protection state again before publication or integration.

Read AGENTS.md, roadmap index/progress, complete Foundation acceptance rules and
FND-05 checklist; architecture/verification/early-baseline contracts; ADRs 0001,
0002, and 0003; foundation/core contracts and FND-04 public code; original
`/tmp/fnd05-readiness-proposal.md`; `/tmp/fnd05-runtime-capacity.md`; and the full
independent expectations at `/tmp/fnd05-independent-expectations.md`.
The latter's verified SHA-256 is
`67436527d7357a98e620a2df532cc6fdba2de696b9e48217154cb71647015546`.
Its literal vectors are under `/tmp/fnd05-independent-vectors/` and must remain
unchanged; they are independent algorithm/parser probes, not yet complete valid
architecture/design/manifest goldens.

No checklist scope amendment appears necessary. Implement only one small exchange
crate, one executable Rust inspector/conformance surface, one executable Scala
fixture writer, versioned contracts/schema, independent tests/corpus, dependency
policy extension, and real saved-package runtime qualification. FND-04 is the
semantic authority. No production Scala DSL, DeviceDB, fabric generator, physical
allocator, CAD adapter, timing engine, loader, or general compiler framework is
introduced. No new non-Foundation prerequisite is created.

Latest user cadence remains local tests then verified increment dev integration;
no pre/post-merge CI unless actual branch protection requires it. The combined
Foundation remote qualification remains due after implementation. Local passes
must not be described as CI. Reuse one increment branch/draft PR and continuation
under the repository's current policy; the parent owns remote writes and merge.

## 2. Complete obligation/applicability map

Every listed FND-05 leaf is required now after accepted FND-04; none is waived,
deleted, optional, or reassigned to a later track. Production implementation and
dependency acquisition are still gated on verification of this revised readiness,
the durable readiness commit/draft PR, and the parent's explicit GO.

| Leaf | Required deliverable/evidence and implementation owner |
| --- | --- |
| a.1 | Exact three envelopes below, units, feature registry and identity fields; exchange owner |
| a.2 | Compatibility/operation matrix and architecture/device/customer ownership; exchange owner with independent review |
| b.1 | Pinned executable Scala writer and Rust reader over the same reviewed contract; Scala and exchange owners |
| b.2 | Canonical full dumps and semantic equality under explicit projections, retaining hierarchy; exchange owner and independent corpus |
| c.1 | Versioned byte/order/projection/hash specification and independent literals; exchange specification plus independent author |
| c.2 | Bounded parser, strict version/features/errors, explicitly unsupported migration; exchange owner and adversarial tests |
| c.3 | Checked wire-to-public-type conversions, no native layout/unsafe casts; exchange owner and API audit |
| d.1 | Scala-to-Rust, hand-input-to-Rust, supported round trips and set permutations versus independent expectations; corpus owner |
| d.2 | Malformed/truncated/oversize/wrong-identity/unsupported cases, asserting intended diagnostics; corpus owner |
| d.3 | FND-04 integer/key/unit/provenance/hierarchy/selection boundary interactions; corpus owner, through public APIs |
| f.1 | Hand-authored full envelopes and literal canonical bytes/hashes before candidate answers; independent author |
| f.2 | Real pinned Scala generation followed by real prebuilt Rust consumption inside the reviewed allowlisted runtime; Scala and runtime owners |
| g.1 | Readability, bounded temporary duplication, no eager graph expansion, transformations/preservation review; independent reviewer |
| g.2 | Independent nesting/repetition/payload axes, limits, stable hashes, exact-version compatibility, measured bytes/time; corpus/runtime owners |
| e.1 | Published corpus/matrix/source/schema/artifact identities, actual Scala input and canonical output, executable reproduction; parent integrates owner evidence |
| e.2 | Separate authoring/runtime results, all local regressions/review, policy-governed qualification and verified integration; parent |
| e.3 | Final audit: all descendants and FND-04 accepted; retain explicit no-RTL/no-full-device-inspection limit; parent |

Later-owned functionality stays outside this acceptance claim: DSL authoring
usability/parity; DB immutable compiled representations; CFG physical allocation
and transport; RTL actual emission; CAD mapping/placement/routing legality;
TMC characterization; PERF production scale; optional CIR adapter qualification.
These are scope boundaries, not substitutes for a required FND-05 test.

## 3. Exact envelope and compatibility contract

Every semantic object is closed. Every listed field is required, including empty
collections and explicitly nullable fields. Unknown fields, missing values, and
wrong types reject; no behavioral defaults, flattened catch-all maps, coercion,
version guessing, partial acceptance, or automatic migration. The root object
has exactly `format`, `version`, `profile`, `required_features`,
`optional_features`, `annotations`, and `body`.

- `version`: exactly `{major, minor}`, JSON integers in 0..=65535.
- `profile`: exactly `{id, revision}`; id is a nonempty bounded string and revision
  a JSON integer in 0..=65535.
- Feature entry: exactly `{id, revision}` with the same bounded revision encoding.
- Every permitted JSON integer literal matches `0|-?[1-9][0-9]*`, then passes
  its exact u16 metadata or i32 annotation range. Negative zero, fraction and
  exponent forms reject; boolean is not an integer. This lexical rule does not
  require a bespoke tokenizer and is distinct from decoded U64-string grammar.
- Feature lists are keyed by ID, not `(ID, revision)` for uniqueness. Repeated ID
  rejects even if the revision/value agrees. Conflicting revisions also reject.

Only these exact format/version/profile/required-feature combinations are accepted:

| Format | Version | Profile/revision | Required feature/revision |
| --- | --- | --- | --- |
| `nodal-fpga.arch` | 0.1 | `structural-selection` / 1 | `nodal-fpga/arch.structural-selection` / 1 |
| `nodal-fpga.mapped-design` | 0.1 | `mapped-structural` / 1 | `nodal-fpga/design.structural` / 1 |
| `nodal-fpga.package-manifest` | 0.1 | `software-package` / 1 | `nodal-fpga/package.software-inspection` / 1 |

The registry maps every known semantic construct of each payload to its required
feature above. Exactly that required entry is necessary. Unknown required IDs,
revisions, duplicates, missing declarations, or a capability registered for a
different format reject before semantic lowering. A registered semantic
capability cannot appear in `optional_features`. Optional entries describe only
nonsemantic annotation capabilities and never change the operation matrix.

`annotations` is the sole extensible location, and exists only at the envelope
root. It is an object mapping namespace-qualified capability IDs to bounded JSON
data. Its version is the containing exchange schema version. Each annotation
namespace must have one matching optional-feature declaration; optional entries
with no data are permitted and remain nonsemantic. Capability/annotation IDs
are at most 128 UTF-8 bytes and match ASCII
`[a-z][a-z0-9.-]*/[a-z][a-z0-9._-]*`. This grammar applies to capability IDs only,
never to FND-04 resource names. Initially no annotation namespace receives
semantic interpretation. Unknown optional namespaces are preserved, each with a
recorded `unknown_annotation` notice. Duplicate decoded keys and all parser
budgets still apply inside their data. Allowed annotation values are null,
boolean, string, signed-32-bit integer, array, and object; no fractional,
exponential, or out-of-i32 numeric literals. Annotation arrays retain order.

Input may include normal JSON whitespace before/after the single document;
canonical output never does. Reject BOM, invalid UTF-8/JSON, lone surrogate
escapes, and any trailing second JSON value. Literal U+FEFF within a string is
ordinary data. No migration command is implemented: requesting migration fails
explicitly. Future migrations require their own named input/output versions,
identities, changed assumptions, tests, and non-in-place outputs.

## 4. Scalars, text, portable keys, and units

`U64` means a JSON string whose decoded value matches exactly
`0|[1-9][0-9]*`, then checked against u64 and the destination field's narrower
range. The grammar applies AFTER JSON escape decoding: `"\u0031"` is a valid
spelling of decoded value `"1"`; canonical output spells it `"1"`. Reject plus,
leading zero, negative, -0, internal/external whitespace, fraction/exponent,
non-ASCII digits, and overflow. A JSON numeric literal, boolean, or null is not
an unsigned quantity even if it has a convenient numeric interpretation.

`Name` is exactly FND-04 Name: nonempty exact UTF-8, <=128 data bytes, no case
folding/normalization/path interpretation. `/` and `..` are data. Structured key
is exactly `{kind, namespace, scope, local}`; scope is an ordered Name array.
Kind is an explicit lowercase wire spelling, never enum ordinal. Allowed key
kinds are `wire`, `pip`, `bel`, `pin`, `node`, `site`, `field`, `template`,
`resource_type`, `domain`, `mode_group`, `storage`. A typed field requires its
specific kind. Keep FND-04's <=64 scope elements and <=4096 total UTF-8 component
bytes; derived qualified keys also pass FND-04 validation. No joined string key
or filesystem resolution is allowed.

Resource kind spellings are `wire`, `pip`, `bel`, `pin`, `node`, `site`, `field`;
direction is `input` or `output`; domain class is `clock`, `power`,
`configuration`, `placement`, or `routing`. Explicit wire strings, not declaration
order or native discriminants, define these spellings.

Every semantic numeric quantity uses U64, including partition IDs (checked u32),
widths (checked as specified), storage capacities/offsets, design bit indices,
feature-domain values, artifact byte lengths, and source byte positions. The only
JSON integer literals are the designated revision/version metadata and bounded
annotation integers. Scala constructs/checks unsigned values with BigInt, never
Double/Long conversions. Reject unpaired UTF-16 surrogates before writing strings.

Units are fixed explicitly at these versioned field sites: pin/design-port width,
storage `bits`, feature width, bit-range start/length, and endpoint bit index are
bits; source_bytes/start/end and artifact bytes are bytes. A bit-range object is
exactly `{unit: "bit", start: U64, length: U64}`. No implicit unit conversion or
allocation proportional to a quantity is performed. Source span is exactly
`{source, source_bytes, start, end}`, with a half-open byte range, validated by
FND-04 constructors. Source identifiers are never opened. No timing number or
zero-delay placeholder exists in this profile.

Provenance is exactly `{span, display}`. `span` is null or the source-span object;
`display` is null or a string. Source/display text each obey FND-04's 1024-byte
limit. Null is legal only at positions explicitly enumerated below or within
annotation data. Missing and null are distinct; required nullable fields must
still be present. In particular, a missing `alias_of`, `partition`, `selector`,
`span`, or `display` is not silently accepted as null. Review the typed decoder's
required-nullable representation: ordinary Option/default behavior alone must not
collapse absence into explicit null. Test every nullable site with present null,
present valid value, absent field, and wrong type; retain FND-04's root-partition
rejection even though child partition can be null.

## 5. Architecture body and FND-04 adapter

Architecture body has exactly `semantic_id`, `namespace`, `resource_types`,
`templates`, `roots`, `partitions`, `domains`, `connections`, `provenance`.
All records map directly to final FND-04 declarations:

| Record | Exact fields |
| --- | --- |
| Pin | name, direction, width, provenance |
| ResourceType | key (resource_type), kind, pins, modes, provenance |
| Domain | key (domain), kind, provenance |
| DomainRef | key (domain), kind, provenance |
| ResourceRef | path (ordered Name array), name, kind, provenance |
| Resource | name, kind, resource_type (typed key), alias_of (null/ResourceRef), domains, provenance |
| Instance | name, template (typed key), partition (null/U64), domains, provenance |
| Endpoint | resource (ResourceRef), pin (Name), provenance |
| FieldRef | path (ordered Name array), name, provenance |
| Connection | name, sources, destination, selector (null/FieldRef), provenance |
| ModeGroup | name, resources, modes, provenance |
| ModeChoice | group, mode, provenance |
| Storage | name, owner (ResourceRef), bits, provenance |
| Feature | name, owner (ResourceRef), storage (Name), range (bit-range), width, domain, guard, alias_of (null/FieldRef), provenance |
| Template | key (template), resources, children, mode_groups, storage, features, connections, provenance |

ValueDomain is one of exactly `{kind:"any"}`, `{kind:"range", minimum:U64,
maximum:U64}`, or `{kind:"set", values:[U64,...]}`. Preserve the variant: Range
and Set with the same members are not silently normalized into one semantic ID.
Widths/storage/ownership/alias/guard/mode/reference legality use the final
FND-04 constructors and `validate_architecture`, not a copied implementation.
Root instance partition cannot be null; child null means explicitly supported
inheritance. All other optional positions are exactly the alias, selector, and
provenance nulls listed above. Empty architectural collections still need fields.

Selection is NOT serialized into architecture, design, or manifest. Tests create
independent public FND-04 Selection inputs against the parsed architecture and
call `validate_selection` for equal/conflicting sharing, distinct instances,
inactive choices, and selection completeness. This retains ownership separation.

## 6. Minimal mapped-design body

Body has exactly `semantic_id`, `namespace`, `name`, `target_build_id`, `cells`,
`ports`, `nets`, `provenance`. Namespace/name are Name; cells/ports/nets have
independently unique names within their categories. There are no dense/device
resource IDs, placements, routes, generic constraints/parameters, timing/reset
maps, mutable caches, or device-resource redefinitions.

- Cell: exactly `{name, resource_type, mode, provenance}`. Cell.resource_type is
  a Key<ResourceType> whose wire key.kind is exactly `resource_type`. It must
  resolve in the target architecture to a ResourceType whose ResourceType.kind
  is `bel`. Cell.mode must be one of that declaration's modes. A `bel`-typed key
  with otherwise matching text rejects, as does a resource_type key resolving
  to a wire declaration; missing type and missing mode retain intended errors.
- Port: exactly `{name, direction, width, provenance}`; positive bit width U64.
- Net: exactly `{name, driver, loads, provenance}`; one scalar driver and one or
  more scalar load endpoints. Net width is one bit by this profile, without
  materializing every bit of any declared bus.
- Cell endpoint: exactly `{kind:"cell", cell, pin, bit, provenance}`.
- Port endpoint: exactly `{kind:"port", port, bit, provenance}`.
- Constant endpoint: exactly `{kind:"constant", value, provenance}`; value is
  exactly string `"0"` or `"1"`, and constant is permitted only as a driver.

The accepted reader requires a verified SavedPackage target. Exact
`target_build_id` equality is checked before interpreting target references.
Resolve cell primitive types/modes/pins through the saved architecture. A cell
output or top-level input can drive; a cell input or top-level output can load.
Every bit index is checked against the declared width without bus expansion.
No terminal may be claimed twice across driver/load ownership records; one net
can have multiple distinct loads. Repeated constant values on distinct nets are
not terminal-ownership conflicts. An unconnected terminal is permitted at this
structural-inspection layer; no functional completeness/behavioral claim follows.
No implicit direction, default mode, inferred port, or automatic net is allowed.
This tiny design check does not claim CAD primitive mapping or route legality.

## 7. Package manifest body and operation requirements

Body has exactly `build_id`, `architecture`, `libraries`, `authoring`, `compiler`,
`backend`, `device_db`, `physical_implementation`, `technology`, `macro_bindings`,
`configuration_map`, `transport`, `activation`, `timing_datasets`, `external_pin_map`.

- `architecture`: exactly `{semantic_id, artifact}`. Artifact is exactly
  `{sha256, bytes}`. The supplied architecture envelope's semantic ID, raw bytes,
  byte length, accepted format/profile/features, and own declared ID are checked.
  The semantic digest already binds the complete architecture contract metadata;
  do not introduce a second parallel architecture-version registry in the manifest.
- `libraries`: keyed records `{id, revision, artifact}`. id and revision are
  nonempty <=128-byte text; ID uniqueness rejects duplicates. Empty is explicit
  for wholly inline Foundation declarations. Every referenced artifact is checked.
- `authoring`, `compiler`, `backend`: ToolBinding. Bound form is exactly
  `{state:"bound", id, version, implementation_sha256, options}`. id/version are
  nonempty <=128-byte text. options is a keyed list of exactly `{name, value}`;
  name is Name, value is <=1024-byte text, duplicate option names reject.
  `implementation_sha256` identifies the pinned tool implementation, not a request
  to ship/execute/download that compiler at runtime. Unbound form is exactly
  `{state:"unbound", reason}`, where reason is `foundation-unimplemented` or
  `not-supplied`. No arbitrary timestamp/path/comment enters a ToolBinding.
- The remaining fixed role fields are ViewBinding. Bound form is exactly
  `{state:"bound", revision, artifact}`, revision nonempty <=128-byte text.
  Unbound form is the same closed reason-tagged shape as ToolBinding.
- `macro_bindings` additionally permits exactly
  `{state:"absent", reason:"no-hard-macros"}`. No other role permits absent in
  version 0.1. Null is never a binding state.

The actual Scala demo has a bound authoring identity: id
`nodal-fpga/scala-fixture-writer`, version `0.1`, and implementation_sha256 of the
exact writer source or a reviewed multi-file source manifest. Required named
identity options include `scala_compiler` (`org.scala-lang:scala3-compiler_3`) and
`scala_version` (the pinned `3.3.8`); record other relevant authoring options/tool
identities explicitly. The authoring harness supplies and verifies the source
hash, avoiding source self-reference. This is identity data, not publisher
authentication. The hand-authored independent package instead declares authoring
`{state:"unbound", reason:"not-supplied"}` and makes no Scala provenance claim.
Thus "bound Scala fixture" describes actual emitted demo bytes, not every
independent hand-authored envelope.

Both use explicit empty libraries for inline declarations, unbound compiler/
backend/device/physical/configuration/transport/activation/timing/pin views, and
genuinely absent hard macros. A bound opaque view means byte verification only,
not physical/configuration/timing qualification. Every semantic dependency,
revision, option, and state enters the build projection. Changing configuration/
physical/timing/pin binding must change build identity, even when architecture
semantic identity is unchanged.

Supported operations and prerequisites:
- Architecture inspect/canonicalize/semantic-compare: exact arch contract,
  full FND-04 semantic validation, and verified semantic ID.
- Saved-package inspect/load-architecture: exact package contract, all referenced
  artifact lengths/digests verified, accepted saved architecture, verified build ID.
- Mapped-design structural inspect/canonicalize/compare: the verified package
  above, exact target build, target-based structural design checks, verified design ID.
- RTL emission, DeviceDB queries, route legality, bitstream/programming, physical
  implementation and timing closure: unsupported operations, even if an opaque
  role happens to be bound. No fallback or external tool download.

Artifact lookup is digest-addressed and supplied by the caller. No manifest URL,
archive extraction, arbitrary path, source lookup, executable hook, or template
component-to-path conversion exists. Admit the complete artifact set before any
resolver call or allocation derived from a declared length:

1. Validate every descriptor and collect distinct digests, including architecture.
   Reused digests must have identical declared lengths. Check unique count, each
   declared length against the per-artifact ceiling, and checked sum of unique
   declared lengths against the aggregate ceiling. Any failure makes zero resolver
   calls. The manifest's own input-byte budget is separate from this aggregate;
   architecture counts once in the referenced-artifact aggregate.
2. Resolve each admitted digest at most once. Bound each actual read by the minimum
   of its declared length, per-artifact byte ceiling, and remaining aggregate
   actual-byte allowance, plus at most one overflow-detection byte. Count actual
   bytes including a failure probe and abort immediately on overrun. The single
   probe may exceed a failed bound by one; no accepted result exceeds any bound.
   Never read the entire next artifact before checking remaining allowance.
   File metadata does not establish actual length.
3. Require exact EOF/length and raw digest agreement. Retain verified immutable
   bytes or an equally immutable verified result; never reopen mutable resolver
   backing content later. Missing, short, oversized, and digest-mismatched content
   receive their intended distinct failures.

Only the architecture role is parsed as an architecture envelope. Library and
bound view payloads are opaque, flat byte artifacts. Their bytes are verified,
never interpreted for further dependency resolution, archive extraction,
executable dispatch, or inferred capabilities. The manifest has no mapped-design
role/reference. A design binds its target package; it is not a semantic dependency
of that target package. Embedded JSON/manifest/design-looking bytes acquire no
transitive semantic claims. Tool implementation digests remain identities, not
resolver requests or executable dependencies. The reader never fetches content.

## 8. Canonicalization and the exact projection

Canonical full dump is JSON UTF-8, no BOM, no insignificant whitespace, no final
newline. Human-readable formatting can be a separately named presentation; it
must not be mislabeled canonical bytes. Objects sort decoded keys lexicographically
by UNSIGNED UTF-8 bytes. Strings escape quote and backslash; use `\b`, `\f`, `\n`,
`\r`, `\t`; other U+0000..001F controls use lowercase `\u00xx`. All other Unicode
scalar values and slash are literal UTF-8; no normalization. Integers use ordinary
minimal decimal digits. Scala must reject lone UTF-16 surrogates and compare each
UTF-8 byte as `b & 255`; default String ordering is not the comparator.

Typed portable key comparator is tuple `(kind, namespace, scope, local)`. Kind
compares its lowercase wire spelling by unsigned UTF-8 bytes, NOT Rust enum
ordinal. Other text uses the same byte comparison. Scope compares ordered elements
lexicographically, with a shorter equal-prefix vector first. Local references
compare `(kind, path, name)`; FieldRef compares `(path, name)`; Endpoint compares
`(resource-reference identity, pin)`. Metadata/provenance is never a set key.

Schema collection classification is exhaustive:
- Ordered: ResourceType.pins, Connection.sources, all scope/path arrays, annotation
  arrays. No truth-table or transport-transaction array is introduced in v0.1.
- Typed-key sets: architecture.resource_types/templates/domains; sort full key.
- Name-keyed sets: roots; each template's resources/children/mode_groups/storage/
  features/connections; architecture.connections; design cells/ports/nets.
- Numeric sets: architecture.partitions and ValueDomain.Set.values, sorted by
  checked numeric magnitude ("2" precedes "10").
- Name sets: ResourceType.modes and ModeGroup.modes.
- Reference sets: resource/instance domains by `(key, kind)`; ModeGroup.resources
  by complete ResourceRef identity. Validation rejects semantically conflicting
  duplicates; sorting never repairs them.
- Guards: Feature.guard keyed by group, with mode retained as its semantic value.
- Features: required_features/optional_features keyed by capability ID.
- Manifest libraries keyed by ID; tool options keyed by name.
- Design loads: endpoint tuple, using kind wire bytes first, then cell/port name,
  pin where present, and numeric bit index. Constant cannot be a load.

Reject duplicates BEFORE canonical output. Preserve set record provenance attached
to its own identity while changing declaration order. Canonical full dumps are
data-lossless under supported parsing, not byte-lossless and not a promise that
incidental original order/whitespace/escape spellings survive. Semantic comparison
means equality of the canonical semantic projection, not graph isomorphism,
semantic renaming, or hardware equivalence. A hash is a fingerprint, not proof
against collisions or publisher authentication.

Projection is a schema-directed traversal; never a recursive key-name filter.
Architecture removes only `/body/semantic_id`, `/annotations`, `/optional_features`
and `provenance` fields belonging to THESE typed records: Architecture body,
ResourceType, Pin, Domain, DomainRef, Template, Resource, Instance, ResourceRef,
Endpoint, FieldRef, Connection, ModeGroup, ModeChoice, Storage, Feature. These
record occurrences are only at the exact field paths defined in section 5;
no arbitrary object nested in annotation data becomes a semantic record. The
whole typed Provenance value (span and display) is excluded. All other fields,
including every namespace/name/key/kind/partition/mode/reference/domain/width/
value/unit/guard and required capability, remain.

Design removes only `/body/semantic_id`, `/annotations`, `/optional_features`,
and typed provenance at body, Cell, Port, Net, and its three endpoint variants.
`target_build_id` ALWAYS remains. Manifest removes only `/body/build_id`,
`/annotations`, and `/optional_features`; no nested similarly named field may
be excluded or accepted outside its closed schema. There is no manifest provenance
field. Timestamps/machine paths are only permissible within excluded annotations
or typed architecture/design provenance; no semantic locator is resolved.

Digest strings are exactly 64 lowercase hex characters. Inputs are:
- Raw artifact: SHA256(exact delivered bytes), no prefix.
- Architecture: SHA256(ASCII `nodal-fpga.arch.semantic.v1\n` || canonical projection).
- Design: SHA256(ASCII `nodal-fpga.design.semantic.v1\n` || canonical projection).
- Package: SHA256(ASCII `nodal-fpga.package.build.v1\n` || canonical projection).
The displayed `\n` is exactly one LF byte in the prefix. There is no further
separator, length prefix, BOM, or JSON newline. Compute, then compare declared
self-ID. A provenance-only architecture edit preserves semantic ID but changes
raw artifact bytes, therefore changes an exact artifact-bound package build ID.

The independent C00/C12/C13/C22/C23/C24 domain-separated vectors are immutable
algorithm tests. C20/C21 projection probes use THEIR synthetic exact exclusions,
not the released envelope paths. C25-C27 are intentionally incomplete generic
specimens and must never pass as final envelopes (their provisional profiles and
empty capabilities/body are insufficient). Add separate full-envelope goldens.

## 9. Parser, checked API, budgets, and deterministic failures

Use a custom safe budget-aware Serde DeserializeSeed/Visitor to build a bounded
JSON value before closed typed decode. Reject decoded duplicate keys before map
insertion; raw serde_json::Value as the first parser loses duplicates and is not
acceptable. Keep serde_json recursion protection enabled and do not enable its
unbounded-depth feature. No bespoke JSON tokenizer, unsafe deserialization,
native-memory casts, or unchecked u64-to-usize conversions.

Read at most max_input_bytes+1 through Read, regardless of file metadata. These
operation-specific stages, rather than one generic late-identity pipeline, govern
which failure takes precedence:

- Common: bounded parse, decoded duplicates and end-of-document; closed envelope
  and exact compatibility/features; closed kind DTO and checked scalar conversion.
  Capability support is checked before semantic lowering.
- Architecture: FND-04 validation, semantic self-ID verification, publication.
- Package: complete descriptor preflight and manifest build-ID verification before
  any resolver call; verify raw artifact bytes/length/digest before interpreting
  the architecture payload; accept the architecture through its checked path;
  publish only after every required artifact and identity passes.
- Design: compare target_build_id with the verified SavedPackage before any target
  type/mode/pin lookup; perform structural checks and semantic self-ID verification;
  then publish.

Never publish partial canonical output or accepted hashes after a late failure.
A wrong well-formed target plus a nonexistent type/pin reports target mismatch
without target lookup. A bad manifest build ID causes zero resolver calls. Wrong
artifact digest must not be masked by a later architecture semantic failure.

Proposed accepted API surface (names can vary without changing this contract):
`read_architecture(Read, Limits)`, `read_package(Read, Resolver, Limits)`, and
`read_design(Read, &SavedPackage, Limits)` return private-field immutable checked
documents. Provide canonical full/projection output and typed digest accessors.
Public ArchIR view remains available immutably. No alternate validator or second
retained authoritative model. Consume wire DTOs into checked FND-04 types and
release temporary parser/DTO storage; root annotations remain available for round
trip. A separate bounded JSON parser API/test surface may exercise pure parser
vectors without falsely treating them as accepted envelopes.

Ceilings are positive and caller-lowered only; validate limits before input:

| Budget | Ceiling / exact counting |
| --- | --- |
| input bytes per JSON document or supplied artifact | 8,388,608 actual bytes, before trimming whitespace |
| container nesting | 64; root object=1; scalar-root=0; each nested object/array adds 1; keys/scalars add 0 |
| aggregate JSON nodes | 200,000; each JSON value plus each decoded object key counts 1 |
| immediate collection entries | 16,384; object members count once each; array elements once each |
| decoded string/key bytes | 65,536 UTF-8 bytes per string or key, after escape decoding |
| unique requested package artifacts | 256 |
| aggregate requested artifact bytes | 33,554,432 actual bytes, counted once per exact digest |
| FND-04 declarations/references/work | existing ceilings 100,000 / 200,000 / 1,000,000 |
| FND-04 depth/key/provenance/diagnostics | existing 64 / component128 and key4096 / string1024 / 128 |

The input cap bounds parser scratch allocation. Finer counters are checked before
retaining another node/entry or constructing semantic indexes. Never reserve from
untrusted size_hint/declared quantities. A temporary decoded string may exist
before its finer length check, but cannot exceed the already bounded input.
Bounded recursion, traversal/drop, output allocation, and resolver reads must be
reviewed together. A cap is not a hard real-time or exact process-memory guarantee.

Mapped-design/manifests additionally charge their own structural records and
references against 100,000/200,000, and explicit lookup/traversal/string-byte work
against 1,000,000. Document exact accounting with the implementation; at minimum
one unit per record/reference/index insertion and each visited name byte+1, plus
endpoint lookup steps. No unmetered numeric-range expansion. This is independent
of FND-04 architecture counters, which retain their existing documented meaning.
Lowered budgets must exercise each intended bound without another one masking it.

Exchange errors carry stable code, stage/operation, RFC6901 JSON pointer, optional
line/column, known declared version/profile, actual/expected, remedy, and original
FND-04 diagnostics including portable keys/provenance/related origins where used.
Initial stable codes: `io`, `invalid_utf8`, `invalid_json`, `duplicate_key`,
`trailing_document`, `limit`, `invalid_limits`, `unknown_field`, `missing_field`,
`wrong_type`, `invalid_enum`, `invalid_unsigned`, `overflow`, `unsupported_format`,
`unsupported_version`, `unsupported_profile`, `unsupported_feature`,
`missing_feature`, `duplicate_feature`, `invalid_annotation`, `semantic`,
`identity_mismatch`, `artifact_missing`, `artifact_length`, `artifact_digest`,
`target_build_mismatch`, `unsupported_operation`; notice `unknown_annotation`.
Stages: `read`, `parse`, `envelope`, `decode`, `semantic`, `identity`, `artifact`,
`operation`. Core failures retain their own core code rather than replacing it
with an unrelated parser string. Parser/schema fail-fast order is input order;
valid canonical output and keyed semantic diagnostic order remain deterministic.
Core's ordered diagnostic list remains authoritative for architecture rejection.
Ensure pointer escaping (`~` -> `~0`, `/` -> `~1`) and preserve untrusted values as
data, not filesystem commands. Cap diagnostic presentation without hiding code,
location, declared bound, or remedy. Review preservation of input order through
closed-schema decoding: a sorted intermediate map must not silently reorder the
promised fail-fast errors. Duplicate detection can use a separate membership set
while retaining input-ordered entries. Canonical sorting happens only when its
schema-aware phase permits it; input error order is not canonical object order.
Review required-nullable behavior separately from unknown/missing-field handling.
Neither checkpoint authorizes a bespoke JSON parser. No failure is a passing
negative test unless its intended category/location is actually observed.

## 10. Pins and dependency policy extension

Candidate direct dependencies, exact pins to acquire only after GO:
- serde `=1.0.229`, default-features=false, features std and derive.
- serde_json `=1.0.154`, default-features=false, feature std only.
- serde_path_to_error `=0.1.20` (path reporting, converted to actual RFC6901 tokens).
- sha2 `=0.10.9`, default-features=false, features std and force-soft; no asm.
- Scala authoring: com.fasterxml.jackson.core:jackson-core:2.21.5, streaming
  JsonGenerator only, no databind/reflection/Jackson Scala module.
Retain existing pinned Rust/Scala/sbt/JDK and formatting tools. Pins above are
verified upstream candidates, not installed/audited/qualified artifacts yet.

Primary sources inspected: https://docs.rs/crate/serde/latest/source/Cargo.toml ;
https://docs.rs/serde_json/latest/serde_json/ ;
https://docs.rs/crate/serde_path_to_error/0.1.20 ;
https://docs.rs/crate/sha2/0.10.9/source/Cargo.toml ;
https://github.com/FasterXML/jackson-core/blob/jackson-core-2.21.5/pom.xml .
Jackson core is generator-only here; check current upstream advisories/release
status at acquisition and record why the exact version is acceptable for this use.
Any necessary pin change must be reviewed and recorded, not silently floated.

Extend FND-04's existing explicit package/path/DAG guard. Add nf-exchange edges
only to nf-types, nf-arch-ir and the reviewed dependencies. Review and freeze the
actual complete resolved registry graph: package names/versions/source/checksums,
all normal/build/dev/target edges, aliases, proc macros, features, build scripts,
native hooks, and canonical local paths. force-soft does not remove declared
cpufeatures/etc edges from the inventory. Preserve adversarial guard tests and
project forbid(unsafe_code); distinguish dependency implementation audit from
project lints. Freeze Maven JAR/POM checksums and resolved runtime classpath too.
No registry name-only allowlist and no blanket build-script prohibition that
would misrepresent reviewed third-party behavior. Keep Scala out of Rust runtime.
After authorized acquisition, reproduce locked/offline. Failure to acquire/review
a needed pin is a blocker, not permission to invent crypto or a JSON tokenizer.

## 11. Independent corpus, review, and measured evidence

Before invoking candidate output to establish an answer, the independent author
must finalize full valid arch/design/package envelopes from this contract and
hand-stated semantics. Review literal canonical JSON bytes, then establish hash
literals using standard sha256sum plus Python hashlib, not production
normalization/serialization/hashing. Retain the existing C00-C38 and other literal
files unchanged. When an intentional contract change requires a new golden,
record the reviewed change instead of silently regenerating expected answers.

Required basis includes repeated t0/t1/t2 line; sparse holes/asymmetric boundaries;
nested a/b and .. literal components; ordered three-source mux and independent
index expectations; same/different instance alias settings and conflicts through
public Selection; legal routing versus illegal template recursion; overlapping
typed domains; exact target-bound mapped design; explicitly unbound package;
Unicode/BMP/supplementary comparison; annotation preservation notice; exact
large-value/tiny-allocation storage and provenance/key bounds.

Execute parser-level and valid-envelope mutations for duplicate decoded keys at
all levels, unknown fields, missing/null/wrong types, truncated/invalid encoding,
trailing documents, unknown exact versions/profiles/features and missing/duplicate
capabilities, numeric grammar/range/type cases, each byte/node/depth/string/record/
reference/work boundary, wrong target/self-ID/artifact length/digest/missing
content, changed package dependencies, keyed declaration permutations, ordered
pin/mux permutations, cold-field edits, semantic key edits, legal/illegal aliases,
and all applicable FND-04 regressions. Explicitly include 2^53-1, 2^53, 2^53+1,
2^63, u64::MAX, u64::MAX+1, u32/Width/source-byte/conversion boundaries, and escaped
decimal digits. Explicit numeric-literal tests include metadata and annotation
`-0`, `1.0`, `1e0`, `-0.0`, `-0e0`, valid 0, i32 endpoints, and adjacent
out-of-range values; preserve the decoded `"\u0031"` U64-string success.
Test all-array, all-object, and mixed container depth 64/65 including scalar
leaves and full-envelope overhead; library recursion failure is not the intended
limit diagnostic. Test nullable absence independently of explicit null.

Artifact tests must include consistent repeated digests resolving once; conflicting
lengths, count+1, per-artifact declared oversize, and aggregate declared sum+1
failing before resolver calls; lowered exact boundaries; dishonest short/appended/
never-ending streams stopping at measured read bounds; and resolver backing
mutation after successful verification never triggering a second read. Opaque
nested manifest/URL/design-looking bytes cause no extra resolver calls or
execution. An added mapped-design manifest role rejects as unknown, and design
bytes in the architecture role reject format. Fully bound opaque roles do not
activate unsupported operations. Exercise each operation-specific error precedence
above and late self-ID failure with no accepted output. Compare parsed semantics
as well as hashes; equality of two candidate-generated hashes alone is insufficient.

Measure separate axes: repeated root count (including 4096 when within budgets),
reference/template depth supported/rejected boundary, payload lengths, Unicode
bytes, and deterministic repeated dumps/digests. Record exact input/source/tool/
seed identities, sizes, counts, elapsed time and limits hit. A chosen budget may
reject a large fixture honestly; do not raise a ceiling or remove expensive
validation to manufacture a scale pass. Keep explicit no-flat-graph/no-production
scale claim. Review bounded temporary parser/DTO/ArchIR duplication and release
intermediates, canonical readability, and transformation preservation.

## 12. Saved-package runtime and actual executable evidence

Pinned Scala authoring generates actual saved bytes outside runtime isolation.
Build Rust once outside isolation, then consume those saved bytes with the real
prebuilt executable. Capture binary/fixture/output identities. The runtime root
contains only the reader, inspected required ELF loader/libraries, saved artifacts,
minimal /dev and isolated /proc, and scratch tmpfs. No repository, host /usr,
home, JDK/Scala, Cargo/Rustup/build tools, or optional LLVM/MLIR/CIRCT application
libraries/executables are mounted wholesale. Clear environment; make inputs
read-only; close inherited descriptors; capture stdout/stderr externally.

The existing capacity probe is NOT acceptance. `bwrap --unshare-all` failed at
NETLINK_ROUTE setup under the OS restriction. Do not claim a network namespace.
The viable local proposal uses user/PID/IPC/UTS namespaces plus independently
reviewed seccomp denial of socket/socketpair/connect/accept/bind/listen/send/recv
families and io_uring_setup, rejecting non-x86_64/x32 ABI attempts. Review exact
launcher/filter before adoption, bind their source/binary identities, and verify
no inherited network-capable descriptors survive. This is a scoped dependency
isolation demonstration, not a hostile-code sandbox-security claim. If this
route cannot meet a required observation, report the exact blocker; do not count
an empty PATH or absent java command as equivalent evidence.

Inspect actual runtime file/process behavior from the host with permitted ELF
and tracing tools. Test both successful supported consumption with the expected
canonical/digest output and rejection of an invalid package inside the SAME
runtime boundary. Retain separate records for authoring tools/output, prebuilt
runtime binary/libraries, mount/env/process/network policy, positive consumption,
and negative package behavior. Host launcher/tracer tools are not consumer
runtime dependencies. Later combined CI may use a separately reviewed minimal
Docker --network=none profile with actual tests; that does not retroactively
qualify the current probe.

## 13. Recommended parallel ownership and integration sequence

FND-04 closure is complete and this increment's single branch is established.
The parent should verify the original reviewer's response on these revised
documents, publish the coherent readiness as the first focused documentation
commit with [skip ci] and one draft PR, and explicitly send GO before production
edits/acquisition. This document does not assert that a draft PR or scheduled
hourly monitor already exists. Active task continuation is not a scheduled
monitor. Any required scheduling setup and its success/blocker must be recorded
truthfully by the coordinator. Preparation workers may read this document and
finalize outside-repo literals meanwhile.

Recommended four non-overlapping implementation lanes after GO:
1. Exchange owner: schemas/versioned contract, nf-exchange Rust parser/DTO/core
   adapters/design/package checks/canonical hashes/CLI and narrow Rust unit tests.
   Own core/rust/exchange and schemas; coordinate Cargo manifest/lock updates with
   dependency owner rather than racing them. No FND-04 semantics changes silently.
2. Scala owner: frontend/scala fixture writer and writer-side numeric/Unicode
   checks, pinned generator integration and emitted actual examples. Own frontend
   paths only; agree wire fixture names/content with independent author first.
3. Independent corpus owner: retained literal vectors, full-envelope goldens,
   black-box conformance/mutation/round-trip/scale tests and independent report.
   Own verify/fixtures/exchange and tests/exchange. Do not import production
   canonicalization to compute expected results, and do not rewrite candidate
   production modules to conceal a mismatch.
4. Dependency/runtime owner: extend reviewed dependency guard/inventory/tests and
   build-check orchestration under tools/tests/bootstrap, acquire/checksum approved
   pins, coordinate root Cargo/lock edits, and build reviewed runtime isolation
   harness/evidence. Do not regenerate independent expected answers or edit
   frontend/Rust implementation without coordinating ownership.

Use an additional independent reviewer when a slot is free; review schema first,
then parser limits/projection/identities/public boundaries/runtime policy and
actual corpus evidence. Do not let reviewer availability delay reporting a real
blocker. Parent owns readiness/completion/roadmap/evidence receipts, remote refs,
checkpoints, reviews, and verified integration. Shared build/cache commands are
serialized by one designated coordinator; workers can use distinct target dirs
only when the dependency/runtime owner agrees. Never run competing workspace
builds or let one worker overwrite another's Cargo.lock.

Order: freeze schema and independent full goldens -> reviewed dependency inventory
and ownership gate -> implementation in parallel -> hand-input/Scala/Rust checks
and independent rejection/scale review -> actual authoring/runtime isolation ->
full required local regressions/reproduction -> exact candidate/source/artifact
record -> policy-governed verified integration -> accepted-evidence closure.

Completion retains actual Scala source/emitted bytes, canonical output, schema/
corpus/dependency/binary hashes, compatibility matrix, command results, review,
limits and separate runtime evidence. No source or accepted-golden change after a
check is silently covered by old results. The parent remains open until every
required descendant and predecessor acceptance is complete.

This increment does not affect generated Verilog.
