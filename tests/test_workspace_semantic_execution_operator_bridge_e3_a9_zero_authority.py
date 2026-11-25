"""A9 operator-boundary regression: diagnostic work grants zero live authority."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT = (
    ROOT
    / "architecture"
    / "workspace-semantic-execution-research-iterate-e3-a8-live-closeout.v0.1.json"
)
A9_REVIEW = (
    ROOT
    / "architecture"
    / "workspace-semantic-execution-research-iterate-e3-a9-root-intake-review.v0.1.json"
)


class E3A9OperatorBoundaryTests(unittest.TestCase):
    def test_consumed_a8_cannot_be_reused_by_a9_diagnostics(self):
        item = json.loads(CLOSEOUT.read_text(encoding="utf-8"))
        self.assertEqual(
            item["status"],
            "CONSUMED_FAIL_ROOT_CANDIDATE_NOT_DURABLY_INGESTED",
        )
        self.assertTrue(item["attempt"]["authority_consumed"])
        self.assertFalse(item["attempt"]["authority_reusable"])
        self.assertFalse(item["attempt"]["silent_retry_permitted"])
        self.assertFalse(item["new_live_authority_exists"])
        self.assertEqual(
            item["next_stage"],
            "E3-A9_ROOT_CANDIDATE_INTAKE_DIAGNOSTIC_REPAIR",
        )

    def test_a9_review_grants_no_live_operator_authority(self):
        item = json.loads(A9_REVIEW.read_text(encoding="utf-8"))
        gate = item["authority_gate"]
        self.assertFalse(gate["live_authority_exists"])
        self.assertFalse(gate["live_authorized"])
        self.assertFalse(gate["retry_authorized"])
        self.assertTrue(gate["fresh_explicit_operator_approval_required"])
        self.assertFalse(gate["a8_authority_reusable"])
        self.assertIn("STOP_AT_FRESH_AUTHORITY_GATE", item["stop_condition"])


if __name__ == "__main__":
    unittest.main()
