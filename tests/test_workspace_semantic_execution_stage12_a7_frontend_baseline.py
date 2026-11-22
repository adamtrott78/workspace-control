from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "architecture/workspace-operator-bridge-a7-frontend-baseline.v0.1.json"
WOP = ROOT / "operator-bridge/tools/run-stage12-wop.ps1"
BOOT = ROOT / "operator-bridge/tools/run-stage12-remote-bootstrap.sh"

class D4AcceptedFrontendBaselineTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(["git","rev-parse",spec], cwd=ROOT, text=True).strip()

    def test_exact_a7_runtime_tree_is_restored(self) -> None:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertEqual(self.git("HEAD:operator-bridge/src"), baseline["exact_runtime_bindings"]["operator-bridge/src_tree"])
        self.assertEqual(self.git("HEAD:operator-bridge/tools/workspace-operator-dev.ps1"), baseline["exact_runtime_bindings"]["operator-bridge/tools/workspace-operator-dev.ps1"])

    def test_d4_waits_for_ready_action_before_frontend_launch(self) -> None:
        text = WOP.read_text(encoding="utf-8")
        self.assertIn("readyManualCycles", text)
        self.assertIn("D4_BACKEND_READY_ACTION_TIMEOUT", text)
        self.assertIn("-OperatorBridgeUrl $Url", text)
        self.assertIn("D4_FRONTEND_TREE_NOT_ACCEPTED_A7", text)

    def test_remote_bootstrap_expands_bash_variables(self) -> None:
        text = BOOT.read_text(encoding="utf-8")
        self.assertIn('D="/tmp/workspace-stage12-wop-${TOKEN}"', text)
        self.assertIn('"${SOURCE_SHA}:${LINUX_REL}"', text)
        self.assertNotIn(r"\${TOKEN}", text)
        proc = subprocess.run(["bash","-n",str(BOOT)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(proc.returncode,0,proc.stderr)

if __name__ == "__main__":
    unittest.main()
