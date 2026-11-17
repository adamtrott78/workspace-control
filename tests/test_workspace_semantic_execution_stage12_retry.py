from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
LINUX_V2 = (
    ROOT
    / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v2.sh"
)
REVIEW_V2 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v0.2.json"
PROCEDURE_V2 = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v0.2.md"


class Stage12RetryTransactionStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = LINUX_V2.read_text(encoding="utf-8")

    def test_v2_transaction_is_bash_syntax_valid(self) -> None:
        proc = subprocess.run(
            ["bash", "-n", str(LINUX_V2)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_windows_readiness_gate_precedes_live_mutation(self) -> None:
        marker = 'echo "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"'
        self.assertIn(
            'WINDOWS_READY_MARKER="STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"',
            self.text,
        )
        self.assertIn('read -r -p', self.text)
        self.assertIn('WINDOWS_READY_CONFIRMATION_MISMATCH', self.text)
        gate = self.text.index(marker)
        for live_mutation in (
            'python3 -m venv "$VENV"',
            '"$PG_PREFIX/bin/initdb"',
            'sudo tailscale serve --bg',
            '"$HARNESS_REL"       --serve-port',
        ):
            self.assertGreater(
                self.text.index(live_mutation),
                gate,
                live_mutation,
            )

    def test_candidate_baseline_is_rechecked_before_arm(self) -> None:
        baseline_check = self.text.index("STAGE12_CANDIDATE_BASELINE=PASS")
        gate = self.text.index("STAGE12_WINDOWS_READY_GATE=PASS")
        self.assertLess(baseline_check, gate)
        self.assertIn(
            'CANDIDATE_BASELINE="0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de"',
            self.text,
        )
        self.assertIn(
            'git ls-remote "$REPO_URL" refs/heads/worker-result-candidates-v1',
            self.text,
        )

    def test_abort_cleanup_verifies_exact_snapshot_restoration(self) -> None:
        self.assertIn("verify_restored_snapshot()", self.text)
        self.assertIn("STAGE12_CLEANUP_ROUTE_RESTORED=PASS", self.text)
        self.assertIn("STAGE12_CLEANUP_ROUTE_RESTORED=FAIL", self.text)
        self.assertIn("STAGE12_CLEANUP_EVIDENCE_PRESERVED=", self.text)
        self.assertIn("SERVE_ROLLBACK_MISMATCH", self.text)
        self.assertIn("FUNNEL_ROLLBACK_MISMATCH", self.text)

    def test_v2_retains_private_route_and_no_widening(self) -> None:
        self.assertIn('ROUTE_PATH="/operator-bridge/v1"', self.text)
        self.assertIn('http://127.0.0.1:8888', self.text)
        self.assertIn('--set-path="$ROUTE_PATH"', self.text)
        self.assertNotIn("tailscale serve reset", self.text)
        self.assertNotIn("tailscale serve --https=443 off", self.text)
        self.assertNotIn("tailscale funnel --bg", self.text)
        self.assertNotIn("0.0.0.0", self.text)
        self.assertIn("PRIVATE_ROUTE_STAGE12_REAL_INSTANT_V2=PASS", self.text)

    def test_retry_review_is_not_authority_and_binds_exact_candidate(self) -> None:
        import json

        review = json.loads(REVIEW_V2.read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY")
        self.assertFalse(review["authority_gate"]["live_retry_authorized"])
        self.assertTrue(
            review["authority_gate"]["explicit_fresh_operator_approval_required"]
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["executable_source_head"],
            "b0466c03acb9d6b863df421e2c116c84bff312f6",
        )
        self.assertEqual(
            review["exact_candidate_bindings"]["linux_private_route_transaction"]["blob_sha"],
            "962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca",
        )

    def test_retry_procedure_eliminates_multiline_windows_launch(self) -> None:
        text = PROCEDURE_V2.read_text(encoding="utf-8")
        self.assertIn("single executable line", text)
        self.assertIn(
            "STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS",
            text,
        )
        self.assertIn(
            "STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS",
            text,
        )
        self.assertNotIn("try {", text)
        self.assertNotIn("finally {", text)


if __name__ == "__main__":
    unittest.main()
