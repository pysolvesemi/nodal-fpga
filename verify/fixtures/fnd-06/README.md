# Frozen independent FND-06 witness contract

These are planned acceptance inputs, not passing reference results. The accepted
FND-02 specification/correspondence/ledger and FND-06 readiness record are the
only semantic sources. No candidate generated RTL, production lowering,
allocator, normalizer or observed consumer result supplied an expectation.
Historical `not-run` records remain unchanged.

## Files and interfaces

- `obligations.json`: all 15 inherited IDs, all 17 required leaves, immutable
  input hashes, 17 literal instances, exact formal/structural/simulation/stage
  rosters, explicit planned counts, timing and execution-binding requirements.
- `semantic_cases.json`: accepted A6D3/0812 tables, eight mux vectors, both exact
  register traces, four packed/frame examples, genuine one-hot identity matrix,
  physical walking patterns, independent per-instance words, negative cases
  and the supplemental config-consumer mutation's literal binary observation.
- `mutations.json`: twelve fixed semantic mutations and three separate formal
  anti-vacuity controls. All required failing witness IDs are named. Endpoint
  omission and config-consumer require both structural and behavioral failure.
- `manifest.py`: `load(repository_root=None)`,
  `validate_bundle(bundle, repository_root=None)` and
  `expected_records(bundle, stage)`. The bundle keys are `obligations`,
  `semantic_cases`, `mutations`. Frozen byte and canonical-content identities
  reject same-count substitutions as well as missing or duplicate records.
  This is input validation only, never execution-result qualification.

Run only the manifest checks with:

```
python -m unittest discover -s tests/foundation -p test_reference_manifest.py -v
```

## Hand-checkable supplementary literals

A genuine one-hot INIT has exactly one set address j. Its sixteen expected
outputs form identity-matrix row j: one at address j, zero everywhere else.
The 256 records materialize this definition directly. A6D3 and historical 0812
are separately retained; 0812 has three set bits and is not genuine one-hot.

Physical walking-one/zero records explicitly list all twenty Q values in
least-significant-bit-first order and all twenty complementary QN values.
The 20-bit hex word followed by three zero hex digits is the frame-0 word,
because bits 19:0 occupy frame data bits 31:12. Toggling carry bit17 is confined
to standalone ConfigMem storage tests; matched LUT/tile behavior fixes it zero.

The seventeen distinct per-instance INIT-only words are copied literally from
the reviewed readiness table, including sparse/t22=0A6D3. They are not addresses
or data learned from generated consumers. FF, carry, reset-value and source are
zero for these supplementary setup cases. Full FF/source/reset behavior retains
its separate observations. Column hold initializes every tile and checks each
unselected instance for every selected column (28 records).

The declared known baseline for padding/hold/transparency is 0A6D3. A hold case
inverts only named used data bit while strobe is low; transparency inverts it
while frame0 strobe remains high. Unused-frame cases complement data with only
that padding strobe high; padding-data cases toggle only the named low bit while
frame0 is high. Expectations follow storage isolation and are never comparisons
of uninitialized unknowns. UserCLK remains low throughout configuration setup.

## Denominators and identity

Six positive formal tops have 7 assertions, 1 explicit assumption and 21 covers.
The register uses 13 sampled states / 12 rising-edge transitions, unconstrained
initial DUT and shadow state and one initialization-only EN/SR assumption.
Combinational tops use one sampled state. Controls are outside positive totals.

The structural roster contains 1,035 instance-level objects: 390 pins, 195 fixed
edges, 34 selectable edges, 340 full configuration chains, 68 typed resources
and 8 intertile links. These require complete candidate-set enumeration, not
queries of expected objects alone. Register state is a signal with a unique
sequential Q driver, and the constant is resolved through declaration and actual
zero connection; neither is invented as a child module or missing JSON net.

The simulation roster contains 1,847 observation records: 1,020 instance
LUT/register records; 32 mux, 160 walking-storage, 80 hold, 80 transparent,
76 padding-frame, 48 padding-data and 288 LUT unit records; 17 instance words,
28 column holds, 16 binary link observations and 2 accepted odd-row witnesses.
An observation record may contain several checks; actual check counts are also
required. The 12 semantic rejection cases and 2 post-initialization four-state
controls are separate negative records. Every ID has multiplicity one.

Variant IDs use the full `NF_SINGLE`, `NF_LEFT`, `NF_MID`, `NF_RIGHT` names.
Instance simulator IDs place shape/tile between family and sample, for example
`LOCAL-A6D3/odd/t10/address1` and `FF0-STATE-R1/sparse/t22/step3`.
`label` is the ID with non-alphanumeric characters changed to underscores.
Planned harness paths/tops are semantic locations; execution must bind actual
source declarations and actual lowered/exported identities without losing IDs.

## Execution gate and retention

Independently review these frozen files before generator/simulator/formal runs.
Mutation parent/derived/patch hashes are deliberately null before generated
bytes exist. The mutation's target and exact semantic edit are frozen now;
unique actual source spans and hashes must be bound before its execution.
Never substitute a guessed hash or relabel plans as observations. The mutation
runner permits only its explicitly derived bytes, preserving provenance checks
for everything else. A parser/compile/hash/crash/timeout failure earns no
semantic mutation credit.

Execution receipts must bind each ID to actual source line/span/hash and DUT
object, condition, expected/observed result and artifact identity. Formal IDs
also bind exact lowered cells and SMT functions. Counts alone never qualify.
All source and generated resources remain programmable and non-EMULATION.
This is static/unit frame-memory setup, not runtime-loader qualification.
Production Nodal fabric generation, PPA, timing and silicon are not claimed.

Publish portable authored fixtures, approved source/generated artifacts and
concise verified summaries only. Keep raw path-bearing generation manifests,
logs, traces and host-resolution details local for independent review. Retain
both fresh runs; compare generated RTL/source inventories without rewriting raw
provenance manifests. Any semantic change requires explicit independent review
and a newly frozen contract before affected replay.

## Pre-execution refinement

`compiled_top` and `declaration_label` bind the planned formal tops to
`lut_formal`, `register_formal`, and `switch_SINGLE/LEFT/MID/RIGHT`. Static switch
labels repeat inside their distinct tops; the stable manifest ID remains
variant-qualified. Actual source line/hash and exported SMT bindings still
belong to execution receipts.

The separately counted `supplemental_simulation` roster has 28 primitive
register trace/state/output records and 8 generated-switch fixed-link records.
These use only accepted register traces and fixed-edge semantics and strengthen
primitive-level diagnostics. They never replace or alter any original
instance or 1,847-record simulation denominator. `storage_behavior` additionally
materializes the 71 hold/transparency/padding input/Q/QN literals shared by the
four variants, so a serializer need not calculate golden storage behavior.
