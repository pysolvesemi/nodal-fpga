# FND-02 independent contract review

Review date: 2026-10-15. Reviewer: independent FND-02 contract reviewer.
Scope: architecture decisions, hand-calculated expectations, reference-input
viability by source inspection, correspondence, traceability and local contract
controls. This review does not run FABulous generation, RTL simulation, formal
proof, a production Nodal flow, runtime loading or performance benchmarks.

Initial working-tree base: `02409567dbbf8763aa8be4e9f67786f2aeea809c`
(tree `c6cd0dda2defe5977dfb5728e734a4ef683721d2`). Reviewed files were
uncommitted additions/changes over that base. Final qualification and integration
must identify the actual published candidate; the base alone is not their hash.

## Disposition

The architecture decisions and concrete reference semantics are coherent and
accepted for the nf-tiny-foundation/1 contract scope. No critical LUT, register,
mux, frame-bit, boundary shape or source-API mismatch was found. All reported
guard/traceability findings were repaired and independently rechecked. There
are no unresolved blocking review findings. The coordinator owns acceptance-
state promotion, completion evidence and verified integration. Clerical
promotion from proposed to accepted-for-profile, with execution left not-run
and corresponding input hashes refreshed, does not alter this semantic review;
any substantive contract change requires renewed review.

The user's current cadence is local required tests per increment, no pre-merge
or post-merge remote CI unless actual protection requires it, and one full
all-tests CI qualification after Foundation is implemented. This review neither
dispatches CI nor substitutes contract tests for later required execution.

## Reviewed authority and boundary

Read AGENTS.md, roadmap index/progress, the complete FND-02 checklist and the
Foundation applicability rules, architecture, verification, early baseline,
ADRs 0001–0003, foundation/nf-tiny contracts, assumption ledger, specification,
correspondence, reference inventory, all authored FABulous inputs, generation
runner and contract validator/tests. The later-track ownership audit covers
DSL, DB, LIB, RTL, CFG, CAD, TMC, VER, PERF, EMU, PHY, PROD, NAT, ADV, CIR and DFT.
No reverse dependency on a blocked track is introduced.

- ADR 0002 preserves a portable finite hierarchical exchange, independent Rust
  validation and JVM-free saved-package use. Required capabilities, unknown
  semantic fields, duplicates, bounds and incompatible versions fail closed.
  Exact schema/canonicalization implementation remains FND-04/FND-05 work.
- ADR 0003 separates architecture intent, immutable DeviceDB and per-job customer
  state, with build-qualified dense IDs and exact package matching. Timing and
  physical identities cannot be silently omitted. External CAD and the optional
  CIRCT adapter remain outside reusable core.
- Primitive controls, ownership/alias consistency, ordered selections, finite
  templates and overlapping domains have explicit meaning and rejection policy.
  The paper repetition/partition/hole/shared-control examples are proportionate;
  none claims production compression, silicon portability or measured scaling.
- One semantic authority plus a separately authored oracle avoids competing
  production definitions. Profile-specific validation stays in test tooling,
  rather than adding nf-tiny or FABulous conditionals to generic core.

## Concrete independent checks

The pinned source checkout is FABulous commit
`d2fc49dade524a4f78062a3a38b213e9c08d6b04`, tree
`6af48dacbfaf6a77617e11ab00ab4966f77711ba`. The checkout was clean. Independently
computed SHA-256 values matched all 17 upstream files and all 22 initial
reference input entries. A separate standard-library CSV inspection, without
importing the production validator or upstream generator, confirmed:

- Shape instances: one 1x1/1 tile/0 east links; square 2x2/4/2; odd 3x2/6/4;
  sparse 3x3/6/2 with the stated holes. Every CSV cell agrees with the independent
  coordinate/type specification. There is no implicit jump across a hole.
- Every switch matrix has the expected source order and exact fixed rows.
  Local A0 is mux input 0; ALT or west W is input 1. LUT I1–I3, EN, SR and Ci
  are fixed as specified; O drives Y and only the declared east endpoints.
