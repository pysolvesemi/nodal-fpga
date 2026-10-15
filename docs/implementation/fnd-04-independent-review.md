# FND-04 independent core architecture review

Date: 2026-10-15 UTC. Review scope: the local `structural-selection` implementation,
public consumers, independent fixtures and ownership boundary identified below.

**Disposition: no unresolved blocking finding in this reviewed local scope.**
The findings below were repaired by the implementation author and covered by
independent public-API tests or reviewer probes before this disposition. This is
a content-hash-bound source review and local execution result, not a clean-commit,
remote CI, merge or accepted-increment receipt. FND-04 completion and the applicable
integration/evidence gates remain with the integration coordinator.

The checkout's existing HEAD was `6d3c429950fc401ef351defb3efa871a994db0b7`, tree
`0bae7e14e0e32620f73e8e56089a12e7ec9fa9e1`; the reviewed implementation was an
uncommitted addition to that readiness checkpoint. Those Git identities therefore
are **not** claimed as the implementation source. The SHA-256 manifest below
identifies the actual reviewed bytes. It was captured before the final rerun and
rechecked unchanged afterwards. This report is the reviewer's only tracked
deliverable; ignored raw captures were also preserved at the coordinator's request. Production, tests and the oracle
were reviewed read-only.

## Basis and independence

Read `AGENTS.md`, roadmap index/progress and every FND-04 descendant, architecture,
verification/early-baseline policy, ADRs 0001–0003, Foundation/nf-tiny contracts,
assumption interactions, the [readiness audit](fnd-04-readiness.md), public API
contract and independent fixtures. No acceptance item was deleted or weakened.
The implementation preserves the readiness profile; DB, CFG, RTL and FND-05/06
retain their separate responsibilities.

The independently authored expectations in
`verify/fixtures/fnd-04/expectations.md` retain preparation-time SHA-256
`b33d80f70272393474ec8583c479acdd488de39d43ee039ca2ab94a0aebd1581`.
They precede production implementation. Tests use public APIs, literal graph and
mode expectations, wider integer arithmetic, tiny bitsets and generated
single-defect inputs. No production resolver/guard/alias helper computes expected
answers. Review-driven regressions add diagnostic/boundary cases without changing
that original legality oracle. The reviewer also built the separate consumer in
Appendix B, outside the repository and the production test modules.

## Findings and disposition

All rows are repaired. Diagnostic expectations refer to stable `Code`/`Stage`
values and structured keys/origins, not merely an arbitrary error.

| Finding / minimal witness | Required result and verified repair |
| --- | --- |
| A local connection and an architecture-level connection, or parent/child connections, drive the same qualified input; an alias can name the same destination. | `Connection`, retaining conflict origins. A bounded streamed instance traversal now canonicalizes destination ownership across scopes. `qualified_destinations_reject_drivers_from_different_containment_scopes` covers local/top, parent/child and alias cases. |
| A definition key `a / TTT / r` has individually short components but five total bytes; `max_key_bytes=4` originally passed. A short definition can also acquire an overlong instance-qualified name. | Singleton `Limit`, never a valid witness. Complete definition and instance keys are bounded for resources, fields, storage, groups and connections. Lowered-key public tests include the long field name; the external consumer repeats the five-byte case. |
| A final audit found an architecture-level connection with namespace 11 bytes and name 25 bytes accepted under `max_key_bytes=30`, despite the complete empty-scope Pip key being 36 bytes. | Singleton Architecture `Limit`; exact 36 accepts, 35/30 reject. Canonical top-level preflight now constructs and validates that Pip key; duplicate diagnostics expose the same key. An unchanged independent pre-repair consumer changed from the expected red witness to green. The permanent regression checks exact bound, one-byte overflow and declaration permutations. |
| Duplicate domain membership or contradictory guard entries reverse their primary origin when their vector is reversed; a duplicate global Domain omitted the other declaration's origin. | Identical complete diagnostic vectors under permutation, with `Duplicate`/`Guard` and both origins. Canonical reference/guard traversal and related origins repair this; the independent suite checks both declaration and membership duplicates. |
| An unknown selected field was reported at architecture stage with a template-definition identity. | `Missing`, `Stage::Selection`, full instance scope and requested field name. `unknown_selected_feature_reports_selection_stage_and_instance_identity` and the consumer check this boundary. |
| `Set([0,1])` versus `Set([1,0])` changed invalid-value diagnostic text. | Identical `Value` diagnostics and canonical expected set text; stored declarations remain unchanged. Public set-permutation tests and consumer agree. |
| Competing path/component/collection/work caps could select different limit diagnostics after a keyed permutation; nested derived comparisons could inspect oversized vectors before admission. | Singleton deterministic `Limit`. An allocation-free uniform shape pass bounds nested vectors and reference paths before sorting; canonical preflight and a uniform selection path-length precheck follow. Independent competing-limit and oversized-path regressions pass. |
| With type modes `[x,y]`, group modes `[x,z1,z2]`, diagnostics cap 1 and work cap 114, reversal changed `Limit(work)` into `Limit(diagnostics)`. Separately, groups `g0:[x,x]`, `g1:[x,y]` at work cap 101 had the inverse problem. | Complete diagnostic equality. Canonical traversal now covers semantic mode validation and Context's per-group duplicate-mode check. External sweeps over every work cap 1–1,999 pass both permutations; independent permanent budget-sweep regressions cover this interaction. These exact thresholds describe the minimal external fixture before repair, not a promised accounting ABI. |
| Owner-plus-alias membership in one mode group changed the error's resource key when membership order was reversed. | Stable `Mode` with identical complete diagnostics. Group resource traversal is canonical; external permutation probe passes. Names-only derived-key loops and PIP collision traversal were also made canonical. |
| A containment cycle A→B→A plus A→an earlier-sorting acyclic leaf could blame the leaf. | `TemplateCycle` naming a genuine cycle member, primary back-edge Instance provenance and related source/target templates. Iterative DFS constructs an actual back-edge witness; the dedicated test checks literal distinct origins. |
| A `ResourceKind::Field` resource and feature could share the same local typed key. The analogous PIP resource/connection collision also needed rejection. Storage/group diagnostics used misleading containing-template or field identities. | `Duplicate` with the actual Field/Pip key and both origins; nominal Storage/ModeGroup keys for those categories. Dedicated collision and nominal-identity tests pass, including the types marker test. |
| Guard activation and repeated alias/mux finite-domain scans were not consistently charged before work. | Guards are charged before activation, both alias finite sets and mux sets are charged, and explicit pin/mode/domain/path scans are budgeted. Compact high-fanout input fails closed at the work cap. The accounting remains conservative logical work, not exact machine cost. |

