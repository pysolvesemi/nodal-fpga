"""Actual filter and FD/environment helper controls; no package acceptance credit."""
from pathlib import Path
import shutil
import subprocess
import sys
import struct
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import runtime_filter
import saved_runtime


class RuntimePolicyTests(unittest.TestCase):
    def test_compiled_filter_and_actual_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            minimal = stage / "root"
            for directory in ["bin", "inputs", "proc", "dev", "tmp"]:
                (minimal / directory).mkdir(parents=True)
            for name, source in [("filter", "socket_filter.c"), ("runtime-probe", "runtime_probe.c")]:
                subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(ROOT / "tools/runtime" / source), "-o", str(stage / name)], check=True)
            blob = subprocess.check_output([str(stage / "filter")])
            runtime_filter.verify(blob)
            filter_path = stage / "filter.bpf"
            filter_path.write_bytes(blob)
            for name, source in [("true", Path("/bin/true")), ("runtime-probe", stage / "runtime-probe")]:
                shutil.copy2(source, minimal / "bin" / name)
                libs, _ = saved_runtime.libraries(source)
                for library in libs:
                    destination = minimal / str(library).lstrip("/")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(library.resolve(), destination)
            code, _, _ = saved_runtime.launch(minimal, filter_path, ["/bin/true"], stage / "control", trace=False)
            self.assertEqual(code, 0, (stage / "control.stderr").read_text())
            self.assertEqual((stage / "control.stderr").read_text(), saved_runtime.POLICY)
            code, _, _ = saved_runtime.launch(minimal, filter_path, ["--x32"], stage / "x32", trace=False)
            self.assertEqual(code, 159)


class RuntimeEvidenceTests(unittest.TestCase):
    def test_loader_requires_real_entry_and_exact_libraries(self):
        libs = {"/lib/libc.so.6", "/lib64/ld-linux-x86-64.so.2"}
        inventory = {name: {"sha256": "a" * 64} for name in libs}
        text = (saved_runtime.POLICY +
                " 2: file=libc.so.6 [0]; needed by /bin/nf-exchange [0]\n" +
                " 2: calling init: /lib/libc.so.6\n" +
                " 2: calling init: /lib64/ld-linux-x86-64.so.2\n" +
                " 2: initialize program: /bin/nf-exchange\n" +
                " 2: transferring control: /bin/nf-exchange\n")
        result = saved_runtime.loader_records(text.encode(), libs, inventory)
        self.assertEqual(set(result["initialized_libraries"]), libs)
        for bad in [text.replace("initialize program: /bin/nf-exchange", "initialize program: /bin/runtime-probe"),
                    text.replace("/lib/libc.so.6", "/unreviewed/libc.so.6"),
                    text + " 2: file=unreviewed.so [0]; loaded\n",
                    text + saved_runtime.POLICY,
                    text.replace(" 2: transferring control: /bin/nf-exchange\n", "")]:
            with self.assertRaises(ValueError):
                saved_runtime.loader_records(bad.encode(), libs, inventory)

    def test_filter_rejects_missing_process_denial(self):
        # A permissive program must not pass merely because it is valid BPF.
        with self.assertRaises(ValueError):
            runtime_filter.verify(struct.pack("=HBBI", 0x06, 0, 0, runtime_filter.ALLOW))
        with self.assertRaises(ValueError):
            runtime_filter.evaluate(b"invalid", 0)

    def test_reader_stderr_requires_boundary_marker(self):
        with self.assertRaises(ValueError):
            saved_runtime.reader_stderr(b" 2: initialize program: /bin/nf-exchange\n", True)
        self.assertEqual(saved_runtime.reader_stderr(saved_runtime.POLICY.encode(), False), b"")
