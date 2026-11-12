import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEXT = (ROOT / "scripts/lambda_ci_v3_production_cutover_live.sh").read_text()


class ProductionOperatorIntegrationTests(unittest.TestCase):
    def test_refresh_is_integrated(self):
        self.assertIn("PRODUCTION_CONTROLLER_REFRESH_REQUIRED", TEXT)
        self.assertIn("PRODUCTION_CONTROLLER_BINDING=PASS", TEXT)

    def test_exact_head_ci_gate_is_integrated(self):
        self.assertIn("PRODUCTION_EXACT_HEAD_CI=PASS", TEXT)
        self.assertIn(
            "STOP_EXACT_HEAD_WORKSPACE_CONTROL_CI_NOT_GREEN",
            TEXT,
        )
        self.assertIn(
            "actions/workflows/workspace-control-validation.yml/runs",
            TEXT,
        )

    def test_terminal_ledger_wait_is_integrated(self):
        self.assertIn("wait_controller_terminal_ledger", TEXT)
        self.assertIn("PRODUCTION_CONTROLLER_LEDGER_TERMINAL=PASS", TEXT)


if __name__ == "__main__":
    unittest.main()
