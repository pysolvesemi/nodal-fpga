# Foundation architecture and ownership contracts

Status: accepted for the Foundation profile following [independent FND-02
review](../implementation/fnd-02-independent-review.md). Normative words specify
reviewed behavior; contract acceptance does not establish execution.
The [Foundation checklist](../roadmap/tracks/00-foundation.md) remains the sole
progress authority. No checkbox is completed by the existence of this document.

This contract refines [architecture](../architecture.md),
[verification policy](../verification.md) and
[the early baseline](../verification-early-baseline.md), following
[ADR 0001](../adr/0001-optional-circt-backend.md).
[ADR 0002](../adr/0002-portable-architecture-exchange.md) owns portable exchange
and strict compatibility; [ADR 0003](../adr/0003-device-design-ownership.md) owns
representation lifetimes, identity and external-CAD-first boundaries. Do not
maintain competing field/type definitions in each consumer.

## Scope and authority

FND-02 freezes reviewed semantic decisions and independently stated examples.
It does not require the executable Scala DSL, production DeviceDB, fabric
emitter, loader or a general compiler framework. FND-04/FND-05 own the initial
executable types and schema/writer/reader. FND-06 executes independent vectors
against the pinned external reference; later tracks implement their own
consumers and proofs. Every non-Foundation track remains blocked by FND-08.

The profile-specific source of LUT/register/configuration facts is
[the nf-tiny contract](nf-tiny.md), with independently authored
[specification](../../verify/fixtures/nf-tiny/specification.json),
[reference inventory](../../verify/fixtures/nf-tiny/reference.json) and
[correspondence](../../verify/fixtures/nf-tiny/correspondence.json).
The [assumption ledger](../../verify/fixtures/assumptions/ledger.json) assigns
stable claim, owner, consumer, test/mutation and invalidation identities.
These profile contracts, not a generic DFF intuition or a moving upstream
manual, decide exact supported register controls and reference correspondence.

A review accepts a claim for a named profile/revision; it does not change a
not-run test into a pass. Critical ambiguity in behavior, mappings or legality
blocks contract acceptance. Nonblocking choices such as a future binary layout
may remain with their named later owner, without weakening due semantic work.

## Primitive, mode and interface semantics

Each primitive contract identifies its revision, typed pins and directions,
widths, parameter bounds, legal modes, configuration features, observable
behavior and applicable state/clock assumptions. It also names independent
expected examples and the capabilities required of each implementation.

- LUT contracts state input significance, truth-table indexing, output polarity
  and all legal parameter/mode combinations. An asymmetric table is required
  to expose pin permutations that AND/XOR-only examples could hide.
- Sequential contracts state active edge, supported controls and their priority,
  whether controls are synchronous/asynchronous, and initial-state assumptions.
  Presence or spelling of a pin does not establish behavior. Unsupported reset,
  enable or initialization modes must be rejected, not emulated silently.
- Mux contracts state the ordered input list, selection encoding, valid values,
  and explicit default/off behavior if any. Reserved or invalid selection is a
  legality error, not an invented constant output or an accidental don't-care.
- Constants and simple I/O declare direction, polarity and modeled values.
  Digital wrapper behavior does not imply pad electrical, tristate, ESD or
  analog qualification. Four-state and two-state assumptions are explicit.
- A mode describes legal use of resources/pins/configuration, including occupancy
  and exclusion constraints. It is distinct from a clocked runtime control and
  from a physical macro implementation. Mutually exclusive modes cannot be
  enabled together merely because both have individually valid settings.

Logical configuration is separate from transient user state. No unspecified
configuration storage or user register is assumed to power up cleared. Explicit
legal defaults do not imply hardware initialization. Startup, load completion,
activation, quiescence and user-state alignment are separate named obligations;
static unit setup does not establish a working runtime loader.

## Templates, hierarchy and resource sharing

A template describes reusable structure and local semantic keys. Instances bind
validated parameters and ports and acquire distinct qualified identities.
Repeated instances share a definition, not physical wires, configuration bits
or customer occupancy. A repeated declaration cannot accidentally alias state.

Resolve parameter types/ranges before lowering. Preserve finite hierarchy and
repetition across the Scala/Rust handoff; avoid allocating the entire large
routing graph on either side merely to serialize it. Template instantiation
must terminate. Graph cycles in physical connectivity are a different concept
and are allowed subject to selected-state legality.

