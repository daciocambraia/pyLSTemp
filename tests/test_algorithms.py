import unittest

import numpy as np

from pylstemp.algorithms.emissivity import ComputeEmissivityAvdan2016
from pylstemp.algorithms.single_channel import BaseTemperatureAlgorithm, MonoWindow2016LST
from pylstemp.algorithms.split_window import (
    SplitWindowDu2015LST,
    SplitWindowKerr1992LST,
    SplitWindowPrice1984LST,
    SplitWindowSobrino1993LST,
)


class TestAlgorithms(unittest.TestCase):
    def setUp(self):
        self.base = np.full((3, 3), 300.0)
        self.mask = np.zeros((3, 3), dtype=bool)

    def test_mono_window_algorithm_shape(self):
        output = MonoWindow2016LST()(
            emissivity_10=np.full((3, 3), 0.98),
            brightness_temperature_10=self.base,
            mask=self.mask,
        )
        self.assertEqual(output.shape, self.base.shape)

    def test_mono_window_uses_landsat_band_10_midpoint_wavelength(self):
        self.assertEqual(MonoWindow2016LST.wavelength_band_10, 10.895e-6)

    def test_avdan_2016_emissivity_matches_article_ndvi_rules(self):
        ndvi = np.array([[-0.1, 0.1, 0.35, 0.6]])
        emissivity_10, emissivity_11 = ComputeEmissivityAvdan2016()(ndvi=ndvi)
        mixed_fvc = ((0.35 - 0.2) / (0.5 - 0.2)) ** 2
        expected_mixed = (0.973 * mixed_fvc) + (0.996 * (1 - mixed_fvc)) + 0.005
        expected = np.array([[0.991, 0.996, expected_mixed, 0.973]])

        self.assertTrue(np.allclose(emissivity_10, expected))
        self.assertTrue(np.allclose(emissivity_11, expected))

    def test_split_window_algorithms_shape(self):
        emissivity = np.full((3, 3), 0.98)
        ndvi = np.full((3, 3), 0.4)

        algorithms = [
            SplitWindowDu2015LST()(
                emissivity_10=emissivity,
                emissivity_11=emissivity,
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                mask=self.mask,
            ),
            SplitWindowKerr1992LST()(
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                ndvi=ndvi,
                mask=self.mask,
            ),
            SplitWindowPrice1984LST()(
                emissivity_10=emissivity,
                emissivity_11=emissivity,
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                mask=self.mask,
            ),
            SplitWindowSobrino1993LST()(
                emissivity_10=emissivity,
                emissivity_11=emissivity,
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                mask=self.mask,
            ),
        ]

        for output in algorithms:
            self.assertEqual(output.shape, self.base.shape)

    def test_du_2015_uses_all_cwv_coefficients_by_default(self):
        output = SplitWindowDu2015LST()(
            emissivity_10=np.full((3, 3), 0.98),
            emissivity_11=np.full((3, 3), 0.98),
            brightness_temperature_10=self.base,
            brightness_temperature_11=self.base - 2,
            mask=self.mask,
        )
        expected = (
            -0.41165
            + (1.00522 + (0.14543 * ((1 - 0.98) / 0.98))) * 299
            + (4.06655 + (-6.92512 * ((1 - 0.98) / 0.98))) * 1
            + (0.24468 * 4)
        )
        self.assertTrue(np.allclose(output, expected))

    def test_du_2015_selects_coefficients_from_water_vapor(self):
        default_output = SplitWindowDu2015LST()(
            emissivity_10=np.full((3, 3), 0.98),
            emissivity_11=np.full((3, 3), 0.98),
            brightness_temperature_10=self.base,
            brightness_temperature_11=self.base - 2,
            mask=self.mask,
        )
        cwv_output = SplitWindowDu2015LST()(
            emissivity_10=np.full((3, 3), 0.98),
            emissivity_11=np.full((3, 3), 0.98),
            brightness_temperature_10=self.base,
            brightness_temperature_11=self.base - 2,
            mask=self.mask,
            water_vapor=3.8,
        )
        self.assertFalse(np.allclose(default_output, cwv_output))

    def test_du_2015_rejects_water_vapor_outside_article_range(self):
        with self.assertRaises(ValueError):
            SplitWindowDu2015LST()(
                emissivity_10=np.full((3, 3), 0.98),
                emissivity_11=np.full((3, 3), 0.98),
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                mask=self.mask,
                water_vapor=7.0,
            )

    def test_kerr_1992_interpolates_article_coefficients(self):
        ndvi = np.full((3, 3), 0.72)
        output = SplitWindowKerr1992LST()(
            brightness_temperature_10=self.base,
            brightness_temperature_11=self.base - 2,
            ndvi=ndvi,
            mask=self.mask,
        )
        expected = (self.base * 3.6) + ((self.base - 2) * -2.6) - 2.4
        self.assertTrue(np.allclose(output, expected))

    def test_kerr_1992_uses_begue_ndvi_cover_values(self):
        self.assertEqual(SplitWindowKerr1992LST.ndvi_bare_soil, 0.11)
        self.assertEqual(SplitWindowKerr1992LST.ndvi_vegetation, 0.72)

    def test_base_temperature_algorithm_is_public(self):
        self.assertTrue(callable(BaseTemperatureAlgorithm))
