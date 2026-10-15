# nf-tiny Foundation reference contract

Decision state: **accepted-for-profile**, following [independent review](../implementation/fnd-02-independent-review.md). Hardware evidence state: **not-run**.

This is the independently authored common-subset contract for FND-02.d/f/g.
It defines reviewed inputs and expected semantics; it does not report an RTL
simulation, formal proof, production Nodal generator, CAD flow, loader, physical
implementation or silicon result. Independent review is retained separately from execution.
FND-06 owns executable reference generation and comparison. RTL-01–04 later
replay the appropriate comparisons against actual Nodal-generated hardware.

## Artifacts and independence

- [`specification.json`](../../verify/fixtures/nf-tiny/specification.json): the
  normative logical semantics, explicit vectors, legal/illegal examples,
  template graph, four independently enumerated shape graphs and execution IDs.
- [`correspondence.json`](../../verify/fixtures/nf-tiny/correspondence.json):
  expected resource/pin/configuration correspondence, transparent aliases,
  exclusions and totality checks. It is not extracted from Nodal lowering.
- [`reference.json`](../../verify/fixtures/nf-tiny/reference.json): immutable
  upstream revision, source hashes, authored-input hashes, licenses and pending
  execution/toolchain obligations.
- [`fabulous/`](../../verify/fixtures/nf-tiny/fabulous/): real FABulous CSV input,
  transparent I/O source and a source-pinned generation runner. No production
  Nodal implementation computes this input or the expected results.