Sparse overrides name an existing instance/local resource and a field the
template expressly permits overriding. Reject unknown targets, duplicate or
conflicting overrides, unresolved parameters, out-of-range indexes and dangling
ports. No order-dependent last-writer-wins override rule is implicit. Removing
a site or creating a sparse hole must explicitly account for its incoming and
outgoing edges; boundary endpoints cannot wrap around or disappear unnoticed.

Physical sharing is explicit and separately modeled:

- Every physical resource has an owning declaration and typed identity.
  Intentional aliases reference that owner rather than duplicating it.
- Shared-control groups declare consumers, permitted settings and consistency
  constraints. Occupancy/exclusion groups state which simultaneous uses are
  legal; mode selection must satisfy the group, not just each member locally.
- Logical configuration features declare width/domain/meaning and their owner.
  A shared feature/alias has an explicit mapping and consistency condition.
  Multiple symbolic names for one field do not create independent storage.
- Physical bit overlap is illegal unless the allocation map explicitly declares
  the same owner/alias relation and its legal-value constraints. Contradictory
  writes through aliases are rejected. A shared default cannot hide a conflict.
- Deduplicating a type or immutable table is a representation optimization.
  Merging instance identities, writable fields or independently occupiable
  resources changes architecture meaning and needs a different contract.

The exact executable mechanisms belong to FND-04 for tiny semantic constraints,
then DB-02/03 and CFG-01/02 for production ownership/allocation. No whole-device
configuration allocator is required merely to review these rules.

## Connectivity and domains

A routing edge declares source/destination direction, fixed or selectable
connectivity, supported buffering/pass-switch behavior, owning selection
feature, and capacity/exclusion/shared-control constraints. A bidirectional
pass device is not two independent buffered drivers. Unsupported electrical
semantics are rejected at the selected profile/operation boundary.

The full architectural graph may contain cycles. A selected legal configuration
must still satisfy contention, mux exclusivity, occupancy and the profile's
policy for customer combinational loops. Checking counts or acyclicity alone
cannot establish correct selected connectivity. Pin permutations require an
explicit map of behavior and selection encoding; they cannot be normalized
away to make two incorrect graphs agree.

Clock, power, configuration, placement and routing domains are overlapping typed
memberships, independent of the containment tree. For example, two instances
can share one user-clock domain, use different power domains and belong to one
configuration domain. That declaration is not evidence that cross-power
isolation, regional reconfiguration or multiple clocks is implemented.
Crossings require declared interfaces and applicable supported capability
checks. Missing membership/constraints needed by an operation are errors, not
an implied global default.

A physical clock source/buffer/mux and its reach/capacity are DeviceDB data.
A customer's generated-clock relation or timing exception is DesignDB intent.
Configuration transport clocks are distinct from user clocks even if a future
wrapper physically derives them from one source. Unsupported timing exceptions
cannot be dropped. Timing values carry units, corners, load/slew/transition
assumptions and provenance; absent characterization remains unknown.

## Technology and package binding

Reuse ADR 0003's complete package identity; do not invent a weaker identity for
a specific adapter. Process-independent interfaces describe required capability.
Technology bindings provide exact cells/macros, supplies, modes, physical/simulation/
timing views and characterization/access limits. An unbound logical fixture can
exercise semantics but cannot certify physical implementation or programming.

A package binds architecture/library/profile, implementation, configuration map,
loader contract, timing sets, pin map, schema/features and compiler/tool inputs.
Changing any semantic dependency requires a new identity and impact review.
Exact target-build checks apply to design checkpoints and configuration before
their respective consumers run. A changed pin map or configuration encoding is
not compatible because the family name remains `nf-tiny`.

No architecture portability claim implies automatic PDK migration. No simple
behavioral PLL, clock wrapper or memory model implies qualified hard IP. Core
can describe capability requirements without depending on proprietary files;
actual restricted views are separately managed by authorized adapters.
Checksums identify bytes, not trusted publishers or rights to redistribute.

## Actionable unsupported-feature policy

Every requested operation checks its supported schema/profile/capability matrix.
An unsupported construct is not accepted as a reduced feature, default value,
empty object, black box or successful skipped test. A diagnostic must report:

1. A stable category/code and the failing operation/stage.
2. Input location plus portable resource key or source provenance where present.
3. Declared schema/profile/build and exact unsupported or conflicting value.
4. The violated constraint or missing capability and relevant related resources.
5. An actionable remedy: supported mode/profile/version, explicit qualified
   conversion, missing view/tool provision, or a clear statement that no
   supported path exists. Never promise that a later track already implements it.

