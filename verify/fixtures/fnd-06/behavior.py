"""Bounded fixture testbench serialization and strict observation parsing.

No subprocesses execute here. Expectations come solely from the separately
reviewed literal corpus. Candidate RTL is never read to construct expectations.
"""
from __future__ import annotations
import json
import hashlib
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE.parent / 'nf-tiny' / 'specification.json'

class Witnesses(list):
    def __init__(self, only_ids=None):
        super().__init__()
        self.expected = {}
        self.bindings = {}
        self.only_ids = None if only_ids is None else set(only_ids)

class BehaviorError(ValueError):
    def __init__(self, category, detail):
        self.category = category
        super().__init__(f'{category}: {detail}')

def _load(spec_path=None, semantic_path=None):
    return (json.loads(Path(spec_path or SPEC).read_text()),
            json.loads(Path(semantic_path or HERE/'semantic_cases.json').read_text()))

def _start(declarations):
    return ['`timescale 1ns/1ps', '`default_nettype none', 'module tb;', declarations,
            (HERE/'simulation/common.sv').read_text()]

def _finish(lines, path, ids=None):
    lines += ['$display("DONE\\t%0d",records); $finish;', 'end', 'endmodule', '`default_nettype wire']
    Path(path).write_text('\n'.join(lines)+'\n')
    if ids is not None:
        source=Path(path).read_bytes()
        for identity in ids:
            matches=[i+1 for i,line in enumerate(source.decode().splitlines()) if f'observe("{identity}",' in line]
            if len(matches)!=1: raise BehaviorError('source-binding-mismatch',identity)
            ids.bindings[identity].update(source_line=matches[0],source_sha256=hashlib.sha256(source).hexdigest(),source_file=Path(path).name)
        if ids.only_ids is not None and set(ids)!=ids.only_ids:
            raise BehaviorError('missing-witness',str(ids.only_ids-set(ids)))

def _obs(lines, ids, name, actual, expected):
    if ids.only_ids is not None and name not in ids.only_ids: return
    if name in ids: raise BehaviorError('duplicate-witness',name)
    ids.append(name)
    ids.expected[name] = expected
    ids.bindings[name] = dict(signal=actual,semantic_checks=1,nonbinary_checks=1)
    lines.append(f'observe("{name}", {actual}, 64\'h{expected:016x});')

def parse_simulation(stdout, expected_ids, expected_values=None):
    expected_values = expected_values if expected_values is not None else getattr(expected_ids, 'expected', None)
    expected_ids = list(expected_ids)
    if expected_values is None or set(expected_values)!=set(expected_ids):
        raise BehaviorError('missing-oracle-values','exact independent expected-value map required')
    if not expected_ids or len(set(expected_ids)) != len(expected_ids):
        raise BehaviorError('zero-or-wrong-obligation-count','expected IDs')
    records=[]; seen=set(); done=[]
    for line in stdout.splitlines():
        if line.startswith('NONBINARY\t'):
            raise BehaviorError('non-binary-output',line)
        if line.startswith('OBS\t'):
            parts=line.split('\t')
            if len(parts)!=5: raise BehaviorError('malformed-observation',line)
            _, identity, expected, actual, timestamp=parts
            if not timestamp.isdecimal(): raise BehaviorError("malformed-observation",line)
            if identity in seen: raise BehaviorError('duplicate-witness',identity)
            if not re.fullmatch('[0-9a-fA-F]+',actual): raise BehaviorError('non-binary-output',line)
            if not re.fullmatch('[0-9a-fA-F]+',expected): raise BehaviorError('malformed-observation',line)
            if expected_values is not None and expected_values.get(identity)!=int(expected,16):
                raise BehaviorError('oracle-value-mismatch',identity)
            if int(expected,16)!=int(actual,16): raise BehaviorError('semantic-mismatch',line)
            seen.add(identity); records.append(dict(id=identity,category='passed',expected=int(expected,16),observed=int(actual,16),time=int(timestamp),semantic_checks=1,nonbinary_checks=1))
        if line.startswith('DONE\t'):
            try: done.append(int(line.split('\t')[1]))
            except (ValueError,IndexError): raise BehaviorError('malformed-observation',line)
    if seen!=set(expected_ids) or done!=[len(records)]:
        raise BehaviorError('zero-or-wrong-obligation-count',f'missing={sorted(set(expected_ids)-seen)}, extra={sorted(seen-set(expected_ids))}, done={done}')
    return records

