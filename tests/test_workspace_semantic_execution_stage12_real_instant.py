from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py"


class Stage12RealInstantHarnessStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = HARNESS.read_text(encoding="utf-8")
        ast.parse(self.text)

    def test_candidate_namespace_and_single_path_commit_are_frozen(self) -> None:
        self.assertIn('CANDIDATE_BRANCH = "worker-result-candidates-v1"', self.text)
        self.assertIn("candidate_branch_non_single_commit_advance", self.text)
        self.assertIn("candidate_commit_path_mismatch", self.text)
        self.assertIn("refs/heads/{self._branch}", self.text)

    def test_no_chatgpt_page_scraping_or_credential_automation(self) -> None:
        forbidden = (
            "selenium",
            "playwright",
            "pyautogui",
            "webdriver",
            "document.querySelector",
            "OPENAI_API_KEY",
            "Authorization: Bearer",
            "password=",
        )
        lowered = self.text.lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), lowered)
        self.assertIn('"credential_automation": False', self.text)
        self.assertIn('"browser_page_content_scraping": False', self.text)
        self.assertIn('"automatic_typing_or_submission": False', self.text)

    def test_persistent_reuse_probe_omits_token_from_second_packet(self) -> None:
        self.assertIn("continuity_token =", self.text)
        self.assertIn("Do NOT include that", self.text)
        self.assertIn("It is intentionally NOT present in this", self.text)
        self.assertIn(
            "validator_evidence_refs=(q2_marker, q2_continuity)",
            self.text,
        )
        self.assertIn("worker_evidence_ref_instruction=(", self.text)
        self.assertIn(
            "evidence_refs=set(validator_evidence_refs)",
            self.text,
        )
        self.assertIn("STAGE12_PERSISTENT_SESSION_REUSE=PASS", self.text)

    def test_connected_tool_mentions_are_literal_and_fail_closed(self) -> None:
        self.assertIn('GITHUB_PLUGIN_MENTION = "@github"', self.text)
        self.assertIn(
            'WORKSPACE_SHELL_PLUGIN_MENTION = "@Workspace Shell"',
            self.text,
        )
        self.assertIn("def _objective_with_plugin_mentions(", self.text)
        self.assertIn('not mention.startswith("@")', self.text)
        self.assertIn("plugin_mentions=plugin_mentions", self.text)

    def test_stale_generation_is_fenced_before_replacement(self) -> None:
        self.assertIn("runtime.recover(", self.text)
        self.assertIn("OperatorActionState.STALE", self.text)
        self.assertIn("ExecutorSessionState.NEEDS_REPLACEMENT", self.text)
        self.assertIn("late_old_generation_candidate_accepted", self.text)
        self.assertIn("late_old_generation_mutated_state", self.text)
        self.assertIn("expected_session_generation=1", self.text)
        self.assertIn("session_generation=1", self.text)

    def test_human_submit_sequence_remains_manual(self) -> None:
        self.assertGreaterEqual(self.text.count("Press Ctrl+Space, then Ctrl+V, then Enter"), 3)
        self.assertIn('"operator_sequence": "Ctrl+Space -> Ctrl+V -> Enter"', self.text)

    def test_final_acceptance_requires_all_processes_and_replacement_ready(self) -> None:
        self.assertIn("stage12_final_state_mismatch", self.text)
        self.assertIn("stage12_final_operator_work_not_empty", self.text)
        self.assertIn("STAGE12_REAL_INSTANT_CALIBRATION=", self.text)
        self.assertIn('"replacement_session_generation": 1', self.text)


if __name__ == "__main__":
    unittest.main()
