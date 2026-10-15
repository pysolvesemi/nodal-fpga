# FND-06 independent reference-harness readiness

Prepared 2026-10-15. Derived from the final technical readiness proposal (SHA-256 `ea6e328cc184f91b45df2ed9426fc8d28f1a5bae7052ee66a98962aca9153771`), preserving its independent P1–P3 clarification decisions and technical obligations. The prior independent review identity is SHA-256 `1f1864412aa5cea266ab9205e34fe6280aa743513ea94edd17b307d3f9955314`; the original pre-revision proposal identity is `fcba3eebd527fb09586cbb3e1d483c73613ed48ee16bb03464f3c8c84094c074`. This adaptation changes publication form and current-task CI cadence only. It is not implementation, generation, simulation, formal evidence, independent acceptance, or permission to begin. No repository edits, builds, installs, reference runs, publication or CI were performed for this adaptation.

## Decision and start gate

FND-05 is accepted on refreshed integration target `f9fd973bf0b065276b34c22742560ad20c4c4ae9`, tree `be27982b0d28c8fdc7942031d023bc55edbf2e95`. Its implementation passed exact-source local checks and independent architecture/runtime review; its separate concise evidence closure passed exact documentation checks and source anchoring and merged through PR #10. All required predecessor nodes are checked. FND-06's complete existing checklist remains coherent without weakening or renumbering; preserve every leaf and the final `.e` closure group.

Current-target audit on 2026-10-15 verified clean local/fetched `dev`, no open competing dev PR, and disabled branch protection with no required contexts. The final FND-05 exchange interfaces, summary validator and acceptance limits were inspected. Accepted FND-02 specification, correspondence, reference and assumption-ledger hashes remain identical to the table below. Independent review of this exact readiness record and its own durable branch/PR checkpoint must precede implementation; no reference generation or semantic qualification has occurred yet.

Fresh capacity checks found Icarus 12.0, Yosys 0.52, Z3 4.13.3 and Python 3.12.14 available. The canonical FABulous-FPGA 2.0.0 import smoke passed against the exact clean pinned upstream checkout. An initial metadata lookup used the wrong distribution name and failed; it is not passing evidence. A read-only user/PID/IPC/UTS namespace probe passed. These establish availability only: the actual isolated reference harness, semantic checks and final CI provisioning remain required FND-06 work. No network namespace, full reference isolation or hardware result is inferred from these probes.

The earlier technical inspection was on FND-05 readiness commit `4895bcc96f527049ad1b22a206987959b11b9878`, tree `08356c48d61fb18d6a8a35c413777e5df8a9c417`; its reviewed technical decisions were rechecked against the accepted predecessor, not relabeled as execution. Reuse the accepted FND-02 contracts and add stage-specific executable evidence on the new FND-06 branch only.

Read the root AGENTS, roadmap/index/progress and full FND-06 checklist; architecture, verification/early baseline, ADRs 0001–0003, foundation/nf-tiny contracts; accepted FND-02 review/completion and corpus; existing metadata validators/Rust model tests; exact generator; source RTL and selected upstream generator/settings sources; cached manifests/smoke source; preparation, isolation-capacity and attribution findings. Runtime-capacity probes are not saved-runtime or reference acceptance.

## Evidence publication and current-task CI disposition

Use the existing version-2 `evidence_mode: summary` contract for new completion records. Publish a concise hashed, source-bound verification checklist/report with exact tested commit/tree, actual repository-relative commands or named environment wrappers, complete observed results and meaningful counts, assumptions, bounds, limitations, tool/profile identities, independent review and real integration identities. Preserve separate generation, compilation, model, structural, simulation, assertion, cover and mutation observations. Map every checked stable leaf ID to its actual observations. Historical v1 receipts and historical FND-02 `not-run` records are unchanged.

All required tests still execute on clean identified source. An implementation-independent reviewer inspects actual local observations, required artifacts and source state before accepting substantive architecture, independence and quality findings. Local logs, waveforms, tool output, detailed process/resource records and raw intermediate evidence remain available for that inspection; they are not uploaded or represented as publicly accessible. Throughout the technical sections below, retention/archive of raw execution evidence means this local inspection record, not a public raw-log bundle. Actual required portable source fixtures, specifications, generated RTL and other deliverables remain hashed artifacts; a prose report cannot replace them. Preserve exact property/witness rosters and semantic checks even when the published checklist is concise.

The latest user direction governs this task: required local qualification and independent architecture review for each increment; no incremental remote CI unless actual branch protection requires it; full combined remote CI after all Foundation implementation. Record the explicit deferral and actual protection findings without giving `not-run` test credit. Preserve all required final combined lanes and verified merges. Neither this proposal nor summary mode changes historical CI records. Do not label a local-only integration as remotely qualified. FND-08 remains the global downstream gate until the exact combined source has passed full remote qualification and accepted evidence closure.

Publish only the reviewed summary and required portable deliverable roster after byte/provenance checks. Exclude private workspace paths, host fingerprints, raw logs, environment dumps, tool roots/caches, wheelhouses and dependency binaries. Named public tool versions, required ABI/platform constraints, approved source/build identities and portable commands remain. Review raw generated manifests for private path fields; retain originals locally and publish a separately identified portable source/output inventory without claiming that its bytes are the original raw manifest. Do not silently sanitize or rewrite hashed originals. CI emits only bounded safe summaries and uploads only validated selected deliverables; failures never authorize a raw-log fallback.

## All 17 leaf obligations and disposition

Every listed leaf is **required for FND-06**; predecessor acceptance is established, while implementation/execution awaits the durable readiness checkpoint and independent review. Existing FND-02 review is reusable input, never substitute execution.

| Leaf | Concrete acceptance deliverable |
|---|---|
| a.1 | Retain literal A6D3/0812 tables, all eight mux vectors and four packed/frame configuration examples; independently review any added witness. Never regenerate expectations from candidate code. |
| a.2 | Retain independently enumerated four-shape graphs; execute total pin/resource/config correspondence, legal/illegal configuration and selected-link checks against actual generated resources. |
| b.1 | Small independent Rust property suite, Icarus simulation and Yosys/Z3 formal/cover wrappers; exact executable/dependency identities, commands and useful tool failure diagnostics. |
| b.2 | Execute exact accepted FABulous runner for one/square/odd/sparse; retain actual switch/configmem/tile/fabric RTL and source RTL separately; retain raw generation logs/manifests locally, publish safe source-bound summaries and portable artifact inventories. |
| b.3 | Execute generated modules and all four fabrics against the independent vectors/graph, including register modes, config bindings and row behavior. |
| c.1 | Each execution receipt references profile, specification, correspondence and historical ledger hashes plus applicable ASM IDs; explicit binary/state/clock/config assumptions. |
| c.2 | Report unsupported modes and bounded result scope; label frame-memory/static-unit setup. Actual runtime-loader qualification stays RTL-04. |
| d.1 | Compile and semantically detect wrong mux index, swapped LUT bit/significance and bad config address. Include accepted FND-02 reset-priority, endpoint and field-alias controls too. |
| d.2 | Wrong/omitted/duplicated pin correspondence must fail independently before trace comparison; hash mismatch alone is not semantic detection credit. |
| d.3 | Useful positive covers, intentionally unreachable cover under overconstraint, and a false assertion control; zero assertions, crashes and timeouts never pass. |
| f.1 | Separate receipts for generation, compilation, Rust model properties, compiled RTL simulation, formal assertions, covers and each mutation. |
| f.2 | Independent reviewer examines literal expectations, all obligation IDs, assumptions, extraction/checking paths and common-mode risks; missing required execution/mismatch blocks closure. |
| g.1 | Keep a small fixture harness; share orchestration/plumbing only. No production lowering/allocator/normalizer as oracle; no fabric specialized to one bitstream. |
| g.2 | All four bounded shapes, repeat pinned runs, fixed seed where used, graph/RTL reproducibility and actual time/RSS/bytes/coverage observations. |
| e.1 | Content-addressed executable corpus, hand-authored specs, exact reference inputs, generated outputs, portable manifests/mutations and immutable binding chain; raw logs/traces retained locally for independent inspection. |
| e.2 | Explicit combinational symbolic, bounded sequential, cover and simulation scopes; applicable final-head qualification, independent review and verified integration. Coordinator applies the latest user-approved CI cadence, not assumptions inferred from old reports. |
| e.3 | Close only after all required descendants and accepted FND-05, demonstrated actual reference input/output and precise absence of production Nodal fabric generation. |

