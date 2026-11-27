from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks/workspace-semantic-execution/private_route_existing_serve_inspect_v1.sh"


class PrivateRouteExistingServeInspectTests(unittest.TestCase):
    def test_read_only_diagnostic_is_syntax_valid_and_non_mutating(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        proc = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("tailscale serve status --json", text)
        self.assertIn("tailscale funnel status --json", text)
        self.assertIn("PRIVATE_ROUTE_EXISTING_TAILSCALE_CONFIG_READONLY=PASS", text)
        forbidden = [
            "tailscale serve --bg",
            "tailscale serve reset",
            "tailscale serve set-config",
            "tailscale funnel --bg",
            " tailscale up ",
            " tailscale down ",
            " off",
        ]
        for token in forbidden:
            self.assertNotIn(token, text, token)


if __name__ == "__main__":
    unittest.main()
