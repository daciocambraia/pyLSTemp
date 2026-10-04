"""Independent regression requirements from the v1.10 audit."""
from pathlib import Path
import sys
import unittest

import numpy as np

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))

from pylstemp import emissivity, split_window
from pylstemp.algorithms.base_temperature import BaseTemperatureAlgorithm
from pylstemp.algorithms.single_channel.mono_window_2016 import MonoWindow2016LST
from pylstemp.algorithms.split_window.jimenez_munoz_2014 import SplitWindowJimenezMunoz2014LST
from pylstemp.algorithms.water_vapor.wang_2015 import WaterVaporWang2015


def image(value):
    return np.full((1, 1), value, dtype=float)


class IndependentRequirements(unittest.TestCase):
    def test_mono_window_uses_consistent_si_units(self):
        bt, epsilon = image(300), image(0.98)
        result = MonoWindow2016LST()(
            brightness_temperature_10=bt, emissivity_10=epsilon,
            mask=np.zeros(bt.shape, dtype=bool),
        )
        expected = bt / (1 + (10.895e-6 * bt / 0.01438) * np.log(epsilon))
        np.testing.assert_allclose(result, expected, rtol=0, atol=1e-8)

    def test_valid_hot_surface_is_preserved(self):
        result = BaseTemperatureAlgorithm()._finalize(
            image(340), mask=np.zeros((1, 1), dtype=bool),
        )
        self.assertEqual(float(result[0, 0]), 340)

    def test_xiaolei_accepts_physical_red_reflectance(self):
        result = emissivity(
            image(0.1), band="band_10", band_4_red=image(0.2),
            emissivity_method="xiaolei-2014",
        )
        self.assertAlmostEqual(float(result[0, 0]), 0.973 - 0.047 * 0.2, places=10)

    def test_avdan_emissivity_does_not_exceed_one(self):
        result = emissivity(image(0.2), band="band_10", emissivity_method="avdan-2016")
        self.assertLessEqual(float(result[0, 0]), 1.0)

    def test_split_window_rejects_avdan_case_insensitively(self):
        with self.assertRaises(ValueError):
            split_window(
                image(300), image(298), image(0.2), image(0.6),
                lst_method="du-2015", emissivity_method="AVDAN-2016",
            )

    def test_wang_averages_direct_and_inverse_regressions(self):
        rng = np.random.default_rng(42)
        x = np.linspace(295, 315, 100)
        y = 0.8 * x + rng.normal(0, 0.35, x.size)
        ndvi = np.full(x.shape, 0.35)
        dx, dy = x - x.mean(), y - y.mean()
        keep = (np.abs(dx) > np.abs(dy)) & (dx * dy >= 0)
        dx, dy = dx[keep], dy[keep]
        covariance = np.sum(dx * dy)
        forward = covariance / np.sum(dx ** 2)
        reverse = covariance / np.sum(dy ** 2)
        self.assertGreaterEqual(forward * reverse, 0.97)
        pv = ((0.35 - 0.2) / (0.5 - 0.2)) ** 2
        emissivity_ratio = (0.0195 * pv + 0.9688) / (0.0149 * pv + 0.9747)
        ratio = emissivity_ratio * (forward + 1 / reverse) / 2
        expected = -18.973 * ratio + 19.13 if ratio > 0.9 else -13.412 * ratio + 14.158
        actual, count = WaterVaporWang2015()._group_water_vapor(x, y, ndvi)
        self.assertEqual(count, int(keep.sum()))
        self.assertAlmostEqual(actual, expected, places=10)

    def test_jimenez_uses_table_one_coefficient(self):
        bt10, bt11, e10, e11 = image(300), image(298), image(0.98), image(0.97)
        actual = SplitWindowJimenezMunoz2014LST()(
            brightness_temperature_10=bt10, brightness_temperature_11=bt11,
            emissivity_10=e10, emissivity_11=e11, water_vapor=2,
            mask=np.zeros((1, 1), dtype=bool),
        )
        mean_e, diff_e, diff_bt = (e10 + e11) / 2, e10 - e11, bt10 - bt11
        expected = (bt10 + 1.378 * diff_bt + 0.183 * diff_bt ** 2 - 0.268
                    + (54.30 - 2.238 * 2) * (1 - mean_e)
                    + (-129.20 + 16.40 * 2) * diff_e)
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-10)

    def test_invalid_band_eleven_does_not_produce_infinity(self):
        with np.errstate(invalid="ignore", over="ignore"):
            result = split_window(
                image(300), image(np.inf), image(0.2), image(0.6),
                lst_method="kerr-1992",
            )
        self.assertFalse(np.isinf(result).any())


if __name__ == "__main__":
    unittest.main(verbosity=2)
