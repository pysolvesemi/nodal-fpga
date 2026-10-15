"""Bounded nf-tiny structural oracle. No generator or HDL compiler is invoked here.

The caller owns source provenance and the isolated Yosys command receipt. Feed
unflattened `hierarchy -check -top eFPGA; proc; write_json` output. Synthetic
controls qualify this checker only, never generated RTL.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

ORACLE = Path(__file__).resolve().parents[1] / 'nf-tiny'
PINS = {'specification.json': '0e58761faed7d2d3ea6154ed605262a9fd4a8d6a13ca7de33d06f70a7a88ef32',
        'correspondence.json': '9aff8b60474fa6b04b07691ebe63421c8ae89df31f90f8d5f55189376fc294fe'}

class StructureError(ValueError):
    def __init__(self, category, witness, expected=None, observed=None, *, diagnostic=None, affected=()):
        self.category, self.witness = category, witness
        self.diagnostic = diagnostic or category
        self.affected = list(affected) or [witness]
        self.expected, self.observed = expected, observed
        super().__init__(f'{category}/{self.diagnostic}: {witness}: expected {expected!r}; observed {observed!r}')

def require(ok, witness, expected=None, observed=None, category='mapping-mismatch'):
    if not ok:
        raise StructureError(category, witness, expected, observed)

def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, 'duplicate-json-key/' + key)
        obj[key] = value
    return obj

def read_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object)

def oracle():
    result = []
    for name, digest in PINS.items():
        data = (ORACLE / name).read_bytes()
        require(hashlib.sha256(data).hexdigest() == digest, name, digest,
                hashlib.sha256(data).hexdigest(), 'provenance-mismatch')
        result.append(json.loads(data, object_pairs_hook=unique_object))
    return result

def expected(shape_id):
    """Enumerate only accepted immutable input, with no candidate argument."""
    spec, corr = oracle()
    shape = next((s for s in spec['shapes'] if s['id'] == shape_id), None)
    require(shape is not None, 'shape', 'accepted shape', shape_id)
    records = {}
    graph = spec['tile_graph']
    for tile in shape['tiles']:
        base = f"{shape_id}/{tile['id']}"
        variant = graph['variants'][tile['type']]
        for pin in graph['common_pins'] + variant['additional_pins']:
            records[f'PIN/{base}/{pin}'] = pin
        for a, b in graph['common_fixed_edges'] + variant['additional_fixed_edges']:
            records[f'FIXED/{base}/{a}->{b}'] = [a, b]
        for edge in graph['configurable_edges']:
            a, b, v = edge['from'], edge['to'], edge['value']
            records[f'SELECT/{base}/{v}/{a}->{b}'] = [a, b, v]
        for binding in corr['config_map']:
            records[f"CONFIG/{base}/{binding['tile_config_bit']}"] = binding
        for resource in corr['resource_map']:
            records[f'RESOURCE/{base}/{resource}'] = resource
    for a, b in shape['intertile_edges']:
        records[f'LINK/{shape_id}/{a}->{b}'] = [a, b]
    return shape, records

def check_correspondence(candidate, *, shape_id='one', tile_id='t00'):
    """Semantic comparison; affected canonical keys can bind mutant receipts."""
    _, accepted = oracle()
    base = f'{shape_id}/{tile_id}'
    def reject(code, keys, wanted, got):
        raise StructureError('mapping-mismatch', keys[0], wanted, got,
                             diagnostic=code, affected=keys)
    for section in ('pin_map','variant_pin_map'):
        maps = [(accepted[section], candidate.get(section, {}))] if section == 'pin_map' else [
            (accepted[section][variant], candidate.get(section, {}).get(variant,{}))
            for variant in accepted[section]]
        for wanted, got in maps:
            missing = sorted(set(wanted)-set(got))
            if missing:
                reject('missing-primary-mapping', ['PIN/'+base+'/'+k for k in missing], missing, sorted(got))
            extra = sorted(set(got)-set(wanted))
            if extra:
                reject('unexpected-primary-mapping', ['PIN/'+base+'/'+k for k in extra], sorted(wanted), extra)
            owners = {}
            for pin, value in got.items():
                ref = value.get('reference')
                if ref in owners:
                    reject('duplicate-primary-mapping', ['PIN/'+base+'/'+p for p in (owners[ref],pin)],
                           'one logical owner per primary target', ref)
                owners[ref] = pin
            changed = [pin for pin in wanted if wanted[pin] != got[pin]]
            if changed:
                reject('pin-order-mismatch', ['PIN/'+base+'/'+p for p in changed],
                       {p:wanted[p] for p in changed}, {p:got[p] for p in changed})
    bindings = candidate.get('config_map', [])
    owners = {}
    for index,binding in enumerate(bindings):
        bit = binding.get('tile_config_bit')
        if bit in owners:
            logical = accepted['config_map'][index]['tile_config_bit'] if index < 20 else index
            reject('config-field-overlap', [f'CONFIG/{base}/{logical}', f'CONFIG/{base}/{owners[bit]}'],
                   'unique physical owner', bit)
        owners[bit] = index
    if bindings != accepted['config_map']:
        changed = [j for j in range(max(len(bindings),20))
                   if j >= len(bindings) or j >= 20 or bindings[j] != accepted['config_map'][j]]
        reject('config-binding-mismatch', [f'CONFIG/{base}/{j}' for j in changed],
               accepted['config_map'],bindings)
    for key in ('resource_map','tile_instance','switch_instance','exclusions'):
        require(candidate.get(key) == accepted[key], 'correspondence/' + key,
                accepted[key], candidate.get(key))

def check_declared_edges(shape_id, edges):
    """Independent directed candidate-edge control, without RTL recompilation."""
    shape, _ = expected(shape_id)
    require(isinstance(edges,list) and all(isinstance(e,list) and len(e)==2 and
            all(isinstance(p,str) for p in e) for e in edges), 'LINK/'+shape_id+'/edge-format')
    actual = [tuple(e) for e in edges]
    wanted = {tuple(e) for e in shape['intertile_edges']}
    for edge in sorted(wanted):
        a,b = edge
        witness = f'LINK/{shape_id}/{a}->{b}'
        if edge not in actual:
            reverse = (b,a) in actual
            raise StructureError('mapping-mismatch',witness,edge,(b,a) if reverse else None,
                                 diagnostic='reversed-directed-edge' if reverse else 'missing-directed-edge')
    for edge in actual:
        if edge not in wanted or actual.count(edge) != 1:
            a,b = edge
            raise StructureError('mapping-mismatch',f'LINK/{shape_id}/{a}->{b}',
                                 'one declared directed edge',edge,
                                 diagnostic='extra-directed-edge' if edge not in wanted else 'duplicate-directed-edge')
    return {'status':'passed','records':['LINK/'+shape_id+'/'+a+'->'+b for a,b in sorted(actual)]}

class Hierarchy:
    """Instance-scoped bit identities; only declared transparent models coalesce."""
    def __init__(self, data):
        self.modules = data.get('modules', {})
        self.nodes, self.parent = {}, {}
        self._visit('', 'eFPGA', (), {})

    def root(self, bit):
        self.parent.setdefault(bit, bit)
        if self.parent[bit] != bit:
            self.parent[bit] = self.root(self.parent[bit])
        return self.parent[bit]

    def union(self, a, b):
        a, b = self.root(a), self.root(b)
        if a == b:
            return
        require(not (a[0] == 'constant' and b[0] == 'constant'), 'constant-short', a, b)
        if b[0] == 'constant':
            a, b = b, a
        self.parent[b] = a

    def raw(self, path, bit):
        if isinstance(bit, str):
            require(bit in ('0', '1'), path + '/nonbinary-bit', '0 or 1', bit)
            return ('constant', bit)
        require(type(bit) is int and bit >= 0, path + '/bit', 'integer', bit)
        return (path, bit)

    def _visit(self, path, key, ancestry, params):
        require(key in self.modules and key not in ancestry, path + '/module', 'acyclic module', key)
        require(len(ancestry) < 16 and len(self.nodes) < 10000, path+'/hierarchy-bound')
        module = self.modules[key]
        origin = module.get('attributes', {}).get('hdlname', key).split()[-1].lstrip('\\')
        allowed = {'eFPGA','nf_tiny_io','my_buf','clk_buf','config_latch',
                   'LUT4c_frame_config_dffesr','cus_mux21','cus_mux41','cus_mux161'}
        allowed |= {v + suffix for v in ('NF_SINGLE','NF_LEFT','NF_MID','NF_RIGHT')
                    for suffix in ('','_ConfigMem','_switch_matrix')}
        require(origin in allowed, path + '/unknown-module', sorted(allowed), origin)
        self.nodes[path] = (module, key, origin)
        defaults = module.get('parameter_default_values', {})
        expected_params = {}
        if origin == 'eFPGA':
            expected_params = {'MaxFramesPerCol':20,'FrameBitsPerRow':32}
        elif origin.startswith('NF_'):
            if origin.endswith('_switch_matrix'):
                expected_params = {'NoConfigBits':1,'GND0':0,'GND':0,'VCC0':1,'VCC':1,'VDD0':1,'VDD':1}
            else:
                expected_params = {'MaxFramesPerCol':20,'FrameBitsPerRow':32,'NoConfigBits':20}
        elif origin == 'LUT4c_frame_config_dffesr':
            expected_params = {'NoConfigBits':19}
        require(set(defaults) == set(expected_params), path+'/parameter-inventory', expected_params, defaults)
        for name, wanted in expected_params.items():
            value = defaults[name]
            require(isinstance(value,str) and value and set(value) <= {'0','1'} and
                    int(value,2) == wanted, path+'/parameter-value/'+name, wanted, value)
        require('Emulate_Bitstream' not in defaults and 'Emulate_Bitstream' not in params,
                path + '/EMULATION', 'non-EMULATION storage')
        for name, value in params.items():
            require(name in defaults and defaults[name] == value, path + '/parameter/' + name,
                    defaults.get(name), value)
        for name, cell in module.get('cells', {}).items():
            child = f'{path}.{name}' if path else name
            typ = cell['type']
            if typ.startswith('$') and typ not in self.modules:
                require(origin in ('LUT4c_frame_config_dffesr','config_latch','cus_mux21','cus_mux41'),
                        child + '/unexpected-lowered-logic', 'primitive boundary', origin)
                require(typ in ('$dff','$dlatch','$mux','$not','$and','$or','$logic_not','$eq'),
                        child + '/unknown-primitive', 'reviewed proc vocabulary', typ)
                continue  # Primitive logic remains an opaque semantic boundary.
            self._visit(child, typ, ancestry + (key,), cell.get('parameters', {}))
            child_module = self.nodes[child][0]
            ports = child_module.get('ports', {})
            require(set(cell['connections']) == set(ports), child + '/ports', sorted(ports), sorted(cell['connections']))
            require(cell.get('port_directions') == {p: v['direction'] for p, v in ports.items()}, child + '/directions')
            for p, port in ports.items():
                bits = cell['connections'][p]
                require(len(bits) == len(port['bits']), child + '/' + p + '/width')
                for a, b in zip(bits, port['bits']):
                    self.union(self.raw(path, a), self.raw(child, b))
        if origin in ('my_buf', 'clk_buf'):
            require(not module.get('cells'), path + '/transparent-logic')
            self.ports(path, {'A': ('input', 1), 'X': ('output', 1)})
            require(self.bits(path, 'A') == self.bits(path, 'X'), path + '/transparent-assignment')
        elif origin == 'nf_tiny_io':
            require(not module.get('cells'), path + '/io-logic')
            for a, b in [('A0','X0'),('A1','X1'),('A2','X2'),('A3','X3'),
                         ('ALT','XA'),('ENABLE','XE'),('RESET','XR'),('RESULT','Y')]:
                require(self.bits(path, a) == self.bits(path, b), path + '/io/' + a)

    def bits(self, path, name):
        module = self.nodes[path][0]
        net = module.get('netnames', {}).get(name, module.get('ports', {}).get(name))
        require(net is not None, path + '/' + name, 'exported net or port')
        require(net.get('offset', 0) == 0 and net.get('upto', 0) == 0,
                path + '/' + name + '/index-order', 'zero-offset descending vector', net)
        return [self.root(self.raw(path, b)) for b in net['bits']]

    def bit(self, path, name, index=0):
        bits = self.bits(path, name)
        require(index < len(bits), path + '/' + name + '/index', index, len(bits))
        return bits[index]

    def ports(self, path, contract):
        ports = self.nodes[path][0].get('ports', {})
        actual = {p: (v['direction'], len(v['bits'])) for p, v in ports.items()}
        require(actual == contract, path + '/port-inventory', contract, actual)
        for p in ports:
            self.bits(path, p)

    def typed(self, path, origin):
        require(path in self.nodes, path, origin, 'missing')
        require(self.nodes[path][2] == origin, path + '/type', origin, self.nodes[path][2])
        return {'path': path, 'module_key': self.nodes[path][1], 'type': origin,
                'parameters': self.nodes[path][0].get('parameter_default_values', {})}

    def driver_ownership(self):
        drivers = {self.root(self.raw('',b)): 'fabric input '+name
                   for name,port in self.nodes[''][0]['ports'].items()
                   if port['direction']=='input' for b in port['bits']}
        for path,(module,_,_) in self.nodes.items():
            for name,cell in module.get('cells',{}).items():
                if cell['type'] in self.modules: continue
                for port,direction in cell.get('port_directions',{}).items():
                    if direction != 'output': continue
                    for b in cell['connections'][port]:
                        bit=self.root(self.raw(path,b))
                        witness=path+'.'+name+'.'+port
                        require(bit not in drivers and bit[0]!='constant',
                                'physical-driver/'+witness,'one physical source',drivers.get(bit,bit))
                        drivers[bit]=witness

    def resolve(self, path, reference):
        parts = reference.split('.')
        for part in parts[:-1]:
            path += '.' + part
        match = re.fullmatch(r'([^\[]+)(?:\[(\d+)\])?', parts[-1])
        require(match is not None, reference)
        name, index = match.groups()
        if name == 'GND0':
            value = self.nodes[path][0].get('parameter_default_values', {}).get('GND0')
            require(isinstance(value, str) and value and set(value) == {'0'}, path + '/GND0', 'zero parameter', value)
            return ('constant', '0')
        return self.bit(path, name, int(index or 0))


def output_drivers(h, path, bit):
    return [(name, cell, port) for name, cell in h.nodes[path][0].get('cells', {}).items()
            for port, direction in cell.get('port_directions', {}).items()
            if direction == 'output' and bit in [h.root(h.raw(path,b)) for b in cell['connections'][port]]]

def connection(h, path, cell, port):
    bits = cell.get('connections', {}).get(port, [])
    require(len(bits) == 1, path+'/'+port+'/scalar', 1, len(bits))
    return h.root(h.raw(path,bits[0]))

def check_state_controls(h, path, driver, witness):
    controls = {}
    target = connection(h,path,driver,'D')
    for selector, hold, next_name in [('EN', h.bit(path,'LUT_flop'), None),
                                      ('SR', h.bit(path,'LUT_out'), 'ConfigBits')]:
        found = output_drivers(h,path,target)
        require(len(found) == 1 and found[0][1]['type'] == '$mux' and found[0][2] == 'Y',
                witness+'/'+selector+'/mux', 'one $mux.Y', [(n,c['type'],p) for n,c,p in found])
        name, cell, _ = found[0]
        require(connection(h,path,cell,'S') == h.bit(path,selector) and
                connection(h,path,cell,'A') == hold, witness+'/'+selector+'/control')
        target = connection(h,path,cell,'B')
        if next_name:
            require(target == h.bit(path,next_name,18), witness+'/reset-value')
        controls[selector] = {'cell':name,'connections':cell['connections']}
    return controls

def check_latch_body(h, path, witness):
    result = {}
    counts={}
    for cell in h.nodes[path][0].get('cells',{}).values():
        counts[cell['type']]=counts.get(cell['type'],0)+1
    require(counts in ({'$dlatch':2,'$not':1},{'$dlatch':2,'$not':2}),
            witness+'/storage-cell-inventory', 'two latches, D inverse, optional dead proc hold inverse',counts)
    # Minimal proc retains an unused inverse of E. Admit exactly that artifact,
    # never an arbitrary extra driver (including one driving the input D).
    extras=[(name,cell) for name,cell in h.nodes[path][0]['cells'].items()
            if cell['type']=='$not' and connection(h,path,cell,'A') != h.bit(path,'D')]
    require(len(extras) == counts['$not']-1, witness+'/storage-inverter-inventory')
    for name,cell in extras:
        out=connection(h,path,cell,'Y')
        sinks=[(n,p) for n,c in h.nodes[path][0]['cells'].items()
               for p,d in c['port_directions'].items() if d=='input'
               and out in [h.root(h.raw(path,b)) for b in c['connections'][p]]]
        require(connection(h,path,cell,'A') == h.bit(path,'E') and not sinks and
                out not in {h.bit(path,p) for p in ('D','E','Q','QN')},
                witness+'/storage-unused-hold', 'isolated inverse of E', name)
    for output in ('Q','QN'):
        found = output_drivers(h,path,h.bit(path,output))
        require(len(found) == 1 and found[0][1]['type'] == '$dlatch' and found[0][2] == 'Q',
                witness+'/'+output+'/state-driver', 'one $dlatch.Q', [(n,c['type'],p) for n,c,p in found])
        name, cell, _ = found[0]
        require(int(cell.get('parameters',{}).get('EN_POLARITY','0'),2) == 1 and
                connection(h,path,cell,'EN') == h.bit(path,'E'), witness+'/'+output+'/enable')
        d = connection(h,path,cell,'D')
        if output == 'Q':
            require(d == h.bit(path,'D'), witness+'/Q/data')
        else:
            inv = output_drivers(h,path,d)
            require(len(inv) == 1 and inv[0][1]['type'] == '$not' and
                    connection(h,path,inv[0][1],'A') == h.bit(path,'D'), witness+'/QN/complement')
        result[output] = {'cell':name,'type':cell['type'],'connections':cell['connections']}
    return result

def _check_shape(shape_id, yosys_json, h, *, defines=(), correspondence=None):
    require(not defines, 'structural-defines', [], list(defines))
    spec, corr = oracle()
    if correspondence is not None:
        check_correspondence(correspondence)
    shape, roster = expected(shape_id)
    records, tilepins = {}, {}
    independent_inputs = [h.root(h.raw('',bit))
                          for port in h.nodes[''][0].get('ports', {}).values()
                          if port['direction'] == 'input' for bit in port['bits']]
    require(len(independent_inputs) == len(set(independent_inputs)) and
            all(bit[0] != 'constant' for bit in independent_inputs),
            shape_id+'/independent-top-inputs', 'distinct unconstrained source bits')
    independent_inputs = set(independent_inputs)
    top_contract = {'FrameData': ('input', 32 * shape['height']),
                    'FrameStrobe': ('input', 20 * shape['width']), 'UserCLK': ('input', 1)}
    instances = {corr['tile_instance'].format(**t) for t in shape['tiles']}
    require(set(h.nodes[''][0].get('cells', {})) == instances, shape_id + '/instances', sorted(instances), sorted(h.nodes[''][0].get('cells', {})))
    # Inventory actual boundary output->input links before intra-tile checks:
    # replacing W with zero must name the lost directed link, not a coincidental
    # new constant-connected intra-tile edge.
    boundary = {}
    for tile in shape['tiles']:
        path = corr['tile_instance'].format(**tile)
        ports = h.nodes[path][0].get('ports', {})
        boundary[tile['id']] = {p.lower():h.bit(path,p) for p in ('E','W') if p in ports}
    early_links = [[a+'.e', b+'.w'] for a,pa in boundary.items() if 'e' in pa
                   for b,pb in boundary.items() if 'w' in pb and pa['e'] == pb['w']]
    check_declared_edges(shape_id, early_links)
    config_owners = set()
    state_owners = {}
    for tile in shape['tiles']:
        typ, tid = tile['type'], tile['id']
        path = corr['tile_instance'].format(**tile)
        base = f'{shape_id}/{tid}'
        h.typed(path, typ)
        io_ports = {'P_' + p: ('input', 1) for p in ('A0','A1','A2','A3','ALT','ENABLE','RESET')}
        io_ports['P_Y'] = ('output', 1)
        for p, desc in io_ports.items():
            top_name = f"Tile_X{tile['x']}Y{tile['y']}_{p}"
            top_contract[top_name] = desc
            require(h.bit('', top_name) == h.bit(path, p), f'PIN/{base}/{p}/fabric')
        tile_contract = dict(io_ports, UserCLK=('input',1), UserCLKo=('output',1),
                             FrameData=('input',32), FrameData_O=('output',32),
                             FrameStrobe=('input',20), FrameStrobe_O=('output',20))
        for p in corr['variant_pin_map'][typ]:
            tile_contract[p.upper()] = ('output' if p == 'e' else 'input', 1)
        h.ports(path, tile_contract)
        lut = path + '.' + corr['resource_map']['lut']
        switch = path + '.' + corr['switch_instance'].format(type=typ)
        mux = path + '.' + corr['resource_map']['mux'].format(type=typ)
        mem = path + '.' + corr['resource_map']['config_memory'].format(type=typ)
        for resource, p, origin in [('lut',lut,'LUT4c_frame_config_dffesr'),
                                    ('mux',mux,'cus_mux21'),('config_memory',mem,typ+'_ConfigMem')]:
            records[f'RESOURCE/{base}/{resource}'] = h.typed(p, origin)
        h.typed(switch, typ + '_switch_matrix')
        allowed = {lut.rsplit('.',1)[1], switch.rsplit('.',1)[1], mem.rsplit('.',1)[1], 'Inst_P_nf_tiny_io'}
        for name, cell in h.nodes[path][0]['cells'].items():
            child = path + '.' + name
            require(name in allowed or h.nodes.get(child, (None,None,None))[2] in ('my_buf','clk_buf'), child + '/unknown-cell')
        require(set(h.nodes[switch][0]['cells']) == {'inst_cus_mux21_L_I0'}, switch + '/cell-inventory')
        switch_contract = {p: ('input',1) for p in
                           ('P_X0','P_X1','P_X2','P_X3','P_XA','P_XE','P_XR','L_O','L_Co')}
        switch_contract.update({p: ('output',1) for p in
                                ('L_I0','L_I1','L_I2','L_I3','L_Ci','L_EN','L_SR','P_RESULT')})
        switch_contract.update(ConfigBits=('input',1), ConfigBits_N=('input',1))
        if 'w' in corr['variant_pin_map'][typ]:
            switch_contract['W0'] = ('input',1)
        if 'e' in corr['variant_pin_map'][typ]:
            switch_contract['E0'] = ('output',1)
        h.ports(switch, switch_contract)
        for net, width in (('FrameData',32),('FrameStrobe',20)):
            require(h.bits(path, net) == h.bits(path, net+'_O'), base+'/'+net+'/transport')
        require(h.bit(path,'UserCLK') == h.bit(path,'UserCLKo'), base+'/clock-transport')
        h.ports(mux, {'A0':('input',1),'A1':('input',1),'S':('input',1),'X':('output',1)})
        lut_cells = h.nodes[lut][0]['cells']
        named = {n:c for n,c in lut_cells.items() if c['type'] in h.modules}
        named_expected = {'cus_mux21_I0mux':'cus_mux21','inst_cus_mux161':'cus_mux161','cus_mux21_O':'cus_mux21'}
        require(set(named) == set(named_expected), lut+'/cell-inventory', sorted(named_expected), sorted(named))
        for name, origin in named_expected.items():
            h.typed(lut+'.'+name,origin)
        primitive_counts = {}
        for cell in lut_cells.values():
            if cell['type'] not in h.modules:
                primitive_counts[cell['type']] = primitive_counts.get(cell['type'],0) + 1
        require(primitive_counts == {'$not':4,'$and':3,'$or':2,'$mux':2,'$dff':1},
                lut+'/lowered-source-inventory', {'$not':4,'$and':3,'$or':2,'$mux':2,'$dff':1},primitive_counts)
        h.ports(lut, {'I':('input',4),'O':('output',1),'Ci':('input',1),'Co':('output',1),
                      'SR':('input',1),'EN':('input',1),'UserCLK':('input',1),'ConfigBits':('input',19)})
        h.ports(mem, {'FrameData':('input',32),'FrameStrobe':('input',20),
                      'ConfigBits':('output',20),'ConfigBits_N':('output',20)})
        require(set(h.nodes[mem][0]['cells']) == {f'Inst_frame0_bit{i}' for i in range(12,32)}, mem + '/latches')
        mappings = dict(corr['pin_map'], **corr['variant_pin_map'][typ])
        pins = {}
        for pin, mapping in mappings.items():
            ref = mapping['reference'].format(type=typ)
            bit = h.resolve(path, ref)
            for alias in mapping.get('aliases', []):
                require(h.resolve(path, alias.format(type=typ)) == bit, f'PIN/{base}/{pin}/alias')
            pins[pin] = bit
            records[f'PIN/{base}/{pin}'] = {'path': path + '.' + ref, 'bit': bit, 'direction': mapping['direction']}
        tilepins[tid] = pins
        # Semantic boundary roles prevent merged aliases from manufacturing cliques.
        sources = ['a0','a1','a2','a3','alt','enable','reset','const0','mux.y','lut.o','clk']
        if 'w' in pins:
            sources.append('w')
        sinks = ['mux.a0','mux.a1','lut.i0','lut.i1','lut.i2','lut.i3','lut.ci','lut.en','lut.sr','lut.clk','y']
        if 'e' in pins:
            sinks.append('e')
        actual_edges = {(a,b) for a in sources for b in sinks if pins[a] == pins[b]}
        expected_edges = {tuple(v) for k,v in roster.items() if k.startswith(f'FIXED/{base}/')}
        require(actual_edges == expected_edges, f'FIXED/{base}', sorted(expected_edges), sorted(actual_edges))
        for a,b in actual_edges:
            records[f'FIXED/{base}/{a}->{b}'] = {'from': a, 'to': b, 'bit': pins[a]}
        for j in (0,1):
            require(h.bit(mux, 'A'+str(j)) == pins['mux.a'+str(j)], f'SELECT/{base}/{j}/ordered-terminal')
            require(h.bit(mux, 'X') == pins['mux.y'], f'SELECT/{base}/{j}/output')
            records[f'SELECT/{base}/{j}/mux.a{j}->mux.y'] = {'path':mux,'terminal':'A'+str(j),'select':j}
        # The complete boundary consumer inventory is checked independently of
        # connectivity. No extra tile/switch/ConfigMem port can hide fanout.
        for p, widths in ((path, {'ConfigBits':20,'ConfigBits_N':20}),
                          (switch, {'ConfigBits':1,'ConfigBits_N':1})):
            for net, width in widths.items():
                require(len(h.bits(p,net)) == width, p+'/'+net+'/width', width, len(h.bits(p,net)))
        state = h.bit(lut, 'LUT_flop')
        state_witness = f'RESOURCE/{base}/lut.register'
        require(state not in state_owners and state not in config_owners and
                state not in set(h.bits(path,'ConfigBits') + h.bits(path,'ConfigBits_N')),
                state_witness+'/state-ownership', 'independent register storage', state)
        state_owners[state] = state_witness
        require(state not in independent_inputs and state[0] != 'constant', f'RESOURCE/{base}/lut.register/state-ownership')
        drivers = []
        for name, cell in h.nodes[lut][0]['cells'].items():
            for port, direction in cell.get('port_directions', {}).items():
                if direction == 'output' and state in [h.root(h.raw(lut,b)) for b in cell['connections'][port]]:
                    drivers.append((name, cell, port))
        require(len(drivers) == 1, f'RESOURCE/{base}/lut.register/driver', 'one Q driver', len(drivers))
        name, driver, port = drivers[0]
        require(driver['type'] == '$dff' and port == 'Q' and len(driver['connections']['Q']) == 1,
                f'RESOURCE/{base}/lut.register/type', '$dff.Q', (driver['type'],port))
        require(int(driver['parameters']['CLK_POLARITY'],2) == 1 and
                [h.root(h.raw(lut,b)) for b in driver['connections']['CLK']] == [h.bit('', 'UserCLK')],
                f'RESOURCE/{base}/lut.register/clock')
        require(len(driver['connections'].get('D', [])) == 1,
                f'RESOURCE/{base}/lut.register/data-width', 1, len(driver['connections'].get('D', [])))
        controls = check_state_controls(h,lut,driver,f'RESOURCE/{base}/lut.register')
        records[f'RESOURCE/{base}/lut.register'] = {'controls':controls,'path':lut+'.LUT_flop','driver':name,'type':driver['type'],
                                                  'bit':state,'connections':driver['connections']}
        for j in range(20):
            witness = f'CONFIG/{base}/{j}'
            latch = mem + f'.Inst_frame0_bit{12+j}'
            h.typed(latch, 'config_latch')
            h.ports(latch, {'D':('input',1),'E':('input',1),'Q':('output',1),'QN':('output',1)})
            chain = {'frame_data': h.bit('', 'FrameData',32*tile['y']+12+j),
                     'memory_data':h.bit(mem,'FrameData',12+j),'D':h.bit(latch,'D'),
                     'frame_strobe':h.bit('', 'FrameStrobe',20*tile['x']),
                     'memory_strobe':h.bit(mem,'FrameStrobe',0),'E':h.bit(latch,'E'),
                     'Q':h.bit(latch,'Q'),'QN':h.bit(latch,'QN'),
                     'memory_q':h.bit(mem,'ConfigBits',j),'memory_qn':h.bit(mem,'ConfigBits_N',j),
                     'tile_q':h.bit(path,'ConfigBits',j),'tile_qn':h.bit(path,'ConfigBits_N',j)}
            for names in [('frame_data','memory_data','D'),('frame_strobe','memory_strobe','E'),
                          ('Q','memory_q','tile_q'),('QN','memory_qn','tile_qn')]:
                require(len({chain[n] for n in names}) == 1, witness+'/'+names[-1], names, chain)
            require(chain['Q'] != chain['QN'] and chain['Q'][0] != 'constant' and chain['QN'][0] != 'constant', witness+'/storage')
            for polarity in ('Q','QN'):
                require(chain[polarity] not in state_owners, state_owners.get(chain[polarity],witness)+'/state-ownership', 'register/config storage disjoint', chain[polarity])
                require(chain[polarity] not in independent_inputs, witness+'/input-storage-alias')
                require(chain[polarity] not in config_owners, witness+'/unique-storage', 'unique', chain[polarity])
                config_owners.add(chain[polarity])
            consumer = h.bit(lut,'ConfigBits',j) if j < 19 else h.bit(switch,'ConfigBits',0)
            require(consumer == chain['Q'], witness+'/consumer', chain['Q'], consumer, 'config-consumer-mismatch')
            if j == 19:
                require(h.bit(mux,'S') == chain['Q'], witness+'/mux.S', chain['Q'], h.bit(mux,'S'), 'config-consumer-mismatch')
                require(h.bit(switch,'ConfigBits_N') == chain['QN'], witness+'/complement')
            storage = check_latch_body(h,latch,witness)
            records[witness] = {'storage':storage,'latch': latch, 'chain':chain, 'consumer': consumer}
    h.ports('', top_contract)
    h.driver_ownership()
    links = {(a+'.e', b+'.w') for a, pa in tilepins.items() if 'e' in pa
             for b, pb in tilepins.items() if 'w' in pb and pa['e'] == pb['w']}
    check_declared_edges(shape_id, [list(e) for e in sorted(links)])
    for a,b in links:
        records[f'LINK/{shape_id}/{a}->{b}'] = {'from':a,'to':b}
    require(set(records) == set(roster), shape_id+'/witness-roster', sorted(roster), sorted(records))
    return {'shape':shape_id,'status':'passed','records':records,
            'counts':{kind:sum(k.startswith(kind+'/') for k in records) for kind in ('PIN','FIXED','SELECT','CONFIG','RESOURCE','LINK')}}

def _pointer(*parts):
    return '/'+'/'.join(str(p).replace('~','~0').replace('/','~1') for p in parts)

class SourceCatalog:
    """Actual compiled-source spans; never a parser for expected HDL behavior."""
    def __init__(self, root, hashes, mount):
        self.root=Path(root); self.mount=mount.rstrip('/')+'/'
        require(self.root.is_dir() and not self.root.is_symlink(), 'source-root', category='provenance-mismatch')
        rows=(self.root/'sources.f').read_text().splitlines()
        require(isinstance(hashes,dict) and rows and len(rows)==len(set(rows)) and set(rows)==set(hashes),
                'source-roster', rows, sorted(hashes) if isinstance(hashes,dict) else hashes, 'provenance-mismatch')
        self.files={}; self.hashes=dict(hashes)
        for name in rows:
            relative=Path(name)
            require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in name,
                    'source-path/'+name, category='provenance-mismatch')
            path=self.root/relative
            require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(self.root.resolve()),
                    'source-file/'+name, category='provenance-mismatch')
            data=path.read_bytes(); got=hashlib.sha256(data).hexdigest()
            require(got==hashes[name], 'source-hash/'+name,hashes[name],got,'provenance-mismatch')
            self.files[name]=data.decode('utf-8').splitlines()

    def spans(self, src, scope):
        require(isinstance(src,str) and bool(src),'source-attribute', 'nonempty attributes.src',src,'provenance-mismatch')
        result=[]
        for span in src.split('|'):
            match=re.fullmatch(r'(.+):(\d+)\.(\d+)-(\d+)\.(\d+)',span)
            require(match is not None,'source-span', 'path:L.C-L.C',span,'provenance-mismatch')
            path,sl,sc,el,ec=match.groups()
            require(path.startswith(self.mount),'source-mount',self.mount,path,'provenance-mismatch')
            name=path[len(self.mount):]
            require(name in self.files,'source-membership',sorted(self.files),name,'provenance-mismatch')
            sl,sc,el,ec=map(int,(sl,sc,el,ec)); lines=self.files[name]
            require(1<=sl<=el<=len(lines) and 1<=sc<=len(lines[sl-1])+1 and
                    1<=ec<=len(lines[el-1])+1 and (sl<el or sc<=ec),
                    'source-bounds/'+name,None,(sl,sc,el,ec),'provenance-mismatch')
            result.append({'path':name,'start_line':sl,'start_column':sc,'end_line':el,
                           'end_column':ec,'sha256':self.hashes[name],'scope':scope})
        return result

    def text(self, binding):
        lines=self.files[binding['path']][binding['start_line']-1:binding['end_line']]
        if len(lines)==1: return lines[0][binding['start_column']-1:binding['end_column']-1]
        return '\n'.join([lines[0][binding['start_column']-1:]]+lines[1:-1]+[lines[-1][:binding['end_column']-1]])

class Provenance:
    def __init__(self,h,catalog,shape_id):
        self.h,self.catalog,self.shape_id=h,catalog,shape_id
        self.shape,_=expected(shape_id); _,self.corr=oracle(); self.modules={}
        for path,(module,key,origin) in h.nodes.items():
            if key in self.modules: continue
            spans=catalog.spans(module.get('attributes',{}).get('src'),'module')
            require(sum(len(re.findall(r'\bmodule\s+\\?'+re.escape(origin)+r'(?=\s|[#(;])',catalog.text(b))) for b in spans)==1,
                    'source-module/'+key,origin,None,'provenance-mismatch')
            self.modules[key]=spans

    def _anchors(self,path,obj,scope):
        module,key,_=self.h.nodes[path]
        if obj.get('attributes',{}).get('src'):
            refs=self.catalog.spans(obj['attributes']['src'],scope)
            for ref in refs:
                require(any(ref['path']==parent['path'] and
                            (parent['start_line'],parent['start_column']) <= (ref['start_line'],ref['start_column']) and
                            (ref['end_line'],ref['end_column']) <= (parent['end_line'],parent['end_column'])
                            for parent in self.modules[key]),
                        'source-containment/'+path,category='provenance-mismatch')
        else:
            require(scope=='net-declaration','source-attribute/'+path,'attributes.src for cell',None,'provenance-mismatch')
            refs=[dict(b,scope='module-fallback') for b in self.modules[key]]
        return refs

    def ref(self,path,name=None,index=0):
        module,key,origin=self.h.nodes[path]
        result={'path':path+('.'+name if name else ''),'module_key':key,'type':origin,
                'kind':'module' if name is None else 'signal','direction':'resource',
                'json_pointer':_pointer('modules',key),'source_bindings':self.modules[key]}
        if name is None:
            result['ports']={port:{'direction':desc['direction'],'width':len(desc['bits']),
                                   'bits':self.h.bits(path,port),'offset':desc.get('offset',0),
                                   'upto':desc.get('upto',0),
                                   'json_pointer':_pointer('modules',key,'ports',port)}
                             for port,desc in module.get('ports',{}).items()}
        if name=='GND0':
            found=[]
            for binding in self.modules[key]:
                for number in range(binding['start_line'],binding['end_line']+1):
                    line=self.catalog.files[binding['path']][number-1]
                    if re.search(r'\bparameter\s+GND0\s*=',line):
                        found.append(dict(binding,start_line=number,end_line=number,start_column=1,
                                          end_column=len(line)+1,scope='parameter-declaration'))
            require(len(found)==1,'source-parameter/'+path+'.GND0','one declaration',found,'provenance-mismatch')
            result.update(kind='parameter',direction='source',bit=('constant','0'),
                          json_pointer=_pointer('modules',key,'parameter_default_values','GND0'),source_bindings=found)
        elif name is not None:
            net=module.get('netnames',{}).get(name,module.get('ports',{}).get(name))
            require(net is not None,'source-net/'+path+'.'+name,category='provenance-mismatch')
            port=module.get('ports',{}).get(name)
            result.update(direction=port['direction'] if port else 'internal',bit=self.h.bit(path,name,index),
                          index=index,json_pointer=_pointer('modules',key,'netnames' if name in module.get('netnames',{}) else 'ports',name),
                          source_bindings=self._anchors(path,net,'net-declaration'))
        if path:
            parent,_,instance=path.rpartition('.')
            cell=self.h.nodes[parent][0]['cells'][instance]
            result['instance_json_pointer']=_pointer('modules',self.h.nodes[parent][1],'cells',instance)
            result['instance_source_bindings']=self._anchors(parent,cell,'cell-instance')
        return result

    def logical(self,tile,pin):
        path=self.corr['tile_instance'].format(**tile)
        mapping=dict(self.corr['pin_map'],**self.corr['variant_pin_map'][tile['type']])[pin]
        ref=mapping['reference'].format(type=tile['type']); parts=ref.split('.')
        path+='.'+'.'.join(parts[:-1]) if len(parts)>1 else ''
        match=re.fullmatch(r'([^\[]+)(?:\[(\d+)\])?',parts[-1]); name,index=match.groups()
        result=self.ref(path,name,int(index or 0)); result['semantic_direction']=mapping['direction']
        return result

    def record(self,identity):
        parts=identity.split('/'); kind=parts[0]
        tiles={t['id']:t for t in self.shape['tiles']}
        if kind=='LINK':
            a,b=parts[2].split('->'); ta,pa=a.split('.');tb,pb=b.split('.')
            return [self.logical(tiles[ta],pa),self.logical(tiles[tb],pb)]
        if len(parts)<4 or parts[2] not in tiles: return []
        tile=tiles[parts[2]]; path=self.corr['tile_instance'].format(**tile); typ=tile['type']
        if kind=='PIN': return [self.logical(tile,parts[3])]
        if kind=='FIXED': return [self.logical(tile,p) for p in parts[3].split('->')]
        if kind=='SELECT':
            mux=path+'.'+self.corr['resource_map']['mux'].format(type=typ)
            return [self.ref(mux,p) for p in ('A'+parts[3],'S','X')]
        if kind=='RESOURCE':
            resource=parts[3]; target=path+'.'+self.corr['resource_map'][resource].format(type=typ)
            if resource=='lut.register':
                node,_,net=target.rpartition('.'); refs=[self.ref(node,net)]
                for name,cell,port in output_drivers(self.h,node,self.h.bit(node,net)):
                    refs.append({'path':node+'.'+name,'kind':'primitive','type':cell['type'],'direction':'output',
                                 'module_key':self.h.nodes[node][1],
                                 'bit':self.h.bit(node,net),'json_pointer':_pointer('modules',self.h.nodes[node][1],'cells',name),
                                 'source_bindings':self._anchors(node,cell,'lowered-state-driver')})
                return refs
            return [self.ref(target)]
        if kind=='CONFIG':
            j=int(parts[3]); mem=path+f'.Inst_{typ}_ConfigMem'; latch=mem+f'.Inst_frame0_bit{12+j}'
            points=[('', 'FrameData',32*tile['y']+12+j),('', 'FrameStrobe',20*tile['x']),
                    (path,'FrameData',12+j),(path,'FrameStrobe',0),(mem,'FrameData',12+j),(mem,'FrameStrobe',0),
                    (latch,'D',0),(latch,'E',0),(latch,'Q',0),(latch,'QN',0),
                    (mem,'ConfigBits',j),(mem,'ConfigBits_N',j),(path,'ConfigBits',j),(path,'ConfigBits_N',j)]
            if j<19: points.append((path+'.Inst_L_LUT4c_frame_config_dffesr','ConfigBits',j))
            else: points += [(path+f'.Inst_{typ}_switch_matrix','ConfigBits',0),
                             (path+f'.Inst_{typ}_switch_matrix','ConfigBits_N',0),
                             (path+f'.Inst_{typ}_switch_matrix.inst_cus_mux21_L_I0','S',0)]
            refs=[self.ref(p,n,i) for p,n,i in points]
            bits={self.h.bit(p,n,i) for p,n,i in points}
            for p,(_,_,origin) in self.h.nodes.items():
                if origin in ('my_buf','clk_buf') and self.h.bit(p,'A') in bits:
                    refs.extend([self.ref(p,'A'),self.ref(p,'X')])
            for output in ('Q','QN'):
                for name,cell,port in output_drivers(self.h,latch,self.h.bit(latch,output)):
                    refs.append({'path':latch+'.'+name,'kind':'primitive','type':cell['type'],'direction':'output',
                                 'module_key':self.h.nodes[latch][1],
                                 'bit':self.h.bit(latch,output),'json_pointer':_pointer('modules',self.h.nodes[latch][1],'cells',name),
                                 'source_bindings':self._anchors(latch,cell,'lowered-storage-driver')})
            return refs
        return []

def check_shape(shape_id,yosys_json,*,source_root,source_hashes,source_mount='/inputs/generated',defines=(),correspondence=None):
    catalog=SourceCatalog(source_root,source_hashes,source_mount)
    h=Hierarchy(yosys_json); provenance=Provenance(h,catalog,shape_id)
    try:
        result=_check_shape(shape_id,yosys_json,h,defines=defines,correspondence=correspondence)
    except StructureError as error:
        error.candidate_refs=provenance.record(error.witness)
        raise
    for identity,record in result['records'].items():
        refs=provenance.record(identity)
        require(bool(refs),'candidate-refs/'+identity,category='provenance-mismatch')
        record['candidate_refs']=refs
    result['source_sha256']=dict(source_hashes)
    return result

def check_all(exports,*,source_roots,source_hashes,source_mount='/inputs/generated',defines=()):
    require(set(exports)==set(source_roots)==set(source_hashes)=={'one','square','odd','sparse'},'shape-roster')
    results=[check_shape(shape,exports[shape],source_root=source_roots[shape],source_hashes=source_hashes[shape],
                         source_mount=source_mount,defines=defines) for shape in ('one','square','odd','sparse')]
    return {'status':'passed','shapes':results,'counts':{k:sum(r['counts'][k] for r in results) for k in results[0]['counts']}}
