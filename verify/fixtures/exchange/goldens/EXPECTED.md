# Independent full-envelope hand expectations

Status: authored outside the repository for independent review before copying.
These are full envelope inputs expected to satisfy the frozen contract, not a
claim that any candidate reader, writer, parser, validator, runtime or CI has
accepted them. No candidate output established any expected answer. No repository
source was changed, no tools installed and no remote writes performed.

Basis: the original final readiness proposal and its independent R1–R5
review; parent-reported accepted FND-04 dev
`c508401afb3bc172a28163b84375157e1ce2ac2d` was observed as local HEAD. The tracked
`docs/implementation/fnd-05-readiness.md` at commit
`4895bcc96f527049ad1b22a206987959b11b9878` was subsequently reconciled before
freezing these artifacts. Its R1–R5 and honest hand-authored/Scala distinction
match this corpus; no wire-field changes were needed.

C00–C38 under `../algorithm/` were retained unchanged. This
folder adds complete architecture/package/design fixtures rather than promoting
incomplete C25–C27 into valid schema examples.

## Byte artifacts and independent construction

`author_goldens.py` uses fixed literal field order and manually selected array
order. It does not sort/canonicalize arbitrary data. It does not import a
repository module or execute any candidate tool. Each record is assembled with
its exact known fields, and typed provenance slots are omitted explicitly when
constructing its independently specified projection. No recursive key-name
filter computes the expected projection.

JSON files are the reviewable literal expectations. `*.canonical.json` and
`*.projection.json` contain UTF-8 without BOM, insignificant whitespace or final
newline. `*.raw.json` for architecture equals two prefix bytes (space, LF), then
the canonical document, then one LF. Its digest therefore binds bytes different
from the canonical dump. Package/design raw inputs equal their canonical files.
`*-hash-input.bin` contains the exact prefix LF plus projection, suitable for
ordinary sha256sum. SHA256SUMS binds every data artifact; IDENTITIES.md lists the
semantic/build hashes, which are hashes of the prefixed projection, not the full
JSON file.

Only standard-library JSON parsing is used to check the literal JSON syntax and
object-member order after assembly. This is not production conformance evidence.
Python hashlib and sha256sum independently agree on every file hash. Never
regenerate these expected files from candidate outputs to make a test pass.

The capability `golden.example/review` is unknown and optional. Each architecture
has corresponding root annotation data, so expect one `unknown_annotation`
notice preserving that data. Its arbitrary `count` number is nonsemantic and must
not be interpreted as a required architecture resource/instance count. The
nested Unicode object's member order is U+E000 before U+10000 in literal UTF-8.
The optional entry and annotations are excluded together from semantic identity.
Packages and designs have explicit empty annotations/optional lists and should
not emit an unknown-annotation notice of their own.

## Primary architecture: manually fixed structure

Files: architecture.raw.json, architecture.canonical.json,
architecture.projection.json, architecture.semantic-hash-input.bin.

- Namespace: `golden`.
- One resource type `generic-cell`, key kind `resource_type`, declared resource
  kind `bel`. Ordered pins are index 0 = I/input/1 bit and index 1 = O/output/1 bit.
  Name-set modes are alternate and normal.
- One template definition `tile`; its four directly owned resources are east,
  local, sink and west, all `generic-cell` BELs. These are four resources, not four
  templates. There are no resource aliases in this primary fixture.
- One local storage `cfg`, owned directly by sink, capacity 2 bits.
- One local feature `route`, owned by sink, referring to cfg, range `[0,2)` bits,
  width 2, exact finite domain `{0,1,2}`, empty guard, no feature alias.
- One local mode group `operation`, containing exactly sink, legal choices
  alternate and normal. Other resources have no required mode-group selection.
- One local connection `mux`: source vector index 0 = east.O, 1 = local.O,
  2 = west.O; destination sink.I; selector is local feature route.
- Three roots t0/t1/t2 instantiate tile in explicit partition 0. There are no
  children. The retained declaration has one template; the physical-instance
  interpretation has 3 distinct tile occurrences and 12 distinct BEL owners.
