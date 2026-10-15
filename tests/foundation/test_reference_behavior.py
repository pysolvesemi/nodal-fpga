"""Parser/plan source tests only. Never invokes a reference executable."""
import importlib.util
from pathlib import Path
import tempfile
import json
import unittest

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/'verify/fixtures/fnd-06/behavior.py'
spec=importlib.util.spec_from_file_location('reference_behavior',PATH)
behavior=importlib.util.module_from_spec(spec)
spec.loader.exec_module(behavior)

class ReferenceBehaviorTests(unittest.TestCase):
    def test_exact_records_required(self):
        output='OBS\ta\t01\t01\t10\nDONE\t1\n'
        self.assertEqual(behavior.parse_simulation(output,['a'],{'a':1})[0]['observed'],1)
        for bad in [output.replace('01\t01','01\t00'),output.replace('01\t01','01\tx'),
                    output.replace('DONE\t1','DONE\t0'),output+output,output.replace('a\t','b\t')]:
            with self.assertRaises(behavior.BehaviorError): behavior.parse_simulation(bad,['a'],{'a':1})
        with self.assertRaises(behavior.BehaviorError): behavior.parse_simulation('DONE\t0\n',[])

    def test_source_serialization_has_physical_writes_and_exact_instance_ids(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'tb.sv'
            for shape,tiles in [('one',1),('square',4),('odd',6),('sparse',6)]:
                ids=behavior.write_simulation(shape,path)
                source=path.read_text()
                core=[x for x in ids if x.startswith(('LOCAL-A6D3/','SECONDARY-A6D3/','REG-R','FF0-STATE-R'))]
                self.assertEqual(len(core),tiles*60)
                self.assertIn('FrameStrobe[column*20]=1',source)
                self.assertNotIn('force ',source)
                self.assertNotIn('EMULATION',source)
                self.assertIn('Inst_L_LUT4c_frame_config_dffesr.LUT_flop',source)
                self.assertEqual(len(set(ids)),len(ids))

    def test_unit_literal_denominators(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tb.sv'
            ids=behavior.write_lut_unit(p)
            self.assertEqual(sum(x.startswith('UNIT-LUT/') for x in ids),288)
            self.assertEqual(sum(x.startswith('UNIT-REG/') for x in ids),28)
            for variant in ['NF_SINGLE','NF_LEFT','NF_MID','NF_RIGHT']:
                ids=behavior.write_units(variant,p)
                self.assertEqual(sum(x.startswith('UNIT-CONFIG/') for x in ids),40)
                self.assertEqual(sum(x.startswith('UNIT-CONFIG-HOLD/') for x in ids),20)
                self.assertEqual(sum(x.startswith('UNIT-CONFIG-TRANSPARENT/') for x in ids),20)
                self.assertEqual(sum(x.startswith('UNIT-CONFIG-PAD-FRAME/') for x in ids),19)
                self.assertEqual(sum(x.startswith('UNIT-CONFIG-PAD-DATA/') for x in ids),12)

    def test_formal_counts_and_guards(self):
        plans=[behavior.formal_plan(t,[], '/work/result.smt2') for t in behavior.FORMAL_TOPS if not t.endswith('control')]
        self.assertEqual(len(plans),6)
        self.assertEqual(sum(x['assertions'] for x in plans),7)
        self.assertEqual(sum(x['assumptions'] for x in plans),1)
        self.assertEqual(sum(x['covers'] for x in plans),21)
        for p in plans:
            self.assertIn('chformal -lower',p['script'])
            self.assertIn('select -assert-none t:$check',p['script'])
            with self.assertRaises(behavior.BehaviorError): behavior.parse_formal_inventory('',p)
        with self.assertRaises(behavior.BehaviorError): behavior.formal_plan('lut',['a;bad'],'/work/a.smt2')

    def test_manifest_exact_identity_set_and_targeted_mutation(self):
        manifest=json.loads((PATH.parent/'obligations.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'tb.sv'; actual=set()
            for shape in ('one','square','odd','sparse'):
                actual.update(behavior.write_simulation(shape,path))
            actual.update(behavior.write_lut_unit(path))
            for v in ('NF_SINGLE','NF_LEFT','NF_MID','NF_RIGHT'):
                actual.update(behavior.write_units(v,path))
            expected={r['id'] for r in manifest['simulation']+manifest['supplemental_simulation']}
            self.assertEqual(actual,expected|{'M-CONFIG-CONSUMER/behavior'})
            ids=behavior.write_lut_unit(path,only_ids=['UNIT-LUT/A6D3/8'])
            self.assertEqual(ids,['UNIT-LUT/A6D3/8'])
            with self.assertRaises(behavior.BehaviorError):
                behavior.parse_simulation('OBS\tUNIT-LUT/A6D3/8\t1\t1\t10\nDONE\t1\n',ids)

    def test_cover_identity_binding_not_counts(self):
        inv=[dict(id='C-A',kind='cover',name='C_A',compiled_label='C_A',source='a.sv:2.1-2.9',top='top'),
             dict(id='C-B',kind='cover',name='C_B',compiled_label='C_B',source='a.sv:3.1-3.9',top='top')]
        text='Checking cover reachability in step 0..\nReached cover statement in step 0 at top: a.sv:2.1-2.9 (C_A)\nReached cover statement in step 0 at top: a.sv:3.1-3.9 (C_B)\nStatus: PASSED'
        self.assertEqual(len(behavior.parse_formal_result(text,0,'cover',['C-A','C-B'],inventory=inv,bound=1)),2)
        for bad in [text.replace('a.sv:3.1-3.9 (C_B)','a.sv:2.1-2.9 (C_A)'),text.replace('(C_B)','(C_UNKNOWN)'),text.replace('(C_B)','(C_B_FAKE)'),text.replace('step 0','step 1')]:
            with self.assertRaises(behavior.BehaviorError):
                behavior.parse_formal_result(bad,0,'cover',['C-A','C-B'],inventory=inv,bound=1)

    def test_false_control_exact_step_and_property(self):
        inv=[dict(id='A-CONTROL-FALSE',kind='assert',name='A_CONTROL_FALSE',source='controls.sv:3.1-3.9',top='false_control')]
        text='Checking assertions in step 0..\nAssert failed in false_control: controls.sv:3.1-3.9 (A_CONTROL_FALSE)\nStatus: FAILED'
        self.assertEqual(behavior.parse_false_control(text,1,inv)['step'],0)
        for bad in [text.replace('step 0','step 1'),text.replace('(A_CONTROL_FALSE)','(OTHER)'),text.replace('Status:', 'Checking assertions in step 1..\nStatus:')]:
            with self.assertRaises(behavior.BehaviorError): behavior.parse_false_control(bad,1,inv)

    def test_export_headers_require_real_definitions_and_membership(self):
        plan=behavior.formal_plan('false-control',[], '/work/a.smt2')
        source='formal/controls.sv:3.20-3.50'
        header='; yosys-smt2-module false_control\n; yosys-smt2-assert 0 A_CONTROL_FALSE '+source+'\n'
        definition='(define-fun |false_control_a 0| ((state |false_control_s|)) Bool false)\n'
        aggregate='(define-fun |false_control_a| ((state |false_control_s|)) Bool (|false_control_a 0| state))\n'
        assume='(define-fun |false_control_u| ((state |false_control_s|)) Bool true)\n'
        good=header+definition+aggregate+assume
        self.assertEqual(len(behavior.parse_formal_inventory(good,plan)),1)
        named=good.replace('A_CONTROL_FALSE '+source,'A_CONTROL_FALSE')
        parsed=behavior.parse_formal_inventory(named,plan)
        self.assertEqual(parsed[0]['source'],'')
        self.assertEqual(behavior._solver_description(parsed[0]),'A_CONTROL_FALSE')
        false_log='Checking assertions in step 0..\nAssert failed in false_control: A_CONTROL_FALSE\nStatus: FAILED'
        self.assertEqual(behavior.parse_false_control(false_log,1,parsed)['step'],0)
        for bad in [header,header+definition+assume,good.replace('Bool (|false_control_a 0| state)','Bool true'),good+definition,good.replace('false_control_a 0| ((state','false_control_a 1| ((state')]:
            with self.assertRaises(behavior.BehaviorError): behavior.parse_formal_inventory(bad,plan)

    def test_duplicate_export_index_and_late_overconstraint_rejected(self):
        plan={'top':'top','assertions':2,'assumptions':0,'covers':0,'properties':[
            dict(id='A',kind='assert',compiled_label='A'),dict(id='B',kind='assert',compiled_label='B')]}
        bad='; yosys-smt2-module top\n; yosys-smt2-assert 0 A a.sv:1.1-1.9\n; yosys-smt2-assert 0 B a.sv:2.1-2.9\n'
        with self.assertRaisesRegex(behavior.BehaviorError,'duplicate SMT property index'):
            behavior.parse_formal_inventory(bad,plan)
        inv=[dict(id=i,kind=k,name=n,source='s.sv:'+str(j)+'.1-'+str(j)+'.9',top='switch_SINGLE') for j,(i,k,n) in enumerate([
            ('A-MUX-ORDER/NF_SINGLE','assert','A_MUX_ORDER'),('C-MUX-LOCAL/NF_SINGLE','cover','C_MUX_LOCAL'),
            ('C-MUX-SECONDARY/NF_SINGLE','cover','C_MUX_SECONDARY'),('H-CONTROL-SELECT0','assume','H_CONTROL_SELECT0')])]
        text='Checking cover reachability in step 0..\nReached cover statement in step 0 at switch_SINGLE: s.sv:1.1-1.9 (C_MUX_LOCAL)\nUnreached cover statement at switch_SINGLE: s.sv:2.1-2.9 (C_MUX_SECONDARY)\nStatus: FAILED'
        self.assertEqual(behavior.parse_overconstraint(text,1,inv)['category'],'cover-unreachable')
        for bad in [text.replace('step 0','step 12'),text.replace('(C_MUX_LOCAL)','(OTHER)'),text+'\nAssert failed in unrelated: OTHER']:
            with self.assertRaises(behavior.BehaviorError): behavior.parse_overconstraint(bad,1,inv)

    def test_cover_and_solver_failure_never_count_as_pass(self):
        for code,text in [(1,'Status: FAILED'),(0,'timeout'),(0,'Status: PASSED')]:
            with self.assertRaises(behavior.BehaviorError): behavior.parse_formal_result(text,code,'cover',['C-a'])

if __name__=='__main__': unittest.main()