def write_lut_unit(output_path, *, spec_path=None, semantic_path=None, only_ids=None):
    _,s=_load(spec_path,semantic_path)
    lines=_start("reg [3:0] inputs=0; reg [18:0] cfg=0; reg clock=0,en=0,sr=0; wire observed;\n"
       "LUT4c_frame_config_dffesr dut(.I(inputs),.O(observed),.Ci(1'b0),.Co(),.EN(en),.SR(sr),.UserCLK(clock),.ConfigBits(cfg));")
    lines += ['initial begin']; ids=Witnesses(only_ids)
    for table in s['lut_tables']:
        for a,e in enumerate(table['expected_by_address']):
            lines += [f"cfg=19'h{table['init_hex']}; inputs=4'd{a}; #10;"]
            _obs(lines,ids,f"UNIT-LUT/{table['init_hex']}/{a}",'observed',e)
    for row in s['onehot']:
        lines += [f"cfg=19'h{row['init_hex']}; inputs=4'd{row['address']}; #10;"]
        _obs(lines,ids,row['id'],'observed',row['expected'])
    # Exact unit register traces, both output modes and internal state continuity.
    for ff in (0,1):
        for trace in s['register_traces']:
            r=trace['reset_value']; lines += [f"clock=0; cfg=19'h{((r<<18)|(ff<<16)|0xA6D3):05x}; #10;"]
            for n,row in enumerate(trace['steps']):
                _edge(lines,row,'clock','en','sr','inputs',s)
                _obs(lines,ids,f'UNIT-REG/FF{ff}/R{r}/step{n}',"{dut.LUT_flop,observed}",(row['q']<<1)|(row['q'] if ff else row['d']))
    _finish(lines,output_path,ids); return ids

def _edge(lines,row,clock,en,sr,inputs,s):
    # Lowering before a rising event is a falling edge and cannot change state.
    if row['edge']=='rise': lines += [f'{clock}=0; #5;']
    lines += [f"{en}={row['en']}; {sr}={row['sr']}; {inputs}=4'b{s['register_drive']['address_for_d'+str(row['d'])]}; #5;"]
    if row['edge']=='rise': lines += [f'{clock}=1; #10;']
    elif row['edge']=='fall': lines += [f'{clock}=0; #10;']
    else: lines += ['#10;']

