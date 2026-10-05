"""Numerical references and compatibility matrix for every registered model.

Literal reference values are calculated independently of package helpers.
See docs/scientific-methods.md for source decisions and sensor limitations.
"""
import unittest
import warnings
import numpy as np
from pylstemp import brightness, emissivity, single_window, split_window, spectral_index, water_vapor, list_algorithms
from pylstemp.algorithms import FAMILY_REGISTRIES
from pylstemp.algorithms.split_window import split_window_registry
from pylstemp.algorithms.spectral_indices import spectral_indices_registry as legacy_registry

SPLIT = ("du-2015", "jimenez-munoz-2014", "kerr-1992", "price-1984", "sobrino-1993")
EMISSIVITY = ("avdan-2016", "gopinadh-2018")


class AllModelTests(unittest.TestCase):
    def setUp(self):
        self.a = np.full((4, 4), 300.)
        self.red, self.nir = self.a*0+0.2, self.a*0+0.6
        self.mask = np.zeros(self.a.shape, bool)
        self.mask[0, 0] = True

    def raw_split(self, key, bt10, bt11, e10, e11, ndvi, **extras):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return split_window_registry.create(key)(
                brightness_temperature_10=bt10, brightness_temperature_11=bt11,
                emissivity_10=e10, emissivity_11=e11, ndvi=ndvi,
                mask=np.zeros(bt10.shape, bool), **extras)

    def test_inventory_is_exhaustive(self):
        expected = {
            "emissivity": set(EMISSIVITY), "single_channel": {"mono-window-2016"},
            "spectral_index": {"ndvi", "evi"},
            "split_window": set(SPLIT), "thermal": {"brightness"},
            "water_vapor": {"wang-2015"}, "radiative_transfer": set(),
        }
        self.assertEqual({name:set(reg.available_keys()) for name,reg in FAMILY_REGISTRIES.items()}, expected)

    def test_price_independent_reference_vector(self):
        result = self.raw_split("price-1984",
            np.array([[290., 300., 310.]]), np.array([[289., 298., 307.]]),
            np.array([[.96, .98, .99]]), np.array([[.97, .97, .985]]), self.a[:1,:3])
        np.testing.assert_allclose(result, [[293.76987777777777,310.2579333333333,321.8523388888889]],rtol=0,atol=1e-10)

    def test_sobrino_independent_reference_vector(self):
        result = self.raw_split("sobrino-1993",
            np.array([[290.,300.,310.]]),np.array([[289.,298.,307.]]),
            np.array([[.96,.98,.99]]),np.array([[.97,.97,.985]]),self.a[:1,:3])
        np.testing.assert_allclose(result, [[294.17,304.49,317.585]],rtol=0,atol=1e-10)

    def test_kerr_soil_mixed_vegetation_references(self):
        result = self.raw_split("kerr-1992",
            np.array([[290.,300.,310.]]),np.array([[289.,298.,307.]]),
            np.ones((1,3)),np.ones((1,3)),np.array([[.11,.415,.72]]))
        np.testing.assert_allclose(result,[[295.2,305.05,315.4]],rtol=0,atol=1e-10)

    def test_du_every_coefficient_interval(self):
        pairs = [(1.,304.95174982905985),(2.75,305.2487552136752),
                 (3.75,305.3557011111111),(4.75,305.2883239250493),
                 (6.,304.58131996055226),(None,305.08098600262986)]
        for pwv,expected in pairs:
            with self.subTest(pwv=pwv):
                result=self.raw_split("du-2015",self.a,self.a-2,self.a*0+.98,self.a*0+.97,
                                      self.a*0+.35,water_vapor=pwv)
                np.testing.assert_allclose(result,expected,rtol=0,atol=1e-10)

    def test_all_split_unit_emissivity_equal_bands_identity(self):
        for key in SPLIT:
            with self.subTest(method=key):
                result=self.raw_split(key,self.a,self.a,self.a*0+1,self.a*0+1,self.a*0+.35,water_vapor=2.)
                # Du has regression intercept/slope, Jimenez a constant offset.
                expected=300.218575 if key=="du-2015" else 299.732 if key=="jimenez-munoz-2014" else 300.9360655737705 if key=="kerr-1992" else 300.
                np.testing.assert_allclose(result,expected,rtol=0,atol=1e-10)



    def test_avdan_class_boundaries_are_explicit(self):
        ndvi=np.array([[-.01,0,.19999,.2,.35,.5,.50001]])
        expected=[[.991,.966,.966,.971,.97275,.978,.973]]
        np.testing.assert_allclose(emissivity(ndvi,band="band_10",emissivity_method="avdan-2016"),expected,rtol=0,atol=1e-10)

    def test_gopinadh_endpoints_and_mixture_both_bands(self):
        ndvi=np.array([[-.1,.15,.315,.48,.9]])
        for band,expected in ((10,[[.971,.971,.979,.987,.987]]),(11,[[.977,.977,.983,.989,.989]])):
            result=emissivity(ndvi,band=f"band_{band}",emissivity_method="gopinadh-2018")
            np.testing.assert_allclose(result,expected,rtol=0,atol=1e-12)

    def test_every_emissivity_propagates_invalid_ndvi(self):
        ndvi=np.array([[np.nan,np.inf,-2,2,.35]])
        for key in EMISSIVITY:
            for band in (10,11):
                with self.subTest(method=key,band=band):
                    result=emissivity(ndvi,band=f"band_{band}",band_4_red=np.full(ndvi.shape,.2),emissivity_method=key)
                    self.assertTrue(np.isnan(result[0,:4]).all())
                    self.assertTrue(np.isfinite(result[0,4]))

    def test_all_single_channel_emissivity_combinations(self):
        for method in EMISSIVITY:
            with self.subTest(method=method):
                result=single_window(self.a,self.red,self.nir,emissivity_method=method,mask=self.mask)
                self.assertTrue(np.isnan(result[self.mask]).all())
                self.assertTrue(np.isfinite(result[~self.mask]).all())

    def test_all_supported_split_emissivity_combinations(self):
        for key in SPLIT:
            for method in ("gopinadh-2018",):
                with self.subTest(lst=key,emissivity=method),warnings.catch_warnings():
                    warnings.simplefilter("ignore",RuntimeWarning)
                    result=split_window(self.a,self.a-2,self.red,self.nir,lst_method=key,
                        emissivity_method=method,water_vapor=2.,mask=self.mask)
                    self.assertTrue(np.isnan(result[self.mask]).all())
                    self.assertTrue(np.isfinite(result[~self.mask]).all())

    def test_every_split_masks_nonfinite_bands(self):
        bad=self.a.copy();bad[0,0]=np.inf;bad[0,1]=np.nan
        for key in SPLIT:
            with self.subTest(method=key),warnings.catch_warnings(),np.errstate(invalid="ignore"):
                warnings.simplefilter("ignore",RuntimeWarning)
                result=split_window(self.a,bad,self.red,self.nir,lst_method=key,water_vapor=2.)
                self.assertTrue(np.isnan(result[0,:2]).all())
                self.assertFalse(np.isinf(result).any())

    def test_brightness_four_sensor_band_reference_values(self):
        references=(("landsat_8",10,278.3055634071797),("landsat_8",11,280.964358282595),
                    ("landsat_9",10,285.7496039316584),("landsat_9",11,283.8210641402533))
        for sensor,band,expected in references:
            with self.subTest(sensor=sensor,band=band):
                result=brightness(np.full((1,1),20000.),band=f"band_{band}",sensor=sensor)
                self.assertAlmostEqual(float(result[0,0]),expected,places=10)

    def test_spectral_indices_and_legacy_numeric_references(self):
        nir=np.array([[.6,.8]]);red=np.array([[.2,.4]]);blue=np.array([[.1,.2]])
        np.testing.assert_allclose(spectral_index("ndvi",nir=nir,red=red),[[.5,1/3]],atol=1e-14)
        np.testing.assert_allclose(legacy_registry.create("ndvi")(band_5_nir=nir,band_4_red=red),[[.5,1/3]],atol=1e-14)
        np.testing.assert_allclose(spectral_index("evi",nir=nir,red=red,blue=blue),[[20/41,10/27]],atol=1e-14)

    def test_wang_low_transmittance_reference(self):
        x=np.arange(100,dtype=float).reshape(10,10)+290
        y=.8*x+50
        result=water_vapor(x,y,np.full(x.shape,.35),window_size=5)
        np.testing.assert_allclose(result,3.480489429442706,rtol=0,atol=1e-9)


    def test_wang_high_transmittance_reference(self):
        x=np.arange(100,dtype=float).reshape(10,10)+290
        y=.95*x+10
        result=water_vapor(x,y,np.full(x.shape,.35),window_size=5)
        np.testing.assert_allclose(result,1.1931535516263383,rtol=0,atol=1e-9)

    def test_hot_surfaces_survive_every_temperature_model(self):
        hot=self.a+50
        result=single_window(hot,self.red,self.nir,mask=self.mask)
        self.assertTrue(np.isfinite(result[~self.mask]).all())
        self.assertTrue(np.all(result[~self.mask]>329.85))
        for key in SPLIT:
            with self.subTest(method=key),warnings.catch_warnings():
                warnings.simplefilter("ignore",RuntimeWarning)
                result=split_window(hot,hot-2,self.red,self.nir,lst_method=key,
                                    water_vapor=2.,mask=self.mask)
                self.assertTrue(np.isfinite(result[~self.mask]).all())
                self.assertTrue(np.all(result[~self.mask]>329.85))
