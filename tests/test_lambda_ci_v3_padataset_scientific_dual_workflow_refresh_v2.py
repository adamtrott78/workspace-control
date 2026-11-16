import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v2.py"
).read_text()


class PADatasetScientificDualWorkflowRefreshV2Tests(unittest.TestCase):
    def test_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(
            HELPER,
            "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v2.py",
            "exec",
        )

    def test_exact_v1_to_v2_transition_is_frozen(self):
        for marker in (
            '"5f29137d9636ed170d3735d0f273220e7cf6f377"',
            '"8da00f39284745cf6c9032620d63574052cd6d61"',
            '"9889a981e34de81e58f3263630f0cba54a8e9e06"',
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
        ):
            self.assertIn(marker, REC)

    def test_reconciler_requires_v1_receipt_before_v2(self):
        for marker in (
            "_padataset_scientific_dual_lane_workflow_refresh_v2",
            "prior_refresh_receipt_sha256",
            "workflow refresh v2 requires v1 predecessor",
            "scientific_dual_effective_refresh",
        ):
            self.assertIn(marker, REC)

    def test_helper_is_one_shot_v2_and_preserves_v1(self):
        for marker in (
            "PRIOR_REFRESH_ACTIVE",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_ACTIVE_RECEIPT",
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V2",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2_PREFLIGHT",
            "prior_refresh_receipt_sha256",
            "ROLLED_BACK_TO_WORKFLOW_REFRESH_V1",
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_V2=PASS",
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

    def test_helper_requires_zero_work_and_exact_predecessor(self):
        for marker in (
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            '"active_workflow_runs": 0',
            "require_target_quiescent()",
            'prior_refresh.get("workflow_blob_sha") != OLD_BLOB',
            'current_policy.get("controller_policy_sha256")',
            'prior_refresh.get("controller_policy_sha256")',
        ):
            self.assertIn(marker, HELPER)


if __name__ == "__main__":
    unittest.main()