- All four ConfigMem files declare 20 frame rows, 20 used bits in frame 0,
  mask bits 31:12 and ConfigBits range 19:0. Remaining rows have zero used bits.
- LUT A6D3 gives ascending outputs `1100101101100101`. The 0812 pattern has
  set addresses 1, 4 and 11. Distinct I0/I3 values expose a significance swap.
- Register traces agree with rising-edge, enable-gated synchronous reset.
  EN=0/SR=1 holds an opposite-to-reset state, detecting reset-over-enable
  priority. Initial state is not assumed zero. FF selection does not gate
  the register's updates. Carry output is excluded rather than assumed zero.
- The four packed feature/frame examples agree with bit positions 0–19 and
  the 12-bit frame shift. The full-fabric row-data/column-strobe slices agree
  with upstream generation source. Latches are level-sensitive while strobed.

Source inspection covered parse_csv, parse_hdl, parse_switchmatrix,
parse_configmem, gen_switchmatrix, gen_configmem, gen_tile, gen_fabric,
fabric/yosys/port definitions, fabulous_settings, LUT source and models_pack.
The actual instance names, scalar/vector pin handling, BEL-first configuration
allocation, matrix row order and reversed concatenation preserve the declared
correspondence. Sparse frame wiring skips NULL positions; user clocks preserve
logical equality through ideal buffers. There are no north/south user routes.

The runner calls the pinned APIs with matching signatures, materializes source
RTL separately from generated modules, checks the source commit and inputs,
and refuses to overwrite an output directory. The upstream Python 3.12 minimum,
Yosys BEL parser, imported physical-flow dependencies and mutable HOME/XDG
configuration are disclosed. Clean configuration and exact tool/dependency
builds must be pinned at FND-06. Source viability is not successful generation.

## Findings and dispositions

### R1 — Structural false passes: repaired and rechecked

The initial validator accepted a nonexistent output mapping, output direction
changed to input, incorrect INIT logical index, a consistently packed forbidden
carry mode, empty register traces, missing obligation/negative inventories and
proposed subset records through the accepted mode. These were reproduced using
in-memory mutations only; production artifacts were not changed by the reviewer.

The coordinator added explicit pin/config checks, required coverage inventories
and subset acceptance guards. Recheck ran 35 foundation tests successfully.
`python3 tools/check_foundation_contracts.py` passed with 12 assumptions,
4 shapes, 16 LUT addresses, 8 mux cases and 20 config bits.
`--accepted` correctly failed on the still-proposed ASM-0001 at that checkpoint.
This negative result is expected and is not accepted-head qualification.

### R2 — Reference freeze and boundary-map guards: repaired and rechecked

At the initial recheck, `check()` did not load reference.json or verify its
input hashes/state. Changes to CSV/generate.py could therefore evade the
contract gate. Empty shapes could pass, and variant east/west directions and
exact references were not enforced. Requested narrow repairs: validate the
reference inventory's state/profile and complete authored-input hashes; retain
exact required shape IDs; enforce e/output/E[0] and w/input/W[0]. These are
freeze guards, not a demand to implement FND-05's general untrusted schema now.

The new reference checker validates state/profile, safe in-tree input paths,
exact input inventory and hashes. The four-shape and exact variant-pin checks
are present. Corrupt/missing/escaping inputs, proposed reference status, empty
shapes and incorrect variant direction/reference have passing negative controls.

### R3 — Assumption-to-consumer traceability: repaired and rechecked

The specification includes wrong-package rejection but initially omitted
ASM-0008. Required field-alias, endpoint and tile-composition witnesses existed
in the specification but were not connected to pertinent ledger records.
Affected consumers were copied identically across every assumption, omitting
DB/TMC/PHY where the claim requires those consumers to replay after change.
The final ledger/specification now includes ASM-0008 and every FND-06 witness
has a pertinent ledger reference. Affected consumers are claim-specific,
including DB/TMC/PHY and the relevant other tracks. No listed FND-06 obligation
remains absent from the ledger.

## Common-mode risks and retained limitations

- Upstream LUT/register and models_pack are implementation inputs, never an
  independent truth oracle. Hand vectors and the simple reference semantics
  must remain independently maintained when FND-06 executes them.
