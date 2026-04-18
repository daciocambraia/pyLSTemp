import unittest

import numpy as np

from pylstemp.api import emissivity_band_10, ndvi
from pylstemp.validation import build_mask_from, normalize_temperature_unit
from pylstemp.exceptions import InvalidMaskError


class TestValidation(unittest.TestCase):
    def test_ndvi_rejects_non_boolean_mask(self):
        with self.assertRaises(InvalidMaskError):
            ndvi(np.ones((2, 2)), np.ones((2, 2)), mask=np.ones((2, 2), dtype=int))

    def test_xiaolei_requires_red_band(self):
        with self.assertRaises(ValueError):
            emissivity_band_10(np.ones((2, 2)), emissivity_method="xiaolei")

    def test_mask_builder_marks_zero_and_nan(self):
        image = np.array([[1.0, 0.0], [np.nan, 2.0]])
        mask = build_mask_from(image)
        self.assertTrue(mask[0, 1])
        self.assertTrue(mask[1, 0])

    def test_temperature_unit_normalization_preserves_legacy_spelling(self):
        self.assertEqual(normalize_temperature_unit("celcius"), "celsius")
