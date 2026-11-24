import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (ROOT / "scripts/lambda_ci_v3_padataset_scientific_workflow_refresh_v4.py").read_text()
LAUNCHER = (ROOT / "scripts/mth602_activate_lanea_refresh_v4.py").read_text()


class PADatasetScientificWorkflowRefreshV4Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(HELPER, "lambda_ci_v3_padataset_scientific_workflow_refresh_v4.py", "exec")
        compile(LAUNCHER, "mth602_activate_lanea_refresh_v4.py", "exec")

    def test_exact_v3_to_v4_transition_is_frozen(self):
        for marker in (
            '"ea5d844c494013eb2322686d7345b5a1b15443c4"',
            '"39190413abbd801bd6d25c2166ac36a7a69968fb"',
            '"7cfe0ab61cc16785f4d267273b48a63361c595dd"',
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v3_receipt_before_v4_and_prefers_v4(self):
        for marker in (
            "def _padataset_scientific_workflow_refresh_v4(",
            "PADataset scientific workflow refresh v4 requires v3 predecessor",
            "scientific_workflow_refresh_v4 =",
            "if scientific_workflow_refresh_v4 is not None:",
            "scientific_workflow_effective_refresh = scientific_workflow_refresh_v4",
        ):
            self.assertIn(marker, REC)

    def test_helper_bindings_are_exact(self):
        lines = set(HELPER.splitlines())
        for marker in (
            "PRIOR_REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
            "REFRESH_ACTIVE = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_ACTIVE_RECEIPT",
            "OLD_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3_BLOB",
            "NEW_BLOB = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_BLOB",
            "PAD_MAIN = candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_PAD_MAIN",
        ):
            self.assertIn(marker, lines)

    def test_helper_requires_exact_v3_predecessor_and_rolls_back_to_v3(self):
        for marker in (
            '!= "V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V3"',
            "candidate.PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V2_BLOB",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            "current controller policy does not match refresh v3",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V3",
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4=PASS",
        ):
            self.assertIn(marker, HELPER)

    def test_helper_is_lane_a_only_and_fail_closed(self):
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
            'EXPECTED_WORKFLOW_BLOB = "39190413abbd801bd6d25c2166ac36a7a69968fb"',
            'WORKFLOW_FILE = "lambda-ci-scientific.yml"',
            'for status in ("queued", "in_progress")',
            "LANEA_PROVIDER_ZERO_WORK=PASS",
            'run(["sudo", "-v"])',
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_V4_PREFLIGHT",
            "REFRESH_PADATASET_SCIENTIFIC_WORKFLOW_V4",
            "MTH602_LANEA_REFRESH_V4_POSTVERIFY=PASS",
        ):
            self.assertIn(marker, LAUNCHER)
        self.assertLess(LAUNCHER.index("provider_zero_work()"), LAUNCHER.index('run(["sudo", "-v"])'))
        self.assertNotIn("shell=True", LAUNCHER)


if __name__ == "__main__":
    unittest.main()
