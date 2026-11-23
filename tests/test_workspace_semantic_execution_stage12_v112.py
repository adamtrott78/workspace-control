from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
V112_REPAIR_HEAD = "60fd1e3f2bfcbbd92ba2a75d0208cbdf1bd00f4e"
LINUX_PATH = "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"
EXPECTED_BASELINE = "7bab6ff51202b3d0c3190d1351e8578d22c4f2f1"
INITIAL_NAMESPACE = "0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de"
EXPECTED_EXISTING_PATH = "worker-results/stage12/5dda87c416484e45ae5a22f0bccf97f4/q1.json"


class Stage12V112CandidateBaselineTests(unittest.TestCase):
    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    def test_live_preflight_binds_reviewed_current_candidate_head(self) -> None:
        text = self.git("show", f"{V112_REPAIR_HEAD}:{LINUX_PATH}")
        self.assertIn(f'CANDIDATE_BASELINE="{EXPECTED_BASELINE}"', text)
        self.assertIn('REMOTE_CANDIDATE="$(git ls-remote', text)
        self.assertIn('CANDIDATE_BASELINE_MISMATCH:$REMOTE_CANDIDATE', text)

    def test_reviewed_baseline_is_single_legitimate_candidate_advance(self) -> None:
        self.assertEqual(self.git("rev-parse", f"{EXPECTED_BASELINE}^"), INITIAL_NAMESPACE)
        changed = self.git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", EXPECTED_BASELINE
        ).splitlines()
        self.assertEqual(changed, [EXPECTED_EXISTING_PATH])
        payload = json.loads(
            self.git("show", f"{EXPECTED_BASELINE}:{EXPECTED_EXISTING_PATH}")
        )
        self.assertEqual(payload["kind"], "RESULT")
        self.assertEqual(payload["session_generation"], 0)
        self.assertTrue(payload["action_id"].startswith("action:stage12:q1:"))

    def test_candidate_watcher_still_requires_single_commit_advances(self) -> None:
        harness = (
            ROOT / "benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate_branch_non_single_commit_advance", harness)
        self.assertIn("candidate_commit_path_mismatch", harness)
        self.assertIn("baseline = watcher.refresh()", harness)


if __name__ == "__main__":
    unittest.main()
