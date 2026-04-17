import unittest

from pylstemp import list_algorithms
from pylstemp.emissivity.registry import emissivity_registry
from pylstemp.temperature.registry import split_window_registry


class TestRegistries(unittest.TestCase):
    def test_algorithm_metadata_is_available(self):
        catalog = list_algorithms()
        self.assertIn("emissivity", catalog)
        self.assertIn("temperature.split_window", catalog)

    def test_emissivity_registry_exposes_canonical_keys(self):
        self.assertIn("avdan", emissivity_registry.available_keys())

    def test_split_window_alias_resolves(self):
        metadata = split_window_registry.metadata("mc-clain")
        self.assertEqual(metadata.key, "mc-millin")
