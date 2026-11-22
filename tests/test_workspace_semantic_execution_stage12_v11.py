from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.1.json"
PROCEDURE = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.1.md"

SOURCE_HEAD = "2f32513f97834da76287d2f948891b758d5194f5"
LAUNCHER_BLOB = "a4619bcc8f4177878ddf0f40bec402e1b211aeb6"
LINUX_BLOB = "3eb352f456d84de565514e2a7046e847ea0d25ea"
HARNESS_BLOB = "7b1feb8fa13cf0ea46883b07831e829fd9e7e75d"
CANDIDATE_BASELINE = "0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de"


class Stage12V11ReviewTests(unittest.TestCase):
    def test_review_is_not_authority_and_binds_exact_current_candidate(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"][
                "explicit_fresh_operator_approval_required_after_review_validation"
            ]
        )
        self.assertTrue(review["predecessor_authority"]["consumed"])
        self.assertFalse(review["predecessor_authority"]["reusable"])
        bindings = review["exact_candidate_bindings"]
        self.assertEqual(bindings["windows_executable_source_head"], SOURCE_HEAD)
        self.assertEqual(bindings["windows_operator_launcher"]["blob_sha"], LAUNCHER_BLOB)
        self.assertEqual(bindings["linux_private_route_transaction"]["blob_sha"], LINUX_BLOB)
        self.assertEqual(bindings["real_instant_harness"]["blob_sha"], HARNESS_BLOB)
        self.assertEqual(
            bindings["candidate_result_branch"]["required_baseline_head"],
            CANDIDATE_BASELINE,
        )

    def test_review_preserves_manual_input_and_safety_boundaries(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        manual = review["manual_interaction"]
        self.assertEqual(manual["worker_service_sequence"], "Ctrl+Space -> Ctrl+V -> Enter")
        self.assertTrue(manual["next_ctrl_space_only_after_next_linux_ready_marker"])
        for key in (
            "automatic_typing",
            "automatic_paste",
            "automatic_enter",
            "automatic_send",
            "dom_or_page_content_scraping",
            "manual_worker_result_relay",
        ):
            self.assertFalse(manual[key])
        safety = review["retained_safety"]
        self.assertFalse(safety["tailscale_funnel"])
        self.assertFalse(safety["public_listener"])
        self.assertFalse(safety["production_postgres_mutation"])
        self.assertFalse(safety["gpu_use"])
        self.assertFalse(safety["generic_shell_authority"])

    def test_procedure_binds_blank_auth_handoff_and_consumption_gate(self) -> None:
        text = PROCEDURE.read_text(encoding="utf-8")
        self.assertIn(SOURCE_HEAD, text)
        self.assertIn(LAUNCHER_BLOB, text)
        self.assertIn(CANDIDATE_BASELINE, text)
        self.assertIn("exactly one blank tab", text)
        self.assertIn("same tab back to `about:blank`", text)
        self.assertIn("STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS", text)
        self.assertIn("STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS", text)
        self.assertIn("Ctrl+Space -> Ctrl+V -> Enter", text)
        self.assertIn("Live attempts authorized now: **0**", text)

    def test_exact_windows_command_parses_without_execution(self) -> None:
        engine = shutil.which("powershell.exe") or shutil.which("pwsh")
        if engine is None:
            self.skipTest("PowerShell parser unavailable on this runner")
        text = PROCEDURE.read_text(encoding="utf-8")
        marker = "```powershell\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
        self.assertIn(SOURCE_HEAD, command)
        self.assertIn(LAUNCHER_BLOB, command)
        self.assertIn("workspace-control-stage12-d4-v11", command)
        self.assertIn("checkout --detach FETCH_HEAD", command)
        parser = (
            "$text=[Console]::In.ReadToEnd(); "
            "$tokens=$null; $errors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseInput("
            "$text,[ref]$tokens,[ref]$errors) | Out-Null; "
            "if($errors.Count -gt 0){"
            "$errors | ForEach-Object { [Console]::Error.WriteLine($_.Message) }; "
            "exit 1}; exit 0"
        )
        proc = subprocess.run(
            [engine, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", parser],
            input=command,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
