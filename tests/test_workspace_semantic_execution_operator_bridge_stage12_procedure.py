from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGE12_LAUNCHER = ROOT / "operator-bridge/tools/run-stage12-real-instant.ps1"
PROCEDURE_V7 = (
    ROOT
    / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.7.md"
)
PROCEDURE_V8 = (
    ROOT
    / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.8.md"
)


class Stage12ProcedurePowerShellParseTests(unittest.TestCase):
    def test_current_stage12_launcher_uses_blank_auth_handoff_before_live_hotkey(self) -> None:
        text = STAGE12_LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("one clean blank startup tab", text)
        self.assertIn("navigate that same tab back to about:blank", text)
        self.assertIn("first live Ctrl+Space will visibly create/focus", text)
        self.assertIn("exactly one about:blank tab remains", text)
        self.assertNotIn(
            "Firefox adapter navigates the single startup tab to https://chatgpt.com/?temporary-chat=true",
            text,
        )

    def test_v07_exact_one_line_command_parses_without_execution(self) -> None:
        engine = shutil.which("powershell.exe") or shutil.which("pwsh")
        if engine is None:
            self.skipTest("PowerShell parser unavailable on this runner")

        text = PROCEDURE_V7.read_text(encoding="utf-8")
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

    def test_v08_exact_one_line_command_parses_and_has_no_backslash_variable_escape(self) -> None:
        engine = shutil.which("powershell.exe") or shutil.which("pwsh")
        if engine is None:
            self.skipTest("PowerShell parser unavailable on this runner")

        text = PROCEDURE_V8.read_text(encoding="utf-8")
        marker = "```powershell\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        command = text[start:end]
        self.assertNotIn("\\${", command)
        self.assertEqual(command.count("${env:ProgramFiles(x86)}"), 2)

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
