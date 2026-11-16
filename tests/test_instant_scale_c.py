"""Contract tests for action C priority normalization."""

import unittest

from scripts.instant_scale_c import normalize_priority


class NormalizePriorityTests(unittest.TestCase):
    def test_valid_values_unchanged(self):
        for value in ("LOW", "MEDIUM", "HIGH"):
            with self.subTest(value=value):
                self.assertEqual(normalize_priority(value), value)

    def test_invalid_values_raise_value_error(self):
        invalid = ("low", "Medium", "high", "", " LOW", "HIGH ", None, True, False, 1, 0, 3.0, [], {}, b"LOW")
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_priority(value)


if __name__ == "__main__":
    unittest.main()
