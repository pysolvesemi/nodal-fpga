"""Execute the frozen behavior corpus through the qualified Session boundary.

No discovery or installation, shell pipelines, production oracles, implicit
EMULATION mode, or remote publication. Tool execution happens only when called
by the coordinator after source/manifest/environment review.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

from reference_results import exact_roster, require


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _capture(result):
    raw=Path(result.stdout_path).read_bytes()
    err=Path(result.stderr_path).read_bytes()
    portable=result.portable()
    require(_digest(result.stdout_path)==portable['stdout_sha256'] and len(raw)==portable['stdout_bytes'], 'stdout capture identity changed')
    require(_digest(result.stderr_path)==portable['stderr_sha256'] and len(err)==portable['stderr_bytes'], 'stderr capture identity changed')
    return raw.decode('utf-8',errors='strict'),err.decode('utf-8',errors='strict')


def _artifacts(work, suffixes):
    rows=[]
    for p in sorted(Path(work).rglob('*')):
        if p.is_file() and any(p.name.endswith(s) for s in suffixes):
            require(not p.is_symlink(),'symlink artifact')
            rows.append(dict(path=p.relative_to(work).as_posix(),sha256=_digest(p),bytes=p.stat().st_size))
    return rows


def _execute(session, identifier, argv, *, inputs=None, expected_exit=0):
    result,work=session.execute(identifier,argv,inputs=inputs,expected_exit=expected_exit)
    stdout,stderr=_capture(result)
    return result,work,stdout,stderr


def _source_directory(session, identifier):
    path=Path(session.output)/'authored-testbenches'/identifier
    path.mkdir(parents=True,exist_ok=False)
    return path


def _simulation(session, behavior, run, name, generated, writer, *writer_args, negative=None):
    from reference_checks import sources
    base=f'run{run}-sim-{name}'
    authored=_source_directory(session,base)
    testbench=authored/'tb.sv'
    witnesses=writer(*writer_args,testbench)
    bindings=dict(witnesses.bindings)
    (authored/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
    argv=[session.environment.command('iverilog'),'-g2012','-s','tb','-o','/work/test.vvp']
    inputs={'/inputs/testbench':authored}
    if generated is not None:
        argv+=sources(generated); inputs['/inputs/generated']=generated
    argv+=['/inputs/testbench/tb.sv']
    compiled,compiled_work,_,_=_execute(session,base+'-compile',argv,inputs=inputs)
    binary=compiled_work/'test.vvp'
    require(binary.is_file() and binary.stat().st_size>0,'simulator binary missing')
    executed,work,stdout,stderr=_execute(session,base,
        [session.environment.command('vvp'),'/inputs/compiled/test.vvp'],
        inputs={'/inputs/compiled':compiled_work},expected_exit=1 if negative else 0)
    common=dict(executed=True,stage=base,source_sha256=_digest(testbench),binary_sha256=_digest(binary))
    if negative:
        matches=re.findall(r'^NONBINARY\t([^\t]+)\t(\d+)\t([^\n]+)$',stdout,re.M)
        require(len(matches)==1 and matches[0][0]==negative and int(matches[0][1])>0,
                'unknown-output control missing named signal/time')
        symbol='x' if negative.endswith('-X') else 'z'
        require(symbol in matches[0][2].lower() and 'non-binary-output' in stdout+stderr,
                'unknown-output control rejected for an unrelated reason')
        require('DONE\t' not in stdout,'unknown-output control incorrectly completed')
        records=[dict(id=negative,category='invalid-input',diagnostic='non-binary-output',
            time=int(matches[0][1]),observed=matches[0][2],binding=bindings[negative],**common)]
    else:
        records=behavior.parse_simulation(stdout,witnesses)
        for row in records: row.update(common,binding=bindings[row['id']])
    stage=dict(id=base,kind='simulation',executed=True,required=len(witnesses),observed=len(records),
               compile_stage=base+'-compile',compile_process=compiled.portable(),process=executed.portable(),
               testbench_sha256=_digest(testbench),binary_sha256=_digest(binary))
    return records,stage


def _lowered_inventory(path, plan, exported):
    data=json.loads(Path(path).read_text())
    modules=data.get('modules',{})
    require(plan['top'] in modules,'formal top missing from lowered JSON')
    actual=[]
    for module,body in modules.items():
        for name,cell in body.get('cells',{}).items():
            if cell['type'] in ('$assert','$assume','$cover','$check'):
                require(module==plan['top'] and cell['type']!='$check','unexpected/unlowered formal cell')
                actual.append(dict(name=name,kind=cell['type'][1:],source=cell.get('attributes',{}).get('src','')))
    require(len(actual)==len(exported),'lowered/exported property count differs')
    used=set(); rows=[]
    for prop in exported:
        candidates=[(i,c) for i,c in enumerate(actual) if c['kind']==prop['kind'] and
                    (c['name']==prop['name'] or (prop['source'] and c['source']==prop['source']) or
                     re.search(r'(?<![A-Za-z0-9_])'+re.escape(prop['compiled_label'])+r'(?![A-Za-z0-9_])',c['name']))]
        require(len(candidates)==1 and candidates[0][0] not in used,'lowered/exported property identity differs')
        index,cell=candidates[0]; used.add(index)
        binding=prop.get('source_binding',{})
        require(binding.get('source_file') and type(binding.get('source_line')) is int and
                re.search(re.escape(binding['source_file'])+':'+str(binding['source_line'])+r'\.',cell['source']) is not None,
                'lowered property source differs from authored declaration')
        rows.append(dict(prop,lowered_cell=cell['name'],lowered_source=cell['source']))
    return rows


def _formal_export(session, behavior, run, logical_top, generated):
    from reference_checks import sources
    name=logical_top.replace('-','_')
    stage=f'run{run}-formal-{name}-export'
    plan=behavior.formal_plan(logical_top,sources(generated),'/work/model.smt2')
    result,work,stdout,stderr=_execute(session,stage,
        [session.environment.command('yosys'),'-Q','-T','-p',plan['script']],
        inputs={'/inputs/generated':generated},expected_exit=1 if logical_top=='zero-control' else 0)
    if logical_top=='zero-control':
        require(re.search(r'selection contains 0 elements instead of the asserted 1',stdout+stderr) is not None
                and 't:$assert' in stdout+stderr,'zero-export control did not fail assertion count guard')
        require(not (work/'model.smt2').exists(),'zero-export control reached SMT export')
        return plan,[],work,dict(id='X-CONTROL-ZERO-EXPORT',category='zero-or-wrong-obligation-count',
             executed=True,stage=stage,solver_executed=False,process=result.portable())
    smt=work/'model.smt2'; lowered=work/'model.smt2.json'
    require(smt.is_file() and lowered.is_file(),'formal artifacts missing')
    inventory=behavior.parse_formal_inventory(smt.read_text(),plan)
    inventory=_lowered_inventory(lowered,plan,inventory)
    for p in inventory:
        p.update(smt_sha256=_digest(smt),lowered_json_sha256=_digest(lowered))
    (work/'bound-properties.json').write_text(json.dumps(inventory,indent=2)+'\n')
    return plan,inventory,work,dict(id=stage,kind='formal-export',executed=True,
        process=result.portable(),artifacts=_artifacts(work,('.smt2','.json')))


def _formal_solve(session, behavior, run, plan, inventory, export_work, *, cover=False, expected_exit=0):
    name=plan['logical_top'].replace('-','_'); mode='cover' if cover else 'assert'
    stage=f'run{run}-formal-{name}-{mode}'
    argv=[session.environment.command('yosys-smtbmc'),'-s','z3','-t',str(plan['bound'])]
    if cover: argv+=['-c']
    argv+=['--dump-vcd','/work/trace%.vcd' if cover else '/work/trace.vcd','/inputs/formal/model.smt2']
    result,work,stdout,stderr=_execute(session,stage,argv,inputs={'/inputs/formal':export_work},expected_exit=expected_exit)
    artifacts=_artifacts(work,('.vcd',))
    ids=[p['id'] for p in inventory if p['kind']==mode]
    if plan['logical_top']=='false-control':
        records=[behavior.parse_false_control(stdout,result.returncode,inventory)]
    elif plan['logical_top']=='overconstraint-control' and cover:
        records=[behavior.parse_overconstraint(stdout,result.returncode,inventory)]
    else:
        records=behavior.parse_formal_result(stdout,result.returncode,mode,ids,inventory=inventory,bound=plan['bound'])
    if cover or expected_exit:
        require(artifacts and all(a['bytes']>0 for a in artifacts),'formal witness trace missing')
    bindings={p['id']:p for p in inventory}
    for row in records:
        row.update(executed=True,stage=stage,bound=plan['bound'],top=plan['top'],
                   property=bindings.get(row['id']),smt_sha256=_digest(export_work/'model.smt2'),traces=artifacts)
    return records,dict(id=stage,kind='formal-cover' if cover else 'formal-assertion',
        executed=True,bound=plan['bound'],top=plan['top'],process=result.portable(),artifacts=artifacts)


def run_behavior(session, run, generated):
    """Run positive simulations/proofs and controls; mutations/Rust remain separate."""
    from reference_checks import fixture_module
    require(type(run) is int and run>0,'invalid run identifier')
    require(set(generated)=={'one','square','odd','sparse'},'behavior requires all four generated shapes')
    behavior=fixture_module(session.root,'behavior')
    fixture=Path(session.root)/'verify/fixtures/fnd-06'
    manifest=json.loads((fixture/'obligations.json').read_text())
    mutations=json.loads((fixture/'mutations.json').read_text())
    semantic=json.loads((fixture/'semantic_cases.json').read_text())
    result={k:[] for k in ('simulation','supplemental_simulation','formal','controls','negative_cases','mutation_baselines','stages','execution_stages')}
    result['inventories']={}
    simulation=[]
    for shape in ('one','square','odd','sparse'):
        rows,stage=_simulation(session,behavior,run,shape,generated[shape],behavior.write_simulation,shape)
        simulation+=rows; stage.update(id=f'SIM-{shape}/run-{run}',stage=stage['id'],category='passed',process_stage=stage['id'])
        result['stages'].append(stage)
    rows,stage=_simulation(session,behavior,run,'lut-unit',generated['one'],behavior.write_lut_unit)
    simulation+=rows; result['execution_stages'].append(stage)
    for variant,shape in [('NF_SINGLE','one'),('NF_LEFT','square'),('NF_MID','odd'),('NF_RIGHT','square')]:
        rows,stage=_simulation(session,behavior,run,variant,generated[shape],behavior.write_units,variant)
        simulation+=rows; result['execution_stages'].append(stage)
    planned={r['id'] for r in manifest['simulation']}; supplements={r['id'] for r in manifest['supplemental_simulation']}
    for row in simulation:
        if row['id'] in planned: result['simulation'].append(row)
        elif row['id'] in supplements: result['supplemental_simulation'].append(row)
        elif row['id']=='M-CONFIG-CONSUMER/behavior': result['mutation_baselines'].append(row)
        else: raise ValueError('unexpected simulation witness '+row['id'])
    exact_roster(manifest['simulation'],result['simulation'],section='simulation')
    exact_roster(manifest['supplemental_simulation'],result['supplemental_simulation'],section='supplemental simulation')
    for top in ('lut','switch-NF_SINGLE','switch-NF_LEFT','switch-NF_MID','switch-NF_RIGHT','register'):
        shape='odd' if top=='switch-NF_MID' else 'square' if top in ('switch-NF_LEFT','switch-NF_RIGHT') else 'one'
        plan,inventory,work,stage=_formal_export(session,behavior,run,top,generated[shape])
        result['execution_stages'].append(stage); result['inventories'][top]=inventory
        for cover in (False,True):
            rows,stage=_formal_solve(session,behavior,run,plan,inventory,work,cover=cover)
            result['formal']+=rows; result['execution_stages'].append(stage)
        for p in inventory:
            if p['kind']=='assume':
                result['formal'].append(dict(id=p['id'],category='constraint-present',executed=True,
                    stage=f'run{run}-formal-{top.replace("-","_")}-assert',property=p,bound=plan['bound']))
    exact_roster(manifest['formal'],result['formal'],section='formal')
    for top in ('false-control','zero-control','overconstraint-control'):
        plan,inventory,work,stage=_formal_export(session,behavior,run,top,generated['one'])
        if top=='zero-control': result['controls'].append(stage); continue
        result['execution_stages'].append(stage); result['inventories'][top]=inventory
        if top=='overconstraint-control':
            _,stage=_formal_solve(session,behavior,run,plan,inventory,work)
            result['execution_stages'].append(stage)
        rows,stage=_formal_solve(session,behavior,run,plan,inventory,work,
            cover=top=='overconstraint-control',expected_exit=1)
        result['controls']+=rows; result['execution_stages'].append(stage)
    exact_roster(mutations['controls'],result['controls'],section='anti-vacuity controls')
    for value in ('x','z'):
        identity='S-POSTINIT-'+value.upper()
        def writer(path,value=value): return behavior.write_unknown_output(path,value)
        rows,stage=_simulation(session,behavior,run,'postinit-'+value,None,writer,negative=identity)
        result['negative_cases']+=rows; result['execution_stages'].append(stage)
    expected=[r for r in semantic['negative_cases'] if r['id'].startswith('S-POSTINIT-')]
    exact_roster(expected,result['negative_cases'],section='postinit unknown controls')
    (Path(session.output)/f'run{run}-behavior-observations.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
