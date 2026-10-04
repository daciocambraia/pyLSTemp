"""Independent calibration, physical-domain and optimization checks."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from pylstemp import brightness, single_window, split_window, water_vapor
from pylstemp.calibration import read_mtl, toa_reflectance, brightness_from_mtl, quality_mask, surface_reflectance
from pylstemp.algorithms.water_vapor.wang_2015 import WaterVaporWang2015
from pylstemp.registry import AlgorithmRegistry
from pylstemp.metadata import AlgorithmSpec


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.m = dict(PROCESSING_LEVEL="L1TP", SPACECRAFT_ID="LANDSAT_8", SUN_ELEVATION=30,
            REFLECTANCE_MULT_BAND_4=2e-5, REFLECTANCE_ADD_BAND_4=-0.1,
            RADIANCE_MULT_BAND_10=0.0003342, RADIANCE_ADD_BAND_10=0.1,
            K1_CONSTANT_BAND_10=774.8853, K2_CONSTANT_BAND_10=1321.0789)

    def test_toa_numeric_oracle_and_fill(self):
        actual = toa_reflectance([[20000, 0]], metadata=self.m, band=4)
        np.testing.assert_allclose(actual, [[0.6, np.nan]], atol=1e-14)

    def test_per_pixel_sun_angle_and_mask(self):
        actual = toa_reflectance([[20000, 20000]], metadata=self.m, band=4,
            sun_elevation=[[30, 90]], mask=np.array([[False, True]]))
        np.testing.assert_allclose(actual, [[0.6, np.nan]], atol=1e-14)

    def test_thermal_numeric_oracle(self):
        actual = brightness_from_mtl([[20000, 0]], metadata=self.m, band=10)
        expected = 1321.0789 / np.log1p(774.8853/(20000*0.0003342+0.1))
        np.testing.assert_allclose(actual, [[expected, np.nan]])

    def test_mtl_overrides_landsat_nine_default_band_eleven(self):
        m = dict(self.m, SPACECRAFT_ID="LANDSAT_9",
            RADIANCE_MULT_BAND_11=0.000349, RADIANCE_ADD_BAND_11=0.1,
            K1_CONSTANT_BAND_11=475.6581, K2_CONSTANT_BAND_11=1198.3494)
        result=brightness_from_mtl([[20000]], metadata=m, band=11)
        expected=1198.3494/np.log1p(475.6581/(20000*0.000349+0.1))
        self.assertAlmostEqual(float(result[0,0]),expected,places=10)

    def test_zero_dn_is_nodata_without_explicit_mask(self):
        self.assertTrue(np.isnan(brightness([[0]],band="band_10",sensor="landsat_8")).all())

    def test_qa_bits_match_usgs_table(self):
        qa=np.array([[0]+[1<<i for i in range(8)]],dtype=np.uint16)
        np.testing.assert_array_equal(quality_mask(qa),[[False,True,True,True,True,True,True,False,False]])
        np.testing.assert_array_equal(quality_mask(qa,exclude_water=True),[[False,True,True,True,True,True,True,False,True]])

    def test_saturation_and_terrain(self):
        sat=np.array([[0,2,8,16,2048,4]],dtype=np.uint16)
        np.testing.assert_array_equal(quality_mask(np.zeros_like(sat),sat),[[False,True,True,True,True,False]])

    def test_sr_is_scaling_not_atmospheric_correction(self):
        np.testing.assert_allclose(surface_reflectance([[10000,0]]),[[0.075,np.nan]])

    def test_reject_bad_solar_angle_and_level(self):
        for angle in (0,-1,91,np.inf):
            with self.assertRaises(ValueError):
                toa_reflectance([[10000]],metadata=self.m,band=4,sun_elevation=angle)
        with self.assertRaises(ValueError):
            toa_reflectance([[10000]],metadata=dict(self.m,PROCESSING_LEVEL="L2SP"),band=4)

    def test_mtl_parser(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"MTL.txt"
            path.write_text('GROUP = DATA\n SPACECRAFT_ID = "LANDSAT_9"\n SUN_ELEVATION = 5.988E1\n END_GROUP = DATA\n')
            m=read_mtl(path)
            self.assertEqual(m["SPACECRAFT_ID"],"LANDSAT_9")
            self.assertAlmostEqual(m["SUN_ELEVATION"],59.88)

    def test_negative_scalar_pwv_rejected(self):
        a=np.full((1,1),300.)
        with self.assertRaises(ValueError):
            split_window(a,a-2,a*0+0.2,a*0+0.6,lst_method="jimenez-munoz-2014",water_vapor=-1)

    def test_user_mask_propagates_through_both_workflows(self):
        a=np.full((2,2),300.); mask=np.array([[True,False],[False,False]])
        for output in (single_window(a,a*0+0.2,a*0+0.6,mask=mask),
                       split_window(a,a-2,a*0+0.2,a*0+0.6,lst_method="du-2015",mask=mask)):
            self.assertTrue(np.isnan(output[0,0]))
            self.assertTrue(np.isfinite(output[~mask]).all())


class WangOptimizationTests(unittest.TestCase):
    def test_vectorization_matches_scalar_windows_and_chunks(self):
        rng=np.random.default_rng(421)
        x=295+rng.normal(0,6,(17,19)); y=0.8*x+50+rng.normal(0,0.2,x.shape)
        n=rng.uniform(-0.1,0.8,x.shape); x[2,3]=np.nan
        algorithm=WaterVaporWang2015()
        edges=algorithm._ndvi_group_edges(float(n[np.isfinite(x)].min()),float(n[np.isfinite(x)].max()),3)
        expected=np.full(x.shape,np.nan)
        for r in range(x.shape[0]):
            for c in range(x.shape[1]):
                if not np.isfinite(x[r,c]): continue
                selection=np.s_[max(0,r-2):r+3,max(0,c-2):c+3]
                expected[r,c]=algorithm._window_water_vapor(x[selection],y[selection],n[selection],ndvi_edges=edges)
        for chunk in (1,8,30):
            actual=algorithm(brightness_band_10=x,brightness_band_11=y,ndvi_image=n,window_size=5,chunk_rows=chunk)
            np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-10,equal_nan=True)

    def test_central_nodata_never_filled_implicitly(self):
        x=np.arange(100,dtype=float).reshape(10,10)+290
        y=0.8*x+50; x[5,5]=np.nan
        actual=water_vapor(x,y,np.full(x.shape,0.35),window_size=5)
        self.assertTrue(np.isnan(actual[5,5]))

    def test_integer_and_dimensions_validation(self):
        a=np.full((3,3),300.)
        for name,value in (("window_size",3.0),("group_count",True),("chunk_rows",0)):
            with self.assertRaises(ValueError):
                water_vapor(a,a-2,a*0+0.35,**{name:value})
        with self.assertRaises(ValueError):
            water_vapor(a.ravel(),a.ravel(),a.ravel())

    def test_registry_collision_is_atomic(self):
        reg=AlgorithmRegistry("test")
        spec=AlgorithmSpec("a",object,"A","test","test",("alias",))
        reg.register(spec)
        with self.assertRaises(ValueError):
            reg.register(AlgorithmSpec("b",object,"B","test","test",("alias",)))
        self.assertEqual(reg.available_keys(),("a",))
