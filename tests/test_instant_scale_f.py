"""Contract tests for action F mode normalization."""

import unittest

from scripts.instant_scale_f import normalize_mode


class NormalizeModeTests(unittest.TestCase):
    def test_valid_modes_unchanged(self):
        for value in ("READ", "WRITE"):
            with self.subTest(value=value):
                self.assertEqual(normalize_mode(value), value)

    def test_invalid_modes_raise_value_error(self):
        for value in ("read", "write", "Read", "Write", "", " READ", "WRITE ", None, True, False, 0, 1, 2.5, [], {}, b"READ"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_mode(value)


if __name__ == "__main__":
    unittest.main()
