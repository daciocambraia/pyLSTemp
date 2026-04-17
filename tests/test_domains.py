import unittest

from pylstemp.algorithms.thermal import BrightnessTemperatureLandsat, brightness_temperature
from pylstemp.algorithms.vegetation import NDVIAlgorithm, ndvi


class TestDomains(unittest.TestCase):
    def test_vegetation_family_exports_ndvi(self):
        self.assertTrue(callable(ndvi))
        self.assertTrue(callable(NDVIAlgorithm))

    def test_thermal_family_exports_brightness_helpers(self):
        self.assertTrue(callable(brightness_temperature))
        self.assertTrue(callable(BrightnessTemperatureLandsat))
