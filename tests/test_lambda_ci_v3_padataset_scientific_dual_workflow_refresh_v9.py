import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v9.py").read_text()
LAUNCHER = (ROOT / "scripts/mth602_activate_laneb_refresh_v9.py").read_text()


class PADatasetScientificDualWorkflowRefreshV9Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(HELPER, "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v9.py", "exec")
        compile(LAUNCHER, "mth602_activate_laneb_refresh_v9.py", "exec")

    def test_exact_v8_to_v9_transition_is_frozen(self):
        for marker in (
            '"8375dd0a0733b01de38f677dee58a373d3adcb48"',
            '"6753795041090a5331a80354f59945be006ac889"',
            '"7cfe0ab61cc16785f4d267273b48a63361c595dd"',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v8_receipt_before_v9_and_prefers_v9(self):
        for marker in (
            "def _padataset_scientific_dual_lane_workflow_refresh_v9(",
            "PADataset lane-B workflow refresh v9 requires v8 predecessor",
            "scientific_dual_workflow_refresh_v9 =",
            "if scientific_dual_workflow_refresh_v9 is not None:",
            "scientific_dual_effective_refresh = scientific_dual_workflow_refresh_v9",
        ):
            self.assertIn(marker, REC)

    def test_helper_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        for marker in (
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_ACTIVE_RECEIPT",
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_ACTIVE_RECEIPT",
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8_BLOB",
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_BLOB",
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_PAD_MAIN",
        ):
            self.assertIn(marker, lines)

    def test_helper_requires_exact_v8_predecessor_and_rolls_back_to_v8(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V8"',
            "candidate.PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V7_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            "current controller policy does not match refresh v8",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V8",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9=PASS",
        ):
            self.assertIn(marker, HELPER)

    def test_helper_changes_only_lane_b_and_requires_zero_work(self):
        for marker in (
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            '"active_workflow_runs": 0',
            "require_target_quiescent()",
            'base.run_systemctl("stop", TARGET_UNIT)',
            'base.run_systemctl("start", TARGET_UNIT)',
            "require_snapshot_same(others_before, others_after)",
            "candidate.verify_installed(BASE_MANIFEST)",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn('run_systemctl("stop", PROVISIONER_UNIT)', HELPER)

    def test_launcher_binds_postmerge_main_blob_and_zero_work_before_sudo(self):
        for marker in (
            'EXPECTED_PAD_MAIN = "7cfe0ab61cc16785f4d267273b48a63361c595dd"',
            'EXPECTED_WORKFLOW_BLOB = "6753795041090a5331a80354f59945be006ac889"',
            'WORKFLOW_FILE = "lambda-ci-scientific-2.yml"',
            'for status in ("queued", "in_progress")',
            "LANEB_PROVIDER_ZERO_WORK=PASS",
            'run(["sudo", "-v"])',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V9_PREFLIGHT",
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V9",
            "MTH602_LANEB_REFRESH_V9_POSTVERIFY=PASS",
        ):
            self.assertIn(marker, LAUNCHER)
        self.assertLess(LAUNCHER.index("provider_zero_work()"), LAUNCHER.index('run(["sudo", "-v"])'))
        self.assertNotIn("shell=True", LAUNCHER)


if __name__ == "__main__":
    unittest.main()