No required FND-06 execution is optional or genuinely N/A. Production RTL/DB/CFG/CAD, real runtime loaders, full application-flow comparison, physical/PPA/timing, large-scale PERF and general formal infrastructure belong to later named owners. Unsupported features remain explicit exclusions/rejections, not disappearing obligations.

## Reusable versus missing

Reusable now:
- Accepted `verify/fixtures/nf-tiny/{specification,correspondence,reference}.json`, immutable assumption ledger, authored four FABulous CSV shapes, four boundary tile/matrix/ConfigMem definitions, transparent I/O and exact `fabulous/generate.py`.
- `tools/check_foundation_contracts.py` and `tests/foundation/test_contracts.py`: historical metadata, arithmetic, totality and negative controls. They intentionally require historical `not-run`; do not relax these guards or promote those snapshots to execution results.
- Generic FND-04 types/validation and independent tests cover three-way reserved selections, alias inconsistency/overlap, package-qualified identities and compact hierarchy. Replay applicable tests, and bind any reused evidence at the current source. Do not copy their implementation into a second production model or call production helpers to make expected graph/semantics.
- FND-01 source/command/profile controls and FND-03 evidence format/roadmap validation. Inspect final FND-05 interfaces only after acceptance; no new exchange format is needed for the reference harness.
- Exact isolated reference tool cache, 80-wheel identity inventory, qualified tools-only smoke/false control and clean upstream checkout. Cache contents are untracked preparation, not a durable/reproducible CI setup by themselves.

Missing: executable independent property/model fixture; generated-RTL compilation/simulation drivers; actual compiled-structure correspondence check; minimal formal/cover wrappers; semantics-targeted mutant runner; separate execution/coverage receipts and controls against forged/missing/zero-count results; deterministic repeats/resource measurements; durable tool provisioning and independently qualified final-CI reference environment. No actual reference corpus has run in this preparation.

Minimal proposed layout: `verify/fixtures/fnd-06/` containing one standalone Rust test source, literal supplementary witness data, a few SV testbench/formal files, one small Python orchestration/checker module and one executable runner. Add narrowly scoped receipt tests under `tests/foundation/` and one reference-only check entrypoint. Avoid a new production crate, broad adapter framework, generalized HDL parser or formal registry service. The Rust fixture can compile with pinned `rustc --test` and the standard library; no property-testing dependency is required for bounded exhaustive/seeded properties.

## Immutable source and assumption bindings

Preserve these accepted bytes and bind new receipts to them:

| Input | SHA-256 |
|---|---|
| specification.json | 0e58761faed7d2d3ea6154ed605262a9fd4a8d6a13ca7de33d06f70a7a88ef32 |
| correspondence.json | 9aff8b60474fa6b04b07691ebe63421c8ae89df31f90f8d5f55189376fc294fe |
| reference.json | 649716da9d708e509ab2437cf9b4976da5468ed471fe1ef822bd0cf9fe4e4738 |
| assumptions/ledger.json | d99d066bb836de9600ae4cecf24ad0cd91dce43c71946419329196f86dccb7f8 |
| fabulous/generate.py | 158197e2fcd82ea8fbdcf11115a26e425113e2a91d5fc73574d1006443d3e0cd |

FABulous v2.0.0 commit `d2fc49dade524a4f78062a3a38b213e9c08d6b04`, tree `6af48dacbfaf6a77617e11ab00ab4966f77711ba`; the prepared upstream checkout was clean at the historical inspection. `reference.json` pins 17 upstream files and all authored inputs. The runner checks the commit, cleanliness and hashes and refuses an existing output directory. Retain its actual source/generated distinction and never convert the source LUT into a claimed generated primitive.

ASM-0001: LUT significance. ASM-0002: register priority/edge/state. ASM-0003: ordered mux/domain. ASM-0004: field ownership/no defaults. ASM-0005: static observation and initialization. ASM-0006: binary domain/four-state rejection. ASM-0007: user-clock separation. ASM-0009: graph/hierarchy. ASM-0010: total correspondence. Bind ASM-0008 to package mismatch checks and source/package identity context without claiming FND-07 integrity work; ASM-0011/0012 remain predecessor/later-owner constraints and are not new hardware claims. Include all applicable stable IDs and exact ledger hash in each stage receipt, not just a profile label.

New evidence records carry their actual execution state/bounds while historical accepted FND-02 `not-run` fields remain untouched. Any substantive changed expectation, map, source pin or assumption requires independent review, appropriate new revision and affected replay. Mutation copies are explicitly derived artifacts with parent hash plus exact patch/hash, never replacements for historical inputs.

## Strict separation of four evidence paths

1. **Reference generation:** accepted FABulous input plus pinned upstream produces candidate source/generated artifacts. Success proves generation only.
2. **Hand oracle:** accepted literal outputs, graph/coordinate lists, ordered pins and twenty binding records are immutable input. Supplementary literals require independent review; output from path 1 cannot populate them.
3. **Independent model semantics:** tiny Rust functions implementing declared truth selection, state transition, selection legality and graph reachability are tested against path 2 and bounded exhaustive properties. Passing model tests do not show compiled RTL behavior.
4. **Compiled RTL:** Icarus executes the actual archived source/generated modules; Yosys/Z3 checks actual compiled reference modules under explicit assumptions. Their observations are compared to paths 2/3, with stage-specific counts and controls. Yosys's BEL-parser/formal/structural use is a shared-tool common-mode risk; independent Icarus execution and literal witnesses remain required.

Python may serialize already-declared literal vectors into SV or parse returned observations. It must not compute golden truth values from FABulous, production lowering, configuration allocation, topology normalization or candidate-generated connectivity. A source extractor reports candidate wiring; a separate expected enumerator reads only accepted oracle data. No normalization may exchange ordered mux inputs, erase an edge direction or guess a new correspondence to make a comparison pass.

