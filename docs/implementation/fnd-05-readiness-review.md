# FND-05 readiness review and R1–R5 disposition

Latest disposition: **accepted as the implementation-readiness contract** after
the original independent reviewer verified the exact submitted files. The final
verification below resolves the historical pending statements retained in this
submission record. No implementation, execution or increment acceptance is claimed.
Readiness publication and explicit coordinator GO remain the next gates.

## Actual independent review basis

The original independent reviewer returned **HOLD for five narrow contract edits;
no scope expansion required**, and reported no other critical ambiguity within
that review's stated scope. The coordinator agreed to R1–R5 on 2026-10-15. The
reviewer inspected repository instructions, complete Foundation/FND-05 checklist,
ADRs 0001–0003, architecture/verification/early-baseline/foundation/core contracts,
FND-04 code and ownership guard, the proposal, independent expectations and
runtime-capacity report. It did not run candidate code, builds, installations,
downloads, or remote writes, and wrote only its requested outside-repository report.

Immutable identities of the original materials:
- Proposal SHA-256: `a7d1df92a9e4c1bb3d27dec183130872d6ac766037272a25e1b464b1ef868945`
- Independent expectations SHA-256: `67436527d7357a98e620a2df532cc6fdba2de696b9e48217154cb71647015546`
- Original independent review SHA-256: `c999274579525adb5368463251e6a11066086578d1534df647568e0249e4a5d8`
- Revised readiness SHA-256 submitted for verification: `e3009777ed48720e2a9391dbcefe396a368bccc7700d053ed57d0bec076cfdc1`

The original review observed implementation merge
`f9fdd8cf8363104bfa0f4063fd851016eb462bec` while closure edits were still pending.
Its read-only comparison with tested candidate
`bc6e3264d5ee8489b8a606d9e7de568ad0f99a7e` found unchanged public core code/API.
It did not independently verify later FND-04 accepted integration. The coordinator
subsequently verified closure PR 8 at
`c508401afb3bc172a28163b84375157e1ce2ac2d`, tree
`c5ebc61886eb5903d3ca654b118edf3bc4d63276`; the revised readiness accurately records
that later base. No historical review result has been relabeled as later execution.

## Findings, incorporated dispositions, and required tests

| Finding | Incorporated disposition | Required test/control, not yet run |
| --- | --- | --- |
| R1: “resource_type key of kind BEL” confused key kind with declaration kind | Section 6 requires Key<ResourceType>, wire key.kind resource_type, resolving to ResourceType.kind bel; mode belongs to that declaration | Valid BEL declaration succeeds; bel-typed key, wire declaration, missing type or mode fail their intended checks |
| R2: numeric literal -0 was ambiguous | Sections 3–4 specify literal grammar 0 or nonzero-leading signed integer, exact u16/i32 range, and rejection of negative zero/fractions/exponents; decoded U64-string grammar stays separate | Metadata/annotation -0 rejects; valid 0 and i32 endpoints pass; adjacent overflow, 1.0, 1e0, -0.0 and -0e0 reject; escaped decimal digit string remains valid |
| R3: artifact limits were eventual rather than complete preflight | Sections 7/9 admit all descriptors/distinct digests before resolver calls, require consistent reused lengths, checked declared aggregate/count/per-item limits, and at most one bounded actual read per digest | Conflicting lengths/count+1/declared oversize/aggregate+1 make zero calls; exact lowered boundaries, lying/short/appended/nonterminating streams and backing mutation exercise measured read bounds and immutable reuse |
| R4: dependency transitivity and self-referencing design prohibition were ambiguous | Section 7 parses only architecture; library/view artifacts are opaque flat leaves; manifest has no mapped-design role; tool digests are identities only | Nested manifest/URL/design-looking opaque bytes cause no extra reads/execution; added design role rejects; design bytes as architecture reject; bound opaque roles do not activate unsupported operations |
| R5: generic late identity checks contradicted early design-target validation | Section 9 fixes operation-specific staging: common decode; architecture validate/self-ID; package preflight/build-ID before resolver and raw digest before interpretation; design target before lookups | Wrong target plus nonexistent reference yields target mismatch without lookup; bad build ID makes zero calls; bad digest is not masked by architecture failure; late self-ID failure publishes no accepted output |

