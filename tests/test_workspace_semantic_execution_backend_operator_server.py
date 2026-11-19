"""Production Operator Bridge server configuration tests."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.operator_bridge_server import (  # noqa: E402
    OperatorBridgeServerConfig,
)


BASE_ENV = {
    "SEMANTIC_EXECUTION_POSTGRES_DSN": (
        "postgresql://user:very-secret@127.0.0.1/control"
    ),
    "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN": (
        "operator@example.invalid"
    ),
}


class OperatorBridgeServerConfigTests(unittest.TestCase):
    def test_required_configuration_fails_closed(self):
        for missing in (
            "SEMANTIC_EXECUTION_POSTGRES_DSN",
            "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN",
        ):
            env = dict(BASE_ENV)
            env.pop(missing)
            with self.assertRaises(ValueError):
                OperatorBridgeServerConfig.from_env(env)

    def test_defaults_are_bounded_and_secrets_are_redacted_from_repr(self):
        config = OperatorBridgeServerConfig.from_env(BASE_ENV)

        self.assertEqual(config.state_key, "control")
        self.assertEqual(config.port, 8765)
        self.assertEqual(config.max_body_bytes, 16_384)
        rendered = repr(config)
        self.assertNotIn("very-secret", rendered)
        self.assertNotIn("operator@example.invalid", rendered)

    def test_explicit_bounded_configuration_parses(self):
        env = dict(
            BASE_ENV,
            SEMANTIC_EXECUTION_STATE_KEY="operator:preflight",
            WORKSPACE_OPERATOR_BRIDGE_PORT="9443",
            WORKSPACE_OPERATOR_BRIDGE_MAX_BODY_BYTES="32768",
        )
        config = OperatorBridgeServerConfig.from_env(env)

        self.assertEqual(config.state_key, "operator:preflight")
        self.assertEqual(config.port, 9443)
        self.assertEqual(config.max_body_bytes, 32_768)

    def test_unsafe_state_key_port_body_or_identity_fails_closed(self):
        cases = (
            {"SEMANTIC_EXECUTION_STATE_KEY": "../escape"},
            {"WORKSPACE_OPERATOR_BRIDGE_PORT": "80"},
            {"WORKSPACE_OPERATOR_BRIDGE_PORT": "70000"},
            {"WORKSPACE_OPERATOR_BRIDGE_MAX_BODY_BYTES": "32"},
            {
                "WORKSPACE_OPERATOR_EXPECTED_TAILSCALE_LOGIN":
                    "operator\nspoof"
            },
        )
        for override in cases:
            env = dict(BASE_ENV)
            env.update(override)
            with self.assertRaises(ValueError):
                OperatorBridgeServerConfig.from_env(env)

    def test_header_and_bind_host_are_not_environment_configurable(self):
        env = dict(
            BASE_ENV,
            WORKSPACE_OPERATOR_BRIDGE_BIND_HOST="0.0.0.0",
            WORKSPACE_OPERATOR_IDENTITY_HEADER="Authorization",
        )
        config = OperatorBridgeServerConfig.from_env(env)

        self.assertFalse(
            hasattr(config, "bind_host"),
            "bind host must stay hard-coded to loopback",
        )
        self.assertFalse(
            hasattr(config, "identity_header"),
            "proxy identity header must stay hard-coded",
        )


if __name__ == "__main__":
    unittest.main()
