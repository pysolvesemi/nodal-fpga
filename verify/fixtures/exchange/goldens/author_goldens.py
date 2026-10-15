#!/usr/bin/env python3
"""Independent hand-fixture byte assembly, NOT a production canonicalizer.

All objects/arrays below are authored in their expected canonical order. This
script does not sort data or import/invoke anything from the repository. It
performs fixed literal substitution and concatenation, hashes with hashlib and
sha256sum, and uses stdlib json only to inspect the finished bytes. Semantic
projections are assembled explicitly with typed provenance slots omitted, not
by recursive name-based deletion. Keep emitted JSON files as reviewed literals.
"""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
PREFIX = {
    'arch': b'nodal-fpga.arch.semantic.v1\n',
    'design': b'nodal-fpga.design.semantic.v1\n',
    'package': b'nodal-fpga.package.build.v1\n',
}
P0 = '{"display":null,"span":null}'
PA = '{"display":"Three independent mux tiles","span":{"end":"512","source":"hand-authored/architecture.scala","source_bytes":"512","start":"0"}}'
PH = '{"display":"Literal child names","span":{"end":"80","source":"hand-authored/hierarchy.scala","source_bytes":"128","start":"8"}}'
PD = '{"display":"Target-bound structural design","span":{"end":"64","source":"hand-authored/design.json","source_bytes":"128","start":"0"}}'
PN = '{"display":"Mux selector","span":{"end":"19","source":"hand-authored/architecture.scala","source_bytes":"512","start":"17"}}'

# Each name fed here is an independently chosen literal with no JSON quoting
# requirement. Escape probes remain in immutable C00-C38, not this convenience.
def q(value):
    assert all(ord(c) >= 32 and c not in '\\"' for c in value)
    return '"' + value + '"'

def arr(*items):
    return '[' + ','.join(items) + ']'

def obj(*items):
    """Preserve the manually supplied field order; never sort or canonicalize."""
    return '{' + ','.join(k + ':' + v for k, v in items if k is not None) + '}'

def kv(k, v):
    return q(k), v

def prov(full, value=P0):
    return kv('provenance', value) if full else (None, None)

def key(local, kind='template', scope=()):
    return '{"kind":' + q(kind) + ',"local":' + q(local) + ',"namespace":"golden","scope":' + arr(*(q(s) for s in scope)) + '}'

def resource_ref(name, path=(), full=True):
    return obj(kv('kind', '"bel"'), kv('name', q(name)), kv('path', arr(*(q(s) for s in path))), prov(full))

def endpoint(name, pin, path=(), full=True):
    return obj(kv('pin', q(pin)), prov(full), kv('resource', resource_ref(name, path, full)))

def field_ref(name, path=(), full=True):
    return obj(kv('name', q(name)), kv('path', arr(*(q(s) for s in path))), prov(full))

def domain_ref(name, kind, full=True):
    return obj(kv('key', key(name, 'domain')), kv('kind', q(kind)), prov(full))

def cell_type(full=True, reverse_pins=False):
    pins = [obj(kv('direction', '"input"'), kv('name', '"I"'), prov(full), kv('width', '"1"')),
            obj(kv('direction', '"output"'), kv('name', '"O"'), prov(full), kv('width', '"1"'))]
    if reverse_pins:
        pins = [pins[1], pins[0]]
    return obj(kv('key', key('generic-cell', 'resource_type')), kv('kind', '"bel"'), kv('modes', '["alternate","normal"]'), kv('pins', arr(*pins)), prov(full))

def resource(name, full=True, alias=None):
    return obj(kv('alias_of', 'null' if alias is None else resource_ref(alias, full=full)), kv('domains', '[]'), kv('kind', '"bel"'), kv('name', q(name)), prov(full), kv('resource_type', key('generic-cell', 'resource_type')))

def instance(name, template, full=True, partition='"0"', domains='[]'):
    return obj(kv('domains', domains), kv('name', q(name)), kv('partition', partition), prov(full), kv('template', key(template)))

def connection(name, sources, dest, full=True, selector='null'):
    return obj(kv('destination', dest), kv('name', q(name)), prov(full), kv('selector', selector), kv('sources', arr(*sources)))

def template(name, full=True, children=(), connections=(), features=(), groups=(), resources=(), storage=()):
    return obj(kv('children', arr(*children)), kv('connections', arr(*connections)), kv('features', arr(*features)), kv('key', key(name)), kv('mode_groups', arr(*groups)), prov(full), kv('resources', arr(*resources)), kv('storage', arr(*storage)))

def group(full=True):
    return obj(kv('modes', '["alternate","normal"]'), kv('name', '"operation"'), prov(full), kv('resources', arr(resource_ref('sink', full=full))))

