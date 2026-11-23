from __future__ import annotations

import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINUX = ROOT / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"


class Stage12V113StaleRouteTests(unittest.TestCase):
    def test_transaction_is_bash_syntax_valid(self) -> None:
        proc = subprocess.run(
            ["bash", "-n", str(LINUX)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_exact_stale_route_is_normalized_before_clean_snapshot(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        observed = text.index('sudo tailscale serve status --json >"$SERVE_OBSERVED"')
        stale = text.index('if [[ "$STALE_ROUTE_STATE" == "EXACT_STALE_ROUTE" ]]')
        cleared = text.index('echo "TAILSCALE_STALE_STAGE12_ROUTE_CLEARED=PASS"')
        clean = text.index('sudo tailscale serve status --json >"$SERVE_BEFORE"')
        semantic = text.index('echo "STAGE12_SEMANTIC_LIVE_BINDING=PASS"')
        consumed = text.index('echo "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"')
        self.assertLess(observed, stale)
        self.assertLess(stale, cleared)
        self.assertLess(cleared, clean)
        self.assertLess(clean, semantic)
        self.assertLess(semantic, consumed)

    def test_stale_route_cleanup_is_fail_closed(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        self.assertIn('ROUTE_PROXY="http://127.0.0.1:8765/operator-bridge/v1"', text)
        self.assertIn("STALE_STAGE12_ROUTE_BACKEND_LISTENER_PRESENT", text)
        self.assertIn("STALE_STAGE12_ROUTE_CLEAR_FAILED", text)
        self.assertIn("UNEXPECTED_HANDLER_SET", text)
        self.assertIn("STAGE12_ROUTE_PROXY_MISMATCH", text)
        self.assertIn("AMBIGUOUS_STAGE12_ROUTE", text)
        self.assertIn('sudo ss -H -ltn', text)
        self.assertNotIn("tailscale serve reset", text)
        self.assertNotIn("tailscale serve --https=443 off", text)

    def test_clean_rollback_snapshot_remains_root_only(self) -> None:
        text = LINUX.read_text(encoding="utf-8")
        self.assertIn("CLEAN_ROOT_MAPPING_MISMATCH", text)
        self.assertIn("STAGE12_ROUTE_STILL_PRESENT", text)
        self.assertIn("TAILSCALE_EXISTING_CONFIG_EXACTLY_RESTORED=PASS", text)


if __name__ == "__main__":
    unittest.main()
