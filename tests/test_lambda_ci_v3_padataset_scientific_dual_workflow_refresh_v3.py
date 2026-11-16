import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v3.py"
).read_text()


class PADatasetScientificDualWorkflowRefreshV3Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v3.py",
            "exec",
        )

    def test_exact_v2_to_v3_transition_is_frozen(self):
        for marker in (
            '"8da00f39284745cf6c9032620d63574052cd6d61"',
            '"85e8deef5240e2d6d7db34318e6b2c35947a83f3"',
            '"dbf167b23e6a1777a31ad5c4bccde44d26d0aad6"',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v2_receipt_before_v3(self):
        for marker in (
            "_padataset_scientific_dual_lane_workflow_refresh_v3",
            "workflow refresh v3 requires v2 predecessor",
            "scientific_dual_workflow_refresh_v3",
            "scientific_dual_effective_refresh",
        ):
            self.assertIn(marker, REC)

    def test_helper_preserves_prior_receipts_and_rolls_back_to_v2(self):
        for marker in (
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_ACTIVE_RECEIPT",
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V3",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3_PREFLIGHT",
            "prior_refresh_receipt_sha256",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V2",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V3=PASS",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("PRIOR_REFRESH_ACTIVE.unlink", HELPER)

    def test_helper_changes_only_lane_b_controller(self):
        for marker in (
            'base.run_systemctl("stop", TARGET_UNIT)',
            'base.run_systemctl("start", TARGET_UNIT)',
            "require_snapshot_same(others_before, others_after)",
            "candidate.verify_installed(BASE_MANIFEST)",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn('run_systemctl("stop", PROVISIONER_UNIT)', HELPER)
        self.assertNotIn('run_systemctl("restart"', HELPER)

    def test_helper_requires_zero_work_and_v2_policy_predecessor(self):
        for marker in (
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            '"active_workflow_runs": 0',
            "require_target_quiescent()",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            'prior_refresh.get("controller_policy_sha256")',
            "does not match refresh v2",
        ):
            self.assertIn(marker, HELPER)


if __name__ == "__main__":
    unittest.main()
