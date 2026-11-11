"""Standard-library regression tests for bounded retry budgets."""
import unittest

from scripts.instant_multi_leaf_retry import normalize_budget, next_budget


class NormalizeBudgetTests(unittest.TestCase):
    def test_accepted(self):
        for value in (0, 4, 2):
            with self.subTest(value=value):
                self.assertEqual(normalize_budget(value), value)

    def test_rejected(self):
        for value in (-1, 5, True, False, 1.0, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_budget(value)


class NextBudgetTests(unittest.TestCase):
    def test_pass_resets_every_budget(self):
        for current in range(5):
            with self.subTest(current=current):
                self.assertEqual(next_budget(current, "PASS"), 0)

    def test_retry(self):
        for current, expected in ((0, 1), (3, 4), (4, 4)):
            with self.subTest(current=current):
                self.assertEqual(next_budget(current, "RETRYABLE_FAILURE"), expected)

    def test_terminal_failure(self):
        for current in (0, 2, 4):
            with self.subTest(current=current):
                self.assertEqual(next_budget(current, "TERMINAL_FAILURE"), 4)

    def test_invalid_outcome(self):
        for outcome in ("", "pass", "RETRY", None, True, 1):
            with self.subTest(outcome=outcome):
                with self.assertRaises(ValueError):
                    next_budget(2, outcome)

    def test_invalid_current(self):
        for current in (-1, 5, 1.0, "1", None):
            with self.subTest(current=current):
                with self.assertRaises(ValueError):
                    next_budget(current, "PASS")

    def test_bool_current(self):
        for current in (True, False):
            with self.subTest(current=current):
                with self.assertRaises(ValueError):
                    next_budget(current, "PASS")


if __name__ == "__main__":
    unittest.main()
