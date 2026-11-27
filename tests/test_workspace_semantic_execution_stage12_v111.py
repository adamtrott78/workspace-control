from __future__ import annotations

import re
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"
BACKEND_PATH = "semantic-execution/src/workspace_semantic_execution/adapters/operator_bridge_http.py"
EXPECTED_SEMANTIC_SHA = "020d35156d90e8268fb560a10e67098a146880de"
EXPECTED_BACKEND_BLOB = "3b6893c157c9f567c837aa70c110012eb96ee18c"


class Stage12V111LiveBindingTests(unittest.TestCase):
    def git(self, spec: str) -> str:
        return subprocess.check_output(
            ["git", "rev-parse", spec],
            cwd=ROOT,
            text=True,
        ).strip()

    def test_live_transaction_binds_validated_semantic_repair(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        self.assertIn(f'SEMANTIC_SHA="{EXPECTED_SEMANTIC_SHA}"', text)
        self.assertIn(
            f'EXPECTED_OPERATOR_HTTP_BLOB="{EXPECTED_BACKEND_BLOB}"',
            text,
        )
        self.assertEqual(
            self.git(f"{EXPECTED_SEMANTIC_SHA}:{BACKEND_PATH}"),
            EXPECTED_BACKEND_BLOB,
        )

    def test_live_semantic_binding_is_proven_before_consumption(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        binding = text.index('echo "STAGE12_SEMANTIC_LIVE_BINDING=PASS"')
        windows_gate = text.index('echo "STAGE12_WINDOWS_READY_GATE=PASS"')
        consumption = text.index(
            'echo "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"'
        )
        archive = text.index(
            'git -C "$ROOT" archive "$SEMANTIC_SHA" semantic-execution'
        )
        self.assertLess(binding, windows_gate)
        self.assertLess(binding, consumption)
        self.assertLess(consumption, archive)
        self.assertIn("LIVE_SEMANTIC_OPERATOR_HTTP_BLOB_MISMATCH", text)

    def test_live_transaction_is_bash_syntax_valid(self) -> None:
        proc = subprocess.run(
            ["bash", "-n", str(LINUX)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
