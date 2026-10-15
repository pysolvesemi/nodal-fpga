# FND-05 independent exchange/runtime review summary

Review date: 2026-10-15 UTC. This is an editorial summary of the independent
read-only review, preserving its disposition and limits. The original report was
archived locally with SHA-256
`0416256b1ecf45dd07953425fe7da171b0b0d54415af766b69b3149fe7e263a4`.
The summary is not a new implementation review or clean-head qualification.

## Disposition

No unresolved blocking finding remains in the reviewed production exchange source and scoped saved-package runtime evidence. The original early findings were fixed and relevant independent regressions passed in the actual inspected development executions. The loader/procfs/process-denial observation is adequate for the current FND05 readiness section 12 and ADR0001 saved-package dependency profile, with the precise limitations below.

This is exact-file-hash source review plus independently inspected actual execution evidence, not repository integration or checklist closure. The coordinator must still bind the reviewed file vector and execution results to the published/qualified source and verify integration under repository policy. A later source change invalidates the affected review and requires appropriate requalification. The report deliberately does not edit the machine report's qualification_complete=false flag or the roadmap.

## Scope and method

Read AGENTS, Foundation acceptance/applicability and FND05/FND08 leaves, accepted readiness/R1–R5 decisions, ADR0001/0002/0003, current exchange crate, source-bound dependency inventory and generator usage, runtime launcher/filter/probe/verifier, and relevant independent test source. Inspected retained Rust, Scala, conformance and actual runtime results. Used read-only filesystem commands and Python standard-library hashing/JSON checks to independently verify evidence. Did not edit repository source, build or run the candidate, derive or replace golden answers, retry ptrace, request host-setting changes, run CI, or perform remote publication.

The review is not a comprehensive audit of every third-party implementation line, cryptography, arbitrary hostile Rust/JVM code, kernel isolation, or future production architecture behavior. Review of dependency graph/hook integrity is distinct from a claim that all dependencies are unsafe-free or vulnerability-free.

## Resolved early findings

1. Manifest budgets: package budget preflight now charges declarations/references, text bytes and index units before descriptor indexing/resolution. The independently specified primary case has exact 15 declaration, 2 reference and 296 work charges. Public-API tests verify below/at/above limits, no resolver call before failed preflight/build identity, one callback per digest, one overflow-probe byte, conflicting lengths and immutable accepted results despite backing-store changes.
2. Optional features: only the exact three registered semantic IDs are barred from optional placement. Unknown optional annotations, including unknown names within nodal-fpga, remain preserved with notices and cannot alter semantic identity.
3. Schema error order: ordered values preserve input member order; typed enum/key/u16/u32 validation occurs at the visited field. Each of four tagged DTO families uses explicit EnumAccess, selects its required discriminator, and decodes the remaining payload in input order while retaining nested paths. Envelope compatibility precedes body admission as the accepted phase contract requires. Missing fields are detected at object end. Required Nullable distinguishes absent from explicit null.
4. Diagnostic token safety: fixed DecodeError categories and structured field tokens replace input-string category inference. Structured append_field handles missing/discriminator/unit-extra fields; ordinary tracked map keys are never duplicated or suffix-guessed. Repeated domain/domain, slash/tilde/backtick, long UTF-8 keys and hostile enum marker regressions are present and passed. Human presentation is capped separately from the exact structured RFC6901 location.
5. Semantic design ordering: bounded borrowed cell/port/net/load indexes sort by semantic key with checked provenance tie-breakers before semantic failure selection. Original indices remain in pointers. Input preflight stays input-ordered. Widths and bit indices never drive bus expansion, range enumeration or allocation.
6. Numeric/BOM categorization: valid-UTF8 BOM is invalid_json. i64/u64 visitor values outside i32 are overflow; pinned-parser f64/unrepresentable literals are invalid_json, including huge integer lexemes. This is honestly documented and independently tested; semantic U64 strings retain exact grammar/range checks. No arbitrary-precision feature or second handwritten JSON scanner was introduced.

## Final source observations

- The bounded Serde seed enforces actual maximum+1 input reads, UTF-8 admission, duplicate decoded keys, key-inclusive node count, depth, immediate collection and decoded-string limits before accepted DTOs exist. Limits are positive and lowered-only; all public read APIs reject invalid limits before I/O.
- Closed private DTOs consume into public checked FND04 types and its authoritative architecture validator. Core diagnostics are retained, with no native-layout serialization, pointer casts or unsafe project code. No second accepted architecture model is exposed.
- Canonicalization enumerates typed sets and cold provenance sites. String/key comparison uses unsigned UTF-8 ordering. Pin lists, mux-source order, structured path segments and annotation arrays are retained. Domain-separated identities exclude only the specified fields; arbitrary nested annotations named provenance/semantic_id are not stripped.
- Package preflight checks all descriptors, deduplicated lengths/count/aggregate limits and the manifest build ID before any resolver callback. Only the architecture role is interpreted; opaque leaves are length/digest-checked and discarded. Accepted objects retain immutable validated state and never reopen backing files or execute named tool bindings.
- Mapped design target identity precedes target lookups. BEL type/mode, direction, pin/port widths, scalar-terminal ownership and legal constant roles are validated. No placement/routing/timing/technology capability is inferred from these checks.
- The final boxed ExchangeError preserves public inspectable diagnostic fields through Deref and JSON newtype serialization while reducing Result error size. Its CLI constructor preserves capped messages; original core diagnostic payloads remain intact. Final parser/canonical collapsible-if changes preserve behavior. No lint suppression was introduced.
- Bounded temporary DTO/JSON duplication is proportionate for this profile; shared templates and hierarchy are retained. Observed repetition/depth/payload results are measured finite test behavior, not production performance or peak-memory guarantees.

