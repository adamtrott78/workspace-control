from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks/workspace-semantic-execution/private_route_fake_worker_activation_v2.sh"


class PrivateRouteActivationV2Tests(unittest.TestCase):
    def test_path_coexistence_transaction_is_syntax_valid(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        proc = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('ROUTE_PATH="/operator-bridge/v1"', text)
        self.assertIn('EXISTING_ROOT_PROXY="http://127.0.0.1:8888"', text)
        self.assertIn(
            'sudo tailscale serve --bg --https=443 --set-path="$ROUTE_PATH"',
            text,
        )
        self.assertIn(
            '"http://127.0.0.1:$BACKEND_PORT$ROUTE_PATH"',
            text,
        )
        self.assertIn(
            'sudo tailscale serve --https=443 --set-path="$ROUTE_PATH" off',
            text,
        )

    def test_existing_jupyter_mapping_is_preserved_and_exactly_restored(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("TAILSCALE_EXISTING_JUPYTER_ROOT_BINDING=PASS", text)
        self.assertIn("TAILSCALE_JUPYTER_ROOT_PRESERVED=PASS", text)
        self.assertIn("TAILSCALE_EXISTING_CONFIG_EXACTLY_RESTORED=PASS", text)
        self.assertIn("TAILSCALE_JUPYTER_ROOT_ROLLBACK_PRESERVED=PASS", text)
        self.assertIn('handlers != {"/":{"Proxy":ROOT_PROXY}}', text)
        self.assertIn('root != "http://127.0.0.1:8888"', text)
        self.assertIn("serve_after != serve_before", text)
        self.assertIn("funnel_after != funnel_before", text)

    def test_transaction_does_not_use_global_serve_reset_or_global_off(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("tailscale serve reset", text)
        self.assertNotIn("tailscale funnel --bg", text)
        self.assertNotIn("tailscale funnel reset", text)
        self.assertNotIn("tailscale serve --https=443 off", text)
        self.assertNotIn("tailscale serve off", text)
        self.assertNotIn("0.0.0.0", text)
        self.assertNotIn("OPENAI_API_KEY", text)

    def test_fake_worker_scope_remains_account_model_browser_gpu_free(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("live_fake_worker_transport_v1.py", text)
        self.assertIn("PRIVATE_ROUTE_FAKE_WORKER_ACCEPTANCE_V2=PASS", text)
        self.assertNotIn("CUDA_VISIBLE_DEVICES", text)
        self.assertNotIn("chat.openai.com", text)
        self.assertNotIn("chatgpt.com", text)


if __name__ == "__main__":
    unittest.main()