## Exact topology and observable configuration plan

| Shape | Dimensions / tiles / east links | Required distinguishing observations |
|---|---|---|
| one | 1x1 / 1 / 0 | NF_SINGLE, all boundaries; local versus ALT selection. |
| square | 2x2 / 4 / 2 | Two independent row chains; distinct row data and per-column strobes. |
| odd | 3x2 / 6 / 4 | NF_LEFT/MID/RIGHT, three-stage AAAA/5555/AAAA literal row witness and independent second row. |
| sparse | 3x3 / 6 / 2 | Holes (2,0),(0,1),(1,2); chains (0,0)->(1,0), (1,1)->(2,1); isolated (0,2),(2,2). No gap bypass. |

Total: 17 matched tile instances and 8 declared intertile links across four cases. Check complete directed fixed and selectable edge sets, not only these totals. Each pin gets a unique primary mapping and correct direction; only declared transparent aliases/exclusions are allowed. No north/south user routing is claimed. Clock/frame buffers are ideal digital plumbing; no timing/electrical equivalence.

### Typed source-to-compiled extraction contract (P1)

Perform a bounded hierarchical structural export with pinned Yosys: `read_verilog` on the archived source roster, `hierarchy -check -top eFPGA`, `proc` only as needed to expose state drivers, then `write_json`. Retain a pre-process hierarchy/RTLIL view plus the post-process JSON, exact arguments/defines and all module/parameter metadata. These are planned commands, not tested API claims. No `flatten`, `clean -purge`, `synth` or broad `prep` in the structural lane. Formal compilation is a different lane and may use its reviewed `prep` flow. If an essential observable is absent, inspect/minimize the export rather than removing its obligation.

Type every accepted correspondence target explicitly:
- **Module resources:** resolve LUT, switch mux and ConfigMem cells through the exact instance path and each cell's actual exported module type, including parameter-derived module keys. Do not assume elaborated module keys equal source names. Check directions, widths, declared vector offsets/index directions and ordered bit connections at each boundary.
- **Register state:** `lut.register` denotes `Inst_L_LUT4c_frame_config_dffesr.LUT_flop`, a one-bit source `reg`/exported state net. Resolve that signal's bit and its unique sequential Q driver after the minimal lowering; record cell type, Q bit, user-clock edge and data/feedback controls. Never require a child cell named LUT_flop. Retain the simulator's hierarchical observation of that same state signal; FF=0 internal-state continuity depends on it.
- **Constant endpoint:** the code writer emits GND0 as `parameter GND0 = 1'b0`, not a guaranteed netname. Bind the pinned source declaration, effective parameter/default metadata where available, and the actual elaborated zero-valued connection reaching switch L_Ci and LUT Ci. Reject constant one, X/Z, an undeclared override, an unrelated driver or failure to resolve the connection. An absent JSON net named GND0 is not itself a missing pin. Do not change the historical map or invent a signal to accommodate its representation.
- **Pins/aliases:** Yosys can merge transparent assignments into shared net bits. Establish driver/sink roles at the correct module boundary; an undirected connected component is not a directed edge. Keep ordered mux terminals; alias names must not form a spurious clique. Resolve only the declared transparent nf_tiny_io, my_buf and clk_buf paths; LUT, mux, latch and register remain semantic boundaries.

Independently enumerate the entire candidate endpoint, driver, sink and edge inventory first, including all ports of every present instance and every mapped configuration consumer. Then compare exact sets to the independently enumerated oracle. Looking up only expected edges is insufficient: reject extra edges/sinks/drivers, wrong-use MID/RIGHT ALT, unknown ports/cells and undeclared fanout. Keep user routing, ideal clock transport and configuration transport as separate typed relations. This is a narrow checker of the pinned tiny resource vocabulary, not a general HDL parser or normalizer. Source anchors are `code_generator_Verilog.py:addConstant`, `gen_switchmatrix.py`, the LUT state declaration/block, and accepted correspondence/totality records. Actual JSON behavior remains to be verified after GO.

The 20-bit word is INIT[15:0], FF[16], carry-select[17]=0, reset-value[18], source[19]. Frame 0 data bits 31:12 map bits 19:0; other frames/data bits have no storage. Fabric row slice is `[32*y+31:32*y]`, column strobe slice `[20*x+19:20*x]`. With UserCLK low, set every row's data, assert only the chosen column's frame-0 strobe, deassert, then observe. Explicitly configure every present tile. Registered observations follow an EN=SR=1 rising edge; no zero initial state is assumed.

Exercise each of the four generated ConfigMem types with walking-one and walking-zero physical data patterns (40 patterns/type), verify all 20 bits and complements, preserve stored values while strobe is low, verify level-sensitive update while selected strobe is high, and verify padding frames 1–19 plus data bits 0–11 leave storage unchanged. Bit 17 can be toggled in this isolated physical-storage test; full matched LUT/tile behavior always constrains it to zero. That distinction avoids falsely claiming carry-mode support. Per-instance distinct legal words and nonselected-column checks prevent cross-row/column aliases. Logical attempts to address padding are rejected by the semantic input contract; hardware padding has no error port and must not be credited with that rejection.

### End-to-end physical configuration correspondence (P2)

Standalone ConfigMem output tests do not discharge config-to-consumer correctness. For each of the **340 instance bindings** (17 instances × 20 bits), retain one typed structural witness with the entire path:

`fabric FrameData[32*y+12+j] -> reviewed row/buffer chain -> ConfigMem FrameData[12+j] -> Inst_frame0_bit{12+j}.D`, with `fabric FrameStrobe[20*x] -> reviewed column/buffer chain -> ConfigMem FrameStrobe[0] -> latch.E`; latch.Q goes to ConfigMem.ConfigBits[j] -> tile.ConfigBits[j], and latch.QN to the corresponding complementary vector. For j=0..18 follow tile bit j to LUT.ConfigBits[j]; for j=19 follow tile bit 19 to switch.ConfigBits[0] and the actual `Inst_{type}_switch_matrix.inst_cus_mux21_L_I0.S` endpoint. Follow the complement to every declared complementary consumer; do not invent a second writable feature or require a complement pin that the 2:1 primitive does not have.

Verify source frame 0, physical data bit, enable polarity/column, Q/QN identity and every downstream ordered slice. Reject swaps, omissions, extra aliases, wrong driver/consumer and nondeclared parameterization. Check the actual latch cell type and pinned non-EMULATION model; `config_latch` is a primitive boundary, not a transparent wire. Declare all Verilog defines explicitly: **EMULATION must be absent** in storage, tile, fabric simulation and structural export. Its static Emulate_Bitstream branch cannot supply storage/programming evidence. No generated resource is specialized to one demonstration word.

The fabric's data/strobe/clock transport may legitimately cross a sparse hole through the source-defined transparent chains; the no-gap-bypass rule applies only to user east-routing edges. Match each present instance to its global row slice and column strobe even where transport skips NULL cells. Retain distinct per-instance legal words, nonselected-column preservation and separate clock-state observations; a ConfigMem template pass cannot stand in for these instance chains.