Illustrative diagnostic expectations, not implemented diagnostic codes:

| Case | Required outcome and useful context |
| --- | --- |
| Unknown semantic field `resett` | Reject at its JSON path; name the supported field/contract rather than discarding it |
| Unsupported required feature revision | Reject before lowering; list requested and supported capability revisions |
| Reset mode absent from the selected primitive profile | Reject with primitive/mode/source key; no guessed reset rewrite |
| Two consumers require contradictory shared selections | Reject with shared owner and both requirements |
| Sparse hole leaves a link to a missing endpoint | Reject with link and missing instance/pin keys |
| Device-build mismatch in a routed checkpoint | Reject before interpreting dense IDs; report expected/observed identities |
| Unknown timing or missing macro view | Block the operation requiring that model; inspection may still explicitly report unknown |
| Requested optional emitter unavailable | Fail selected-backend invocation; do not silently choose the default |
| Input exceeds bounded nesting/count/size | Reject with actual bound and declared limit; do not truncate or expand unboundedly |

Unknown nonsemantic annotations follow ADR 0002's restricted escape hatch and
must never carry a hidden functional feature. Backend failure, unknown timing,
missing reference artifacts, unsupported comparison and skipped execution have
distinct statuses; none is a passing required test.

## Bounded paper walk-throughs

These hand-calculated cases exercise the contracts without claiming executable
Scala, an elaborator, simulation, formal proof or measured performance. Exact
nf-tiny LUT/register vectors remain in its separate independently reviewed
specification, avoiding a second copy here.

### Repetition and an odd boundary

Let a hypothetical tile template `T` contain one BEL with one ordered input pin
`I` and one output pin `O`. Instantiate a line with keys `t0`, `t1`, `t2`, and
fixed directed links `t0.O -> t1.I` and `t1.O -> t2.I` only.

There is one template definition, three physical BEL instances and two links.
`t2.O -> t0.I` does not exist. A 1-instance line has one BEL and zero internal
links. Reusing `T` does not alias `t0` and `t1`. Partitioning the 3-instance line
as `{t0,t1}` and `{t2}` produces one local and one cross-partition link with the
same selected connectivity. Dropping the latter preserves BEL counts but breaks
the contract. An explicit independent enumeration can detect that on this tiny
case without becoming the production storage format.

Removing `t1` yields two BEL instances. Removing the two incident links yields
zero links. A bypass `t0.O -> t2.I` would be an explicitly declared new link, not
an implicit consequence of the hole. This tests a sparse boundary independently
of a nominal rectangular interior.

### Shared selection and ordered inputs

Consider an illustrative 2-input mux with ordered inputs `[west, north]` and a
one-bit feature `S` where `0` selects west and `1` selects north. This is a paper
example, not a claim about the pinned external reference encoding.

Two aliases of the same physical `S` requiring `0` and `0` are consistent;
requirements `0` and `1` conflict. Two distinct tile-local `S` owners may legally
hold different values. Reversing the input list while retaining the same bit
value reverses selection; a correspondence must translate the value as well as
the names. A compiler cannot sort the input list as though it were an unordered
set. Known expected cases must distinguish west=0/north=1 and west=1/north=0.

### Identity and overlapping domains

Let `t0` belong to clock `C0`, power `P0`, configuration `Q0`; let `t1` belong to
clock `C0`, power `P1`, configuration `Q0`. One clock membership does not merge
power ownership, and one configuration membership does not grant independent
partial reconfiguration. An operation needing P0/P1 isolation must reject a
profile lacking that capability even though the data can name both domains.

A checkpoint referring to build A, partition 0, local BEL 2 cannot be imported
against build B solely because B also contains local BEL 2. A portable mapping
may establish equivalent resources, but it must rebind the checkpoint and
independently check selected configuration/constraints. A change from physical
configuration bit 7 to bit 9 similarly requires a new map/build and cannot be
repaired by a comment or a reused family label.

## Optimization, determinism and compatibility review

The proportional choice is one semantic contract, one portable exchange and
separate independently authored expectations. Do not duplicate authoritative
modes in frontend-specific types, external tool adapters and emitter templates.
Consumer-specific representations may cache/transform those meanings, provided
independent checks and explicit correspondence establish preservation.

Preserve templates and sparse exceptions; intern cold names/provenance and reuse
immutable type/timing records when measurements later justify it. Do not mandate
SoA, mmap, CSR, one partition size, a distributed runtime or fully flat graphs
in FND-02. These are measured DB/PERF choices. The paper line example scales
conceptually as one template plus instance/boundary data; this is not a measured
memory/runtime claim or a guarantee that every irregular graph compresses.

