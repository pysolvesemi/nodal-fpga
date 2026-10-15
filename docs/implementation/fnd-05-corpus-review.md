# FND-05 independent corpus and conformance summary

Status: independent corpus frozen; final local conformance replay passed on the
source/binary identities recorded below. Scope-specific result only.
This report does not close a checklist item or claim final increment acceptance.
The parent owns qualification, runtime/dependency review, publication and verified
integration. All results described here are local unless explicitly identified
otherwise; no remote CI was run by the corpus author.

## Independent authority and retained provenance

The complete literal corpus was fixed outside the repository before production
reader/writer answers, against accepted FND-04
`c508401afb3bc172a28163b84375157e1ce2ac2d` and the R1–R5 readiness contract
published at `4895bcc96f527049ad1b22a206987959b11b9878`.
Preparation status and all expectation bytes are preserved. Temporary-path
references in explanatory prose were replaced with repository-relative names.
The original review was locally archived with SHA-256
`5bcd1420357a6bc3561dc264144a66667cca543ad42d49feefc0ca940ebf1318`;
this editorial summary does not constitute a new execution or acceptance review.

- [Preparation expectations](../../verify/fixtures/exchange/preparation.md) retain
  every original C00–C38 byte length and digest. The pre-sanitization report had
  SHA-256 `67436527d7357a98e620a2df532cc6fdba2de696b9e48217154cb71647015546`
  and is preserved locally; that is not a hash of the edited document.
- Original C00–C38 and domain-hash input bytes remain unchanged in
  [algorithm](../../verify/fixtures/exchange/algorithm/). Their copied manifest
  SHA-256 is `1f521e92126fd7392dd5a47828d0cfa7986f43e262f5b9de6665d7ea105f19af`.
  C25–C27 remain incomplete examples, not promoted to accepted envelopes.
- [Full goldens](../../verify/fixtures/exchange/goldens/), with original manifest
  SHA-256 `acfd21c1b776a3565796fad15186db4b0b0993585b1c480bc790841b398ff4b9`.
  [EXPECTED.md](../../verify/fixtures/exchange/goldens/EXPECTED.md) freezes hand
  semantics; [IDENTITIES.md](../../verify/fixtures/exchange/goldens/IDENTITIES.md)
  records independently calculated identities. Explicit literal assembly source,
  and audit source remain alongside them. Raw preparation logs are locally
  archived outside the candidate, not repository fixtures.
- Focused independently authored package cases have manifest SHA-256
  `d6e1bba14a28ffa88faf5d0123369eafbff39daaf68fbc8195d9eb45e6c927af`;
  focused guard/resource-alias/range cases have manifest SHA-256
  `dd506d29c3d01e5b4c77147d0bcb7b6e591c16fe48aa3e0bc4156045a9527ba2`.
  These additions did not alter either original manifest.

The independent author used literal/manual object and collection order, Python
standard-library JSON and hashlib, and ordinary sha256sum. No expected bytes,
projections, semantic summaries or hashes were captured from candidate output.
Dynamic changed inputs use an explicit schema-directed test projection, separately
crosschecked against the fixed full goldens; it never calls production helpers.
No recursive key-name exclusion or golden-refresh-on-failure is permitted.

### Primary identity chain

| Item | Independent expectation |
| --- | --- |
| Architecture raw bytes | 6,624, including leading space/LF and final LF |
| Architecture raw SHA-256 | `432171ad8cfc32c3a684584c6af990f8a665a89fcd7c74a03f421490a44601f5` |
| Architecture semantic ID | `0c5e51acf90f91981b7e3375e5ab58b05d20020aa51a594008f8d7a30e1c80a4` |
| Package build ID | `0cbc4eb05c0f661740158587135aa55b4e03ab74f6a9e5e1dcfa95e3c42fbf9f` |
| Target-bound design ID | `bae95cd16fc8ffa058248eb3b83ea91bd6963b62833c48f04abb7d961265cddd` |

