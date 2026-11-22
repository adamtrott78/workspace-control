from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.9.json"
PROCEDURE = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.9.md"
AUTH18 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.8.json"

class Stage12V19ReviewTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()

    def test_frozen_a7_bytes_are_unchanged(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        bindings = review["exact_candidate_bindings"]
        self.assertEqual(self.git("HEAD:operator-bridge/src"), bindings["operator-bridge/src_tree"])
        self.assertEqual(
            self.git("HEAD:operator-bridge/tools/workspace-operator-dev.ps1"),
            bindings["operator-bridge/tools/workspace-operator-dev.ps1"],
        )
        self.assertFalse(review["accepted_frontend"]["changed_in_v19"])

    def test_wrapper_revalidates_backend_after_frontend_start(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertEqual(
            self.git("HEAD:operator-bridge/tools/run-stage12-wop.ps1"),
            review["exact_candidate_bindings"]["operator-bridge/tools/run-stage12-wop.ps1"],
        )
        text = (ROOT / "operator-bridge/tools/run-stage12-wop.ps1").read_text(encoding="utf-8")
        for marker in (
            "D4_BACKEND_REVALIDATED_AFTER_FRONTEND_START=PASS",
            "D4_BACKEND_EXITED_DURING_FRONTEND_START",
            "D4_BACKEND_LOST_AFTER_FRONTEND_START",
            "D4_Q1_NOT_CLAIMABLE_AFTER_FRONTEND_START",
            "D4_OPERATOR_BACKEND_ROUTE_LOST",
        ):
            self.assertIn(marker, text)

    def test_v18_is_consumed_and_v19_grants_zero_authority(self) -> None:
        authority = json.loads(AUTH18.read_text(encoding="utf-8"))
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        procedure = PROCEDURE.read_text(encoding="utf-8")
        self.assertTrue(authority["attempt_contract"]["consumed"])
        self.assertFalse(authority["attempt_contract"]["reusable"])
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertIn("Live attempts authorized by this review alone: **0**", procedure)

if __name__ == "__main__":
    unittest.main()
