"""Contract tests for the live fake-worker transport harness."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "live_fake_worker_transport_v1.py"
)


class LiveFakeWorkerTransportHarnessTests(unittest.TestCase):
    def test_describe_is_account_free_gpu_free_and_content_free(self):
        cp = subprocess.run(
            [sys.executable, str(HARNESS), "--describe"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        contract = json.loads(cp.stdout)
        self.assertFalse(contract["model_inference"])
        self.assertFalse(contract["browser_automation"])
        self.assertFalse(contract["gpu_required"])
        self.assertEqual(contract["backend_bind"], "127.0.0.1")
        self.assertIn(
            "immutable_fake_candidate_intake",
            contract["required_flow"],
        )
        serialized = json.dumps(contract)
        self.assertNotIn("postgresql://", serialized)
        self.assertNotIn("@example", serialized)

    def test_private_route_requires_explicit_backend_port(self):
        cp = subprocess.run(
            [
                sys.executable,
                str(HARNESS),
                "--base-url",
                "https://operator.invalid",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
            env={},
        )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn(
            "--serve-port is required with --base-url",
            cp.stderr + cp.stdout,
        )

    def test_harness_never_configures_tailscale_or_accepts_identity_override(self):
        source = HARNESS.read_text(encoding="utf-8")
        self.assertNotIn("tailscale serve", source.lower())
        self.assertNotIn("subprocess.run", source)
        self.assertNotIn("--identity", source)
        self.assertIn(
            "request_identity = None if base_url",
            source,
        )
        self.assertIn(
            '"Tailscale-User-Login"',
            source,
        )


if __name__ == "__main__":
    unittest.main()
