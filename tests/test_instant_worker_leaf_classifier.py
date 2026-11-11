"""Independent boundary and input-validation tests for the worker leaf classifier."""

import importlib.util
from pathlib import Path
import unittest


_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "instant_worker_leaf_classifier.py"
_SPEC = importlib.util.spec_from_file_location("instant_worker_leaf_classifier", _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
classify_action = _MODULE.classify_action


def action(**overrides):
    candidate = {
        "reasoning_class": "LOW",
        "unresolved_architecture": False,
        "authority_expansion": False,
        "objective_validator": True,
        "context_items": 8,
        "files_touched": 3,
    }
    candidate.update(overrides)
    return candidate


class LeafClassifierTests(unittest.TestCase):
    def test_classification_rules_and_precedence(self):
        cases = [
            ({}, "LEAF_EXECUTABLE"),
            ({"reasoning_class": "MEDIUM"}, "LEAF_EXECUTABLE"),
            ({"context_items": 9}, "DECOMPOSE_AGAIN"),
            ({"files_touched": 4}, "DECOMPOSE_AGAIN"),
            ({"objective_validator": False}, "DECOMPOSE_AGAIN"),
            ({"reasoning_class": "HIGH"}, "ESCALATE_REASONING"),
            ({"unresolved_architecture": True}, "ESCALATE_REASONING"),
            ({"authority_expansion": True}, "ESCALATE_REASONING"),
            ({"reasoning_class": "HIGH", "context_items": 9}, "ESCALATE_REASONING"),
            ({"authority_expansion": True, "objective_validator": False}, "ESCALATE_REASONING"),
            ({"unrelated_field": "ignored"}, "LEAF_EXECUTABLE"),
        ]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                self.assertEqual(classify_action(action(**changes)), expected)

    def test_invalid_values_raise_value_error(self):
        cases = [
            {"reasoning_class": "UNKNOWN"},
            {"context_items": -1},
            {"files_touched": -1},
            {"context_items": True},
            {"files_touched": False},
            {"unresolved_architecture": 0},
            {"authority_expansion": "false"},
            {"objective_validator": None},
            {"context_items": 1.5},
            {"files_touched": "2"},
        ]
        for invalid in cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    classify_action(action(**invalid))

    def test_all_missing_required_fields_raise_value_error(self):
        for missing in (
            "reasoning_class",
            "unresolved_architecture",
            "authority_expansion",
            "objective_validator",
            "context_items",
            "files_touched",
        ):
            with self.subTest(missing=missing):
                candidate = action()
                del candidate[missing]
                with self.assertRaises(ValueError):
                    classify_action(candidate)

    def test_non_dictionary_raises_value_error(self):
        for value in (None, [], "action", 1, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    classify_action(value)

    def test_validation_precedes_escalation(self):
        with self.assertRaises(ValueError):
            classify_action(action(reasoning_class="HIGH", files_touched=True))


if __name__ == "__main__":
    unittest.main()