def storage(full=True, owner='sink', name='cfg', bits='2'):
    return obj(kv('bits', q(bits)), kv('name', q(name)), kv('owner', resource_ref(owner, full=full)), prov(full))

def feature(full=True, name='route', alias=None, owner='sink', width='2', start='0', length='2', domain='{"kind":"set","values":["0","1","2"]}', guard='[]'):
    return obj(kv('alias_of', 'null' if alias is None else field_ref(alias, full=full)), kv('domain', domain), kv('guard', guard), kv('name', q(name)), kv('owner', resource_ref(owner, full=full)), prov(full, PN), kv('range', '{"length":' + q(length) + ',"start":' + q(start) + ',"unit":"bit"}'), kv('storage', '"cfg"'), kv('width', q(width)))

ARCH_ANNOTATIONS='{"golden.example/review":{"count":3,"message":"independent hand fixture","unicode_order":{"\ue000":"BMP","\U00010000":"supplementary"}}}'
OPTIONAL='[{"id":"golden.example/review","revision":1}]'

def envelope(kind, body, full=True, annotations=ARCH_ANNOTATIONS, optional=OPTIONAL):
    format_id, profile, capability = {
        'arch': ('nodal-fpga.arch', 'structural-selection', 'nodal-fpga/arch.structural-selection'),
        'design': ('nodal-fpga.mapped-design', 'mapped-structural', 'nodal-fpga/design.structural'),
        'package': ('nodal-fpga.package-manifest', 'software-package', 'nodal-fpga/package.software-inspection'),
    }[kind]
    return obj(kv('annotations', annotations) if full else (None,None), kv('body', body), kv('format', q(format_id)), kv('optional_features', optional) if full else (None,None), kv('profile', '{"id":'+q(profile)+',"revision":1}'), kv('required_features', '[{"id":'+q(capability)+',"revision":1}]'), kv('version', '{"major":0,"minor":1}'))

def architecture_body(full=True, identity=None, variant='primary'):
    if variant in ('primary', 'mux-reversed', 'pins-reversed', 'cold-edit'):
        domain_defs = [domain_ref('clock', 'clock', full), domain_ref('config', 'configuration', full), domain_ref('power0', 'power', full), domain_ref('power1', 'power', full)]
        roots = []
        for name,power in [('t0','power0'),('t1','power1'),('t2','power1')]:
            domains=arr(domain_ref('clock','clock',full),domain_ref('config','configuration',full),domain_ref(power,'power',full))
            roots.append(instance(name,'tile',full,domains=domains))
        source_names = ['east','local','west'] if variant != 'mux-reversed' else ['west','local','east']
        mux=connection('mux',[endpoint(n,'O',full=full) for n in source_names],endpoint('sink','I',full=full),full,field_ref('route',full=full))
        tiles=[template('tile',full,connections=[mux],features=[feature(full)],groups=[group(full)],resources=[resource(n,full) for n in ['east','local','sink','west']],storage=[storage(full)])]
        edges=[connection('edge0',[endpoint('sink','O',['t0'],full)],endpoint('west','I',['t1'],full),full),
               connection('edge1',[endpoint('sink','O',['t1'],full)],endpoint('west','I',['t2'],full),full)]
        origin=PA if variant!='cold-edit' else '{"display":"Different display only","span":{"end":"512","source":"different-machine/architecture.scala","source_bytes":"512","start":"0"}}'
    elif variant == 'hierarchy':
        domain_defs=[]
        roots=[instance('r','wrapper',full)]
        tiles=[template('leaf',full,resources=[resource('cell',full)]),
               template('wrapper',full,children=[instance('..','leaf',full,partition='null'),instance('a/b','leaf',full,partition='null')])]
        edges=[connection('bridge',[endpoint('cell','O',['r','..'],full)],endpoint('cell','I',['r','a/b'],full),full)]
        origin=PH
    elif variant == 'alias':
        domain_defs=[]
        roots=[instance('t0','alias-tile',full),instance('t1','alias-tile',full)]
        tiles=[template('alias-tile',full,features=[feature(full,'F',owner='cell',domain='{"kind":"any"}'),feature(full,'alias',alias='F',owner='cell',domain='{"kind":"any"}')],resources=[resource('cell',full)],storage=[storage(full,owner='cell')])]
        edges=[]
        origin=P0
    elif variant == 'high-u64':
        domain_defs=[]
        roots=[instance('t0','large-offset',full)]
        tiles=[template('large-offset',full,features=[feature(full,'last-bit',owner='cell',width='1',start='18446744073709551614',length='1',domain='{"kind":"any"}')],resources=[resource('cell',full)],storage=[storage(full,owner='cell',bits='18446744073709551615')])]
        edges=[]
        origin=P0
    else:
        raise AssertionError(variant)
    return obj(kv('connections',arr(*edges)),kv('domains',arr(*domain_defs)),kv('namespace','"golden"'),kv('partitions','["0"]'),prov(full,origin),kv('resource_types',arr(cell_type(full,variant=='pins-reversed'))),kv('roots',arr(*roots)),kv('semantic_id',q(identity)) if full else (None,None),kv('templates',arr(*tiles)))

