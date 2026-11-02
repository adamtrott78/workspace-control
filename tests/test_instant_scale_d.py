"""Unit tests for result normalization."""

import unittest

from scripts.instant_scale_d import normalize_result


class NormalizeResultTests(unittest.TestCase):
    def test_valid_results(self):
        for value in ("PASS", "FAIL", "PENDING"):
            with self.subTest(value=value):
                self.assertEqual(normalize_result(value), value)

    def test_invalid_results(self):
        for value in ("pass", "Fail", "pending", "", "SUCCESS", " PASS", "FAIL ", 0, 1, True, None, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_result(value)


if __name__ == "__main__":
    unittest.main()
