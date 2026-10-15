#!/usr/bin/env python3
"""Fixture transcription audit. Reads only independent literal files; no repo imports.
Never emits or repairs golden data. Checks fixed expectations, not general model
legality and not production implementation conformance.
"""
from pathlib import Path
import hashlib,json,re
P=Path(__file__).resolve().parent
DIGEST=re.compile('[0-9a-f]{64}\\Z')
U64=re.compile('(0|[1-9][0-9]*)\\Z')

def fields(o,expected):
    assert isinstance(o,dict)
    assert set(o)==set(expected.split()),(set(o),expected)

def number(v):
    assert isinstance(v,str) and U64.fullmatch(v) and int(v)<=2**64-1,v

def provenance(o):
    fields(o,'display span')
    assert o['display'] is None or isinstance(o['display'],str)
    if o['span'] is not None:
        s=o['span'];fields(s,'source source_bytes start end')
        for k in ['source_bytes','start','end']: number(s[k])
        assert 0<=int(s['start'])<=int(s['end'])<=int(s['source_bytes'])

def key(o,kind):
    fields(o,'kind namespace scope local');assert o['kind']==kind
    assert o['namespace']=='golden'
    assert isinstance(o['scope'],list)

def domain(o):
    fields(o,'key kind provenance');key(o['key'],'domain');provenance(o['provenance'])

def ref(o):
    fields(o,'kind name path provenance');assert o['kind']=='bel';provenance(o['provenance'])

def fieldref(o):
    fields(o,'name path provenance');provenance(o['provenance'])

def endpoint(o):
    fields(o,'pin provenance resource');ref(o['resource']);provenance(o['provenance'])

def connection(o):
    fields(o,'destination name provenance selector sources');provenance(o['provenance'])
    endpoint(o['destination'])
    for x in o['sources']: endpoint(x)
    if o['selector'] is not None: fieldref(o['selector'])

def instance(o,root):
    fields(o,'domains name partition provenance template');key(o['template'],'template');provenance(o['provenance'])
    if o['partition'] is not None: number(o['partition']);assert int(o['partition'])<=2**32-1
    else: assert not root
    for d in o['domains']: domain(d)

def architecture(o):
    body=o['body'];fields(body,'connections domains namespace partitions provenance resource_types roots semantic_id templates')
    assert DIGEST.fullmatch(body['semantic_id']);provenance(body['provenance'])
    for x in body['connections']: connection(x)
    for x in body['domains']: domain(x)
    for x in body['partitions']:number(x)
    for x in body['roots']:instance(x,True)
    for t in body['resource_types']:
        fields(t,'key kind modes pins provenance');key(t['key'],'resource_type');provenance(t['provenance'])
        for pin in t['pins']:
            fields(pin,'direction name provenance width');number(pin['width']);provenance(pin['provenance'])
    for t in body['templates']:
        fields(t,'children connections features key mode_groups provenance resources storage');key(t['key'],'template');provenance(t['provenance'])
        for x in t['children']:instance(x,False)
        for x in t['connections']:connection(x)
        for r in t['resources']:
            fields(r,'alias_of domains kind name provenance resource_type');key(r['resource_type'],'resource_type');provenance(r['provenance'])
            if r['alias_of'] is not None:ref(r['alias_of'])
            for d in r['domains']:domain(d)
        for g in t['mode_groups']:
            fields(g,'modes name provenance resources');provenance(g['provenance'])
            for r in g['resources']:ref(r)
        for s in t['storage']:
            fields(s,'bits name owner provenance');ref(s['owner']);number(s['bits']);provenance(s['provenance'])
        for f in t['features']:
            fields(f,'alias_of domain guard name owner provenance range storage width');ref(f['owner']);provenance(f['provenance']);number(f['width'])
            fields(f['range'],'length start unit');assert f['range']['unit']=='bit'
            number(f['range']['length']);number(f['range']['start'])
            assert int(f['range']['length'])==int(f['width'])
            assert int(f['range']['length'])+int(f['range']['start'])<=2**64-1
            if f['alias_of'] is not None:fieldref(f['alias_of'])
            d=f['domain']
            if d['kind']=='any': fields(d,'kind')
            elif d['kind']=='set':
                fields(d,'kind values')
                for v in d['values']:number(v)
            else:assert False,'unexpected fixture domain'
            assert f['guard']==[]

