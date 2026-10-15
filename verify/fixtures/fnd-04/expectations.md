# Independently frozen FND-04 expectations

Authored 2026-10-15 before production implementation was inspected or present.
Author: independent fixture author. Repository edits and tests are not authorized yet.
Authority: docs/contracts/foundation.md, docs/contracts/nf-tiny.md, ADRs 0002/0003,
complete FND-04 checklist, assumption ledger ASM-0002/0003/0004/0008/0009/0010/0011,
and the accepted /tmp/fnd04-readiness-proposal.md profile.

## Hand-calculated topology and ownership

- LINE-1: template T with ordered pins I(input,1), O(output,1), one owned BEL and
  local configuration owner S; instance t0; physical owners [t0/S]; edges [].
- LINE-3: same single template instantiated as t0,t1,t2; physical owners
  [t0/S,t1/S,t2/S]; exactly [(t0/O,t1/I),(t1/O,t2/I)]. There is no wrap edge.
- LINE-3-PARTITION: partition 0 contains t0,t1; partition 1 contains t2.
  Same portable edges, exactly one local and one cross-partition edge.
- SPARSE: remove t1 and both incident edges; owners [t0/S,t2/S], edges [].
- SPARSE-BYPASS: the same sparse instance set with explicitly declared
  [(t0/O,t2/I)] has one edge. Removal alone must not create this edge.
- SPARSE-DANGLING: remove t1 without removing incident edges: MissingReference.
- REVERSED: t1/I as source or t0/O as destination: DirectionMismatch.
- WIDTH: a source width 2 connected to destination width 1: WidthMismatch.
- ROUTING-CYCLE: explicit t0/O->t1/I and t1/O->t0/I: structurally accepted.
- TEMPLATE-CYCLE: T instantiates T, or A instantiates B and B instantiates A:
  RecursiveTemplate. It must not be confused with a routing cycle.
- MUX-ORDER: ordered sources [A,B,C], select2 means C. select3 is InvalidValue.
  Swapping A and B changes selected source for select0 and select1.
- DOMAINS: t0=(Clock C0, Power P0, Configuration Q0),
  t1=(Clock C0, Power P1, Configuration Q0): accepted with independent sets.
  A clock key must never resolve as a power key merely because names match.

## Exact integer boundary expectations

- Local ID maximum 4294967295 is accepted; 4294967296 is rejected.
- A local table count 4294967296 is accepted without allocating a table;
  its highest valid index is 4294967295. count 4294967297 is rejected.
- u64 maximum is 18446744073709551615; max+0 accepts, max+1 rejects;
  (max-1)+1 accepts; (max/2)*2=18446744073709551614 accepts;
  9223372036854775808*2 rejects.
- Half-open interval [max-3,max) from start=max-3,length=3 accepts;
  start=max-3,length=4 rejects. [max,max) is a valid empty byte range.
- [4,6) and [6,8) are adjacent, not overlapping. [4,6)/[5,7) overlap;
  [4,8)/[5,6) are a contained overlap; equal nonempty ranges overlap.
- Feature widths 0 and 65 reject. Width1 maximum1 accepts, value2 rejects;
  width63 maximum9223372036854775807 accepts, value9223372036854775808 rejects;
  width64 maximum18446744073709551615 accepts. Never shift a u64 by64.
- Near-limit expected results are derived using independent u128 arithmetic.
  Tiny overlap expectations are derived from independently enumerated bit sets.
- Structured scope components ["a/b","c"] and ["a","b/c"] differ.
  Unicode/case components are exact, without implicit normalization.
- Same numeric local ID in builds A and B is a BuildMismatch; wrong partition
  is UnknownPartition; index>=count is LocalIdOutOfBounds; a cross-kind reference
  is either unrepresentable through typed API or KindMismatch when explicit.

## Sharing and modes

- Distinct storage owners t0/S and t1/S may hold different values.
- Independently owned features with equal, partial or contained nonempty slices
  of the same storage reject as UndeclaredOverlap, including exclusive guards.
- Direct aliases preserve significance and match owner scope, width, slice and
  value domain. Equal simultaneous bit requirements accept; differing shared
  bit requirements reject as AliasConflict.
- Mutually exclusive guards use distinct choices of the same group. Their
  differing values accept in separate valid selections. Distinct groups can
  coexist and must not be treated as exclusive.
- A supplied setting whose guard is not active rejects as InactiveFeature.
- Two choices selected in the same single-selection group: ModeConflict.
- Missing group/choice or undeclared asynchronous-reset mode: UnknownMode.
- A conjunction requesting different choices of one group: ContradictoryGuard.
- Dangling owner: MissingReference. Wrong owner instance: ScopeMismatch.
  Alias-to-alias: UnsupportedAliasChain. Cyclic alias graph: AliasCycle.
  Nonidentical width/slice/domain: AliasMismatch. Identity mapping only.
- Six independently enumerated activation bitsets over complete choices
  [(g0a,g1a),(g0a,g1b),(g0b,g1a),(g0b,g1b)] are:
  always=1111, g0a=0011, g0b=1100, g1a=0101, g1b=1010,
  g0a&&g1b=0010 (least significant bit is first choice).
- Exhaust all 6*6 guard pairs, 4 mode choices and 4*4 two-bit value pairs.
  Expected inactive iff either alias's bitset excludes the choice; otherwise
  expected conflict iff their individual per-bit requirements differ.
  This oracle neither calls production guard evaluation nor alias resolution.

## Negative/mutation detection

Each legal witness has a targeted single-defect mutation: dangling/reversed
endpoint, lost cross-partition edge, implicit sparse bypass, reused instance
storage identity, mux order swap, selector3, wrong build/partition/local bound,
undeclared overlap, ignored guard exclusion, false exclusion across groups,
conflicting shared write, inactive write, dangling/chained/cyclic alias,
wrong alias slice/domain/width, contradictory/unknown mode, template recursion,
unknown typed-domain membership, duplicate key and configured limit+1.
Tests require the intended stable category and source, not arbitrary failure.
Some topology/order mutations remain individually structurally valid; those are
caught by independent expected-graph/selected-source comparisons instead.

## Provenance, determinism, bounds and limits

Test source range validity, primary resource/source and related conflict sources,
operation stage, actual/expected bound and nonempty remedy. Keyed declaration
permutations must yield identical deterministically ordered diagnostics; ordered
pin and mux vectors must remain ordered. Source span units, limits, diagnostic
code spelling and omitted-setting policy await the API contract, not observed
production behavior. Scale axes are isolated: 1/16/256/4096 resources;
1/8/32 hierarchy depth and limit+1; 1/2/4 partitions; huge scalar offset with
only tiny allocations. Explicit public-API consumer and wrong-kind compile-fail
checks cover the reusable boundary. Every expected result is authored outside
production implementation and never refreshed from validator output.

No RTL, hardware simulation, behavioral primitive engine, DeviceDB, physical
allocator, serializer, Scala frontend, timing or PDK qualification is claimed.
This increment does not affect generated Verilog.