def write_units(variant, output_path, *, spec_path=None, semantic_path=None, only_ids=None):
    _,s=_load(spec_path,semantic_path)
    if variant not in ('NF_SINGLE','NF_LEFT','NF_MID','NF_RIGHT'): raise ValueError(variant)
    west=variant in ('NF_MID','NF_RIGHT')
    decl=f'''reg [31:0] data=0; reg [19:0] strobe=0; wire [19:0] q,qn;
{variant}_ConfigMem memory(.FrameData(data),.FrameStrobe(strobe),.ConfigBits(q),.ConfigBits_N(qn));
reg local_input=0,secondary=0,select_input=0; reg [6:0] fixed_inputs=0;
wire result,i0,i1,i2,i3,ci,en,sr,east;
{variant}_switch_matrix mux(.P_X0(local_input),.P_X1(fixed_inputs[0]),.P_X2(fixed_inputs[1]),.P_X3(fixed_inputs[2]),
.P_XA({'fixed_inputs[6]' if west else 'secondary'}),.P_XE(fixed_inputs[3]),.P_XR(fixed_inputs[4]),.L_O(fixed_inputs[5]),.L_Co(1'b0),
{'.W0(secondary),' if west else ''}.L_I0(i0),.L_I1(i1),.L_I2(i2),.L_I3(i3),.L_Ci(ci),.L_EN(en),.L_SR(sr),.P_RESULT(result),
{'.E0(east),' if variant in ('NF_LEFT','NF_MID') else ''}.ConfigBits(select_input),.ConfigBits_N(~select_input));'''
    lines=_start(decl); lines += ['initial begin']; ids=Witnesses(only_ids)
    for i,row in enumerate(s['mux_rows']):
        lines += [f"local_input={row['a0']}; secondary={row['a1']}; select_input={row['select']}; #10;"]
        _obs(lines,ids,f'UNIT-MUX/{variant}/{i}','i0',row['expected'])
    for b in (0,1):
        lines += [f"fixed_inputs=7'b{str(b)*7}; #10;"]
        actual='{ci,east,result,sr,en,i3,i2,i1}' if variant in ('NF_LEFT','NF_MID') else '{ci,result,sr,en,i3,i2,i1}'
        _obs(lines,ids,f'UNIT-FIXED/{variant}/{b}',actual,(127 if variant in ('NF_LEFT','NF_MID') else 63)*b)
    for row in s['walking_storage']:
        word=int(row['config_hex'],16); comp=sum(v<<i for i,v in enumerate(row['qn_lsb_first']))
        lines += [f"strobe=0; data=32'h{row['frame0_hex']}; #10; strobe=1; #10; strobe=0; #10;"]
        _obs(lines,ids,f"UNIT-CONFIG/{variant}/{row['mode']}/j{row['bit']}",'{qn,q}',(comp<<20)|word)
    for row in s['storage_behavior']:
        family,index=row['id'].split('/')
        lines += [f"strobe=0; data=32'h{row['baseline_frame0_hex']}; #10; strobe=1; #10;"]
        if family!='TRANSPARENT': lines += ['strobe=0; #10;']
        lines += [f"data=32'h{row['frame_data_hex']}; strobe=20'h{row['frame_strobe_hex']}; #10;"]
        q=sum(v<<i for i,v in enumerate(row['expected_q_lsb_first']))
        qn=sum(v<<i for i,v in enumerate(row['expected_qn_lsb_first']))
        suffix=('f' if family=='PAD-FRAME' else 'b' if family=='PAD-DATA' else 'j')+index
        _obs(lines,ids,f'UNIT-CONFIG-{family}/{variant}/{suffix}','{qn,q}',(qn<<20)|q)
        lines += ['strobe=0; #10;']
    _finish(lines,output_path,ids); return ids