- The reference generator and HDL-port parser share Python/Yosys infrastructure;
  later comparisons may share simulators/solvers. Pin and disclose those common
  dependencies. Compare observable semantics and independent graph expectations,
  not generated text or tool agreement alone.
- Transparent I/O is authored plumbing. The source pin and review establish its
  simple mapping, not an additional independent hardware implementation.
- Current tests protect selected contract invariants and intended mutations.
  They are not a complete malformed-input schema validator or RTL netlist
  correspondence extractor. The latter is due in FND-06, strict exchange parsing
  in FND-05. Arbitrarily coordinated edits still require independent review.
- `additional_one_hot` currently labels a three-set-bit sparse pattern (0812).
  Its values are unambiguous; FND-06 must include actual one-hot INIT values as
  promised by its exhaustive/symbolic LUT obligation. This naming is nonblocking.
- The row witness establishes asymmetric directed composition. FND-06 still
  owes actual generation of all shapes, complete pin/config/edge coverage,
  nonvacuous state witnesses, independent known vectors, primitive/tile checks
  and the intended mutation detections with solver/simulation scope recorded.
- Binary static setup is not a transport controller, atomic activation, illegal
  load recovery, electrical buffering, timing, P&R, manufacturing test or silicon
  qualification. Those owners and unsupported modes remain explicit.

## Acceptance scope

This report accepts the FND-02.a–d, f and g contract/review deliverables and the
all-track audit portion of e. It cannot close the parent by itself. Record
accepted artifact identities and final local qualification, verify integration
and complete the bounded report before marking the final closure leaves.

Final independent local recheck: 43 foundation tests passed; the direct contract
check passed with 12 assumptions, 22 input hashes, 4 shapes, 16 LUT addresses,
8 mux cases and 20 config bits. All hardware execution states remain not-run.
The complete bootstrap/Rust/Scala candidate checks and actual merge verification
are separate coordinator-owned qualification, not claimed by this report.

This increment does not affect generated Verilog.
The deliverables are contracts, reference inputs and local contract controls;
reference generation remains a required, not-run FND-06 execution.

## Reviewed pre-promotion artifact digests

These SHA-256 values identify the reviewed content before the authorized
clerical acceptance-state promotion. The completion report must additionally
identify the published accepted candidate and refreshed input hashes.

| Path | SHA-256 |
| --- | --- |
| `docs/adr/0002-portable-architecture-exchange.md` | `3448ad6833c6ac2b661b697d95d18b8e4d1d6ba27f336fcefa5913e6b364f674` |
| `docs/adr/0003-device-design-ownership.md` | `36f846270951e5f2b350c05df903290b9055fae7a7806653fea68fca41434a65` |
| `docs/contracts/foundation.md` | `257afcad6133084514c889047ef2c5c69f9276b7f6cf663feac4c072b796c5fe` |
| `docs/contracts/nf-tiny.md` | `829b537e1a60f09439f315237b6f75027dfde4903041a054bb3c71e91d2b8a56` |
| `verify/fixtures/assumptions/ledger.json` | `36d14ab94f8c05429be78043f289bf947b60e905a5c98affb76cb45ba187e9c9` |
| `verify/fixtures/nf-tiny/specification.json` | `6a83819f442aa6b1882e5406d307b1f942d31da85d944728c5ffb49f66158900` |
| `verify/fixtures/nf-tiny/correspondence.json` | `8b62b2261b4241d88f8f3805f2474c6c782342b5dc3267648437c17e3045fd3e` |
| `verify/fixtures/nf-tiny/reference.json` | `cf1d0fa6467bdb552ba050b75d779fdd8f9ef64ed22ebc47b0a0556a4e37cdcd` |
| `tools/check_foundation_contracts.py` | `12db059851177372a4d2d7e1569fad1eff8757d8f0de3873f1f77df68e77f7db` |
| `tests/foundation/test_contracts.py` | `22086ecca89e6928b8520bc31663867286ad4e4310d69a6e786a841b0922c3df` |