prefix={'architecture':b'nodal-fpga.arch.semantic.v1\n','package':b'nodal-fpga.package.build.v1\n','design':b'nodal-fpga.design.semantic.v1\n'}
for line in (P/'SHA256SUMS').read_text().splitlines():
    sha,name=line.split('  ',1)
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==sha,name

for f in P.glob('*.canonical.json'):
    b=f.read_bytes();assert b[:1]==b'{' and b[-1:]==b'}' and not b.startswith(b'\xef\xbb\xbf')
    def ordered(pairs):
        keys=[k.encode('utf-8') for k,v in pairs]
        assert keys==sorted(keys) and len(keys)==len(set(keys)),f
        return dict(pairs)
    o=json.loads(b,object_pairs_hook=ordered)
    fields(o,'annotations body format optional_features profile required_features version')
    fields(o['version'],'major minor');assert o['version']=={'major':0,'minor':1}
    fields(o['profile'],'id revision');assert o['profile']['revision']==1
    assert len(o['required_features'])==1
    for e in o['required_features']+o['optional_features']:fields(e,'id revision')
    stem=f.name.removesuffix('.canonical.json');kind=stem.split('-')[0]
    projection=(P/(stem+'.projection.json')).read_bytes()
    expected=hashlib.sha256(prefix[kind]+projection).hexdigest()
    id_field='build_id' if kind=='package' else 'semantic_id'
    assert o['body'][id_field]==expected
    if kind=='architecture':architecture(o)

A=json.loads((P/'architecture.canonical.json').read_bytes())['body']
assert [r['name'] for r in A['roots']]==['t0','t1','t2']
assert len(A['resource_types'])==len(A['templates'])==1
T=A['templates'][0]
assert [r['name'] for r in T['resources']]==['east','local','sink','west']
assert [p['name'] for p in A['resource_types'][0]['pins']]==['I','O']
assert [s['resource']['name'] for s in T['connections'][0]['sources']]==['east','local','west']
assert T['features'][0]['domain']=={'kind':'set','values':['0','1','2']}
assert [r['domains'][-1]['key']['local'] for r in A['roots']]==['power0','power1','power1']
for i,e in enumerate(A['connections']):
    assert e['name']=='edge'+str(i)
    assert e['sources'][0]['resource']['path']==['t'+str(i)]
    assert e['sources'][0]['resource']['name']=='sink' and e['sources'][0]['pin']=='O'
    assert e['destination']['resource']['path']==['t'+str(i+1)]
    assert e['destination']['resource']['name']=='west' and e['destination']['pin']=='I'

H=json.loads((P/'architecture-hierarchy.canonical.json').read_bytes())['body']
assert [t['key']['local'] for t in H['templates']]==['leaf','wrapper']
assert [c['name'] for c in H['templates'][1]['children']]==['..','a/b']
assert all(c['partition'] is None for c in H['templates'][1]['children'])
assert H['connections'][0]['sources'][0]['resource']['path']==['r','..']
assert H['connections'][0]['destination']['resource']['path']==['r','a/b']
AL=json.loads((P/'architecture-alias.canonical.json').read_bytes())['body']['templates'][0]['features']
assert AL[0]['name']=='F' and AL[0]['alias_of'] is None
assert AL[1]['name']=='alias' and AL[1]['alias_of']['name']=='F'
for k in ['owner','storage','range','width','domain']:assert AL[0][k]==AL[1][k]

