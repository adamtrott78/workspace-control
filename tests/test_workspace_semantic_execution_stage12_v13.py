from __future__ import annotations

import shutil
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

    def test_v13_frontend_edits_are_superseded_by_accepted_a7_baseline(self) -> None:
        dev_blob = subprocess.check_output(
            ["git","rev-parse","a9532ca8b86b7839822939a970e16af1d4a41864:operator-bridge/tools/workspace-operator-dev.ps1"],
            cwd=ROOT,
            text=True,
        ).strip()
        tray_blob = subprocess.check_output(
            ["git","rev-parse","a9532ca8b86b7839822939a970e16af1d4a41864:operator-bridge/src/WorkspaceOperator/Windows/TrayApplicationContext.cs"],
            cwd=ROOT,
            text=True,
        ).strip()
        self.assertEqual(dev_blob, "ac035d2fc898274c32cad43954ce44c15b198207")
        self.assertEqual(tray_blob, "b86e04065b354b8aa54ee2a9ca3e71ab555cde7c")
        self.assertNotIn("Dispatch failed closed:", TRAY.read_text(encoding="utf-8"))

    def test_wop_runs_linux_half_over_existing_ssh_path(self) -> None:
        text = WOP.read_text(encoding="utf-8")
        remote = (ROOT / "operator-bridge/tools/run-stage12-remote-bootstrap.sh").read_text(encoding="utf-8")
        self.assertIn("atrott@gokhan-lambda-vector.tailca6171.ts.net", text)
        self.assertIn("ssh.exe", text)
        self.assertIn("run-stage12-remote-bootstrap.sh", text)
        self.assertIn("[System.IO.File]::ReadAllText", text)
        self.assertIn('Replace("`r`n","`n").Replace("`r","`n")', text)
        self.assertNotIn("$remoteTemplate", text)
        self.assertIn("D4_WOP_REMOTE_EXACT_BINDINGS=PASS", remote)
        self.assertIn("STAGE12_WINDOWS_READY_CONFIRMATION", remote)
        self.assertNotIn("SendKeys", text)

    def test_wop_powershell_parses_when_parser_available(self) -> None:
        engine = shutil.which("powershell.exe") or shutil.which("pwsh")
        if engine is None:
            self.skipTest("PowerShell parser unavailable on this runner")
        script = WOP.read_text(encoding="utf-8")
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
            input=script,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_linux_v4_is_noninteractive_for_windows_marker_only(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        self.assertIn('WINDOWS_READY="${STAGE12_WINDOWS_READY_CONFIRMATION:-}"', text)
        self.assertNotIn("read -r -p", text)
        self.assertIn("STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS", text)
        self.assertIn("PRIVATE_ROUTE_STAGE12_REAL_INSTANT_V3=PASS", text)

    def test_linux_v4_bash_syntax(self) -> None:
        proc = subprocess.run(["bash","-n",str(LINUX)],cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(proc.returncode,0,proc.stderr)


class Stage12V15ParserSafeTransportTests(unittest.TestCase):
    def test_remote_bootstrap_is_checked_in_and_bash_valid(self) -> None:
        bootstrap = ROOT / "operator-bridge/tools/run-stage12-remote-bootstrap.sh"
        self.assertTrue(bootstrap.is_file())
        proc = subprocess.run(
            ["bash", "-n", str(bootstrap)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_wop_has_no_embedded_bash_here_string(self) -> None:
        text = WOP.read_text(encoding="utf-8")
        self.assertNotIn("$remoteTemplate", text)
        self.assertIn("run-stage12-remote-bootstrap.sh", text)
        self.assertIn("[System.IO.File]::ReadAllText", text)

    def test_operator_validation_parses_stage12_wop_in_windows_powershell(self) -> None:
        workflow = (ROOT / ".github/workflows/operator-bridge-validation.yml").read_text(encoding="utf-8")
        self.assertIn('"operator-bridge/tools/run-stage12-wop.ps1"', workflow)


if __name__ == "__main__":
    unittest.main()
