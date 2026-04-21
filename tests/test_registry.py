import unittest

from pylstemp import list_algorithms
from pylstemp.algorithms import FAMILY_REGISTRIES
from pylstemp.algorithms.emissivity import emissivity_registry
from pylstemp.algorithms.split_window import split_window_registry
from pylstemp.algorithms.spectral_indices import spectral_indices_registry
from pylstemp.algorithms.thermal import thermal_registry
from pylstemp.algorithms.water_vapor import water_vapor_registry


class TestRegistries(unittest.TestCase):
    def test_algorithm_metadata_is_available(self):
        catalog = list_algorithms()
        self.assertIn("emissivity", catalog)
        self.assertIn("split_window", catalog)
        self.assertIn("thermal", catalog)
        self.assertIn("spectral_indices", catalog)
        self.assertIn("water_vapor", catalog)
        self.assertIn("radiative_transfer", catalog)

    def test_family_registries_are_discovered_automatically(self):
        self.assertIn("emissivity", FAMILY_REGISTRIES)
        self.assertIn("single_channel", FAMILY_REGISTRIES)
        self.assertIn("split_window", FAMILY_REGISTRIES)
        self.assertIn("thermal", FAMILY_REGISTRIES)
        self.assertIn("spectral_indices", FAMILY_REGISTRIES)
        self.assertIn("water_vapor", FAMILY_REGISTRIES)
        self.assertIn("radiative_transfer", FAMILY_REGISTRIES)

    def test_emissivity_registry_exposes_canonical_keys(self):
        self.assertIn("avdan-2016", emissivity_registry.available_keys())

    def test_water_vapor_registry_exposes_wang_2015(self):
        self.assertIn("wang-2015", water_vapor_registry.available_keys())

    def test_split_window_registry_exposes_year_keys(self):
        self.assertIn("jimenez-munoz-2014", split_window_registry.available_keys())
        self.assertIn("price-1984", split_window_registry.available_keys())
        self.assertNotIn("mc-millin-1975", split_window_registry.available_keys())

    def test_thermal_and_spectral_indices_registries_discover_default_modules(self):
        self.assertIn("brightness", thermal_registry.available_keys())
        self.assertIn("ndvi", spectral_indices_registry.available_keys())
