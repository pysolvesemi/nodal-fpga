# ADR 0003 — Architecture, immutable device and per-job design ownership

Status: accepted for the Foundation profile following [independent FND-02
review](../implementation/fnd-02-independent-review.md). These ownership contracts
do not claim an implemented DeviceDB, DesignDB or CAD adapter.

## Decision

Maintain three separate representations, connected by explicit validated
contracts rather than shared mutable objects:

| Representation | Owns | Does not own |
| --- | --- | --- |
| ArchIR | Portable architecture intent: typed resources, modes, hierarchy/templates, routing patterns, logical features, domains and explicit physical intent | Customer cells/routes, runtime state, process-specific tool objects or a compiled file layout |
| DeviceDB | Resolved immutable device build: resource/query tables, legal capabilities, exact package-qualified references and bound configuration/timing/technology manifests | Placement reservations, congestion, current user configuration or mutable customer netlists |
| DesignDB and job overlays | One customer's mapped cells/nets/ports/constants, selected modes, clock/constraint intent, provenance; per-job packing, placement, routing and analysis state | Authority to redefine device resources, physical configuration semantics or the device's capability limits |

The reusable Rust core depends only on public semantic contracts. Frontends,
libraries, concrete devices, technology bindings, adapters and applications
consume those contracts in that direction. Core must not import a concrete
library/device, Scala runtime, nextpnr internals, proprietary PDK or optional
MLIR/CIRCT adapter. External users must be able to add a primitive library or
device without adding device-name conditionals to core.

ArchIR is validated into a resolved semantic device model. Device queries,
fabric RTL and configuration maps are views of that model, with independently
checked correspondence. The model must not be reconstructed from a customer's
routed design. The manufactured fabric retains every declared supported legal
configuration; optimizing it into one demonstration bitstream is forbidden.

## Lifetime and mutation boundaries

A DeviceDB is immutable for one device build and may serve concurrent jobs.
Indexes/caches that are purely functions of that build can be immutable shared
artifacts or internal observationally transparent caches. Their lifetime and
synchronization must not expose mutable placement or routing state in device
queries. No process-global mutable current-device/current-design singleton is
part of the public API.

Each job owns its mutable cells, nets, placement, route selection, resource
reservations, congestion and timing caches. Separate jobs cannot reserve or
modify resources for one another. Derived state records the device build,
design revision, constraints, options and tool/seed/worker identity on which it
depends; stale state is rejected or explicitly recomputed. Timing characterization
belongs to the device package; arrival times, slack and constraint-dependent
analysis belong to the job. Logical user configuration is an output of a
validated job, distinct from the device's immutable configuration feature/map
contract and from hardware's transient register state.

Checkpoint import validates device identity, supported schema/features and
referenced resources before reuse. An old package-local ID is never interpreted
against the current package merely because its numeric range happens to fit.
Backend-neutral mapped/placed/routed checkpoints do not make an unvalidated
external route trustworthy; CAD-04 owns independent route legality checks.

## Identity layers

Use explicit identities for different purposes:

1. Portable semantic resource keys are namespace-qualified, typed and scoped
   through template/instance paths. They identify declared meaning and support
   source correspondence. A key must be unique in its declared scope; a display
   name is not a substitute. Reused template-local keys are qualified by each
   instance, so reuse does not merge independent physical resources.
2. Dense IDs identify a typed resource in one compiled device build. Local
   indexes may be partition-local 32-bit values where checked safe; lengths,
   file offsets and cross-partition addressing must support the declared larger
   ranges with checked conversions. A reference carries or inherits a verified
   device-build context and partition/kind. IDs are not a portable ABI, physical
   configuration addresses, or stable across recompilation promises.
3. Design/job IDs identify customer cells, nets and mutable analysis results
   within their own design revision. They reference device resources through
   the validated device-build context, not by mutating them.
4. Artifact digests bind bytes. Semantic architecture fingerprints bind the
   declared semantics under a versioned canonicalization rule. Device-build
   identity binds the complete compiled contract below. A family name, filename,
   Git branch or marketing device name is none of these identities.

A permitted representation transformation supplies an explicit correspondence
between old/new resource meanings. A template may be stored once while two
instances have distinct keys and configuration ownership. Changing dense ID
assignment or partition boundaries may preserve semantic meaning while changing
package bytes and build identity. Renaming a semantic key requires a reviewed
map; it is different from changing a nonsemantic display label.

## Device package and incompatibility

A device package manifest binds exact revisions/digests of architecture and
resource libraries, semantic profile, compiler/backend and relevant options,
all schema/feature versions, physical implementation, technology/macro bindings,
configuration map and transport/activation contract, timing corner datasets,
and external package/pin map. Referenced artifacts are content-checked before
use. A hash's domain/version and the manifest's self-identity exclusion rule
must be specified by its owning serialization contract to avoid ambiguous or
self-referential hashes.

A software-only profile explicitly declares physical technology, characterization
or package views unbound/absent when they are unavailable. A fabricated revision
or zero-delay placeholder is not allowed. Inspection of such a package is
possible only within its supported scope; physical implementation, timing
closure or programming requires the corresponding qualified bindings. Restricted
PDK/model bytes remain outside redistributable packages; a digest/reference is
not a grant of access or license.