Add supplemental `FND06-MUT-CONFIG-CONSUMER`: in a labelled NF_SINGLE tile copy connect switch ConfigBits[0] to tile.ConfigBits[16] instead of bit 19, retaining valid RTL and unchanged oracle. Require the compiled physical checker to fail at that specific sink with `config-consumer-mismatch`. Also simulate INIT=AAAA, FF=0, source=1, A0=0, ALT=1 after explicit legal setup: expected y=1, mutant y=0. This directly validates the compiled consumer-extraction path; the inherited metadata FIELD-ALIAS rejection keeps its separate credit. Sources: `gen_configmem.py:205–293`, `gen_tile.py:394–484,575–591`, `gen_fabric.py:227–239,420–572` at the pinned commit. No production allocator or real loader is added.

## Minimal Rust properties and RTL simulation

Rust scope:
- Independently authored `lut(init, inputs)` and bit-array/table oracle: all 65,536 INIT values × 16 addresses = 1,048,576 comparisons. Construct the expected table independently of the candidate address helper; use explicit ordered input-bit cases and literal A6D3/0812 checks to catch shared significance errors. This is **model arithmetic coverage**, separately complemented by symbolic RTL proof.
- All eight 2:1 cases; separate generic three-input ordered mux permits 0/1/2 and rejects 3. Do not reinterpret the reference's power-of-two mux as supporting invalid-code hardware diagnostics.
- Enumerate all two-state q, EN, SR, d, reset-value combinations and edge categories; replay both exact register traces and test output mode independently. Both reset values and EN=0/SR=1 with q opposite reset must appear.
- Validate four literal config words/frame words, all twenty bindings, every specified illegal case (carry, width, selection, unknown feature, missing feature, overlap, X, wrong package, padding address), plus inconsistent declared alias requests. Use typed errors with intended categories, not any failure/panic.
- Independently enumerate the tiny graph and compare exact keys/directions/edge sets. Optional fixed-seed supplementary cases use a documented PRNG and seed, for example 0xF0060001 with 4,096 samples, never in place of exhaustive required cases.
- Where checking production generic legality, call accepted FND-04/FND-05 APIs only as the implementation under test and compare to independent expected categories; do not add nf-tiny special cases to core.

Icarus scope:
- Compile actual `sources.f` for every shape, preserving stdout/stderr, invocation, return status and compiler binary hash. Compile success is its own receipt.
- Source LUT/register unit: literal A6D3 and 0812 at all 16 addresses (32 LUT observations), plus each genuine one-hot INIT=1<<j for j=0..15 at all 16 addresses (256 independently reviewed identity-matrix observations; total 288), both FF/reset modes, both exact register traces, rising/no-edge/falling-edge holds, and hierarchical observation of the declared register resource while FF=0 to show state still updates. Unknown pre-init q is permitted; after initialization any X/Z observation fails explicitly.
- Generated switch modules for all four tile variants: all eight selected-input cases, each fixed data/control link, Ci=0, local/ALT/west source distinctions. Unused ALT in MID/RIGHT must not influence outputs.
- Generated ConfigMem checks above, followed by generated tiles and complete four-shape fabrics. Use literal packed examples, source selections, both FF/reset modes and propagation witnesses. Each of the 8 intertile links must transport distinguishing 0 and 1 observations with alternative/local sources held differently; never infer edge coverage from module instantiation alone.
- Separate negative X/Z stimulus validation and post-init observed-output checks, with explicit failing signal/time. A two-state SMT pass cannot fulfill four-state rejection.
- Report exact performed sample/transition counts; do not call these simulation samples all-config or all-fabric proofs. No nextpnr, customer synthesis or runtime bitstream controller is needed.

## Minimal formal/cover recipe and anti-vacuity gate

Use source LUT/models_pack and actual generated switch modules as DUTs. Independent assertion expressions implement the reviewed contract, not the same mux-tree implementation. Start with three small harness families; no full-fabric symbolic proof or general framework is required:

| Top | Symbolic scope | Planned expected cells after lowering | Execution scope |
|---|---|---|---|
| LUT comb | All 16 INIT bits and four inputs; FF=0, carry=0, Ci=0 | 1 assert, 0 assume, 4 cover | One-step combinational symbolic check; two discriminating A6D3 covers and two genuine one-hot covers. |
| Each generated switch variant | Binary source select and both distinct sources; compare L_I0 to ordered mux meaning | 1 assert, 0 assume, 2 cover | One-step check; cover both selects with differing source values. Fixed links also checked structurally/simulation. |
| Register | Arbitrary stable INIT, reset value and FF mode; arbitrary binary EN/SR/data per user edge; unconstrained DUT initial q | 2 asserts, 1 explicit initialization assume, 9 cover | 13 sampled states (steps 0..12), representing 12 user-edge transitions; separate BMC and cover runs. Compare registered output only after one required EN=SR=1 edge; combinational output always agrees. |

Register timing convention: sampled state k is immediately before user rising edge k; q_k contains all prior edge effects, combinational d_k comes from current inputs, and edge k updates q_(k+1). Yosys/SMT single-clock transitions must implement this exact convention. Both DUT and independent shadow use those same samples. Harness initialized_0=0 is the only initialized bookkeeping; DUT q_0 and shadow q_0 are unconstrained. The sole assumption is `!initialized_k -> (EN_k && SR_k)`, so it constrains only step 0. At the first transition, q and shadow become reset_value and initialized becomes 1. No future EN/SR/input choices are constrained; INIT/reset-value/FF are symbolic stable constants, carry=0 and Ci=0 are explicit domain restrictions. Actual DUT initial q is never equated to the shadow or a known value.

Assert registered-output agreement at every initialized sample with FF=1; assert combinational-output agreement for FF=0 even before initialization. Every register cover below is initialized-gated and includes the appropriate actual DUT output relation. Transition covers also require a previously initialized sample and inspect the previous controls plus current observed result. No-edge/falling-edge and FF=0 internal q continuity remain Icarus obligations. Archive source labels and expression bindings, not merely counts. Expected counts are proposed pre-execution contracts; review legitimate wrapper changes rather than accepting whatever count the tool happens to emit.

Mandatory Yosys 0.52 export guard, adapted to the exact top/counts:

`read_verilog -formal ...; prep -top TOP; chformal -lower; select -assert-count N t:$assert; select -assert-count A t:$assume; select -assert-count C t:$cover; select -assert-none t:$check; write_smt2 -wires OUT`

N is predeclared and nonzero for proof harnesses. Independently check exported `; yosys-smt2-assert`, assume and cover counts against the manifest. Archive post-lowering cell inventory, SMT2 hash, assumption list, exact resolved solver identity/hash/options (absolute resolution retained locally; public command uses the named qualified environment), bound and result. Run `yosys-smtbmc -s z3 -t 1` for combinational checks; `-t 13` for the 13-state/12-transition register BMC; distinct `-c` runs for covers, with witness VCD/testbench or equivalent traces retained. Freeze appropriate per-stage timeouts; timeout/unknown is inconclusive, not pass.

