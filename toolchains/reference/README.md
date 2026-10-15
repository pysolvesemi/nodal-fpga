# Independent reference environment

This optional external-test profile is never sourced by default core, Scala or
saved-package runtime entrypoints. It contains no redistributed dependency
binaries. `sources.json` records four exact official Debian archives, 78 exact
PyPI wheel URLs/hashes, and two independently built wheel identities tied to exact
FABulous/SDF git commits. Installed package contents are compared with all eighty
wheel archives before execution. The source import resolves to a clean checkout
of the pinned upstream commit, not the installed FABulous package copy.

## Preparation and reconstruction

Use an external archive directory with `downloads/` and `python-wheels/`.
`python3 toolchains/reference/provision.py --archives ARCHIVES --fetch` explicitly
acquires only official hash-checked archives. The two pinned-source wheels are
not fetched from a different release or silently rebuilt: provide the separately
built, retained, exact-hash wheels from the approved external preparation. Their
source URL/commit, local build identity and distinction from registry artifacts
are recorded in the manifest. Upstream build dependencies are not yet a qualified
fresh CI build closure. No wheelhouse or bundled image may be published.

Given an independently qualified CPython 3.12.14 interpreter, reconstruct an
external cache offline with:

```
python3 toolchains/reference/provision.py --archives ARCHIVES \
  --destination NEW_REFERENCE_CACHE --python QUALIFIED_PYTHON
```

The reconstruction verifies every archive, extracts packages without system
installation, creates a separate venv, installs exactly the hash-locked runtime
closure without dependency resolution/network, removes installer distributions,
and writes relocatable wrappers plus actual local binary identities. It never
runs editable upstream synchronization. A successful reconstruction is explicitly
not qualification; run the capability lane and complete corpus afterward.

## Isolated invocation

```
python3 tools/reference_environment.py --cache REFERENCE_CACHE \
  --upstream CLEAN_PINNED_UPSTREAM --smoke-output NEW_LOCAL_OUTPUT
```

This tools-only capability lane performs no reference generation, simulation or
formal proof. It checks actual generator imports and version/source resolution,
read-only source/root mounts, clean environment and descriptors, socket denial,
subprocess support, exact tool versions, timeout, bounded output/storage failure,
negative exit and session denial. Raw records stay local. Only the bounded
portable summary is printed.

Python orchestration imports `ReferenceEnvironment` from
`tools.reference_environment`, constructs it with `(repo, cache, upstream)`, then
calls `run(argv, new_output_dir, inputs={"/inputs/name": host_path})`. Tool names
come from `command(name)`. Each stage runs in `/work`, backed by
`new_output_dir/work`, with fresh HOME/config/tmp. Raw stdout/stderr live in
`new_output_dir/logs`; `ProcessResult.portable()` excludes their private paths.
`local-environment.json` is private evidence, not a publication artifact.

A bounded immutable source snapshot includes only `tools`, `verify` and
`toolchains`; it excludes bytecode, caches, artifacts and the checkout's git
metadata. During development the snapshot is explicitly labeled dirty and each
file hash retained. Final qualification supplies `NF_EXPECT_SHA` or
`expected_sha=...`, requiring exact HEAD and a clean tracked/untracked source tree.
Every mounted file and symlink, including wrappers, support scripts, recursive
stdlib and upstream git metadata, is bound in a private recursive runtime inventory,
with the bwrap executable hash/version. The inventory is rechecked immediately
before every launch; changed or added bytes fail closed.
The separately authored harness and prior generated outputs mount read-only under
`/inputs`. Compile the standalone model with the pinned ordinary Rust toolchain
in its own build profile, then mount its exact prebuilt binary as a reference
input; the hardware root does not import the Rust compiler/cache.

## Enforcement and scope

The actual child runs in unprivileged bubblewrap user/PID/IPC/UTS namespaces with
all capabilities dropped, no inherited environment, and descriptors 0/1/2.
Only named interpreter/stdlib, selected tool/venv/source roots and their ELF
library closure are mounted read-only; no ambient `/usr`, home or host cache is
mounted. Optional Tk/Tcl GUI support is outside this headless CPython profile.
The only regular writable mount is `/work`. A Linux x86_64 seccomp filter denies
socket-family/io_uring operations, mount/unshare/setns and session escape, killing
alternate/x32 syscall ABIs. Reviewed tools may fork/clone necessary children.
This is socket-denial isolation, not a network namespace or a generic hostile-code
security certification. No ptrace or denied network namespace is requested.

`Limits` defaults to 120 seconds wall/CPU, 4 GiB address space per process, 16 MiB
combined captured stdout/stderr, 256 MiB sampled aggregate files, 128 MiB per file,
4096 files, 64 descendant processes and 256 FDs per process. CPU, address-space,
file-size and FD limits are kernel rlimits. RLIMIT_NPROC is UID-scoped, not a
per-job cgroup. Additional descendant-count/storage checks run every nominal
20 ms plus scan cost; between-sample overshoot is possible and depends on child
write/fork rate and scan/scheduling latency. They are rejection guardrails, not
hard aggregate quotas. Captured logs never exceed their combined byte ceiling.
Timeout or any bound breach kills the process group; namespace-init death cleans
remaining namespace processes. No unrestricted retry obtains acceptance.

CPU/user/system/max-RSS come from `wait4` of the actual tool inside the namespace,
not merely bubblewrap's launcher. Killed runs can lack this accounting and retain
launcher-only measurements; they are failed controls with no workload performance
credit. Maximum RSS is a process-tree wait4 maximum, not simultaneous summed RSS.
Wall duration includes isolation/startup/capture. Raw command/error details remain
local, and any tool-error/crash/timeout is distinct from semantic mismatch.

## Final CI gate and redistribution limit

The existing prepared environment is not a portable CI image. Required ABI is
Linux x86_64, glibc >= 2.38, libstdc++ >= 14 and CPython 3.12.14/cp312. Final FND-08
must pin an actual Debian trixie base digest, exact runtime libraries and CPython
source/archive/build closure, record the independently built image/binaries,
reconstruct the dependencies, and replay capability controls plus the complete
reference corpus. `qualified_ci_image: null` deliberately records that unfinished
gate; a mutable tag, default Debian Python, or local host success cannot fill it.
Separately rebuilt wheels may differ; retain and qualify their actual identities
rather than relabeling them as the prepared bytes. The provisioning recipe has
not itself earned a fresh-environment qualification result.

The exact lln-libparse 0.56.0 LLVM contributor/pybind11 notice ancestry remains
unresolved. Official wheels remain external test-only installations. Do not
redistribute wheelhouses, tool binaries, raw local manifests/logs, runtime roots
or bundled images in Nodal deliverables. Preserve upstream source/license notices
for actual permitted generated/source RTL artifacts.
