"""Synthetic JSON controls only: no generator, Yosys, or RTL execution credit."""
import copy
import importlib.util
from pathlib import Path
import unittest
import tempfile
import hashlib

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('fnd06_structure', ROOT/'verify/fixtures/fnd-06/structure.py')
s = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s)

class Module:
    def __init__(self):
        self.value = {'ports':{},'netnames':{},'cells':{},'parameter_default_values':{}}
        self.next = 2
    def net(self, name, width=1, direction=None, bits=None):
        if bits is None:
            bits = list(range(self.next,self.next+width))
            self.next += width
        self.value['netnames'][name] = {'bits':bits}
        if direction:
            self.value['ports'][name] = {'direction':direction,'bits':bits}
        return bits
    def cell(self, name, typ, connections, directions, parameters=None):
        self.value['cells'][name] = {'type':typ,'connections':connections,
                                    'port_directions':directions,'parameters':parameters or {}}
    def instantiate(self, name, typ, module, connections):
        self.cell(name, typ, connections, {k:v['direction'] for k,v in module.value['ports'].items()})

def synthetic_one():
    """Manually wired single-tile transport/control specimen, not reference RTL."""
    latch = Module()
    for p,d in [('D','input'),('E','input'),('Q','output'),('QN','output')]:
        latch.net(p,direction=d)
    n=latch.net('not_d')
    latch.cell('invert','$not',{'A':latch.value['ports']['D']['bits'],'Y':n},{'A':'input','Y':'output'})
    for out,db in [('Q',latch.value['ports']['D']['bits']),('QN',n)]:
        latch.cell('latch_'+out,'$dlatch',{'D':db,'EN':latch.value['ports']['E']['bits'],
                   'Q':latch.value['ports'][out]['bits']},{'D':'input','EN':'input','Q':'output'},{'EN_POLARITY':'1'})
    mux = Module()
    for p,d in [('A0','input'),('A1','input'),('S','input'),('X','output')]:
        mux.net(p,direction=d)
    lut = Module()
    for p,d,w in [('I','input',4),('O','output',1),('Ci','input',1),('Co','output',1),
                  ('SR','input',1),('EN','input',1),('UserCLK','input',1),('ConfigBits','input',19)]:
        lut.net(p,w,d)
    q = lut.net('LUT_flop')
    lut_out=lut.net('LUT_out'); reset=lut.net('reset_mux'); enabled=lut.net('enable_mux')
    lut.cell('reset','$mux',{'A':lut_out,'B':lut.value['ports']['ConfigBits']['bits'][18:19],
             'S':lut.value['ports']['SR']['bits'],'Y':reset},{'A':'input','B':'input','S':'input','Y':'output'})
    lut.cell('enable','$mux',{'A':q,'B':reset,'S':lut.value['ports']['EN']['bits'],'Y':enabled},
             {'A':'input','B':'input','S':'input','Y':'output'})
    lut.cell('$procdff$1','$dff',{'Q':q,'D':enabled,
                               'CLK':lut.value['ports']['UserCLK']['bits']},
             {'Q':'output','D':'input','CLK':'input'},{'CLK_POLARITY':'1','WIDTH':'1'})
    mux16 = Module()
    lut.instantiate('cus_mux21_I0mux','cus_mux21',mux,
                    {p:lut.net('carry_mux_'+p) for p in mux.value['ports']})
    lut.instantiate('cus_mux21_O','cus_mux21',mux,
                    {p:lut.net('output_mux_'+p) for p in mux.value['ports']})
    lut.instantiate('inst_cus_mux161','cus_mux161',mux16,{})
    for typ,count in [('$not',4),('$and',3),('$or',2)]:
        for j in range(count):
            lut.cell(typ+str(j),typ,{'A':lut.net(typ+'a'+str(j)),'Y':lut.net(typ+'y'+str(j))},
                     {'A':'input','Y':'output'})
    io = Module()
    for a,b in [('A0','X0'),('A1','X1'),('A2','X2'),('A3','X3'),('ALT','XA'),('ENABLE','XE'),('RESET','XR'),('RESULT','Y')]:
        bits=io.net(a,direction='input')
        io.net(b,direction='output',bits=bits)
    mem = Module()
    fd=mem.net('FrameData',32,'input'); fs=mem.net('FrameStrobe',20,'input')
    qb=mem.net('ConfigBits',20,'output'); qn=mem.net('ConfigBits_N',20,'output')
    for j in range(20):
        mem.instantiate('Inst_frame0_bit'+str(12+j),'config_latch',latch,
                        {'D':[fd[12+j]],'E':[fs[0]],'Q':[qb[j]],'QN':[qn[j]]})
    sw = Module()
    sw.value['parameter_default_values'].update(GND0='0',GND='0',VCC0='1',VCC='1',VDD0='1',VDD='1')
    for p in ('P_X0','P_X1','P_X2','P_X3','P_XA','P_XE','P_XR','L_O','L_Co'):
        sw.net(p,direction='input')
    for out,src in [('L_I1','P_X1'),('L_I2','P_X2'),('L_I3','P_X3'),('L_EN','P_XE'),('L_SR','P_XR'),('P_RESULT','L_O')]:
        sw.net(out,direction='output',bits=sw.value['ports'][src]['bits'])
    sw.net('L_Ci',direction='output',bits=['0'])
    sw.net('L_I0',direction='output')
    sw.net('ConfigBits',direction='input'); sw.net('ConfigBits_N',direction='input')
    sw.net('L_I0_input',bits=sw.value['ports']['P_X0']['bits']+sw.value['ports']['P_XA']['bits'])
    sw.instantiate('inst_cus_mux21_L_I0','cus_mux21',mux,
                   {p:sw.value['ports'][n]['bits'] for p,n in [('A0','P_X0'),('A1','P_XA'),('S','ConfigBits'),('X','L_I0')]})
    tile = Module()
    for p in ('A0','A1','A2','A3','ALT','ENABLE','RESET'):
        tile.net('P_'+p,direction='input')
    tile.net('P_Y',direction='output')
    for p,w in [('UserCLK',1),('FrameData',32),('FrameStrobe',20)]:
        bits=tile.net(p,w,'input')
        tile.net(p+'o' if p=='UserCLK' else p+'_O',w,'output',bits)
    qb=tile.net('ConfigBits',20); qn=tile.net('ConfigBits_N',20)
    for alias,src in [('X0','A0'),('X1','A1'),('X2','A2'),('X3','A3'),('XA','ALT'),('XE','ENABLE'),('XR','RESET'),('RESULT','Y')]:
        tile.net('P_'+alias,bits=tile.value['ports']['P_'+src]['bits'])
    for p in ('L_I0','L_Co'):
        tile.net(p)
    for a,b in [('L_I1','P_A1'),('L_I2','P_A2'),('L_I3','P_A3'),('L_EN','P_ENABLE'),('L_SR','P_RESET'),('L_O','P_Y')]:
        tile.net(a,bits=tile.value['ports'][b]['bits'])
    tile.net('L_Ci',bits=['0'])
    nets=tile.value['netnames']
    tile.instantiate('Inst_NF_SINGLE_ConfigMem','NF_SINGLE_ConfigMem',mem,
                     {p:nets[p]['bits'] for p in mem.value['ports']})
    tile.instantiate('Inst_P_nf_tiny_io','nf_tiny_io',io,
                     {p:nets['P_'+p]['bits'] for p in io.value['ports']})
    con={p:nets[p]['bits'] for p in sw.value['ports'] if p not in ('ConfigBits','ConfigBits_N')}
    con.update(ConfigBits=[qb[19]],ConfigBits_N=[qn[19]])
    tile.instantiate('Inst_NF_SINGLE_switch_matrix','NF_SINGLE_switch_matrix',sw,con)
    con={p:nets['L_'+p]['bits'] for p in ('O','Ci','Co','EN','SR')}
    con.update(I=[nets['L_I'+str(j)]['bits'][0] for j in range(4)],UserCLK=nets['UserCLK']['bits'],ConfigBits=qb[:19])
    tile.instantiate('Inst_L_LUT4c_frame_config_dffesr','LUT4c_frame_config_dffesr',lut,con)
    top=Module(); con={}
    for p,v in tile.value['ports'].items():
        if p.endswith('_O') or p=='UserCLKo':
            con[p]=top.net('unused_'+p,len(v['bits']))
        else:
            name='Tile_X0Y0_'+p if p.startswith('P_') else p
            con[p]=top.net(name,len(v['bits']),v['direction'])
    top.instantiate('Tile_X0Y0_NF_SINGLE','NF_SINGLE',tile,con)
    top.value['parameter_default_values']={'MaxFramesPerCol':format(20,'b'),'FrameBitsPerRow':format(32,'b')}
    for mod in (tile,mem):
        mod.value['parameter_default_values']=dict(top.value['parameter_default_values'],NoConfigBits=format(20,'b'))
    sw.value['parameter_default_values']['NoConfigBits']='1'
    lut.value['parameter_default_values']['NoConfigBits']=format(19,'b')
    return {'modules':{k:v.value for k,v in [('eFPGA',top),('NF_SINGLE',tile),('NF_SINGLE_ConfigMem',mem),
             ('NF_SINGLE_switch_matrix',sw),('LUT4c_frame_config_dffesr',lut),('nf_tiny_io',io),('config_latch',latch),('cus_mux21',mux),('cus_mux161',mux16)]}}

