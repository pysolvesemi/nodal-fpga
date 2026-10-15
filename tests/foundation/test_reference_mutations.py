"""Synthetic patch/receipt controls, never actual reference execution evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import reference_mutations as m
from reference_checks import fixture_module
from reference_results import ReferenceResultError

RTL={
'M-MUX-INDEX': 'cus_mux21 inst_cus_mux21_L_I0 (.A0(L_I0_input[0]), .A1(L_I0_input[1]), .S(select), .X(out));',
'M-LUT-BIT':'cus_mux161 inst_cus_mux161 (.A1 (LUT_values[1]), .A8 (LUT_values[8]), .X(out));',
'M-CONFIG-ADDRESS':'config_latch Inst_frame0_bit12 (.D(FrameData[12]),.E(FrameStrobe[0]),.Q(ConfigBits[0]),.QN(ConfigBits_N[0]));',
'M-PRIORITY':'always @(posedge UserCLK) begin\n if (EN) begin\n if (SR) LUT_flop <= c_reset_value;\n else LUT_flop <= LUT_out;\n end\nend',
'M-ENDPOINT-OMIT':'NF_MID Tile_X1Y0_NF_MID (.W(Tile_X0Y0_E), .UserCLK(UserCLK));',
'M-CONFIG-CONSUMER':'NF_SINGLE_switch_matrix Inst_NF_SINGLE_switch_matrix (.ConfigBits(ConfigBits[20-1:19]), .ConfigBits_N(ConfigBits_N[20-1:19]));',
}

class MutationControls(unittest.TestCase):
    def test_frozen_roster(self):
        rows,sha=m.manifest(ROOT)
        self.assertEqual(tuple(rows),m.IDS)
        self.assertEqual(len(sha),64)
    def test_exact_six_unique_rtl_patches(self):
        for key,text in RTL.items():
            result,span=m.patch_rtl(key,text.encode())
            self.assertNotEqual(result,text.encode())
            self.assertEqual(span['occurrences'],1)
            with self.assertRaises(ReferenceResultError): m.patch_rtl(key,(text+'\n'+text).encode())
            with self.assertRaises(ReferenceResultError): m.patch_rtl(key,result)
    def test_mux_only_order_changes(self):
        result,_=m.patch_rtl('M-MUX-INDEX',RTL['M-MUX-INDEX'].encode())
        self.assertIn(b'.A0(L_I0_input[1])',result)
        self.assertIn(b'.A1(L_I0_input[0])',result)
        self.assertIn(b'.S(select), .X(out)',result)
    def test_wrong_parent_not_patched(self):
        wrong=RTL['M-CONFIG-ADDRESS'].replace('FrameData[12]','FrameData[11]')
        with self.assertRaisesRegex(ReferenceResultError,'unexpected parent'): m.patch_rtl('M-CONFIG-ADDRESS',wrong.encode())
    def test_all_mapping_controls_detect_intended_failure(self):
        structure=fixture_module(ROOT,'structure'); rows,_=m.manifest(ROOT)
        for identifier in ('M-CORR-SWAP','M-CORR-OMIT','M-CORR-DUPLICATE','M-FIELD-ALIAS','M-ENDPOINT-REVERSE'):
            parent=structure.expected('odd')[0]['intertile_edges'] if identifier=='M-ENDPOINT-REVERSE' else structure.oracle()[1]
            baseline=copy.deepcopy(parent)
            candidate,span=m.derive_json(identifier,parent)
            self.assertEqual(parent,baseline)
            try:
                if identifier=='M-ENDPOINT-REVERSE': structure.check_declared_edges('odd',candidate)
                else: structure.check_correspondence(candidate)
            except structure.StructureError as error:
                record=m._mapping_record(error,rows[identifier],{'stage':'synthetic','executed':True})
            else: self.fail(identifier+' was not detected')
            self.assertEqual(record['diagnostic'],rows[identifier]['diagnostic'])
    def test_alias_derivative_is_explicit(self):
        baseline=m.alias_input(0)
        result,span=m.derive_json('M-ALIAS-CONFLICT',baseline)
        self.assertEqual(baseline['requests'],{'ff':0,'source':0})
        self.assertEqual(result['requests'],{'ff':0,'source':1})
        self.assertEqual(result['declarations'],baseline['declarations'])
    def test_json_binding_and_tamper(self):
        structure=fixture_module(ROOT,'structure')
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'mutant'
            binding=m.materialize(ROOT,'M-CORR-OMIT',structure.oracle()[1],out)
            self.assertNotEqual(binding['baseline_sha256'],binding['derived_sha256'])
            self.assertEqual(binding['patch_sha256'],m.digest((out/'mutation.patch').read_bytes()))
            with self.assertRaises(ReferenceResultError): m.materialize(ROOT,'M-CORR-OMIT',structure.oracle()[1],out)
            (out/'candidate.json').write_text('{}')
            with self.assertRaisesRegex(ReferenceResultError,'undeclared derivative bytes'): m.verify_derivative(out,binding)
    def test_rtl_fresh_copy_and_unchanged_roster(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'baseline'; base.mkdir(); target=m.RTL_TARGETS['M-MUX-INDEX'][1]
            path=base/target; path.parent.mkdir(parents=True); path.write_text(RTL['M-MUX-INDEX'])
            (base/'sources.f').write_text(target+'\n')
            (base/'source.v').write_text('module source; endmodule\n')
            (base/'sources.f').write_text(target+'\nsource.v\n')
            (base/'generation.json').write_text(json.dumps({'shape':'one','upstream_commit':'a'*40,'upstream_tree':'b'*40,
              'generated_rtl':[{'path':target,'sha256':m.digest(path.read_bytes())}],
              'source_rtl':[{'path':'source.v','sha256':m.digest((base/'source.v').read_bytes())}]}))
            out=Path(tmp)/'derived'; binding=m.materialize(ROOT,'M-MUX-INDEX',base,out)
            self.assertEqual(path.read_text(),RTL['M-MUX-INDEX'])
            self.assertEqual((out/'generation.json').read_bytes(),(base/'generation.json').read_bytes())
            (out/'unexpected.v').write_text('x')
            with self.assertRaisesRegex(ReferenceResultError,'undeclared derivative file'): m.verify_derivative(out,binding)
    def test_exact_negative_semantic_receipt(self):
        text='OBS\tUNIT-LUT/A6D3/1\t0001\t0000\t10\nFATAL: semantic-mismatch UNIT-LUT/A6D3/1 time=10\n'
        record=m.parse_negative(text,'UNIT-LUT/A6D3/1',1)
        self.assertEqual(record['observed'],0)
        for bad in (text.replace('0000','xxxx'),text.replace('0001','0000'),text.replace('A6D3/1','A6D3/8'),
                    text+text,text+'DONE\t1\n','compiler failed',text.replace('semantic-mismatch','some other failure')):
            with self.assertRaises(ReferenceResultError): m.parse_negative(bad,'UNIT-LUT/A6D3/1',1)
    def test_compiled_failure_requires_provenance(self):
        structure=fixture_module(ROOT,'structure'); rows,_=m.manifest(ROOT)
        error=structure.StructureError('mapping-mismatch','LINK/odd/t00.e->t10.w',
                                       diagnostic='missing-directed-edge')
        with self.assertRaisesRegex(ReferenceResultError,'lacks source attribution'):
            m._mapping_record(error,rows['M-ENDPOINT-OMIT'],{'artifact_sha256':'a'*64})
    def test_baseline_missing_blocks_before_execution(self):
        class Session:
            root=ROOT
        with self.assertRaisesRegex(ReferenceResultError,'baseline witness missing'):
            m.run_mutations(Session(),{},baseline={},alias_hook=None)

if __name__=='__main__': unittest.main()


class PublishedMutationControls(unittest.TestCase):
    def setUp(self):
        import shutil
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.fixture=self.root/'verify/fixtures/fnd-06';self.fixture.mkdir(parents=True)
        shutil.copyfile(ROOT/'verify/fixtures/fnd-06/mutations.json',self.fixture/'mutations.json')
        self.archive=self.fixture/'mutation-artifacts'
        shutil.copytree(ROOT/'verify/fixtures/fnd-06/mutation-artifacts',self.archive)
        self.inventory=json.loads((self.archive/'inventory.json').read_text())
        # Binding-only synthetic replay controls: no execution credit.
        self.results=[{'id':r['id'],'binding':{k:r[k] for k in m.PORTABLE_BINDING_FIELDS}}
                      for r in self.inventory]
    def save(self):
        (self.archive/'inventory.json').write_bytes(m.encode(self.inventory))
    def test_exact_portable_replay(self):
        self.assertEqual(m.verify_published_mutations(self.root,self.results)['mutations'],12)
    def test_missing_and_extra_patch_rejected(self):
        path=self.archive/(m.IDS[0]+'.patch');data=path.read_bytes();path.unlink()
        with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,self.results)
        path.write_bytes(data);(self.archive/'extra.patch').write_text('extra')
        with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,self.results)
    def test_missing_extra_duplicate_bindings_rejected(self):
        for results in (self.results[:-1],self.results+[self.results[0]],self.results[:-1]+[self.results[0]]):
            with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,results)
    def test_changed_fresh_binding_rejected(self):
        for key in m.PORTABLE_BINDING_FIELDS:
            results=copy.deepcopy(self.results);results[0]['binding'][key]=None
            with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,results)
    def test_patch_tampering_rejected(self):
        path=self.archive/(m.IDS[0]+'.patch');path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,self.results)
    def test_unapproved_inventory_fields_rejected(self):
        self.inventory[0]['observations']=[];self.save()
        with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,self.results)
    def test_frozen_witness_and_category_rejected(self):
        for field in ('required_failing_witnesses','expected_category','manifest_sha256'):
            original=self.inventory[0][field];self.inventory[0][field]='tampered';self.save()
            with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,self.results)
            self.inventory[0][field]=original
    def test_unsafe_path_even_with_matching_fresh_binding(self):
        for target in ('/tmp/source','../source','a/../source','a\\source','candidate.json\nextra'):
            self.inventory[0]['target']=target;self.results[0]['binding']['target']=target;self.save()
            with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,self.results)
    def test_bad_headers_even_with_matching_hash(self):
        path=self.archive/(m.IDS[0]+'.patch');patch=path.read_bytes().replace(b'--- baseline/',b'--- /absolute/',1)
        path.write_bytes(patch);sha=m.digest(patch)
        self.inventory[0]['patch_sha256']=sha;self.results[0]['binding']['patch_sha256']=sha;self.save()
        with self.assertRaisesRegex(ReferenceResultError,'headers'): m.verify_published_mutations(self.root,self.results)
    def test_symlink_patch_rejected(self):
        path=self.archive/(m.IDS[0]+'.patch');path.unlink();path.symlink_to(self.archive/(m.IDS[1]+'.patch'))
        with self.assertRaises(ReferenceResultError): m.verify_published_mutations(self.root,self.results)

    def test_duplicate_inventory_key_rejected(self):
        path=self.archive/'inventory.json'
        raw=path.read_text().replace('"id": "M-MUX-INDEX",',
                                    '"id": "M-MUX-INDEX", "id": "M-MUX-INDEX",',1)
        path.write_text(raw)
        with self.assertRaisesRegex(ReferenceResultError,'duplicate mutation inventory key'):
            m.verify_published_mutations(self.root,self.results)
