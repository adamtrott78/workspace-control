"""Unit tests for decision normalization."""

import unittest

from scripts.instant_scale_h import normalize_decision


class NormalizeDecisionTests(unittest.TestCase):
    def test_valid_decisions(self):
        for value in ("EXECUTE", "DECOMPOSE", "ESCALATE"):
            with self.subTest(value=value):
                self.assertEqual(normalize_decision(value), value)

    def test_invalid_decisions(self):
        for value in ("execute", "Decompose", "ESCALATE ", "", "PASS", None, True, 1, [], {}, b"EXECUTE"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    normalize_decision(value)


if __name__ == "__main__":
    unittest.main()