def synthetic_shape(shape):
    """Explicit four-shape synthetic hierarchy, no compiled-output extraction."""
    rows = {
        'one': [(0,0,'SINGLE')],
        'square': [(0,0,'LEFT'),(1,0,'RIGHT'),(0,1,'LEFT'),(1,1,'RIGHT')],
        'odd': [(0,0,'LEFT'),(1,0,'MID'),(2,0,'RIGHT'),(0,1,'LEFT'),(1,1,'MID'),(2,1,'RIGHT')],
        'sparse': [(0,0,'LEFT'),(1,0,'RIGHT'),(1,1,'LEFT'),(2,1,'RIGHT'),(0,2,'SINGLE'),(2,2,'SINGLE')],
    }[shape]
    dims = {'one':(1,1),'square':(2,2),'odd':(3,2),'sparse':(3,3)}[shape]
    data = synthetic_one()
    mods = data['modules']
    base = copy.deepcopy(mods['NF_SINGLE'])
    base_switch = copy.deepcopy(mods['NF_SINGLE_switch_matrix'])
    for suffix in ('LEFT','MID','RIGHT'):
        typ='NF_'+suffix
        tile=copy.deepcopy(base); switch=copy.deepcopy(base_switch)
        for old,new in [('Inst_NF_SINGLE_ConfigMem','Inst_'+typ+'_ConfigMem'),
                        ('Inst_NF_SINGLE_switch_matrix','Inst_'+typ+'_switch_matrix')]:
            tile['cells'][new]=tile['cells'].pop(old)
            tile['cells'][new]['type']=typ+('_ConfigMem' if 'ConfigMem' in new else '_switch_matrix')
        swcon=tile['cells']['Inst_'+typ+'_switch_matrix']['connections']
        swdir=tile['cells']['Inst_'+typ+'_switch_matrix']['port_directions']
        if suffix in ('MID','RIGHT'):
            tile['ports']['W']={'direction':'input','bits':[10000]}
            tile['netnames']['W']={'bits':[10000]}
            switch['ports']['W0']={'direction':'input','bits':[10000]}
            switch['netnames']['W0']={'bits':[10000]}
            switch['netnames']['L_I0_input']['bits'][1]=10000
            switch['cells']['inst_cus_mux21_L_I0']['connections']['A1']=[10000]
            swcon['W0']=[10000]; swdir['W0']='input'
        if suffix in ('LEFT','MID'):
            tile['ports']['E']={'direction':'output','bits':tile['netnames']['L_O']['bits']}
            tile['netnames']['E']={'bits':tile['netnames']['L_O']['bits']}
            switch['ports']['E0']={'direction':'output','bits':switch['ports']['L_O']['bits']}
            switch['netnames']['E0']={'bits':switch['ports']['L_O']['bits']}
            swcon['E0']=tile['netnames']['L_O']['bits']; swdir['E0']='output'
        mods[typ]=tile; mods[typ+'_switch_matrix']=switch
        mods[typ+'_ConfigMem']=copy.deepcopy(mods['NF_SINGLE_ConfigMem'])
    top=Module()
    top.value['parameter_default_values']=mods['eFPGA']['parameter_default_values']
    fd=top.net('FrameData',32*dims[1],'input'); fs=top.net('FrameStrobe',20*dims[0],'input')
    clock=top.net('UserCLK',direction='input')
    routing={(x,y):top.net(f'e{x}{y}') for x,y,t in rows if t in ('LEFT','MID')}
    for x,y,suffix in rows:
        typ='NF_'+suffix; tile=mods[typ]; con={}
        for p,v in tile['ports'].items():
            if p=='FrameData': con[p]=fd[32*y:32*(y+1)]
            elif p=='FrameStrobe': con[p]=fs[20*x:20*(x+1)]
            elif p=='UserCLK': con[p]=clock
            elif p=='E': con[p]=routing[x,y]
            elif p=='W': con[p]=routing[x-1,y]
            elif p.endswith('_O') or p=='UserCLKo': con[p]=top.net(f'{x}{y}_{p}',len(v['bits']))
            else: con[p]=top.net(f'Tile_X{x}Y{y}_{p}',len(v['bits']),v['direction'])
        top.cell(f'Tile_X{x}Y{y}_{typ}',typ,con,{p:v['direction'] for p,v in tile['ports'].items()})
    mods['eFPGA']=top.value
    return data

