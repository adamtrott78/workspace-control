"""Standard-library regression tests for bounded retry budgets."""
import unittest

from scripts.instant_multi_leaf_retry import normalize_budget


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


if __name__ == "__main__":
    unittest.main()
