"""Synthetic Session plumbing tests; no reference executable is launched."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import reference_behavior_execution as execution
from reference_checks import fixture_module

class FakeSession:
    def __init__(self,output):
        self.root=ROOT; self.output=output; self.calls=[]
        self.environment=SimpleNamespace(command=lambda x:x)
        self.behavior=fixture_module(ROOT,'behavior')
    def execute(self,identity,argv,*,inputs=None,expected_exit=0):
        self.calls.append((identity,list(argv),expected_exit))
        directory=self.output/identity; work=directory/'work'; work.mkdir(parents=True)
        stdout=''; stderr=''; tool=argv[0]
        if tool=='iverilog':
            tb=(inputs['/inputs/testbench']/'tb.sv').read_text()
            (work/'test.vvp').write_text('synthetic test binary')
            (work/'fake-tb.sv').write_text(tb)
        elif tool=='vvp':
            tb=(inputs['/inputs/compiled']/'fake-tb.sv').read_text()
            rows=re.findall(r'observe\("([^"]+)", (.+), 64\'h([0-9a-f]+)\);',tb)
            if 'postinit-' in identity:
                kind='X' if identity.endswith('-x') else 'Z'
                stdout=f'NONBINARY\tS-POSTINIT-{kind}\t20000\t000000000000000{kind.lower()}\nFATAL: non-binary-output\n'
            else:
                stdout=''.join(f'OBS\t{i}\t{value}\t{value}\t10000\n' for i,_,value in rows)+f'DONE\t{len(rows)}\n'
        elif tool=='yosys':
            encoded=identity.split('-formal-',1)[1].removesuffix('-export')
            logical=next(k for k in self.behavior.FORMAL_TOPS if k.replace('-','_')==encoded)
            if logical=='zero-control':
                stderr='ERROR: Assertion failed: selection contains 0 elements instead of the asserted 1: t:$assert\n'
            else:
                plan=self.behavior.formal_plan(logical,[],'/work/model.smt2')
                top=plan['top']; text=f'; yosys-smt2-module {top}\n'; counters={'assert':0,'assume':0,'cover':0}; cells={}
                for p in plan['properties']:
                    kind=p['kind']; index=counters[kind]; counters[kind]+=1
                    label=p['compiled_label']; src=f"/source/verify/fixtures/fnd-06/{p['source_file']}:{p['source_line']}.1-{p['source_line']}.99"
                    letter={'assert':'a','assume':'u','cover':'c'}[kind]
                    text+=f'; yosys-smt2-{kind} {index} {label} {src}\n'
                    text+=f'(define-fun |{top}_{letter} {index}| ((state |{top}_s|)) Bool true)\n'
                    cells[label]={'type':'$'+kind,'attributes':{'src':src}}
                for kind,letter in [('assert','a'),('assume','u')]:
                    members=' '.join(f'(|{top}_{letter} {i}| state)' for i in range(counters[kind]))
                    expr='true' if not members else members if counters[kind]==1 else '(and '+members+')'
                    text+=f'(define-fun |{top}_{letter}| ((state |{top}_s|)) Bool {expr})\n'
                (work/'model.smt2').write_text(text)
                (work/'model.smt2.json').write_text(json.dumps({'modules':{top:{'cells':cells}}}))
                (work/'fake-plan.json').write_text(json.dumps(plan))
        elif tool=='yosys-smtbmc':
            source=inputs['/inputs/formal']; plan=json.loads((source/'fake-plan.json').read_text())
            inv=self.behavior.parse_formal_inventory((source/'model.smt2').read_text(),plan)
            cover='-c' in argv
            if cover:
                stdout='Checking cover reachability in step 0..\n'
                for p in inv:
                    if p['kind']=='cover':
                        desc=f"{p['top']}: {p['source']} ({p['name']})"
                        if plan['logical_top']=='overconstraint-control' and 'SECONDARY' in p['id']:
                            stdout+='Unreached cover statement at '+desc+'\n'
                        else: stdout+='Reached cover statement in step 0 at '+desc+'\n'
                (work/'trace0.vcd').write_text('synthetic trace')
            else:
                stdout=''.join(f'Checking assertions in step {i}..\n' for i in range(plan['bound']))
                if plan['logical_top']=='false-control':
                    p=inv[0]; stdout+=f"Assert failed in {p['top']}: {p['source']} ({p['name']})\n"
                    (work/'trace.vcd').write_text('synthetic counterexample')
            stdout+='Status: '+('FAILED' if expected_exit else 'PASSED')+'\n'
        else: raise AssertionError(tool)
        out=directory/'stdout.log'; err=directory/'stderr.log'; out.write_text(stdout);err.write_text(stderr)
        portable=dict(category='tool-error' if expected_exit else 'passed',returncode=expected_exit,
            stdout_bytes=len(out.read_bytes()),stderr_bytes=len(err.read_bytes()),
            stdout_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),stderr_sha256=hashlib.sha256(err.read_bytes()).hexdigest(),storage_bytes=1,file_count=1)
        result=SimpleNamespace(stdout_path=out,stderr_path=err,returncode=expected_exit,portable=lambda:portable)
        return result,work

class BehaviorExecutionTests(unittest.TestCase):
    def test_full_synthetic_session_exact_rosters_and_control_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory); generated={}
            for shape in ('one','square','odd','sparse'):
                path=output/('generated-'+shape); path.mkdir(); (path/'source.v').write_text('// synthetic source')
                (path/'sources.f').write_text('source.v\n'); generated[shape]=path
            session=FakeSession(output)
            result=execution.run_behavior(session,1,generated)
            self.assertEqual(len(result['simulation']),1847)
            self.assertEqual(len(result['supplemental_simulation']),36)
            self.assertEqual(len(result['formal']),29)
            self.assertEqual(len(result['controls']),3)
            self.assertEqual(len(result['negative_cases']),2)
            self.assertEqual(len(result['mutation_baselines']),1)
            canonical={s['id'] for s in result['stages'] if s['id'].startswith('SIM-')}
            self.assertEqual(canonical,{f'SIM-{s}/run-1' for s in generated})
            self.assertFalse(any('zero_control-assert' in i or 'zero_control-cover' in i for i,_,_ in session.calls))
            self.assertTrue(all(r['executed'] and r['binding']['source_sha256'] for r in result['simulation']))

    def test_lowered_property_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'lowered.json'; p.write_text(json.dumps({'modules':{'top':{'cells':{'wrong':{'type':'$assert','attributes':{'src':'other'}}}}}}))
            prop=dict(id='A',kind='assert',name='right',source='known',compiled_label='right')
            with self.assertRaises(ValueError): execution._lowered_inventory(p,{'top':'top'},[prop])
            prop['source']=''
            p.write_text(json.dumps({'modules':{'top':{'cells':{'wrong':{'type':'$assert','attributes':{}}}}}}))
            with self.assertRaises(ValueError): execution._lowered_inventory(p,{'top':'top'},[prop])

if __name__=='__main__': unittest.main()
