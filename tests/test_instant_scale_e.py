"""Unit tests for epoch normalization."""

import unittest

from scripts.instant_scale_e import normalize_epoch


class NormalizeEpochTests(unittest.TestCase):
    def test_valid_epochs(self):
        for epoch in range(10):
            with self.subTest(epoch=epoch):
                self.assertEqual(normalize_epoch(epoch), epoch)

    def test_invalid_epochs(self):
        for value in (-1, 10, True, False, None, 1.0, "1", [], {}, 2 + 0j):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    normalize_epoch(value)


if __name__ == "__main__":
    unittest.main()