The final traversal audit distinguishes keyed collections from semantic sequences:
canonicalization is transient and does not reorder stored declarations, interface
pins or mux source order. Remaining raw shape/counting traversals have uniform
failure/fixed-charge behavior; raw semantic pin/source sequences intentionally
retain their meaning. Review did not add a normalization or alternate model.

## Architecture and public boundary conclusions

- Private modules have coherent responsibilities: `bounds` owns admission and
  accounting; `references` owns borrowed indexes, scoped resolution and diagnostic
  identity; `declarations` owns hierarchy, modes, storage and alias/overlap rules;
  `connections` owns endpoint/mux legality and cross-scope destination ownership;
  `selection` owns transient choices, writes and completeness. They share the
  borrowed declaration model and report/context machinery. This separation avoids
  parallel models and keeps selection state out of definitions; no generic
  optimization framework or further module abstraction is warranted here.
- `nf-types` has no dependencies. `nf-arch-ir` has exactly one normal path
  dependency, `nf-types`. The existing bootstrap remains separate. No concrete
  device, primitive library, Scala, adapter, external crate or separately installed
  LLVM/MLIR/CIRCT SDK enters this default core DAG. Both new crates forbid unsafe.
- Ownership registry schema 2 identifies exact package name/path/version and
  dependency kind/target/alias/path. Static manifest/source policy and actual
  locked/offline Cargo metadata agree: three packages, one internal edge, zero
  external dependencies. Negative controls retain renamed/dev/build/target and
  registry rejection, canonical paths/symlinks, graph cycles, source/native/build
  hooks, workspace configuration, publishing and unsafe policy. This is a bounded
  repository guard plus compiler enforcement, not a general Rust security parser.
- ArchIR resource tables intentionally require unique local names even across
  resource kinds; references separately verify their declared kind.
- Nominal sealed markers separate resource categories. Portable identity is exact
  kind/namespace/ordered-scope/local name; provenance and display labels do not
  enter it. Whole-declaration derived equality/order remains structural, including
  provenance and stored vector order. It is not semantic canonicalization.
- Dense IDs, exact BuildId, partition context, table count and portable keys remain
  distinct. `u32::MAX` is a valid ID with a `2^32` populated count. Resolution checks
  build, partition, kind and range before host-index conversion. Explicit total
  one-to-one correspondence cannot be inferred from names/counts. Huge declared
  counts with tiny mappings reject without iterating over the numeric count.
- Bit/byte counts and offsets are separate checked `u64` quantities. Half-open
  ranges handle adjacency/empty ranges and overflow; width 64 avoids shifting by
  64. Feature width does not cap storage offset. No pointer casts, unchecked file
  layout, Rust enum discriminant or memory image is promised as a portable ABI.
  Only this x86_64 host was executed; cross-target execution was not performed.
- Provenance remains on declarations/references and structured diagnostics. Source
  spans validate numeric half-open bounds against a caller-declared byte length;
  without source text they do not verify UTF-8 slicing boundaries or source-file
  existence. The API contract explicitly describes this limit.
- The validated witness immutably borrows the original model. Selections are
  separate transient inputs. Definitions remain reusable; full instance paths
  distinguish state ownership. Child-only explicit resolution, recursion versus
  routing-cycle distinction, endpoint direction/width and mux source order are
  preserved. No implicit sparse bypass or hidden topology rewrite is added.
- Direct resource aliases and feature owner classes retain local scope and exact
  owner/storage/slice/width/domain requirements. Exclusivity alone never permits
  undeclared overlap. Active alias-only writes, inactive owners with active aliases,
  equal co-active writes and independent instance values behave as specified.
  Storage objects remain separate even when offsets and resource owners agree.
