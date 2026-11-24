from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.10.json"
AUTH19 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.9.json"


class Stage12V110ReviewTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()

    def test_v19_is_consumed_nonreusable(self) -> None:
        authority = json.loads(AUTH19.read_text(encoding="utf-8"))
        self.assertTrue(authority["attempt_contract"]["consumed"])
        self.assertFalse(authority["attempt_contract"]["reusable"])
        self.assertIn("CHUNKED_POST_BODY", authority["status"])

    def test_backend_repair_and_a7_bindings_are_exact(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        bindings = review["exact_candidate_bindings"]
        self.assertEqual(
            self.git("HEAD:semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py"),
            bindings["semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py"],
        )
        self.assertEqual(
            self.git("HEAD:tests/test_workspace_semantic_execution_backend_operator_http.py"),
            bindings["tests/test_workspace_semantic_execution_backend_operator_http.py"],
        )
        self.assertEqual(self.git("HEAD:operator-bridge/src"), bindings["operator-bridge/src_tree"])
        self.assertFalse(review["accepted_frontend"]["changed_in_v110"])

    def test_review_grants_zero_live_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(review["authority_gate"]["fresh_operator_approval_required"])


if __name__ == "__main__":
    unittest.main()
