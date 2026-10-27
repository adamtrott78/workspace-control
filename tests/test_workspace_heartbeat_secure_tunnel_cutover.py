import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "workspace_heartbeat_secure_tunnel_cutover.sh"


class WorkspaceHeartbeatSecureTunnelCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SCRIPT.read_text()

    def test_shell_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_pins_accepted_runtime_and_tunnel(self):
        self.assertIn(
            'CANDIDATE_SHA="def7c5fe6498b1bd742d912c1490d1f7160cab5f"',
            self.text,
        )
        self.assertIn(
            'ROLLBACK_SHA="9e5858738a4fd11801510e2839b0f94f19541506"',
            self.text,
        )
        self.assertIn(
            'TUNNEL_ID="tunnel_6ae017d8655c8191976ef3bccc31f593"',
            self.text,
        )
        self.assertIn("workspace-heartbeat-runtime-v048", self.text)
        self.assertIn("workspace-heartbeat-runtime-v047", self.text)

    def test_secret_is_file_referenced_and_mode_locked(self):
        self.assertIn("--control-plane-api-key-ref", self.text)
        self.assertIn('"file:$SECRET_FILE"', self.text)
        self.assertIn('chmod 600 "$SECRET_FILE"', self.text)
        self.assertIn('expected 600', self.text)
        self.assertNotRegex(self.text, r"sk-[A-Za-z0-9]")

    def test_refuses_parallel_acceptance_tunnel(self):
        self.assertIn(
            "stop the isolated acceptance tunnel (Ctrl-C in its terminal) before production cutover",
            self.text,
        )

    def test_preserves_explicit_v047_ngrok_rollback(self):
        self.assertIn("heartbeat-up.v047-ngrok.rollback", self.text)
        self.assertIn("heartbeat-rollback-v047-ngrok", self.text)
        self.assertIn("rollback was attempted", self.text)

    def test_normal_launcher_uses_tunnel_window_and_readiness(self):
        self.assertIn('-n tunnel', self.text)
        self.assertIn('/readyz', self.text)
        self.assertIn(
            "WORKSPACE_HEARTBEAT_V048_TUNNEL_CUTOVER_LOCAL_GATE=PASS",
            self.text,
        )


if __name__ == "__main__":
    unittest.main()
