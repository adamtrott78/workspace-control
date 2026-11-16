"""Tests for independent recovery implementation."""

import unittest

from scripts.instant_lease_recovery_x import normalize_attempt


class NormalizeAttemptTests(unittest.TestCase):
    def test_valid(self):
        for value in range(4):
            with self.subTest(value=value):
                self.assertEqual(normalize_attempt(value), value)

    def test_invalid(self):
        for value in (-1, 4, True, False, 1.0, 2.0, "1", None, [], {}, 1 + 0j):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    normalize_attempt(value)


if __name__ == "__main__":
    unittest.main()
