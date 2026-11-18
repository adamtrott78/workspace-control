from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
LINUX_V2 = (
    ROOT
    / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v2.sh"
)
REVIEW_V2 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.2.json"
PROCEDURE_V2 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.2.md"
PROCEDURE_V3 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.3.md"
REVIEW_V3 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.3.json"
PROCEDURE_V4 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.4.md"
REVIEW_V4 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.4.json"
PROCEDURE_V5 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.5.md"
REVIEW_V5 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.5.json"
PROCEDURE_V6 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.6.md"
REVIEW_V6 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.6.json"
PROCEDURE_V7 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.7.md"
REVIEW_V7 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.7.json"
PROCEDURE_V8 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.8.md"
REVIEW_V8 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.8.json"
AUTHORITY_V8 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-authority.v0.8.json"


class Stage12RetryTransactionStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = LINUX_V2.read_text(encoding="utf-8")

    def test_v2_transaction_is_bash_syntax_valid(self) -> None:
        proc = subprocess.run(
            ["bash", "-n", str(LINUX_V2)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_windows_readiness_gate_precedes_live_mutation(self) -> None:
        marker = 'echo "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"'
        self.assertIn(
            'WINDOWS_READY_MARKER="STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"',
            self.text,
        )
        self.assertIn('read -r -p', self.text)
        self.assertIn('WINDOWS_READY_CONFIRMATION_MISMATCH', self.text)
        gate = self.text.index(marker)
        for live_mutation in (
            'python3 -m venv "$VENV"',
            '"$PG_PREFIX/bin/initdb"',
            'sudo tailscale serve --bg',
            '"$HARNESS_REL"       --serve-port',
        ):
            self.assertGreater(
                self.text.index(live_mutation),
                gate,
                live_mutation,
            )

    def test_candidate_baseline_is_rechecked_before_arm(self) -> None:
        baseline_check = self.text.index("STAGE12_CANDIDATE_BASELINE=PASS")
        gate = self.text.index("STAGE12_WINDOWS_READY_GATE=PASS")
        self.assertLess(baseline_check, gate)
        self.assertIn(
            'CANDIDATE_BASELINE="0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de"',
            self.text,
        )
        self.assertIn(
            'git ls-remote "$REPO_URL" refs/heads/worker-result-candidates-v1',
            self.text,
        )

    def test_abort_cleanup_verifies_exact_snapshot_restoration(self) -> None:
        self.assertIn("verify_restored_snapshot()", self.text)
        self.assertIn("STAGE12_CLEANUP_ROUTE_RESTORED=PASS", self.text)
        self.assertIn("STAGE12_CLEANUP_ROUTE_RESTORED=FAIL", self.text)
        self.assertIn("STAGE12_CLEANUP_EVIDENCE_PRESERVED=", self.text)
        self.assertIn("SERVE_ROLLBACK_MISMATCH", self.text)
        self.assertIn("FUNNEL_ROLLBACK_MISMATCH", self.text)

    def test_v2_retains_private_route_and_no_widening(self) -> None:
        self.assertIn('ROUTE_PATH="/operator-bridge/v1"', self.text)
        self.assertIn('http://127.0.0.1:8888', self.text)
        self.assertIn('--set-path="$ROUTE_PATH"', self.text)
        self.assertNotIn("tailscale serve reset", self.text)
        self.assertNotIn("tailscale serve --https=443 off", self.text)
        self.assertNotIn("tailscale funnel --bg", self.text)
        self.assertNotIn("0.0.0.0", self.text)
        self.assertIn("PRIVATE_ROUTE_STAGE12_REAL_INSTANT_V2=PASS", self.text)

    def test_retry_review_is_not_authority_and_binds_exact_candidate(self) -> None:
        import json

        review = json.loads(REVIEW_V2.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"]["explicit_fresh_operator_approval_required"]
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["executable_source_head"],
            "b0466c03acb9d6b863df421e2c116c84bff312f6",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["linux_private_route_transaction"]["blob_sha"],
            "962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca",
        )

    def test_retry_procedure_eliminates_multiline_windows_launch(self) -> None:
        text = PROCEDURE_V2.read_text(encoding="utf-8")
        self.assertIn("single executable line", text)
        self.assertIn(
            "STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS",
            text,
        )
        self.assertIn(
            "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS",
            text,
        )
        self.assertNotIn("try {", text)
        self.assertNotIn("finally {", text)

    def test_v03_execution_policy_repair_is_process_scoped_and_fail_closed(self) -> None:
        text = PROCEDURE_V3.read_text(encoding="utf-8")
        marker = "```powershell\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
        self.assertIn("-ExecutionPolicy Bypass -File", command)
        self.assertIn("Get-ExecutionPolicy -List", command)
        self.assertIn("MachinePolicy", command)
        self.assertIn("UserPolicy", command)
        self.assertIn("GROUP_POLICY_EXECUTION_POLICY_PRESENT", command)
        self.assertNotIn("Set-ExecutionPolicy", command)
        self.assertNotIn("Unblock-File", command)
        self.assertNotIn("reg.exe", command.lower())
        self.assertNotIn("set-itemproperty", command.lower())
        self.assertIn("workspace-control-stage12-retry-v3", command)
        self.assertIn(
            "STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS",
            text,
        )
        self.assertIn(
            "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS",
            text,
        )

    def test_v03_review_is_not_authority_and_keeps_executable_bindings(self) -> None:
        import json

        review = json.loads(REVIEW_V3.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"]["existing_v02_authority_does_not_authorize_v03_procedure"]
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["windows_operator_launcher"]["blob_sha"],
            "d9d474ca6870585c9e4767f551086e17b4525fbc",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["linux_private_route_transaction"]["blob_sha"],
            "962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["operator_procedure"]["blob_sha"],
            "62d98d601b451621fd17a869149ed295f1f9ca9a",
        )

    def test_v04_dotnet_discovery_is_bounded_nonpersistent_and_net10(self) -> None:
        text = PROCEDURE_V4.read_text(encoding="utf-8")
        marker = "```powershell\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
        self.assertIn("Get-Command dotnet", command)
        self.assertIn("ProgramFiles", command)
        self.assertIn("LOCALAPPDATA", command)
        self.assertIn("DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS", command)
        self.assertIn("DOTNET10_VERSION_MISMATCH", command)
        self.assertIn("-notmatch '^10\\.'", command)
        self.assertIn("$OldPath=$env:PATH", command)
        self.assertIn("$OldDotnetRoot=$env:DOTNET_ROOT", command)
        self.assertIn("$env:PATH=$OldPath", command)
        self.assertIn("$env:DOTNET_ROOT=$OldDotnetRoot", command)
        self.assertNotIn("setx", command.lower())
        self.assertNotIn("winget", command.lower())
        self.assertNotIn("choco", command.lower())
        self.assertNotIn("msiexec", command.lower())
        self.assertNotIn("Set-ExecutionPolicy", command)
        self.assertNotIn("SetEnvironmentVariable", command)
        self.assertIn("-ExecutionPolicy Bypass -File", command)

    def test_v04_review_is_not_authority_and_keeps_executable_bindings(self) -> None:
        import json

        review = json.loads(REVIEW_V4.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"]["existing_v03_authority_does_not_authorize_v04_procedure"]
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["windows_operator_launcher"]["blob_sha"],
            "d9d474ca6870585c9e4767f551086e17b4525fbc",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["operator_procedure"]["blob_sha"],
            "1d33484a311a98d36c532addfadd16c79ab56f71",
        )

    def test_v05_adds_only_userprofile_dotnet_location(self) -> None:
        text = PROCEDURE_V5.read_text(encoding="utf-8")
        marker = "```powershell\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
        self.assertIn("$env:USERPROFILE", command)
        self.assertIn("'.dotnet\\dotnet.exe'", command)
        self.assertIn("DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS", command)
        self.assertIn("-notmatch '^10\\.'", command)
        self.assertIn("$env:PATH=$OldPath", command)
        self.assertIn("$env:DOTNET_ROOT=$OldDotnetRoot", command)
        self.assertNotIn("winget", command.lower())
        self.assertNotIn("choco", command.lower())
        self.assertNotIn("msiexec", command.lower())
        self.assertNotIn("setx", command.lower())
        self.assertIn("-ExecutionPolicy Bypass -File", command)

    def test_v05_review_is_not_authority_and_keeps_executable_bindings(self) -> None:
        import json

        review = json.loads(REVIEW_V5.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"]["existing_v04_authority_does_not_authorize_v05_procedure"]
        )
        self.assertEqual(
            review["dotnet_delta"]["added_location"],
            "%USERPROFILE%\\.dotnet\\dotnet.exe",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["windows_operator_launcher"]["blob_sha"],
            "d9d474ca6870585c9e4767f551086e17b4525fbc",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["operator_procedure"]["blob_sha"],
            "40049b88799b3bc4683931d0a56a50c07591fc61",
        )

    def test_v06_reuses_bounded_stage10_node24_toolcache_binding(self) -> None:
        text = PROCEDURE_V6.read_text(encoding="utf-8")
        marker = "```powershell\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
        self.assertIn("Get-Command node.exe", command)
        self.assertIn("RUNNER_TOOL_CACHE", command)
        self.assertIn("actions-runner\\_work\\_tool", command)
        self.assertIn("'^24\\.\\d+\\.\\d+", command)
        self.assertIn("'x64'", command)
        self.assertIn("'node.exe'", command)
        self.assertIn("'npm.cmd'", command)
        self.assertIn("NODE24_NOT_FOUND_IN_REVIEWED_LOCATIONS", command)
        self.assertIn("NODE24_VERSION_MISMATCH", command)
        self.assertIn("NPM_NOT_AVAILABLE_IN_REVIEWED_NODE24", command)
        self.assertIn("$env:PATH=$OldPath", command)
        self.assertNotIn("winget", command.lower())
        self.assertNotIn("choco", command.lower())
        self.assertNotIn("npm install -g", command.lower())
        self.assertNotIn("setx", command.lower())

    def test_v06_review_is_invalidated_before_authority(self) -> None:
        import json

        review = json.loads(REVIEW_V6.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "INVALIDATED_PREAUTH_PROCEDURE_DEFECT")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertFalse(review["invalidation"]["authority_artifact_created"])
        self.assertFalse(review["invalidation"]["windows_execution_started"])
        self.assertFalse(review["invalidation"]["linux_execution_started"])
        self.assertFalse(review["invalidation"]["live_authority_consumed"])
        self.assertEqual(
            review["exact_candidate_bindings"]["operator_procedure"]["blob_sha"],
            "dd995d976fb6c3d1f1427d194e58e5037f331573",
        )

    def test_v07_repairs_powershell_structure_and_bounded_node_fallback(self) -> None:
        text = PROCEDURE_V7.read_text(encoding="utf-8")
        marker = "~~~powershell\n".replace("~~~", "```")
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
        self.assertIn("$DotnetDir=Split-Path -Parent $DotnetPath", command)
        self.assertIn("Where-Object { $_.Name -match '^24\\.\\d+\\.\\d+$' }", command)
        self.assertIn("$CurrentNodeVersion", command)
        self.assertIn("$CurrentNpmVersion", command)
        self.assertIn("$env:DOTNET_ROOT=$DotnetDir; try {", command)
        self.assertEqual(command.count("try { git init -q $Stage"), 1)
        self.assertNotIn("^24\\.\\d+\\.\\d+ try {", command)
        self.assertNotIn("$env:DOTNET_ROOT=$DotnetDir try {", command)
        self.assertNotIn("winget", command.lower())
        self.assertNotIn("choco", command.lower())
        self.assertNotIn("npm install -g", command.lower())
        self.assertNotIn("setx", command.lower())

    def test_v07_validated_review_is_not_authority_and_keeps_exact_bindings(self) -> None:
        import json

        review = json.loads(REVIEW_V7.read_text(encoding="utf-8"))
        self.assertEqual(
            review["status"],
            "VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY",
        )
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"]["v06_operator_approval_does_not_authorize_v07_procedure"]
        )
        self.assertEqual(review["procedure_delta"]["required_node_major_version"], 24)
        self.assertEqual(
            review["exact_candidate_bindings"]["operator_procedure"]["blob_sha"],
            "620e78f044189ab679019380a76d3f8c62711ca0",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["windows_operator_launcher"]["blob_sha"],
            "d9d474ca6870585c9e4767f551086e17b4525fbc",
        )
        self.assertEqual(
            review["validation"]["candidate_head"],
            "215287bb1bb49b90d5cf207fb4ebf368a57c7ec3",
        )
        self.assertEqual(review["validation"]["workspace_control_run"], 3010)
        self.assertEqual(review["validation"]["semantic_execution_run"], 310)
        self.assertEqual(review["validation"]["operator_bridge_run"], 583)
        self.assertEqual(review["validation"]["result"], "SUCCESS")

    def test_v08_removes_only_programfiles_x86_escape_defect(self) -> None:
        text7 = PROCEDURE_V7.read_text(encoding="utf-8")
        text8 = PROCEDURE_V8.read_text(encoding="utf-8")
        marker = "~~~powershell\n".replace("~~~", "```")
        start7 = text7.index(marker) + len(marker)
        end7 = text7.index("\n```", start7)
        start8 = text8.index(marker) + len(marker)
        end8 = text8.index("\n```", start8)
        command7 = text7[start7:end7]
        command8 = text8[start8:end8]
        bad = "\\${env:ProgramFiles(x86)}"
        good = "${env:ProgramFiles(x86)}"
        self.assertEqual(command7.count(bad), 2)
        self.assertEqual(command8.count(bad), 0)
        self.assertEqual(command8.count(good), 2)
        self.assertEqual(command7.replace(bad, good), command8)
        self.assertEqual(len(command7) - len(command8), 2)

    def test_v08_review_is_not_authority_and_keeps_exact_bindings(self) -> None:
        import json

        review = json.loads(REVIEW_V8.read_text(encoding="utf-8"))
        self.assertEqual(
            review["status"],
            "VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY",
        )
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"]["v07_authority_does_not_authorize_v08_procedure"]
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["operator_procedure"]["blob_sha"],
            "58c714ba5c0c6e6dee337ce70f0c4b550e65a87c",
        )
        self.assertEqual(review["procedure_delta"]["removed_literal_backslashes"], 2)
        self.assertTrue(review["procedure_delta"]["no_other_command_byte_change"])
        self.assertEqual(
            review["validation"]["candidate_head"],
            "f0051fb3534da19073faee7b33f04edd999c12df",
        )
        self.assertEqual(review["validation"]["workspace_control_run"], 3016)
        self.assertEqual(review["validation"]["semantic_execution_run"], 316)
        self.assertEqual(review["validation"]["operator_bridge_run"], 589)
        self.assertEqual(review["validation"]["result"], "SUCCESS")

    def test_v08_authority_binds_exact_validated_review_and_invalidated_v07(self) -> None:
        import json

        authority = json.loads(AUTHORITY_V8.read_text(encoding="utf-8"))
        self.assertEqual(
            authority["status"],
            "AUTHORIZED_STAGE12_REAL_INSTANT_RETRY_SINGLE_ATTEMPT",
        )
        self.assertEqual(
            authority["approval_basis"]["approved_final_state_head"],
            "fc2921819bb61f110004add32563d34df66dfa84",
        )
        self.assertEqual(
            authority["approval_basis"]["approved_review_blob_sha"],
            "3d4f3a589e317baf51bbcb9f3341448bbc7cda48",
        )
        self.assertEqual(
            authority["approval_basis"]["approved_procedure_blob_sha"],
            "58c714ba5c0c6e6dee337ce70f0c4b550e65a87c",
        )
        self.assertEqual(
            authority["approval_basis"]["candidate_validation"],
            {
                "workspace_control_run": 3016,
                "semantic_execution_run": 316,
                "operator_bridge_run": 589,
                "result": "SUCCESS",
            },
        )
        self.assertEqual(
            authority["approval_basis"]["final_state_validation"],
            {
                "validated_head": "fc2921819bb61f110004add32563d34df66dfa84",
                "workspace_control_run": 3017,
                "semantic_execution_run": 317,
                "operator_bridge_run": 590,
                "result": "SUCCESS",
            },
        )
        self.assertEqual(
            authority["predecessor_authority"]["prior_status"],
            "INVALIDATED_UNCONSUMED_PREEXECUTION_PROCEDURE_ESCAPE_DEFECT",
        )
        self.assertFalse(authority["predecessor_authority"]["consumed"])
        self.assertTrue(authority["predecessor_authority"]["invalidated"])
        self.assertFalse(authority["predecessor_authority"]["reusable"])
        self.assertEqual(
            authority["exact_authorized_execution"]["operator_procedure"]["blob_sha"],
            "58c714ba5c0c6e6dee337ce70f0c4b550e65a87c",
        )
        self.assertEqual(
            authority["exact_authorized_execution"]["candidate_result_branch"]["required_baseline_head"],
            "0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de",
        )
        self.assertEqual(authority["authority_consumption"]["attempts_authorized"], 1)
        self.assertEqual(
            authority["authority_consumption"]["live_authority_consumption_marker"],
            "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS",
        )


if __name__ == "__main__":
    unittest.main()
