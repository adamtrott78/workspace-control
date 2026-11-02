"""Unit tests for worker-slot normalization."""

import unittest

from scripts.instant_scale_a import normalize_worker_slot


class NormalizeWorkerSlotTests(unittest.TestCase):
    def test_valid_slots(self):
        for value in range(1, 5):
            with self.subTest(value=value):
                self.assertEqual(normalize_worker_slot(value), value)

    def test_invalid_values(self):
        for value in (0, 5, -1, True, False, 1.0, 2.0, "1", None, [], {}, 1 + 0j):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_worker_slot(value)


if __name__ == "__main__":
    unittest.main()
