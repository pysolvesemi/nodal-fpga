# FND-05 independent serialization expectations (preparation)

Status: read-only preparation outside the repository. No production parser,
canonicalizer, serializer or hash implementation was called to derive these
expectations. No repository file was edited, no tools were installed, no branch
was published and no implementation/acceptance/CI result is claimed. The exact
wire contract and accepted envelopes remain subject to the FND-05 readiness
freeze after FND-04. This increment does not affect generated Verilog.

The observed checkout was `increment/fnd-04-core`, HEAD
`6d3c429950fc401ef351defb3efa871a994db0b7`, with existing FND-04 worktree edits.
This is a source-inspection snapshot, not an accepted or remotely refreshed
integration identity. Sources read: repository AGENTS.md; FND-05 complete
checklist; ADR 0002 and ADR 0003; foundation contracts; core API; current public
`nf-types` identity/units/diagnostics and `nf-arch-ir` declarations; FND-04
readiness; the preparatory FND-05 readiness proposal and runtime-capacity review.
The runtime capacity probe does not qualify an actual saved-package consumer.

This published copy changes explanatory path references only; all literal
expectations, byte lengths and digests remain unchanged. Original prose is
archived locally; it is not an execution log or a new conformance result.

## 1. Exact proposed contract and what remains provisional

These expectations follow the parent's proposed wire rules:

- Canonical bytes are UTF-8 without BOM, whitespace outside strings or final
  newline. A domain-separator prefix may itself contain a newline; that is a
  hash-input delimiter, not a newline in canonical JSON.
- Object keys sort lexicographically by unsigned UTF-8 byte strings, after JSON
  escape decoding. U+E000 sorts before U+10000. UTF-16 ordering is incorrect.
- Strings escape quote/backslash and use `\b`, `\f`, `\n`, `\r`, `\t`. Other
  U+0000–001F controls use lower-case `\u00xx`. Slash and all other Unicode
  scalar values remain literal. Reject lone surrogates. Do not normalize Unicode.
- Semantic unsigned integer quantities are decimal strings with grammar
  `0|[1-9][0-9]*`, bounded to the field's exact integer type. Small explicitly
  designated schema metadata are JSON integers. Boolean is not an integer.
- Reject duplicate decoded object keys at every level, including annotations.
  Do not parse first into a map that has already discarded duplicates.
- Typed-key sets use tuple `(kind, namespace, scope, local)`. Every textual
  component compares unsigned UTF-8 bytes; `scope` compares its ordered elements
  lexicographically, shorter equal-prefix vectors first. Lowercase wire kind
  spellings compare lexicographically, never by a Rust enum ordinal. Validate
  duplicate semantic identity before producing canonical output.
- Numeric finite sets sort by checked integer magnitude, never by digit strings.
  Arrays that carry semantic sequence retain their order. Neither universal
  array sorting nor universal array preservation implements the contract.
- Suggested reader ceilings: 8,388,608 input bytes; container nesting 64;
  200,000 JSON nodes; 16,384 immediate members/elements; 65,536 decoded UTF-8
  bytes per key or string. Limits are positive and caller-lowered only.
- Proposed accounting: each JSON value and each object key counts one node;
  keys do not add nesting. Root object nesting is 1. A nested container adds 1;
  a primitive value adds no container nesting. Scalar-root depth is 0, although
  an envelope reader rejects scalar roots by type. Immediate member count is
  object members, not twice that count for their keys and values.
- All budget parameters/counting, exact envelope field spelling, allowed profile
  and capability matrix, annotation number subset, projection paths and prefixes
  remain proposals until readiness freezes them. No vector with an empty body
  below establishes valid architecture/design/package semantics.

The parent supplied these proposed domain prefixes, including one LF (0A):
- arch: `nodal-fpga.arch.semantic.v1\n`; 28 bytes; hex `6e6f64616c2d667067612e617263682e73656d616e7469632e76310a`.
- design: `nodal-fpga.design.semantic.v1\n`; 30 bytes; hex `6e6f64616c2d667067612e64657369676e2e73656d616e7469632e76310a`.
- package: `nodal-fpga.package.build.v1\n`; 28 bytes; hex `6e6f64616c2d667067612e7061636b6167652e6275696c642e76310a`.

Semantic/build digest is SHA-256(prefix || canonical projection), with no extra
separator, length prefix or trailing JSON newline. Raw artifact digest is
SHA-256(exact supplied file bytes), without any prefix or canonicalization.
A digest detects byte corruption; it is not publisher authentication.

## 2. Literal canonical byte vectors

Every code block below contains one independently authored canonical JSON byte
vector. The Markdown block delimiter's newline is not part of the vector.
Files under `algorithm/` contain the exact bytes with no
newline. The hex is authoritative for invisible/non-ASCII characters.
Python hashlib and the separately invoked `sha256sum` agreed for every listed
raw digest. This checks the standard hashing computation only, not candidate
conformance. The script uses no production imports and no `json.dumps` output.

### C00

Empty canonical JSON object. Canonical-layer probe, not a valid envelope.

```json
{}
```

