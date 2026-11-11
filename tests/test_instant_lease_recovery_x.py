"""Unit tests for bounded attempt normalization."""

import unittest

from scripts.instant_lease_recovery_x import normalize_attempt


class NormalizeAttemptTests(unittest.TestCase):
    def test_valid_attempts(self):
        for attempt in range(4):
            with self.subTest(attempt=attempt):
                self.assertEqual(normalize_attempt(attempt), attempt)

    def test_invalid_attempts(self):
        for value in (-1, 4, True, False, 1.0, "1", None, [], {}, 2 + 0j):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    normalize_attempt(value)


if __name__ == "__main__":
    unittest.main()