- Clock/power/configuration/placement/routing memberships remain independent typed
  references. Their existence/kind checks do not imply containment, electrical
  isolation, CDC, reconfiguration, timing or placement/routing crossing safety.

## Complexity, boundedness and observations

Declarations remain shared and borrowed through ordered indexes. Index construction
and sorted interval sweeps scale with supplied declaration counts, with tree/sort
comparison factors. Explicit references walk bounded path components. Independent
feature ownership uses per-storage interval sweeps; there is no bitmap sized by a
`u64` capacity/offset. Correspondence uses supplied-entry indexes, not dense-count
materialization; its API has no `ValidationLimits`, so readers must separately
bound their supplied collections.

Instance checking is streamed, not free of instance-count cost. It retains bounded
pending paths and destination ownership constraints rather than flattened resources
or a copied connectivity model. Occurrences and pending stack are capped separately
by `max_declarations`; key/depth/work checks apply while traversing. Selection
composite-key lookups also clone bounded instance paths for guards, settings and
group completeness. This is bounded transient allocation, distinct from copying
the model; it is not a zero-allocation hot path, and those host costs are not
individually metered. No additional optimization was required for these fixtures.
Selection starts a separate budget and checks every instantiated group/active owner class. Reusing a
small template DAG does not promise admission of its exponential expansion.

Default ceilings are 100,000 declarations, 200,000 references, 16,384 entries per
collection, depth 64, component/key bytes 128/4,096, provenance bytes 1,024,
128 diagnostics and 1,000,000 charged work units. Lower positive capabilities are
supported; zero/raised ceilings reject. Shape entries/path lengths are charged to
work before canonical comparison. Work counts collection/name/resolution/scanning
operations conservatively; tree comparisons, allocations and host runtime overhead
are not instruction-by-instruction metered. Input byte limits, process quotas and
reader admission remain caller concerns. No hard real-time or exact RSS bound is
claimed. Diagnostic-cap exhaustion rejects with a singleton limit, never a partial
successful model.

Independent fixture counts checked in this review:

- 121 boundary arithmetic pairs using a `u128` oracle; widths 1–64.
- 81 tiny intervals and all 6,561 pairs, plus huge scalar bounds.
- 2,304 sharing selections: 172 accepted, 516 conflicts, 1,616 inactive writes;
  64 independently owned overlap pairs and 128 seeded single-defect mutations.
- Isolated scale axes: 1/16/256/4,096 repeated instances; depths 1/8/32/64 and
  rejected 65; partitions 1/2/4; compact high fanout and huge logical offsets.
  Seed: `0xF0041D3E5EED`. An additional 6,000 permanent comparisons sweep work
  caps 1–2,000 for mode-name, mode-group and owner/alias membership permutations.
  These are finite local fixtures, not production capacity.

The final all-target run observed the 4,096-instance fixture retaining one template,
with shallow instance-vector capacity 819,200 bytes and name payload 31,658 bytes.
These two byte counts omit nested structures, indexes and allocator overhead.
The test's independently checked validation counters and elapsed observations are
recorded below; timings are from one shared debug-build runner, not benchmarks.

```text
FND04-SCALE selection_instances=4096 elapsed_ns=76943445
FND04-SCALE instances=4096 templates=1 shallow_instance_capacity_bytes=819200 instance_name_payload_bytes=31658 elapsed_ns=23409926 stats=ValidationStats { declarations: 4106, references: 4099, work: 209839, hierarchy_depth: 1 }
FND04-SCALE hierarchy_depth=64 templates=64 elapsed_ns=2079103 stats=ValidationStats { declarations: 137, references: 67, work: 36886, hierarchy_depth: 64 }
FND04-SCALE partitions=1 links=7 cross_partition_links=0 elapsed_ns=214263
FND04-SCALE partitions=2 links=7 cross_partition_links=7 elapsed_ns=236166
FND04-SCALE partitions=4 links=7 cross_partition_links=7 elapsed_ns=205359
```

The external consumer declares 11 templates and 320 child instance declarations,
336 accounted declaration entries in total. Its ten fanout-32 levels would have
1,125,899,906,842,624 leaves and 1,162,219,258,676,257 total occurrences if expanded.
It instead rejects with exactly `Code::Limit`, `Stage::Architecture`, message
`validation capability exceeded: work`, expected `1000000`. Final observation:
44 ms inside validation; 0.049886967001 s for the whole prebuilt consumer process;
peak RSS 10,496 KiB. Peak RSS covers the entire prebuilt consumer process, not just
this validator call; compilation was excluded. No hypothetical occurrence was counted
as an actually materialized or validated resource.

## Final local commands and results

Runner: Linux 6.18.44 x86_64, glibc 2.41; Python 3.12.14;
`rustc 1.98.1 (48a229cea 2026-09-01)`;
`cargo 1.98.1 (797e8a9bc 2026-08-05)`.
Commands used the existing isolated toolchain environment and `TZ=UTC`.