- Two architecture connections exist: edge0 is t0.sink.O -> t1.west.I;
  edge1 is t1.sink.O -> t2.west.I. There is no t2 -> t0 wraparound edge. These
  destinations differ from each tile's mux destination sink.I, so no destination
  has duplicate drivers.
- Expanding this tiny fixture by hand yields three mux occurrences and two fixed
  cross-root edges, five connection occurrences total. A canonical dump must
  retain one template and two architecture edges rather than flattening the graph.
- Four domain definitions: clock/class clock, config/class configuration,
  power0/class power, power1/class power. All roots share clock and config.
  t0 is in power0; t1/t2 are in power1. There are nine explicit root-domain
  references, with no inferred extra memberships or crossing qualification.
- Body provenance has display `Three independent mux tiles` and source identifier
  `hand-authored/architecture.scala`, declared bytes 512, span `[0,512)`. The route
  feature carries `Mux selector` and `[17,19)` in the same declared source. These
  are intentionally synthetic numeric origins, not claims about a physical source
  file or authorization to read it. Other required provenance objects contain
  explicit null display/span. Provenance survives the full dump and is excluded
  only at the enumerated typed record positions in the semantic projection.

### Primary selections, through public FND-04 Selection APIs

No Selection is serialized into any envelope. Construct the following separate
inputs in tests, with independently supplied provenance as desired:

1. Modes: t0.operation=normal, t1.operation=alternate, t2.operation=normal.
   Feature writes: t0.route=0, t1.route=1, t2.route=2. Expect valid completeness,
   independent instance ownership and selected sources t0.east.O, t1.local.O,
   t2.west.O respectively.
2. Change only t1.route to 3. It fits two bits but violates `{0,1,2}`; expect
   intended `value` diagnostic at t1.route, with actual 3 and feature-origin context.
3. Omit t1.route while retaining all modes: expect `missing_selection` for its
   active storage class; no implicit value 0.
4. Omit t1.operation while retaining feature values: expect `missing_selection`
   for that instantiated mode group; no default mode.
5. Supply t1.route twice, even with equal values: expect `duplicate` rather than
   silently taking first/last or treating it as the same explicit write.
6. Use field path `["t1",".."]`: no such child is declared in tile; expect missing
   path resolution. Dot-dot does not mean parent traversal.

Ordered mux expectations are hand-stated, not simulated hardware: with source
values east=1/local=0/west=0, value0 selects 1; values1/2 select 0. Assignments
0/1/0 and 0/0/1 independently distinguish indices1 and2. No LUT/register/RTL
behavior is claimed by these structural facts.

### Declaration-order and cold-field variants

- architecture-root-permuted.raw.json swaps the t0/t2 root declarations.
  architecture-set-permuted.raw.json additionally changes feature-domain order
  to `[2,0,1]` and mode-name order to `[normal,alternate]`. Both must canonicalize
  exactly to architecture.canonical.json and preserve the primary semantic ID.
  Neither edit changes ordered pin/mux/path vectors. These raw files have their
  own exact artifact hashes and cannot replace the original artifact under its
  package descriptor, even though their semantic/canonical form agrees.
- architecture-mux-reversed changes the source vector to west/local/east and
  independently recomputes its semantic ID. It is structurally valid. Selector0
  chooses west, selector1 local, selector2 east; identity differs from primary.
- architecture-pins-reversed keeps pin names/directions but changes interface
  vector order to O then I. It is structurally valid and has different semantic
  identity under the explicit ordered-pin contract. Named connection lookup need
  not change just because the interface order changes; no hardware equivalence
  claim is inferred either way.
- architecture-cold-edit changes body display/source and root annotation text.
  Its semantic projection is byte-identical to the primary projection, its
  semantic ID is identical, and its full/raw artifact hashes differ. No semantic
  resource name, reference, value or required capability was changed.

## Focused hierarchy fixture

Files: architecture-hierarchy.*.

Two template definitions are retained: leaf and wrapper. Leaf owns one BEL cell.
Wrapper has no resources/features/storage; it has two children named literally
`..` and `a/b`, both instantiating leaf with null partition inheritance. Root r
instantiates wrapper with explicit partition 0. All required empty arrays exist.