def arch_document(full=True, identity=None, variant='primary'):
    annotations=ARCH_ANNOTATIONS if variant!='cold-edit' else '{"golden.example/review":{"count":3,"message":"changed annotation only","unicode_order":{"\ue000":"BMP","\U00010000":"supplementary"}}}'
    return envelope('arch',architecture_body(full,identity,variant),full,annotations)

records=[]

def verify_literal_object_order(data):
    # This independent audit only checks supplied order; it never rewrites bytes.
    def pairs(items):
        keys=[k.encode('utf-8') for k,v in items]
        assert keys==sorted(keys),[k for k,v in items]
        assert len(keys)==len(set(keys))
        return dict(items)
    return json.loads(data,object_pairs_hook=pairs)

def put(name, data):
    if isinstance(data,str): data=data.encode('utf-8')
    path=HERE/name
    path.write_bytes(data)
    digest=hashlib.sha256(data).hexdigest()
    assert subprocess.check_output(['sha256sum',str(path)],text=True).split()[0]==digest
    records.append((name,len(data),digest))
    return digest

def make_arch(name,variant='primary'):
    projection=arch_document(False,variant=variant).encode('utf-8')
    semantic_id=hashlib.sha256(PREFIX['arch']+projection).hexdigest()
    canonical=arch_document(True,semantic_id,variant).encode('utf-8')
    # Intentional exact insignificant whitespace makes raw != canonical.
    raw=b' \n'+canonical+b'\n'
    verify_literal_object_order(canonical);verify_literal_object_order(projection)
    put(name+'.projection.json',projection)
    put(name+'.semantic-hash-input.bin',PREFIX['arch']+projection)
    put(name+'.canonical.json',canonical)
    digest=put(name+'.raw.json',raw)
    return dict(semantic_id=semantic_id,canonical=canonical,raw=raw,raw_sha256=digest)

arch=make_arch('architecture')
variants={n:make_arch('architecture-'+n,n) for n in ['hierarchy','alias','high-u64','mux-reversed','pins-reversed','cold-edit']}
assert variants['cold-edit']['semantic_id']==arch['semantic_id']
assert variants['cold-edit']['raw_sha256']!=arch['raw_sha256']
assert variants['mux-reversed']['semantic_id']!=arch['semantic_id']
assert variants['pins-reversed']['semantic_id']!=arch['semantic_id']

UNBOUND='{"reason":"foundation-unimplemented","state":"unbound"}'
AUTHORING='{"reason":"not-supplied","state":"unbound"}'
ABSENT='{"reason":"no-hard-macros","state":"absent"}'

def package_body(arch,full=True,identity=None):
    # Explicit manual order; implementation hash is absent because this fixture
    # is hand-authored, never falsely attributed to an actual Scala execution.
    artifact='{"bytes":'+q(str(len(arch['raw'])))+',"sha256":'+q(arch['raw_sha256'])+'}'
    return obj(kv('activation',UNBOUND),kv('architecture','{"artifact":'+artifact+',"semantic_id":'+q(arch['semantic_id'])+'}'),kv('authoring',AUTHORING),kv('backend',UNBOUND),kv('build_id',q(identity)) if full else (None,None),kv('compiler',UNBOUND),kv('configuration_map',UNBOUND),kv('device_db',UNBOUND),kv('external_pin_map',UNBOUND),kv('libraries','[]'),kv('macro_bindings',ABSENT),kv('physical_implementation',UNBOUND),kv('technology',UNBOUND),kv('timing_datasets',UNBOUND),kv('transport',UNBOUND))

def make_package(name,arch):
    projection=envelope('package',package_body(arch,False),False).encode('utf-8')
    build_id=hashlib.sha256(PREFIX['package']+projection).hexdigest()
    canonical=envelope('package',package_body(arch,True,build_id),True,'{}','[]').encode('utf-8')
    verify_literal_object_order(canonical);verify_literal_object_order(projection)
    put(name+'.projection.json',projection)
    put(name+'.build-hash-input.bin',PREFIX['package']+projection)
    put(name+'.canonical.json',canonical)
    put(name+'.raw.json',canonical)
    return build_id

build_id=make_package('package',arch)
cold_build_id=make_package('package-cold-edit',variants['cold-edit'])
assert build_id!=cold_build_id

def cell(name,mode,full=True):
    return obj(kv('mode',q(mode)),kv('name',q(name)),prov(full),kv('resource_type',key('generic-cell','resource_type')))

def port(name,direction,width,full=True):
    return obj(kv('direction',q(direction)),kv('name',q(name)),prov(full),kv('width',q(width)))

