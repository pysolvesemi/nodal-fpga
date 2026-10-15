# Independent focused semantic cases

These are separately authored inputs for required fields absent from the compact
primary fixture. No original golden is changed. Standard-library Python derives
new semantic IDs from explicitly traversed schema records, before candidate use.
Source: tests/exchange/prepare_semantic_cases.py; exact bytes: SHA256SUMS.

- guarded-alias: original two-instance alias fixture, plus operation group on each
  cell. F guard requires normal; alias guard requires alternate. The single
  storage class exists regardless of which name is active. t0 normal/F=1 and t1
  alternate/alias=2 is complete/valid; t1's owning F may be inactive. Supplying
  t0.alias while t0 mode normal is inactive; omitting either mode or the active
  class's value is missing_selection. Different mutually exclusive names may
  legally carry different values in separate selections. Repeated guard group
  declarations are invalid even when their mode is the same.
- resource-alias: original alias feature fixture plus resource cell-alias, a
  direct same-template alias of owned cell with the same kind and resource_type.
  It owns no independent storage/features. Two declarations refer to one resource
  owner per instance. Assigning storage ownership to the alias is invalid.
- range-domain: original primary architecture with route's set {0,1,2} replaced
  by the tagged inclusive range 0..2. The same three numeric settings are legal,
  but the preserved domain form yields a different semantic identity. No implicit
  set/range equivalence is part of the wire contract.