def write_simulation(shape_id, output_path, *, spec_path=None, semantic_path=None, only_ids=None):
    spec,s=_load(spec_path,semantic_path)
    shape=next(x for x in spec['shapes'] if x['id']==shape_id)
    tiles=shape['tiles']; by_id={t['id']:t for t in tiles}
    width,height=shape['width'],shape['height']
    decl=[f'reg [{32*height-1}:0] FrameData=0; reg [{20*width-1}:0] FrameStrobe=0; reg UserCLK=0;']
    ports=['.FrameData(FrameData)','.FrameStrobe(FrameStrobe)','.UserCLK(UserCLK)']
    for t in tiles:
        key=t['id']; prefix=f"Tile_X{t['x']}Y{t['y']}_P_"
        decl += [f'reg [3:0] i_{key}=0; reg alt_{key}=0,en_{key}=0,sr_{key}=0; wire y_{key}; reg [19:0] word_{key}=0;']
        ports += [f'.{prefix}A{b}(i_{key}[{b}])' for b in range(4)]
        ports += [f'.{prefix}{p}({v}_{key})' for p,v in [('ALT','alt'),('ENABLE','en'),('RESET','sr'),('Y','y')]]
    decl += ['eFPGA dut('+','.join(ports)+');','task load_column(input integer column); begin','UserCLK=0; FrameStrobe=0; FrameData=0;','case(column)']
    for x in range(width):
        decl += [f'{x}: begin']
        for t in tiles:
            if t['x']==x: decl += [f"FrameData[{32*t['y']} +: 32]={{word_{t['id']},12'b0}};"]
        decl += ['end']
    decl += ['default: $fatal(1,"invalid-column");','endcase','#10; FrameStrobe[column*20]=1; #10; FrameStrobe=0; #10;','end endtask']
    lines=_start('\n'.join(decl)); lines+=['initial begin']; ids=Witnesses(only_ids)
    def path(t): return f"dut.Tile_X{t['x']}Y{t['y']}_{t['type']}"
    def setup(word=0xAAAA):
        lines.append('UserCLK=0;')
        for t in tiles: lines.append(f"word_{t['id']}=20'h{word:05x}; i_{t['id']}=0; alt_{t['id']}=0; en_{t['id']}=0; sr_{t['id']}=0;")
        for x in range(width): lines.append(f'load_column({x});')
    def config(t,word):
        lines.extend([f"word_{t['id']}=20'h{word:05x};",f"load_column({t['x']});"])
    def state(t): return path(t)+'.Inst_L_LUT4c_frame_config_dffesr.LUT_flop'
    def consumers(t):
        p=path(t)
        return '{'+f'{state(t)},{p}.ConfigBits_N,{p}.Inst_{t["type"]}_switch_matrix.ConfigBits,{p}.Inst_L_LUT4c_frame_config_dffesr.ConfigBits,{p}.ConfigBits'+'}'
    def consumers_expected(word): return ((word^0xfffff)<<40)|(word<<20)|word
    setup(0)
    # Establish state through the declared enabled reset edge, never an initial-q assumption.
    for t in tiles: lines.append(f"en_{t['id']}=1; sr_{t['id']}=1;")
    lines += ['#10; UserCLK=1; #10; UserCLK=0; #10;']
    for t in tiles: lines.append(f"en_{t['id']}=0; sr_{t['id']}=0;")
    words={r['tile']:r for r in s['instance_words'] if r['shape']==shape_id}
    for t in tiles: lines.append(f"word_{t['id']}=20'h{words[t['id']]['config_hex']};")
    for x in range(width): lines.append(f'load_column({x});')
    for t in tiles:
        _obs(lines,ids,f"INSTANCE-CONFIG-WORD/{shape_id}/{t['id']}",consumers(t),consumers_expected(int(words[t['id']]['config_hex'],16)))
    # Change selected column data; every other column must retain its distinct word and state.
    for x in range(width):
        for t in tiles:
            if t['x']==x: lines.append(f"word_{t['id']}=20'h0A6D3;")
        lines.append(f'load_column({x});')
        for t in tiles:
            if t['x']!=x:
                _obs(lines,ids,f"COLUMN-HOLD/{shape_id}/{x}/{t['id']}",consumers(t),consumers_expected(int(words[t['id']]['config_hex'],16)))
        for t in tiles:
            if t['x']==x: lines.append(f"word_{t['id']}=20'h{words[t['id']]['config_hex']};")
        lines.append(f'load_column({x});')
    table=s['lut_tables'][0]['expected_by_address']
    for t in tiles:
        key=t['id']
        for source in (0,1):
            setup(); config(t,0xA6D3|(source<<19))
            west=t['type'] in ('NF_MID','NF_RIGHT')
            predecessor=next((p for p in tiles if p['x']==t['x']-1 and p['y']==t['y']),None)
            if source and west and predecessor is None: raise BehaviorError('oracle-error','missing predecessor')
            for a,e in enumerate(table):
                i0=a&1
                lines += [f"i_{key}=4'd{(a ^ 1) if source else a}; alt_{key}={i0 if source else 1-i0};"]
                if source and west:
                    lines += [f"i_{predecessor['id']}=4'd{i0}; alt_{key}={1-i0};"]
                lines+=['#10;']
                family='SECONDARY' if source else 'LOCAL'
                _obs(lines,ids,f'{family}-A6D3/{shape_id}/{key}/address{a}',f'y_{key}',e)
        for ff in (1,0):
            for trace in s['register_traces']:
                r=trace['reset_value']; setup(); config(t,0xA6D3|(ff<<16)|(r<<18))
                for n,row in enumerate(trace['steps']):
                    _edge(lines,row,'UserCLK',f'en_{key}',f'sr_{key}',f'i_{key}',s)
                    family='REG' if ff else 'FF0-STATE'
                    actual='{'+state(t)+f',y_{key}'+'}'
                    _obs(lines,ids,f'{family}-R{r}/{shape_id}/{key}/step{n}',actual,(row['q']<<1)|(row['q'] if ff else row['d']))
    for frm,to in shape['intertile_edges']:
        a=by_id[frm.split('.')[0]]; b=by_id[to.split('.')[0]]
        setup(); config(b,0x8AAAA)
        for value in (0,1):
            lines += [f"i_{a['id']}=4'd{value}; i_{b['id']}=4'd{1-value}; alt_{b['id']}={1-value}; #10;"]
            _obs(lines,ids,f'LINK/{shape_id}/{frm}->{to}/value{value}',f"{{y_{a['id']},y_{b['id']}}}",value*3)
    if shape_id=='odd':
        setup()
        for row in s['shape_witness']['configuration']:
            config(by_id[row['tile']],int(row['init_hex'],16)|(row['source']<<19))
        for row in s['shape_witness']['rows']:
            value=row['t00.a0']; lines += [f'i_t00={value}; i_t01={1-value}; #10;']
            expected=(row['t00.y']<<3)|(row['t10.y']<<2)|(row['t20.y']<<1)|(1-value)
            _obs(lines,ids,f'ROW-ODD/{value}','{y_t00,y_t10,y_t20,y_t01}',expected)
    if shape_id=='one':
        setup(); row=s['config_consumer_mutation']; t=tiles[0]
        config(t,int(row['config_hex'],16))
        lines += [f"i_t00=0; alt_t00={row['alt']}; #10;"]
        _obs(lines,ids,'M-CONFIG-CONSUMER/behavior','y_t00',row['expected_y'])
    _finish(lines,output_path,ids); return ids

