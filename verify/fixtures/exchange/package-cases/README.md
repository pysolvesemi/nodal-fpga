# Independently signed package preflight cases

These additional test inputs were authored from the frozen package using Python
standard-library JSON/hashlib, before candidate execution. They do not replace
or regenerate the complete golden corpus. Source:
`tests/exchange/prepare_package_cases.py`. SHA256SUMS binds data bytes.

- same-digest: library and architecture use the exact same digest/length. One
  unique artifact, one resolver call/read. Semantic artifact roles remain distinct.
- conflicting-length: the library repeats the architecture digest with length
  6625 instead of 6624. Reject artifact_length before any resolver call.
- two-artifacts: one architecture plus one opaque leaf. Exactly two unique digests;
  sum declared length = 6624 plus opaque-leaf.bin length. An artifacts limit1 or
  aggregate limit one below that sum rejects limit before any resolver call.
- opaque-reused: the opaque leaf appears as both library and configuration_map.
  Still exactly two unique artifacts total. Only the architecture is interpreted;
  the leaf's nested-manifest/design/URL-looking text causes no extra resolution,
  execution, network request or operation capability.
- oversized-declared: one library advertises 8388609 bytes, above the per-artifact
  ceiling. Reject limit before any resolver call or declared-size allocation.

All manifest self-IDs are independently recomputed correctly so that a bad self-ID
cannot mask the intended descriptor preflight. Changing self-ID to all zeros is
an independent identity_mismatch case with zero resolver calls.
