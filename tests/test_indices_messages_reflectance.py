"""Regressions for index corrections, one NDVI and actionable method errors."""
import unittest,warnings
import numpy as np
from pylstemp import spectral_index,brightness,emissivity,single_window,split_window,water_vapor,toa_reflectance,list_algorithms
from pylstemp.algorithms import FAMILY_REGISTRIES
from pylstemp.algorithms.spectral_index import spectral_index_registry
from pylstemp.algorithms.spectral_indices import spectral_indices_registry
from pylstemp.algorithms.spectral_indices.ndvi import ndvi as legacy_ndvi
from pylstemp.exceptions import InvalidMaskError,InvalidTemperatureUnitError,InvalidMethodRequested,InputShapesNotEqual
from pylstemp.utils import compute_ndvi
from pylstemp.calibration import surface_reflectance

class IndexCorrections(unittest.TestCase):
    def test_ndvi_zero_and_near_zero_denominators_are_invalid(self):
        nir=np.array([[0.,1e-17,-1e-17,.6]])
        red=np.array([[0.,1e-17,1e-17,.2]])
        actual=spectral_index("ndvi",nir=nir,red=red)
        self.assertTrue(np.isnan(actual[0,:3]).all())
        self.assertAlmostEqual(actual[0,3],.5)

    def test_ndvi_exact_ratio_without_denominator_bias(self):
        # Denominator 1e-12 exceeds the tolerance: result must remain exactly 1.
        self.assertEqual(float(spectral_index("ndvi",nir=np.array([[1e-12]]),red=np.array([[0.]]))[0,0]),1.)
        for eps in (-1,np.inf,np.nan):
            with self.assertRaisesRegex(ValueError,"tolerance"):compute_ndvi([[.6]],[[.2]],eps=eps)

    def test_all_nonfinite_index_inputs_propagate(self):
        for name in ("ndvi",):
            for band in ("nir","red"):
                for bad in (np.nan,np.inf,-np.inf):
                    data=dict(nir=np.array([[.6]]),red=np.array([[.2]]))
                    data[band][0,0]=bad
                    with self.subTest(index=name,band=band,value=bad):
                        self.assertTrue(np.isnan(spectral_index(name,**data)).all())


    def test_scalar_and_vector_shapes_are_supported(self):
        self.assertEqual(spectral_index("ndvi",nir=.6,red=.2).shape,())
        self.assertAlmostEqual(float(spectral_index("ndvi",nir=.6,red=.2)),.5)
        np.testing.assert_allclose(spectral_index("ndvi",nir=[.6,.8],red=[.2,.4]),[.5,1/3])

    def test_inputs_not_mutated(self):
        a=np.array([[.6,np.inf]]);b=np.array([[.2,.1]]);old=a.copy()
        spectral_index("ndvi",nir=a,red=b)
        np.testing.assert_array_equal(a,old)

