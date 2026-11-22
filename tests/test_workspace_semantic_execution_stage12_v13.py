from __future__ import annotations

import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "operator-bridge/tools/install-wop-commands.ps1"
DEV = ROOT / "operator-bridge/tools/workspace-operator-dev.ps1"
WOP = ROOT / "operator-bridge/tools/run-stage12-wop.ps1"
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"
TRAY = ROOT / "operator-bridge/src/WorkspaceOperator/Windows/TrayApplicationContext.cs"
PROCEDURE = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.3.md"

class Stage12V13WopRepairTests(unittest.TestCase):
    def test_long_term_command_is_wop_d4(self) -> None:
        installer = INSTALLER.read_text(encoding="utf-8")
        procedure = PROCEDURE.read_text(encoding="utf-8")
        self.assertIn('"wop-d4"', installer)
        self.assertIn('"wop-d4" = "d4"', installer)
        self.assertIn("wop d4", procedure)

    def test_bootstrap_works_with_old_driver_online_action(self) -> None:
        text = DEV.read_text(encoding="utf-8")
        self.assertIn('"online" {', text)
        self.assertIn("install-wop-commands.ps1", text)
        self.assertIn("run-stage12-wop.ps1", text)

    def test_dev_runtime_requires_actual_bridge_enabled_receipt(self) -> None:
        text = DEV.read_text(encoding="utf-8")
        self.assertIn("WORKSPACE_OPERATOR_BRIDGE_ENABLED=PASS", text)
        self.assertIn("DEV_HOTKEY_REGISTRATION_NOT_CONFIRMED", text)
        self.assertIn("Select-String", text)

    def test_hotkey_dispatch_failures_are_visible(self) -> None:
        text = TRAY.read_text(encoding="utf-8")
        self.assertIn("Dispatch failed closed:", text)
        self.assertIn("ToolTipIcon.Warning", text)
        self.assertIn("DispatchOutcome.Failed", text)

    def test_wop_runs_linux_half_over_existing_ssh_path(self) -> None:
        text = WOP.read_text(encoding="utf-8")
        self.assertIn("atrott@gokhan-lambda-vector.tailca6171.ts.net", text)
        self.assertIn("ssh.exe", text)
        self.assertIn("D4_WOP_REMOTE_EXACT_BINDINGS=PASS", text)
        self.assertIn("STAGE12_WINDOWS_READY_CONFIRMATION", text)
        self.assertNotIn("SendKeys", text)

    def test_linux_v4_is_noninteractive_for_windows_marker_only(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        self.assertIn('WINDOWS_READY="${STAGE12_WINDOWS_READY_CONFIRMATION:-}"', text)
        self.assertNotIn("read -r -p", text)
        self.assertIn("STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS", text)
        self.assertIn("PRIVATE_ROUTE_STAGE12_REAL_INSTANT_V3=PASS", text)

    def test_linux_v4_bash_syntax(self) -> None:
        proc = subprocess.run(["bash","-n",str(LINUX)],cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(proc.returncode,0,proc.stderr)

if __name__ == "__main__":
    unittest.main()
