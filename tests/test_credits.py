import unittest

from pylstemp import ORIGINAL_LIBRARY_CREDIT


class TestCredits(unittest.TestCase):
    def test_original_library_credit_is_exposed(self):
        self.assertIn("Oladimeji Mudele", ORIGINAL_LIBRARY_CREDIT)
