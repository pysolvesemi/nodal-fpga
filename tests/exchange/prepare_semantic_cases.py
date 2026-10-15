"""Independently author focused decoded-schema controls; never run during tests.
No production imports. Full original goldens and C00-C38 remain immutable.
"""
from pathlib import Path
import copy
import hashlib
from support import P0, encoded, fixture, resign_architecture, architecture_projection

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'verify/fixtures/exchange/semantic-cases'
OUT.mkdir(exist_ok=True)

def write(name,doc):
    signed=resign_architecture(doc)
    (OUT/(name+'.json')).write_bytes(encoded(signed))
    (OUT/(name+'.projection.json')).write_bytes(encoded(architecture_projection(signed)))
    print(name,signed['body']['semantic_id'])

guard=fixture('architecture-alias')
template=guard['body']['templates'][0]
owner=copy.deepcopy(template['features'][0]['owner'])
template['mode_groups']=[{'name':'operation','resources':[owner],'modes':['alternate','normal'],'provenance':copy.deepcopy(P0)}]
template['features'][0]['guard']=[{'group':'operation','mode':'normal','provenance':copy.deepcopy(P0)}]
template['features'][1]['guard']=[{'group':'operation','mode':'alternate','provenance':copy.deepcopy(P0)}]
write('guarded-alias',guard)
resource_alias=fixture('architecture-alias')
resource=copy.deepcopy(resource_alias['body']['templates'][0]['resources'][0])
resource['name']='cell-alias'
resource['alias_of']=copy.deepcopy(resource_alias['body']['templates'][0]['features'][0]['owner'])
resource_alias['body']['templates'][0]['resources'].append(resource)
write('resource-alias',resource_alias)
range_domain=fixture()
range_domain['body']['templates'][0]['features'][0]['domain']={'kind':'range','minimum':'0','maximum':'2'}
write('range-domain',range_domain)
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted(OUT.iterdir()) if f.name!='SHA256SUMS'))
