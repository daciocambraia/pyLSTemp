"""Methods with the same selector must retain distinct scientific identities."""
import unittest
from pylstemp import list_algorithms
from pylstemp.provenance import _card, _card_index, optical_contract


class MethodIdentity(unittest.TestCase):
    def test_cards_are_unique_by_family_and_method(self):
        index=_card_index()
        self.assertEqual(len(index),16)
        self.assertIsNotNone(index.get(('single_channel','avdan-2016')))
        self.assertIsNotNone(index.get(('emissivity','avdan-2016')))
        self.assertNotEqual(index[('single_channel','avdan-2016')]['equation'],
                            index[('emissivity','avdan-2016')]['equation'])
        self.assertNotEqual(index[('single_channel','jimenez-munoz-2014')]['coefficients'],
                            index[('split_window','jimenez-munoz-2014')]['coefficients'])

    def test_optical_contract_uses_the_requested_family(self):
        for family in ('emissivity','single_channel'):
            contract=optical_contract('avdan-2016',None,family=family)
            self.assertEqual(contract['family'],family)
            self.assertEqual(contract['source_condition'],_card(family,'avdan-2016')['optical_contract'])
        contract=optical_contract('kerr-1992','surface_reflectance',family='split_window')
        self.assertEqual(contract['source_condition'],_card('split_window','kerr-1992')['optical_contract'])

    def test_catalog_uses_each_exact_scientific_card(self):
        catalog=list_algorithms()
        for family,items in catalog.items():
            if family=='credit':continue
            for method,item in items.items():
                with self.subTest(family=family,method=method):
                    card=_card(family,method)
                    self.assertIsNotNone(card)
                    self.assertEqual(item['source_location'],card['source_location'])
                    self.assertEqual(item['optical_input_contract'],card['optical_contract'])
