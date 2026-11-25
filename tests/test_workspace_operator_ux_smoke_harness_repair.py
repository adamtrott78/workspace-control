from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-operator-ux-smoke-harness-repair.v0.1.json"
DEV = ROOT / "operator-bridge/tools/workspace-operator-dev.ps1"
PORT = ROOT / "operator-bridge/src/WorkspaceOperator/Bootstrap/LocalSmokeOperatorActionPort.cs"
PROGRAM = ROOT / "operator-bridge/src/WorkspaceOperator/Program.cs"


class OperatorUxSmokeHarnessRepairTests(unittest.TestCase):
    def test_review_grants_zero_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        gate = review["authority_gate"]
        self.assertFalse(gate["live_authorized"])
        self.assertFalse(gate["retry_authorized"])
        self.assertTrue(gate["fresh_explicit_authority_required"])

    def test_smoke_waits_for_fresh_adapter_handshake_before_ready(self) -> None:
        text = DEV.read_text(encoding="utf-8")
        self.assertIn("function Test-BrowserAdapterConnectedSince", text)
        self.assertIn("browser_command_hub", text)
        self.assertIn("adapter_connected", text)
        self.assertIn("DEV_FIREFOX_ADAPTER_HANDSHAKE_TIMEOUT", text)
        self.assertIn("WORKSPACE_OPERATOR_BROWSER_ADAPTER_CONNECTED=PASS", text)
        self.assertLess(
            text.index("WORKSPACE_OPERATOR_BROWSER_ADAPTER_CONNECTED=PASS"),
            text.index("WORKSPACE_OPERATOR_SMOKE_READY="),
        )

    def test_helper_is_self_contained_and_staged_outside_checkout(self) -> None:
        text = DEV.read_text(encoding="utf-8")
        self.assertIn("--runtime win-x64 --self-contained true", text)
        self.assertIn('$helperDir = Join-Path $runtimeRoot ("helper-" + $buildTree)', text)
        self.assertIn('$helper = Join-Path $helperDir "WorkspaceOperator.exe"', text)
        self.assertNotIn(
            '$helper = Join-Path $bridgeRoot "src\\WorkspaceOperator\\bin\\Release\\net10.0-windows\\WorkspaceOperator.exe"',
            text,
        )

    def test_smoke_projects_pending_ack_after_local_prepared(self) -> None:
        port = PORT.read_text(encoding="utf-8")
        program = PROGRAM.read_text(encoding="utf-8")
        self.assertIn("public bool HasSentUnconfirmed", port)
        self.assertIn("Volatile.Read(ref _state) == 2", port)
        self.assertIn(
            "localSmokePort.HasSentUnconfirmed ? 1 : 0",
            program,
        )

    def test_smoke_instructions_cover_enter_and_pending_ack_check(self) -> None:
        text = DEV.read_text(encoding="utf-8")
        self.assertIn("After Ctrl+V then Enter", text)
        self.assertIn("should minimize", text)
        self.assertIn("pending durable acknowledgment without refocusing Firefox", text)


if __name__ == "__main__":
    unittest.main()
