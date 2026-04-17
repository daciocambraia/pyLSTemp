import unittest

import numpy as np

from pylstemp.temperature import (
    BaseTemperatureAlgorithm,
    MonoWindowLST,
    SplitWindowJiminezMunozLST,
    SplitWindowKerrLST,
    SplitWindowMcClainLST,
    SplitWindowMcMillinLST,
    SplitWindowPriceLST,
    SplitWindowSobrino1993LST,
)


class TestAlgorithms(unittest.TestCase):
    def setUp(self):
        self.base = np.full((3, 3), 300.0)
        self.mask = np.zeros((3, 3), dtype=bool)

    def test_mono_window_algorithm_shape(self):
        output = MonoWindowLST()(
            emissivity_10=np.full((3, 3), 0.98),
            brightness_temperature_10=self.base,
            mask=self.mask,
        )
        self.assertEqual(output.shape, self.base.shape)

    def test_split_window_algorithms_shape(self):
        emissivity = np.full((3, 3), 0.98)
        ndvi = np.full((3, 3), 0.4)

        algorithms = [
            SplitWindowJiminezMunozLST()(
                emissivity_10=emissivity,
                emissivity_11=emissivity,
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                mask=self.mask,
            ),
            SplitWindowKerrLST()(
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                ndvi=ndvi,
                mask=self.mask,
            ),
            SplitWindowMcMillinLST()(
                brightness_temperature_10=self.base,
                brightness_temperature_11=self.base - 2,
                mask=self.mask,
            ),
            SplitWindowPriceLST()(
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

    def test_mcclain_alias_points_to_mcmillin(self):
        self.assertIs(SplitWindowMcClainLST, SplitWindowMcMillinLST)

    def test_base_temperature_algorithm_is_public(self):
        self.assertTrue(callable(BaseTemperatureAlgorithm))
