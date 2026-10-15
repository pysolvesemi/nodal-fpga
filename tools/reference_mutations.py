"""Frozen FND-06 mutants: unique patches, fresh derivatives, semantic detection.

Only the declared derivative is exempt from the baseline generation digest.
Compilation errors, missing witnesses and crashes never receive mutation credit.
"""
from __future__ import annotations
import copy
import difflib
import hashlib
import json
from pathlib import Path
import re

from reference_results import require, portable_rtl_inventory, exact_roster

IDS = ('M-MUX-INDEX','M-LUT-BIT','M-CONFIG-ADDRESS','M-PRIORITY',
       'M-CORR-SWAP','M-CORR-OMIT','M-CORR-DUPLICATE','M-ENDPOINT-OMIT',
       'M-ENDPOINT-REVERSE','M-FIELD-ALIAS','M-ALIAS-CONFLICT','M-CONFIG-CONSUMER')
RTL_TARGETS = {
    'M-MUX-INDEX': ('one','Tile/NF_SINGLE/NF_SINGLE_switch_matrix.v'),
    'M-LUT-BIT': ('one','BEL/LUT4c_frame_config_dffesr.v'),
    'M-CONFIG-ADDRESS': ('one','Tile/NF_SINGLE/NF_SINGLE_ConfigMem.v'),
    'M-PRIORITY': ('one','BEL/LUT4c_frame_config_dffesr.v'),
    'M-ENDPOINT-OMIT': ('odd','Fabric/eFPGA.v'),
    'M-CONFIG-CONSUMER': ('one','Tile/NF_SINGLE/NF_SINGLE.v'),
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encode(value):
    return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()

def manifest(root):
    path=Path(root)/'verify/fixtures/fnd-06/mutations.json'
    data=json.loads(path.read_text())
    rows=data['mutations']
    require(tuple(r['id'] for r in rows)==IDS,'frozen mutation identities/order differ')
    return {r['id']:r for r in rows},digest(path.read_bytes())

def one_match(pattern,text,label):
    matches=list(re.finditer(pattern,text,re.S))
    require(len(matches)==1,label+': patch requires one exact occurrence')
    return matches[0]

def patch_ports(text,instance,changes):
    cell=one_match(r'\b'+re.escape(instance)+r'\s*\((?P<body>.*?)\)\s*;',text,instance)
    body=cell['body']; edits=[]
    for port,(old,new) in changes.items():
        match=one_match(r'\.'+re.escape(port)+r'\s*\(\s*(?P<value>[^()]*)\s*\)',body,instance+'.'+port)
        require(re.sub(r'\s+','',match['value'])==re.sub(r'\s+','',old),instance+'.'+port+': unexpected parent connection')
        start,end=match.span('value'); edits.append((start,end,new))
    for start,end,new in sorted(edits,reverse=True): body=body[:start]+new+body[end:]
    start,end=cell.span('body')
    return text[:start]+body+text[end:], {'instance':instance,'ports':list(changes),'start':start,'end':end,'occurrences':1}

def patch_rtl(identifier,parent):
    text=parent.decode('utf-8')
    if identifier=='M-MUX-INDEX':
        result,span=patch_ports(text,'inst_cus_mux21_L_I0',{'A0':('L_I0_input[0]','L_I0_input[1]'),'A1':('L_I0_input[1]','L_I0_input[0]')})
    elif identifier=='M-LUT-BIT':
        result,span=patch_ports(text,'inst_cus_mux161',{'A1':('LUT_values[1]','LUT_values[8]'),'A8':('LUT_values[8]','LUT_values[1]')})
    elif identifier=='M-CONFIG-ADDRESS':
        result,span=patch_ports(text,'Inst_frame0_bit12',{'D':('FrameData[12]','FrameData[13]')})
    elif identifier=='M-ENDPOINT-OMIT':
        result,span=patch_ports(text,'Tile_X1Y0_NF_MID',{'W':('Tile_X0Y0_E',"1'b0")})
    elif identifier=='M-CONFIG-CONSUMER':
        result,span=patch_ports(text,'Inst_NF_SINGLE_switch_matrix',{'ConfigBits':('ConfigBits[20-1:19]','ConfigBits[16]')})
    elif identifier=='M-PRIORITY':
        pattern=r'if\s*\(EN\)\s*begin\s*if\s*\(SR\)\s*LUT_flop\s*<=\s*c_reset_value;\s*else\s*LUT_flop\s*<=\s*LUT_out;\s*end'
        match=one_match(pattern,text,'register EN/SR block')
        start,end=match.span(); result=text[:start]+'if (SR) LUT_flop <= c_reset_value; else if (EN) LUT_flop <= LUT_out;'+text[end:]
        span={'instance':'LUT4c_frame_config_dffesr','start':start,'end':end,'occurrences':1}
    else: raise ValueError('not an RTL mutation: '+identifier)
    require(result!=text,'mutation did not change bytes')
    return result.encode(),span

def derive_json(identifier,parent):
    candidate=copy.deepcopy(parent)
    if identifier=='M-CORR-SWAP':
        pins=candidate['pin_map']; pins['lut.i0']['reference'],pins['lut.i3']['reference']=pins['lut.i3']['reference'],pins['lut.i0']['reference']
        location='/pin_map/{lut.i0,lut.i3}/reference'
    elif identifier=='M-CORR-OMIT':
        del candidate['pin_map']['y']; location='/pin_map/y'
    elif identifier=='M-CORR-DUPLICATE':
        candidate['pin_map']['lut.i3']['reference']=candidate['pin_map']['lut.i0']['reference']; location='/pin_map/lut.i3/reference'
    elif identifier=='M-FIELD-ALIAS':
        require(candidate['config_map'][19]['tile_config_bit']==19,'source physical parent bit')
        candidate['config_map'][19]['tile_config_bit']=16; location='/config_map/19/tile_config_bit'
    elif identifier=='M-ENDPOINT-REVERSE':
        require(candidate[0]==['t00.e','t10.w'],'directed edge parent')
        candidate[0]=['t10.w','t00.e']; location='/0'
    elif identifier=='M-ALIAS-CONFLICT':
        require(candidate==alias_input(0),'agreeing alias baseline')
        candidate['requests']['source']=1; location='/requests/source'
    else: raise ValueError('not a JSON mutation: '+identifier)
    return candidate,{'json_pointer':location,'occurrences':1}

def alias_input(source):
    return {'declarations':[{'feature':'ff','bit':16,'alias':'test-alias'},
                            {'feature':'source','bit':16,'alias':'test-alias'}],
            'requests':{'ff':0,'source':source}}

def materialize(root, mutation_id, baseline_input, output):
    """Create exactly one fresh labelled derivative, returning its hash binding."""
    root,output=Path(root),Path(output)
    rows,manifest_hash=manifest(root); require(mutation_id in rows,'unknown mutant')
    require(not output.exists(),'mutation output already exists')
    output.mkdir(parents=True)
    inventory={}
    if mutation_id in RTL_TARGETS:
        shape,target=RTL_TARGETS[mutation_id]
        baseline_input=Path(baseline_input)
        original=portable_rtl_inventory(baseline_input,shape)
        names=[r['path'] for r in original['artifacts']]+['sources.f','generation.json']
        for name in names:
            path=baseline_input/name
            require(path.is_file() and not path.is_symlink(),'unsafe derivative input')
            data=path.read_bytes(); inventory[name]=digest(data)
            dest=output/name; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
        parent=(output/target).read_bytes(); derived,span=patch_rtl(mutation_id,parent)
    else:
        target='candidate.json'
        parent=baseline_input if isinstance(baseline_input,bytes) else encode(baseline_input)
        candidate,span=derive_json(mutation_id,json.loads(parent))
        derived=(json.dumps(candidate,indent=2)+'\n').encode(); inventory[target]=digest(parent)
        original=None
    (output/target).write_bytes(derived)
    patch=''.join(difflib.unified_diff(parent.decode().splitlines(True),derived.decode().splitlines(True),fromfile='baseline/'+target,tofile='derived/'+target)).encode()
    require(bool(patch),'empty mutation patch')
    (output/'mutation.patch').write_bytes(patch)
    binding={'id':mutation_id,'target':target,'baseline_sha256':digest(parent),'derived_sha256':digest(derived),
             'patch_sha256':digest(patch),'manifest_sha256':manifest_hash,'location':span,
             'baseline_inventory':inventory,'baseline_artifacts':original,'parent_bytes':len(parent),'derived_bytes':len(derived)}
    (output/'mutation-binding.json').write_bytes(encode(binding))
    verify_derivative(output,binding)
    return binding

def verify_derivative(output,binding):
    output=Path(output)
    for name,sha in binding['baseline_inventory'].items():
        path=output/name
        require(path.is_file() and not path.is_symlink(),'missing/unsafe derivative file')
        wanted=binding['derived_sha256'] if name==binding['target'] else sha
        require(digest(path.read_bytes())==wanted,'undeclared derivative bytes: '+name)
    require(digest((output/'mutation.patch').read_bytes())==binding['patch_sha256'],'mutation patch changed')
    require((output/'mutation-binding.json').read_bytes()==encode(binding),'mutation binding changed')
    expected=set(binding['baseline_inventory'])|{'mutation.patch','mutation-binding.json'}
    actual={str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}
    require(actual==expected,'undeclared derivative file')

def parse_negative(stdout,identity,expected):
    """One separately executed witness; first-error simulators cannot mask peers."""
    rows=[line.split('\t') for line in stdout.splitlines() if line.startswith('OBS\t')]
    require(len(rows)==1 and len(rows[0])==5,'mutant lacks unique executed observation')
    _,key,wanted,got,time=rows[0]
    require(key==identity and re.fullmatch('[0-9a-fA-F]+',wanted) is not None and
            re.fullmatch('[0-9a-fA-F]+',got) is not None and time.isdecimal(),'wrong/nonbinary mutant witness')
    require(int(wanted,16)==expected,'mutant changed oracle value')
    require(int(got,16)!=expected and 'semantic-mismatch '+identity in stdout,'mutant lacks intended mismatch')
    require('NONBINARY\t' not in stdout and 'DONE\t' not in stdout,'unexpected simulator termination')
    return {'id':identity,'category':'semantic-mismatch','expected':expected,'observed':int(got,16),'time':int(time)}

def _simulation(session,generated,identifier,witness,negative):
    from reference_checks import fixture_module,sources
    behavior=fixture_module(session.root,'behavior')
    fixture=session.output/(identifier+'-fixture'); fixture.mkdir()
    tb=fixture/'tb.sv'
    if witness.startswith('UNIT-LUT/'):
        ids=behavior.write_lut_unit(tb,only_ids=[witness])
    elif witness.startswith(('UNIT-MUX/','UNIT-CONFIG/')):
        ids=behavior.write_units('NF_SINGLE',tb,only_ids=[witness])
    else:
        ids=behavior.write_simulation('odd' if witness.startswith('ROW-ODD/') else 'one',tb,only_ids=[witness])
    compile_result,work=session.execute(identifier+'-compile',
        [session.environment.command('iverilog'),'-g2012','-s','tb','-o','/work/test.vvp',
         *sources(generated),'/inputs/fixture/tb.sv'],inputs={'/inputs/generated':generated,'/inputs/fixture':fixture})
    result,_=session.execute(identifier+'-execute',[session.environment.command('vvp'),'/inputs/compiled/test.vvp'],
                            inputs={'/inputs/compiled':work},expected_exit=1 if negative else 0)
    stdout=result.stdout_path.read_text()
    record=parse_negative(stdout,witness,ids.expected[witness]) if negative else behavior.parse_simulation(stdout,ids)[0]
    record.update(executed=True,stage=identifier+'-execute',compile=compile_result.portable(),process=result.portable(),
                  compiled_sha256=digest((work/'test.vvp').read_bytes()),harness_sha256=digest(tb.read_bytes()))
    return record

def _structure(session,generated,identifier,shape,binding):
    from reference_checks import fixture_module,sources
    structure=fixture_module(session.root,'structure')
    verify_derivative(generated,binding)
    script='read_verilog '+' '.join(sources(generated))+'; hierarchy -check -top eFPGA; write_rtlil /work/preproc.il; proc; write_json /work/structure.json'
    result,work=session.execute(identifier+'-structure',[session.environment.command('yosys'),'-Q','-T','-p',script],
                                inputs={'/inputs/generated':generated})
    try:
        hashes={name:(binding['derived_sha256'] if name==binding['target'] else binding['baseline_inventory'][name])
                for name in (generated/'sources.f').read_text().splitlines()}
        structure.check_shape(shape,structure.read_json(work/'structure.json'),source_root=generated,source_hashes=hashes)
    except structure.StructureError as error:
        return error,{'stage':identifier+'-structure','executed':True,'process':result.portable(),
                      'artifact_sha256':digest((work/'structure.json').read_bytes())}
    require(False,'structural mutant unexpectedly passed')

def _mapping_record(error,row,execution):
    if execution.get('artifact_sha256'):
        require(bool(getattr(error,'candidate_refs',[])), 'compiled mutation lacks source attribution')
    wanted=row['required_failing_witnesses']
    affected=error.affected
    # Translate checker diagnostics into the immutable manifest vocabulary.
    diagnostics={'missing-directed-edge':'missing-intertile-edge','reversed-directed-edge':'edge-direction-mismatch'}
    diagnostic=diagnostics.get(error.diagnostic,error.diagnostic)
    require(diagnostic==row['diagnostic'],'wrong semantic structural diagnostic')
    canonical=[w for w in wanted if w.startswith(('PIN/','CONFIG/','LINK/'))]
    require(all(any(a==w or a.startswith(w+'/') for a in affected) for w in canonical),'wrong failing structural witness')
    require(error.category in ('mapping-mismatch','config-consumer-mismatch'),'wrong structural failure category')
    return dict(execution,category='mapping-mismatch',diagnostic=diagnostic,witnesses=canonical,
                expected=error.expected,observed=error.observed,candidate_refs=getattr(error,'candidate_refs',[]))

def run_mutations(session,generated_by_shape,*,baseline,alias_hook):
    from reference_checks import fixture_module
    structure=fixture_module(session.root,'structure')
    rows,_=manifest(session.root); results=[]
    for identifier,row in rows.items():
        required=row['required_failing_witnesses']
        for witness in required:
            if witness=='N-ALIAS-CONFLICT': continue
            require(witness in baseline and baseline[witness].get('executed') is True and
                    baseline[witness].get('category')=='passed' and baseline[witness].get('stage'),
                    identifier+': baseline witness missing/unqualified '+witness)
            stages={record['id']:record for record in session.processes}
            require(baseline[witness]['stage'] in stages and stages[baseline[witness]['stage']]['process'].get('returncode')==0,
                    identifier+': baseline stage lacks actual successful process '+witness)
        output=session.output/('derived-'+identifier)
        observations=[]
        if identifier in RTL_TARGETS:
            shape,_=RTL_TARGETS[identifier]; generated=generated_by_shape[shape]
            semantic=[w for w in required if not w.startswith(('CONFIG/','LINK/'))]
            if row.get('additional_required_result'):
                semantic.append(row['additional_required_result']['witness'])
            semantic=list(dict.fromkeys(semantic))
            for index,witness in enumerate(semantic):
                observations.append(_simulation(session,generated,identifier+'-baseline-'+str(index),witness,False))
            binding=materialize(session.root,identifier,generated,output)
            # A separate actual whole-fabric compile is mandatory, even for unit mutants.
            from reference_checks import sources
            compile_result,_=session.execute(identifier+'-fabric-compile',
                [session.environment.command('iverilog'),'-g2012','-s','eFPGA','-o','/work/fabric.vvp',*sources(output)],
                inputs={'/inputs/generated':output})
            if identifier in ('M-ENDPOINT-OMIT','M-CONFIG-CONSUMER'):
                error,execution=_structure(session,output,identifier,shape,binding)
                observations.append(_mapping_record(error,row,execution))
            for index,witness in enumerate(semantic):
                verify_derivative(output,binding)
                observations.append(_simulation(session,output,identifier+'-mutant-'+str(index),witness,True))
            stage=identifier+'-fabric-compile'
        else:
            if identifier=='M-ENDPOINT-REVERSE':
                parent=structure.expected('odd')[0]['intertile_edges']
                structure.check_declared_edges('odd',parent)
            elif identifier=='M-ALIAS-CONFLICT': parent=alias_input(0)
            else:
                parent=(session.root/'verify/fixtures/nf-tiny/correspondence.json').read_bytes()
                structure.check_correspondence(json.loads(parent))
            binding=materialize(session.root,identifier,parent,output)
            candidate=json.loads((output/'candidate.json').read_text())
            if identifier=='M-ALIAS-CONFLICT':
                result=alias_hook(parent,candidate,binding)
                negative=result.get('negative',{}); agreeing=result.get('baseline',{})
                require(negative.get('executed') is True and negative.get('category')=='invalid-input' and
                        negative.get('diagnostic')=='inconsistent-alias-requests' and
                        negative.get('generic_diagnostic')=='Code::Conflict' and negative.get('stage') and
                        agreeing.get('executed') is True and agreeing.get('category')=='passed' and
                        agreeing.get('id')=='alias-agree' and result.get('process') and
                        result.get('binary_sha256') and result.get('source_sha256'),
                        'missing actual generic alias evidence')
                observations.append(result)
            else:
                try:
                    if identifier=='M-ENDPOINT-REVERSE': structure.check_declared_edges('odd',candidate)
                    else: structure.check_correspondence(candidate)
                except structure.StructureError as error:
                    observations.append(_mapping_record(error,row,{'stage':identifier+'-mapping','executed':True,
                                                                  'checker_sha256':digest(Path(structure.__file__).read_bytes())}))
                else: require(False,'mapping mutant unexpectedly passed')
            stage=observations[-1]['stage']
        verify_derivative(output,binding)
        additional=row.get('additional_required_result')
        if additional:
            matches=[o for o in observations if o.get('id')==additional['witness'] and o.get('category')==additional['category']]
            require(len(matches)==1,'missing additional mutation behavior')
            observed=matches[0]
            if identifier=='M-CONFIG-CONSUMER':
                require(observed['expected']==additional['expected_y'] and observed['observed']==additional['mutant_y'],
                        'wrong config-consumer binary failure')
            elif identifier=='M-ENDPOINT-OMIT':
                # ROW-ODD packs t00,t10,t20,t01; row1 independently fixes outer bits 1,0.
                wanted=(1<<3)|(additional['expected']['t10.y']<<2)|(additional['expected']['t20.y']<<1)
                mutant=(1<<3)|(additional['mutant']['t10.y']<<2)|(additional['mutant']['t20.y']<<1)
                require(observed['expected']==wanted and observed['observed']==mutant,'wrong omitted-link row failure')
        result={'id':identifier,'category':row['expected_category'],'executed':True,'stage':stage,
                'binding':binding,'observations':observations,
                'baseline_witnesses':{w:baseline[w] for w in required if w in baseline}}
        if identifier in RTL_TARGETS: result['fabric_compile']=compile_result.portable()
        results.append(result)
        (session.output/'mutations.json').write_bytes(encode(results))
    exact_roster(list(rows.values()),results,section='mutations')
    return results


PORTABLE_BINDING_FIELDS = ('id','target','baseline_sha256','derived_sha256',
                          'patch_sha256','manifest_sha256','location','parent_bytes','derived_bytes')


def verify_published_mutations(root, results):
    """Compare fresh execution bindings with the portable archive, never an oracle."""
    root=Path(root)
    archive=root/'verify/fixtures/fnd-06/mutation-artifacts'
    require(archive.is_dir() and not archive.is_symlink(),'missing/unsafe mutation archive')
    expected_files={'inventory.json','README.md'}|{identifier+'.patch' for identifier in IDS}
    require({p.name for p in archive.iterdir()}==expected_files,'mutation archive file roster differs')
    require(all(p.is_file() and not p.is_symlink() for p in archive.iterdir()),'unsafe mutation archive file')
    raw=(archive/'inventory.json').read_bytes()
    def unique_keys(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'duplicate mutation inventory key: '+key)
            result[key]=value
        return result
    inventory=json.loads(raw,object_pairs_hook=unique_keys)
    require(isinstance(inventory,list) and tuple(r.get('id') for r in inventory)==IDS,
            'published mutation identity roster differs')
    require(isinstance(results,list) and tuple(r.get('id') for r in results)==IDS,
            'fresh mutation identity roster differs')
    frozen,manifest_sha=manifest(root)
    fields=set(PORTABLE_BINDING_FIELDS)|{'required_failing_witnesses','expected_category'}
    for archived,fresh in zip(inventory,results):
        identifier=archived['id']; row=frozen[identifier]
        require(set(archived)==fields,'unexpected portable mutation fields: '+identifier)
        binding=fresh.get('binding',{})
        require(all(key in binding and binding[key]==archived[key] for key in PORTABLE_BINDING_FIELDS),
                'published/fresh mutation binding differs: '+identifier)
        require(archived['manifest_sha256']==manifest_sha and
                archived['required_failing_witnesses']==row['required_failing_witnesses'] and
                archived['expected_category']==row['expected_category'],
                'published mutation manifest binding differs: '+identifier)
        target=archived['target']
        require(isinstance(target,str) and bool(target) and not target.startswith('/') and
                all(part not in ('','..','.') for part in target.split('/')) and
                '\\' not in target and '\n' not in target and '\r' not in target,
                'unsafe mutation target path: '+identifier)
        require(target==(RTL_TARGETS[identifier][1] if identifier in RTL_TARGETS else 'candidate.json'),
                'unexpected mutation target path: '+identifier)
        patch=(archive/(identifier+'.patch')).read_bytes()
        require(digest(patch)==archived['patch_sha256'],'published mutation patch hash differs: '+identifier)
        lines=patch.decode('utf-8').splitlines()
        require(len(lines)>2 and lines[:2]==['--- baseline/'+target,'+++ derived/'+target] and
                sum(line.startswith('--- ') for line in lines)==1 and
                sum(line.startswith('+++ ') for line in lines)==1,
                'unsafe mutation patch headers: '+identifier)
    return {'status':'passed','mutations':len(IDS),'inventory_sha256':digest(raw)}
