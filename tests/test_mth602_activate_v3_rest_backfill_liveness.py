import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = (ROOT / "scripts/mth602_activate_v3_rest_backfill_liveness_v1.py").read_text()
CONTROLLER = (ROOT / "controller/lambda-ci-controller/v3/controller.go").read_text()


class MTH602RestBackfillBootstrapTests(unittest.TestCase):
    def test_controller_has_bounded_rest_capacity_floor(self):
        self.assertIn(
            "Using REST-attested queued demand as bounded capacity floor",
            CONTROLLER,
        )
        self.assertIn(
            "desired = minInt(len(jobs), s.policy.MaxRunners)",
            CONTROLLER,
        )
        self.assertIn("restDesiredFloor", CONTROLLER)

    def test_launcher_selects_go_by_exact_module_compatibility(self):
        self.assertIn('"/opt/workspace-ci/go/1.26.3/bin/go"', LAUNCHER)
        self.assertIn('"/usr/local/go/bin/go"', LAUNCHER)
        self.assertIn('"GOTOOLCHAIN": "local"', LAUNCHER)
        self.assertIn('"list", "-m"', LAUNCHER)
        self.assertIn("GO_TOOLCHAIN_SELECTED=", LAUNCHER)
        self.assertIn("no installed Go compiler can parse the exact controller module", LAUNCHER)

    def test_launcher_uses_existing_transactional_controller_only_repair(self):
        self.assertIn("lambda_ci_v3_live_controller_repair_v1", LAUNCHER)
        self.assertIn("REFRESH_V3_CONTROLLER_BINARY_LIVE_V1", LAUNCHER)
        self.assertIn("previous_controller_refresh_sha256", LAUNCHER)
        self.assertIn("candidate_controller_sha256", LAUNCHER)
        self.assertIn("MTH602_V3_REST_BACKFILL_BOOTSTRAP=PASS", LAUNCHER)

    def test_launcher_does_not_mutate_policy_or_provisioner(self):
        self.assertNotIn('systemctl", "restart"', LAUNCHER)
        self.assertNotIn("PROVISIONER_UNIT", LAUNCHER)
        self.assertNotIn("root-policy.json", LAUNCHER)
        self.assertNotIn("controller_policy_sha256", LAUNCHER)
        self.assertNotIn("ledger.Put", LAUNCHER)


if __name__ == "__main__":
    unittest.main()
