from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v1.sh"
WINDOWS = ROOT / "operator-bridge/tools/run-stage12-real-instant.ps1"


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


if __name__ == "__main__":
    unittest.main()
