"""Validate FND-02 contract records; this is not hardware execution evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class ContractError(ValueError):
    pass


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"FND02-DUPLICATE-KEY: {key}")
        result[key] = value
    return result


def load(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(), object_pairs_hook=unique_object)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"FND02-JSON: {path}: {exc}") from exc
    if not isinstance(result, dict):
        raise ContractError(f"FND02-OBJECT: {path}")
    return result


def validate_ledger(data: dict, *, accepted: bool = False) -> int:
    if data.get('format_version') != 1:
        raise ContractError('FND02-LEDGER-VERSION: expected 1')
    records = data.get('records')
    if not isinstance(records, list) or not records:
        raise ContractError('FND02-LEDGER-EMPTY: records required')
    identifiers = set()
    for record in records:
        if not isinstance(record, dict):
            raise ContractError('FND02-RECORD: object required')
        identifier = record.get('id')
        if not isinstance(identifier, str) or not re.fullmatch(r'ASM-[0-9]{4}', identifier):
            raise ContractError('FND02-ASSUMPTION-ID: stable ASM-xxxx required')
        if identifier in identifiers:
            raise ContractError(f'FND02-ASSUMPTION-DUPLICATE: {identifier}')
        identifiers.add(identifier)
        for field in ['title', 'claim', 'rationale', 'source_revision', 'owner', 'reviewer',
                      'owning_increment', 'change_policy']:
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ContractError(f'FND02-RECORD-FIELD: {identifier}/{field}')
        for field in ['affected_consumers', 'independent_expected_examples', 'required_obligations']:
            if not isinstance(record.get(field), list) or not record[field]:
                raise ContractError(f'FND02-RECORD-FIELD: {identifier}/{field}')
        profile = record.get('profile')
        if not isinstance(profile, dict) or not profile.get('id') or not profile.get('version'):
            raise ContractError(f'FND02-PROFILE: {identifier}')
        decision = record.get('decision_state')
        if decision not in {'proposed', 'accepted-for-profile', 'disputed', 'superseded'}:
            raise ContractError(f'FND02-DECISION: {identifier}')
        if accepted and decision != 'accepted-for-profile':
            raise ContractError(f'FND02-UNACCEPTED: {identifier}')
        if accepted and 'pending' in record['reviewer'].lower():
            raise ContractError(f'FND02-REVIEW-PENDING: {identifier}')
        # FND-02 accepts contracts, never claims future execution.
        if record.get('evidence_state') != 'not-run':
            raise ContractError(f'FND02-EXECUTION-CREDIT: {identifier}')
        obligations = set()
        for item in record['required_obligations']:
            if not isinstance(item, dict) or not item.get('id') or not item.get('owner') or not item.get('scope'):
                raise ContractError(f'FND02-OBLIGATION: {identifier}')
            if item['id'] in obligations:
                raise ContractError(f'FND02-OBLIGATION-DUPLICATE: {identifier}/{item["id"]}')
            obligations.add(item['id'])
            if item.get('evidence_state') != 'not-run':
                raise ContractError(f'FND02-EXECUTION-CREDIT: {identifier}/{item["id"]}')
        formal = record.get('formal_scope')
        if not isinstance(formal, dict) or formal.get('kind') != 'not-run' or formal.get('bound') is not None or formal.get('assumptions') != []:
            raise ContractError(f'FND02-FORMAL-CREDIT: {identifier}')
        if not isinstance(record.get('supersedes'), list):
            raise ContractError(f'FND02-HISTORY: {identifier}')
    for record in records:
        for previous in record['supersedes']:
            if previous == record['id'] or previous not in identifiers:
                raise ContractError(f'FND02-HISTORY: {record["id"]}/{previous}')
    return len(records)


def validate_subset(spec: dict, correspondence: dict, assumption_ids: set[str], *, accepted: bool = False) -> dict:
    for name, record in [('specification', spec), ('correspondence', correspondence)]:
        if record.get('format_version') != 1 or record.get('profile') != 'nf-tiny-foundation/1':
            raise ContractError(f'FND02-SUBSET-VERSION: {name}')
        if record.get('evidence_state') != 'not-run':
            raise ContractError(f'FND02-EXECUTION-CREDIT: {name}')
        if accepted and record.get('decision_state') != 'accepted-for-profile':
            raise ContractError(f'FND02-UNACCEPTED: {name}')
        if not set(record.get('assumptions', [])) <= assumption_ids:
            raise ContractError(f'FND02-ASSUMPTION-REFERENCE: {name}')
    witness = spec['lut_witness']
    rows = witness['rows']
    if [r['address'] for r in rows] != list(range(16)):
        raise ContractError('FND02-LUT-COVERAGE: expected each address once')
    init = int(witness['init_hex'], 16)
    for row in rows:
        address = row['address']
        if row['input'] != format(address, '04b') or row['expected'] != (init >> address) & 1:
            raise ContractError(f'FND02-LUT-VECTOR: address {address}')
    mux_cases = set()
    for row in spec['mux_witness']['rows']:
        key = (row['a0'], row['a1'], row['select'])
        if key in mux_cases or any(type(v) is not int or v not in (0, 1) for v in key):
            raise ContractError('FND02-MUX-COVERAGE: invalid/duplicate case')
        mux_cases.add(key)
        if row['expected'] != key[key[2]]:
            raise ContractError('FND02-MUX-VECTOR: ordered input mismatch')
    if len(mux_cases) != 8:
        raise ContractError('FND02-MUX-COVERAGE: expected 8 cases')
    if len(spec['register_witnesses']) != 2 or {seq['reset_value'] for seq in spec['register_witnesses']} != {0, 1}:
        raise ContractError('FND02-REGISTER-COVERAGE')
    for sequence in spec['register_witnesses']:
        if len(sequence['steps']) < 5 or {step['q'] for step in sequence['steps']} != {0, 1}:
            raise ContractError('FND02-REGISTER-COVERAGE')
        q = sequence['initial_q']
        for step in sequence['steps']:
            if step['edge'] == 'rise' and step['en']:
                q = sequence['reset_value'] if step['sr'] else step['d']
            if q is None or step['q'] != q:
                raise ContractError('FND02-REGISTER-VECTOR: enable-gated synchronous reset mismatch')
    graph = spec['tile_graph']
    common = set(graph['common_pins'])
    if len(common) != len(graph['common_pins']) or set(correspondence['pin_map']) != common:
        raise ContractError('FND02-PIN-TOTALITY: common pins')
    expected_pins = {
        **{f'a{i}': ('input', f'P_A{i}') for i in range(4)},
        'clk': ('input', 'UserCLK'), 'lut.clk': ('input', 'Inst_L_LUT4c_frame_config_dffesr.UserCLK'),
        'alt': ('input', 'P_ALT'), 'enable': ('input', 'P_ENABLE'),
        'reset': ('input', 'P_RESET'), 'y': ('output', 'P_Y'),
        'const0': ('source', 'Inst_{type}_switch_matrix.GND0'),
        'mux.a0': ('input', 'Inst_{type}_switch_matrix.L_I0_input[0]'),
        'mux.a1': ('input', 'Inst_{type}_switch_matrix.L_I0_input[1]'),
        'mux.y': ('output', 'Inst_{type}_switch_matrix.L_I0'),
        **{f'lut.{pin}': (direction, f'Inst_L_LUT4c_frame_config_dffesr.{name}')
           for pin, direction, name in [('ci', 'input', 'Ci'), ('en', 'input', 'EN'),
                                        ('sr', 'input', 'SR'), ('o', 'output', 'O')]},
    }
    for pin, (direction, reference) in expected_pins.items():
        entry = correspondence['pin_map'][pin]
        if entry['direction'] != direction or entry['reference'] != reference:
            raise ContractError(f'FND02-PIN-CONTRACT: {pin}')
    for index in range(4):
        entry = correspondence['pin_map'][f'lut.i{index}']
        if entry['reference'] != f'Inst_L_LUT4c_frame_config_dffesr.I[{index}]' or entry['direction'] != 'input':
            raise ContractError('FND02-PIN-ORDER: LUT input significance')
    variants = graph['variants']
    if set(variants) != set(correspondence['variant_pin_map']):
        raise ContractError('FND02-PIN-TOTALITY: variants')
    for variant, detail in variants.items():
        maps = dict(correspondence['pin_map'])
        maps.update(correspondence['variant_pin_map'][variant])
        expected = common | set(detail['additional_pins'])
        if set(maps) != expected or set(correspondence['variant_pin_map'][variant]) != set(detail['additional_pins']):
            raise ContractError(f'FND02-PIN-TOTALITY: {variant}')
        for pin, entry in correspondence['variant_pin_map'][variant].items():
            if (entry['direction'], entry['reference']) != {'e': ('output', 'E[0]'), 'w': ('input', 'W[0]')}[pin]:
                raise ContractError('FND02-VARIANT-PIN-CONTRACT')
        refs = [entry['reference'] for entry in maps.values()]
        if len(set(refs)) != len(refs):
            raise ContractError(f'FND02-PIN-AMBIGUITY: {variant}')
        if any(entry['direction'] not in {'input', 'output', 'source'} for entry in maps.values()):
            raise ContractError(f'FND02-PIN-DIRECTION: {variant}')
        edges = graph['common_fixed_edges'] + detail['additional_fixed_edges']
        if len({tuple(edge) for edge in edges}) != len(edges) or any(len(edge) != 2 or not set(edge) <= expected for edge in edges):
            raise ContractError(f'FND02-GRAPH-ENDPOINT: {variant}')
    if {shape['id'] for shape in spec['shapes']} != {'one', 'square', 'odd', 'sparse'}:
        raise ContractError('FND02-SHAPE-COVERAGE')
    shape_ids = set()
    for shape in spec['shapes']:
        if shape['id'] in shape_ids:
            raise ContractError('FND02-SHAPE-DUPLICATE')
        shape_ids.add(shape['id'])
        tiles = {tile['id']: tile for tile in shape['tiles']}
        positions = {(tile['x'], tile['y']) for tile in shape['tiles']}
        if len(tiles) != len(shape['tiles']) or len(positions) != len(tiles):
            raise ContractError('FND02-TILE-DUPLICATE')
        for tile in tiles.values():
            if tile['type'] not in variants or not (0 <= tile['x'] < shape['width'] and 0 <= tile['y'] < shape['height']):
                raise ContractError('FND02-TILE-BOUNDS')
        edges = shape['intertile_edges']
        if len({tuple(edge) for edge in edges}) != len(edges):
            raise ContractError('FND02-EDGE-DUPLICATE')
        for src, dst in edges:
            a, ap = src.split('.', 1)
            b, bp = dst.split('.', 1)
            if a not in tiles or b not in tiles:
                raise ContractError('FND02-GRAPH-ENDPOINT: unknown tile')
            a, b = tiles[a], tiles[b]
            if ap != 'e' or bp != 'w' or a['y'] != b['y'] or b['x'] != a['x'] + 1:
                raise ContractError('FND02-GRAPH-DIRECTION: expected adjacent east link')
            if ap not in variants[a['type']]['additional_pins'] or bp not in variants[b['type']]['additional_pins']:
                raise ContractError('FND02-GRAPH-ENDPOINT: missing variant pin')
        expected_sources = {f"{tile['id']}.e" for tile in tiles.values() if 'e' in variants[tile['type']]['additional_pins']}
        expected_sinks = {f"{tile['id']}.w" for tile in tiles.values() if 'w' in variants[tile['type']]['additional_pins']}
        if {edge[0] for edge in edges} != expected_sources or {edge[1] for edge in edges} != expected_sinks or len(edges) != len(expected_sources) or len(edges) != len(expected_sinks):
            raise ContractError('FND02-GRAPH-COVERAGE: dangling or omitted link')
        holes = {tuple(item) for item in shape.get('holes', [])}
        all_positions = {(x, y) for x in range(shape['width']) for y in range(shape['height'])}
        if positions & holes or positions | holes != all_positions:
            raise ContractError('FND02-SHAPE-HOLES')
    bindings = correspondence['config_map']
    width = spec['configuration']['width']
    if sorted(binding['tile_config_bit'] for binding in bindings) != list(range(width)):
        raise ContractError('FND02-CONFIG-TOTALITY')
    addresses = [(binding['frame'], binding['data_bit']) for binding in bindings]
    if len(set(addresses)) != len(addresses):
        raise ContractError('FND02-CONFIG-OVERLAP')
    for binding in bindings:
        bit = binding['tile_config_bit']
        expected_feature = 'init' if bit < 16 else ['ff', 'carry_i0', 'reset_value', 'source'][bit - 16]
        if bit < 16 and binding.get('logical_index') != bit:
            raise ContractError('FND02-CONFIG-INDEX')
        if bit == 17 and binding.get('constraint') != 0:
            raise ContractError('FND02-CONFIG-CONSTRAINT')
        if binding['feature'] != expected_feature or (bit < 19 and binding.get('primitive_bit') != bit) or (bit == 19 and binding.get('switch_bit') != 0):
            raise ContractError('FND02-CONFIG-FEATURE')
        if binding['frame'] != 0 or binding['data_bit'] != bit + 12:
            raise ContractError('FND02-CONFIG-ADDRESS')
    if {c['id'] for c in spec['legal_configurations']} != {'comb', 'registered-reset0', 'registered-reset1', 'source1'}:
        raise ContractError('FND02-CONFIG-COVERAGE')
    for config in spec['legal_configurations']:
        logical = config['logical']
        if logical['carry_i0'] != 0 or not 0 <= int(logical['init'], 16) <= 65535 or any(type(logical[field]) is not int or logical[field] not in {0, 1} for field in ['ff', 'reset_value', 'source']):
            raise ContractError('FND02-CONFIG-ILLEGAL')
        packed = int(logical['init'], 16) | logical['ff'] << 16 | logical['carry_i0'] << 17 | logical['reset_value'] << 18 | logical['source'] << 19
        if int(config['config_hex'], 16) != packed or int(config['frame0_hex'], 16) != packed << 12:
            raise ContractError('FND02-CONFIG-VECTOR')
    required_negatives = {'carry-enabled', 'source-out-of-range', 'init-too-wide', 'undeclared-field', 'missing-field', 'undeclared-overlap', 'unknown-select', 'wrong-package', 'unmapped-address'}
    if {case['id'] for case in spec['illegal_configurations']} != required_negatives:
        raise ContractError('FND02-NEGATIVE-COVERAGE')
    required_obligations = {'LUT-EXHAUSTIVE', 'REGISTER', 'MUX', 'CONFIG', 'TILE', 'GRAPH', 'COVER-STATE', 'XZ-REJECTION', 'MUT-LUT-BIT', 'MUT-PRIORITY', 'MUT-MUX-INDEX', 'MUT-CONFIG-ADDRESS', 'MUT-CORRESPONDENCE', 'MUT-ENDPOINT', 'MUT-FIELD-ALIAS'}
    if {item['id'] for item in spec['obligations']} != {'FND06-' + item for item in required_obligations}:
        raise ContractError('FND02-OBLIGATION-COVERAGE')
    if any(item['owner'] != 'FND-06' or item['evidence_state'] != 'not-run' for item in spec['obligations']):
        raise ContractError('FND02-OBLIGATION-STATE')
    return {'shapes': len(shape_ids), 'lut_addresses': len(rows), 'mux_cases': len(mux_cases), 'config_bits': width}


def validate_reference(root: Path, manifest: dict, *, accepted: bool = False) -> int:
    if manifest.get('format_version') != 1 or manifest.get('profile') != 'nf-tiny-foundation/1':
        raise ContractError('FND02-REFERENCE-VERSION')
    if accepted and manifest.get('decision_state') != 'accepted-for-profile':
        raise ContractError('FND02-UNACCEPTED: reference')
    if manifest.get('evidence_state') != 'not-run':
        raise ContractError('FND02-EXECUTION-CREDIT: reference')
    upstream = manifest['upstream']
    if upstream['repository'] != 'https://github.com/FPGA-Research/FABulous' or not re.fullmatch('[0-9a-f]{40}', upstream['commit']):
        raise ContractError('FND02-REFERENCE-PIN')
    base = (root / 'verify/fixtures/nf-tiny').resolve()
    paths = set()
    for item in manifest['input_files']:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts or item['path'] in paths:
            raise ContractError('FND02-INPUT-PATH')
        paths.add(item['path'])
        path = base / relative
        if not path.is_file() or not path.resolve().is_relative_to(base):
            raise ContractError('FND02-INPUT-PATH')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ContractError(f'FND02-INPUT-HASH: {relative}')
    expected = {'specification.json', 'correspondence.json'} | {
        str(path.relative_to(base)) for path in (base / 'fabulous').rglob('*')
        if path.is_file() and '__pycache__' not in path.parts
    }
    if paths != expected:
        raise ContractError('FND02-INPUT-INVENTORY')
    return len(paths)


def check(root: Path = ROOT, *, accepted: bool = False) -> dict:
    ledger = load(root / 'verify/fixtures/assumptions/ledger.json')
    count = validate_ledger(ledger, accepted=accepted)
    subset = validate_subset(load(root / 'verify/fixtures/nf-tiny/specification.json'),
                             load(root / 'verify/fixtures/nf-tiny/correspondence.json'),
                             {record['id'] for record in ledger['records']}, accepted=accepted)
    inputs = validate_reference(root, load(root / 'verify/fixtures/nf-tiny/reference.json'), accepted=accepted)
    return {'reference_inputs': inputs, 'assumptions': count, 'contract_review_only': True, 'hardware_execution': 'not-run', **subset}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accepted', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(check(accepted=args.accepted), sort_keys=True))
        return 0
    except ContractError as exc:
        print(exc)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
