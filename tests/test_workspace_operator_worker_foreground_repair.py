from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-operator-worker-foreground-repair.v0.1.json"
SOURCE = ROOT / "operator-bridge/src/WorkspaceOperator/Windows/Win32WorkerWindowSafetyPort.cs"


class OperatorWorkerForegroundRepairTests(unittest.TestCase):
    def test_review_grants_zero_authority(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        gate = review["authority_gate"]
        self.assertFalse(gate["live_authorized"])
        self.assertFalse(gate["retry_authorized"])
        self.assertTrue(gate["fresh_explicit_authority_required"])

    def test_foreground_path_is_bounded_and_uses_attached_input_only_as_fallback(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        ordinary = text.index("if (TryActivateForeground(window))")
        fallback = text.index("return TryActivateForegroundWithAttachedInput(window);")
        self.assertLess(ordinary, fallback)
        self.assertIn("BringWindowToTop(window)", text)
        self.assertIn("SetForegroundWindow(window)", text)
        self.assertIn("AttachThreadInput(", text)
        self.assertIn("finally", text)
        self.assertIn("WaitForForeground(window)", text)
        self.assertIn("attempt < 12", text)

    def test_repair_does_not_add_input_injection_or_page_access(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        forbidden = (
            "SendInput",
            "mouse_event",
            "keybd_event",
            "PostMessage",
            "SendMessage",
            "Clipboard",
            "WebView",
            "document.",
            "querySelector",
        )
        for token in forbidden:
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
