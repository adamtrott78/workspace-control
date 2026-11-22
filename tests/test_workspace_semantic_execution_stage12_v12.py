from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.2.json"
PROCEDURE = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.2.md"

SOURCE_HEAD = "2f32513f97834da76287d2f948891b758d5194f5"
LAUNCHER_BLOB = "a4619bcc8f4177878ddf0f40bec402e1b211aeb6"
CANDIDATE_BASELINE = "0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de"


class Stage12V12ReviewTests(unittest.TestCase):
    def test_review_is_not_authority_and_predecessor_is_unconsumed_nonreusable(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(review["authority_gate"]["explicit_fresh_operator_approval_required_after_review_validation"])
        self.assertFalse(review["predecessor_authority"]["consumed"])
        self.assertFalse(review["predecessor_authority"]["reusable"])
        self.assertFalse(review["predecessor_authority"]["live_consumption_marker_observed"])
        self.assertEqual(review["exact_candidate_bindings"]["windows_executable_source_head"], SOURCE_HEAD)
        self.assertEqual(review["exact_candidate_bindings"]["windows_operator_launcher"]["blob_sha"], LAUNCHER_BLOB)
        self.assertEqual(review["exact_candidate_bindings"]["candidate_result_branch"]["required_baseline_head"], CANDIDATE_BASELINE)

    def test_procedure_repairs_bounded_tool_discovery_and_moving_head_bug(self) -> None:
        text = PROCEDURE.read_text(encoding="utf-8")
        self.assertIn("$env:ProgramFiles", text)
        self.assertIn("Microsoft\\dotnet\\dotnet.exe", text)
        self.assertIn(".dotnet\\dotnet.exe", text)
        self.assertIn("RUNNER_TOOL_CACHE", text)
        self.assertIn("actions-runner\\_work\\_tool", text)
        self.assertIn("NODE24_NOT_FOUND_IN_REVIEWED_LOCATIONS", text)
        self.assertNotIn("Get-Command dotnet -ErrorAction Stop", text)
        self.assertIn("checkout --detach $SourceSha", text)
        self.assertIn('$Head=(git -C $Stage rev-parse HEAD)', text)
        self.assertNotIn("fetch --force --depth=1 origin workspace-semantic-execution-migration-v1", text)
        self.assertIn("workspace-control-stage12-d4-v12", text)
        self.assertIn("Live attempts authorized now: **0**", text)

    def test_no_install_or_persistent_policy_widening(self) -> None:
        text = PROCEDURE.read_text(encoding="utf-8").lower()
        for forbidden in ("winget install", "choco install", "set-executionpolicy", "invoke-webrequest"):
            self.assertNotIn(forbidden, text)
        self.assertIn("persistent path edit", text)
        self.assertIn("restores them in `finally`".replace("\\", ""), text)

    def test_exact_windows_command_parses_without_execution(self) -> None:
        engine = shutil.which("powershell.exe") or shutil.which("pwsh")
        if engine is None:
            self.skipTest("PowerShell parser unavailable on this runner")
        text = PROCEDURE.read_text(encoding="utf-8")
        marker = "```powershell\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
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