The source pin is FABulous **v2.0.0**, commit
[`d2fc49dade524a4f78062a3a38b213e9c08d6b04`](https://github.com/FPGA-Research/FABulous/commit/d2fc49dade524a4f78062a3a38b213e9c08d6b04).
The annotated/tag name is descriptive; the full commit and file hashes govern.
It is a released source version, rather than an unpinned development branch.
The clone and exact source text were inspected. Generation and simulation have
not been run as part of this contract review.

The upstream LUT/register and primitive models remain unmodified **source
inputs**, with their original attribution. FABulous generates the switch,
configuration-memory, tile and fabric modules around them. The generated tile
instantiates the real upstream LUT/register. Neither that source primitive nor
our transparent I/O helper may be relabelled as generated RTL. The retained
Apache-2.0 license is in `fabulous/LICENSE.FABulous`; upstream's LUT header is
Copyright 2021 University of Manchester. This revision has no NOTICE file.

## Exact LUT and register semantics

The selected [upstream LUT4 source](https://github.com/FPGA-Research/FABulous/blob/d2fc49dade524a4f78062a3a38b213e9c08d6b04/fabulous/fabric_files/FABulous_project_template_verilog/Tile/LUT4AB/LUT4c_frame_config_dffesr.v)
sets address `I0 + 2*I1 + 4*I2 + 8*I3` and returns `INIT[address]`.
Bit 0 is the value at address 0000, not the first character of an MSB-first hex
string. The explicit A6D3 truth vector, in ascending address order, is
`1 1 0 0 1 0 1 1 0 1 1 0 0 1 0 1`.
The additional 0812 witness sets only addresses 1, 4 and 11. These asymmetric
patterns expose input permutations that AND/XOR-only examples can conceal.

On **rising UserCLK**, EN=0 holds the previous state regardless of SR.
EN=1/SR=1 loads the configured reset value. EN=1/SR=0 captures the LUT result.
There is no asynchronous reset or specified initial state. Changing SR without
a rising edge does not change the register. FF=0 selects the combinational
result; FF=1 selects the register. The register still updates when FF=0.
Both reset values and both FF modes are required witnesses.

The upstream carry-select bit is constrained to zero and Ci is fixed to zero.
Co remains a real, unobserved upstream majority-carry output; it is explicitly
excluded and must never be assumed zero. No carry or fractured-LUT claim is
made. Each stimulus and observation in the binary matched domain must reject
X/Z rather than coercing it to zero. Unknown initial q is permitted before the
explicit EN=SR=1 initialization edge and is not a fabricated failure or pass.

## Routing and boundary graph

Every present tile has one LUT/register, one 2:1 routing mux, direct user I/O
and one immutable instance identity. The mux drives LUT I0; LUT I1–I3, EN and
SR have fixed directed links from user inputs. LUT O drives the user output
and, where present, the east output. Ci has a fixed zero driver.

Mux selection 0 selects local A0. Selection 1 selects ALT in NF_SINGLE and
NF_LEFT, or the predecessor's west input W in NF_MID and NF_RIGHT. There is
no disable value, wired-OR, bidirectional pass switch or simultaneous selected
sources. Every binary encoding is legal for this 2:1 mux. Invalid nonbinary or
out-of-width values are rejected by the semantic input contract, not masked.

The matrix inputs are literal CSV columns, with all selected cells equal to 1.
At the pinned [parser](https://github.com/FPGA-Research/FABulous/blob/d2fc49dade524a4f78062a3a38b213e9c08d6b04/fabulous/fabric_generator/parser/parse_switchmatrix.py),
that means left-to-right source order. The
[generator](https://github.com/FPGA-Research/FABulous/blob/d2fc49dade524a4f78062a3a38b213e9c08d6b04/fabulous/fabric_generator/gen_fabric/gen_switchmatrix.py)
places the first source at mux index 0 and allocates mux bits in row order.
Only L_I0 has two sources; every other row is a fixed link with no config bit.
Using CSV avoids `.list` ordering/priority ambiguity.

The proposed shapes are:

| Input | Dimensions | Present tiles | East links | Purpose |
| --- | --- | --- | --- | --- |
| one.csv | 1 x 1 | 1 | 0 | All boundaries, no neighbor |
| square.csv | 2 x 2 | 4 | 2 | Two independent row chains |
| odd.csv | 3 x 2 | 6 | 4 | Odd width, repeated middle template |
| sparse.csv | 3 x 3 | 6 | 2 | Explicit holes, offset chain, isolated tiles |

Coordinates increase east in x and south in y. `specification.json` enumerates
all present coordinates, types and intertile edges independently of the CSV.
A hole never creates a connection across the gap. There are no north/south user
routing edges; two-dimensional placement exercises clock/frame/boundary
wiring but does not imply a 2-D routing network. Four boundary tile variants
ensure that no required west input dangles and no east output escapes the
fixture. NF_MID/NF_RIGHT retain unused ALT input pins as explicit exclusions.

The tiny graphs are fully enumerable oracle data, not a requirement to flatten
production DeviceDB. Repeated tiles may share immutable template definitions;
instance paths and configuration ownership remain distinct. Declaration
reordering is allowed only with the reviewed semantic map; reordering mux
inputs or changing physical bit bindings requires translation and a new
appropriate identity, rather than claiming byte compatibility.

## Configuration, aliases and clocks

Each tile has exactly 20 logical config bits: INIT[15:0], FF[16], constrained
carry-select[17], reset-value[18], and source-select[19]. BEL declaration order
places the 19 LUT bits first; the switch receives tile bit 19 as its own bit 0.
The explicit ConfigMem CSV maps frame 0 data bits 31:12 onto config bits 19:0.
It declares 20 frame rows; other frames and data bits are padding without
storage. Every bit is explicitly set; no power-up default is assumed.

For A6D3, the comb, registered-reset0, registered-reset1 and alternate-source
20-bit words are 0A6D3, 1A6D3, 5A6D3 and 8A6D3. Their frame-0 words are
0A6D3000, 1A6D3000, 5A6D3000 and 8A6D3000 respectively. These values are
independent arithmetic examples, not bitstream-generator output.

The full fabric exposes FrameData with one 32-bit word per row, at `[32*y+31:
32*y]`, and FrameStrobe with 20 bits per column, at `[20*x+19:20*x]`.
For static setup keep UserCLK low, set every row's intended data, assert frame
0 strobe for the selected column, then deassert it before observing. Repeat
for columns. [Configuration latches](https://github.com/FPGA-Research/FABulous/blob/d2fc49dade524a4f78062a3a38b213e9c08d6b04/fabulous/fabric_files/FABulous_project_template_verilog/Fabric/models_pack.v)
are level-sensitive while their strobe is high. This is a declared unit/frame
memory interface setup, not proof of a runtime bitstream controller, atomic
activation, interrupted loads or restart behavior. RTL-04 owns the real-loader
obligations. UserCLK and configuration strobes are distinct signals.

No logical configuration aliases are declared. Transparent I/O names and
ConfigBits_N are physical signal aliases, not independent writable features.
Undeclared overlap, inconsistent alias requests and applying a different
package's mapping must fail closed. Nodal's logical rejection of an unmapped
configuration address must not be confused with the reference's hardware
padding, which has no error port and simply has no storage there.

## Execution and qualification boundary

A planned generation command, after FND-06 selects and records exact Python,
Yosys and dependency builds, is:

```sh
uv run --project "$FABULOUS" --frozen --no-dev python \
  "$NODAL/verify/fixtures/nf-tiny/fabulous/generate.py" \
  --upstream "$FABULOUS" --output "$OUTPUT/one" --shape one
```

Repeat for square, odd and sparse with fresh output directories. Use a clean
HOME/XDG configuration directory and explicit pinned FAB_YOSYS_PATH. The
upstream uv.lock is hash-pinned; exact resolved runtime identities and licenses
remain FND-06/FND-07 obligations. The runner checks the immutable upstream and
all authored-input hashes, refuses to overwrite output, emits sources.f and
records generated/source artifacts separately in generation.json. Preserve
stdout/stderr, exact commands, tool identities and generated artifact hashes.
Failure or missing tools must remain an explicit blocker.

Python 3.12+ is required by this release. Yosys is used internally to parse BEL
ports, not to synthesize a customer design. No nextpnr placement/routing,
bitstream-generator or ASIC flow is invoked by this runner. FABulous's Python
package imports some physical-flow libraries; keep these in the isolated
reference environment, never the core/default runtime. Pin actual simulator
and solver builds separately before claiming any execution result.

FND06-LUT-EXHAUSTIVE, REGISTER, MUX, CONFIG, TILE, GRAPH, COVER-STATE and
XZ-REJECTION require the stated scopes in the JSON. Mutation IDs cover LUT
indexing, EN/SR priority, mux ordering, frame addressing, endpoint loss/reversal,
field aliasing and faulty correspondence. A timeout or unrelated crash does
not count as a detected mutation. The template map must remain total across
pins, directions, state, config significance and every observed output.

Three-input mux invalid-code rejection, configuration aliases, asynchronous
reset, carry, multi-clock/CDC, pass switches, power isolation, supertiles and
runtime transports are not matched by this reference. Nodal requirements for
those capabilities are retained and need separate independent tests. Source
supports the proposed rectangular/NULL layouts and has its own 32-row/32-column,
32-data-bit/20-frame restrictions; none are permanent Nodal architecture limits.
Successful generation of each proposed shape is still **not-run** until FND-06.

Any source revision, correspondence, input order or semantic change requires
review and replay. Never regenerate an expected answer from the implementation
under test to make a disagreement disappear.
