"""Hand-authored evidence cases, real temporary Git identities, no fake project runs."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import roadmap
FIXTURES = Path(__file__).parent / 'evidence_fixtures'


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = tempfile.TemporaryDirectory()
        cls.base = Path(cls.cache.name) / 'base'
        cls.base.mkdir()
        git(cls.base, 'init', '-b', 'target')
        git(cls.base, 'config', 'user.email', 'fixture@example.invalid')
        git(cls.base, 'config', 'user.name', 'Independent test fixture')
        (cls.base / 'base.txt').write_text('base\n')
        git(cls.base, 'add', '.')
        git(cls.base, 'commit', '-m', 'independent base')
        cls.target = git(cls.base, 'rev-parse', 'HEAD')
        git(cls.base, 'checkout', '-b', 'implementation')
        (cls.base / 'witness.txt').write_text('fixture-witness\n')
        git(cls.base, 'add', '.')
        git(cls.base, 'commit', '-m', 'source witness')
        cls.commit = git(cls.base, 'rev-parse', 'HEAD')
        cls.tree = git(cls.base, 'rev-parse', 'HEAD^{tree}')
        git(cls.base, 'checkout', 'target')
        git(cls.base, 'merge', '--no-ff', 'implementation', '-m', 'actual fixture merge [skip ci]')
        cls.merge = git(cls.base, 'rev-parse', 'HEAD')

    @classmethod
    def tearDownClass(cls):
        cls.cache.cleanup()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'repo'
        shutil.copytree(self.base, self.root)
        (self.root / 'docs/completion').mkdir(parents=True)
        self.report = self.root / 'docs/completion/FND-01.md'
        self.report.write_text(f'# Test-only evidence\n{self.commit}\n{self.tree}\n[metadata](FND-01.evidence.json)\n')
        (self.root / 'source.json').write_text(json.dumps({'head':self.commit,'tree':self.tree,'dirty':False,'profile':'fixture/1'}))
        raw = (FIXTURES / 'base.json').read_text()
        for key, value in {'COMMIT':self.commit, 'TREE':self.tree,
                           'SOURCE_HASH':hashlib.sha256((self.root/'source.json').read_bytes()).hexdigest(),
                           'REPORT_HASH':hashlib.sha256(self.report.read_bytes()).hexdigest(),
                           'WITNESS_HASH':hashlib.sha256((self.root/'witness.txt').read_bytes()).hexdigest()}.items():
            raw = raw.replace('@'+key+'@', value)
        self.data = json.loads(raw)
        self.markdown = (FIXTURES / 'partial.md').read_text()

    def check(self, data=None, markdown=None, **kwargs):
        (self.root / 'docs/completion/FND-01.evidence.json').write_text(json.dumps(self.data if data is None else data))
        parsed = roadmap.parse_documents({'fixture.md':self.markdown if markdown is None else markdown})
        roadmap.validate(parsed, self.root, **kwargs)
        return parsed

    def reject(self, code, **kwargs):
        with self.assertRaises(roadmap.RoadmapError) as caught:
            self.check(**kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_positive_partial_execution(self):
        parsed = self.check(expected_sources={'FND-01':self.commit})
        self.assertFalse(parsed.nodes['FND-01'].checked)
        self.assertTrue(parsed.nodes['FND-01.a'].checked)

    def test_hand_authored_negative_evidence(self):
        for case in json.loads((FIXTURES/'rejections.json').read_text()):
            with self.subTest(case=case['name']):
                data = copy.deepcopy(self.data)
                target = data
                for key in case['path'][:-1]:
                    target = target[key]
                target[case['path'][-1]] = case['value']
                self.reject(case['code'], data=data)

    def test_actual_closed_increment(self):
        self.data['items']['FND-01.e'] = ['review']
        self.data['integration'] = {'state':'merged','commit':self.merge,'tree':self.tree,'parents':[self.target,self.commit]}
        self.data['ci']['post_merge']['state'] = 'skipped'
        self.check(markdown=self.markdown.replace('[ ]','[x]'))

    def test_closed_increment_cannot_use_pending_merge(self):
        self.data['items']['FND-01.e'] = ['review']
        self.reject('RM-EVIDENCE-INTEGRATION', markdown=self.markdown.replace('[ ]','[x]'))

    def test_reopened_regression_retains_immutable_old_receipt_without_credit(self):
        parsed = self.check(markdown=self.markdown.replace('[x]','[ ]'))
        self.assertFalse(any(node.checked for node in parsed.nodes.values()))

    def test_reopened_leaf_does_not_invalidate_other_checked_leaf(self):
        md = self.markdown.replace('  - [ ] FND-01.e', '  - [x] FND-01.b Accepted unaffected review.\n  - [ ] FND-01.e').replace('[x] FND-01.a','[ ] FND-01.a')
        self.data['items']['FND-01.b']=['review']
        self.check(markdown=md)

    def test_explicit_expected_candidate_rejects_stale_receipt(self):
        self.reject('RM-EVIDENCE-SOURCE', expected_sources={'FND-01':self.target})

    def test_explicit_source_expectation_checks_even_unchecked_increment(self):
        self.reject("RM-EVIDENCE-SOURCE", markdown=self.markdown.replace("[x]", "[ ]"), expected_sources={"FND-01":self.target})

    def test_unknown_source_expectation_is_not_ignored(self):
        self.reject('RM-EVIDENCE-SOURCE', expected_sources={'FND-99':self.commit})

    def test_authoritative_profile_required(self):
        self.reject('RM-EVIDENCE-PROFILE', markdown=self.markdown.replace('fixture/1','other/1'))

    def test_open_ancestor_profile_applies_to_checked_descendants(self):
        md=self.markdown.replace('; profile: fixture/1', '')
        md=md.replace('Independently authored evidence fixture','Independently authored evidence fixture <!-- profile: wrong/2 -->')
        self.reject('RM-EVIDENCE-PROFILE',markdown=md)

    def test_report_and_manifest_source_must_agree(self):
        self.report.write_text(self.report.read_text().replace(self.commit,self.target))
        self.data['artifacts']['docs/completion/FND-01.md']=hashlib.sha256(self.report.read_bytes()).hexdigest()
        self.reject('RM-EVIDENCE-SOURCE')

    def test_missing_report_link(self):
        self.report.write_text(f'{self.commit}\n{self.tree}\n')
        self.data['artifacts']['docs/completion/FND-01.md']=hashlib.sha256(self.report.read_bytes()).hexdigest()
        self.reject('RM-EVIDENCE-MISSING')

    def test_missing_artifact(self):
        (self.root/'witness.txt').unlink()
        self.reject('RM-EVIDENCE-MISSING')

    def test_escaping_artifact_path(self):
        self.data['artifacts']['../escape']='0'*64
        self.reject('RM-EVIDENCE-PATH')

    def test_symlink_escape(self):
        (self.root/'escape').symlink_to(self.root.parent)
        self.data['artifacts']['escape/anything']='0'*64
        self.reject('RM-EVIDENCE-PATH')

    def test_source_commit_cannot_be_tree_object(self):
        self.data['source']['commit']=self.tree
        self.reject('RM-EVIDENCE-SOURCE')

    def test_source_object_missing_is_explicit(self):
        self.data['source']['commit']='0'*40
        self.reject('RM-EVIDENCE-SOURCE')

    def test_stale_raw_execution_identity_cannot_be_relabelled(self):
        (self.root/'source.json').write_text(json.dumps({'head':self.target,'tree':self.tree,'dirty':False}))
        self.data['artifacts']['source.json']=hashlib.sha256((self.root/'source.json').read_bytes()).hexdigest()
        self.reject('RM-EVIDENCE-SOURCE')

    def test_dirty_execution_cannot_qualify(self):
        (self.root/'source.json').write_text(json.dumps({'head':self.commit,'tree':self.tree,'dirty':True}))
        self.data['artifacts']['source.json']=hashlib.sha256((self.root/'source.json').read_bytes()).hexdigest()
        self.reject('RM-EVIDENCE-SOURCE')

    def test_duplicate_json_keys(self):
        path=self.root/'duplicate.json';path.write_text('{"a": 1, "a": 2}')
        with self.assertRaises(roadmap.RoadmapError) as caught:roadmap.read_json(path)
        self.assertEqual(caught.exception.code,'RM-EVIDENCE-FORMAT')

    def test_merge_parent_mismatch(self):
        self.data['integration']={'state':'merged','commit':self.merge,'tree':self.tree,'parents':[self.commit,self.target]}
        self.reject('RM-EVIDENCE-INTEGRATION')

    def test_prospective_unintegrated_merge_cannot_count(self):
        self.data['integration']={'state':'merged','commit':self.merge,'tree':self.tree,'parents':[self.target,self.commit]}
        git(self.root,'checkout','--detach',self.commit)
        self.reject('RM-EVIDENCE-SOURCE')

    def test_derived_json_cannot_be_edited_as_status(self):
        parsed=self.check();path=self.root/'status.json'
        path.write_text(roadmap.render(parsed));roadmap.verify_derived(parsed,path)
        path.write_text(path.read_text().replace('"checked": true','"checked": false'))
        with self.assertRaises(roadmap.RoadmapError) as caught:roadmap.verify_derived(parsed,path)
        self.assertEqual(caught.exception.code,'RM-DERIVED-CONFLICT')

    def test_derived_writer_cannot_overwrite_authoritative_inputs(self):
        parsed=self.check()
        for target in ['docs/roadmap/tracks/00-foundation.md','docs/completion/FND-01.evidence.json','tools/ownership.json']:
            with self.subTest(target=target):
                with self.assertRaises(roadmap.RoadmapError) as caught:
                    roadmap.write_view(parsed,self.root,self.root/target)
                self.assertEqual(caught.exception.code,'RM-DERIVED-PATH')
        (self.root/'artifacts').mkdir()
        roadmap.write_view(parsed,self.root,self.root/'artifacts/view.json')
        roadmap.verify_derived(parsed,self.root/'artifacts/view.json')

    def test_manifest_is_bounded_before_json_parse(self):
        self.check()
        with patch.object(roadmap, 'JSON_BYTES', 8):
            self.reject('RM-LIMIT')

    def test_artifact_bytes_are_bounded(self):
        with patch.object(roadmap, 'ARTIFACT_BYTES', 8):
            self.reject('RM-LIMIT')

    def test_total_artifact_bytes_are_bounded(self):
        with patch.object(roadmap, 'TOTAL_ARTIFACT_BYTES', 8):
            self.reject('RM-LIMIT')

    def test_wrong_metadata_types_report_structured_diagnostics(self):
        for field, value in [('observations', []), ('items', []), ('source', []), ('review', None), ('ci', None)]:
            with self.subTest(field=field):
                data=copy.deepcopy(self.data);data[field]=value
                expected='RM-EVIDENCE-MISSING' if field=='observations' else ('RM-EVIDENCE-SOURCE' if field=='source' else 'RM-EVIDENCE-FORMAT')
                self.reject(expected,data=data)

    def test_real_roadmap_and_historical_profiles(self):
        result=roadmap.check(ROOT)
        self.assertEqual((result['increments'],result['nodes']),(82,648))
        self.assertGreaterEqual(result['checked_increments'],2)
        first=roadmap.read_json(ROOT/'docs/completion/FND-01.evidence.json')
        second=roadmap.read_json(ROOT/'docs/completion/FND-02.evidence.json')
        self.assertEqual(first['ci']['qualification'],'executed')
        self.assertEqual(second['ci']['qualification'],'not-run')


class SourceAnchorTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        git(self.root,'init','-b','candidate')
        git(self.root,'config','user.email','fixture@example.invalid')
        git(self.root,'config','user.name','Source anchor fixture')
        self.path='docs/roadmap/tracks/00-foundation.md'
        (self.root/Path(self.path).parent).mkdir(parents=True)
        self.original='- [ ] FND-01 Work.\n  Depends on: none.\n  - [ ] FND-01.a Run. <!-- requires: execution; profile: fixture/1 -->\n  - [ ] FND-01.e Close.\n'
        (self.root/self.path).write_text(self.original)
        (self.root/'code.py').write_text('print(1)\n')
        git(self.root,'add','.');git(self.root,'commit','-m','tested source')
        self.source=git(self.root,'rev-parse','HEAD')

    def candidate(self,path,text):
        target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
        git(self.root,'add','.');git(self.root,'commit','-m','candidate')
        return git(self.root,'rev-parse','HEAD')

    def test_status_and_evidence_link_only_anchor_is_accepted(self):
        candidate=self.candidate(self.path,self.original.replace('[ ]','[x]')+'  Evidence: retained report.\n')
        roadmap.verify_source_anchor(self.root,self.source,candidate)

    def test_completion_evidence_only_anchor_is_accepted(self):
        candidate=self.candidate('docs/completion/FND-01.md','Actual report, separately checked.\n')
        roadmap.verify_source_anchor(self.root,self.source,candidate)

    def test_qualification_contract_changes_need_fresh_execution(self):
        for old,new in [('execution','review'),('fixture/1','other/1'),('none.','FND-02.'),('Run.','Waive run.')]:
            with self.subTest(change=new):
                candidate=self.candidate(self.path,self.original.replace(old,new))
                with self.assertRaises(roadmap.RoadmapError) as caught:
                    roadmap.verify_source_anchor(self.root,self.source,candidate)
                self.assertEqual(caught.exception.code,'RM-SOURCE-ANCHOR')

    def test_implementation_change_needs_fresh_execution(self):
        candidate=self.candidate('code.py','print(2)\n')
        with self.assertRaises(roadmap.RoadmapError) as caught:
            roadmap.verify_source_anchor(self.root,self.source,candidate)
        self.assertEqual(caught.exception.code,'RM-SOURCE-ANCHOR')

    def test_workflow_change_needs_fresh_execution(self):
        candidate=self.candidate('.github/workflows/check.yml','new qualification contract\n')
        with self.assertRaises(roadmap.RoadmapError) as caught:
            roadmap.verify_source_anchor(self.root,self.source,candidate)
        self.assertEqual(caught.exception.code,'RM-SOURCE-ANCHOR')