FORMAL_TOPS = {
    'lut': ('lut_formal','formal/lut.sv',1,0,4,1),
    'switch-NF_SINGLE': ('switch_SINGLE','formal/switch.sv',1,0,2,1),
    'switch-NF_LEFT': ('switch_LEFT','formal/switch.sv',1,0,2,1),
    'switch-NF_MID': ('switch_MID','formal/switch.sv',1,0,2,1),
    'switch-NF_RIGHT': ('switch_RIGHT','formal/switch.sv',1,0,2,1),
    'register': ('register_formal','formal/register.sv',2,1,9,13),
    'false-control': ('false_control','formal/controls.sv',1,0,0,1),
    'zero-control': ('zero_control','formal/controls.sv',1,0,0,1),
    'overconstraint-control': ('switch_SINGLE','formal/switch.sv',1,1,2,1),
}

def formal_plan(top, sources, smt_path, *, fixture_root='/source/verify/fixtures/fnd-06'):
    compiled,filename,a,h,c,bound=FORMAL_TOPS[top]
    all_sources=list(sources)+[str(Path(fixture_root)/filename)]
    # Reject script interpolation, accidental EMULATION and whitespace-ambiguous inputs.
    if any(not re.fullmatch(r'[/A-Za-z0-9_.+-]+',str(p)) for p in all_sources+[smt_path]):
        raise BehaviorError('invalid-input','unsafe Yosys path')
    define=' -D FND06_OVERCONSTRAIN' if top=='overconstraint-control' else ''
    script='; '.join([
      'read_verilog -formal -sv'+define+' '+' '.join(all_sources),
      f'prep -top {compiled}', 'chformal -lower',
      f'select -assert-count {a} t:$assert',f'select -assert-count {h} t:$assume',
      f'select -assert-count {c} t:$cover', 'select -assert-none t:$check',
      f'write_json {smt_path}.json',f'write_smt2 -wires {smt_path}'])
    manifest=json.loads((HERE/'obligations.json').read_text())
    logical='switch-NF_SINGLE' if top=='overconstraint-control' else top
    properties=[dict(r) for r in manifest['formal'] if r['top']==logical]
    if top=='false-control': properties=[dict(id='A-CONTROL-FALSE',label='A_CONTROL_FALSE',kind='assert')]
    if top=='zero-control': properties=[dict(id='X-CONTROL-ZERO-EXPORT',label='X_CONTROL_ZERO_EXPORT',kind='assert')]
    if top=='overconstraint-control': properties += [dict(id='H-CONTROL-SELECT0',label='H_CONTROL_SELECT0',kind='assume')]
    # Switch declaration labels are local to separately elaborated top modules.
    for p in properties:
        p['compiled_label']=p.get('declaration_label',p['label'])
        source_path=HERE/filename
        source_lines=source_path.read_text().splitlines()
        line_numbers=[i+1 for i,line in enumerate(source_lines) if re.search(r'\b'+re.escape(p['compiled_label'])+r'\s*:',line)]
        # Shared switch file has four repeated labels, distinguished by top module span.
        if filename=='formal/switch.sv':
            module_start=next(i+1 for i,line in enumerate(source_lines) if line.startswith('module '+compiled+';'))
            module_end=next(i+1 for i,line in enumerate(source_lines) if i+1>module_start and line=='endmodule')
            line_numbers=[i for i in line_numbers if module_start<i<module_end]
        if top!='zero-control' and len(line_numbers)!=1:
            raise BehaviorError('property-binding-mismatch',p['id'])
        p['source_line']=line_numbers[0] if line_numbers else None
        p['source_sha256']=hashlib.sha256(source_path.read_bytes()).hexdigest()
        p['source_file']=filename
    return dict(logical_top=top,top=compiled,source=filename,script=script,
        assertions=a,assumptions=h,covers=c,bound=bound,properties=properties,
        proof_args=['-s','z3','-t',str(bound),'--dump-vcd',smt_path+'.assert.vcd',smt_path],
        cover_args=['-s','z3','-t',str(bound),'-c','--dump-vcd',smt_path+'.cover%.vcd',smt_path])