Use a bounded basis rather than the Cartesian product of future features:
1x1, 2x2 and odd/boundary-heavy nf-tiny shapes where actually supported by each
profile, one sparse/hole case, a shared-control conflict, an ordering mutation,
a wrong-package reference and a repeated-template/partition comparison. Exact
common-reference availability is recorded in the nf-tiny inventory; unsupported
reference shapes retain separate Nodal expectations rather than disappearing.
FND-04/05 implement bounded structural/conformance checks; FND-06 owns the
reference execution, DB owns representation transforms and PERF owns measured
large-scale budgets.

Identical semantic inputs and pinned build dependencies must yield deterministic
architecture artifacts. Explicit semantic-key changes, different physical
layouts and transformed ordered lists need correspondence, not an assertion of
byte identity. CAD replay additionally records seed, workers, platform,
floating-point policy and external builds; a seed alone is not a reproducibility
proof. Requalification follows any changed assumptions, dependencies or maps.

## Later-track ownership audit

This audit covers every later track and remaining Foundation owner. It assigns
responsibility and guards against reverse dependencies; it is not execution
credit, a dependency amendment or permission to start a blocked increment.

| Owner | Consumes and implements | Boundary retained by FND-02 |
| --- | --- | --- |
| FND-03 | Roadmap/evidence parser and completion/assumption references | Contract/ledger status is separate from test execution; no semantic hardware verifier implied |
| FND-04 | Typed IDs/units, tiny ArchIR, references/modes/sharing validation | No production DeviceDB, generator or file-layout ABI required here |
| FND-05 | Exact versioned envelopes, Scala fixture writer/Rust reader, canonicalization, bounded input and compatibility corpus | ADR 0002 behavior is normative intent; no existing executable schema or saved-runtime result claimed |
| FND-06–08 | Independent reference harness/execution, pinned dependencies/policy, release replay and contract freeze | No dependency on blocked DSL/DB/RTL/CAD/VER; no Nodal-generated fabric claim |
| [DSL-01–04](../roadmap/tracks/01-scala-frontend.md) | Typed source construction, templates, parity/provenance, usable downstream author package | No per-resource JVM bridge, duplicate semantics, full JVM graph expansion or HDL compiler |
| [DB-01–06](../roadmap/tracks/02-device-compiler.md) | Validation/lowering, immutable queries, connectivity, safe compiled format, binding, incremental publication | Core remains generic; compact/expanded, partition, reader and full/incremental equivalence use independent tiny oracles; dense IDs are build-local |
| [LIB-01–04](../roadmap/tracks/03-libraries.md) | Executable primitive/vector library, tile constructors, later arithmetic/memory and qualified macro contracts | FND-02 examples do not implement reusable libraries or imply real analog/memory IP |
| [RTL-01–05](../roadmap/tracks/04-fabric-rtl.md) | Focused primitive/tile/fabric emission, actual loaders/wrappers and synthesis-safe qualification | Preserve all supported configurations; early independent/reference comparisons due at each owning gate; static setup is not runtime loading |
| [CFG-01–05](../roadmap/tracks/05-configuration.md) | Logical feature legality, physical allocation, controller, integrity/bitstreams, routed-feature qualification | Semantic sharing/defaults precede addresses; independent vectors/real loader remain required; checksum is not authentication |
| [CAD-01–06](../roadmap/tracks/06-cad-integration.md) | Mapped contracts, Yosys mapping, actual nextpnr architecture integration, independent route checks, Nodal handoff, full replay | External-CAD-first; job state never mutates DeviceDB; no blanket SystemVerilog/VHDL or Nodal-native support claim |
| [TMC-01–04](../roadmap/tracks/07-timing-clocking.md) | Clock-resource legality, single-/multi-clock constraints, timing models, characterization/correlation preparation | Unknown delay stays unknown; physical clocks differ from user constraints; no unmeasured speed grade |
| [VER-01–07](../roadmap/tracks/08-verification.md) | Independent model, proofs, composition, user equivalence, full FABulous comparison, coverage and release dossier | Foundation/early RTL obligations cannot wait for VER; no shared lowering as sole oracle; bounded proof and coverage limits stay explicit |
| [PERF-01–04](../roadmap/tracks/09-scale-performance.md) | Measured workloads, representation/read costs, CAD quality, concurrent/cache/large-package qualification | Hierarchy intent and tiny examples establish no production scale or PPA; budgets come from recorded measurements |
| [EMU-01–03](../roadmap/tracks/10-emulation.md) | Board implementation, actual target-loader recovery and release corpus on hardware | Host substitutions are isolated; no ASIC timing/electrical or manufacturing qualification inferred |
| [PHY-01–04](../roadmap/tracks/11-physical-implementation.md) | Qualified technology access/binding, hardening, post-layout/electrical evidence and tapeout readiness | Process-independent models do not grant PDK access or automatic portability; DFT pre-silicon dependencies remain; no tapeout authorization |
| [PROD-01–04](../roadmap/tracks/12-commercial-qualification.md) | Measured product requirements, real silicon correlation, SDK/release and long-lived support | nf-tiny is a software/research profile; commercial claims require device/process/package/test evidence and DFT-06/07 |
| [NAT-01–04](../roadmap/tracks/13-native-cad.md) | Optional measured decision and native pack/place/route qualification with neutral checkpoints | No inevitable EDA rewrite; external engine may remain; generic HDL synthesis stays outside |
| [ADV-01–04](../roadmap/tracks/14-advanced-families.md) | Heterogeneous resources, regional security/reconfiguration, protocol/multi-die constraints, product qualification | Naming overlapping domains/dies is not advanced algorithm or security support; future profiles need bounded work and requalification |
| [CIR-01–03](../roadmap/tracks/15-compiler-backend-evaluation.md) | Optional alternatives review, bounded prototype and separately adopted opt-in qualification | ADR 0001 unchanged; no Foundation/default dependency or general compiler IR; proceed/adopt gates remain additional requirements |
| [DFT-01–07](../roadmap/tracks/16-dft-manufacturing-test.md) | Pre-silicon fault/access/test contracts and generated artifacts, then actual silicon/tester correlation | Configuration chains are not ASIC scan; functional resource coverage is not manufacturing coverage; external labs/factories/equipment remain outside core ownership |

