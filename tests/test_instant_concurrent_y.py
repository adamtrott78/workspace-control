"""Contract tests for strict priority normalization."""

import unittest

from scripts.instant_concurrent_y import normalize_priority


class NormalizePriorityTests(unittest.TestCase):
    def test_valid_values(self):
        for value in ("LOW", "MEDIUM", "HIGH"):
            with self.subTest(value=value):
                self.assertEqual(normalize_priority(value), value)

    def test_invalid_strings(self):
        for value in ("", "low", "Low", "medium", "High", " HIGH", "HIGH ", "CRITICAL", "LOW\n"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_priority(value)

    def test_non_strings(self):
        for value in (None, True, False, 0, 1, 3.0, b"LOW", ["LOW"], {"value": "LOW"}, ("LOW",)):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    normalize_priority(value)


if __name__ == "__main__":
    unittest.main()
