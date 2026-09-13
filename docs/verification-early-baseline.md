# Early fabric baseline and assumption contract

This is an acceptance specification for the [roadmap](roadmap/README.md), not evidence of an implemented verifier or passing fabric. It supplements the [verification policy](verification.md). The owning track checkboxes remain the only progress record; this document does not duplicate their state.

## Gate ownership and sequencing

| Owner | Required evidence before closure | Deliberate boundary |
| --- | --- | --- |
| FND-02 | Reviewed independent tiny specification, declared FABulous common subset, correspondence rules and assumption ledger | Contract decisions, not execution claims; resolve critical semantic ambiguities before acceptance |
| FND-06, then FND-08 | Pin and generate reference LUT/register/switch/tiny-tile artifacts; compare against hand-calculated vectors and an independently enumerated graph; demonstrate relevant mutation detection | A minimal Foundation-owned test harness, not production Nodal fabric generation, VER-01, or CAD integration |
| DB-01–04, DB-06 | Independent tiny checks of representation and rebuild equivalence | No production RTL or late VER dependency; exhaustive expansion is only a tiny-test oracle |
| RTL-01, RTL-02 | Compare actual emitted primitives/switches/tiles with the independent specification and matched FABulous-generated resources | Match supported semantics; do not equate equal resource counts or Verilog text with correctness |
| RTL-03 | Compare actual generated small fabrics under corresponding hand-specified legal configurations and reset/state assumptions | Static unit setup is labelled; no completed runtime-loader or complete CAD-flow claim |
| RTL-04 | Drive each generated fabric through its actual configuration loader; compare functional operation after declared activation/reset alignment | No hierarchical force, memory preload or hardwired-bitstream substitute |
| VER-04, VER-05, VER-07 | Full user-design flow, pinned cross-generator regression, early-baseline replay and release traceability | Retain independent models and all existing formal, coverage and physical/silicon gates |

All non-Foundation increments retain FND-08 as a blocker. Foundation does not depend on VER-05 or an unfinished Nodal generator. Its bootstrap reference harness lives with `verify/fixtures/` and may later be reused by `adapters/fabulous/`; reuse must not invert dependency ownership. External reference tools belong to the test environment, not core or saved-package runtime dependencies.

The early comparisons are acceptance obligations, not optional experiments. Missing tools or reference artifacts, unreviewed correspondence, and unresolved critical common-subset mismatches block the owning gate. Explicit Nodal-only capabilities still require independent verification; an unsupported comparison is not a passed comparison. Any change to required scope follows the existing roadmap amendment policy, not an ad-hoc waiver.

## Independent inputs and artifact contract

Begin with a hand-reviewed specification. Describe it independently in the FABulous input format and Scala/ArchIR once that frontend exists. Do not use the production Nodal emitter, configuration allocator or topology normalizer to manufacture expected results or silently translate away mismatches. Record shared code, simulators, synthesis tools and primitive libraries as possible common-mode failure sources.

Each matched fixture records the reference revision and dependencies, input files and hashes, supported modes, dimensions, generated artifacts, resource/pin correspondence, legal configuration constraints, reset/initial-state/clock assumptions and expected vectors. The manifests also record the checker revision, commands, solver/depth where applicable, coverage denominator, negative cases, artifact hashes and actual results. Changing a reference revision or correspondence map requires replay and review; never automatically regenerate a golden answer from the candidate.

A pin/resource correspondence map must be total and unambiguous over the declared matched subset, with explicit documented aliases and exclusions. Validate it independently, including a deliberately wrong map. It may account for pin permutations or different configuration encodings, but it may not erase direction, control priority, shared-resource restrictions or observable behavior. If results disagree, retain a minimized reproducer and resolve it using independent semantics rather than a majority vote between tools.

## Matched-subset test obligations

Specify LUT address-bit order and all input selections; register edge, reset/enable priority and initialization; fixed versus programmable links, buffered/pass-switch behavior where supported, mux selection exclusions and shared controls; configuration bit significance, address order, defaults and aliases; and user/configuration clock separation and I/O behavior. Do not assume unconfigured memory powers up cleared.

Use asymmetric configurations and pin patterns, not only symmetric AND/XOR examples that can hide permutation errors. Cover 1x1, 2x2, odd/boundary-heavy and sparse/asymmetric cases where genuinely supported by each selected profile. Document unavailable shapes or modes and verify Nodal-only cases independently. The common subset is a test contract, not a permanent architectural limit on Nodal-FPGA.

