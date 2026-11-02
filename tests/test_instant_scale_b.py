"""Unit tests for retry-count normalization."""

import unittest

from scripts.instant_scale_b import normalize_retry_count


class NormalizeRetryCountTests(unittest.TestCase):
    def test_valid_values(self):
        for value in range(4):
            with self.subTest(value=value):
                self.assertEqual(normalize_retry_count(value), value)

    def test_invalid_values(self):
        for value in (-1, 4, True, False, None, 1.0, "1", [], {}, 2 + 0j):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    normalize_retry_count(value)


if __name__ == "__main__":
    unittest.main()
