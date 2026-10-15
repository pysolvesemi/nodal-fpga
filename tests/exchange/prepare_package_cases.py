"""Independent case authoring, never run implicitly by conformance tests.

Reads frozen literals and creates explicit package preflight test inputs. Uses
only Python stdlib. No production outputs/imports. Existing full goldens are not
changed. Re-run only for reviewed intentional test-contract updates.
"""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'verify/fixtures/exchange'
OUT=BASE/'package-cases'
OUT.mkdir(exist_ok=True)
package=json.loads((BASE/'goldens/package.canonical.json').read_bytes())
raw=(BASE/'goldens/architecture.raw.json').read_bytes()
raw_descriptor=copy.deepcopy(package['body']['architecture']['artifact'])
leaf=b'{"format":"nodal-fpga.package-manifest","url":"https://example.invalid/never-fetch","nested_design":{"execute":false}}'
leaf_descriptor={'bytes':str(len(leaf)),'sha256':hashlib.sha256(leaf).hexdigest()}

def encoded(doc):return json.dumps(doc,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def write(name,doc):
    projected=copy.deepcopy(doc)
    del projected['annotations'];del projected['optional_features'];del projected['body']['build_id']
    doc['body']['build_id']=hashlib.sha256(b'nodal-fpga.package.build.v1\n'+encoded(projected)).hexdigest()
    (OUT/(name+'.json')).write_bytes(encoded(doc))

def library(descriptor):return {'id':'extra','revision':'1','artifact':copy.deepcopy(descriptor)}

same=copy.deepcopy(package);same['body']['libraries']=[library(raw_descriptor)];write('same-digest',same)
conflict=copy.deepcopy(same);conflict['body']['libraries'][0]['artifact']['bytes']=str(len(raw)+1);write('conflicting-length',conflict)
leaf_package=copy.deepcopy(package);leaf_package['body']['libraries']=[library(leaf_descriptor)];write('two-artifacts',leaf_package)
opaque=copy.deepcopy(leaf_package);opaque['body']['configuration_map']={'state':'bound','revision':'opaque-one','artifact':copy.deepcopy(leaf_descriptor)}
write('opaque-reused',opaque)
large=copy.deepcopy(package);large['body']['libraries']=[library({'bytes':'8388609','sha256':'1'*64})];write('oversized-declared',large)
(OUT/'opaque-leaf.bin').write_bytes(leaf)
(OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted(OUT.iterdir()) if f.name!='SHA256SUMS'))
print('Independent package cases prepared; original full-golden artifacts unchanged.')
