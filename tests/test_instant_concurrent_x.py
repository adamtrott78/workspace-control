"""Unit tests for strict slot normalization."""

import unittest

from scripts.instant_concurrent_x import normalize_slot


class NormalizeSlotTests(unittest.TestCase):
    def test_valid_slots(self):
        for value in range(1, 9):
            with self.subTest(value=value):
                self.assertEqual(normalize_slot(value), value)

    def test_invalid_slots(self):
        for value in (0, 9, -1, True, False, 1.0, 2.0, "1", None, [], {}, 1 + 0j):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    normalize_slot(value)

    def test_int_subclass_rejected(self):
        class DerivedInt(int):
            pass

        with self.assertRaises(ValueError):
            normalize_slot(DerivedInt(3))


if __name__ == "__main__":
    unittest.main()
