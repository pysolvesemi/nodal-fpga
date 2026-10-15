# FND-05 saved-package runtime verification summary

Status: six development-local cases and four harness controls passed; independent
source/result review accepted the scoped dependency observation on 2026-10-15.
The tested candidate was dirty. This is not clean-head qualification, integration
or checklist closure; source changes require affected checks and review again.

## Identity and actual outcomes

The [development source vector](fnd-05-development-source.sha256) and
[independent review source vector](fnd-05-review-source.sha256) bind actual source
files, not merely the readiness HEAD. Reader SHA-256:
`2ccf48d3d54b005d23064a827394b227fb8e94891c2223d4051885ea25a2b920`.

| Executed case | Expected and observed outcome |
| --- | --- |
| package-summary | Exit 0; package build ID `19eb6b74ea1bb42f94736b4d149a249e1a55f70b03313a01d73df85f7b32bf14` |
| package-canonical | Exit 0; exact actual Scala bytes, SHA-256 `113bac1ab16704c955e2f220d183c1dc37776def00acb4bc7e73154806b10fb0` |
| architecture-canonical | Exit 0; exact actual Scala bytes, SHA-256 `17217b1c8f0bb606693aca0977b6edafb6bfc4feb58cf2fdae0a9a9e7ed263ca` |
| design-canonical | Exit 0; exact actual Scala bytes, SHA-256 `763cd4c9839b22cc766f3fbcf1cb3f2fcae829a3b55a8030cae00d79fc8cc3a2` |
| invalid-package | Exit 1; identity_mismatch at /body/build_id, empty stdout |
| x32-denied | Exit 159 / SIGSYS, empty stdout |

Four harness tests passed: actual filter/probe controls, loader-entry/library
rejection, permissive-filter rejection and missing-marker rejection. The Scala
input came from the actual 17-group writer run and passed 83 independent
conformance groups separately. Candidate output did not create expected goldens.

## What was observed and independently verified

- The [launcher](../../tools/saved_runtime.py) admitted only the prebuilt reader,
  reviewed probe, exact ELF libraries and copied JSON input files. The minimal
  read-only root had nine regular files with verified hashes, sizes and modes,
  no symlinks, and four non-executable JSON inputs.
- The actual reader executable and copied binary were matched by hash and live
  identity. Its mappings contained only itself, libc, libgcc and the ELF loader.
  Environment was restricted to four controlled entries; descriptors were only
  stdin/stdout/stderr. The process was single-threaded with NoNewPrivs and seccomp
  active, no capabilities or tracer, and the inspected mount boundary was correct.
- Source checkout, toolchains, package caches, Scala/JDK and optional application
  SDKs were absent from the runtime root. The launcher and observation tools were
  outside that consumer root. The build and authoring profiles remain separate.
- The [filter](../../tools/runtime/socket_filter.c),
  [verifier](../../tools/runtime_filter.py) and
  [probe](../../tools/runtime/runtime_probe.c) cover architecture/x32 checks and
  actual socket, io_uring and fork/vfork/clone/clone3 denial controls.
- A blocked output pipe enables observation of the actual reader. Stable process
  ancestry, executable identity and before/after observations fail closed on
  races, missing snapshots or timeout. Parsed loader initialization/entry records
  bind every consumer to the admitted libraries. Full canonical bytes must match
  actual Scala output after observation, not just a successful probe.
- The independent reviewer rehashed the root, source/filter, outputs and snapshots,
  checked modes/file set, reader identity, maps/environment/descriptors/status and
  mounts, and verified all canonical comparisons and the negative case.

## Observation limits and reproduction

Ptrace was unavailable; a separate executor setup failed before tracing. Neither
was a security bypass or successful runtime proof. Network-namespace setup was
also unavailable. The explicitly selected loader-procfs route does not enumerate
all file syscalls or same-process executable replacement attempts. It establishes
no network namespace and is not a hostile-code security certification.

```sh
./nf saved-runtime --binary target/debug/nf-exchange \
  --scala-artifacts ACTUAL_SCALA_DIRECTORY --output FRESH_LOCAL_OUTPUT \
  --observation-profile loader-procfs
python3 -m unittest discover -s tests/runtime -v
```

Keep fresh actual inputs and all required checks; partial untraced observations
receive no qualification credit. The machine report deliberately leaves
qualification_complete false because execution cannot replace review/closure.

Original execution records and snapshots were preserved locally outside the
candidate with verified hashes. This repository publishes the summary and
source bindings, not raw logs, machine snapshots or private archive locations.
Original machine report SHA-256:
`da8448fa9a2b5230be1e86f59cd529ab4bc6d05db67d8c45665f766097842431`.
Any reader, writer, launcher, filter, library or qualification-contract change
requires rebinding the affected evidence. See the [checkpoint](fnd-05-checkpoint.md)
for pending final clean-commit and integration gates.

This increment does not affect generated Verilog.
