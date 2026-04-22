import unittest

import numpy as np

from pylstemp import (
    brightness,
    emissivity,
    single_window,
    spectral_indices,
    split_window,
    water_vapor,
)


def brightness_band_10(thermal_band, **kwargs):
    return brightness(thermal_band, band="band_10", **kwargs)


def brightness_band_11(thermal_band, **kwargs):
    return brightness(thermal_band, band="band_11", **kwargs)


def emissivity_band_10(ndvi_image, **kwargs):
    return emissivity(ndvi_image, band="band_10", **kwargs)


def emissivity_band_11(ndvi_image, **kwargs):
    return emissivity(ndvi_image, band="band_11", **kwargs)


class TestPublicApi(unittest.TestCase):
    def setUp(self):
        # Small deterministic inputs make the formulas easy to validate in tests.
        self.band_10 = np.full((4, 4), 1000.0)
        self.band_11 = np.full((4, 4), 900.0)
        self.band_4 = np.full((4, 4), 0.2)
        self.band_5 = np.full((4, 4), 0.6)
        self.rad_gain_band_10 = 0.0003342
        self.rad_bias_band_10 = 0.1
        self.rad_gain_band_11 = 0.0003342
        self.rad_bias_band_11 = 0.1
        self.sensor_8 = "landsat_8"
        self.sensor_9 = "landsat_9"

    def test_ndvi_returns_expected_shape(self):
        output = spectral_indices(
            indice="ndvi",
            band_5_nir=self.band_5,
            band_4_red=self.band_4,
        )
        self.assertEqual(output.shape, self.band_5.shape)

    def test_individual_brightness_helpers_preserve_shape(self):
        brightness_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_8,
            rad_gain=self.rad_gain_band_10,
            rad_bias=self.rad_bias_band_10,
        )
        brightness_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_8,
            rad_gain=self.rad_gain_band_11,
            rad_bias=self.rad_bias_band_11,
        )
        self.assertEqual(brightness_10.shape, self.band_10.shape)
        self.assertEqual(brightness_11.shape, self.band_11.shape)

    def test_individual_brightness_helpers_support_landsat_9(self):
        brightness_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_10,
            rad_bias=self.rad_bias_band_10,
        )
        brightness_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_11,
            rad_bias=self.rad_bias_band_11,
        )
        self.assertEqual(brightness_10.shape, self.band_10.shape)
        self.assertEqual(brightness_11.shape, self.band_11.shape)

    def test_brightness_temperature_changes_with_sensor_constants(self):
        brightness_8_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_8,
            rad_gain=self.rad_gain_band_10,
            rad_bias=self.rad_bias_band_10,
        )
        brightness_9_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_10,
            rad_bias=self.rad_bias_band_10,
        )
        brightness_8_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_8,
            rad_gain=self.rad_gain_band_11,
            rad_bias=self.rad_bias_band_11,
        )
        brightness_9_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_11,
            rad_bias=self.rad_bias_band_11,
        )
        self.assertFalse(np.allclose(brightness_8_10, brightness_9_10))
        self.assertFalse(np.allclose(brightness_8_11, brightness_9_11))

    def test_brightness_helpers_use_sensor_default_radiance_values(self):
        brightness_10 = brightness_band_10(self.band_10, sensor=self.sensor_8)
        brightness_11 = brightness_band_11(self.band_11, sensor=self.sensor_9)
        self.assertEqual(brightness_10.shape, self.band_10.shape)
        self.assertEqual(brightness_11.shape, self.band_11.shape)

    def test_brightness_helpers_allow_manual_radiance_override(self):
        default_output = brightness_band_10(self.band_10, sensor=self.sensor_8)
        custom_output = brightness_band_10(
            self.band_10,
            sensor=self.sensor_8,
            rad_gain=0.0005,
            rad_bias=0.2,
        )
        self.assertFalse(np.allclose(default_output, custom_output))

    def test_individual_emissivity_helpers_preserve_shape(self):
        ndvi_image = spectral_indices(
            indice="ndvi",
            band_5_nir=self.band_5,
            band_4_red=self.band_4,
        )
        output_10 = emissivity_band_10(
            ndvi_image,
            band_4_red=self.band_4,
            emissivity_method="avdan-2016",
        )
        output_11 = emissivity_band_11(
            ndvi_image,
            band_4_red=self.band_4,
            emissivity_method="avdan-2016",
        )
        self.assertEqual(output_10.shape, ndvi_image.shape)
        self.assertEqual(output_11.shape, ndvi_image.shape)

    def test_single_window_preserves_shape(self):
        brightness_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_8,
            rad_gain=self.rad_gain_band_10,
            rad_bias=self.rad_bias_band_10,
        )
        output = single_window(
            brightness_10,
            band_4_red=self.band_4,
            band_5_nir=self.band_5,
        )
        self.assertEqual(output.shape, self.band_10.shape)

    def test_split_window_preserves_shape(self):
        brightness_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_10,
            rad_bias=self.rad_bias_band_10,
        )
        brightness_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_11,
            rad_bias=self.rad_bias_band_11,
        )
        output = split_window(
            brightness_10,
            brightness_11,
            band_4_red=self.band_4,
            band_5_nir=self.band_5,
            lst_method="du-2015",
        )
        self.assertEqual(output.shape, self.band_10.shape)

    def test_split_window_rejects_single_channel_emissivity_method(self):
        brightness_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_10,
            rad_bias=self.rad_bias_band_10,
        )
        brightness_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_9,
            rad_gain=self.rad_gain_band_11,
            rad_bias=self.rad_bias_band_11,
        )
        with self.assertRaisesRegex(ValueError, "single-channel emissivity method"):
            split_window(
                brightness_10,
                brightness_11,
                band_4_red=self.band_4,
                band_5_nir=self.band_5,
                lst_method="du-2015",
                emissivity_method="avdan-2016",
            )

    def test_split_window_supports_du_2015_method(self):
        brightness_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_8,
        )
        brightness_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_8,
        )
        output = split_window(
            brightness_10,
            brightness_11,
            band_4_red=self.band_4,
            band_5_nir=self.band_5,
            lst_method="du-2015",
        )
        self.assertEqual(output.shape, self.band_10.shape)

    def test_split_window_du_2015_accepts_water_vapor(self):
        brightness_10 = brightness_band_10(
            self.band_10,
            sensor=self.sensor_8,
        )
        brightness_11 = brightness_band_11(
            self.band_11,
            sensor=self.sensor_8,
        )
        default_output = split_window(
            brightness_10,
            brightness_11,
            band_4_red=self.band_4,
            band_5_nir=self.band_5,
            lst_method="du-2015",
        )
        cwv_output = split_window(
            brightness_10,
            brightness_11,
            band_4_red=self.band_4,
            band_5_nir=self.band_5,
            lst_method="du-2015",
            water_vapor=3.8,
        )
        self.assertFalse(np.allclose(default_output, cwv_output))

    def test_water_vapor_preserves_shape(self):
        brightness_10 = np.array(
            [
                [300.0, 301.0, 302.0, 303.0, 304.0],
                [301.0, 302.0, 303.0, 304.0, 305.0],
                [302.0, 303.0, 304.0, 305.0, 306.0],
                [303.0, 304.0, 305.0, 306.0, 307.0],
                [304.0, 305.0, 306.0, 307.0, 308.0],
            ]
        )
        brightness_11 = 0.8 * brightness_10
        ndvi_image = np.full((5, 5), 0.35)

        output = water_vapor(
            brightness_10,
            brightness_11,
            ndvi_image,
            method="wang-2015",
            window_size=5,
            group_count=1,
        )

        self.assertEqual(output.shape, brightness_10.shape)
        self.assertTrue(np.isfinite(output[2, 2]))

    def test_split_window_jimenez_munoz_accepts_water_vapor(self):
        brightness_10 = brightness_band_10(self.band_10, sensor=self.sensor_8)
        brightness_11 = brightness_band_11(self.band_11, sensor=self.sensor_8)

        output = split_window(
            brightness_10,
            brightness_11,
            band_4_red=self.band_4,
            band_5_nir=self.band_5,
            lst_method="jimenez-munoz-2014",
            water_vapor=2.0,
        )

        self.assertEqual(output.shape, self.band_10.shape)

    def test_split_window_jimenez_munoz_accepts_pixel_water_vapor(self):
        brightness_10 = brightness_band_10(self.band_10, sensor=self.sensor_8)
        brightness_11 = brightness_band_11(self.band_11, sensor=self.sensor_8)
        water_vapor = np.full(self.band_10.shape, 2.0)

        output = split_window(
            brightness_10,
            brightness_11,
            band_4_red=self.band_4,
            band_5_nir=self.band_5,
            lst_method="jimenez-munoz-2014",
            water_vapor=water_vapor,
        )

        self.assertEqual(output.shape, self.band_10.shape)

    def test_split_window_jimenez_munoz_requires_water_vapor(self):
        brightness_10 = brightness_band_10(self.band_10, sensor=self.sensor_8)
        brightness_11 = brightness_band_11(self.band_11, sensor=self.sensor_8)

        with self.assertRaisesRegex(ValueError, "requires water_vapor"):
            split_window(
                brightness_10,
                brightness_11,
                band_4_red=self.band_4,
                band_5_nir=self.band_5,
                lst_method="jimenez-munoz-2014",
            )