The tools-only finding is material: unlowered `$check` was silently dropped by SMT export and a false assertion appeared green. Existing rejected diagnostic logs earn zero proof credit. Each reference suite must rerun an always-false symbolic assertion control with exactly one assertion and require normal solver execution, exit 1, FAILED and a step-0 counterexample. A zero-assert export must fail before SMT-BMC even if it would return PASSED.

Vacuity control: on an isolated generated-switch wrapper derivative add the explicit assumption `select==0` while retaining both required select covers. Baseline reaches both; derivative must report select=1 unreachable within the complete one-step combinational domain. Its proof may still pass, but the suite rejects it as `cover-unreachable/overconstrained`. Preserve exact changed assumption and witness/result. Optionally add contradictory-assumption `cover(1)` control, but it is not needed to grow this into a general formal framework. The legal baseline's useful covers must succeed. A failed register cover proves only non-reachability within the stated 13-state bound, without an independent completeness argument. No bounded register result is an unbounded proof; do not count an attempted induction as proof unless separately completed and recorded.

### Literal property and witness roster (P3)

This roster is a proposed independent contract, not generated execution evidence. Before running anything, materialize it as a reviewed fixture manifest with one record per exact ID: owning inherited obligation, oracle JSON pointer or supplementary literal, intended harness file/declaration label, actual source line/hash after implementation, DUT target, condition, expected category and multiplicity. Missing/duplicate/substituted IDs fail even if aggregate counts agree. Proposed declaration locations below are not claims that these source files already exist. The eventual exporter must bind each label to its lowered $assert/$assume/$cover and exported SMT function, with no lost or unexpected properties.

**Formal roster:** source locations are planned `formal/lut.sv:<ID>`, `formal/switch.sv:<ID>` instantiated independently for each variant, and `formal/register.sv:<ID>`, all under the proposed fnd-06 fixture directory. Every row has expected count one per listed top.

| Stable ID | Exact intended condition / expected result |
|---|---|
| A-LUT-ALL | O equals independent INIT[I0+2*I1+4*I2+8*I3] for every 16-bit INIT and 4-bit input; assertion passes. |
| C-LUT-A6D3-A1 | INIT=A6D3, I=0001, O=1; cover reached. |
| C-LUT-A6D3-A8 | INIT=A6D3, I=1000, O=0; cover reached. |
| C-LUT-ONEHOT-HIT | INIT=0002, I=0001, O=1; cover reached. |
| C-LUT-ONEHOT-MISS | INIT=0002, I=1000, O=0; cover reached. |
| A-MUX-ORDER/<variant> | Generated L_I0 equals select ? secondary : local; assertion passes for SINGLE/LEFT/MID/RIGHT. |
| C-MUX-LOCAL/<variant> | local=0, secondary=1, select=0 and actual L_I0=0; cover reached. |
| C-MUX-SECONDARY/<variant> | local=0, secondary=1, select=1 and actual L_I0=1; cover reached. |
| H-REG-INIT-ONLY | !initialized -> EN && SR at sample 0 only; one explicit assume, no initial-q constraint. |
| A-REG-FF | initialized && FF -> O=q_shadow; assertion passes. |
| A-REG-COMB | !FF -> O=independent LUT value; assertion passes, no initialization guard. |
| C-REG-Q0 | initialized && FF && q_shadow=0 && O=0; cover reached. |
| C-REG-Q1 | initialized && FF && q_shadow=1 && O=1; cover reached. |
| C-REG-FF0 | initialized && !FF && O=d, with d=1; cover reached. Does not claim internal q equivalence in FF0. |
| C-REG-FF1 | initialized && FF && O=q_shadow, with q_shadow=1; cover reached. |
| C-REG-R0 | initialized && FF && reset_value=0 && previous EN=SR=1 && O=q_shadow=0; cover reached. |
| C-REG-R1 | initialized && FF && reset_value=1 && previous EN=SR=1 && O=q_shadow=1; cover reached. |
| C-REG-CAPTURE | previous/current initialized && FF && previous EN=1/SR=0 && q_shadow changes && O=q_shadow=previous d; cover reached. |
| C-REG-HOLD-SR | previous/current initialized && FF && previous EN=0/SR=1 && previous q_shadow!=reset_value && O=q_shadow=previous q_shadow=previous O; cover reached. |
| C-REG-RESET | previous/current initialized && FF && previous EN=SR=1 && previous q_shadow!=reset_value && O=q_shadow=reset_value; cover reached. |

Positive formal roster totals: six tops (one LUT, four switches, one register), **7 assertions, 1 explicit assumption, 21 covers**. Harness init attributes, symbolic constants, tie-offs and chosen clock abstraction are separately inventoried; zero explicit assumptions does not mean absence of all domain restrictions. A6D3 and 0812 remain asymmetric constants; accepted historical `additional_one_hot` names a three-set-bit value 0812, which is not counted as genuine one-hot activity. Mathematical one-hot inclusion in A-LUT-ALL plus the genuine one-hot covers and 256 literal simulation cases give explicit coverage.

**Control roster:** `A-CONTROL-FALSE` has one assertion, zero assumes/covers and must produce an assertion counterexample at step 0 with normal solver exit 1. `X-CONTROL-ZERO-EXPORT` uses a deliberately omitted/unlowered assertion export and must be rejected by the obligation-count guard before proof credit. `H-CONTROL-SELECT0` adds exactly one assume to the NF_SINGLE switch derivative; A-MUX-ORDER may pass, C-MUX-LOCAL must remain reachable and C-MUX-SECONDARY must be unreachable in its complete one-step combinational domain. Both original cover IDs remain required. Proposed source labels reside in `formal/controls.sv`; control receipts are separate from positive totals.

**Semantic negative roster:** location `semantic_cases.json:<ID>` references `specification.json#/illegal_configurations/<index>` for the nine historical rows, with exact expected `invalid-input:<code>` and one result each: `N-CARRY` unsupported-mode; `N-SOURCE-RANGE` invalid-mux-selection; `N-INIT-WIDTH` feature-width-overflow; `N-UNKNOWN-FEATURE` unsupported-feature; `N-MISSING-FEATURE` missing-config-feature; `N-OVERLAP` config-field-overlap; `N-SELECT-X` non-binary-stimulus; `N-PACKAGE` package-identity-mismatch; `N-PADDING-ADDRESS` invalid-config-address. Add independently reviewed `N-SELECT-Z` non-binary-stimulus, `N-ALIAS-CONFLICT` inconsistent alias requests and `N-THREEWAY-3` invalid-mux-selection (each one). Bind the latter two to exact accepted generic validator diagnostic enums after FND-05; their semantic categories cannot be substituted by arbitrary errors. Separate simulator `S-POSTINIT-X` and `S-POSTINIT-Z` cases intentionally observe each unknown after initialization and must report a non-binary output with named signal/time. Never count pre-init unknown state as these negative witnesses.

