import unittest

from pylstemp.algorithms.thermal import (
    BrightnessTemperatureLandsat,
    brightness_band_10,
    brightness_band_11,
)
from pylstemp.algorithms.spectral_index import EVIAlgorithm, NDVIAlgorithm, evi, ndvi


class TestDomains(unittest.TestCase):
    def test_spectral_index_family_exports_indices(self):
        self.assertTrue(callable(evi))
        self.assertTrue(callable(ndvi))
        self.assertTrue(callable(EVIAlgorithm))
        self.assertTrue(callable(NDVIAlgorithm))

    def test_thermal_family_exports_brightness_helpers(self):
        self.assertTrue(callable(brightness_band_10))
        self.assertTrue(callable(brightness_band_11))
        self.assertTrue(callable(BrightnessTemperatureLandsat))