```sh
source .cache/toolchains/env.sh
export TZ=UTC
cargo fmt --all -- --check
cargo clippy --locked --offline --workspace --all-targets -- -D warnings
cargo test --locked --offline --workspace --all-targets -- --nocapture
cargo test --locked --offline --workspace --doc
python3 -m unittest discover -s tests/bootstrap -p test_contracts.py
cargo metadata --locked --offline --format-version 1 > /tmp/fnd04-review/metadata.json
python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from check_boundaries import check_metadata
check_metadata(Path('.').resolve(), json.loads(Path('/tmp/fnd04-review/metadata.json').read_text()))
PY
cargo run --quiet --locked --offline -p nf-arch-ir --example model
```

All passed: 40 ArchIR integration tests, 8 independent types tests, one types
nominal-category unit test (49 unit/integration tests total), three compile-fail
types doctests, one bootstrap doctest and 60 bootstrap contract tests. The metadata
guard reports
`resolved_core_packages=3 resolved_core_edges=1 core_external_dependencies=0`.
The repository documentation-link check also passed using `tools.nf.docs_check`.
The actual example stdout is byte-for-byte equal to the documented text in
[the API contract](../development/core-api.md), SHA-256
`1615356294a3728c68d2bb9fe76c296dfd5c4ecd3daa73340cdc76ccd4868bd2`.
It demonstrates three instances of one template, two explicit links, complete
legal values and a Selection-stage illegal value retaining both source origins.

The independent consumer's permutation results all report equality, and its
specific category/stage/key/limit expectations were additionally asserted by the
review runner. The mode/group budget sweeps each report `all invariant` across
1,999 work caps. The final top-level connection regression also passes unchanged;
its red/green evidence and source are in Appendix C. Other consumer source and
reproduction are in Appendix B. Raw sources,
commands, metadata, measurements and outputs are retained in ignored
`artifacts/fnd04-development/review-probes/`, with a `capture.sha256` manifest for
the coordinator to retain with later acceptance evidence. The following hashes
identify local development execution, not remotely archived accepted evidence:

```text
e446ba18980bc49d95e09d810624cf412b0d16bf523f1f47b081e97d3da85292  final-tests.log
bacc1e6218c7049485137cf30fa11c1eb5b00a2c4b52de5c38cccc6095083b46  fmt-tools.log
847670d9f65c13fe7469f086a550ee03fd1cb54fa6c4f0ec72a6e732bf86010e  metadata.json
84924a6d5b9a63536e7c600acb2226efbbd113fb3f6974926e97336bcdbfb684  metadata-check.log
1615356294a3728c68d2bb9fe76c296dfd5c4ecd3daa73340cdc76ccd4868bd2  model.stdout
a71b60ff3e60f9d74abe9646b07ce94d2e9f47c285b9c72607884d829b8bd78a  probe-output.log
8abd08919d2534cf736fc66dc67223dbcc1bcc182c2a3244a9ad4d01c041fbdc  probe-measurements.json
f9eef68a6c091264b385b6d411b00138868b185197d23809c21a5ec9551c5220  mode_order.log
f9eef68a6c091264b385b6d411b00138868b185197d23809c21a5ec9551c5220  group_order.log
5d9c72dc757ee7387196a953651f12148b7e4070ad898c679d6dca7a3e8fa633  top-connection-before.log
a4d044a85ce41778ac239ec6a0e1ea320543b1dca6ec6a2a0185665ff30ed65d  top-connection-after.log
07cba540b93d0e48d8d5ef44685089e53cd765dbe13a43411566d2236a592b11  pre-top-key-repair-source.sha256
7ef331ba183c7b0484bbc2a73f3d426aea25d3ad869d5ac604827d131ce61933  run-probes.py
f57de0c7b35a63f0f69da7ee3522dff2a88acdc272024ee2bba0b90147412321  final-run.sh
6bcdeb796e7c2e90b4446725cb07f4ee4b03b90ed82b50670ae9340a8b9769ee  capture.sha256
aa19a7fcb52de6ac28556f621ff4983101f16999c03dc7dcfaf459d9160fea98  docs-check.log
```

## Acceptance limits

This increment does not affect generated Verilog.

The actual frontend exercised here is a Rust builder. There is no Verilog emitter,
primitive simulator, runtime loader, physical allocator, production DeviceDB,
serializer, Scala exchange execution, fabric-equivalence proof, board run, timing,
PPA or PDK qualification in this reviewed increment. FND-05 owns wire-format and
cross-language contracts; later DB/CFG/RTL and independent reference execution
retain their own gates. FND-03 source/profile receipt integrity and integration
qualification remain separate from the semantic correctness established here.
No local result in this review is relabelled as remote CI or accepted completion.

## Appendix A: reviewed content identities

The sorted manifest's SHA-256 is `8fb5709635347a68344682fd8eca6917f5861885867f0d6d8f505050de009d96`. The report itself and the
coordinator's evolving checkpoint are excluded to avoid a self-referential hash.
All listed bytes were unchanged across the final reviewer execution.

