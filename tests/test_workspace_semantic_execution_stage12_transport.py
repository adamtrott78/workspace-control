from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v1.sh"
WINDOWS = ROOT / "operator-bridge/tools/run-stage12-real-instant.ps1"
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-review.v0.1.json"


class Stage12TransportStaticTests(unittest.TestCase):
    def test_linux_transaction_is_syntax_valid_and_path_specific(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        proc = subprocess.run(
            ["bash", "-n", str(LINUX)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('ROUTE_PATH="/operator-bridge/v1"', text)
        self.assertIn('http://127.0.0.1:8888', text)
        self.assertIn('--set-path="$ROUTE_PATH"', text)
        self.assertIn('http://127.0.0.1:$BACKEND_PORT$ROUTE_PATH', text)
        self.assertIn('TAILSCALE_EXISTING_CONFIG_EXACTLY_RESTORED=PASS', text)
        self.assertNotIn("tailscale serve reset", text)
        self.assertNotIn("tailscale serve --https=443 off", text)
        self.assertNotIn("tailscale funnel --bg", text)
        self.assertNotIn("0.0.0.0", text)

    def test_linux_transaction_uses_isolated_postgres_and_frozen_semantic_source(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        self.assertIn(
            'SEMANTIC_SHA="7c20097c5f177f23c16a765b95ce94d7161f0d29"',
            text,
        )
        self.assertIn("--auth-host=reject", text)
        self.assertIn("listen_addresses = ''", text)
        self.assertIn("psycopg[binary]==3.3.9", text)
        self.assertIn("live_real_instant_calibration_v1.py", text)

    def test_windows_launcher_preserves_manual_auth_and_submit_boundary(self) -> None:
        text = WINDOWS.read_text(encoding="utf-8")
        self.assertIn("STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS", text)
        self.assertIn("sign in normally", text)
        self.assertIn("Ctrl+V", text)
        self.assertIn("press Enter", text)
        self.assertIn('Read-Host', text)
        forbidden = (
            "SendKeys",
            "Set-Clipboard",
            "pyautogui",
            "selenium",
            "playwright",
            "OPENAI_API_KEY",
            "password=",
        )
        lowered = text.lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), lowered)

    def test_windows_launcher_refuses_browser_permission_widening(self) -> None:
        text = WINDOWS.read_text(encoding="utf-8")
        self.assertIn('@("nativeMessaging", "tabs", "sessions")', text)
        self.assertIn('refuses Firefox permission drift', text)
        self.assertIn('refuses content-script/page-content access', text)
        self.assertIn('refuses host-permission widening', text)

    def test_windows_launcher_uses_https_private_origin_only(self) -> None:
        text = WINDOWS.read_text(encoding="utf-8")
        self.assertIn(
            'https://gokhan-lambda-vector.tailca6171.ts.net/',
            text,
        )
        self.assertIn("--operator-bridge-url=$OperatorBridgeUrl", text)
        self.assertIn("--scheduler-hotkey=$SchedulerHotkey", text)

    def test_review_candidate_is_exact_and_not_authority(self) -> None:
        import json
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(
            review["authority_gate"]["live_real_account_authorized"]
        )
        self.assertTrue(
            review["authority_gate"]["explicit_operator_approval_required"]
        )
        bindings = review["exact_candidate_bindings"]
        self.assertEqual(
            bindings["source_head"],
            "b282ccdebae222d70454db46fc287fdc4809cd6a",
        )
        self.assertEqual(
            bindings["real_instant_harness"]["blob_sha"],
            "7b1feb8fa13cf0ea46883b07831e829fd9e7e75d",
        )
        self.assertEqual(
            bindings["linux_private_route_transaction"]["blob_sha"],
            "28248b17bc775ad938c221c240a3c7f3e204e82b",
        )
        self.assertEqual(
            bindings["windows_operator_launcher"]["blob_sha"],
            "d9d474ca6870585c9e4767f551086e17b4525fbc",
        )
        self.assertEqual(
            bindings["candidate_result_branch"]["initialization_commit"],
            "0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de",
        )
        self.assertFalse(
            bindings["candidate_result_branch"]["source_or_authority_branch"]
        )

    def test_review_preserves_real_account_and_browser_safety_boundaries(self) -> None:
        import json
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        human = review["human_interaction_boundary"]
        self.assertEqual(
            human["normal_chatgpt_authentication"],
            "MANUAL_ONLY",
        )
        self.assertEqual(
            human["worker_service_sequence"],
            "Ctrl+Space -> Ctrl+V -> Enter",
        )
        self.assertFalse(human["credential_automation"])
        self.assertFalse(human["automatic_typing"])
        self.assertFalse(human["automatic_submission"])
        browser = review["browser_boundary"]
        self.assertEqual(
            browser["allowed_extension_permissions"],
            ["nativeMessaging", "tabs", "sessions"],
        )
        self.assertFalse(browser["content_scripts"])
        self.assertFalse(browser["host_permissions"])
        self.assertFalse(browser["dom_or_page_content_scraping"])
        host = review["host_runtime_boundary"]
        self.assertEqual(host["backend_bind"], "127.0.0.1:8765")
        self.assertFalse(host["tailscale_funnel"])
        self.assertFalse(host["public_listener"])
        self.assertFalse(host["production_postgres_mutation"])
        self.assertFalse(host["gpu_required"])


if __name__ == "__main__":
    unittest.main()
