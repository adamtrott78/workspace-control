"""Unit tests for batch-size normalization."""

import unittest

from scripts.instant_scale_g import normalize_batch_size


class NormalizeBatchSizeTests(unittest.TestCase):
    def test_valid_batch_sizes(self):
        for value in range(1, 17):
            with self.subTest(value=value):
                self.assertEqual(normalize_batch_size(value), value)

    def test_invalid_batch_sizes(self):
        for value in (0, 17, -1, 100, True, False, 1.0, 16.0, "1", None, [], {}, 1 + 0j):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_batch_size(value)


if __name__ == "__main__":
    unittest.main()