There are three instance occurrences total (one wrapper and two leaves), two
physical BEL owners, and one architecture edge: r/child `..`/cell.O -> r/child
`a/b`/cell.I. Both leaf occurrences inherit partition 0. Exact reference paths
are `["r",".."]` and `["r","a/b"]`. Do not join them into a filesystem path.
There is no child `a` then child `b`, and dot-dot does not resolve a parent.
No mode/feature selections are required; an empty Selection is complete.

Changing the destination path to `["r","a","b"]` while keeping the declarations
must fail missing child resolution, not match the literal `a/b` child. Changing
`["r",".."]` to `["r"]` does not denote the same resource: wrapper owns no cell.
Adding recursive wrapper containment is a separate `template_cycle` failure;
the bridge itself is ordinary directed connectivity, not template recursion.

## Focused alias fixture

Files: architecture-alias.*.

One alias-tile template owns one BEL cell and one two-bit cfg storage. Feature F
owns cfg range `[0,2)`, width2, Any domain. Feature alias is a direct alias of F
with the exact same resource owner, storage, interval, width and domain. Both
have empty guards. Roots t0/t1 independently instantiate the template in partition0.
There are two physical resource owners and two independent writable storage
classes, each class having two active names. There are no mode groups or edges.

Separate Selection cases:

- t0.alias=1 and t1.F=2: valid. Each instance class has one explicit active write,
  and different instances may hold different values.
- t0.F=1, t0.alias=1, t1.F=2: valid equal simultaneous alias writes.
- t0.F=0, t0.alias=1, t1.F=2: `conflict` in t0's class.
- t0.alias=1 alone: `missing_selection` for t1's active class.
- t0.alias=4, t1.F=2: `value`, because 4 does not fit width2.
- Declaring alias as a chain through a second alias should fail `alias_chain`.
  Declaring a different slice/domain/owner must fail intended alias consistency,
  not be “fixed” by overwriting the owner or deduplicating declarations.

## Focused exact high-u64 fixture

Files: architecture-high-u64.*.

One large-offset template, one cell owner, one cfg storage whose bit capacity is
18446744073709551615 (u64 MAX), and one last-bit feature at start
18446744073709551614 with length1/width1/Any domain. Its checked half-open end is
MAX, so it fits exactly. One root t0. These are scalar logical quantities: no
MAX-sized array, byte buffer or full configuration bitmap should be allocated.
Selections t0.last-bit=0 and =1 are valid; =2 fails `value`. Replacing start with
MAX while preserving length1 fails checked range endpoint overflow.

This does not establish that a real MAX-bit device exists or can be programmed.
It exercises exact integer interchange and tiny-allocation logical validation.

## Exact software-only package

Files: package.*, and package-cold-edit.*.

The primary architecture descriptor binds the exact architecture.raw.json bytes,
including its leading/trailing whitespace. Expected descriptor:

- bytes = "6624"
- sha256 = 432171ad8cfc32c3a684584c6af990f8a665a89fcd7c74a03f421490a44601f5
- architecture semantic_id = 0c5e51acf90f91981b7e3375e5ab58b05d20020aa51a594008f8d7a30e1c80a4

Libraries is explicitly empty. Authoring is unbound/not-supplied because these
bytes were independently hand-authored. The parent clarified that the proposal's
bound Scala authoring requirement applies to the separate actual Scala demo;
it must not falsely attribute this golden to Scala. Compiler, backend, device_db,
physical_implementation, technology, configuration_map, transport, activation,
timing_datasets and external_pin_map are unbound/foundation-unimplemented.
macro_bindings is absent/no-hard-macros. Null is not used as a binding state.

Successful package consumption uses exactly one resolver request for the primary
architecture raw digest and returns that immutable accepted architecture. It has
no tool implementation digest request and no recursive dependency resolution.
The manifest's own bytes are not counted in its one-artifact aggregate. All
unsupported operations (RTL, DeviceDB queries, physical/timing/programming) remain
unsupported regardless of parsing success or named fields.