**Mutation roster:** each inherited ID uses the exact mutation-table target and intended failure, one result per variant below: `M-MUX-INDEX`, `M-LUT-BIT`, `M-CONFIG-ADDRESS`, `M-PRIORITY`, `M-CORR-SWAP`, `M-CORR-OMIT`, `M-CORR-DUPLICATE`, `M-ENDPOINT-OMIT`, `M-ENDPOINT-REVERSE`, `M-FIELD-ALIAS`, `M-ALIAS-CONFLICT`, and supplemental `M-CONFIG-CONSUMER`. Mapping swap/omit/duplicate controls are semantic mapping failures; endpoint omit needs compiled graph and binary behavior failures, endpoint reverse needs directed graph failure; alias conflict differs from overlap. The false/zero/vacuity controls above are additional distinct records. Materialize exact patch/source labels under `mutations.json`, original/derived SHA-256 and expected failing property/witness IDs; no parser/compile/hash/crash failure gets the intended category. Choose the LUT-bit implementation (INIT[1]/INIT[8] swap) and mux implementation (swap actual compiled mux A0/A1) as the frozen baseline mutations, rather than an execution-time choice of alternatives.

### Literal per-template and per-instance roster

The following names are exact independent oracle instance lists, not extracted candidate inventories:
- one: t00:SINGLE
- square: t00:LEFT, t10:RIGHT, t01:LEFT, t11:RIGHT
- odd: t00:LEFT, t10:MID, t20:RIGHT, t01:LEFT, t11:MID, t21:RIGHT
- sparse: t00:LEFT, t10:RIGHT, t11:LEFT, t21:RIGHT, t02:SINGLE, t22:SINGLE

Variant names expand to the exact NF_* identifiers. Each instance record references its accepted `specification.json#/shapes/<shape>/tiles/<tile>` record by actual array pointer and semantic key (not an assumed map syntax), plus the source paths/line spans of its generated cell. Baseline expected artifacts per shape are G-<shape>, COMPILE-<shape>, GRAPH-<shape>, SIM-<shape>, with generation/compile/passed comparison as distinct result kinds; each has count one per run, repeated separately for run-1/run-2.

| Shape | Instances | Semantic pins | Fixed intra-tile edges | Selectable edges | Intertile edges | Config chains |
|---|---:|---:|---:|---:|---:|---:|
| one | 1 | 22 | 11 | 2 | 0 | 20 |
| square | 4 | 92 | 46 | 8 | 2 | 80 |
| odd | 6 | 140 | 70 | 12 | 4 | 120 |
| sparse | 6 | 136 | 68 | 12 | 2 | 120 |
| Planned denominator | **17** | **390** | **195** | **34** | **8** | **340** |

The per-template structural denominator is four variants: 92 pins, 46 fixed edges, 8 selectable edges and 80 config bindings. Every per-instance structural record is still required, including each repeated type's parameterization, placement, frame paths and distinct state/config ownership. Totals are planned denominators, not executed coverage.

Record one exact ID per object: `PIN/<shape>/<tile>/<logical-pin>`, `FIXED/<shape>/<tile>/<from>-><to>`, `SELECT/<shape>/<tile>/<source-value>/<from>-><to>`, `CONFIG/<shape>/<tile>/<j>`, and `RESOURCE/<shape>/<tile>/<lut|lut.register|mux|config_memory>`. Each references its literal oracle record and resolved candidate path/type/bit/direction plus observed equality/result. Complete pin/edge/config sets must match, with no missing/extra/duplicated object. RESOURCE explicitly distinguishes the register state signal from the three module resources. Compile/aggregate hashes cannot satisfy these object witnesses.

The eight intertile witness bases are `LINK/square/t00.e->t10.w`, `LINK/square/t01.e->t11.w`, `LINK/odd/t00.e->t10.w`, `LINK/odd/t10.e->t20.w`, `LINK/odd/t01.e->t11.w`, `LINK/odd/t11.e->t21.w`, `LINK/sparse/t00.e->t10.w`, `LINK/sparse/t11.e->t21.w`. Each has one structural witness and two binary behavior witnesses suffixed `/value0` and `/value1` (16 behavior records), holding the downstream alternative/local source differently. The const0->lut.ci edge instead requires its fixed zero; constant edges are not required to transport one. Check source row/west adjacency and absence of any user path over holes separately from permitted frame transport.

For each of the 17 instances, freeze the following simulator witness families in `simulation/instances.sv` with emitted assertion labels and source/JSON-pointer bindings: `LOCAL-A6D3/<address0..15>` (16), `SECONDARY-A6D3/<address0..15>` (16), `REG-R0/<step0..8>` (9), `REG-R1/<step0..4>` (5), `FF0-STATE-R0/<step0..8>` (9), `FF0-STATE-R1/<step0..4>` (5). This gives **60 observation records per instance, 1,020 total**; records may contain multiple explicit checks, whose actual count is additionally reported. Register rows use the accepted 9-step/5-step traces and d-drive rule. For FF0 rows inspect LUT_flop as state and O as combinational output after each required event; pre-init q remains unconstrained. Secondary vectors drive ALT on SINGLE/LEFT and the actual predecessor's output on MID/RIGHT; configure the predecessor to independently known AAAA/source0 behavior and drive its A0 rather than forcing W. Hold the target's local A0 opposite the chosen secondary I0. Initialize all other tiles explicitly; no uncontrolled row can supply a passing observation.

Per-template unit roster: `UNIT-MUX/<variant>/<eight-case-index>` gives 32 cases; `UNIT-CONFIG/<variant>/<one|zero>/<j0..19>` gives 160 walking-pattern records, each observing all 20 Q/QN pairs. `UNIT-CONFIG-HOLD/<variant>/<j>` (80), `UNIT-CONFIG-TRANSPARENT/<variant>/<j>` (80), `UNIT-CONFIG-PAD-FRAME/<variant>/<f1..19>` (76), and `UNIT-CONFIG-PAD-DATA/<variant>/<b0..11>` (48) independently check storage/strobe and padding behavior with expected equality/update. `UNIT-LUT/A6D3/<a>`, `UNIT-LUT/0812/<a>` and `UNIT-LUT/ONEHOT/<j>/<a>` give 288 literal observations. Config padding-frame cases vary frame data while only that unused strobe is high; padding-data cases toggle only the named low bit under frame0 with used bits held fixed. Each uses a fully initialized known storage baseline, not unknown-value equality.

Finally, `INSTANCE-CONFIG-WORD/<shape>/<tile>` (17) observes that instance's independently assigned distinct legal word through its full consumer chain, and `COLUMN-HOLD/<shape>/<selected-x>/<unselected-tile>` covers every unselected instance for every configured column (0+4+12+12=28 records). Check register state separately while UserCLK remains low, without requiring pre-init q to be known. These are small explicit lists in the eventual witness manifest; optional random stress never replaces them. The independent per-instance setup words are fixed below (all INIT-only, FF=carry=reset-value=source=0); observe each ConfigBits vector and its actual consumer slices without hierarchical force. These complementary setup witnesses do not replace the separate FF/source/reset behavioral vectors or the compiled consumer mutation. Review these supplementary literals before GO; never derive them from candidate output.

