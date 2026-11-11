import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "controller/lambda-ci-controller/cmd/v3-legacy-retire/main.go"
).read_text(encoding="utf-8")
MIGRATION_PLAN = (
    ROOT / "architecture/lambda-ci-v3-migration-plan.v1.json"
).read_text(encoding="utf-8")


class LegacyScaleSetRetirementTests(unittest.TestCase):
    def test_scope_is_only_production_accepted_legacy_scale_sets(self):
        for name in (
            '"lambda-workspace-control"',
            '"lambda-padataset"',
            '"lambda-padataset-gpu"',
        ):
            self.assertIn(name, SOURCE)
        self.assertIn(
            'preservedUnacceptedLegacyScaleSets = []string{',
            SOURCE,
        )
        for name in (
            '"lambda-research-engine"',
            '"lambda-research-engine-gpu"',
        ):
            self.assertIn(name, SOURCE)

        target_block = SOURCE.split(
            "var retirementTargets = []retirementTarget{", 1
        )[1].split(
            "var preservedUnacceptedLegacyScaleSets", 1
        )[0]
        self.assertNotIn('"lambda-research-engine"', target_block)
        self.assertNotIn('"lambda-research-engine-gpu"', target_block)

    def test_preflight_covers_every_queue_runner_and_execution_counter(self):
        for field in (
            "TotalAvailableJobs",
            "TotalAcquiredJobs",
            "TotalAssignedJobs",
            "TotalRunningJobs",
            "TotalRegisteredRunners",
            "TotalBusyRunners",
        ):
            self.assertIn(f"st.{field} != 0", SOURCE)

    def test_rollback_window_receipt_is_persisted_before_any_delete(self):
        write_pos = SOURCE.index(
            "if err := atomicWriteReceipt(receiptPath, receipt); err != nil"
        )
        delete_pos = SOURCE.index("client.DeleteRunnerScaleSet")
        self.assertLess(write_pos, delete_pos)
        self.assertIn(
            'Phase:                           rollbackWindowPhase',
            SOURCE,
        )
        self.assertIn(
            'PreservedLegacyBytesConfigState: true',
            SOURCE,
        )

    def test_post_commit_host_state_is_observation_only(self):
        self.assertIn(
            'argv = []string{"is-active", "--quiet", unit}',
            SOURCE,
        )
        self.assertIn(
            'argv = []string{"is-enabled", "--quiet", unit}',
            SOURCE,
        )
        for forbidden in (
            '"systemctl", "stop"',
            '"systemctl", "disable"',
            '"systemctl", "start"',
            '"systemctl", "enable"',
        ):
            self.assertNotIn(forbidden, SOURCE)

    def test_production_receipt_binding_is_fail_closed(self):
        self.assertIn('"V3_PRODUCTION_GENERATION_CUTOVER"', SOURCE)
        self.assertIn('"COMMITTED_V3_PRODUCTION"', SOURCE)
        self.assertIn(
            "receipt.ProductionValidationConfirmed",
            SOURCE,
        )
        self.assertIn(
            "reflect.DeepEqual(receipt.AcceptedRunnerClassIDs, acceptedClasses)",
            SOURCE,
        )

    def test_retirement_is_resumable_after_partial_remote_mutation(self):
        self.assertIn('"PARTIAL_RETIREMENT"', SOURCE)
        self.assertIn('flag.String("resume-receipt"', SOURCE)
        self.assertIn(
            "retired scale set unexpectedly exists during resume",
            SOURCE,
        )
        self.assertIn(
            "legacy scale-set ID changed",
            SOURCE,
        )

    def test_completed_retirement_has_fresh_process_verification_mode(self):
        self.assertIn('flag.String("verify-receipt"', SOURCE)
        self.assertIn("verifyCompletedRetirement", SOURCE)
        self.assertIn("LEGACY_SCALE_SET_ABSENT=", SOURCE)
        self.assertIn("V3_TARGET_SCALE_SET_PRESENT=", SOURCE)
        self.assertIn("V3_LEGACY_SCALE_SET_RETIREMENT_VERIFY=PASS", SOURCE)

    def test_migration_plan_requires_rollback_window_and_accepted_target(self):
        self.assertIn(
            '"target v3 route/class accepted"',
            MIGRATION_PLAN,
        )
        self.assertIn(
            '"rollback window receipt recorded"',
            MIGRATION_PLAN,
        )
        self.assertIn(
            '"preserve old installed bytes/config/state for rollback window"',
            MIGRATION_PLAN,
        )


if __name__ == "__main__":
    unittest.main()
