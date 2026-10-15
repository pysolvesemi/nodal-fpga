# Finite Foundation reference checks

`./nf check reference` is an optional, explicit reference profile. It does not
participate in a default Rust build and does not import a concrete device into
reusable engine crates. Its implementation is qualified separately from the
final combined CI environment.

## Inputs and execution

Prepare the exact external tools using `toolchains/reference/README.md`, set
`NF_REFERENCE_ROOT` to that prepared reference cache and `FABULOUS_UPSTREAM` to
the clean pinned FABulous source checkout. Source the normal pinned Rust
environment for the independent standard-library model and generic API tests.
No tool download or dependency resolution occurs inside the hardware runs.

Run `./nf check reference`. For final clean-head qualification, also set
`NF_EXPECT_SHA` to the actual candidate commit. A changed or dirty checkout then
fails before execution. Development runs retain their dirty flag and actual
source hashes; they cannot stand in for clean final-head qualification.

The finite oracle is frozen under `verify/fixtures/fnd-06/`. Its expectations
come from the accepted specification, correspondence and hand-reviewed
literals. The generator and candidate graphs cannot update these expectations.
Changes to the oracle require another independent review before execution.
The explicit FND-06 generation adapter retains the historical FND-02 generator
and its pinned inputs unchanged. It creates the official `.FABulous` project
marker before validated upstream initialization, which the historical scaffold
omitted. Each generation record binds both script hashes and this exact
execution adjustment; it does not bypass the upstream project validator.

The runner uses separate generation, compilation, structural, simulation,
formal, model and semantic mutation stages. Four bounded shapes are generated
twice in fresh output directories. Actual RTL/source-list hashes and complete
structural correspondence must agree across runs, and each semantic suite must
independently cover its exact named roster. Equal aggregate counts do not
substitute for matching identities or expected values.

Every explicit stage input is hashed before and after use. The isolated tool
source snapshot and full mounted runtime closure are bound separately. The
hardware environment receives selected readonly tools, source and stage inputs,
a fresh writable work directory, and no inherited network descriptors. Socket
creation and selected escape mechanisms are denied. This is the reviewed Linux
trusted-tool bounded-corpus profile, not a hostile-code sandbox or a network
namespace. CPU/address-space/file-size limits are hard resource limits;
aggregate process/storage limits are sampled and can overshoot between samples.
Killed processes may have only launcher-scoped resource accounting; the record
states that limitation rather than reporting it as full tool consumption.

## Results and privacy

Detailed captures, original path-bearing generation manifests, runtime
inventories, observations and intermediate files remain in ignored local
`artifacts/fnd06-reference/` run directories. Failure leaves its partial records
for diagnosis and never returns a passing summary. These files are not an
upload list.

Repository acceptance uses a concise verification checklist: tested commit and
tree, commands, exact required/executed/passed counts, independent architecture
review, limitations and actual integration identities. Only actual passing
checks may close roadmap items. Authored fixtures and explicitly reviewed
portable generated RTL deliverables are separate from raw execution logs.
Every fresh shape must byte-match the published portable RTL archive, including
its exact file roster, source list, pinned input identities and generator hashes.
Every freshly materialized mutant must match its published relative-path patch
and portable baseline/derived binding. Missing or changed archive entries fail
the run. These deliverables record reproduction, never supply semantic expected
values or replace actual generation, compilation, simulation or proof.
Historical FND-02 `not-run` records remain historical, unchanged records.

A simulator mismatch counts as a semantic negative only when the expected
baseline passes and the exact frozen mutant fails at its intended witness with
the intended values. A timeout, crash, missing property, compile error, or
resource-limit event cannot earn mutation credit. Formal proofs require actual
nonzero assertion identities; covers require actual reached-property bindings.
The deliberate false assertion, missing-export and overconstraint controls are
separate from positive proof totals.

## Scope

This checks the finite Foundation reference contract. It does not implement or
qualify a production Nodal fabric, configuration loader, place-and-route flow,
PPA result, arbitrary architecture, or manufacturing process. Remote CI and its
fresh toolchain reconstruction remain separate FND-08 acceptance gates.