```text
17ff9b331f215c4ad32494e6bd09d24ca858ca5f6d654bea44e1122719406097  Cargo.lock
eab592473bdc77aec24c6d1bb62dcde828c4c251bee7527b286c733ca184b2b3  Cargo.toml
33cc2afcba78f502d90bd1645fbece7e8f5d50e70967104801a8bd47f1dbcf25  core/rust/arch-ir/Cargo.toml
5a1476aaa42dc4ef965778ee2091c191b46ce2fd992642b5fb84e8e49f50dd18  core/rust/arch-ir/examples/model.rs
d2ab4f84f349c4ecc7bb5db203cee585788bd169d30a1fc514ac14d86908fe39  core/rust/arch-ir/src/lib.rs
d4fadf1d525f442cf2127574dbd9bae0893646d9f14f3efa5cb1f017440365aa  core/rust/arch-ir/src/validate/bounds.rs
0598e3e5957704e99a45847b377b48e3bf230bda893a70ae69601bf73c531277  core/rust/arch-ir/src/validate/connections.rs
a64f426b8d9eec0b04de039d6c45ab85b33a1cafd0f999714d8781a407f8dc43  core/rust/arch-ir/src/validate/declarations.rs
3fcc8aab340da643b8dd376dccdda5047f12a445eb5726baf94b95a0c1ef58dc  core/rust/arch-ir/src/validate/references.rs
f72094107ebc3d28396898c5f07187f32223b4d2d84614a455bb4b203d87f1ba  core/rust/arch-ir/src/validate/selection.rs
e112891875782e59ca3149b8efd764e2c286010868da6b891a4479fdc86d1f64  core/rust/arch-ir/src/validate.rs
49f2194be118693682822dc6a296a1203147de0cc1943cbc18b0b0353eb36465  core/rust/arch-ir/tests/independent_contract.rs
86d72d201a305b198bccf62615ac0ea330a1cd9fd46527cd25d543fc5adeb8b5  core/rust/types/Cargo.toml
fcad56968f737f651f565f79ea6cfcee65a7dea40145a4a35c11e4ce6f6eb7d9  core/rust/types/src/diagnostics.rs
ef9103dcf0cf4327f45c5927788fa84f2db1f3952d3fb642455a42f519fdddb3  core/rust/types/src/identity.rs
21d6e32f6ce6aa6ff4c2b84835367e5b756d77f01a76afcd76eb9a3916d6e638  core/rust/types/src/lib.rs
1d35910584c6e7c220ba07b637f6b5e630b93cd5d0fee1be4c416459385a31cc  core/rust/types/src/units.rs
f2900a80b0ebc1932b2cbcaae3561842a5e8264715f548fecc57868b66e3ee25  core/rust/types/tests/independent_contract.rs
37dc80f82b5b9cafdf8f1457fbfcc746c10b427d349fa9a0491a4361148b6f10  docs/development/core-api.md
b26b3d60872b88e389ec8b8882c121dd4326e3bfff40dee548c3cf7df3068615  docs/implementation/fnd-04-readiness.md
5bc9add557a0be6e2dab6177afd65602f5852a1888a33ba11bceff7aa1e48e89  tests/bootstrap/test_contracts.py
c16c61db4ff845d475be6ca0906af7ec545c497ad976ccc7f83bf7e247df8842  tools/check_boundaries.py
2ba4f76e6738a123dd85c06105a83fc658f5833f62b1b3ce0cfd777736680d65  tools/nf.py
acf4e2c6ca81b2831d1c57b39c62faf3f356e7b5e635d586382c52f3d3b5c577  tools/ownership.json
251c4a89368c6adda0272aa45100c9bc9be91ecd2f1515c0ac83a7c65f7a460c  verify/fixtures/fnd-04/README.md
0a2ad8b9bf8a2ce3e3ad34de366530d4c0c1d00a74ce17d87a4f6ad86a271403  verify/fixtures/fnd-04/corpus.rs
b33d80f70272393474ec8583c479acdd488de39d43ee039ca2ab94a0aebd1581  verify/fixtures/fnd-04/expectations.md
fe7a469a2e84f4e36b3ca0faacde94c5b6ab00cf4cb5a2be29af500455fac8e7  verify/fixtures/fnd-04/inventory.json
```

## Appendix B: external public-API consumer

This probe is independent, temporary review code, not a production module or
source of expected answers for repository tests. Copy the following manifest and
source into a separate directory. Adjust the two absolute dependency paths to the
reviewed checkout when reproducing elsewhere; doing so changes the manifest hash.
The original manifest SHA-256 is `f739bee3ceb726c782f4249ff2f9f52a587406105d476df87ed6056a03233c76`; `src/main.rs` SHA-256
is `e98b56497aa18cd2582a3c67ce53316de5e4242fd6dc301a06de5b444785f9ea`.

```toml
[package]
name = "fnd04-review-probe"
version = "0.0.0"
edition = "2024"
[dependencies]
nf-types = { path = "/workspace/scratch/b1740b7ae4cf/nodal-fpga/core/rust/types" }
nf-arch-ir = { path = "/workspace/scratch/b1740b7ae4cf/nodal-fpga/core/rust/arch-ir" }
```