## Actual development results inspected

The reviewer inspected actual commands/results and independently rehashed
artifacts; it did not itself build or execute the implementation. Rust formatting,
strict Clippy, workspace tests and doctests passed, including 8 exchange unit and
12 independent public-API tests. The reviewed bootstrap run passed 74 tests,
Scala WriterChecks passed 17 groups, conformance passed 83 groups, and four runtime
harness controls passed. Earlier intermediate counts are not credited as final.

All six actual saved-runtime cases passed their intended positive/negative
outcomes, with exact actual Scala canonical equality. The independent reviewer
checked every root file and output/snapshot hash, executable identity, source and
filter, permitted libraries, environment/descriptors/status and mounts. The
[runtime summary](fnd-05-runtime.md) records the outcomes and precise observation
limits; the [checkpoint](fnd-05-checkpoint.md) records reproduction and pending
integration gates. Raw execution records are locally archived outside the
candidate, not published in this repository.

## Dependency/advisory disposition

The exact Rust resolved graph, source-tree/archive identities, normal/build/dev/target declarations, activated features and build/proc-macro hooks are frozen and checked before build execution. force-soft is not falsely represented as erasing cpufeatures/libc graph edges. Project forbid(unsafe_code) is not third-party unsafe-free certification. Scala compiler/runtime JAR/POM classpaths are distinct and absent from the saved runtime.

Jackson2.21.5 is affected by upstream advisories. The retained pin is acceptable only for the reviewed bounded trusted-source UTF-8 JsonGenerator fixture writer: writeNumber(Int) and writeString, no parser/databind/NumberInput/reflection/code-loading paths. Static/compiled-class guards are review tripwires, not comprehensive hostile-source security proof. Official upstream references checked during this review:

- https://github.com/FasterXML/jackson-core/security/advisories/GHSA-7hhh-6rmp-j9qf (DataInput parser, fixed2.21.7)
- https://github.com/FasterXML/jackson-core/security/advisories/GHSA-p6pp-m3f8-5c89 (numeric-string validation, fixed2.21.7)
- https://github.com/FasterXML/jackson-core/security/advisories/GHSA-649p-m576-vr99 (char-backed parser length limit, fixed2.21.6)
- https://github.com/FasterXML/jackson/wiki/Jackson-Release-2.21.7 (current release and generator fix context)

The additional WriterBasedJsonGenerator zero-length custom escape issue is not reached by the reviewed UTF-8 byte generator and six-character control escapes. FND07 must revisit on broadened parser/coercion/numeric-string/reflection/service-loading APIs, untrusted JSON input, source language/classpath/pin/build-input changes, or relevant new advisory. No general clean-security claim or FND07 completion follows.

## Rust-build applicability clarification

FND05's explicit leaves and accepted readiness require the new graph/hooks/checksums review and actual locked/offline build, actual pinned Scala authoring, and separate saved-package consumer runtime. Readiness section12 explicitly builds Rust outside runtime isolation. FND01.c.3 owns the accepted historical isolated Rust-build baseline; FND08.c.1 explicitly replays all three profiles independently on the Foundation release candidate. A new JVM-absent Rust buildroot is not an additional FND05 acceptance requirement under this frozen plan.

The current local build host contains Scala/JDK. Its build and exact dependency graph are evidence of compilation/ownership, not a new JVM-absent default-build-profile replay. FND01's historical result cannot be relabeled as current22-package isolation. Existing ADR/default-build guards remain required, and the full FND08 replay remains open. No current claim that all ADR profiles were requalified is supported.

## Claim limits and remaining coordinator gates

This review supports current-profile FND05 parser/package/design/canonical/source quality and scoped saved-runtime observation. It does not close source publication, clean-head qualification binding, verified merge/evidence closure, or any remaining coordinator checklist obligation. There is no RTL emitter, full DeviceDB inspection, programming/configuration allocator, CAD legality, production performance, hardware equivalence or silicon qualification.

This increment does not affect generated Verilog.

## Exact reviewed identities and publication example

The [28-entry reviewed source vector](fnd-05-review-source.sha256) preserves every
source hash from the independent report, including exchange, runtime harness,
dependency inventories and readiness. The separately retained
[43-entry development input vector](fnd-05-development-source.sha256) binds the
independent conformance inputs. These vectors identify dirty development source;
they do not certify any later commit, policy edit or reviewed summary bytes.

The reviewer independently extracted all three complete JSON examples, excluding
only the documented presentation newline. Architecture 6,525 bytes, package
1,839 bytes and design 2,186 bytes matched actual Scala output and successful
runtime canonical output exactly. The example distinguishes generated observations
from independent expected goldens and preserves its source-bound authoring identity.

Independent editorial/cleanup review confirmed faithful preservation of the original
findings, limits, source vectors, four manifests and 121 literal artifacts. Exact
clean-commit qualification remains pending. No authoritative checkbox is closed
by this editorial conversion.
