"""Removed methods must not be discoverable or callable in v1.11."""
import importlib.util,json,unittest
from pathlib import Path
import numpy as np
import pylstemp
from pylstemp import emissivity,split_window,list_algorithms
from pylstemp.exceptions import InvalidMethodRequested

class RemovedMethods(unittest.TestCase):
    def test_both_catalog_views_contain_only_available_methods(self):
        a=list_algorithms();b=list_algorithms(include_inactive=True)
        self.assertEqual(a,b)
        keys={k for family,items in b.items() if family!='credit' for k in items}
        self.assertEqual(len(keys),14)
        self.assertTrue(keys.isdisjoint({'rozenstein-2014','sobrino-2004-tm6','sobrino-2008'}))
        for family,items in b.items():
            if family!='credit':
                for item in items.values():self.assertEqual(item['workflow_status'],'active')

    def test_removed_calls_fail(self):
        t=np.array([300.]);u=t-2
        with self.assertRaises(InvalidMethodRequested):
            split_window(t,u,lst_method='rozenstein-2014',emissivity_10=np.array([.97]),emissivity_11=np.array([.98]))
        for key in ['sobrino-2004-tm6','sobrino-2008','sobrino-2008-simplified','sobrino-2008-full']:
            with self.subTest(method=key),self.assertRaises(InvalidMethodRequested):emissivity(np.array([.35]),method=key)

    def test_modules_exports_and_cards_are_absent(self):
        import pylstemp.algorithms.split_window as sw
        self.assertFalse(hasattr(sw,'SplitWindowRozenstein2014LST'))
        for module in ['pylstemp.algorithms.split_window.rozenstein_2014','pylstemp.emissivity_models']:
            self.assertIsNone(importlib.util.find_spec(module))
        cards=json.loads(Path(pylstemp.__file__).with_name('method_cards.json').read_text(encoding='utf8'))
        self.assertEqual(len(cards),16)
        self.assertFalse(any(c['method'] in {'rozenstein-2014','sobrino-2004-tm6'} or c['method'].startswith('sobrino-2008') for c in cards))

if __name__=='__main__':unittest.main()
