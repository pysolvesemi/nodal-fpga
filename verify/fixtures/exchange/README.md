# Independent FND-05 exchange corpus

This corpus was authored before production reader/writer output was available.
It is not generated from `nf-exchange`, Scala fixture output, or FND-04 lowering.
The contract is [FND-05 readiness](../../../docs/implementation/fnd-05-readiness.md).
All completion/qualification status belongs to the Foundation roadmap and actual
execution evidence, not the presence of these files.

- `algorithm/`: original C00–C38 literal parser/canonicalization probes and exact
  domain-hash inputs, retained byte-for-byte. C25–C27 are intentionally incomplete
  envelope examples and must not pass as valid envelopes.
- `preparation.md`: original independently authored rules, literal hashes,
  malformed/limit cases and hand expectations. It retains its historical
  preparatory status; explanatory source paths are repository-relative.
- `prepare_algorithm_vectors.py`: original independent preparation source, retained
  for provenance. Historical temporary output defaults are authored script
  constants, not private run metadata. Do not run it to update
  expected answers from candidate output.
- `goldens/`: complete valid architecture, exact-artifact-bound software package,
  target-bound mapped design and focused variants. `EXPECTED.md` freezes hand
  semantics; `IDENTITIES.md` records exact independently calculated identities.
  `author_goldens.py` is original independent literal assembly source. It does not
  sort arbitrary input or import production helpers. Checked-in byte files remain
  the conformance authority and must not be regenerated to hide a mismatch.
- Each directory's `SHA256SUMS` binds its immutable byte fixtures. The original
  full-golden manifest has SHA-256
  `acfd21c1b776a3565796fad15186db4b0b0993585b1c480bc790841b398ff4b9`.

The hand-authored package truthfully declares authoring unbound/not-supplied. The
separate actual Scala demonstration must bind its actual reviewed writer source
identity, pinned Scala identity options and actual emitted artifact bytes.

Public black-box tests live under `tests/exchange/`. They use literal expected
bytes and standard-library hashing, never candidate output to derive expected
answers. Dynamic mutations are test inputs, not replacements for these goldens.

This increment does not affect generated Verilog.

Raw preparation/execution logs and generated observation copies are not published
in this corpus. They were preserved locally outside the candidate. The four
literal-artifact manifests contain only functional expected inputs and outputs;
their exact bytes are unchanged. See the
[conformance summary](../../../docs/implementation/fnd-05-corpus-review.md) for
actual development results, source binding and pending acceptance gates.