The architecture has one retained template, three independent roots, four local
BEL declarations, two fixed cross-root connections, and an ordered east/local/
west three-input mux. Selector values 0/1/2 select those exact indexes; 3 is
illegal. Shared clock/configuration and differing power domains are preserved.
The design has two cells, three ports, four nets and five loads; terminal direction,
bit bounds and single-net ownership are independently asserted. Unconnected
terminals remain permitted by the structural profile.

Focused fixtures preserve hierarchy and literal `..`/`a/b` components, direct
alias classes, mutually exclusive guards, high-u64 capacity/last-bit ranges,
ordered pin/mux changes, keyed permutations and cold provenance/annotation edits.
A sparse root hole rejects references into the hole, then accepts after those
edges are removed. A legal routing cycle remains distinct from illegal recursive
template instantiation. Numeric sets explicitly put 2 before 10.

## Executable controls and intended outcomes

The [test README](../../tests/exchange/README.md) gives executable reproduction and
layer ownership. No test starts a competing Cargo/sbt build. Missing prebuilt Rust
or actual Scala authoring output is an error, never a skipped required test.

| Area | Independent observation/control |
| --- | --- |
| Canonical bytes | All C00–C38, unsigned UTF-8 U+E000/U+10000 order, escapes, no normalization, exact full/projection dumps and round trips |
| Parser rejection | Malformed UTF-8/surrogates/JSON/BOM/truncation/trailing value; duplicate decoded keys at every architecture/package/design record and annotation levels |
| Scalars | U64 grammar/type/escaped digit, 2^53−1/2^53/2^53+1/2^63/u64 endpoints, narrower partition/Width/source ranges, metadata/annotation integer lexemes |
| Closed schema | Unknown/missing/wrong/null at semantic records; required nullable fields tested separately from legal null; exact versions/profiles/features |
| Ordering | Paired invalid fields prove input-order failure rather than map-sort order; tagged discriminator selects variant then payload retains input order |
| Diagnostics | Exact RFC6901 hostile backtick/slash/tilde keys, repeated parent-name tokens, unknown enum marker strings cannot forge codes; bounded presentation with exact large pointers |
| Semantics | FND-04 diagnostics remain original typed categories and origins; hierarchy, domains, mux/alias/guard/selection outcomes use public APIs |
| Package | Raw digest plus length before architecture interpretation; build preflight before resolver; no inferred design dependency; immutable digest reuse; flat opaque artifacts |
| Design | Wrong target precedes nonexistent type/pin lookup; proper resource_type key resolves a BEL; modes, pins, bit bounds, direction and ownership failures are distinguished |
| Unsupported work | Explicit unbound roles and fully bound opaque roles both leave RTL/device/route/program/timing operations unsupported |
| Limits | Exact byte/node/depth/string/collection boundaries; lowered FND-04 axes; zero/raised values on all 16 caller-limit fields across all four public read APIs |
| Scale | Independent roots, template depth, UTF-8 annotation/provenance byte lengths, stable repeated canonical/raw/semantic outputs, exact adjacent rejections |

Every negative CLI test requires nonzero exit and empty stdout. Field-specific
controls assert the exact intended pointer; semantic controls assert the intended
original core category. A stale identity, missing artifact, parser recursion
failure or unrelated exception cannot stand in for a different intended failure.

### R1–R5 controls

- R1: valid resource_type key/BEL succeeds; bel-typed key is invalid_enum, declared
  wire resolution is semantic/wrong_kind, absent type/mode has its own category.
- R2: negative zero/fraction/exponent numeric lexemes reject; i32 and u16 endpoints
  and adjacent ranges are checked independently. Escaped decimal digit strings
  remain valid U64. Numeric literals beyond i32 that fit Serde integer visitors
  report overflow; beyond their integer representation report invalid_json,
  never acceptance/coercion. Semantic U64 string overflow remains overflow.