Important cross-track edges remain intact: PHY-01 consumes DFT-01; PHY-02
consumes DFT-02/03; PHY-03 supplies DFT-05; PHY-04 consumes DFT-05; DFT-06 feeds
PROD-02 and DFT-07 feeds PROD-03. None becomes a Foundation dependency. CIR and
NAT are optional with their existing decision gates. Hard macro, timing,
configuration and physical interfaces retain their separate evidence owners.

## FND-02 obligation mapping

This is a deliverable map, not a second status ledger. Contract acceptance is
recorded in the independent review; integration and closure remain separately
controlled by the authoritative roadmap.

| FND-02 leaves | Deliverable here and acceptance boundary |
| --- | --- |
| a.1–a.2 | ADR 0002 exchange and ADR 0003 ownership/external-CAD-first decisions; preserve ADR 0001's optional-backend gate |
| b.1 | Primitive/mode, finite hierarchy, explicit sharing and actionable rejection contracts above; exact profile behavior lives in nf-tiny |
| b.2–b.3, d.1–d.3, f.1–f.2 | Separate linked ledger, nf-tiny specification/reference/correspondence and independent review; this general contract does not substitute for those artifacts or execute their witnesses |
| c.1–c.2 | Typed overlapping domains, technology separation and exact package identity/incompatibility rules in ADR 0003 and this document |
| g.1 | Proportionate representation/duplication review: retain compact templates and generic core; defer layout choices pending measurement; no general compiler framework |
| g.2 | Bounded boundary/repetition, sharing/order, identity/domain paper cases; explicit compatibility expectations and unmeasured scaling limits |
| e.1–e.3 | All-later-track audit above contributes to review; accepted artifact revisions/hashes, applicable qualification, integration and completion remain separate closure work |

## Review and evidence disposition

Independent review must check the ADR decisions, legal/illegal examples, exact
nf-tiny/reference assumptions, total and unambiguous correspondence, ledger
owners and later execution obligations. Retain the reviewer identity, source
revision, findings and dispositions; do not label proposed documents accepted
until that review resolves critical ambiguity. FND-02 closure separately needs
applicable final-head documentation/contract qualification and integration under
[project instructions](../../AGENTS.md).

FND-06 scheduled execution remains not run until its tools produce recorded
reference artifacts and results. There is no FND-02 RTL simulation, formal
proof, real-loader run, production Nodal flow, performance measurement or silicon
qualification supplied by these paper walk-throughs.

This increment does not affect generated Verilog.
