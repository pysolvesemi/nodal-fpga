"""Summary-only receipt cases; real temporary commits and an executed tiny check.

These are validator fixtures, never qualification receipts for the project.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_evidence as retained

roadmap = retained.roadmap


class SummaryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        retained.EvidenceTests.setUpClass.__func__(cls)
        retained.git(cls.base, 'checkout', '--detach', cls.commit)
        assert retained.git(cls.base, 'status', '--porcelain') == ''
        cls.command = [sys.executable, '-c', "from pathlib import Path; assert Path('witness.txt').read_text() == 'fixture-witness\\n'"]
        cls.execution = subprocess.run(cls.command, cwd=cls.base, capture_output=True, text=True)
        assert cls.execution.returncode == 0, cls.execution.stderr
        retained.git(cls.base, 'checkout', 'target')

    @classmethod
    def tearDownClass(cls):
        cls.cache.cleanup()

    def setUp(self):
        retained.EvidenceTests.setUp(self)
        raw = (retained.FIXTURES / 'summary.json').read_text()
        for name, value in {'COMMIT': self.commit, 'TREE': self.tree,
                            'REPORT_HASH': hashlib.sha256(self.report.read_bytes()).hexdigest()}.items():
            raw = raw.replace('@' + name + '@', value)
        self.data = json.loads(raw)
        (self.root / 'source.json').unlink()

    check = retained.EvidenceTests.check
    reject = retained.EvidenceTests.reject

    def mutate(self, path, value):
        data = copy.deepcopy(self.data)
        target = data
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        return data

    def test_execution_needs_only_concise_report_no_logs_or_source_record(self):
        self.assertEqual(self.execution.returncode, 0)
        self.assertEqual(set(self.data['artifacts']), {'docs/completion/FND-01.md'})
        self.assertFalse((self.root / 'source.json').exists())
        self.check(expected_sources={'FND-01': self.commit})

    def test_format_is_explicit_and_v1_cannot_silently_opt_out(self):
        for path, value in [(('format_version',), True), (('format_version',), 2.0), (('format_version',), 1),
                            (('format_version',), 3), (('evidence_mode',), 'retained'),
                            (('increment',), 'FND-02'), (('status',), 'complete'),
                            (('candidate',), self.data['source'])]:
            with self.subTest(path=path, value=value):
                self.reject('RM-EVIDENCE-FORMAT', data=self.mutate(path, value))
        data = copy.deepcopy(self.data); del data['evidence_mode']
        self.reject('RM-EVIDENCE-FORMAT', data=data)

    def test_old_retained_receipt_still_requires_raw_source_record(self):
        raw = json.loads((retained.FIXTURES / 'base.json').read_text())
        self.assertIn('source_record', raw['observations']['run'])
        self.assertNotIn('evidence_mode', raw)
        data = copy.deepcopy(self.data)
        data['format_version'] = 1; del data['evidence_mode']
        self.reject('RM-EVIDENCE-FORMAT', data=data)

    def test_incomplete_failed_skipped_or_fabricated_checkbox_is_rejected(self):
        replacements = [
            (('observations', 'run', 'executed'), False),
            (('observations', 'run', 'executed'), 1),
            (('observations', 'run', 'exit_code'), False),
            (('observations', 'run', 'exit_code'), 1),
            (('observations', 'run', 'command'), '  '),
            (('observations', 'run', 'checks'), {'done': True}),
        ]
        for name in ['required', 'executed', 'passed']:
            for value in [0, -1, True, '1', 1.0, 2]:
                replacements.append((('observations', 'run', 'checks', name), value))
        for name in ['failed', 'skipped']:
            for value in [1, -1, False, '0']:
                replacements.append((('observations', 'run', 'checks', name), value))
        for value in ['failed', 'timeout', 'skipped', 'not-run', 'N/A', 'partial']:
            replacements.append((('observations', 'run', 'result'), value))
        for path, value in replacements:
            with self.subTest(path=path, value=value):
                self.reject('RM-EVIDENCE-EXECUTION', data=self.mutate(path, value))

    def test_shape_observer_outcome_and_limit_guards(self):
        for path, value in [
            (('observations', 'run', 'summary'), ''),
            (('observations', 'run', 'observer'), ' '),
            (('observations', 'run', 'observer'), ' fixture-executor'),
            (('observations', 'run', 'limitations'), []),
            (('observations', 'run', 'limitations'), [' ']),
            (('observations', 'run', 'source_record'), '/private/source.json'),
            (('observations', 'run', 'hostname'), 'private-host'),
            (('observations', 'run'), True),
        ]:
            with self.subTest(path=path, value=value):
                self.reject('RM-EVIDENCE-FORMAT', data=self.mutate(path, value))
        self.reject('RM-EVIDENCE-MISSING', data=self.mutate(('observations',), {}))

    def test_dirty_or_stale_execution_review_and_source_do_not_qualify(self):
        for value in [True, None, 0, 'false']:
            with self.subTest(dirty=value):
                self.reject('RM-EVIDENCE-SOURCE', data=self.mutate(('observations', 'run', 'dirty'), value))
        for path in [('source', 'tree'), ('observations', 'run', 'source', 'commit'),
                     ('review', 'source', 'commit')]:
            with self.subTest(path=path):
                self.reject('RM-EVIDENCE-SOURCE', data=self.mutate(path, self.target))
        for commit in ['0' * 40, self.tree]:
            self.reject('RM-EVIDENCE-SOURCE', data=self.mutate(('source', 'commit'), commit))
        self.reject('RM-EVIDENCE-SOURCE', expected_sources={'FND-01': self.target})
        self.reject('RM-EVIDENCE-PROFILE', data=self.mutate(('observations', 'run', 'profile'), 'wrong/2'))

    def test_review_cannot_replace_required_execution_or_source_check(self):
        self.reject('RM-EVIDENCE-EXECUTION', data=self.mutate(('items', 'FND-01.a'), ['review']))
        data = copy.deepcopy(self.data)
        del data['observations']['run']; data['items']['FND-01.a'] = ['review']
        data['review']['observations'] = ['review']
        self.reject('RM-EVIDENCE-EXECUTION', data=data)

    def test_independent_review_identity_coverage_and_dimensions(self):
        replacements = [
            (('review',), {}), (('review', 'identity'), 'fixture-author'),
            (('review', 'identity'), 'fixture-author '),
            (('review', 'identity'), ' '), (('review', 'authors'), []),
            (('review', 'authors'), [' ']), (('review', 'authors'), ['a', 'a']),
            (('review', 'kind'), 'automatic-pass'), (('review', 'result'), 'pending'),
            (('review', 'limitations'), [' ']),
            (('review', 'observations'), ['run']),
            (('review', 'observations'), ['run', 'review', 'unknown']),
            (('review', 'observations'), ['run', 'review', 'review']),
            (('review', 'dimensions'), {}),
        ]
        for dimension in ['architecture', 'independence', 'quality']:
            replacements += [(('review', 'dimensions', dimension, 'result'), 'pending'),
                             (('review', 'dimensions', dimension, 'summary'), ' ')]
        for path, value in replacements:
            with self.subTest(path=path, value=value):
                self.reject('RM-EVIDENCE-REVIEW', data=self.mutate(path, value))

    def test_item_references_cannot_be_missing_unknown_or_duplicated(self):
        for value in [[], ['missing'], ['run', 'run']]:
            self.reject('RM-EVIDENCE-MISSING', data=self.mutate(('items', 'FND-01.a'), value))
        self.reject('RM-EVIDENCE-MISSING', data=self.mutate(('items',), {}))
        self.reject('RM-EVIDENCE-ITEM', data=self.mutate(('items', 'FND-99.a'), ['run']))

    def test_artifact_observation_requires_an_actual_hashed_deliverable(self):
        self.data['observations']['artifact'] = dict(self.data['observations']['review'],
            kind='artifact', result='inspected', artifacts=['witness.txt'])
        self.data['review']['observations'].append('artifact')
        self.reject('RM-EVIDENCE-MISSING')
        self.data['artifacts']['witness.txt'] = hashlib.sha256((self.root / 'witness.txt').read_bytes()).hexdigest()
        self.check()
        self.reject('RM-EVIDENCE-MISSING', data=self.mutate(('observations', 'artifact', 'artifacts'), [self.data['report']]))
        (self.root / 'witness.txt').write_text('tampered\n')
        self.reject('RM-EVIDENCE-HASH')

    def test_report_hash_and_profile_are_still_required(self):
        self.report.write_text(self.report.read_text() + 'unreviewed change\n')
        self.reject('RM-EVIDENCE-HASH')
        self.data['artifacts'][self.data['report']] = hashlib.sha256(self.report.read_bytes()).hexdigest()
        self.reject('RM-EVIDENCE-PROFILE', markdown=self.markdown.replace('fixture/1', 'other/2'))

    def merged(self):
        self.data['integration'] = {'state': 'merged', 'commit': self.merge, 'tree': self.tree,
                                    'parents': [self.target, self.commit]}
        self.data['ci']['post_merge']['state'] = 'skipped'
        self.data['items']['FND-01.e'] = ['review']

    def test_real_merge_allows_closure_and_partial_work_stays_partial(self):
        parsed = self.check()
        self.assertFalse(parsed.nodes['FND-01'].checked)
        self.merged()
        self.check(markdown=self.markdown.replace('[ ]', '[x]'))

    def test_closed_root_or_closure_without_merge_is_rejected(self):
        self.data['items']['FND-01.e'] = ['review']
        for md in [self.markdown.replace('[ ]', '[x]'),
                   self.markdown.replace('[ ] FND-01.e', '[x] FND-01.e')]:
            with self.subTest(markdown=md):
                self.reject('RM-EVIDENCE-INTEGRATION', markdown=md)

    def test_merge_must_be_actual_source_parent_equal_tree_ancestor(self):
        self.merged()
        self.reject('RM-EVIDENCE-INTEGRATION', data=self.mutate(('integration', 'parents'), [self.commit, self.target]))
        self.reject('RM-EVIDENCE-SOURCE', data=self.mutate(('integration', 'tree'), '0' * 40))
        self.reject('RM-EVIDENCE-INTEGRATION', data=self.mutate(('integration', 'commit'), self.commit))
        retained.git(self.root, 'checkout', '--detach', self.commit)
        self.reject('RM-EVIDENCE-SOURCE')

    def test_real_merge_with_untested_tree_changes_cannot_count(self):
        self.merged()
        (self.root / 'unqualified.txt').write_text('unqualified merge resolution\n')
        retained.git(self.root, 'add', 'unqualified.txt')
        retained.git(self.root, 'commit', '--amend', '-m', 'fixture merge with untested resolution')
        self.data['integration']['commit'] = retained.git(self.root, 'rev-parse', 'HEAD')
        self.data['integration']['tree'] = retained.git(self.root, 'rev-parse', 'HEAD^{tree}')
        self.reject('RM-EVIDENCE-INTEGRATION')

    def test_summary_cannot_claim_post_merge_suppression_or_fake_ci_run(self):
        self.reject('RM-EVIDENCE-CI', data=self.mutate(('ci', 'post_merge', 'state'), 'skipped'))
        post = {'state': 'executed', 'reason': 'Unintegrated fixture cannot claim post-merge checks.',
                'runs': ['https://invalid.example/post-merge-run']}
        self.reject('RM-EVIDENCE-CI', data=self.mutate(('ci', 'post_merge'), post))
        self.reject('RM-EVIDENCE-CI', data=self.mutate(('ci', 'qualification'), 'executed'))
        self.reject('RM-EVIDENCE-CI', data=self.mutate(('ci', 'runs'), ['https://invalid.example/run']))
        self.reject('RM-EVIDENCE-CI', data=self.mutate(('ci', 'reason'), ' '))

    def test_summary_mode_does_not_waive_documentation_source_anchor(self):
        path = self.root / 'tools/changed.py'; path.parent.mkdir()
        path.write_text('print("qualification input changed")\n')
        retained.git(self.root, 'add', 'tools/changed.py')
        retained.git(self.root, 'commit', '-m', 'changed qualification input')
        candidate = retained.git(self.root, 'rev-parse', 'HEAD')
        with self.assertRaises(roadmap.RoadmapError) as caught:
            roadmap.verify_source_anchor(self.root, self.commit, candidate)
        self.assertEqual(caught.exception.code, 'RM-SOURCE-ANCHOR')
