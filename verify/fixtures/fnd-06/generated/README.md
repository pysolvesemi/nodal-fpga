# Actual FABulous reference RTL deliverables

These four shape directories contain the actual, unedited output bytes from the
first repetition of the passed FND-06 development execution: 7 RTL files for
`one`, 10 for `square`, and 13 each for `odd` and `sparse` (43 total).
Each directory includes the exact ordered `sources.f`, upstream
`LICENSE.FABulous`, and a portable `manifest.json`. Raw execution metadata,
logs, host inventories, tool binaries, and process paths are excluded.

The manifest distinguishes copied source RTL from generated RTL, binds both the
immutable historical runner and FND-06 execution adapter, records the pinned
upstream commit/tree, and links every original input by repository-relative path,
byte length and SHA-256. The original CSVs, configuration inputs and shared source
files remain in `../../nf-tiny`; they are not rewritten here. The adapter's only
execution adjustment creates the official `.FABulous` project directory before
context initialization. Apache-2.0 upstream licensing is retained per shape;
source-file attribution comments are preserved byte-for-byte.

Replay uses the isolated reference profile through `./nf check reference`
with the separately provisioned, pinned reference tools and upstream checkout.
The coordinator must call `tools.reference_archive.verify_archive` for each shape
and fresh generated inventory. It requires exact archived bytes, file roster,
source list, license and provenance metadata; missing archives are failures.
The validator performs no hardware execution itself. Fresh generation and the
independent semantic/structural witnesses remain separate required checks.

These are externally generated reference RTL, not Nodal-emitted RTL. They are
actual deliverables and reproducibility comparisons, not independent golden
semantic expectations. Development execution does not establish fresh portable
CI reconstruction, production implementation qualification, or silicon claims.
