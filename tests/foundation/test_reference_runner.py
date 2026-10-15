"""Pure runner controls. Actual namespace/tool smoke is a separate explicit lane."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.reference_runner import Limits, run_bounded, storage_usage
from tools.reference_environment import DENIED, socket_filter, ReferenceEnvironment
from tools.runtime_filter import evaluate, ALLOW, ERRNO_EPERM, KILL


class ReferenceRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.work = self.root / 'work'
        self.work.mkdir()

    def run_code(self, code, limits=Limits(), env=None):
        return run_bounded([sys.executable, '-c', code], output_dir=self.root / 'logs',
                           work_dir=self.work, cwd=self.work, limits=limits, env=env)

    def test_success_and_separate_hashed_streams(self):
        result = self.run_code('import sys; print("out"); print("err",file=sys.stderr)')
        self.assertEqual(result.category, 'passed')
        self.assertEqual(result.stdout_path.read_bytes(), b'out\n')
        self.assertEqual(result.stderr_path.read_bytes(), b'err\n')
        self.assertEqual(result.stdout_sha256, hashlib.sha256(b'out\n').hexdigest())
        self.assertNotIn('stdout_path', result.portable())
        self.assertGreater(result.max_rss_kib, 0)

    def test_nonzero_is_not_semantic_detection(self):
        self.assertEqual(self.run_code('raise SystemExit(3)').category, 'tool-error')

    def test_timeout_is_failure(self):
        result = self.run_code('import time; time.sleep(10)', replace(Limits(), wall_seconds=.15))
        self.assertEqual(result.category, 'timeout')
        self.assertLess(result.wall_seconds, 2)
        self.assertNotEqual(result.returncode, 0)

    def test_stream_flood_is_capped_not_buffered(self):
        result = self.run_code('import os;\nwhile True: os.write(1,b"x"*65536)',
                               replace(Limits(), output_bytes=12345))
        self.assertEqual(result.category, 'output-limit')
        self.assertEqual(result.stdout_bytes + result.stderr_bytes, 12345)
        self.assertEqual(result.stdout_path.stat().st_size, 12345)

    def test_aggregate_storage_limit(self):
        result = self.run_code('from pathlib import Path; import time; Path("a").write_bytes(b"a"*10000); time.sleep(1)',
                               replace(Limits(), storage_bytes=1000))
        self.assertEqual(result.category, 'storage-limit')

    def test_file_count_limit(self):
        result = self.run_code('from pathlib import Path; import time; [Path(str(i)).touch() for i in range(10)]; time.sleep(1)',
                               replace(Limits(), files=3))
        self.assertEqual(result.category, 'storage-limit')

    def test_symlink_is_rejected_without_following(self):
        (self.work / 'escape').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError, 'unsafe-output'):
            storage_usage(self.work, Limits())

    def test_pipe_holding_descendant_is_cleaned(self):
        result = self.run_code('import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(10)"])',
                               replace(Limits(), wall_seconds=1))
        self.assertLess(result.wall_seconds, 2)
        self.assertEqual(result.category, 'passed')

    def test_environment_is_not_inherited(self):
        os.environ['NF_TEST_SECRET'] = 'must-not-inherit'
        self.addCleanup(os.environ.pop, 'NF_TEST_SECRET', None)
        result = self.run_code('import os; assert "NF_TEST_SECRET" not in os.environ')
        self.assertEqual(result.category, 'passed')

    def test_preexisting_logs_are_not_overwritten(self):
        (self.root / 'logs').mkdir()
        with self.assertRaises(FileExistsError):
            self.run_code('print("never")')

    def test_invalid_limits_fail_before_launch(self):
        for key, value in [('wall_seconds', 0), ('poll_seconds', float('nan')),
                           ('files', 1.2), ('open_files', True), ('wall_seconds', 3601)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                replace(Limits(), **{key: value}).validate()

    def test_socket_namespace_and_alternate_abi_filter(self):
        blob = socket_filter()
        for syscall in DENIED:
            self.assertEqual(evaluate(blob, syscall), ERRNO_EPERM)
        for syscall in [0, 1, 2, 3, 9, 59, 60, 231, 56, 57, 58, 435]:
            self.assertEqual(evaluate(blob, syscall), ALLOW)
        for arch in [0, 0x40000003, 0xc00000b7]:
            self.assertEqual(evaluate(blob, 0, arch), KILL)
        for syscall in [0x40000000, 0x40000029, 0xffffffff]:
            self.assertEqual(evaluate(blob, syscall), KILL)

    def test_runtime_inventory_binds_extra_files_and_symlinks(self):
        environment = ReferenceEnvironment.__new__(ReferenceEnvironment)
        environment.mounts = {'/reference': self.work}
        environment.bwrap = sys.executable
        (self.work / 'wrapper').write_text('first')
        before = environment._runtime_inventory()
        (self.work / 'wrapper').write_text('second')
        self.assertNotEqual(before, environment._runtime_inventory())
        (self.work / 'link').symlink_to('/outside/not-followed')
        inventory = environment._runtime_inventory()
        self.assertEqual(inventory['/reference/link'],
                         {'kind': 'symlink', 'target': '/outside/not-followed'})
        self.assertIn('sha256', inventory['host:bwrap'])

    def test_mutated_runtime_fails_before_output_or_process(self):
        environment = ReferenceEnvironment.__new__(ReferenceEnvironment)
        environment.mounts = {'/reference': self.work}
        environment.bwrap = sys.executable
        environment.runtime_inventory = environment._runtime_inventory()
        (self.work / 'unexpected.py').write_text('changed')
        target = self.root / 'must-not-exist'
        with self.assertRaisesRegex(ValueError, 'mounted runtime/source bytes changed'):
            environment.run(['/never-launched'], target)
        self.assertFalse(target.exists())

    def test_portable_source_lock_has_exact_complete_roster(self):
        data = json.loads((ROOT / 'toolchains/reference/sources.json').read_text())
        self.assertEqual(len(data['debian_packages']), 4)
        self.assertEqual(len(data['python_packages']), 80)
        self.assertEqual(len({p['name'].lower() for p in data['python_packages']}), 80)
        for entry in data['debian_packages'] + data['python_packages']:
            self.assertRegex(entry.get('sha256', entry.get('prepared_wheel_sha256')), r'^[0-9a-f]{64}$')
            self.assertNotIn('/', entry['filename'])
        serialized = json.dumps(data)
        for private in ['/workspace/', '/home/', '/tmp/', '/opt/codex']:
            self.assertNotIn(private, serialized)
        self.assertIsNone(data['platform']['qualified_ci_image'])


if __name__ == '__main__':
    unittest.main()