- R3: counted resolver controls establish zero calls for preflight failures, one
  read per unique admitted digest, exact EOF and length+1 maximum probe, short/
  corrupt/nonterminating stream outcomes, and no reopening after backing mutation.
- R4: manifest/URL/design-looking opaque bytes are not interpreted or recursively
  resolved. Added design role and design-as-architecture reject. Tool source IDs
  do not become resolver requests or runtime executable hooks.
- R5: manifest build ID precedes resolution; raw artifact integrity precedes
  architecture interpretation; design target precedes target lookups; late
  self-ID failure publishes no accepted output.

### Manifest counters isolated from architecture validation

The primary literal manifest has 12 role bindings plus body, architecture binding
and descriptor: 15 declarations. Architecture semantic identity plus descriptor
are 2 references. Ten 24-byte reasons, one 12-byte reason and one 14-byte reason
charge length+1, totaling 278; declarations+references+one descriptor insertion
produce 296 work. These counts were calculated directly from the independent
literal and the documented accounting contract.

Each axis is tested independently at total−1, total and total+1. A fake NotFound
resolver proves total−1 fails with limit/semantic at `/body` and zero calls, while
exact/above reaches the resolver exactly once. It deliberately stops before
architecture validation so an independent larger architecture budget cannot mask
the manifest result. All 16 zero/raised public capability controls use readers
that panic if touched, proving invalid configuration fails before input or resolver.

## Transparent expectation corrections and implementation findings

Four initial Python semantic category labels were transcription mistakes. They
were corrected against unchanged accepted FND-04 source, not inferred from the
candidate's answer:

| Case | Accepted FND-04 authority | Correct original category |
| --- | --- | --- |
| Root partition null | declarations.rs root partition check | partition_mismatch |
| Repeated guard group | declarations.rs feature guard check | guard |
| Repeated finite domain value | declarations.rs feature_domain | domain |
| Reserved three-input mux value | connections.rs mux_domain | domain |

Accepted-source SHA-256 matched both the working file and `git show c508401...`:
`declarations.rs` = `a64f426b8d9eec0b04de039d6c45ab85b33a1cafd0f999714d8781a407f8dc43`;
`connections.rs` = `0598e3e5957704e99a45847b377b48e3bf230bda893a70ae69601bf73c531277`.
No golden byte or intended legal/illegal semantic outcome changed.

The tests exposed genuine candidate defects in metadata overflow classification
and nested tagged-field pointer retention. Review added input-order, hostile
error-marker, repeated-parent pointer and checked partition-order controls;
production owners repaired these without changing the independent outcomes.

The first API test revision used compile-time fixture inclusion. The existing
ownership guard correctly rejected this. Tests now read the unchanged fixture
files with standard filesystem reads rooted at CARGO_MANIFEST_DIR; the guard was
not weakened. Five direct Limits initializers replaced lint-triggering post-default
assignment; no lint was suppressed.

## Actual local execution, 2026-10-15 UTC

The final independent replay passed **83 Python test groups in 4.964 seconds**
using an already-built reader and actual fresh Scala output; it launched no build.
Reader SHA-256 was unchanged before and after:
`2ccf48d3d54b005d23064a827394b227fb8e94891c2223d4051885ea25a2b920`.
The designated build owner's Rust lane passed **12 independent public-API tests**,
8 exchange unit tests, predecessor suites, formatting and strict Clippy.

The [original 43-entry source vector](fnd-05-development-source.sha256), SHA-256
`39728b58f179b0624cb306d3a96dd97fc9ed62c99cb6bc6d0b515efea05868fe`,
binds the uncommitted implementation/test inputs. HEAD
`4895bcc96f527049ad1b22a206987959b11b9878` alone does not identify those inputs.
Deterministic test seeds were 0, 1, 17, 365 and 65535; reviewed default ceilings
applied except explicit caller-lowered boundary controls. Earlier 68/73-group
runs are intermediate history only. Raw logs and copied generated observations
were archived locally outside the candidate; none is a published expected input.
The functional literal corpus and its integrity manifests remain unchanged.