def cell_terminal(cell_name,pin,full=True):
    return obj(kv('bit','"0"'),kv('cell',q(cell_name)),kv('kind','"cell"'),kv('pin',q(pin)),prov(full))

def port_terminal(port_name,bit,full=True):
    return obj(kv('bit',q(bit)),kv('kind','"port"'),kv('port',q(port_name)),prov(full))

def constant_terminal(value,full=True):
    return obj(kv('kind','"constant"'),prov(full),kv('value',q(value)))

def net(name,driver,loads,full=True):
    return obj(kv('driver',driver),kv('loads',arr(*loads)),kv('name',q(name)),prov(full))

def design_body(target,full=True,identity=None):
    cells=[cell('c0','normal',full),cell('c1','alternate',full)]
    ports=[port('flag','output','1',full),port('in','input','2',full),port('out','output','2',full)]
    nets=[net('n0',port_terminal('in','0',full),[cell_terminal('c0','I',full)],full),
          net('n1',cell_terminal('c0','O',full),[cell_terminal('c1','I',full),port_terminal('out','0',full)],full),
          net('n2',cell_terminal('c1','O',full),[port_terminal('out','1',full)],full),
          net('n3',constant_terminal('1',full),[port_terminal('flag','0',full)],full)]
    return obj(kv('cells',arr(*cells)),kv('name','"demo"'),kv('namespace','"golden-design"'),kv('nets',arr(*nets)),kv('ports',arr(*ports)),prov(full,PD),kv('semantic_id',q(identity)) if full else (None,None),kv('target_build_id',q(target)))

def make_design(name,target):
    projection=envelope('design',design_body(target,False),False).encode('utf-8')
    identity=hashlib.sha256(PREFIX['design']+projection).hexdigest()
    canonical=envelope('design',design_body(target,True,identity),True,'{}','[]').encode('utf-8')
    verify_literal_object_order(canonical);verify_literal_object_order(projection)
    put(name+'.projection.json',projection)
    put(name+'.semantic-hash-input.bin',PREFIX['design']+projection)
    put(name+'.canonical.json',canonical)
    put(name+'.raw.json',canonical)
    return identity

design_id=make_design('design',build_id)
cold_design_id=make_design('design-cold-target',cold_build_id)
assert design_id!=cold_design_id

# Focused supplied-input keyed-set permutations preserve manually reviewed
# canonical bytes. Byte swaps are explicit fixture edits, not a normalizer.
root_a=instance('t0','tile',True,domains=arr(domain_ref('clock','clock'),domain_ref('config','configuration'),domain_ref('power0','power'))).encode('utf-8')
root_c=instance('t2','tile',True,domains=arr(domain_ref('clock','clock'),domain_ref('config','configuration'),domain_ref('power1','power'))).encode('utf-8')
assert arch['canonical'].count(root_a)==1 and arch['canonical'].count(root_c)==1
swapped=arch['canonical'].replace(root_a,b'@@ROOT_A@@').replace(root_c,root_a).replace(b'@@ROOT_A@@',root_c)
put('architecture-root-permuted.raw.json',swapped)
# Explicitly reorder only declared sets, preserving all ordered source/pin/path
# vectors. Their independently expected canonical file stays the primary one.
set_swapped=swapped.replace(b'"values":["0","1","2"]',b'"values":["2","0","1"]').replace(b'"modes":["alternate","normal"]',b'"modes":["normal","alternate"]')
assert set_swapped != swapped
put('architecture-set-permuted.raw.json',set_swapped)
# A false whole-file digest difference does not alter this fixture's declared
# semantic ID; expected canonical bytes are architecture.canonical.json.

put('SHA256SUMS',''.join(f'{h}  {n}\n' for n,l,h in records).encode('ascii'))
identities=(
 '# Independent full-envelope identities\n\n'
 f'- Primary architecture semantic_id: `{arch["semantic_id"]}`\n'
 f'- Primary architecture raw SHA-256: `{arch["raw_sha256"]}`\n'
 f'- Primary architecture raw bytes: {len(arch["raw"])}\n'
 f'- Package build_id: `{build_id}`\n'
 f'- Design semantic_id: `{design_id}`\n'
 f'- Cold-only architecture semantic_id: `{variants["cold-edit"]["semantic_id"]}`\n'
 f'- Cold-only package build_id: `{cold_build_id}`\n'
 f'- Design rebound to cold-only package semantic_id: `{cold_design_id}`\n'
 + ''.join(f'- {n} architecture semantic_id: `{v["semantic_id"]}`\n' for n,v in variants.items())
)
(HERE/'IDENTITIES.md').write_text(identities)
print(identities)
print('Wrote',len(records)-1,'independently assembled byte artifacts, plus SHA256SUMS.')
