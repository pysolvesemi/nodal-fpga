# Foundation exchange 0.1

The closed normative schema, scalar grammar, projection sites, set comparators,
identity domains, operation prerequisites and admission limits are frozen in
[the reviewed FND-05 contract](../../../docs/implementation/fnd-05-readiness.md),
sections 3–9. This directory names that versioned contract; it is not a generic
JSON Schema validator, migration engine or a second schema definition.

Executable language boundaries:

- Rust `core/rust/exchange/src/wire.rs` declares closed private DTOs; `parser.rs`
  retains object input order and duplicate keys through bounded admission.
- Rust `architecture.rs` lowers into the public checked FND-04 model. Its public
  validator remains authoritative; Selection remains a separate transient API.
- `canonical.rs` enumerates semantic sets and cold provenance sites. It never
  removes arbitrary fields recursively or uses core record Ord for wire order.
- `document.rs`, `package.rs`, and `design.rs` establish immutable admission
  witnesses. Caller-provided digest bindings resolve flat byte leaves only.
- Scala's executable fixture writer is an authoring demonstration, not a DSL.
- Independent literals and tests live under `verify/fixtures/exchange` and
  `tests/exchange`; candidate output is never a golden authoring input.

## Compatibility

Only these exact format / version / profile / required-feature tuples are read:

| Format | Version | Profile | Required feature revision 1 |
| --- | --- | --- | --- |
| nodal-fpga.arch | 0.1 | structural-selection/1 | nodal-fpga/arch.structural-selection |
| nodal-fpga.package-manifest | 0.1 | software-package/1 | nodal-fpga/package.software-inspection |
| nodal-fpga.mapped-design | 0.1 | mapped-structural/1 | nodal-fpga/design.structural |

Unknown major/minor/profile/required feature fails closed. Unknown optional
annotation capabilities are retained with a notice, including unknown names in
the `nodal-fpga` namespace; the three registered semantic features cannot be
optional. No migration, inference, legacy fallback or external download exists.

## Executable file adapter

`nf-exchange parse INPUT [--limits JSON]` exercises only bounded parsing and
canonical JSON spelling. It does not accept an architecture/package/design.

`nf-exchange arch INPUT --output canonical|projection|summary` accepts an
architecture. `package MANIFEST` additionally takes zero or more explicit
`--artifact SHA256=PATH` bindings. `design DESIGN --package MANIFEST` takes those
same explicit bindings. The default output is summary. Successful canonical and
projection output is exact UTF-8 without a final newline. Failures produce one
structured JSON object on stderr, nonzero exit, and no partial stdout.

`--limits` is a JSON object of partial positive integer overrides for the public
Limits fields; nested `core` fields use the public ValidationLimits field names.
Every public reader checks lowered-only capabilities before reading input.
Artifact names/keys are never paths: the CLI adapter alone opens explicitly
supplied filenames, while the library accepts a digest-to-Read callback.

The initial stable codes in the reviewed contract gain `duplicate` for duplicate
library IDs, tool option names, or caller digest bindings. Malformed digest
strings use `identity_mismatch` at decode (before hashing), wrong JSON types use
`wrong_type`, and invalid capability-ID grammar uses `invalid_annotation` at
envelope. Schema errors retain exact RFC6901 token data, including backticks.
Human message/actual/expected and Display pointer presentation is capped at 1024
UTF-8 bytes each. The structured pointer remains exact, at most twice admitted
input bytes plus bounded depth; it is not recopied into parser error messages.

This profile supports only structural software inspection and semantic
comparison. Bound opaque artifacts do not enable RTL, DeviceDB, routing,
programming, timing, physical implementation, or any external execution.

## Error-order phases

Bounded JSON parsing precedes envelope shape decoding. Within each closed-schema
phase, present member/type/enum failures follow the input member order; missing
fields are detected when their object ends. Envelope compatibility then checks
format, version, profile and feature declarations in the documented order before
body shape decoding or semantic lowering. Tagged objects first select their
required discriminator, then decode the remaining variant payload in input order.
The private ordered-value deserializer routes exactly the four supported tagged
DTO families without Serde's intermediate Content map, preserving nested paths.
Unsigned grammar, u16 metadata and u32 partition narrowing occur at the visited
field. Core checked constructors and the authoritative semantic validator follow
schema admission and retain their own ordered diagnostics. Target equality still
precedes mapped target lookups; no phase may publish a partial result.

The pinned numeric visitor rejects every non-i32 JSON numeric literal. Integer
values delivered as i64/u64 outside i32 report `overflow`; values delivered as
f64 or rejected by the pinned parser as unrepresentable report `invalid_json`.
Thus an integer lexeme beyond u64 can receive `invalid_json`, with no float
coercion or acceptance. Semantic U64 decimal strings always use the separate
exact grammar/range check and report `overflow` above u64. No arbitrary-precision
parser feature, second numeric scanner or hand-written JSON parser is enabled.
Known contract metadata in error presentation also has the 1024-byte text cap;
exact location remains the separately retained RFC6901 pointer.

## Manifest accounting

Manifest body declarations count body, architecture binding, every artifact
descriptor occurrence, every library, each tool/view binding, and each tool
option. References count the architecture semantic-ID binding, each descriptor
occurrence, and each bound implementation identity. Work counts every declaration
and reference, one index-insertion unit per descriptor/library/option, and UTF-8
bytes plus one for every library id/revision, bound tool id/version, option
name/value, bound view revision, and unbound/absent reason. Fixed role names,
digests and common metadata are not name-byte charges. Parser/header counters
remain separate. The primary independent manifest therefore costs 15 declarations,
2 references and 296 work units; counter failure is `limit` at `/body` before any
resolver call. Libraries/options honor lowered collection limits; option names
also honor the lowered core component limit. Architecture and design counters
are independently enforced by their respective validators.