def _smt_definitions(text):
    definitions={}
    for match in re.finditer(r'\(define-fun \|([^|]+)\|',text):
        start=match.start(); level=0; quoted=False; end=None
        for i in range(start,len(text)):
            ch=text[i]
            if ch=='|': quoted=not quoted
            if quoted: continue
            if ch=='(': level+=1
            elif ch==')':
                level-=1
                if level==0: end=i+1; break
        if end is None or match[1] in definitions:
            raise BehaviorError('property-binding-mismatch','missing/duplicate SMT definition')
        definitions[match[1]]=text[start:end]
    return definitions

def parse_formal_inventory(smt_text,plan):
    """Bind exact source labels to exported SMT property IDs, never counts alone."""
    records=[]; module=None
    for line in smt_text.splitlines():
        if line.startswith('; yosys-smt2-module '): module=line.split(' ',2)[2]
        m=re.match(r'; yosys-smt2-(assert|assume|cover) (\d+) (\S+)(?: (.+))?$',line)
        if m: records.append(dict(kind=m[1],index=int(m[2]),name=m[3],source=m[4] or '',module=module))
    if any(r['module']!=plan['top'] for r in records):
        raise BehaviorError('property-binding-mismatch','unexpected property module')
    counts={k:sum(r['kind']==k for r in records) for k in ('assert','assume','cover')}
    wanted={'assert':plan['assertions'],'assume':plan['assumptions'],'cover':plan['covers']}
    if counts!=wanted or not counts['assert']:
        raise BehaviorError('zero-or-wrong-obligation-count',f'{counts} != {wanted}')
    if len({(r['kind'],r['index']) for r in records})!=len(records):
        raise BehaviorError('property-binding-mismatch','duplicate SMT property index')
    definitions=_smt_definitions(smt_text)
    expected_functions={f"{plan['top']}_{ {'assert':'a','assume':'u','cover':'c'}[r['kind']]} {r['index']}" for r in records}
    actual_functions={name for name in definitions if re.fullmatch(re.escape(plan['top'])+r'_[auc] \d+',name)}
    if expected_functions!=actual_functions:
        raise BehaviorError('property-binding-mismatch','SMT indexed definition set')
    for kind,letter in [('assert','a'),('assume','u')]:
        aggregate=definitions.get(f"{plan['top']}_{letter}",'')
        members=re.findall(r'\(\|('+re.escape(plan['top'])+'_'+letter+r' \d+)\| state\)',aggregate)
        wanted={f"{plan['top']}_{letter} {r['index']}" for r in records if r['kind']==kind}
        if not aggregate or set(members)!=wanted or len(members)!=len(set(members)):
            raise BehaviorError('property-binding-mismatch','SMT aggregate membership')
    assigned=set(); result=[]
    for p in plan['properties']:
        label=p['compiled_label']
        def bound(r):
            named=re.search(r'(?<![A-Za-z0-9_])'+re.escape(label)+r'(?![A-Za-z0-9_])',r['name'])
            located=p.get('source_line') is not None and re.search(re.escape(p['source_file'])+':'+str(p['source_line'])+r'\.',r['source'])
            return named or located
        matches=[(i,r) for i,r in enumerate(records) if r['kind']==p['kind'] and bound(r)]
        if len(matches)!=1 or matches[0][0] in assigned:
            raise BehaviorError('property-binding-mismatch',p['id'])
        i,r=matches[0]; assigned.add(i)
        function=f"{plan['top']}_{ {'assert':'a','assume':'u','cover':'c'}[r['kind']]} {r['index']}"
        definition=definitions[function]
        if re.search(r'\)\) Bool\s',definition) is None:
            raise BehaviorError('property-binding-mismatch','property function must return Bool')
        result.append(dict(r,id=p['id'],compiled_label=label,top=plan['top'],smt_function=function,
            smt_definition_sha256=hashlib.sha256(definition.encode()).hexdigest(),
            source_binding={k:p.get(k) for k in ('source_file','source_line','source_sha256')}))
    if len(assigned)!=len(records): raise BehaviorError('property-binding-mismatch','unexpected exported property')
    return result

