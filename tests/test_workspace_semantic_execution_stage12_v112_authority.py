from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_HEAD = "741414f8ddc09470087092615fb2d57a247eb89b"
AUTHORITY_PATH = "architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.12.json"


class Stage12V112AuthorityTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()

    def authority(self) -> dict:
        raw = subprocess.check_output(
            ["git", "show", f"{AUTHORITY_HEAD}:{AUTHORITY_PATH}"],
            cwd=ROOT,
            text=True,
        )
        return json.loads(raw)

    def test_authority_is_exactly_one_pending_attempt(self) -> None:
        a = self.authority()
        self.assertEqual(a["status"], "PENDING_OPERATOR_WOP_EXECUTION")
        self.assertEqual(a["approval_basis"]["approved_scope"], "EXACTLY_ONE_V1_12_D4_ATTEMPT")
        self.assertEqual(a["attempt_contract"]["attempts_authorized"], 1)
        self.assertFalse(a["attempt_contract"]["consumed"])
        self.assertTrue(a["attempt_contract"]["reusable"])
        self.assertTrue(a["attempt_contract"]["no_silent_retry"])

    def test_authority_binds_reviewed_candidate_and_semantic_backend(self) -> None:
        a = self.authority()
        b = a["exact_execution_bindings"]
        source = b["authority_parent_head"]
        self.assertEqual(
            self.git(f"{source}:benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"),
            b["benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"],
        )
        self.assertEqual(
            b["candidate_baseline"],
            "7bab6ff51202b3d0c3190d1351e8578d22c4f2f1",
        )
        self.assertEqual(
            self.git(f"{b['live_semantic_sha']}:semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py"),
            b["live_operator_http_blob"],
        )

    def test_authority_preserves_a7_and_marker_order(self) -> None:
        a = self.authority()
        b = a["exact_execution_bindings"]
        source = b["authority_parent_head"]
        self.assertEqual(
            self.git(f"{source}:operator-bridge/src"),
            "51480cc44f62d661421e975e67af127ecd0b0417",
        )
        self.assertEqual(
            a["attempt_contract"]["required_marker_order"],
            [
                "STAGE12_CANDIDATE_BASELINE=PASS",
                "STAGE12_SEMANTIC_LIVE_BINDING=PASS",
                "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS",
            ],
        )
        self.assertFalse(a["retained_prohibitions"]["candidate_history_rewrite"])


if __name__ == "__main__":
    unittest.main()