| Exact instance | 20-bit word | Frame-0 word |
|---|---|---|
| one/t00 | 00001 | 00001000 |
| square/t00 | 00002 | 00002000 |
| square/t10 | 00004 | 00004000 |
| square/t01 | 00008 | 00008000 |
| square/t11 | 00010 | 00010000 |
| odd/t00 | 00020 | 00020000 |
| odd/t10 | 00040 | 00040000 |
| odd/t20 | 00080 | 00080000 |
| odd/t01 | 00100 | 00100000 |
| odd/t11 | 00200 | 00200000 |
| odd/t21 | 00400 | 00400000 |
| sparse/t00 | 00800 | 00800000 |
| sparse/t10 | 01000 | 01000000 |
| sparse/t11 | 02000 | 02000000 |
| sparse/t21 | 04000 | 04000000 |
| sparse/t02 | 08000 | 08000000 |
| sparse/t22 | 0A6D3 | 0A6D3000 |

The roster is finite and proportionate to the accepted four shapes, not a future general coverage framework.

## Complete inherited obligation and mutation inventory

All 15 accepted FND-02 execution IDs remain required:
- FND06-LUT-EXHAUSTIVE: symbolic actual source RTL all-INIT/all-address assertion plus separately labelled independent Rust 1,048,576-case model property; literal simulation witnesses.
- FND06-REGISTER: both reset values, FF modes, enable/reset priority and all edge categories.
- FND06-MUX: all eight binary cases and separate three-input invalid selection rejection.
- FND06-CONFIG: twenty physical bindings, strobe preservation/padding, legal and illegal semantic inputs.
- FND06-TILE: actual generated switch/configmem/tile with actual source LUT in both FF modes.
- FND06-GRAPH: all four shapes, total correspondence and exact directed edge sets.
- FND06-COVER-STATE: both q/select/FF/reset values and every declared link; explicit denominator and witness IDs.
- FND06-XZ-REJECTION: separate stimulus/output four-state failures.
- FND06-MUT-LUT-BIT, FND06-MUT-PRIORITY, FND06-MUT-MUX-INDEX, FND06-MUT-CONFIG-ADDRESS, FND06-MUT-CORRESPONDENCE, FND06-MUT-ENDPOINT and FND06-MUT-FIELD-ALIAS as below.

Mutations run on fresh labelled copies. Each binds baseline/derived hashes, one exact patch location, compile success where applicable, target obligation, expected category and actual failing witness. Baseline passes first. A generic hash guard, parser failure, missing file, compile error, crash, timeout or any unrelated rejection is a failed mutation experiment, never detection credit. The trusted mutation runner explicitly permits only its declared derived bytes so ordinary provenance checks cannot mask the intended semantic test.

| Mutation | Valid derivative / intended detection |
|---|---|
| MUX-INDEX | Swap actual compiled generated mux inputs (or invert its select) at exactly one site. Differing 0/1 input vector and/or symbolic assertion must fail at that mux. |
| LUT-BIT | Swap INIT[1]/INIT[8] in a labelled source-copy binding, or I0/I3 significance. A6D3/0812 literal addresses and symbolic LUT assertion produce an output mismatch/counterexample. |
| CONFIG-ADDRESS | Change one generated ConfigMem data-bit connection by one while retaining valid RTL. Walking-one/zero test fails the named bit/frame binding. Do not substitute logical padding rejection for physical-map mutation detection. |
| PRIORITY | Move SR ahead of EN in a labelled source copy. With q opposite reset, EN=0/SR=1 rising edge must produce the exact register semantic mismatch. |
| CORRESPONDENCE | Separately swap I0/I3, omit y, and duplicate a primary mapping in derived maps. Independent pin/order/totality check reports the specific semantic defect before traces; no self-normalization or mere digest rejection. |
| ENDPOINT | Omit the actual t00.e->t10.w connection by replacing the receiving signal with a defined 0, keeping compilation valid; exact graph and odd-row literal behavior must fail. Also reverse the declared candidate edge in a separate structural-control input: direction check must fail. Do not accept a combinational-loop hang as a reversal witness. |
| FIELD-ALIAS | Bind source and ff to physical bit 16 without a declared alias in a derived candidate binding. Independent ownership check reports overlap; inconsistent requests through an explicitly declared test alias separately report alias conflict. |
| CONFIG-CONSUMER (supplemental) | Misbind the actual compiled NF_SINGLE switch ConfigBits[0] to tile bit 16; require the named physical consumer mismatch and the explicit AAAA/source1 binary output mismatch described in P2. |
| VACUITY | Restrict select=0 but retain select=1 required cover; reject overconstraint with normal solver completion. Run the independent false-assert and zero-assert-export controls too. |

## Results, scale and determinism

Use explicit categories: `passed`, `semantic-mismatch` with expected/observed values, `invalid-input` with intended code, `mapping-mismatch`, `assertion-counterexample`, `cover-reached`, `cover-unreachable`, `missing-tool/unsupported-environment`, `provenance-mismatch`, `compile-error`, `tool-error`, `timeout/unknown`, `missing-artifact`, `zero-or-wrong-obligation-count`. Only the predeclared expected category/witness qualifies a negative control. A status string alone does not count: check process exit, actual assertion/vector execution, nonzero expected coverage, complete stage roster and bound artifact hashes. Add negative receipt tests for missing shape, zero assertions, removed cover, absent mutant, wrong source/artifact hash and substituted compile error.

Measure the existing bounded workloads, not a new PERF track: 1/4/6/6 tiles, 0/2/4/2 links, all four tile variants, 20 bindings/variant, 1,048,576 Rust LUT cases, exact simulation observations, fixed formal bounds and complete mutation inventory. Record wall/user/sys time, max RSS, generated/source RTL file count and bytes, structural JSON bytes, SMT bytes, trace bytes and per-stage result counts. Retain detailed host CPU/OS observations locally; publish only the required platform/ABI constraints, measurement scope and one-worker execution disposition; fixed seeds only where randomness actually occurs.

Run each shape twice from fresh output/config directories with identical reviewed pins. Compare byte hashes of actual RTL/source lists and exact candidate graph correspondence. `generation.json` intentionally records command/output paths, so do not demand its raw bytes match across different output directories or erase those provenance fields; compare its semantic/source/generated inventories separately and preserve both raw manifests. If emitted RTL embeds an incidental path/timestamp, retain the difference and review a narrowly specified reproducibility treatment rather than silently stripping it. Repeat semantic suites/coverage and record measured costs; no 16x16, production scale, PPA or routing-quality claim is needed.

## Reproducible environment and CI boundary

Prepared reference-tool versions (not accepted execution): Icarus/VVP 12.0 (Debian 12.0-2+b1), Yosys/SMT-BMC/ABC 0.52-2 (Yosys commit fee39a3284c90249e1d9684cf6944ffbbcbb8f90), Z3 4.13.3-1, CPython 3.12.14, uv 0.12.23 and FABulous 2.0.0 plus 79 frozen dependencies. Exact prepared host/runtime identity manifests stay local for independent inspection. Publish the approved portable tool/source/build/dependency inventory required to reproduce the qualified reference profile; do not publish a private host fingerprint or treat an observed local manifest as upstream provenance. Refresh effective executable, import, dependency and ABI identities after GO.