def _solver_description(prop):
    return f"{prop['source']} ({prop['name']})" if prop['source'] else prop['name']

def _solver_match(path,description,inventory,kind):
    matches=[p for p in inventory if p['kind']==kind and path==p['top'] and description==_solver_description(p)]
    if len(matches)!=1: raise BehaviorError('property-binding-mismatch',path+': '+description)
    return matches[0]

def parse_formal_result(stdout,returncode,mode,expected_property_ids, *, inventory=None, bound=None):
    expected_property_ids=list(expected_property_ids)
    if not expected_property_ids: raise BehaviorError('zero-or-wrong-obligation-count','empty proof/cover roster')
    if returncode!=0 or 'Status: PASSED' not in stdout or 'Status: FAILED' in stdout:
        raise BehaviorError('assertion-counterexample' if mode=='assert' and returncode==1 and 'Status: FAILED' in stdout else 'tool-error',stdout[-2000:])
    if inventory is None or bound is None: raise BehaviorError('property-binding-mismatch','inventory and bound required')
    if mode=='cover':
        reached=re.findall(r'Reached cover statement in step (\d+) at ([^:]+): ([^\n]+)',stdout)
        if len(reached)!=len(expected_property_ids): raise BehaviorError('cover-unreachable','missing cover witnesses')
        observed={}
        for step,path,description in reached:
            prop=_solver_match(path,description,inventory,'cover')
            if prop['id'] in observed: raise BehaviorError('property-binding-mismatch','duplicate cover')
            if int(step)>=bound: raise BehaviorError('bound-mismatch',step)
            observed[prop['id']]=dict(id=prop['id'],category='cover-reached',step=int(step),site=path+': '+description)
        if set(observed)!=set(expected_property_ids): raise BehaviorError('property-binding-mismatch','cover ID set')
        checked={int(n) for n in re.findall(r'Checking cover reachability in step (\d+)',stdout)}
        if not checked or min(checked)!=0 or max(checked)>=bound or not set(int(x[0]) for x in reached)<=checked:
            raise BehaviorError('bound-mismatch','cover reachability steps')
        return [observed[p] for p in expected_property_ids]
    if mode!='assert': raise ValueError(mode)
    if set(expected_property_ids)!={p['id'] for p in inventory if p['kind']=='assert'}:
        raise BehaviorError('property-binding-mismatch','assertion ID set')
    steps={int(n) for n in re.findall(r'Checking assertions in step (\d+)',stdout)}
    if steps!=set(range(bound)):
        raise BehaviorError('bound-mismatch',f'checked {sorted(steps)}, required {bound} states')
    return [dict(id=p,category='passed') for p in expected_property_ids]

