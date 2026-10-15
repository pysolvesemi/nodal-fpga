# ADR 0002 — Portable architecture exchange

Status: accepted for the Foundation profile following [independent FND-02
review](../implementation/fnd-02-independent-review.md). This is contract
acceptance, not an implemented schema, writer or reader. Implementation belongs
to FND-04/FND-05 and the later DSL/DB tracks.

## Context and decision

Follow [the architecture](../architecture.md) and
[ADR 0001](0001-optional-circt-backend.md). Scala constructs architectures;
Rust independently validates and compiles their portable description. Exchange
inspectable, versioned UTF-8 JSON first. A saved package must contain the
information needed for its supported operation without invoking Scala/JVM,
replaying source code or passing live language objects. The Rust builder uses
the same contract and validation path, rather than a privileged second model.

The interchange contract and independently reviewed conformance corpus are
authoritative. Neither Scala classes, Rust structs, generated serializers,
MLIR operations nor a downstream EDA format alone defines the semantics.
Preserve hierarchy, repeated templates, explicit bindings, logical configuration
and source correspondence. Do not require a fully expanded routing graph.

This is a small architecture exchange, not an arbitrary expression language,
generic HDL compiler, compiler-pass framework or plugin execution protocol.
Frontend elaboration resolves source-language generation and typed parameters;
the exchanged template/instance description is finite and independently
checkable. No serialized closures, executable deserialization hooks or mandatory
per-resource JNI/FFI calls enter the boundary.

## Envelope and strict compatibility policy

FND-05 implements the exact envelope and published supported-version matrix.
This ADR fixes its required behavior before any wire version is released:

1. Every document identifies its format kind, explicit major/minor schema
   version, semantic profile and profile revision, required capabilities,
   optional annotation capabilities, and payload. Architecture, mapped-design
   and device-package manifest envelopes are different kinds; a reader must not
   infer a kind from a filename or reinterpret one kind as another.
2. A reader accepts only explicitly listed format/version/profile combinations.
   An unknown major, unknown minor or unsupported profile revision is an error,
   even when a numeric version appears newer or superficially compatible.
   A future minor is not automatically accepted. Supporting an older version
   requires retained tests and an explicit compatibility entry.
3. Required capability identifiers include a revision. Each known semantic
   payload construct must have the required capability advertised by that
   version's registry. An unknown or unsupported required capability, missing
   declaration, conflicting revision or duplicate declaration is an error.
   Readers check capability support before semantic lowering/publication.
4. Optional capabilities may describe only nonsemantic annotations whose
   omission cannot change connectivity, modes, legality, configuration, timing,
   identity, safety or requested output. Unknown optional annotation
   capabilities may be ignored with a recorded diagnostic. A feature that
   affects any of those meanings must be required. Labeling it optional cannot
   turn an unsupported feature into success.
5. Unknown fields are errors at every semantic object, including the envelope.
   A versioned `annotations` container is the sole extension escape hatch. Its
   namespace-qualified values are bounded JSON data, never executable content
   or authoritative constraints. Unknown annotation namespaces may be preserved
   opaquely or omitted with a diagnostic; a reader promising lossless round trip
   must preserve them. Annotations cannot override a semantic field. A supported
   annotation feature has meaning only within that nonsemantic boundary.
6. Reject duplicate object keys rather than taking the first or last value.
   Reject malformed UTF-8/JSON, unexpected types, non-finite numbers, invalid
   enums, missing required values and reference/namespace collisions. Missing,
   explicit null and a declared default are distinct; null is legal only where
   the schema explicitly permits it. No parser silently supplies a behavioral
   default or ignores a spelling mistake.
7. An input is either accepted under its declared contract or rejected with
   location and remedy. No best-effort downgrade, version guessing, automatic
   migration, implicit backend substitution or publication of partially
   interpreted artifacts is permitted. A deliberately requested migration is
   a separate operation with input/output identities, changed assumptions and
   its own compatibility tests; it never rewrites the source package in place.

Capability and profile support is operation-specific. A tool able to inspect a
package need not be able to emit or route it; it must identify that difference
before accepting the requested operation. Parsing success is not device or
backend qualification. External tools must not be downloaded implicitly to
satisfy a capability declaration.

## Values, bounds and portable identity

Represent resource references by typed portable keys with explicit scope,
not native pointers, JVM object identities or unqualified dense integers.
[ADR 0003](0003-device-design-ownership.md) defines the distinct portable,
compiled-package and per-job identities.

