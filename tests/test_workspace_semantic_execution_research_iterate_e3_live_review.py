"""Static acceptance for frozen E3-LIVE review/procedure."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "architecture"
BENCH = ROOT / "benchmarks" / "workspace-semantic-execution"


class E3LiveReviewTests(unittest.TestCase):
    def test_review_is_frozen_zero_authority_and_bound_to_c2_pass(self):
        closeout = json.loads(
            (ARCH / "workspace-semantic-execution-research-iterate-e3-c2-closeout.v0.1.json").read_text()
        )
        review = json.loads(
            (ARCH / "workspace-semantic-execution-research-iterate-e3-live-review.v0.1.json").read_text()
        )
        self.assertEqual(closeout["status"], "PASS")
        self.assertEqual(
            closeout["source_head"],
            "e14e71d1981a4aedbe9af75a54087683fe4718e1",
        )
        self.assertEqual(review["status"], "FROZEN_ZERO_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_authority_exists"])
        self.assertFalse(review["authority_gate"]["live_authorized"])
        self.assertTrue(
            review["authority_gate"]["fresh_explicit_operator_approval_required"]
        )
        self.assertTrue(review["authority_gate"]["one_shot"])
        self.assertIn("STOP_AT_AUTHORITY_GATE", review["stop_condition"])

    def test_procedure_stops_before_authority_and_wrapper_is_inert_on_import(self):
        procedure = (
            ARCH / "workspace-semantic-execution-research-iterate-e3-live-procedure.v0.1.md"
        ).read_text()
        wrapper = (
            BENCH / "live_research_iterate_e3.py"
        ).read_text()
        self.assertIn("## STOP_AT_AUTHORITY_GATE", procedure)
        self.assertIn("NO LIVE AUTHORITY EXISTS", procedure)
        self.assertIn(
            "6115b48dfdf4a4954b3b1626598f897e4e71eeec",
            wrapper,
        )
        self.assertIn('if __name__ == "__main__":', wrapper)
        self.assertNotIn("subprocess.", wrapper)
        self.assertNotIn("pynvml", wrapper)
        self.assertNotIn("PADataset", wrapper)

    def test_review_binds_exact_instrumentation_blobs(self):
        review = json.loads(
            (ARCH / "workspace-semantic-execution-research-iterate-e3-live-review.v0.1.json").read_text()
        )
        self.assertEqual(
            review["bindings"]["accepted_e2_topology"]["blob"],
            "d6acd6a4266641813deecb900b877b7250b02530",
        )
        self.assertEqual(
            review["bindings"]["resource_observer"]["blob"],
            "458a869252f108bea52952e12852961bc3158d1f",
        )
        self.assertEqual(
            review["bindings"]["e3_live_wrapper"]["blob"],
            "51e471886a4911c9f00d824316c600bf8f8fae19",
        )


if __name__ == "__main__":
    unittest.main()