Length: 2 bytes. SHA-256: `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.

### C01

Object member order and insignificant input whitespace have no semantic meaning.

```json
{"a":"0","z":"1"}
```

Length: 17 bytes. SHA-256: `c1255c4aadeffe9ef4af62ee8d35ca666bbf423af4850de35feccaeaf626e54c`.

### C02

Unsigned UTF-8 key order is ASCII a, U+E000, U+10000. This differs from UTF-16 code-unit order.

```json
{"a":"ascii","":"bmp","𐀀":"supp"}
```

Length: 39 bytes. SHA-256: `8db4b888a63478ea8ab6c323190f2464cb6e272c75f4906461424f93c173b339`.

Exact hex: `7b2261223a226173636969222c22ee8080223a22626d70222c22f0908080223a2273757070227d`.

### C03

Quotation mark/backslash escaped; slash literal; short standard control escapes; other control escapes lowercase.

```json
{"text":"\"\\/\b\f\n\r\t\u0000\u0001\u000b\u001f"}
```

Length: 50 bytes. SHA-256: `ab1a990a6cbb7919e83e4636f3473b94c47ab28aef184efd9ecde08d32ae7cf1`.

Exact hex: `7b2274657874223a225c225c5c2f5c625c665c6e5c725c745c75303030305c75303030315c75303030625c7530303166227d`.

### C04

Other Unicode is literal UTF-8, including U+2028/U+2029; no Unicode normalization.

```json
{"text":"é é /    😀"}
```

Length: 31 bytes. SHA-256: `ca6364333aedaf3e7a9a2226d373fcdc09fb89a852698c20316974eee2281a39`.

Exact hex: `7b2274657874223a22c3a92065cc81202f20e280a8e280a920f09f9880227d`.

### C05

Precomposed U+00E9 is a different semantic name from C06.

```json
{"name":"é"}
```

Length: 13 bytes. SHA-256: `2f16b8477146a1b2ba7d6bb7cf7c9979c191cc2838a107dbf5f0d920b4cb3ba1`.

Exact hex: `7b226e616d65223a22c3a9227d`.

### C06

U+0065 U+0301 is retained exactly; distinct bytes and key identity from C05.

```json
{"name":"é"}
```

Length: 14 bytes. SHA-256: `6a547588c4055916e090ed61467326046dd52810679d03bfb84d862a7123522e`.

Exact hex: `7b226e616d65223a2265cc81227d`.

### C07

Exact unsigned values; 2^53+1 and 2^63 must not be rounded, truncated or represented through signed Long.

```json
{"values":["0","9007199254740991","9007199254740992","9007199254740993","9223372036854775807","9223372036854775808","18446744073709551615"]}
```

Length: 140 bytes. SHA-256: `505e2b47f9e771204c3e34ba198b08aaa46b24982f1edc6769db4feef5b4e2bd`.

### C08

A schema-declared numeric finite set is sorted by integer magnitude, not decimal-string lexicographic order.

```json
{"set":["0","2","10","9007199254740993","18446744073709551615"]}
```

Length: 64 bytes. SHA-256: `e35eee79f3d123742c3e9dc250b2f027fd914c60fa1d60c9ebcfbe2452fc3a25`.

### C09

A numeric partition set also sorts numerically; both values fit u32.

```json
{"partitions":["2","10"]}
```

Length: 25 bytes. SHA-256: `dec1a3cffdda1aadeab19d1e1d63b87057f60eb6e38a4648e2c05dba81339d78`.

### C10

Ordered pin vector; must stay I10 then I2.

```json
{"pins":[{"name":"I10"},{"name":"I2"}]}
```

Length: 39 bytes. SHA-256: `a674d223cbce8005981af7be6279ecf55f3d96008b20ac0764fce19bbf99f2ab`.

### C11

Changing ordered pin positions changes the semantic projection; must differ from C10.

```json
{"pins":[{"name":"I2"},{"name":"I10"}]}
```

Length: 39 bytes. SHA-256: `8c09098ccd2bf2f41e3a790cf24311928b564694f981717552a7bb721d61e08a`.

### C12

Three-input mux index 0 chooses east in this ordered list.

```json
{"sources":["east","local","west"],"value":"0"}
```

Length: 47 bytes. SHA-256: `8785fd608adf15f6fb94958e8f2885468d24b6d136a27e26229a1cc8457ef04c`.

### C13

Three-input mux index 0 chooses west; generic array sorting would hide the defect.

```json
{"sources":["west","local","east"],"value":"0"}
```

Length: 47 bytes. SHA-256: `eeab80873f6cb230288ac85682c0b73582a27aa77bfeb7b0a8311cbf0dc5c119`.

### C14

Slash and dot-dot are literal component data, not path separators or parent traversal.

```json
{"kind":"wire","local":"x/y","namespace":"demo","scope":["root",".."]}
```

Length: 70 bytes. SHA-256: `7400c638555fddc950cee539bba3950926fea236bf9a8b2b57099aaad18ddfef`.

### C15

Distinct structured identity from C14; joining components would incorrectly collide them.

```json
{"kind":"wire","local":"y","namespace":"demo","scope":["root","..","x"]}
```

Length: 72 bytes. SHA-256: `a19011b4b8f23b1a4b8681e7ea021289d494db00293a4d4ee9e6c10a5a19c091`.

### C16

Ordered scope vector changed; identity differs from C14.

```json
{"kind":"wire","local":"x/y","namespace":"demo","scope":["..","root"]}
```

Length: 70 bytes. SHA-256: `92c4355c5beaba7dc2157e7f8d1d39d370132071d0d77f7d633704191215b39e`.

### C17

Typed key set: kind UTF-8 order puts bel before wire regardless of local-name order.

```json
{"keys":[{"kind":"bel","local":"b","namespace":"n","scope":[]},{"kind":"wire","local":"a","namespace":"n","scope":[]}]}
```

Length: 119 bytes. SHA-256: `6140c30a89c000bfc1312c02bd5a6f9ab93ce817e5661623185d384f5b7596c7`.

### C18

Typed comparator compares namespace before scope/local after equal kind.

```json
{"keys":[{"kind":"wire","local":"z","namespace":"a","scope":["x"]},{"kind":"wire","local":"a","namespace":"b","scope":[]}]}
```

Length: 123 bytes. SHA-256: `45552bc2020d53241a069648de9e2f97105b8af9c04ea756a3bff89eda63229f`.

### C19

Scope vectors compare elementwise; shorter equal-prefix vector precedes the longer one, then compare local.

```json
{"keys":[{"kind":"wire","local":"z","namespace":"n","scope":[]},{"kind":"wire","local":"z","namespace":"n","scope":["a"]},{"kind":"wire","local":"a","namespace":"n","scope":["a","b"]}]}
```

Length: 185 bytes. SHA-256: `57791fbdbd4f82e6c531a61e657d5290978773b4ef3c236af7e1871da432b13d`.

### C20

Synthetic exact-path projection probe, not an accepted envelope; semantic source/name fields must be retained.

```json
{"annotations":{"example.org/note":"A"},"body":{"name":"tile","source":"semantic-source"},"provenance":{"display":"Tile A","source":"/machine/A.scala","timestamp":"2030-01-01T00:00:00Z"},"semantic_id":"self-A"}
```

Length: 210 bytes. SHA-256: `a85fd948fbe523c2b819ef10cb35ee0f1989fd4aa40d7fef40caa45cdf765352`.

### C21

Cold metadata/self-ID edit only in this synthetic exact-path fixture; same projection as C20.

```json
{"annotations":{"example.org/note":"B"},"body":{"name":"tile","source":"semantic-source"},"provenance":{"display":"Tile B","source":"/machine/B.scala","timestamp":"2031-01-01T00:00:00Z"},"semantic_id":"self-B"}
```

Length: 210 bytes. SHA-256: `611c68d4fa125b713c5c8f10777cb7b3427e57706b7f5dbc664a1fd3f2d2db01`.

### C22

Manually stated common semantic projection of C20/C21 after excluding exactly /annotations, /provenance, /semantic_id.

```json
{"body":{"name":"tile","source":"semantic-source"}}
```

Length: 51 bytes. SHA-256: `dee3a18d4446d71a5cb81fae2fa0a8a5145e14960a8957ad64244aee3dac95de`.

### C23

Changing semantic /body/source changes projection/hash; a global source-name exclusion is wrong.

```json
{"body":{"name":"tile","source":"other-source"}}
```

Length: 48 bytes. SHA-256: `85b9ba95bf004e97514bcbea03962e733948d5616dff03c39e28db50f7128ffd`.

### C24

Nested similarly named semantic_id is not the exact root self-ID. Retain if schema permits; otherwise reject as unknown, never silently strip.

```json
{"body":{"name":"tile","semantic_id":"nested-semantic-data","source":"semantic-source"}}
```

Length: 88 bytes. SHA-256: `19b8a10cb6077b89ec34b50186360fc5b764f7abde482d6fbf2b43a1d0e9f838`.

### C25

PROVISIONAL common-envelope canonicalization specimen only. Empty body/capabilities are not claimed to pass the final arch schema.

```json
{"annotations":{},"body":{},"format":"nodal-fpga.arch","optional_features":[],"profile":{"id":"structural-selection","revision":1},"required_features":[],"version":{"major":0,"minor":1}}
```

Length: 186 bytes. SHA-256: `db5337ba89cd6f639f75737b342d84aadbf4eaaf8c20d24c25b60605f5991de5`.

### C26

PROVISIONAL mapped-design kind specimen only, not a valid mapped-design body or final profile claim.

```json
{"annotations":{},"body":{},"format":"nodal-fpga.mapped-design","optional_features":[],"profile":{"id":"structural-selection","revision":1},"required_features":[],"version":{"major":0,"minor":1}}
```

Length: 195 bytes. SHA-256: `68a9b86ca591bc6451178ae93245a21cc283b9385d65ccd8cde044f9a7137590`.

### C27

PROVISIONAL package-manifest kind specimen only, not a valid manifest body.

```json
{"annotations":{},"body":{},"format":"nodal-fpga.package-manifest","optional_features":[],"profile":{"id":"structural-selection","revision":1},"required_features":[],"version":{"major":0,"minor":1}}
```

Length: 198 bytes. SHA-256: `c95c04a9918a5ea186c29d79492535af6d4eaf68214c275d568111f33ff749f0`.

### C28

Budget specimen: 7 raw bytes, 3 nodes (root + key + numeric value), 1 container depth, 1 member, 1 decoded key byte.

```json
{"a":0}
```

Length: 7 bytes. SHA-256: `45b619e97b5d9b029af4522e9ffb02fa99ff2bf226c82ee22a7cc10269a557e8`.

Exact hex: `7b2261223a307d`.

### C29

Budget specimen: 8 raw bytes, 3 nodes, 2 container depth, root has 1 member, child array 0 entries.

```json
{"a":[]}
```

Length: 8 bytes. SHA-256: `50e8660084976a10f0b3b9b3a6352d5881cbd219b5587a26224971a60ff2cc55`.

Exact hex: `7b2261223a5b5d7d`.

### C30

Budget specimen: 9 raw bytes, 4 nodes, 2 container depth, root 1 member, array 1 entry.

```json
{"a":[0]}
```

Length: 9 bytes. SHA-256: `1a21eb98104bbacebc876c8de01e474ad8d2520871aec7f74f0bbdf0eb21d6a1`.

Exact hex: `7b2261223a5b305d7d`.

### C31

Budget specimen: 13 raw bytes, 5 nodes, 1 container depth, 2 immediate members.

```json
{"a":0,"b":1}
```

Length: 13 bytes. SHA-256: `f4c1d8bd90d7ccd720aa5a69a67185fb9caf4f35926a4eacf53a86d0e70bdf88`.

Exact hex: `7b2261223a302c2262223a317d`.

### C32

Budget specimen: 11 raw bytes, 5 nodes, 2 container depth, 2 immediate array entries.

```json
{"a":[0,1]}
```

Length: 11 bytes. SHA-256: `93311353abbdb5a624f4b12e858dc80a66f67fccc077a627fd59a266052477c5`.

Exact hex: `7b2261223a5b302c315d7d`.

### C33

Budget specimen: 10 raw UTF-8 bytes, 3 nodes, 1 depth; decoded value has 2 bytes, not 1.

```json
{"a":"é"}
```

Length: 10 bytes. SHA-256: `b3a092a6af48807fa9482b2ee140105575daa26d5b24b3c0e60a7e2dee6683b1`.

Exact hex: `7b2261223a22c3a9227d`.

### C34

Diagnostic JSON Pointer specimen; value 0 is at /a~1b/~0x/0, escaping slash and tilde.

```json
{"a/b":{"~x":[0]}}
```

Length: 18 bytes. SHA-256: `f5ae9d2ee063b788929dcca1fc9f2b0e99e092af98583ec903c19ce5446b09aa`.

Exact hex: `7b22612f62223a7b227e78223a5b305d7d7d`.

### C35

Case-sensitive semantic name, distinct from C36.

```json
{"name":"A"}
```

Length: 12 bytes. SHA-256: `b2c9ee672db13673e38e84d0da1a6e765c88b3d0f1dc65244d3f736045aa5c84`.

### C36

Case-sensitive semantic name, distinct from C35.

```json
{"name":"a"}
```

Length: 12 bytes. SHA-256: `d9d719b27480b55cd4918020e7473e716ed3569c8adafe926cf9b10b4f8ef064`.

### C37

Required capabilities are a keyed set by ID; revisions are checked, not another opportunity to repeat an ID.

```json
{"required_features":[{"id":"alpha","revision":2},{"id":"beta","revision":1}]}
```

Length: 78 bytes. SHA-256: `f658118d43f1782fcab92713543c70c3753e2f65418123bd09be7464829a13a6`.

### C38

Tiny-allocation large-offset specimen: one-bit half-open range [MAX-1, MAX) in MAX-bit logical capacity.

```json
{"bits":"18446744073709551615","end":"18446744073709551615","start":"18446744073709551614","width":"1"}
```

Length: 103 bytes. SHA-256: `d9cd2a2e47afe9ce518c917470a25dbdb59c05fe7f6649c4917ead1f22638fba`.

## 3. Domain-separated independent digest vectors

These are algorithm/projection unit vectors, not accepted envelopes.
- C00, arch: `0238ad9bf1790e32d910f809a8a36c4a9ea59807fb42262532cf21950014c9ee`. Hash input length 30 bytes.
- C00, design: `7bce1890090e664bf1c46315f2e718cd2095277ab8c6ca4241e1a3779d9a8577`. Hash input length 32 bytes.
- C00, package: `1b55f082bda864631ace6cee73850ebfb76476ba1ec0841f69edeadea7b7367c`. Hash input length 30 bytes.
- C12, arch: `31c4405d5ad42a15e225040830aa386b1c4f1ed1e4f36fdc9be9d49adc6cb60a`. Hash input length 75 bytes.
- C12, design: `50ffee02f0659cbc8ec62b679a813183c5816a837d9c8a50b30244458ff75166`. Hash input length 77 bytes.
- C12, package: `64ddf37c9ff48fd688c981d686c8962b570ec9fa8e26b8055506ed3433828c8e`. Hash input length 75 bytes.
- C13, arch: `23c60dc2b48c53ad5748b932315b25e558811940e969a45c126da7d61e8d62e8`. Hash input length 75 bytes.
- C13, design: `4991c3d63885a623d8c0af298debbeb52c330c9a21b9fdbbdccc32fcdf9bba26`. Hash input length 77 bytes.
- C13, package: `c7f69de7f8d3a9e1d7006921d8858809458ef04b7331b9ced8a674818e5a00e5`. Hash input length 75 bytes.
- C22, arch: `49003ea8b2cd727ac670b7ae21099076f628eb5bd0bbaf195a12bab267d2e165`. Hash input length 79 bytes.
- C22, design: `32e3eb45956c1f9b886fef5b27802a14a0e06b5ab193128514bc55cf5c976cac`. Hash input length 81 bytes.
- C22, package: `e8a9e9fc0511cc6b28aefce511599f688484a67b2912205b22fe94b7db6f4ad7`. Hash input length 79 bytes.
- C23, arch: `d4a13e158a794b3d7739b551d84101088ec3edb339c801035b5bc0cec8664ec7`. Hash input length 76 bytes.
- C23, design: `dcc04ed19ee876507575786cd344384db913f7c792a45d7282508309927ba7f9`. Hash input length 78 bytes.
- C23, package: `4fd9be6a83e8857cec98db93c3816c678671f080c1cac894d1a6b47b4f27e460`. Hash input length 76 bytes.
- C24, arch: `31983ca656e198db348f4c1d82cfe88c91c072b2a34681749062ab054b717e67`. Hash input length 116 bytes.
- C24, design: `00f48db938f80725c5e5741628286784b9a94deec0264db805a9714411152641`. Hash input length 118 bytes.
- C24, package: `94cf4a8832f5aae2a5a271baaa59d722af6f6dbd01f3a181a1a1c4ca5aabd555`. Hash input length 116 bytes.

Same canonical projection under the three different prefixes must produce the
three separately listed digests. Prefix spelling/case/LF changes must not be
normalized. C20/C21 project manually to C22 only under this synthetic fixture's
explicit exclusion list. Their raw digests differ, but their arch semantic digest
is the listed arch digest of C22. C23 changes semantic `body.source`, so its
semantic digest differs. C24 prevents recursive removal by field name.

C25/C26/C27 are distinct canonical common-envelope shapes, but final required
capabilities and payloads must replace the empty specimens before any envelope
acceptance fixture is established. Unknown or mismatched kind must reject,
including when the filename suggests another kind. Do not infer a kind by suffix.

## 4. Exact artifact binding versus semantic identity

This independent two-file pair has the same decoded JSON and canonical form,
but different exact delivered bytes. It deliberately uses a generic object,
not a released architecture envelope. It tests raw byte binding before the
same relation is carried into the final full-package fixture.

- artifact-A: Python bytes literal `b'{"x":"0"}'`; length 9; hex `7b2278223a2230227d`; raw SHA-256 `ac34341052287fc96dc7e5a7b70f5dc0739ebef2f785cff27aa0cbdc8bf7bcac`.
  Exact canonical artifact-binding fragment: `{"artifact":{"bytes":"9","sha256":"ac34341052287fc96dc7e5a7b70f5dc0739ebef2f785cff27aa0cbdc8bf7bcac"}}`.
  Proposed package-domain SHA-256 of this fragment: `27c795533257fcfdd1c5a5c769ff05e2bb6a0afae7700083c2e1fb3d82b1ab23`.

- artifact-B: Python bytes literal `b'{ "x" : "0" }\n'`; length 14; hex `7b20227822203a20223022207d0a`; raw SHA-256 `6aaaa4b7831b61bbee075913eda9530616ee5fcee7c13b46955a8f8145a62fb8`.
  Exact canonical artifact-binding fragment: `{"artifact":{"bytes":"14","sha256":"6aaaa4b7831b61bbee075913eda9530616ee5fcee7c13b46955a8f8145a62fb8"}}`.
  Proposed package-domain SHA-256 of this fragment: `c7a226e9bbde30486ba0f028df3869ec97da0936428001132a6e0dacdf796928`.

Manually reasoned expectations:

1. Canonical JSON for both supplied files is exactly `{"x":"0"}` (9 bytes).
2. Supplying B against A's digest fails even though semantic JSON is equal.
3. Supplying A with a declared length of 8 or 10 fails the byte-length check.
4. A manifest binding B needs B's exact 14-byte length and digest, and therefore
   a different package build identity under the same package projection rule.
5. Architecture label/provenance-only edits may preserve semantic architecture
   identity while changing the artifact digest and package build identity.
6. Remove only the exact manifest self-build-ID path from its own build hash.
   Verify the declared ID against the computed result afterward. Do not omit
   target_build_id in a mapped-design body; it binds that design to the package.
7. A manifest must not hash a design artifact that already depends on that same
   manifest's build ID, creating a circular identity dependency.

## 5. Literal parsing and duplicate-key negative vectors

Below, `b'...'` is a Python bytes literal, not a JSON spelling. Hex specifies
bytes unambiguously. Every rejection must occur with its intended diagnostic,
input location and remedy; a panic, timeout or unrelated version failure is not
a passing negative case. Use these at the parser layer or insert only the marked
mutation into an otherwise valid final envelope, so schema failure cannot mask
parser behavior. Code spellings for exchange errors must be frozen later;
these are required outcome categories, not invented accepted diagnostic codes.

- D01: `b'{"a":0,"a":1}'`: duplicate decoded key `a` at root. Reject, never first/last wins.
- D02: `b'{"a":0,"\u0061":1}'`: escaped-equivalent duplicate decoded key `a`.
- D03: `b'{"x":{"a":0,"\u0061":1}}'`: nested duplicate at `/x/a`.
- D04: `b'{"annotations":{"example.org/a":{"x":0,"\u0078":1}}}'`: nested annotation duplicate. Unknown namespace does not skip its parser safety checks.
- D05: `b'{"/":0,"\/":1}'`: decoded slash keys duplicate. JSON Pointer reports `/~1`.
- D06: `b'{"~":0,"\u007e":1}'`: decoded tilde keys duplicate. Pointer reports `/~0`.
- D07: UTF-8 hex `7b22c3a9223a302c225c7530306539223a317d`: literal `é` and escaped `\u00e9` duplicate.
- D08: `b'{"\ud800\udc00":0,"\uD800\uDC00":1}'`: two encodings of U+10000 duplicate.
- D09: literal `é` and `e`+U+0301 keys are distinct, not duplicates; retaining both does not establish that a closed schema allows either key.
- D10: `b'{"body":{},"body":{}}'`: reject duplicate even if values agree.
- J01: hex `7b2278223a22c080227d`: overlong UTF-8 encoding of NUL. Reject UTF-8.
- J02: hex `7b2278223a22eda080227d`: encoded surrogate U+D800. Reject UTF-8.
- J03: hex `7b2278223a22f4908080227d`: scalar above U+10FFFF. Reject UTF-8.
- J04: hex `7b2278223a22f09f98227d`: truncated multibyte sequence. Reject UTF-8.
- J05: hex `7b2278223a2280227d`: stray continuation byte. Reject UTF-8.
- J06: `b'{"x":"\ud800"}'`: lone high-surrogate escape. Reject JSON string.
- J07: `b'{"x":"\udc00"}'`: lone low-surrogate escape. Reject JSON string.
- J08: `b'{"x":"\ud800A"}'`: high surrogate not followed by a low-surrogate escape. Reject.
- J09: `b'{"x":"\udc00\ud800"}'`: reversed surrogate order. Reject.
- J10: `b'{"x":"\ud800\udc00"}'`: valid escaped pair U+10000. Canonicalize to literal UTF-8 `f0908080` inside the string, not surrogate UTF-8 or two escapes.
- J11: `b'{"x":"\q"}'` and `b'{"x":"\u00G0"}'`: invalid JSON escapes. Reject.
- J12: hex `7b2278223a2200227d`: literal unescaped NUL in a string. Reject; canonical `\u0000` is valid.
- J13: hex `efbbbf7b7d`: leading UTF-8 BOM. Reject under the proposed input policy; do not silently strip it.
- J14: `b'{"x":'`, `b'{"x":"a}'`, `b'['`: truncated object/string/array. Reject.
- J15: `b'{}{}'` and `b'{} 0'`: trailing JSON document. Reject even though first value is valid.
- J16: `b'{"x":NaN}'`, `b'{"x":Infinity}'`, `b'{"x":-Infinity}'`: invalid/non-finite JSON values. Reject.
- J17: `b'{"x":01}'`, `b'{"x":+1}'`, `b'{"x":}'`, `b'{"x":0,}'`: malformed JSON. Reject.
- J18: byte `0a` after a complete object may be accepted as insignificant input whitespace if the final input policy allows it; canonical output always excludes it and raw digest always covers it. This must be distinct from BOM rejection.
- J19: literal U+FEFF *inside* a valid string is data, not an input BOM. No stripping.

## 6. Exact unsigned integers and Scala expectations

The wire grammar applies to the decoded string value; JSON escape spellings can
still represent its digits (`"\u0031"` decodes to `"1"`). If the intended policy
instead requires unescaped digit tokens, freeze that additional lexical rule
explicitly; the proposed semantic grammar alone does not do so.

Accept as u64 decimal strings exactly:

- `"0"` -> 0
- `"9007199254740991"` -> 2^53-1
- `"9007199254740992"` -> 2^53
- `"9007199254740993"` -> 2^53+1, distinct from 2^53
- `"9223372036854775807"` -> 2^63-1
- `"9223372036854775808"` -> 2^63, above signed Long.MAX_VALUE
- `"18446744073709551615"` -> 2^64-1

Reject u64 string values `""`, `"00"`, `"01"`, `"+1"`, `"-0"`, `"-1"`, `" 1"`,
`"1 "`, `"1.0"`, `"1e0"`, `"1E+0"`, `"0x1"`, Unicode fullwidth `"１"`, Arabic-Indic
`"١"`, a newline/tab within the decoded value, and `"18446744073709551616"`.
The last case is range overflow; the others violate the ASCII decimal grammar.
Reject JSON numbers `0`, `9007199254740993`, `18446744073709551615`, `1e0`, `-0`,
JSON booleans and null in semantic u64 positions because their *wire type* is
wrong, regardless of whether a number happens to fit. Metadata revision `1`
is valid where explicitly specified, while metadata string `"1"`, boolean `true`,
fraction `1.5` or unsupported revision `2` are separate failures.

Scala fixture-writer checks, without using Scala output to generate expectations:

- Construct inputs from `BigInt("18446744073709551615")` and
  `BigInt("9223372036854775808")`, bound `0 <= n && n <= (BigInt(1)<<64)-1`,
  then emit decimal strings. C07 is the independent literal output expectation.
- `BigInt("9007199254740993")` must emit `"9007199254740993"`, not the rounded
  Double value `"9007199254740992"`.
- `BigInt(-1)` and `BigInt(1)<<64` reject before output; no `.toLong` truncation,
  `.longValue` sign change, floating-point conversion or two's-complement rewrite.
- Scala `String` can contain unpaired UTF-16 surrogates. Detect/reject one rather
  than using a UTF-8 encoder that silently writes replacement characters.
- Scala default string ordering is UTF-16 code-unit ordering: explicitly compare
  UTF-8 bytes as unsigned integers for C02. JVM `Byte` is signed: compare `b & 255`.
- Writer-side bounds prevent emitting an invalid scalar. Reader tests still
  include hand-authored invalid strings so shared writer/reader checks cannot
  conceal the same bug.

FND-04 field-specific boundaries remain stronger than generic u64 parsing:

- `"4294967295"` fits a u32 dense ID or partition; `"4294967296"` does not.
  TableCount accepts 2^32 entries, but DenseId does not accept local index 2^32.
- Width accepts `"1"` through `"64"`; `"0"` and `"65"` fail width validation.
  Width 64 accepts value MAX; no shift-by-64 overflow.
- C38's range has length 1 and fits capacity MAX. `(start=MAX,length=1)`
  overflows the checked endpoint and must fail without huge allocation.
- MAX bytes converted to bits overflows. Bit offset 7 is not byte-aligned;
  exact conversion rejects rather than rounding to 0 or 1 byte.
- Source span `[2,4)` with declared bytes 4 is valid numeric provenance. `[2,5)`
  fails bounds. Serialized source identifiers are not opened as files.

## 7. Literal lowered-limit boundaries

These are parser-layer tests using intentionally tiny caller-lowered limits.
Keep all other limits ample so the intended bound is the only violated one.
An envelope-level harness should embed equivalent cases in a valid envelope
and add the known envelope overhead before choosing the lowered bound.

- Input bytes: C28 is literal `{"a":0}`, exactly 7 bytes: limit 7 reaches parsing;
  limit 6 fails input-byte budget. Literal `{"a":0} ` is 8 bytes: limit 7 fails
  before trimming whitespace, even though its JSON value equals C28.
- Byte count is actual streamed bytes, not file metadata or decoded character
  count. At limit N, read at most N+1 bytes to establish overflow. An adversarial
  reader whose initial metadata says 7 but supplies 8 must still fail at N=7.
- Node count: C28 has root object + key a + number 0 = 3. Limit 3 passes parser;
  limit 2 fails. C31 has root + 2 keys + 2 values = 5: limit 5 passes; 4 fails.
- Container nesting: C28 depth 1 passes limit 1. C29 depth 2 fails limit 1 and
  passes 2. C30 has an extra scalar node but remains container depth 2.
- Immediate object entries: C31 has 2 members: limit 2 passes; 1 fails. Keys and
  values are not counted separately as 4 collection entries.
- Immediate array entries: C32 has 2 elements: limit 2 passes; 1 fails. The root
  object has only 1 member, so the child array is the location of failure.
- Decoded string/key UTF-8 bytes: C33 value `é` is 2 bytes. Limit 2 passes; 1
  fails. ASCII spelling `{"a":"\u00e9"}` has 14 raw bytes, the same decoded
  2-byte value and the same canonical output C33. Do not count six escape bytes
  toward the decoded-string cap or one Unicode code point as one UTF-8 byte.
- Decoded object keys are also bounded: literal `{"é":0}` with string limit 1
  fails on the key (2 UTF-8 bytes), even though the number has no string value.
- Empty objects/arrays have no immediate entries but still count as value nodes.
  C00 depth/node count is 1, not 0. Positive lowered limit 1 accepts it at parser
  level. Configuration value 0 is invalid for every limit, even for empty input.
- Every ceiling plus one as a *configured limit* rejects before parsing: bytes
  8388609; nesting 65; nodes 200001; entries 16385; string bytes 65537.
  A caller cannot raise one ceiling merely by lowering another.

For full-ceiling tests, exact byte constructions can be produced outside the
candidate implementation using Python bytes repetition; these are specified
inputs rather than candidate-generated expected outputs:

- `b' ' * (8388608 - 2) + b'{}'` is exactly 8 MiB and contains valid JSON under
  the proposed whitespace-input policy; one additional leading space exceeds
  input-byte budget. Its envelope type/body may subsequently fail; only parser
  budget acceptance is asserted. No full success should be claimed for it.
- `b'[' * 64 + b'0' + b']' * 64` has depth 64 and 65 nodes; 65 bracket pairs
  has depth 65 and must fail the nesting budget.
- `b'[' + b'0,' * 16383 + b'0]'` has 16,384 immediate elements; one more
  element fails the collection limit while staying well under the byte cap.
- `b'{"x":"' + b'a' * 65536 + b'"}'` has a 65,536-byte decoded value and
  65,544 raw bytes; adding one `a` fails decoded-string length.
- Aggregate 200,000-node boundary: array with 12 child arrays of 16,383 zeros
  and one child array of 3,390 zeros. Nodes = 1 outer + 13 inner containers +
  12*16383 + 3390 = 200000. Add one zero to the final array for 200001. No
  array exceeds 16,384 entries, depth is 2, and bytes stay below 8 MiB.

Input-byte, nesting, node, collection, decoded-string and FND-04 semantic work
budgets are separate. Bounds failing during parse must not produce an accepted
partial model, incomplete canonical output or verified digest. A declared huge
numeric value does not authorize preallocation. Full-sized budget tests are
not substitutes for the tiny literal off-by-one vectors above.

## 8. Hand-explained semantic/order/identity corpus

These are independently stated semantic cases to instantiate after the wire
schema is frozen. The examples do not call the production resolver or normalize
an input to obtain the expected result.

### A. Repeated line and sparse boundary

One reusable `tile` template contains one owned BEL `cell` with ordered pins
I(input, width1), O(output, width1), and one independent two-bit configuration
owner `cfg`, domain range 0..2. Roots t0/t1/t2 instantiate that definition in
partition 0. Exactly two architecture edges exist: t0.cell.O -> t1.cell.I and
t1.cell.O -> t2.cell.I. Supply values t0.cfg=0, t1.cfg=1, t2.cfg=2.

Expected: one template definition, three distinct instance-qualified cell and
cfg identities, two links, no wraparound t2->t0, and independent settings. The
same template pointer/key is not an alias between t0.cfg and t1.cfg. Permute
resource-type/template/root/connection *keyed declaration* order: semantic digest
and canonical dump stay equal. Increase repetition to N: retained definitions
stay one; root count N and line-edge count N-1. No mandatory flattened graph
belongs in the wire format. Removing t1 without deleting the two incident links
fails missing references. Removing t1 and both edges leaves two roots and zero
edges, not an inferred t0->t2 bypass.

### B. Nested hierarchy and component identity

Wrapper W has children named `a/b` and `..`, both instances of leaf T. Root r
instantiates W. Qualified paths `["r","a/b"]` and `["r",".."]` are valid explicit
vectors; `["r","a","b"]` and `["r"]` do not become equivalent to them. A relative
reference path `[".."]` resolves the literal child named `..` if it exists. It
never resolves a parent. A child called `..` missing from a template is a missing
reference, never filesystem traversal. Source paths are cold data and no reader
opens them. Two template definitions sharing textual local names but differing
in scope/kind remain distinct typed keys where the model permits them.

### C. Asymmetric three-input mux

Use sources `[east.O, local.O, west.O]` and destination sink.I. Give selector
width2 and exact finite set `{0,1,2}`. With independent source values east=1,
local=0, west=0, selector0 chooses east (observed conceptual value1), selector1
chooses local (0), selector2 chooses west (0). A second assignment east=0,
local=1, west=0 distinguishes selector1, and a third assignment 0,0,1 distinguishes
selector2. These are hand expectations about selection ordering, not RTL runs.

Reverse sources without remapping selector: selector0 now chooses west, so
semantic hash changes (C12 versus C13). A universal array sorter is wrong even
if all three entries remain present. Set `{2,0,1}` canonicalizes numerically to
`{0,1,2}`. Duplicate `{0,1,1,2}` rejects before deduplication. Width2 `Any` admits
3 and is invalid for this three-source mux. `Range(0,2)` and `Set(0,1,2)` can
select the same numeric values, but FND-04 does not promise canonical equivalence
between domain forms; preserve the tagged representation and distinct hashes
unless a future explicit semantics-preserving rule is independently accepted.

### D. Sharing, aliases and complete selections

One template declares owned feature F and direct alias A with the same local
resource owner, storage, half-open range, width and domain. Equal simultaneous
F=1/A=1 is valid; F=0/A=1 conflicts. A write only through active alias A satisfies
the one storage class; requiring a redundant owner write would be wrong.
Distinct roots of the same template may set their respective storage classes
differently. Resource alias cannot own independent storage. Alias chain A->B->F,
partial overlap or differing width/domain fails the intended semantic category.
Two independent overlapping feature intervals reject even under mutually
exclusive guards. Adjacent `[0,1)` and `[1,2)` intervals do not overlap.

### E. Cycle and direction distinction

Two declared fixed edges A.O->B.I and B.O->A.I form a structurally legal routing
cycle under this profile if each canonical destination has only one driver.
Template A instantiating B which instantiates A is a recursive containment cycle
and rejects, even if not reached from any root. Do not substitute a global
acyclic graph check for the two different contracts. A source input pin, missing
pin, width mismatch or double driver rejects its own intended category.

### F. Exact identities and three envelope responsibilities

- Architecture envelope owns portable declarations and their semantic identity.
  It contains no customer route/congestion/placement-state authority.
- Mapped-design envelope binds an exact target package build ID, while retaining
  separate design identity/cells/nets/ports/constants as the frozen scope allows.
  Changing target_build_id changes design identity and wrong-target use rejects
  before interpreting package-local references. Equal family labels, counts or
  even architecture semantic hashes do not authorize reuse against another build.
- Package manifest binds arch semantic ID plus exact artifact digest and length,
  versions/features and every required dependency/binding identity. Changing
  configuration-map bit address, technology/macro binding, compiler/backend
  options, timing dataset or external pin map changes build identity.
- Foundation-only package explicitly marks unavailable compiler/device/physical
  views unbound. Supported inspection/saved-architecture consumption may succeed
  only within the final operation matrix. Programming, routing, physical timing
  or generated-fabric claims must reject unsupported/unbound prerequisites.
- No generated DeviceDB or RTL is required or fabricated for these tests.

### G. Enumerated semantic projection only

For every excluded provenance/display/annotation path in the final schema, pair
one fixture editing exactly that path with a semantic-preserving expectation.
For each neighboring semantic path, include a change that must alter the hash
or fail the closed schema. Do not erase any key named `name`, `label`, `source`,
`timestamp`, `provenance`, `annotations` or `semantic_id` recursively by spelling.
In particular, a resource named `source` and a portable local key `annotations`
are semantic data. Namespace-qualified arbitrary annotation values remain bounded
JSON data and cannot add accepted functional capabilities. Unknown root fields,
including `annotations2`, fail instead of being treated as annotation aliases.

Root optional annotation capabilities and annotations must have one explicitly
frozen projection rule. If both are purely cold and excluded, adding an unknown
optional namespace with its data preserves semantic identity and reports a
preservation diagnostic; raw bytes and artifact-bound package identity still
change. Unknown required capability never becomes optional by moving its name
into annotations. Missing required capabilities for a present construct fail.

### H. FND-04 exact key/provenance boundaries

- Empty Name rejects; ASCII `a` repeated 128 times is a valid component,
  while 129 bytes exceeds the constructor ceiling. Thirty-two literal emoji
  U+1F600 are exactly 128 UTF-8 bytes and fit; 33 are 132 bytes and fail.
- Scope vectors with 64 one-byte components can fit the scope-count ceiling;
  65 components fail even though the aggregate bytes remain small. The final
  architecture hierarchy may impose additional depth/derived-key limits.
- A key with namespace of 128 ASCII bytes, local of 128 bytes, and 30 scope
  components of 128 bytes has exactly 4096 data bytes (32*128). It fits the
  complete-key constructor ceiling. Add one additional one-byte scope component
  for 4097 bytes: it fails total bytes without violating component or scope-count
  ceilings. No invented slash delimiters contribute to this sum.
- A declaration key that fits independently can produce an over-limit qualified
  instance key after prefixing its instance path. The reader must use FND-04's
  derived-key checks, not merely accept each component separately.
- Source/display provenance limit is 1024 decoded UTF-8 bytes each, independently
  of the parser's 65536-byte string ceiling. Exactly 1024 may fit, 1025 fails.
  Schema-level semantic name limits can similarly reject a string that passed
  generic JSON parsing. This distinction must appear in the intended diagnostic.

## 9. Closed schema, compatibility and diagnostics mutations

After final valid base fixtures exist, retain an otherwise unchanged accepted
base for each mutation so that the intended failure is observable:

1. Unknown major, unknown minor, unknown profile ID, unsupported profile revision:
   fail exact compatibility, no guessed newer-minor compatibility or migration.
2. Unknown required capability/revision, duplicate ID, conflicting revisions,
   or missing required declaration for a used construct: fail before lowering.
3. Unknown optional annotation namespace: preserve its bounded parsed JSON data
   through supported data round trip and return a recorded diagnostic.
   Preservation need not preserve its original whitespace or escape spelling.
4. Unknown field at envelope, profile, version, feature declaration, body,
   resource key, nested declaration, reference, selection, binding and artifact
   descriptor: fail at that exact location. The annotations container's bounded
   arbitrary data does not make neighboring semantic fields open.
5. Required field missing, explicit null, string instead of object, object instead
   of array, number instead of decimal string: distinct malformed inputs, no
   silently supplied default. Nullable positions must be enumerated separately.
6. Duplicate typed declarations with same key and identical or differing payload:
   reject either case. Sorting is not permission to deduplicate.
7. Wrong artifact digest, wrong byte length, missing supplied artifact, wrong
   package build ID or wrong mapped target: fail before accepting artifact use.
8. Unknown enum or unsupported pass-switch/timing/reset/transport capability:
   explicit unsupported diagnostic, never reinterpret as a supported default.
9. Errors retain operation/stage, stable code, input JSON Pointer, declared
   profile/version, offending value, relevant semantic key and actionable remedy.
   C34 tests pointer escaping; `/a/b/~x/0` is not the correct pointer.
10. No accepted partial output is emitted on a late identity/hash failure after
    parsing and structural validation otherwise succeeded.

## 10. Readiness/implementation handoff and acceptance boundaries

Before moving any vector into a conformance corpus:

1. Freeze exact kind IDs, profiles/revisions, capabilities and kind-specific
   payloads, allowed nulls and annotation-number subset. These envelopes cannot
   be accepted merely because generic JSON parses.
2. Freeze hash domain bytes, exact projection paths including annotation feature
   declarations and self-ID location, typed collection keys and all ordering.
3. Freeze resource accounting/diagnostic identifiers; preserve literal tiny
   boundaries so off-by-one behavior is not inferred from the candidate reader.
4. Build final architecture/mapped/package known-good fixtures independently from
   their hand semantics above. Compute canonical bytes by review, then use only
   standard hashing tools to establish expected digest literals. If a fixture
   changes intentionally, review the expected change rather than regenerating
   goldens from the serializer under test.
5. Execute hand-input-to-Rust, pinned-Scala-to-Rust and supported round trips;
   test all negative categories with intended diagnostics. Writer/reader agreement
   alone does not satisfy FND-05.d/f.
6. Measure independent nesting/repetition/payload axes; report source, tools,
   corpus identities, elapsed time/size and failures separately from limits.
7. Qualify the real prebuilt reader and actual artifacts in the saved-runtime
   boundary, with no Scala/JVM/Rust build tooling/optional SDK. An environment
   capacity probe or empty PATH is not consumer isolation evidence.
8. Keep FND-05 open until every required descendant and FND-04 meet the governing
   acceptance/qualification/integration cadence. This preparation checks none.

Reproduction of raw digest computation for any listed exact vector:

```sh
sha256sum verify/fixtures/exchange/algorithm/C02.json
python3 -c 'from pathlib import Path; import hashlib; p=Path("verify/fixtures/exchange/algorithm/C02.json"); print(hashlib.sha256(p.read_bytes()).hexdigest())'
```

The original preparation source is `prepare_algorithm_vectors.py`. Its temporary
output defaults are historical authoring locations, not current run provenance.
It writes a temporary report and independent fixtures, uses Python standard
library plus sha256sum, verifies JSON syntax with stdlib json.loads without
serializing values, and never invokes a repository implementation.