Use exact integer quantities with explicit units and range checks where the
contract calls for integer quantities. Do not let a JSON library round an ID,
bit mask, size or offset through a floating-point number. FND-04 defines checked
widths/conversions; FND-05 chooses and tests the exact wire encoding for their
full ranges, including values outside an implementation's convenient native
JSON-number range. Timing estimates, units and unknown values must be explicit;
missing characterization is never zero delay.

Readers declare and check input-byte, nesting, record-count, reference-depth
and expansion/work limits before unsafe allocation or recursive traversal.
They validate lengths and arithmetic before converting to local indexes.
Limits are visible profile/tool capabilities; exceeding one is a resource-limit
error, not permission to truncate the architecture. Template recursion must
terminate under the supported finite model. A legal routing cycle does not
imply recursive template expansion and must not be rejected merely as a cycle.

## Canonicalization and hashes

Keep three questions distinct: semantic equivalence, reproducible build identity
and byte integrity. The versioned canonicalization specification in FND-05
must classify collections as ordered sequences or unordered keyed sets, provide
independent golden bytes/hashes and define exact text/number treatment.

- Object-member order and insignificant JSON whitespace carry no meaning.
- Sets keyed by explicit semantic identity are compared/canonicalized by that
  identity; duplicate keys are errors, not another declaration order.
- Ordered pin vectors, mux inputs, truth-table bits and transport transactions
  retain order. Sorting them without an explicit semantics-preserving mapping
  changes meaning.
- Source file paths, timestamps, display labels and diagnostic annotations do
  not enter semantic architecture identity. Provenance remains available in
  cold metadata; raw file digests still cover the actual delivered bytes.
- A declared portable key is semantic identity. Renaming it requires an explicit
  correspondence for equivalence and need not preserve the hash. Renaming only
  a display label does not change semantics.
- Build identity also binds the compiler/backend, versions/options and all
  semantic dependencies identified by ADR 0003. Byte-identical output is required
  for the same pinned build contract; a semantic-equivalence mapping between
  different builds does not promise identical dense IDs or physical encoding.

No digest value in FND-02 demonstrates an executable canonicalizer. FND-05 owns
its algorithm/version and byte-level conformance; DB-04 owns the later compiled
binary representation. Neither may hash a Rust memory image or allow local
paths/timestamps to masquerade as semantic input. A checksum detects corruption;
it does not authenticate the publisher.

## Bounded walk-through

The following is an illustrative envelope shape, not an executable fixture or
a released schema. Names and version numbers are examples; FND-05 must publish
one exact schema rather than treating this sketch as a second authority.

```json
{
  "format": "nodal-fpga.arch",
  "version": {"major": 0, "minor": 1},
  "profile": {"id": "example-tiny", "revision": 1},
  "required_features": [{"id": "hierarchical-templates", "revision": 1}],
  "optional_features": [],
  "annotations": {"example.org/review-note": "illustrative only"},
  "body": {
    "templates": [{"key": "tile", "ports": ["west", "east"]}],
    "instances": [{"key": "tile_0", "template": "tile"}]
  }
}
```

Reordering object members has no semantic effect. Changing the example minor
version to an unsupported value fails before lowering. Adding `boddy` fails as
an unknown envelope field; moving it into annotations does not make it a
payload. Adding a required unsupported pass-switch capability fails explicitly.
A comment in an unknown annotation namespace may be omitted with a diagnostic,
but a timing exception or reset mode may not be hidden there. These are paper
expectations for later independent conformance tests, not execution results.

## Alternatives, costs and ownership

JSON trades file size and parsing cost for inspectability and easy independent
fixtures at Foundation scale. Repetition remains compact; JSON is not selected
as the permanent high-volume DeviceDB format. DB-04 evaluates FPGA Interchange
subsets and binary encodings against measured requirements, without importing
their in-memory layout into core.

Live cross-language objects couple runtime and ABI lifetimes; an obligatory
JVM/MLIR bridge violates saved-package independence. A new general-purpose
compiler IR would duplicate another project's responsibility without evidence.
An immediate binary schema would add design and debugging cost before semantic
fixtures exist. These alternatives are deferred, not described as inherently
incapable or slower.

FND-04 implements foundational model/types; FND-05 implements minimal Scala
writer/Rust reader and strict conformance. DSL-01–04 own the usable authoring
frontend and parity; DB-01–06 own production lowering/queries/storage. CAD owns
customer interchange and tool adapters. Independent expectations must not be
derived solely from the writer/reader pair under test. See the complete
[ownership audit](../contracts/foundation.md#later-track-ownership-audit).

This increment does not affect generated Verilog.
