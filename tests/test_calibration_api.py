"""Calibration dispatch: independent equations, masks and input contracts."""
import unittest
import numpy as np
from pylstemp import calibrate, brightness, toa_radiance, toa_reflectance
from pylstemp.calibration import brightness_from_mtl, surface_reflectance
from pylstemp.calibration.quality import _quality_mask_from_arrays
from pylstemp.exceptions import InvalidMethodRequested


class CalibrationAPI(unittest.TestCase):
    def metadata(self):
        return dict(SPACECRAFT_ID="LANDSAT_8", PROCESSING_LEVEL="L1TP",
                    RADIANCE_MULT_BAND_10=.01, RADIANCE_ADD_BAND_10=.1,
                    REFLECTANCE_MULT_BAND_4=.0001, REFLECTANCE_ADD_BAND_4=-.1,
                    K1_CONSTANT_BAND_10=774.8853, K2_CONSTANT_BAND_10=1321.0789,
                    SUN_ELEVATION=30.)

    def test_radiance_and_reflectance_equations_with_qa_mask(self):
        dn=np.array([1000.,2000.,0.]); mask=np.array([False,True,False])
        m=self.metadata()
        radiance=calibrate(dn, method="toa-radiance", metadata=m, band=10, mask=mask)
        reflectance=calibrate(dn, method="toa-reflectance", metadata=m, band=4, mask=mask,
                              sun_elevation=90.)
        np.testing.assert_allclose(radiance,[10.1,np.nan,np.nan],equal_nan=True)
        np.testing.assert_allclose(reflectance,[0.,np.nan,np.nan],atol=1e-15,equal_nan=True)
        np.testing.assert_array_equal(radiance,toa_radiance(dn,metadata=m,band=10,mask=mask))
        np.testing.assert_array_equal(reflectance,toa_reflectance(dn,metadata=m,band=4,mask=mask,sun_elevation=90.))

    def test_brightness_radiance_and_explicit_dn_routes(self):
        m=self.metadata();dn=np.array([1000.,2000.]);radiance=.01*dn+.1
        expected=1321.0789/np.log1p(774.8853/radiance)
        for data,kw in ((radiance,{}),(dn,{"input_quantity":"dn"})):
            with self.subTest(quantity=kw):
                result=calibrate(data,method="brightness",band=10,metadata=m,**kw)
                np.testing.assert_allclose(result,expected)
                np.testing.assert_array_equal(result,brightness(data,band=10,metadata=m,**kw))
        np.testing.assert_allclose(brightness_from_mtl(dn,metadata=m,band=10),expected)

    def test_selector_is_required_and_unknown_values_are_rejected(self):
        with self.assertRaises(TypeError):calibrate([1.])
        for method in (None,[],"unknown","surface-reflectance"):
            with self.subTest(method=method),self.assertRaises(InvalidMethodRequested):
                calibrate([1.],method=method)

    def test_wrong_method_arguments_and_quantities_are_rejected(self):
        with self.assertRaises(TypeError):
            calibrate([1.],method="toa-radiance",metadata=self.metadata(),band=10,sun_elevation=45.)
        with self.assertRaises(ValueError):
            calibrate([10.],method="brightness",metadata=self.metadata(),band=10,rad_gain=.01)
        m=self.metadata();m['PROCESSING_LEVEL']='L2SP'
        with self.assertRaises(ValueError):calibrate([1.],method="toa-reflectance",metadata=m,band=4)

    def test_auxiliary_imports_survive_package_migration(self):
        np.testing.assert_allclose(surface_reflectance([10000.]),[.075])
        np.testing.assert_array_equal(_quality_mask_from_arrays(np.array([0,8],dtype='uint16')),[False,True])
