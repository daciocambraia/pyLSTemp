import unittest

import numpy as np

from pylstemp import brightness_temperature, emissivity, ndvi, single_window, split_window


class TestPublicApi(unittest.TestCase):
    def setUp(self):
        # Small deterministic inputs make the formulas easy to validate in tests.
        self.band_10 = np.full((4, 4), 1000.0)
        self.band_11 = np.full((4, 4), 900.0)
        self.band_4 = np.full((4, 4), 0.2)
        self.band_5 = np.full((4, 4), 0.6)

    def test_ndvi_returns_expected_shape(self):
        output = ndvi(self.band_5, self.band_4)
        self.assertEqual(output.shape, self.band_5.shape)

    def test_brightness_temperature_returns_tuple(self):
        brightness_10, brightness_11 = brightness_temperature(self.band_10, self.band_11)
        self.assertEqual(brightness_10.shape, self.band_10.shape)
        self.assertEqual(brightness_11.shape, self.band_11.shape)

    def test_emissivity_returns_both_bands(self):
        ndvi_image = ndvi(self.band_5, self.band_4)
        emissivity_10, emissivity_11 = emissivity(ndvi_image, self.band_4, emissivity_method="avdan")
        self.assertEqual(emissivity_10.shape, ndvi_image.shape)
        self.assertEqual(emissivity_11.shape, ndvi_image.shape)

    def test_single_window_preserves_shape(self):
        output = single_window(self.band_10, self.band_4, self.band_5)
        self.assertEqual(output.shape, self.band_10.shape)

    def test_split_window_preserves_shape(self):
        output = split_window(
            self.band_10,
            self.band_11,
            self.band_4,
            self.band_5,
            lst_method="jiminez-munoz",
            emissivity_method="avdan",
        )
        self.assertEqual(output.shape, self.band_10.shape)
