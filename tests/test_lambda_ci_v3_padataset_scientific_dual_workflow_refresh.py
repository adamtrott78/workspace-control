import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    ROOT / "scripts/lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v1.py"
).read_text()


class PADatasetScientificDualWorkflowRefreshTests(unittest.TestCase):
    def test_candidate_python_sources_compile(self):
        compile(REC, "lambda_ci_v3_reconciler.py", "exec")
        compile(HELPER, "lambda_ci_v3_padataset_scientific_dual_workflow_refresh_v1.py", "exec")

    def test_exact_lane_b_workflow_transition_is_frozen(self):
        self.assertIn(
            'PADATASET_SCIENTIFIC_DUAL_WORKFLOW_BLOB = "6280a6e7b2ad8cc379277fa320e8839a94f360ec"',
            REC,
        )
        self.assertIn(
            '"5f29137d9636ed170d3735d0f273220e7cf6f377"',
            REC,
        )
        self.assertIn(
            '"4674d1b07d7d7bb7ee3cbe4ab8a709d536486c13"',
            REC,
        )
        self.assertIn(
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_ACTIVE_RECEIPT",
            REC,
        )

    def test_reconciler_layers_refresh_over_immutable_dual_lane_activation(self):
        for marker in (
            "V3_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH",
            "dual_active_receipt_sha256",
            'dual_active["target_controller_policy_sha256"]',
            "scientific_dual_workflow_refresh",
            "expected_b_policy_sha",
            "expected_b_blob",
            "controller_policy_file_sha256",
        ):
            self.assertIn(marker, REC)

    def test_helper_targets_only_lane_b_controller_and_preserves_others(self):
        for marker in (
            "PADATASET_SCIENTIFIC_DUAL_TARGET_CLASS",
            'base.run_systemctl("stop", TARGET_UNIT)',
            'base.run_systemctl("start", TARGET_UNIT)',
            "require_snapshot_same(others_before, others_after)",
            "candidate.verify_installed(BASE_MANIFEST)",
            "ROLLED_BACK_PREVIOUS_DUAL_WORKFLOW",
            "COMMITTED_ACTIVE_DUAL_WORKFLOW_REFRESH",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn('run_systemctl("restart"', HELPER)
        self.assertNotIn('run_systemctl("stop", PROVISIONER_UNIT)', HELPER)
        self.assertNotIn('run_systemctl("restart", PROVISIONER_UNIT)', HELPER)

    def test_helper_requires_zero_work_fresh_preflight(self):
        for marker in (
            "PADATASET_SCIENTIFIC_DUAL_WORKFLOW_REFRESH_PREFLIGHT",
            '"assigned_jobs": 0',
            '"running_jobs": 0',
            '"active_workflow_runs": 0',
            "PREFLIGHT_MAX_SECONDS",
            "scale_set_id",
            "confirmed_at",
        ):
            self.assertIn(marker, HELPER)

    def test_helper_requires_one_shot_exact_operator_authority(self):
        for marker in (
            "REFRESH_PADATASET_SCIENTIFIC_DUAL_WORKFLOW_V1",
            'value["authority"] != "workspace-control-operator"',
            "AUTHORITY_MAX_SECONDS",
            "O_EXCL",
            "consume_authority(authority, authority_raw)",
            '"dual_active_receipt_sha256"',
            '"preflight_confirmation_sha256"',
            '"previous_workflow_blob_sha"',
            '"workflow_blob_sha"',
            '"padataset_main_sha"',
            '"previous_controller_policy_sha256"',
            '"controller_policy_sha256"',
            '"target_class_id"',
        ):
            self.assertIn(marker, HELPER)

    def test_helper_replaces_only_existing_single_trusted_workflow_blob(self):
        for marker in (
            '"route_id": "scientific-single-gpu-2"',
            '"path": WORKFLOW_PATH',
            '"default_branch": "main"',
            '"blob_sha": OLD_BLOB',
            '"compile_time_job_key": "padataset-scientific-2"',
            'refreshed_workflow["blob_sha"] = NEW_BLOB',
            'refreshed["trusted_workflows"] = [refreshed_workflow]',
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn("append(refreshed_workflow)", HELPER)


if __name__ == "__main__":
    unittest.main()