All rows are **incorporated, awaiting original-reviewer verification**. Their
presence is not evidence that implementation tests passed. The complete required
cases remain in readiness section 11, including controls against unrelated
failures being mistaken for successful negative tests.

## Other actual review conclusions retained

The original reviewer found no need for broader redesign of the proportionate
three-envelope scope, obligation map, FND-04 semantic authority, immutable package/
customer ownership, explicit canonical comparator/projection/domain separation,
annotation preservation, dependency inventory, independent goldens, or actual
saved-runtime requirement. Those conclusions are design review only.

Two implementation review checkpoints remain explicit in revised sections 4/9/11:
- Required-nullable fields remain required. Plain Option/default deserialization
  must not turn missing alias_of/partition/selector/span/display into null.
- Preserve input order long enough for promised schema fail-fast error ordering;
  a sorted intermediate map must not silently change it. Duplicate detection,
  canonical sorting, and error traversal have separate responsibilities.

Also retain all-array/all-object/mixed nesting 64/65 checks including scalar
leaves and envelope overhead; configured limits versus actual counts; traversal/
drop safety; exact new design/manifest work accounting before limit acceptance;
complete resolved dependency identities/edges/features/hook review; and real
Scala/prebuilt-Rust positive and negative executions in the same reviewed runtime.
A library recursion failure, empty PATH, capacity probe, or network-denial filter
is not by itself the claimed input-limit/runtime acceptance evidence.

## Coordinator clarification included for verification

After the original review, the coordinator relayed the independent golden author's
identity clarification. A hand-authored independent package declares authoring
unbound/not-supplied, avoiding false Scala attribution. Only the actual Scala demo
binds nodal-fpga/scala-fixture-writer version 0.1, its exact source/source-manifest
hash supplied and verified by the harness, and named Scala compiler/version
identity options. Source identity is not publisher authentication. Revised section
7 records this clarification; it is included in the pending re-review scope.

## Next gate

The readiness author has stopped edits after these two documentation files and
reported their exact hashes to the coordinator. The coordinator should ask the
original reviewer to verify the revised files/hashes and return an explicit
result. Only after that response may this document record the actual verified
disposition. The parent owns first readiness commit/draft PR, any required
scheduled-continuation setup, and explicit implementation GO. No scheduled hourly
monitor or CI launch is claimed here. All FND-05 leaves remain required and open;
no checklist amendment is proposed or made.

This increment does not affect generated Verilog.

## Final independent verification — 2026-10-15

The original independent reviewer verified readiness SHA-256
`e3009777ed48720e2a9391dbcefe396a368bccc7700d053ed57d0bec076cfdc1` and the
submitted review-record SHA-256
`0c9bddafce5f94731c4417605fb53cd5d3d3aef56e63a5d3e7adbe536713ac17`.
R1–R5 are correctly incorporated, resolving the previous HOLD. Required-nullable,
input-order and recursion-bound checkpoints remain explicit. The independent
hand-golden versus actual Scala authoring-identity distinction is coherent and
avoids source self-reference.

Local HEAD/tree match `c508401afb3bc172a28163b84375157e1ce2ac2d` /
`c5ebc61886eb5903d3ca654b118edf3bc4d63276`; the public FND-04 model/API remains
unchanged from the reviewed implementation. No additional blocking contract issue
was found. This was read-only verification, with no builds, downloads or
implementation execution. Readiness publication and explicit parent GO remain
required; all FND-05 implementation and acceptance obligations remain open.

This final disposition records the returned review; the readiness contract bytes
are unchanged. The earlier pending statements describe the submitted record, not
an unresolved review. This review record itself changes only to record that result.