### Measured separate axes

Elapsed values below are observations on this local profile, not guaranteed
upper bounds; each CLI invocation also has a 30-second harness timeout. Deterministic test construction and source
binding preserve reproduction of each point; raw timing logs stay local.

| Axis | Independent points and final observations |
| --- | --- |
| Repeated roots | 1/16/256/4096; two repetitions each; 2,156–714,686 input bytes; retained one template; 4096 case 0.679 seconds total |
| Template depth | 1/2/16/64; 2,135–25,382 input bytes; depth64 0.013 seconds; depth65 semantic limit; no flattening |
| Annotation payload | 0/1/128/1024/16384/65536 decoded UTF-8 bytes; two canonical/projection/summary repetitions each; largest 72,073 input bytes and 0.056 seconds; 65537 rejects |
| Provenance payload | 0/1/128/1024 decoded UTF-8 bytes; two repetitions each; largest 7,621 input bytes; 1025 rejects original core limit |
| Container/parser boundaries | Pure array/object/mixed 64 accepts and 65 rejects; full-envelope overhead included; exact 8MiB input, 200000 nodes, 16384 entries, 65536 string-byte boundaries and adjacent failures |
| Diagnostic amplification | 64 containers, each admissible 65536-byte key; 4,260,166 input bytes; final duplicate yields exact 4,194,496-byte escaped pointer with only 28 message bytes; 0.769 seconds |

Cold payload changes preserved the fixed primary semantic projection and ID while
changing independently computed raw digests. Numeric capacity up to u64::MAX
remained a scalar; no allocation proportional to that capacity was requested.
The diagnostic control's input SHA-256 is
`5b4f1f983642c1d774305703e6c6003a01b9374fb30bbc54681c2454ebcf9e9b`.
The test asserts every structured-pointer byte and records its length plus
bounded presentation size; that large diagnostic is not reproduced here.

The actual Scala fixture is separate from the honest hand-authored package.
Its architecture semantics must equal the independent primary projection exactly;
its own typed provenance/annotations, source-bound authoring identity and exact raw
artifact digest legitimately produce different package/design identities. The
Scala harness verifies the actual source SHA before writing; the independent
cross-language tests verify it again and recompute package/design expectations
with Python standard-library hashing. Authoring provenance is not authentication.

Actual source SHA-256 is
`3a2d58dc56cbb5728c8dce3bda64c606ee8eae3be4942725f6ff6cb499e96722`.
Its architecture is 6,525 bytes with raw SHA-256
`17217b1c8f0bb606693aca0977b6edafb6bfc4feb58cf2fdae0a9a9e7ed263ca`;
semantic identity remains the independent primary architecture ID. The actual
package build ID is
`19eb6b74ea1bb42f94736b4d149a249e1a55f70b03313a01d73df85f7b32bf14`,
and target-bound design ID is
`f0bc2631ced9c862f357ad943934cf1c58f0be59d90be73c5853198b1061d891`.
Actual canonical/projection outputs were verified without altering goldens.
The [published example](fnd-05-example.md) retains the complete three actual
envelopes; generated observation copies and execution logs remain local only.

The independent source/runtime reviewer reported all six same-boundary cases
passing for this reader. The [runtime summary](fnd-05-runtime.md) records actual
outcomes and limits; this corpus review makes no syscall/exec-tracing or broad
sandbox claim. Final clean-head qualification and integration remain pending.

## Boundaries retained

These checks cover bounded portable structural exchange and saved software-package
inspection. They do not establish production-device scale, exact RSS or real-time
bounds, RTL, DeviceDB lowering/full-device inspection, physical allocation, route
legality, timing, transport or programming. Separate dependency/source-quality
review, real allowlisted saved-runtime evidence, full predecessor regressions,
policy-governed qualification and final integration remain parent-owned gates.

This increment does not affect generated Verilog.
