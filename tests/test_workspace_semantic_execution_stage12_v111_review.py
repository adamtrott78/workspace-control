from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.11.json"
AUTH110 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.10.json"


class Stage12V111ReviewTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()

    def test_v110_is_consumed_nonreusable(self) -> None:
        authority = json.loads(AUTH110.read_text(encoding="utf-8"))
        self.assertTrue(authority["attempt_contract"]["consumed"])
        self.assertFalse(authority["attempt_contract"]["reusable"])
        self.assertIn("LIVE_SEMANTIC_BINDING_STALE", authority["status"])

    def test_review_binds_live_semantic_repair_and_unchanged_a7(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        bindings = review["exact_candidate_bindings"]
        self.assertEqual(
            self.git("HEAD:benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"),
            bindings["benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"],
        )
        self.assertEqual(
            self.git(f'{bindings["live_semantic_sha"]}:semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py'),
            bindings["live_operator_http_blob"],
        )
        self.assertEqual(self.git("HEAD:operator-bridge/src"), bindings["operator-bridge/src_tree"])
        self.assertFalse(review["accepted_frontend"]["changed_in_v111"])

    def test_review_grants_zero_live_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(review["authority_gate"]["formal_windows_cleanup_required"])
        self.assertTrue(review["authority_gate"]["fresh_operator_approval_required"])


if __name__ == "__main__":
    unittest.main()