def synthetic_sources(data,root):
    lines=[]
    for key,mod in data['modules'].items():
        origin=mod.get('attributes',{}).get('hdlname',key).split()[-1]
        start=len(lines)+1
        lines.append('module '+origin+';')
        if 'GND0' in mod.get('parameter_default_values',{}): lines.append("parameter GND0 = 1'b0;")
        for name,net in mod.get('netnames',{}).items():
            lines.append('wire '+name+';')
            net.setdefault('attributes',{})['src']=f'/inputs/generated/source.v:{len(lines)}.1-{len(lines)}.{len(lines[-1])+1}'
        for name,cell in mod.get('cells',{}).items():
            lines.append('// instance '+name)
            cell.setdefault('attributes',{})['src']=f'/inputs/generated/source.v:{len(lines)}.1-{len(lines)}.{len(lines[-1])+1}'
        lines.append('endmodule')
        mod.setdefault('attributes',{})['src']=f'/inputs/generated/source.v:{start}.1-{len(lines)}.10'
    raw=('\n'.join(lines)+'\n').encode()
    (root/'source.v').write_bytes(raw);(root/'sources.f').write_text('source.v\n')
    return {'source.v':hashlib.sha256(raw).hexdigest()}

class StructureControls(unittest.TestCase):
    def setUp(self):
        self.data=synthetic_one()
    def check_data(self,shape,data,**kwargs):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); hashes=synthetic_sources(data,root)
            return s.check_shape(shape,data,source_root=root,source_hashes=hashes,**kwargs)
    def check(self):
        return self.check_data('one',self.data)
    def test_synthetic_complete_roster(self):
        self.assertEqual(self.check()['counts'], {'PIN':22,'FIXED':11,'SELECT':2,'CONFIG':20,'RESOURCE':4,'LINK':0})
    def test_oracle_exact_denominators(self):
        keys=[k for shape in ('one','square','odd','sparse') for k in s.expected(shape)[1]]
        self.assertEqual({kind:sum(k.startswith(kind+'/') for k in keys) for kind in ('PIN','FIXED','SELECT','CONFIG','RESOURCE','LINK')},
                         {'PIN':390,'FIXED':195,'SELECT':34,'CONFIG':340,'RESOURCE':68,'LINK':8})
        self.assertEqual(len(keys),len(set(keys)))
    def test_all_synthetic_shapes_exact_witnesses(self):
        with tempfile.TemporaryDirectory() as directory:
            exports={shape:synthetic_shape(shape) for shape in ('one','square','odd','sparse')}
            roots={shape:Path(directory)/shape for shape in exports}
            for root in roots.values(): root.mkdir()
            hashes={shape:synthetic_sources(data,roots[shape]) for shape,data in exports.items()}
            result=s.check_all(exports,source_roots=roots,source_hashes=hashes)
        self.assertEqual(result['counts'], {'PIN':390,'FIXED':195,'SELECT':34,'CONFIG':340,'RESOURCE':68,'LINK':8})
    def test_compiled_endpoint_omission_names_link(self):
        data=synthetic_shape('odd')
        data['modules']['eFPGA']['cells']['Tile_X1Y0_NF_MID']['connections']['W']=['0']
        with self.assertRaises(s.StructureError) as caught: self.check_data('odd',data)
        self.assertEqual(caught.exception.witness,'LINK/odd/t00.e->t10.w')
        self.assertEqual(caught.exception.diagnostic,'missing-directed-edge')
    def test_cross_row_link_rejected(self):
        data=synthetic_shape('square')
        cells=data['modules']['eFPGA']['cells']
        cells['Tile_X1Y0_NF_RIGHT']['connections']['W']=cells['Tile_X0Y1_NF_LEFT']['connections']['E']
        with self.assertRaisesRegex(s.StructureError,'LINK/square/t00.e->t10.w'): self.check_data('square',data)
    def test_parameterized_module_keys(self):
        mod=self.data['modules'].pop('NF_SINGLE')
        mod['attributes']={'hdlname':'NF_SINGLE'}
        self.data['modules']['$paramod$example']=mod
        self.data['modules']['eFPGA']['cells']['Tile_X0Y0_NF_SINGLE']['type']='$paramod$example'
        self.check()
    def test_unknown_top_cell(self):
        top=self.data['modules']['eFPGA']['cells']
        top['extra']=copy.deepcopy(next(iter(top.values())))
        with self.assertRaises(s.StructureError): self.check()
    def test_swapped_mux_order(self):
        c=self.data['modules']['NF_SINGLE_switch_matrix']['cells']['inst_cus_mux21_L_I0']['connections']
        c['A0'],c['A1']=c['A1'],c['A0']
        with self.assertRaisesRegex(s.StructureError,'ordered-terminal'): self.check()
    def test_extra_switch_cell(self):
        cells=self.data['modules']['NF_SINGLE_switch_matrix']['cells']
        cells['unexpected']=copy.deepcopy(next(iter(cells.values())))
        with self.assertRaisesRegex(s.StructureError,'cell-inventory'): self.check()
    def test_missing_latch(self):
        del self.data['modules']['NF_SINGLE_ConfigMem']['cells']['Inst_frame0_bit12']
        with self.assertRaisesRegex(s.StructureError,'latches'): self.check()
    def test_shifted_latch_data(self):
        c=self.data['modules']['NF_SINGLE_ConfigMem']['cells']['Inst_frame0_bit12']['connections']
        c['D']=[c['D'][0]+1]
        with self.assertRaisesRegex(s.StructureError,'CONFIG/one/t00/0/D'): self.check()
    def test_swapped_q_qn(self):
        c=self.data['modules']['NF_SINGLE_ConfigMem']['cells']['Inst_frame0_bit12']['connections']
        c['Q'],c['QN']=c['QN'],c['Q']
        with self.assertRaisesRegex(s.StructureError,'CONFIG/one/t00/0/tile_q'): self.check()
    def test_wrong_consumer(self):
        m=self.data['modules']['NF_SINGLE']
        m['cells']['Inst_NF_SINGLE_switch_matrix']['connections']['ConfigBits']=[m['netnames']['ConfigBits']['bits'][16]]
        with self.assertRaisesRegex(s.StructureError,'config-consumer-mismatch'): self.check()
    def test_duplicate_state_driver(self):
        cells=self.data['modules']['LUT4c_frame_config_dffesr']['cells']
        cells['extra']=copy.deepcopy(cells['$procdff$1'])
        with self.assertRaisesRegex(s.StructureError,'lowered-source-inventory|lut.register/driver'): self.check()
    def test_wrong_state_clock(self):
        m=self.data['modules']['LUT4c_frame_config_dffesr']
        m['cells']['$procdff$1']['connections']['CLK']=m['ports']['EN']['bits']
        with self.assertRaisesRegex(s.StructureError,'lut.register/clock'): self.check()
    def test_gnd_is_parameter_not_net(self):
        self.assertNotIn('GND0',self.data['modules']['NF_SINGLE_switch_matrix']['netnames'])
        self.check()
        self.data['modules']['NF_SINGLE_switch_matrix']['parameter_default_values']['GND0']='1'
        with self.assertRaisesRegex(s.StructureError,'GND0'): self.check()
    def test_declared_vector_reversal(self):
        self.data['modules']['LUT4c_frame_config_dffesr']['netnames']['I']['upto']=1
        with self.assertRaisesRegex(s.StructureError,'index-order'): self.check()
    def test_emulation_rejected(self):
        with self.assertRaisesRegex(s.StructureError,'structural-defines'):
            self.check_data('one',self.data,defines=('EMULATION',))
    def test_missing_shape(self):
        with self.assertRaisesRegex(s.StructureError,'shape-roster'): s.check_all({'one':self.data},source_roots={},source_hashes={})
    def test_mapping_controls(self):
        for change in ('swap','omit','duplicate'):
            _,c=s.oracle()
            if change=='swap':
                c['pin_map']['lut.i0'],c['pin_map']['lut.i3']=c['pin_map']['lut.i3'],c['pin_map']['lut.i0']
            elif change=='omit': del c['pin_map']['y']
            else: c['pin_map']['lut.i1']=copy.deepcopy(c['pin_map']['lut.i0'])
            with self.assertRaisesRegex(s.StructureError,'PIN/one/t00/'): s.check_correspondence(c)
    def test_reversed_or_duplicate_declared_links(self):
        edges=[['t00.e','t10.w'],['t10.e','t20.w'],['t01.e','t11.w'],['t11.e','t21.w']]
        s.check_declared_edges('odd',edges)
        for bad in ([edges[0][::-1]]+edges[1:], edges[:-1], edges+[edges[0]]):
            with self.assertRaises(s.StructureError): s.check_declared_edges('odd',bad)
    def test_register_reset_priority(self):
        m=self.data['modules']['LUT4c_frame_config_dffesr']
        m['cells']['enable']['connections']['S']=m['ports']['SR']['bits']
        with self.assertRaisesRegex(s.StructureError,'lut.register/EN/control'): self.check()
    def test_latch_negative_enable(self):
        self.data['modules']['config_latch']['cells']['latch_Q']['parameters']['EN_POLARITY']='0'
        with self.assertRaisesRegex(s.StructureError,'Q/enable'): self.check()
    def test_latch_wrong_complement(self):
        m=self.data['modules']['config_latch']
        m['cells']['latch_QN']['connections']['D']=m['ports']['D']['bits']
        with self.assertRaisesRegex(s.StructureError,'QN/complement'): self.check()
    def test_unknown_child_module(self):
        self.data['modules']['cus_mux21']['attributes']={'hdlname':'unreviewed_mux'}
        with self.assertRaisesRegex(s.StructureError,'unknown-module'): self.check()
    def test_shorted_top_inputs(self):
        m=self.data['modules']['NF_SINGLE']
        m['netnames']['P_A1']['bits']=m['ports']['P_A0']['bits']
        m['ports']['P_A1']['bits']=m['ports']['P_A0']['bits']
        with self.assertRaisesRegex(s.StructureError,'independent-top-inputs'): self.check()
    def test_mapping_diagnostic_and_affected_ids(self):
        _,c=s.oracle()
        c['pin_map']['lut.i0'],c['pin_map']['lut.i3']=c['pin_map']['lut.i3'],c['pin_map']['lut.i0']
        with self.assertRaises(s.StructureError) as caught: s.check_correspondence(c)
        self.assertEqual(caught.exception.diagnostic,'pin-order-mismatch')
        self.assertEqual(caught.exception.affected,['PIN/one/t00/lut.i0','PIN/one/t00/lut.i3'])
        _,c=s.oracle()
        c['config_map'][19]['tile_config_bit']=16
        with self.assertRaises(s.StructureError) as caught: s.check_correspondence(c)
        self.assertEqual(caught.exception.diagnostic,'config-field-overlap')
        self.assertEqual(caught.exception.witness,'CONFIG/one/t00/19')
    def test_reversal_names_exact_link(self):
        with self.assertRaises(s.StructureError) as caught:
            s.check_declared_edges('square',[['t10.w','t00.e'],['t01.e','t11.w']])
        self.assertEqual(caught.exception.diagnostic,'reversed-directed-edge')
        self.assertEqual(caught.exception.witness,'LINK/square/t00.e->t10.w')
    def test_register_configuration_alias(self):
        mod=self.data['modules']['LUT4c_frame_config_dffesr']
        old=mod['netnames']['LUT_flop']['bits'][0]
        new=mod['ports']['ConfigBits']['bits'][0]
        for net in mod['netnames'].values(): net['bits']=[new if b==old else b for b in net['bits']]
        for cell in mod['cells'].values():
            for port,bits in cell['connections'].items(): cell['connections'][port]=[new if b==old else b for b in bits]
        with self.assertRaisesRegex(s.StructureError,'RESOURCE/one/t00/lut.register/state-ownership'): self.check()
    def test_extra_latch_input_driver(self):
        mod=self.data['modules']['config_latch']
        mod['cells']['extra_input_driver']={'type':'$not','connections':{'A':mod['ports']['E']['bits'],'Y':mod['ports']['D']['bits']},
                                           'port_directions':{'A':'input','Y':'output'},'parameters':{}}
        with self.assertRaisesRegex(s.StructureError,'storage-cell-inventory|storage-unused-hold|physical-driver'): self.check()
    def test_record_provenance_totality(self):
        result=self.check()
        for identifier,record in result['records'].items():
            self.assertTrue(record['candidate_refs'],identifier)
            for ref in record['candidate_refs']:
                for field in ('path','type','direction','json_pointer','source_bindings'):
                    self.assertIn(field,ref)
                for binding in ref['source_bindings']:
                    self.assertEqual(binding['sha256'],result['source_sha256'][binding['path']])
    def test_bad_source_bindings(self):
        for failure in ('missing-map','wrong-hash','missing-src','bad-format','escape','out-of-bounds','wrong-module'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                data=synthetic_one(); root=Path(directory); hashes=synthetic_sources(data,root)
                if failure=='missing-map': hashes={}
                elif failure=='wrong-hash': hashes['source.v']='0'*64
                elif failure=='missing-src': del data['modules']['eFPGA']['attributes']['src']
                elif failure=='bad-format': data['modules']['eFPGA']['attributes']['src']='source.v:nonsense'
                elif failure=='escape': data['modules']['eFPGA']['attributes']['src']='/inputs/generated/../source.v:1.1-1.2'
                elif failure=='out-of-bounds': data['modules']['eFPGA']['attributes']['src']='/inputs/generated/source.v:999999.1-999999.2'
                elif failure=='wrong-module':
                    (root/'source.v').write_text((root/'source.v').read_text().replace('module eFPGA;','module wrong;'))
                    hashes['source.v']=hashlib.sha256((root/'source.v').read_bytes()).hexdigest()
                with self.assertRaisesRegex(s.StructureError,'provenance-mismatch'):
                    s.check_shape('one',data,source_root=root,source_hashes=hashes)
    def test_missing_net_src_has_explicit_module_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); hashes=synthetic_sources(self.data,root)
            del self.data['modules']['NF_SINGLE']['netnames']['P_A0']['attributes']['src']
            result=s.check_shape('one',self.data,source_root=root,source_hashes=hashes)
            ref=result['records']['PIN/one/t00/a0']['candidate_refs'][0]
            self.assertEqual(ref['source_bindings'][0]['scope'],'module-fallback')
    def test_mutant_failure_has_source_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); hashes=synthetic_sources(self.data,root)
            mod=self.data['modules']['NF_SINGLE']
            mod['cells']['Inst_NF_SINGLE_switch_matrix']['connections']['ConfigBits']=[mod['netnames']['ConfigBits']['bits'][16]]
            with self.assertRaises(s.StructureError) as caught:
                s.check_shape('one',self.data,source_root=root,source_hashes=hashes)
            refs=caught.exception.candidate_refs
            self.assertTrue(refs)
            self.assertTrue(any('Inst_NF_SINGLE_switch_matrix.ConfigBits' in ref['path'] for ref in refs))
            self.assertTrue(all(b['sha256']==hashes[b['path']] for ref in refs for b in ref['source_bindings']))
    def test_missing_candidate_refs_rejected(self):
        from unittest.mock import patch
        with patch.object(s.Provenance,'record',return_value=[]):
            with self.assertRaisesRegex(s.StructureError,'candidate-refs'): self.check()
    def test_duplicate_json_key(self):
        with self.assertRaisesRegex(s.StructureError,'duplicate-json-key'):
            s.json.loads('{"a":0,"a":1}',object_pairs_hook=s.unique_object)

if __name__=='__main__': unittest.main()