HI=json.loads((P/'architecture-high-u64.canonical.json').read_bytes())['body']['templates'][0]
assert HI['storage'][0]['bits']=='18446744073709551615'
assert HI['features'][0]['range']=={'length':'1','start':'18446744073709551614','unit':'bit'}
assert HI['features'][0]['width']=='1'

PK=json.loads((P/'package.canonical.json').read_bytes())['body']
fields(PK,'activation architecture authoring backend build_id compiler configuration_map device_db external_pin_map libraries macro_bindings physical_implementation technology timing_datasets transport')
fields(PK['architecture'],'artifact semantic_id');fields(PK['architecture']['artifact'],'bytes sha256')
raw=(P/'architecture.raw.json').read_bytes();assert len(raw)==6624
assert PK['architecture']['artifact']['bytes']=='6624'
assert PK['architecture']['artifact']['sha256']==hashlib.sha256(raw).hexdigest()
assert PK['architecture']['semantic_id']==A['semantic_id']
assert PK['authoring']=={'state':'unbound','reason':'not-supplied'}
assert PK['libraries']==[] and PK['macro_bindings']=={'state':'absent','reason':'no-hard-macros'}
for k in ['activation','backend','compiler','configuration_map','device_db','external_pin_map','physical_implementation','technology','timing_datasets','transport']:
    assert PK[k]=={'state':'unbound','reason':'foundation-unimplemented'}

D=json.loads((P/'design.canonical.json').read_bytes())['body']
fields(D,'cells name namespace nets ports provenance semantic_id target_build_id')
assert D['target_build_id']==PK['build_id']
assert [c['name'] for c in D['cells']]==['c0','c1']
assert [p['name'] for p in D['ports']]==['flag','in','out']
assert len(D['nets'])==4
terminal=[];drivers=0;loads=0
for c in D['cells']:
    fields(c,'mode name provenance resource_type');key(c['resource_type'],'resource_type');provenance(c['provenance'])
for p in D['ports']:
    fields(p,'direction name provenance width');number(p['width']);provenance(p['provenance'])
for n in D['nets']:
    fields(n,'driver loads name provenance');provenance(n['provenance']);drivers+=1;loads+=len(n['loads'])
    for e in [n['driver']]+n['loads']:
        provenance(e['provenance'])
        if e['kind']=='constant':fields(e,'kind provenance value');assert e['value']=='1';assert e is n['driver']
        elif e['kind']=='cell':
            fields(e,'bit cell kind pin provenance');assert e['bit']=='0';terminal.append(('cell',e['cell'],e['pin'],e['bit']))
        else:
            fields(e,'bit kind port provenance');terminal.append(('port',e['port'],e['bit']))
assert drivers==4 and loads==5 and len(terminal)==len(set(terminal))==8
assert ('port','in','1') not in terminal
assert (P/'architecture.projection.json').read_bytes()==(P/'architecture-cold-edit.projection.json').read_bytes()
assert (P/'package.projection.json').read_bytes()!=(P/'package-cold-edit.projection.json').read_bytes()
assert (P/'design.projection.json').read_bytes()!=(P/'design-cold-target.projection.json').read_bytes()

# The original algorithm corpus stays byte-for-byte bound to its report hashes.
report=Path('/tmp/fnd05-independent-expectations.md').read_text()
entries=re.findall(r'### (C\d\d).*?Length: (\d+) bytes\. SHA-256: `([0-9a-f]{64})`',report,re.S)
assert len(entries)==39
for name,count,digest in entries:
    data=(Path('/tmp/fnd05-independent-vectors')/(name+'.json')).read_bytes()
    assert len(data)==int(count) and hashlib.sha256(data).hexdigest()==digest,name

print('PASS: 46 data-artifact hashes; closed field inventories; literal object ordering; self-ID hash inputs; exact package binding; fixed primary/hierarchy/alias/high-u64/design expectations; all 39 C00-C38 bytes unchanged.')
print('This audit did not call candidate code or establish FND-05 implementation acceptance.')