```rust
use nf_arch_ir::*;
use nf_types::{Name, Key, Provenance, PartitionId, BitCount, BitOffset, BitRange, Width};
fn n(s:&str)->Name { Name::new(s).unwrap() }
fn p(s:&str)->Provenance { Provenance::new(None,Some(s.into())).unwrap() }
fn rr()->ResourceRef { ResourceRef { path:vec![], name:n("r"),kind:ResourceKind::Bel,provenance:p("ref")} }
fn base()->Architecture {
 let mut a=Architecture::new(n("a"));
 a.partitions.push(PartitionId::new(0));
 a.resource_types.push(ResourceType{key:Key::new("a",vec![],"R").unwrap(),kind:ResourceKind::Bel,pins:vec![],modes:vec![n("x"),n("y")],provenance:p("type")});
 let mut t=Template::new(Key::new("a",vec![],"TTT").unwrap());
 t.resources.push(Resource{name:n("r"),kind:ResourceKind::Bel,resource_type:a.resource_types[0].key.clone(),alias_of:None,domains:vec![],provenance:p("resource")});
 a.roots.push(Instance{name:n("i"),template:t.key.clone(),partition:Some(PartitionId::new(0)),domains:vec![],provenance:p("instance")});
 a.templates.push(t);a
}
fn main() {
 let mut a=base();let mut alias=a.templates[0].resources[0].clone();alias.name=n("rAlias");alias.alias_of=Some(rr());a.templates[0].resources.push(alias);
 let mut alias_ref=rr();alias_ref.name=n("rAlias");
 a.templates[0].mode_groups.push(ModeGroup{name:n("g"),resources:vec![rr(),alias_ref],modes:vec![n("x")],provenance:p("group")});
 let e1=validate_architecture(&a,&ValidationLimits::default()).unwrap_err();a.templates[0].mode_groups[0].resources.reverse();let e2=validate_architecture(&a,&ValidationLimits::default()).unwrap_err();
 println!("mode alias membership permutation same={} first={:?} reverse={:?}",e1==e2,e1,e2);

 let a=base();let l=ValidationLimits{max_depth:1,max_key_component_bytes:10,..ValidationLimits::default()};let v=validate_architecture(&a,&l).unwrap();
 let mut s=Selection{modes:vec![ModeSetting{path:vec![n("i"),n("i")],group:n("g"),mode:n("x"),provenance:p("deep")},ModeSetting{path:vec![n("i")],group:n("12345678901"),mode:n("x"),provenance:p("long")}],features:vec![]};
 let e1=validate_selection(&v,&s).unwrap_err();s.modes.reverse();let e2=validate_selection(&v,&s).unwrap_err();
 println!("selection preflight permutation same={} first={:?} reverse={:?}",e1==e2,e1,e2);

 let mut a=base();
 a.resource_types[0].kind=ResourceKind::Field;
 a.templates[0].resources[0].kind=ResourceKind::Field;
 let mut owner=rr();owner.kind=ResourceKind::Field;
 a.templates[0].storage.push(Storage{name:n("s"),owner:owner.clone(),bits:BitCount::new(1),provenance:p("storage")});
 a.templates[0].features.push(Feature{name:n("r"),owner,storage:n("s"),range:BitRange::new(BitOffset::new(0),BitCount::new(1)).unwrap(),width:Width::new(1).unwrap(),domain:ValueDomain::Any,guard:vec![],alias_of:None,provenance:p("feature r")});
 println!("field resource-feature collision={:?}",validate_architecture(&a,&ValidationLimits::default()).map(|_|()));

 let mut a=base();a.templates[0].resources.clear();
 for level in 0..10 {
  let previous=a.templates.last().unwrap().key.clone();
  let mut t=Template::new(Key::new("a",vec![],format!("L{level}")).unwrap());
  for i in 0..32 {t.children.push(Instance{name:n(&format!("i{i}")),template:previous.clone(),partition:None,domains:vec![],provenance:Provenance::default()});}
  a.templates.push(t);
 }
 a.roots[0].template=a.templates.last().unwrap().key.clone();
 let now=std::time::Instant::now();
 let e=validate_architecture(&a,&ValidationLimits::default()).unwrap_err();
 println!("highfanout virtual_instances=1162219258676257 templates=11 child_instance_declarations=320 leaf_instances=1125899906842624 accounted_declarations=336 elapsed_ms={} diagnostic={:?}",now.elapsed().as_millis(),e);

 let mut a=base();
 let victim=Template::new(Key::new("a",vec![],"aaVictim").unwrap());
 let mut ca=Template::new(Key::new("a",vec![],"mmCycleA").unwrap());
 let mut cb=Template::new(Key::new("a",vec![],"zzCycleB").unwrap());
 let mut edge=a.roots[0].clone(); edge.partition=None;
 edge.name=n("a_to_b");edge.template=cb.key.clone();ca.children.push(edge.clone());
 edge.name=n("a_to_victim");edge.template=victim.key.clone();ca.children.push(edge.clone());
 edge.name=n("b_to_a");edge.template=ca.key.clone();cb.children.push(edge);
 a.roots[0].template=ca.key.clone();a.templates=vec![victim,ca,cb];
 println!("cycle primary={:?}",validate_architecture(&a,&ValidationLimits::default()).unwrap_err());

 let mut a=base();
 let mut bad=Template::new(Key::new("a",vec![],"long").unwrap());
 let mut other=Template::new(Key::new("a",vec![],"b").unwrap());
 other.children=vec![a.roots[0].clone();3];
 bad.resources.clear();
 a.templates=vec![bad,other];
 let l=ValidationLimits{max_key_component_bytes:3,max_collection:2,..ValidationLimits::default()};
 let e1=validate_architecture(&a,&l).unwrap_err();a.templates.reverse();
 let e2=validate_architecture(&a,&l).unwrap_err();
 println!("preflight permutation same={} first={:?} reverse={:?}",e1==e2,e1,e2);

 let a=base();
 let v=validate_architecture(&a,&ValidationLimits::default()).unwrap();
 let s=Selection{modes:vec![], features:vec![FeatureSetting{field:FieldRef{path:vec![n("i")],name:n("missing"),provenance:p("bad field")},value:0,provenance:p("bad setting")}]};
 println!("missing selection field={:?}",validate_selection(&v,&s));
 let l=ValidationLimits{max_key_bytes:4,..ValidationLimits::default()};
 println!("qualified limit4 result={:?}",validate_architecture(&a,&l).map(|_|()));
 let mut a=base(); let dk=Key::new("a",vec![],"D").unwrap();
 a.domains.push(Domain{key:dk.clone(),kind:DomainClass::Clock,provenance:p("domain")});
 a.roots[0].domains=vec![DomainRef{key:dk.clone(),kind:DomainClass::Clock,provenance:p("first")},DomainRef{key:dk,kind:DomainClass::Clock,provenance:p("second")}];
 let e1=validate_architecture(&a,&ValidationLimits::default()).unwrap_err();a.roots[0].domains.reverse();
 let e2=validate_architecture(&a,&ValidationLimits::default()).unwrap_err();
 println!("domain permutation same={} first={:?} reverse={:?}",e1==e2,e1,e2);
 let mut a=base();
 a.templates[0].mode_groups.push(ModeGroup{name:n("g"),resources:vec![rr()],modes:vec![n("x"),n("y")],provenance:p("group")});
 a.templates[0].storage.push(Storage{name:n("s"),owner:rr(),bits:BitCount::new(1),provenance:p("storage")});
 a.templates[0].features.push(Feature{name:n("f"),owner:rr(),storage:n("s"),range:BitRange::new(BitOffset::new(0),BitCount::new(1)).unwrap(),width:Width::new(1).unwrap(),domain:ValueDomain::Any,guard:vec![ModeChoice{group:n("g"),mode:n("x"),provenance:p("first")},ModeChoice{group:n("g"),mode:n("y"),provenance:p("second")}],alias_of:None,provenance:p("feature")});
 let e1=validate_architecture(&a,&ValidationLimits::default()).unwrap_err();a.templates[0].features[0].guard.reverse();
 let e2=validate_architecture(&a,&ValidationLimits::default()).unwrap_err();
 println!("guard permutation same={} first={:?} reverse={:?}",e1==e2,e1,e2);

 a.templates[0].features[0].guard.clear();
 a.templates[0].storage[0].bits=BitCount::new(2);
 a.templates[0].features[0].width=Width::new(2).unwrap();
 a.templates[0].features[0].range=BitRange::new(BitOffset::new(0),BitCount::new(2)).unwrap();
 a.templates[0].features[0].domain=ValueDomain::Set(vec![0,1]);
 let s=Selection{modes:vec![ModeSetting{path:vec![n("i")],group:n("g"),mode:n("x"),provenance:p("setting")}], features:vec![FeatureSetting{field:FieldRef{path:vec![n("i")],name:n("f"),provenance:p("field")},value:2,provenance:p("setting")}]};
 let v=validate_architecture(&a,&ValidationLimits::default()).unwrap();
 let e1=validate_selection(&v,&s).unwrap_err();
 a.templates[0].features[0].domain=ValueDomain::Set(vec![1,0]);
 let v=validate_architecture(&a,&ValidationLimits::default()).unwrap();
 let e2=validate_selection(&v,&s).unwrap_err();
 println!("set permutation same={} first={:?} reverse={:?}",e1==e2,e1,e2);
}
```

