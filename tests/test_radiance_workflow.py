"""Independent USGS calibration oracles and physical-quantity contracts."""
import unittest
import numpy as np
from pylstemp import brightness, toa_radiance, toa_reflectance, spectral_index
from pylstemp.calibration import brightness as calibration_brightness, brightness_from_mtl
from pylstemp.exceptions import InvalidMaskError

class RadianceWorkflow(unittest.TestCase):
    def setUp(self):
        self.m=dict(PROCESSING_LEVEL="L1TP",SPACECRAFT_ID="LANDSAT_8",SUN_ELEVATION=30,
            RADIANCE_MULT_BAND_4=.007,RADIANCE_ADD_BAND_4=-35,
            RADIANCE_MULT_BAND_5=.005,RADIANCE_ADD_BAND_5=-25,
            REFLECTANCE_MULT_BAND_4=.00002,REFLECTANCE_ADD_BAND_4=-.1,
            REFLECTANCE_MULT_BAND_5=.00002,REFLECTANCE_ADD_BAND_5=-.1,
            RADIANCE_MULT_BAND_10=.0003342,RADIANCE_ADD_BAND_10=.1,
            RADIANCE_MULT_BAND_11=.0003342,RADIANCE_ADD_BAND_11=.1,
            K1_CONSTANT_BAND_10=774.8853,K2_CONSTANT_BAND_10=1321.0789,
            K1_CONSTANT_BAND_11=480.8883,K2_CONSTANT_BAND_11=1201.1442)

    def test_radiance_numeric_oracle_and_masks(self):
        dn=np.array([[20000.,0.,-1.,np.inf,np.nan,30000.]])
        old=dn.copy();mask=np.array([[False,False,False,False,False,True]])
        np.testing.assert_allclose(toa_radiance(dn,metadata=self.m,band=4,mask=mask),
            [[105.,np.nan,np.nan,np.nan,np.nan,np.nan]],equal_nan=True)
        np.testing.assert_array_equal(dn,old)
        self.assertEqual(float(toa_radiance(20000.,metadata=self.m,band=4)),105.)

    def test_usgs_planck_oracle_both_bands_both_sensors_and_dn_equivalence(self):
        for spacecraft,pairs in (("LANDSAT_8",((774.8853,1321.0789),(480.8883,1201.1442))),
                                 ("LANDSAT_9",((799.0284,1329.2405),(475.6581,1198.3494)))):
            for band,(k1,k2) in zip((10,11),pairs):
                m=dict(self.m,SPACECRAFT_ID=spacecraft)
                m[f"K1_CONSTANT_BAND_{band}"]=k1;m[f"K2_CONSTANT_BAND_{band}"]=k2
                m[f"RADIANCE_MULT_BAND_{band}"]=.0003;m[f"RADIANCE_ADD_BAND_{band}"]=.2
                dn=np.array([[20000.,0.,30000.]])
                radiance=toa_radiance(dn,metadata=m,band=band)
                expected=k2/np.log1p(k1/np.array([[6.2,np.nan,9.2]]))
                with self.subTest(sensor=spacecraft,band=band):
                    np.testing.assert_allclose(brightness(radiance,band,metadata=m),expected,rtol=0,atol=1e-12)
                    np.testing.assert_allclose(brightness(dn,band,metadata=m,input_quantity="dn"),expected,rtol=0,atol=1e-12)
                    np.testing.assert_array_equal(brightness_from_mtl(dn,metadata=m,band=band),brightness(radiance,band,metadata=m))

    def test_brightness_default_radiance_and_shared_public_function(self):
        self.assertIs(brightness,calibration_brightness)
        self.assertAlmostEqual(float(brightness(10.,10,"landsat_8")),1321.0789/np.log1p(774.8853/10.),places=12)
        self.assertFalse(np.allclose(brightness([[20000.]],10,"landsat_8"),
            brightness([[20000.]],10,"landsat_8",input_quantity="dn")))

    def test_double_calibration_conflicts_are_rejected(self):
        for kwargs in (dict(rad_gain=.0003),dict(rad_bias=.1),dict(input_quantity="reflectance"),
                       dict(metadata=self.m,sensor="landsat_9"),
                       dict(metadata=self.m,input_quantity="dn",rad_gain=.0003)):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                options=dict(sensor="landsat_8",**{k:v for k,v in kwargs.items() if k!="sensor"})
                if "sensor" in kwargs:options["sensor"]=kwargs["sensor"]
                brightness([[10.]],10,**options)

    def test_invalid_radiance_k_constants_and_mask(self):
        np.testing.assert_allclose(brightness([[0.,-1.,np.nan,np.inf,10.]],10,"landsat_8"),
            [[np.nan,np.nan,np.nan,np.nan,1321.0789/np.log1p(774.8853/10.)]],equal_nan=True)
        for bad in (0,-1,np.inf,np.nan):
            with self.assertRaises(ValueError):brightness([[10.]],10,metadata=dict(self.m,K1_CONSTANT_BAND_10=bad))
        with self.assertRaises(InvalidMaskError):brightness([[10.]],10,"landsat_8",mask=[[1]])

    def test_invalid_metadata_bands_coefficients_and_level(self):
        for band in (0,12,True,4.0,"4"):
            with self.assertRaises(ValueError):toa_radiance([[20000.]],metadata=self.m,band=band)
        for m in (None,{},dict(self.m,PROCESSING_LEVEL="L2SP"),dict(self.m,RADIANCE_MULT_BAND_4=0),
                  dict(self.m,RADIANCE_MULT_BAND_4=np.nan),dict(self.m,RADIANCE_ADD_BAND_4=np.inf)):
            with self.assertRaises(ValueError):toa_radiance([[20000.]],metadata=m,band=4)

    def test_radiance_and_reflectance_ndvi_are_distinct(self):
        red=toa_radiance([[20000.]],metadata=self.m,band=4)
        nir=toa_radiance([[30000.]],metadata=self.m,band=5)
        self.assertAlmostEqual(spectral_index("ndvi",nir=nir,red=red).item(),20/230)
        red_r=toa_reflectance([[20000.]],metadata=self.m,band=4)
        nir_r=toa_reflectance([[30000.]],metadata=self.m,band=5)
        self.assertAlmostEqual(spectral_index("ndvi",nir=nir_r,red=red_r).item(),.25)