The cold-edit package references the cold-edit architecture's changed exact
bytes. Architecture semantic identity remains equal, but package build identity
differs because the raw digest/length binding remains semantic package data.

Required focused negatives without deriving answers from candidate output:

- Original descriptor + canonical bytes instead of exact raw bytes: length and
  digest mismatch; do not canonicalize artifacts before raw verification.
- Correct length + different bytes: `artifact_digest`.
- Correct digest + descriptor length one smaller/larger: intended descriptor/read
  length failure, never silent truncation/padding.
- Missing supplied artifact: intended missing-artifact failure; no network fetch.
- Wrong manifest self-build ID: zero resolver calls before rejection.
- Changed config/physical/timing/pin binding with unchanged build_id: build-ID
  mismatch before resolver calls. With an independently recomputed valid build ID,
  a bound opaque artifact would still require its own byte verification and would
  not enable unsupported physical operations.
- Wrong architecture raw digest, with underlying architecture semantic defect:
  raw integrity failure occurs before architecture interpretation.
- A design-looking payload supplied as architecture, with correct raw descriptor:
  exact format mismatch; no filename/kind inference.

## Target-bound mapped design

Files: design.*; design-cold-target.* is a valid counterpart targeted to the
cold-edit package, not to the primary package.

Design namespace golden-design, name demo. Two customer cells: c0 uses the
resource_type key generic-cell with declared BEL kind and mode normal; c1 uses
the same type and mode alternate. The key's own kind is resource_type, never bel.
These cells do not mutate or reserve physical architecture instances.

Ports: flag/output/width1; in/input/width2; out/output/width2. Nets:

- n0: top input in[0] -> c0.I[0].
- n1: c0.O[0] -> c1.I[0] and top output out[0]. Loads are sorted cell then port.
- n2: c1.O[0] -> top output out[1].
- n3: constant "1" -> top output flag[0].

There are 4 nets, 4 drivers (one is a constant), 5 load endpoints, 8 distinct
nonconstant terminal ownership records, and one unconnected terminal in[1].
There is no terminal repeated across records. Unconnected input in[1] is allowed
at this structural layer. No bus is expanded during parsing. The type/mode/pin
checks use the already verified package's saved architecture. No packing,
placement, route, primitive functionality or physical timing is established.

- Primary design target equals the primary package build ID and must pass exact
  target comparison before type/mode/pin lookup. Its own semantic ID includes
  that target_build_id.
- design-cold-target has a different target and a separately correct self-ID.
  It is valid against package-cold-edit, but must report target_build_mismatch
  against the primary package even though the architectures are semantically equal.
- Wrong target plus nonexistent type/pin still reports target_build_mismatch
  before a target lookup. Wrong self-ID with correct target must reject after
  structural checking, without publishing accepted canonical output.
- BEL key kind in Cell.resource_type is wrong typed-key data; matching local text
  does not repair it. A resource_type key resolving to a wire type is also invalid.
- Using cell input as driver, top input as load, or constant as load rejects direction.
- Reusing out[0] in another load, repeating c0.O[0] as a second net driver, or
  listing c1.I[0] twice rejects terminal ownership duplication.
- Port bit2 for width2, or cell pin bit1 for width1, rejects bounds.
- Unknown mode/type/pin rejects its intended lookup category.

## Diagnostic naming

Selection/architecture categories such as value, missing_selection, duplicate,
conflict and alias_chain are original FND-04 diagnostic codes retained inside an
exchange `semantic` failure when applicable. Exchange identity failures use
`identity_mismatch`; package byte failures use `artifact_missing`,
`artifact_length` or `artifact_digest`; mismatched design target uses
`target_build_mismatch`. Do not invent a generic artifact_digest_mismatch code.
Public Selection-only tests see their original FND-04 diagnostic directly.

## Audit status and limits

The supplied Python/shell audit checks exact SHA files, object-member UTF-8 order,
field inventories and manually authored collection order, endpoint bounds and
fixture-specific hand expectations without calling candidate code. Such an
audit is a check on oracle transcription, not a substitute for later independent
review and real Scala/Rust conformance execution. FND-05 remains open.

This increment does not affect generated Verilog.
