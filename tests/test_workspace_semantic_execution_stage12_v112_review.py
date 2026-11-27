from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.12.json"


class Stage12V112ReviewTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()

    def test_review_binds_frozen_candidate_and_candidate_history(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        bindings = review["exact_candidate_bindings"]
        source = bindings["source_head"]
        self.assertEqual(
            self.git(f"{source}:benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"),
            bindings["benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"],
        )
        self.assertEqual(bindings["candidate_baseline"], "7bab6ff51202b3d0c3190d1351e8578d22c4f2f1")
        self.assertEqual(
            self.git(f"{bindings['candidate_baseline']}^"),
            "0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de",
        )

    def test_review_preserves_semantic_fix_and_a7(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        bindings = review["exact_candidate_bindings"]
        self.assertEqual(
            self.git(f"{bindings['live_semantic_sha']}:semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py"),
            bindings["live_operator_http_blob"],
        )
        self.assertEqual(
            self.git(f"{bindings['source_head']}:operator-bridge/src"),
            bindings["operator-bridge/src_tree"],
        )

    def test_review_grants_zero_live_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(review["authority_gate"]["fresh_operator_approval_required"])
        self.assertEqual(review["candidate_validation"]["result"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