The initial compatibility rule is exact target-build matching. Designs,
configuration maps and bitstreams for a different build are rejected before
routing reuse or programming/activation as applicable. Semantic equivalence
alone is not bitstream compatibility. A later compatibility or migration tool
must name the exact source/target builds, verify the required mappings and
produce a newly bound artifact. No implicit compatibility by family label,
matching resource counts or similar RTL is permitted.

| Change | Required treatment |
| --- | --- |
| Display label/comment only | Semantic meaning may remain equal; raw-byte digest changes when bytes change; follow the declared canonicalization scope |
| Reordered keyed declarations | May preserve semantics; confirm the ordering rule; pinned rebuild determinism still applies |
| Reordered mux inputs or LUT bits | Behavioral change unless selection/truth-table correspondence is translated and independently checked |
| Partition or dense-ID reassignment | Rebind resource references under the new build; old dense IDs cannot be reused directly |
| Configuration address/bit order, reserved encoding or loader activation | New configuration/build identity; reject old bitstreams absent explicit qualified conversion |
| Primitive mode/reset semantics, pin direction or shared-control constraint | New semantic/library/profile identity; revalidate affected consumers and evidence |
| Physical cell/macro/PDK implementation or package pin map | New bound identity and affected physical/electrical/timing/test qualification |
| Timing dataset/corner revision | New bound package identity and invalidated timing caches; unchanged configuration is not automatically a cross-build programming waiver |
| Tool/backend/options that affect artifacts | New reproducible build identity and affected qualification; retain configuration-preservation obligations |

DB-05/06 and CFG own implementation of binding/publication/bitstream checks;
PROD-04 owns long-lived supported compatibility. FND-02 declares the fail-closed
boundary, without claiming those mechanisms already exist.

## Overlapping domains and technology boundary

Containment hierarchy describes devices/dies/regions/instances. Clock, power,
configuration, placement and routing domains are typed memberships and
constraints that may overlap and cross that hierarchy. Do not force them into
one tree or equate membership sets. Membership alone does not permit an unsafe
crossing, partial update or power-state transition; each operation requires
its own supported profile and interface constraints.

Physical clock resources specify eligible sources, connectivity, capacity and
reach. Customer clock domains and timing relationships are DesignDB constraints,
not copies of the physical resource tree. Configuration-clock transport,
user-clock operation and state/reset/activation contracts remain distinct.
The first single-user-clock profile does not establish multiclock support.

Architecture intent names required capabilities, logical interfaces and units.
A technology binding separately identifies realization, supplies, legal modes,
macro/cell revisions, simulation/timing/physical views and their coverage/access
constraints. Missing views or unsupported electrical combinations fail at the
operation that needs them. A process port needs requalification; a reusable
schema does not make it automatic. Protocol resources such as NoC/SERDES/die
links require suitable future contracts, not just arbitrary PIP edges.

## External-CAD-first ownership

Qualified external engines provide initial customer HDL synthesis and
pack/place/route. Yosys and nextpnr integrations are explicit adapters with
pinned capabilities, translations and provenance. nextpnr needs an actual
architecture integration; generic JSON export alone does not establish it.
CAD-03 chooses a suitable generic/Himbächel/full architecture route using its
own evidence, keeping any C++/Python glue out of core.

`nodal-hdl` owns its existing high-level HDL/MLIR compilation; it hands off a
versioned mapped-design contract or the explicitly qualified generated-Verilog
path. `nodal-eda` owns projects, UI and product orchestration. This repository
owns headless device/fabric/configuration tooling and adapters. Native generic
synthesis is not hidden inside a foundation model or the optional NAT track.
NAT-01 requires measured need before a native CAD replacement; external engines
may remain the qualified production choice.

The default fabric emitter is a small structured Rust component under ADR 0001.
CIR-01 reviews alternatives before expansion into a general compiler; CIR-02/03
require their separate proceed/adopt gates. An optional CIRCT process cannot
replace ArchIR/DeviceDB/configuration authority or become a default dependency.
The ordinary Rust compiler toolchain is allowed; default build, saved-package
runtime and Scala-authoring isolation are distinct profiles with stage-specific
evidence. No executable RTL-emission/runtime capability is asserted here.

## Rationale and acceptance boundary

Separating immutable device data from per-job mutations makes concurrent readers,
checkpoint invalidation and independent legality checking tractable without
mandating a particular storage layout or distributed runtime. Template sharing
reduces representational duplication; it does not prove memory or runtime
performance. A compact tiny fixture still needs an independently expanded
oracle to expose shared mistakes.

See [the foundation contracts](../contracts/foundation.md) for primitive/sharing
semantics, bounded examples, actionable failures and the complete later-track
boundary audit. FND-04/FND-05 establish minimal executable types/interchange;
DB/CAD implement their production consumers after FND-08. Contract review,
reference simulation, formal proof, actual loader tests and silicon qualification
are separate evidence states with separate owners.

This increment does not affect generated Verilog.
