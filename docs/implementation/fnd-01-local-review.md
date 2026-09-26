# FND-01 local implementation review

This record covers preparation of the first implementation candidate after
readiness commit `ef737ff19072a0eea6887ba524d3cdbee8779c11`. The exact published
candidate is recorded in PR #1. These observations are not remote qualification
or accepted increment closure.

- `python3 nf check contracts`: 20 unittest cases passed, including independent
  mutation controls for forbidden application/device/adapter dependencies,
  renamed/optional target dependencies, dev dependencies, build scripts, source
  includes/native links, symlink escapes, publishing/unsafe-policy violations,
  tool pin drift, corrupted/offline downloads and source-identity mismatch.
- Documentation links and whitespace outside fenced examples passed. Original
  Foundation obligations/states and all other tracks were preserved.
- The workflow YAML was parsed locally: three selected execution lanes and one
  aggregate, read-only content permission, dev-only automatic path filters and
  explicit dispatch. This does not prove registration or execution on GitHub.
- `git diff --check` passed for the prepared source.

## Actual Scala probe

The available environment provides Ubuntu OpenJDK 17.0.20. The pinned sbt
1.12.11 launcher was downloaded from its Maven publisher location and independently
hashed as `b4c0c55d68f11b1510d884641cb1b1456191dac40ddc958bf86c825adc344e16`.
The first launch failed because this runtime disallows the IPC socket sbt tries
to open. Inspection of the pinned sbt source showed its supported
`sbt.server.forcestart` property continues without that boot socket on failure.
The local probe used that property with `sbt.server.autostart=false`; no socket
restriction was changed.

Executed launcher tasks: `scalafmtAll scalafmtSbt clean compile run`. Pinned
scalafmt formatted the sources/build, Scala 3.3.8 compiled the one source, and
the actual executable printed:

```text
nodal-fpga/bootstrap/1
frontend=scala3
profile=build-only
```

This is a successful noncanonical Scala-source check, not evidence for the
Temurin 21 profile, clean repeated builds or a generated architecture/HDL artifact.
The canonical CI must still run its formatter checks, setup, compilation and
repeats on the exact published source. Rust is absent locally and its distribution
probe timed out, so no Rust compilation is claimed here.

## Review limits and remaining gates

The core crate contains no third-party dependencies or hardware implementation.
The boundary guard fails closed on new dependencies/members until their owner
explicitly reviews the policy. Its conservative lexical checks are not a proof
against arbitrary malicious code; Cargo metadata and actual isolated builds are
also required. The selected workflow has no candidate-source write permission.
No optimization or wider framework is needed for the tiny bootstrap witness.

Keep exact-candidate targeted/full qualification, independent evidence inspection,
review, verified integration and all closure obligations open. Timing/scale claims
await the actual clean-repeat lanes. All roadmap checkboxes remain unchecked.

This increment does not affect generated Verilog.