After GO, invoke the prepared venv's Python directly, or `uv run --no-sync`, with the exact clean source. Avoid default editable sync: it dirties upstream with egg-info/fabulous_nix. The installed distribution metadata comes from an exact-source archive wheel; imports must still resolve to the pinned clean checkout. Use fresh HOME/XDG/FAB_USER_CONFIG_DIR, explicit pinned FAB_YOSYS_PATH and bounded output roots; record effective configuration and executable resolution. The runner's historical suggested command remains historical input; a new execution receipt documents the actual no-sync command. No reference tool enters default core PATH/dependencies or the saved-package runtime profile.

Required prepared-tool ABI: Yosys/Z3 require glibc>=2.38 and libstdc++>=14. Successful same-host relocation is not Ubuntu24.04 qualification. Historical capacity probes did not establish a qualified isolated reference container or complete network isolation. Recheck the actual supported isolation capabilities after FND-05 acceptance; keep detailed host/probe observations local. Missing required capabilities block the affected execution; no unrestricted fallback earns acceptance.

Before final CI, qualify a separate reference-only environment: digest-pinned Debian trixie base with exact package/archive checksums and an explicitly pinned CPython3.12.14 interpreter/build, stdlib and required runtime ABI libraries. Debian default Python is insufficient proof of cp312 compatibility. An official exact source build is a possible route; pin its source checksum/build recipe and separately record its binary identity, then rerun dependency/import/ELF/tool false-control smokes and the complete corpus. Do not assume a named Python image/tag exists without checking. Reconstitute locked dependencies from official hash-checked archives; keep local FABulous/SDF build-source pins and wheel identities explicit. If container binary/wheel bytes differ from prepared local builds, record the separately qualified environment rather than claiming byte-identical reuse.

Use a clean unprivileged ephemeral test container on final-CI infrastructure, read-only source inputs, dedicated writable outputs, bounded memory/time/one worker, dropped capabilities and no network during actual verification after provisioning. Record base-image digest and actual resulting image/runtime manifest, not a mutable tag alone. This test container is not a new core/default dependency or a Nodal distributable. The existing Ubuntu24.04 workflow runner can host a qualified Debian container; executing extracted trixie tools directly on that runner is unqualified. A successful local run does not replace this CI qualification/replay. Follow the coordinator's current authorized CI cadence; do not dispatch from this proposal.

## Actual generated-output retention and summary delivery

The source parser removes unused tile types. Planned inventories are one:SINGLE (7 total RTL files), square:LEFT/RIGHT (10), odd:LEFT/MID/RIGHT (13), sparse:LEFT/RIGHT/SINGLE (13): 31 generated entries and 12 copied-source entries across four fresh outputs. Verify actual inventories after generation; these are not executed counts. The full pinned commit also binds helper/code-writer sources outside the 17 selected source hashes; record resolved imported paths.

For each shape retain original authored input, exact upstream source/license copies, all generated `Tile/<type>/{<type>_switch_matrix,<type>_ConfigMem,<type>}.v`, `Fabric/eFPGA.v`, `sources.f`, raw `generation.json`, stdout/stderr, exact commands, tool/dependency inventories and hashes. Raw logs, original path-bearing manifests and private execution details remain local for independent inspection. Classify `BEL/LUT4c_frame_config_dffesr.v`, `BEL/nf_tiny_io.v` and `Fabric/models_pack.v` as **source RTL**, with FABulous-generated switch/configmem/tile/fabric separately labelled. Preserve all shapes, not just a pasted successful excerpt.

Retain test/formal source, compiled simulator identity/hash, observations/waveforms, structural JSON/expected graph identities, SMT2/property inventory, covers/counterexamples, mutation patches/outputs and resource measurements for the independent review. Publish the required portable executable fixtures, independently authored specifications, actual generated/source RTL with reviewed provenance, portable manifests and mutation specifications as hashed deliverables; publish concise separate observations for the executed stages. Raw execution output and detailed intermediate traces stay local. A portable deliverable manifest gives relative paths, sizes and SHA-256; summary receipts bind actual tested commit/tree, upstream commit/tree, historical input/ledger hashes, stage, topology, reproducible command, qualified profile and observed result. Preserve private exact executable resolution locally, representing it publicly by the reviewed tool identity and environment wrapper. The report at `docs/completion/FND-06.md` is itself hashed and links the receipt and actual permitted artifact identities. Temporary local retention alone cannot replace a required portable deliverable, but no new raw-log upload is required. Receipts use actual executed identifiers and counts, never planned values.

Use version 2's existing observation and review schema: clean-source execution has positive complete required/executed/passed counts, zero failed/skipped and successful harness exit; negative child exits qualify only through checks of their intended result. The independent reviewer must cover every observation and all three review dimensions. Keep integration pending until the actual merge exists; record source and real merge identities separately. A later documentation-only closure requires the narrow source-anchor check, actual documentation validation and verified closure integration. Summary validation alone never proves tests, review or final-head qualification.

Show the real CSV frontend and actual generated external-reference Verilog in the completion demonstration, including an actual tile/config/mux snippet and the corresponding hashed full files. Scala is not the reference frontend; no Nodal fabric emission is demonstrated. Do not use the blanket no-Verilog-effects statement to hide that FND-06 generates external reference RTL; instead explicitly state which reference outputs were generated and that production Nodal generation remains absent.

Licensing: preserve FABulous Apache notices and exact provenance. The retained lln-libparse 0.56.0 attribution investigation identifies unresolved exact LLVM contributor/pybind11 notice ancestry; recovered candidate notices are not exact resolved attribution. Keep official wheels external, installed from official sources for the reference environment. Do not vendor/redistribute the wheelhouse, uncertain-credit wheels or a bundled tool image in Nodal packages; archive dependency identities/official URLs/notices instead of republishing dependency binaries. No secret/proprietary material enters fixtures. FND-07 carries the explicit redistribution boundary and environment policy forward; this preparation grants no redistribution clearance.

## Recommended handoff sequence

1. Finish FND-05 independent review, verified integration and evidence closure; establish accepted FND-05, then refresh actual dev/ref/PR/protection and inspect final interfaces. Approve/readiness-record the complete FND-06 scope on its own authorized branch/PR, retaining all IDs.
2. Freeze small independent property, semantic, structural, simulator and formal/cover contracts before running the generation owner. Review literal additions and exact expected counts/mutations.
3. GO the pinned generator on all four fresh outputs; retain generation/compile evidence first. Diagnose any source/API discrepancy without editing oracle values.
4. Execute Rust, structural, simulation, symbolic/BMC, cover and every semantic mutation independently; diagnose first failures before broad reruns. Repeat for determinism/cost observations.
5. Independently review actual local executions, required artifacts and common-mode controls; preserve predecessor regressions and exact source anchors. Qualify the local reference environment and prepare the reproducible separate CI environment; perform required branch-protection checks if any. Defer the complete remote reference replay to the final combined Foundation CI under the user-approved cadence, without counting it as already executed.
6. Complete durable source-bound summary evidence, required local qualification/review, verified integration and authoritative FND-06 closure under the explicit current-task CI disposition only when its applicable gates are genuinely satisfied. FND-08 must execute the retained corpus in full combined remote qualification before opening downstream eligibility; no later RTL/VER gate is checked by this work.