Keep two corpora. A hand-configured generator corpus isolates resource/wiring/configuration behavior without synthesis or placement/routing. A later application corpus maps the same user RTL through each full toolchain and checks each configured fabric against the original design. Different legal placements, routes and configuration bytes are allowed unless identical encoding is an explicit requirement. PPA comparisons need matched physical conditions and are benchmarks, not functional proofs.

From RTL-04 onward, apply transport-specific sequences through both actual loaders, recording each load-complete/activation event and resetting user state under the reviewed contract. Align user-cycle observations after activation rather than assuming equal transport latency. Verify each startup/containment contract separately when wrappers differ; do not mask failures with testbench initialization. Include interrupted loads, invalid addresses, reset/clock interruption and loading a second unrelated configuration. Model-only/static-unit tests remain separately labelled and cannot count as runtime-loader coverage.

Prove tractable primitive/tile properties over symbolic legal configuration and state relations where feasible; otherwise state the simulation/proof scope. Include cover witnesses against vacuity and targeted mutations for LUT indexing, endpoints, field aliasing, reset priority and correspondence maps. The intended check must detect the mutation; a timeout or unrelated crash is not successful fault detection. End-to-end samples do not establish all-configurations correctness.

## Assumption ledger

FND-02 creates the initial machine-readable ledger under `verify/fixtures/assumptions/`; this planning document does not create populated evidence or choose a production schema. Use stable identifiers such as `ASM-0001` and preserve supersession history. FND-03 completion templates and later verification manifests reference these identifiers.

Each record must contain the normative claim, profile/version scope, rationale or source revision, owner/reviewer, affected consumers, independent expected examples, owning increment, required test/proof/mutation IDs, and change/invalidation policy. Keep the decision state (proposed, accepted-for-profile, disputed, superseded) separate from evidence state (not-run, passed-with-stated-scope, failed, unavailable). Record formal bounds and assumptions explicitly rather than treating any bounded result as an unbounded pass.

Examples of claims to resolve are LUT input significance, reset/enable priority, mux polarity, shared-field ownership, safe configuration activation, package identity and permissible graph transformations. These are categories for review, not approved facts. FND-02 may schedule later execution without claiming it has occurred; FND-06/RTL/DB closure requires the stage-specific evidence actually due. Unresolved critical semantic ambiguities block contract acceptance. Changed claims invalidate affected fixtures, generated views, configuration bindings and released-package claims until reviewed and retested.

## Representation-invariance

Use an independent simple enumerator for tiny devices to check compact templates versus explicit resources, sparse exceptions and inter-partition links. Compare partitioned versus unpartitioned views, allowed declaration reordering/internal renaming, portable versus mmap readers and full versus incremental builds. Check resource roles, pin/direction mappings, fixed/selected connectivity, legal-mode exclusions, shared controls and configuration semantics, not only counts.

These transformations are valid only under the declared semantic identity map. Do not reorder semantically ordered mux inputs without translating their selection encoding. Dense IDs, binary section order and physical bit locations may change; preserve or rebind the configuration contract and publish a new package identity when required. Reject incompatible old bitstreams. Byte-identical determinism applies to identical semantic inputs under the pinned build contract, not to arbitrary identity or package-layout changes.

Inject omitted boundary edges, reversed edges, incorrect partition offsets, stale cached configuration maps and broken identity maps. Require the relevant comparison to fail. Keep these checks bounded to independent tiny fixtures; benchmark large synthetic representations separately without requiring full expansion of every large device.

## Evidence and limits

Record actual Scala input and generated Nodal fabric RTL when available, the independently authored FABulous input and its generated RTL, and configuration/bitstream/load traces at the appropriate stage. Do not present hand-written illustrative RTL as generated output. FND reference preparation cannot close RTL or VER increments, and a later passing example cannot retrospectively establish missing early evidence.

VER-07 replays affected baselines at the qualified head/profile and checks assumption-to-evidence traceability. The existing policy still governs physical signoff, emulation and silicon correlation. This strategy reduces unchecked assumptions and exposes changes early; it does not promise zero rework or turn comparison with another generator into commercial silicon qualification.
