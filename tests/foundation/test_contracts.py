"""Independent structural negative controls; no RTL/formal execution credit."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from check_foundation_contracts import ContractError, load, unique_object, validate_ledger, validate_subset, validate_reference


class LedgerControls(unittest.TestCase):
    def setUp(self):
        self.data = load(ROOT / 'verify/fixtures/assumptions/ledger.json')

    def reject(self, mutate, diagnostic):
        mutate(self.data)
        with self.assertRaisesRegex(ContractError, diagnostic):
            validate_ledger(self.data)

    def test_current_contracts(self):
        self.assertEqual(validate_ledger(self.data), 12)
        self.assertEqual(self.data['records'][0]['id'], 'ASM-0001')
        self.assertEqual(self.data['records'][-1]['id'], 'ASM-0012')

    def test_duplicate_json_key(self):
        with self.assertRaisesRegex(ContractError, 'FND02-DUPLICATE-KEY'):
            json.loads('{"id": 1, "id": 2}', object_pairs_hook=unique_object)

    def test_duplicate_assumption(self):
        self.reject(lambda d: d['records'].append(copy.deepcopy(d['records'][0])), 'FND02-ASSUMPTION-DUPLICATE')

    def test_missing_claim(self):
        self.reject(lambda d: d['records'][0].pop('claim'), 'FND02-RECORD-FIELD')

    def test_missing_expected_examples(self):
        self.reject(lambda d: d['records'][0].update(independent_expected_examples=[]), 'FND02-RECORD-FIELD')

    def test_execution_not_implied_by_acceptance(self):
        self.data['records'][0]['decision_state'] = 'accepted-for-profile'
        self.assertEqual(validate_ledger(self.data), 12)
        self.reject(lambda d: d['records'][0].update(evidence_state='passed-with-stated-scope'), 'FND02-EXECUTION-CREDIT')

    def test_future_obligation_not_passed(self):
        self.reject(lambda d: d['records'][0]['required_obligations'][0].update(evidence_state='passed'), 'FND02-EXECUTION-CREDIT')

    def test_formal_claim_not_invented(self):
        self.reject(lambda d: d['records'][0]['formal_scope'].update(kind='unbounded-proof'), 'FND02-FORMAL-CREDIT')

    def test_unknown_superseded_id(self):
        self.reject(lambda d: d['records'][0].update(supersedes=['ASM-9999']), 'FND02-HISTORY')

    def test_duplicate_obligation(self):
        self.reject(lambda d: d['records'][0]['required_obligations'].append(copy.deepcopy(d['records'][0]['required_obligations'][0])), 'FND02-OBLIGATION-DUPLICATE')

    def test_proposal_cannot_close(self):
        self.data['records'][0]['decision_state'] = 'proposed'
        with self.assertRaisesRegex(ContractError, 'FND02-UNACCEPTED'):
            validate_ledger(self.data, accepted=True)

    def test_pending_review_cannot_close(self):
        for record in self.data['records']:
            record['decision_state'] = 'accepted-for-profile'
        self.data['records'][0]['reviewer'] = 'pending'
        with self.assertRaisesRegex(ContractError, 'FND02-REVIEW-PENDING'):
            validate_ledger(self.data, accepted=True)



class SubsetControls(unittest.TestCase):
    def setUp(self):
        self.spec = load(ROOT / 'verify/fixtures/nf-tiny/specification.json')
        self.mapping = load(ROOT / 'verify/fixtures/nf-tiny/correspondence.json')
        self.ids = {f'ASM-{i:04}' for i in range(1, 13)}

    def reject(self, diagnostic):
        with self.assertRaisesRegex(ContractError, diagnostic):
            validate_subset(self.spec, self.mapping, self.ids)

    def test_independent_vectors(self):
        self.assertEqual(validate_subset(self.spec, self.mapping, self.ids),
                         {'shapes': 4, 'lut_addresses': 16, 'mux_cases': 8, 'config_bits': 20})

    def test_swapped_lut_bit(self):
        self.spec['lut_witness']['rows'][2]['expected'] = 1
        self.reject('FND02-LUT-VECTOR')

    def test_missing_lut_address(self):
        self.spec['lut_witness']['rows'].pop()
        self.reject('FND02-LUT-COVERAGE')

    def test_mux_polarity(self):
        self.spec['mux_witness']['rows'][2]['expected'] = 1
        self.reject('FND02-MUX-VECTOR')

    def test_reset_priority(self):
        self.spec['register_witnesses'][0]['steps'][5]['q'] = 0
        self.reject('FND02-REGISTER-VECTOR')

    def test_missing_pin(self):
        self.mapping['pin_map'].pop('y')
        self.reject('FND02-PIN-TOTALITY')

    def test_ambiguous_pin(self):
        self.mapping['pin_map']['lut.i0']['reference'] = self.mapping['pin_map']['lut.i3']['reference']
        self.reject('FND02-PIN-ORDER')

    def test_swapped_pin_map(self):
        a = self.mapping['pin_map']['lut.i0']['reference']
        self.mapping['pin_map']['lut.i0']['reference'] = self.mapping['pin_map']['lut.i3']['reference']
        self.mapping['pin_map']['lut.i3']['reference'] = a
        self.reject('FND02-PIN-ORDER')

    def test_missing_link(self):
        self.spec['shapes'][1]['intertile_edges'].pop()
        self.reject('FND02-GRAPH-COVERAGE')

    def test_wrong_output_direction(self):
        self.mapping['pin_map']['y']['direction'] = 'input'
        self.reject('FND02-PIN-CONTRACT')

    def test_nonexistent_output(self):
        self.mapping['pin_map']['y']['reference'] = 'missing'
        self.reject('FND02-PIN-CONTRACT')

    def test_wrong_logical_index(self):
        self.mapping['config_map'][0]['logical_index'] = 9
        self.reject('FND02-CONFIG-INDEX')

    def test_illegal_legal_configuration(self):
        self.spec['legal_configurations'][0]['logical']['carry_i0'] = 1
        self.spec['legal_configurations'][0]['config_hex'] = '2A6D3'
        self.spec['legal_configurations'][0]['frame0_hex'] = '2A6D3000'
        self.reject('FND02-CONFIG-ILLEGAL')

    def test_empty_register_witnesses(self):
        self.spec['register_witnesses'] = []
        self.reject('FND02-REGISTER-COVERAGE')

    def test_empty_obligations(self):
        self.spec['obligations'] = []
        self.reject('FND02-OBLIGATION-COVERAGE')

    def test_empty_negatives(self):
        self.spec['illegal_configurations'] = []
        self.reject('FND02-NEGATIVE-COVERAGE')

    def test_unaccepted_subset(self):
        self.spec['decision_state'] = 'proposed'
        with self.assertRaisesRegex(ContractError, 'FND02-UNACCEPTED'):
            validate_subset(self.spec, self.mapping, self.ids, accepted=True)

    def test_empty_shapes(self):
        self.spec['shapes'] = []
        self.reject('FND02-SHAPE-COVERAGE')

    def test_variant_direction(self):
        self.mapping['variant_pin_map']['NF_RIGHT']['w']['direction'] = 'output'
        self.reject('FND02-VARIANT-PIN-CONTRACT')

    def test_variant_reference(self):
        self.mapping['variant_pin_map']['NF_RIGHT']['w']['reference'] = 'missing'
        self.reject('FND02-VARIANT-PIN-CONTRACT')

    def test_reverse_link(self):
        self.spec['shapes'][1]['intertile_edges'][0].reverse()
        self.reject('FND02-GRAPH-DIRECTION')

    def test_overlap_field(self):
        self.mapping['config_map'][-1]['data_bit'] = 28
        self.reject('FND02-CONFIG-OVERLAP')

    def test_wrong_address(self):
        self.mapping['config_map'][0]['data_bit'] = 11
        self.reject('FND02-CONFIG-ADDRESS')

    def test_wrong_config_vector(self):
        self.spec['legal_configurations'][0]['frame0_hex'] = '0A6D2000'
        self.reject('FND02-CONFIG-VECTOR')

    def test_missing_hole(self):
        self.spec['shapes'][3]['holes'].pop()
        self.reject('FND02-SHAPE-HOLES')

    def test_unknown_assumption(self):
        self.mapping['assumptions'].append('ASM-9999')
        self.reject('FND02-ASSUMPTION-REFERENCE')



class ReferenceControls(unittest.TestCase):
    def setUp(self):
        self.manifest = load(ROOT / 'verify/fixtures/nf-tiny/reference.json')

    def test_hash_inventory(self):
        self.assertGreaterEqual(validate_reference(ROOT, self.manifest), 20)

    def test_corrupt_input_hash(self):
        self.manifest['input_files'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ContractError, 'FND02-INPUT-HASH'):
            validate_reference(ROOT, self.manifest)

    def test_missing_input(self):
        self.manifest['input_files'].pop()
        with self.assertRaisesRegex(ContractError, 'FND02-INPUT-INVENTORY'):
            validate_reference(ROOT, self.manifest)

    def test_escape_input(self):
        self.manifest['input_files'][0]['path'] = '../outside'
        with self.assertRaisesRegex(ContractError, 'FND02-INPUT-PATH'):
            validate_reference(ROOT, self.manifest)

    def test_proposed_reference_not_accepted(self):
        self.manifest['decision_state'] = 'proposed'
        with self.assertRaisesRegex(ContractError, 'FND02-UNACCEPTED'):
            validate_reference(ROOT, self.manifest, accepted=True)


if __name__ == '__main__':
    unittest.main()
