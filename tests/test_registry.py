import unittest

from pylstemp import list_algorithms
from pylstemp.algorithms import FAMILY_REGISTRIES
from pylstemp.algorithms.emissivity import emissivity_registry
from pylstemp.algorithms.split_window import split_window_registry
from pylstemp.algorithms.thermal import thermal_registry
from pylstemp.algorithms.vegetation import vegetation_registry


class TestRegistries(unittest.TestCase):
    def test_algorithm_metadata_is_available(self):
        catalog = list_algorithms()
        self.assertIn("emissivity", catalog)
        self.assertIn("split_window", catalog)
        self.assertIn("thermal", catalog)
        self.assertIn("vegetation", catalog)
        self.assertIn("radiative_transfer", catalog)

    def test_family_registries_are_discovered_automatically(self):
        self.assertIn("emissivity", FAMILY_REGISTRIES)
        self.assertIn("single_channel", FAMILY_REGISTRIES)
        self.assertIn("split_window", FAMILY_REGISTRIES)
        self.assertIn("thermal", FAMILY_REGISTRIES)
        self.assertIn("vegetation", FAMILY_REGISTRIES)
        self.assertIn("radiative_transfer", FAMILY_REGISTRIES)

    def test_emissivity_registry_exposes_canonical_keys(self):
        self.assertIn("avdan", emissivity_registry.available_keys())

    def test_split_window_alias_resolves(self):
        metadata = split_window_registry.metadata("mc-clain")
        self.assertEqual(metadata.key, "mc-millin")

    def test_thermal_and_vegetation_registries_discover_default_modules(self):
        self.assertIn("brightness", thermal_registry.available_keys())
        self.assertIn("ndvi", vegetation_registry.available_keys())