Commands for the exact prepared environment:

```sh
source .cache/toolchains/env.sh
cargo build --offline --manifest-path /tmp/fnd04-review-probe/Cargo.toml --bins
/tmp/fnd04-review-probe/target/debug/fnd04-review-probe
/tmp/fnd04-review-probe/target/debug/mode_order
/tmp/fnd04-review-probe/target/debug/group_order
```

The following excerpts show the supplemental binaries' `main` functions; their
imports and `n`, `p`, `rr`, `base` helpers repeat the helpers above. Exact full
files are retained as `src/bin/mode_order.rs` and `src/bin/group_order.rs` in the
capture directory. Their full-file hashes also bind those repeated helpers. `mode_order.rs` has SHA-256 `5604c0630f1e926840fffd6c9fef427316afaa8aa75ff7fc5cc0186a90a6e11f`;
`group_order.rs` has SHA-256 `e41a61adbf25851b264566743fe262c57bd6ef2095f288816bc621292e94f0dd`. The code scans limits rather than
fixing an accounting-specific threshold and compares complete results.

```rust
fn main() {
 let mut a=base();
 a.templates[0].mode_groups.push(ModeGroup{name:n("g"),resources:vec![rr()],modes:vec![n("x"),n("z1"),n("z2")],provenance:p("group")});
 let mut b=a.clone();b.templates[0].mode_groups[0].modes.reverse();
 for work in 1..2000 {
 let limits=ValidationLimits{max_work:work,max_diagnostics:1,..ValidationLimits::default()};
 let x=validate_architecture(&a,&limits).map(|_|());
 let y=validate_architecture(&b,&limits).map(|_|());
 if x!=y { println!("work={work} first={x:?} reversed={y:?}"); return; }
 }
 println!("all invariant");
}
```

