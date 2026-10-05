"""Release scope: Level-1 workflows with Avdan/Gopinadh, without Xiaolei."""
import importlib.util
import unittest
import numpy as np
from pylstemp import emissivity, list_algorithms, single_window, spectral_index, split_window
from pylstemp.exceptions import InvalidMethodRequested


class ReleaseScope(unittest.TestCase):
    def test_catalog_contains_only_retained_emissivity_and_twelve_algorithms(self):
        catalog = list_algorithms()
        self.assertEqual(set(catalog["emissivity"]), {"avdan-2016", "gopinadh-2018"})
        self.assertEqual(sum(len(methods) for family, methods in catalog.items()
                             if family != "credit"), 12)
        self.assertIsNone(importlib.util.find_spec(
            "pylstemp.algorithms.emissivity.xiaolei_2014"))

    def test_removed_method_is_rejected_by_each_public_workflow(self):
        t10 = np.full((3, 3), 300.)
        red = np.full(t10.shape, .2)
        nir = np.full(t10.shape, .6)
        ndvi = spectral_index("ndvi", nir=nir, red=red)
        for key in ("xiaolei-2014", "XIAOLEI-2014"):
            calls = (
                lambda: emissivity(ndvi, 10, emissivity_method=key),
                lambda: emissivity(ndvi, 11, emissivity_method=key),
                lambda: single_window(t10, red, nir, emissivity_method=key),
                lambda: split_window(t10, t10-2, red, nir,
                                     lst_method="du-2015", emissivity_method=key),
            )
            for index, call in enumerate(calls):
                with self.subTest(key=key, workflow=index):
                    with self.assertRaises(InvalidMethodRequested) as error:
                        call()
                    self.assertIn("not registered", str(error.exception))
                    self.assertIn("avdan-2016", str(error.exception))
                    self.assertIn("gopinadh-2018", str(error.exception))

    def test_remaining_emissivity_methods_do_not_require_a_red_band(self):
        n = np.array([[-.1, .1, .35, .6]])
        for method in ("avdan-2016", "gopinadh-2018"):
            for band in (10, 11):
                with self.subTest(method=method, band=band):
                    result = emissivity(n, band, emissivity_method=method)
                    self.assertTrue(np.isfinite(result).all())
                    self.assertTrue(((result > 0) & (result <= 1)).all())

    def test_ndvi_accepts_calibrated_radiance_and_cancels_common_scaling(self):
        nir, red = np.array([[20., 30.]]), np.array([[10., 20.]])
        actual = spectral_index("ndvi", nir=nir, red=red)
        np.testing.assert_allclose(actual, [[1/3, .2]], rtol=0, atol=1e-15)
        np.testing.assert_allclose(
            spectral_index("ndvi", nir=7*nir, red=7*red), actual,
            rtol=0, atol=1e-15)
        differently_scaled = spectral_index("ndvi", nir=2*nir, red=red)
        self.assertFalse(np.allclose(actual, differently_scaled))
