# Independent exchange conformance

The expected full-envelope bytes and C00–C38 were fixed before candidate reader
or Scala writer answers. Their manifests, hand semantics and independent
SHA-256 derivation are under `verify/fixtures/exchange/`. Tests never import the
production canonicalizer, parser, projection or digest implementation to build
an expected answer. `support.py` constructs deliberate changed inputs with
Python's standard library; literal-primary crosschecks constrain that helper.

Run against an already-built public executable and actual Scala authoring output:

```sh
NF_EXCHANGE_BIN="$PWD/target/debug/nf-exchange" \
NF_EXCHANGE_SCALA_DIR=/path/to/actual-scala-output \
python3 -m unittest discover -s tests/exchange -v
```

Neither dependency is optional: a missing executable or Scala output fails
setup rather than silently skipping a required cross-language control. The
repository's designated build owner runs `nf check exchange` to coordinate the
locked/offline build and real Scala generation. Do not launch a competing Cargo
or sbt build from these black-box tests.

The additional public API suite is
`core/rust/exchange/tests/independent_contract.rs`. It reads the same immutable
fixtures through ordinary filesystem reads rooted at `CARGO_MANIFEST_DIR`; it
does not use forbidden Rust source-inclusion macros or compile fixture data into
production. Its counted readers/resolvers establish limits and no-reopen claims
that cannot be inferred from CLI exit status alone. Coordinate Cargo execution
with the build owner.

Coverage is separated by observable contract:

- `test_fixture_integrity.py`: original manifest identity, every literal byte,
  independent prefix hashes and hand-declared structure.
- `test_parser.py`: exact lexical/Unicode bytes, decoded duplicate keys, bounded
  input/containers/nodes/collections/strings, positive lower-only capabilities.
- `test_architecture.py`: exact projections/round trips, closed schema and required
  nullable fields, scalar conversions, preserved diagnostic categories/origins,
  ordered versus keyed collections, hierarchy/mux/alias/domain semantics.
- `test_package_design.py`: exact raw-artifact binding, all package states and
  unsupported operation boundaries, mapped-design target and terminal ownership,
  hostile diagnostic keys and tagged-field order.
- `test_envelopes.py`: every package/design object duplicate site, compatibility
  precedence and full-envelope depth overhead.
- `test_scala.py`: actual emitted Scala architecture equals the independent
  semantic projection; exact source/artifact/package/design binding is checked
  independently before Rust consumption.
- `test_scale.py`: separate root-count, template-depth, annotation/provenance
  payload-byte axes with deterministic repetitions and `EXCHANGE_SCALE` records.

`prepare_package_cases.py` and `prepare_semantic_cases.py` are transparent
independent fixture authoring scripts, not test setup or golden-refresh commands.
They must never be replaced by candidate-output capture. Historical preparation
scripts and unchanged full-golden sources retain their original output paths.

Negative tests require intended code and, where a field site is part of the
contract, exact RFC6901 pointer; core semantic tests require their intended
original FND-04 diagnostic code. CLI failures must have empty stdout. A random
failure, parser recursion error, stale self-ID or unrelated missing dependency is
not a passing control for another boundary.

This is bounded Foundation structural/software-package evidence. It does not
establish production scale, exact RSS/time guarantees, RTL emission, full
DeviceDB inspection, routing, timing or bitstream behavior. It does not replace
separate saved-runtime isolation, dependency review, full regressions, policy
qualification or final acceptance.

Verification is published as a source-bound summary in
[the corpus review](../../docs/implementation/fnd-05-corpus-review.md). Raw
execution logs and generated observation copies are not test inputs and are not
required in the repository. This does not make the actual prebuilt reader, Scala
authoring output, independent literal fixtures or their byte-integrity checks
optional. No test or golden was changed for this evidence-format conversion.