```rust
fn main() {
 let mut a=base();
 a.templates[0].mode_groups.push(ModeGroup{name:n("g0"),resources:vec![rr()],modes:vec![n("x"),n("x")],provenance:p("group0")});
 a.templates[0].mode_groups.push(ModeGroup{name:n("g1"),resources:vec![rr()],modes:vec![n("x"),n("y")],provenance:p("group1")});
 let mut b=a.clone();b.templates[0].mode_groups.reverse();
 for work in 1..2000 {
 let limits=ValidationLimits{max_work:work,max_diagnostics:1,..ValidationLimits::default()};
 let x=validate_architecture(&a,&limits).map(|_|());
 let y=validate_architecture(&b,&limits).map(|_|());
 if x!=y { println!("work={work} first={x:?} reversed={y:?}"); return; }
 }
 println!("all invariant");
}
```

## Appendix C: final top-level connection key regression

This independent consumer was authored and executed before the narrow repair.
It accepts the literal 36-byte bound, then requires a singleton Architecture
`Limit` at 30 bytes. Before the fix it printed `accepted=true` and exited 101
at the expected-rejection assertion; after the fix the identical source prints
`accepted=false` and `top_level_connection_key_limit=correctly_rejected`, exiting 0.
The preserved `pre-top-key-repair-source.sha256` identifies the earlier reviewed
source; `top-connection-before.log` is explicitly a pre-repair negative witness,
not a current-source success. Current source is Appendix A. The permanent test
adds the one-byte overflow, permutation and nominal duplicate-key assertions.

Full source `src/bin/top_connection_key.rs` SHA-256:
`e463623b530a3749cb671a3020666eddc808ac1f575d016122183e8997b65a38`.

```sh
source .cache/toolchains/env.sh
cargo run --quiet --offline --manifest-path /tmp/fnd04-review-probe/Cargo.toml --bin top_connection_key
```

```rust
use nf_arch_ir::*;
use nf_types::{BitCount, Code, Key, Name, PartitionId, Provenance, Stage};
fn n(s: &str) -> Name { Name::new(s).unwrap() }
fn main() {
    let namespace = "abcdefghijk"; // 11 UTF-8 bytes
    let mut a = Architecture::new(n(namespace));
    let type_key = Key::new(namespace, vec![], "R").unwrap();
    a.resource_types.push(ResourceType {
        key: type_key.clone(), kind: ResourceKind::Bel,
        pins: vec![
            Pin { name: n("I"), direction: Direction::Input, width: BitCount::new(1), provenance: Provenance::default() },
            Pin { name: n("O"), direction: Direction::Output, width: BitCount::new(1), provenance: Provenance::default() },
        ], modes: vec![], provenance: Provenance::default(),
    });
    let mut t = Template::new(Key::new(namespace, vec![], "T").unwrap());
    t.resources.push(Resource { name: n("r"), kind: ResourceKind::Bel, resource_type: type_key,
        alias_of: None, domains: vec![], provenance: Provenance::default() });
    a.roots.push(Instance { name: n("i"), template: t.key.clone(), partition: Some(PartitionId::new(0)),
        domains: vec![], provenance: Provenance::default() });
    a.templates.push(t);
    a.partitions.push(PartitionId::new(0));
    let endpoint = |pin: &str| Endpoint {
        resource: ResourceRef { path: vec![n("i")], name: n("r"), kind: ResourceKind::Bel, provenance: Provenance::default() },
        pin: n(pin), provenance: Provenance::default(),
    };
    a.connections.push(Connection { name: n("abcdefghijklmnopqrstuvwxy"), // 25 bytes; Pip key total 36
        sources: vec![endpoint("O")], destination: endpoint("I"), selector: None, provenance: Provenance::default() });
    validate_architecture(&a, &ValidationLimits { max_key_bytes: 36, ..ValidationLimits::default() }).unwrap();
    let result = validate_architecture(&a, &ValidationLimits { max_key_bytes: 30, ..ValidationLimits::default() });
    println!("namespace_bytes=11 connection_name_bytes=25 complete_key_bytes=36 limit=30 accepted={}", result.is_ok());
    let errors = result.expect_err("top-level connection Pip key must honor combined namespace/name bound");
    assert_eq!(errors.len(), 1);
    assert_eq!(errors[0].code, Code::Limit);
    assert_eq!(errors[0].stage, Stage::Architecture);
    assert_eq!(errors[0].expected.as_deref(), Some("30"));
    println!("top_level_connection_key_limit=correctly_rejected");
}
```