class CanonicalAndMessages(unittest.TestCase):
    def setUp(self):
        self.t=np.full((3,3),300.);self.red=self.t*0+.2;self.nir=self.t*0+.6

    def test_catalog_has_one_ndvi_and_legacy_shares_implementation(self):
        catalog=list_algorithms()
        self.assertNotIn("spectral_indices",catalog)
        self.assertNotIn("spectral_indices",FAMILY_REGISTRIES)
        self.assertEqual(sum("ndvi" in methods for family,methods in catalog.items() if family!="credit"),1)
        self.assertIs(spectral_indices_registry,spectral_index_registry)
        modern=spectral_index("ndvi",nir=self.nir,red=self.red)
        np.testing.assert_array_equal(legacy_ndvi(self.nir,self.red),modern)
        np.testing.assert_array_equal(spectral_indices_registry.create("ndvi")(
            band_5_nir=self.nir,band_4_red=self.red),modern)

    def test_metadata_describes_every_method(self):
        for family,methods in list_algorithms().items():
            if family=="credit":continue
            for name,metadata in methods.items():
                with self.subTest(family=family,method=name):
                    self.assertTrue(metadata["input_requirements"])
                    self.assertTrue(metadata["water_vapor_support"])

    def test_actionable_errors_cover_all_public_workflows(self):
        cases=[
          (lambda:spectral_index("ndvi",nir=self.nir,red=self.red[:1]),InputShapesNotEqual,"spectral_index"),
          (lambda:brightness(self.t,12,"landsat_8", input_quantity="dn"),ValueError,"band must be"),
          (lambda:emissivity(self.red,12,emissivity_method="gopinadh-2018"),ValueError,"band must be"),
          (lambda:single_window(self.t,self.red,self.nir,mask=np.zeros(self.t.shape,int)),InvalidMaskError,"single_window"),
          (lambda:split_window(self.t,self.t-2,self.red,self.nir,lst_method="du-2015",water_vapor=np.full((1,1),2.)),InputShapesNotEqual,"same shape"),
          (lambda:water_vapor(self.t,self.t-2,self.red,window_size=20),ValueError,"water_vapor")]
        for call,error,phrase in cases:
            with self.subTest(phrase=phrase),self.assertRaisesRegex(error,phrase):call()

    def test_missing_and_nonnumeric_inputs_are_clear(self):
        with self.assertRaisesRegex(TypeError,"spectral_index"):spectral_index()
        with self.assertRaisesRegex(ValueError,"nir.*None"):spectral_index("ndvi",nir=None,red=self.red)
        with self.assertRaisesRegex(ValueError,"nir.*numeric"):spectral_index("ndvi",nir=["bad"],red=[.2])

    def test_invalid_method_types_and_units_are_clear(self):
        for method in (None,[],123," "):
            with self.assertRaisesRegex(InvalidMethodRequested,"family"):spectral_index(method,nir=self.nir,red=self.red)
        with self.assertRaisesRegex(InvalidTemperatureUnitError,"kelvin"):single_window(self.t,self.red,self.nir,unit=None)

    def test_band_aliases_are_case_and_whitespace_insensitive(self):
        expected=brightness([[20000.]],10,"landsat_8", input_quantity="dn")
        for band in ("B10"," Band_10 "," b10 "):
            np.testing.assert_array_equal(brightness([[20000.]],band,"landsat_8", input_quantity="dn"),expected)
        with self.assertRaisesRegex(ValueError,"landsat_8"):brightness([[20000.]],10,None, input_quantity="dn")

    def test_unused_pwv_warns_for_all_legacy_methods(self):
        for method in ("price-1984","kerr-1992","sobrino-1993"):
            with warnings.catch_warnings(record=True) as messages:
                warnings.simplefilter("always")
                split_window(self.t,self.t-2,self.red,self.nir,lst_method=method,water_vapor=2.)
            self.assertTrue(any("will be ignored" in str(m.message) and method in str(m.message) for m in messages))

    def test_du_checks_pwv_type_and_range_before_conversion(self):
        for value in (-1,np.nan,np.inf,6.30001):
            with self.subTest(value=repr(value)),self.assertRaisesRegex(ValueError,"du-2015"):
                split_window(self.t,self.t-2,self.red,self.nir,lst_method="du-2015",water_vapor=value)

class ReflectanceInputs(unittest.TestCase):
    def setUp(self):
        self.l1=dict(PROCESSING_LEVEL="L1TP",SPACECRAFT_ID="LANDSAT_8",COLLECTION_NUMBER=2,
            SUN_ELEVATION=30,REFLECTANCE_MULT_BAND_4=.00002,REFLECTANCE_ADD_BAND_4=-.1)

    def test_level1_toa_matches_known_physical_value(self):
        np.testing.assert_allclose(toa_reflectance([[20000,0]],metadata=self.l1,band=4),[[.6,np.nan]],atol=1e-14)

    def test_level2_surface_scaling_and_qa_mask(self):
        m=np.array([[False,True,False]])
        np.testing.assert_allclose(surface_reflectance([[10000,20000,0]],mask=m),
            [[.075,np.nan,np.nan]],atol=1e-14)



    def test_surface_values_are_not_silently_clipped(self):
        value=surface_reflectance([[1,50000]])
        self.assertLess(value[0,0],0);self.assertGreater(value[0,1],1)

    def test_invalid_metadata_is_actionable(self):
        with self.assertRaisesRegex(ValueError,"MTL"):toa_reflectance([[20000]],metadata=None,band=4)
