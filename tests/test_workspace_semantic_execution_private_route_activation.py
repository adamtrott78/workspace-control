"""Contract tests for private Operator Bridge route activation proposal."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "architecture"
    / "workspace-semantic-execution-private-route-activation.v0.1.json"
)
SERVER_PATH = (
    ROOT
    / "semantic-execution"
    / "src"
    / "workspace_semantic_execution"
    / "operator_bridge_server.py"
)


class PrivateRouteActivationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_proposal_is_non_authoritative_and_fail_closed(self):
        self.assertEqual(self.contract["status"], "PROPOSAL_NOT_AUTHORITY")
        gate = self.contract["authority_gate"]
        self.assertFalse(gate["live_activation_authorized"])
        self.assertTrue(gate["requires_explicit_operator_approved_host_activation"])
        self.assertTrue(gate["requires_reviewed_network_or_helper_route"])
        self.assertFalse(gate["generic_shell_bypass"])
        self.assertFalse(gate["manual_sidecar_bypass"])
        self.assertFalse(gate["workspace_shell_profile_widening"])
        self.assertFalse(gate["helper_registry_widening"])

    def test_exact_loopback_transport_binding_matches_server_contract(self):
        backend = self.contract["proposed_backend_binding"]
        self.assertEqual(backend["bind_host"], "127.0.0.1")
        self.assertEqual(backend["port"], 8765)
        self.assertEqual(backend["state_key"], "control")
        self.assertEqual(backend["base_path"], "/operator-bridge/v1")
        transport = self.contract["proposed_transport"]
        self.assertEqual(transport["mode"], "TAILSCALE_SERVE_PRIVATE_HTTPS")
        self.assertFalse(transport["public_internet"])
        self.assertFalse(transport["tailscale_funnel"])
        self.assertFalse(transport["backend_non_loopback_listener"])
        self.assertEqual(transport["identity_header"], "Tailscale-User-Login")

        source = SERVER_PATH.read_text(encoding="utf-8")
        self.assertIn('port: int = 8765', source)
        self.assertIn('state_key: str = "control"', source)
        self.assertIn('bind_host="127.0.0.1"', source)
        self.assertIn('expected_identity_header="Tailscale-User-Login"', source)

    def test_runtime_secrets_are_required_but_never_committed_as_values(self):
        runtime = {item["name"]: item for item in self.contract["required_runtime_inputs"]}
        self.assertFalse(runtime["SEMANTIC_EXECUTION_POSTGRES_DSN"]["persist_in_git"])
        self.assertFalse(runtime["SEMANTIC_EXECUTION_POSTGRES_DSN"]["log_value"])
        self.assertFalse(runtime["WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN"]["persist_in_git"])
        self.assertFalse(runtime["WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN"]["log_value"])
        serialized = json.dumps(self.contract)
        self.assertNotIn("postgresql://", serialized)
        self.assertNotIn("@example", serialized)

    def test_fake_worker_scope_is_account_model_browser_and_gpu_free(self):
        acceptance = self.contract["fake_worker_acceptance"]
        self.assertFalse(acceptance["model_inference"])
        self.assertFalse(acceptance["browser_automation"])
        self.assertFalse(acceptance["gpu_required"])
        self.assertFalse(acceptance["real_chatgpt_account"])
        self.assertEqual(acceptance["required_result"], "PASS")
        self.assertEqual(
            acceptance["required_flow"][-1],
            "status_ready_0_sent_0",
        )

    def test_unresolved_host_values_remain_explicit(self):
        self.assertEqual(
            set(self.contract["unresolved_host_bindings"]),
            {
                "reviewed_private_base_url",
                "expected_tailscale_login_value",
                "postgres_dsn_value",
                "exact_authorized_activation_mechanism",
            },
        )


if __name__ == "__main__":
    unittest.main()
