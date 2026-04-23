import unittest

import numpy as np

from pylstemp.api import brightness, emissivity, spectral_index
from pylstemp.validation import build_mask_from, normalize_temperature_unit
from pylstemp.exceptions import InvalidMaskError


class TestValidation(unittest.TestCase):
    def test_ndvi_rejects_non_boolean_mask(self):
        with self.assertRaises(InvalidMaskError):
            spectral_index(
                index="ndvi",
                nir=np.ones((2, 2)),
                red=np.ones((2, 2)),
                mask=np.ones((2, 2), dtype=int),
            )

    def test_xiaolei_requires_red_band(self):
        with self.assertRaises(ValueError):
            emissivity(
                np.ones((2, 2)),
                band="band_10",
                emissivity_method="xiaolei-2014",
            )

    def test_brightness_rejects_unknown_band(self):
        with self.assertRaisesRegex(ValueError, "band must be"):
            brightness(np.ones((2, 2)), band="band_12", sensor="landsat_8")

    def test_mask_builder_marks_zero_and_nan(self):
        image = np.array([[1.0, 0.0], [np.nan, 2.0]])
        mask = build_mask_from(image)
        self.assertTrue(mask[0, 1])
        self.assertTrue(mask[1, 0])

    def test_temperature_unit_normalization_preserves_legacy_spelling(self):
        self.assertEqual(normalize_temperature_unit("celcius"), "celsius")
