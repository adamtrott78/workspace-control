from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks/workspace-semantic-execution/private_route_fake_worker_activation_v1.sh"
REVIEW = ROOT / "architecture/workspace-semantic-execution-private-route-host-review.v0.1.json"


class PrivateRouteActivationTests(unittest.TestCase):
    def test_activation_script_is_syntax_valid_and_fail_closed(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        proc = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('SEMANTIC_SHA="7c20097c5f177f23c16a765b95ce94d7161f0d29"', text)
        self.assertIn('BASE_URL="https://gokhan-lambda-vector.tailca6171.ts.net"', text)
        self.assertIn("TAILSCALE_WINDOWS_OPERATOR_PEER_MISSING", text)
        self.assertIn("TAILSCALE_OPERATOR_OWNER_MISMATCH", text)
        self.assertIn("TAILSCALE_LOGIN_BINDING=PASS", text)
        self.assertNotIn("adamtrott78@gmail.com", text)
        self.assertIn('BACKEND_PORT="8765"', text)
        self.assertIn('sudo tailscale serve --bg --https=443 "http://127.0.0.1:$BACKEND_PORT"', text)
        self.assertIn('sudo tailscale serve --https=443 off', text)
        self.assertIn('sudo tailscale funnel status --json', text)
        self.assertIn('listen_addresses = \'\'', text)
        self.assertIn('--auth-host=reject', text)
        self.assertIn('psycopg[binary]==3.3.9', text)
        self.assertNotIn("0.0.0.0", text)
        self.assertNotIn("tailscale funnel --bg", text)
        self.assertNotIn("OPENAI_API_KEY", text)
        self.assertNotIn("CUDA", text)

    def test_activation_script_uses_ephemeral_local_postgres_and_exact_harness(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('RUNTIME_ROOT="/tmp/workspace-semantic-execution-private-route-v1"', text)
        self.assertIn('PG_PREFIX="/opt/workspace-ci/postgresql/postgresql-14.24-pgvector-0.8.6"', text)
        self.assertIn('git -C "$ROOT" archive "$SEMANTIC_SHA"', text)
        self.assertIn('live_fake_worker_transport_v1.py', text)
        self.assertIn('--base-url "$BASE_URL"', text)
        self.assertIn('--serve-port "$BACKEND_PORT"', text)
        self.assertIn('PRIVATE_ROUTE_FAKE_WORKER_ACCEPTANCE=PASS', text)

    def test_host_review_binds_route_without_persisting_private_values(self) -> None:
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_activation_authorized"])
        self.assertEqual(
            review["host_bindings"]["reviewed_private_base_url"],
            "https://gokhan-lambda-vector.tailca6171.ts.net",
        )
        login = review["host_bindings"]["expected_tailscale_login_value"]
        self.assertEqual(login["persistence"], "RUNTIME_ONLY_NOT_COMMITTED_NOT_LOGGED")
        dsn = review["host_bindings"]["postgres_dsn_value"]
        self.assertEqual(dsn["persistence"], "RUNTIME_ONLY_NOT_COMMITTED_NOT_LOGGED")
        self.assertFalse(dsn["host_tcp_listener"])
        self.assertEqual(dsn["auth_host"], "reject")
        self.assertFalse(dsn["production_database_touched"])
        mechanism = review["host_bindings"]["exact_authorized_activation_mechanism"]
        self.assertTrue(mechanism["requires_explicit_operator_approval_of_exact_candidate"])
        self.assertEqual(
            mechanism["candidate_commit"],
            "8116662727003e9fe0904fa88ff7836608aeac00",
        )
        serialized = REVIEW.read_text(encoding="utf-8")
        self.assertNotIn("adamtrott78@gmail.com", serialized)
        self.assertNotIn("OPENAI_API_KEY", serialized)


if __name__ == "__main__":
    unittest.main()
