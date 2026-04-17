import unittest

from pylstemp.thermal import BrightnessTemperatureLandsat, brightness_temperature
from pylstemp.vegetation import ndvi


class TestDomains(unittest.TestCase):
    def test_vegetation_domain_exports_ndvi(self):
        self.assertTrue(callable(ndvi))

    def test_thermal_domain_exports_brightness_helpers(self):
        self.assertTrue(callable(brightness_temperature))
        self.assertTrue(callable(BrightnessTemperatureLandsat))