def parse_false_control(stdout,returncode,inventory):
    steps=re.findall(r'Checking assertions in step (\d+)',stdout)
    failures=re.findall(r'Assert failed in ([^:]+): ([^\n]+)',stdout)
    if returncode!=1 or 'Status: FAILED' not in stdout or steps!=['0'] or len(failures)!=1:
        raise BehaviorError('control-failure','false assertion did not yield normal step-0 counterexample')
    prop=_solver_match(*failures[0],inventory,'assert')
    if prop['id']!='A-CONTROL-FALSE' or len(inventory)!=1:
        raise BehaviorError('control-failure','wrong false assertion')
    return dict(id=prop['id'],category='assertion-counterexample',step=0)

def parse_overconstraint(stdout,returncode,inventory):
    steps=re.findall(r'Checking cover reachability in step (\d+)',stdout)
    reached=re.findall(r'Reached cover statement in step (\d+) at ([^:]+): ([^\n]+)',stdout)
    missed=re.findall(r'Unreached cover statement at ([^:]+): ([^\n]+)',stdout)
    if returncode!=1 or 'Status: FAILED' not in stdout or not steps or set(steps)!={'0'} or len(reached)!=1 or reached[0][0]!='0' or len(missed)!=1:
        raise BehaviorError('control-failure','overconstraint must normally finish one-step cover completion')
    local=_solver_match(reached[0][1],reached[0][2],inventory,'cover')
    secondary=_solver_match(*missed[0],inventory,'cover')
    ids={p['id'] for p in inventory}
    if local['id']!='C-MUX-LOCAL/NF_SINGLE' or secondary['id']!='C-MUX-SECONDARY/NF_SINGLE' or ids!={'A-MUX-ORDER/NF_SINGLE','C-MUX-LOCAL/NF_SINGLE','C-MUX-SECONDARY/NF_SINGLE','H-CONTROL-SELECT0'}:
        raise BehaviorError('control-failure','wrong reachable/unreachable/control property')
    if 'Assert failed' in stdout: raise BehaviorError('control-failure','unexpected assertion failure')
    return dict(id='H-CONTROL-SELECT0',category='cover-unreachable',reason='overconstrained',unreachable=secondary['id'])

def write_unknown_output(output_path, value):
    """Inject a post-initialization observation fault into the shared checker.

    This is a four-state checker control, not a claim that legal DUT operation
    produces an unknown. Signal observed is first explicitly initialized to 0.
    """
    if value not in ('x','z'): raise ValueError(value)
    lines=_start('reg observed=0;'); ids=Witnesses()
    lines+=['initial begin',f"#10; observed=1'b{value}; #10;"]
    _obs(lines,ids,f'S-POSTINIT-{value.upper()}','observed',0)
    _finish(lines,output_path,ids)
    return ids
