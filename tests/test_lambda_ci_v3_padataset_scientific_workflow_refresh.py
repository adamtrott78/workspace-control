import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REC = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
HELPER = (ROOT / "scripts/lambda_ci_v3_padataset_scientific_workflow_refresh_v1.py").read_text()

class PADatasetScientificWorkflowRefreshTests(unittest.TestCase):
    def test_reconciler_layers_workflow_refresh_over_immutable_activation(self):
        self.assertIn("PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_ACTIVE_RECEIPT", REC)
        self.assertIn("V3_PADATASET_SCIENTIFIC_WORKFLOW_REFRESH", REC)
        self.assertIn("scientific_active_receipt_sha256", REC)
        self.assertIn("controller_policy_file_sha256", REC)
        self.assertIn("workflow_refresh[\"workflow_blob_sha\"]", REC)
        self.assertIn("4cf390ec334b0569dbfc2399ff86c2d892f97586", REC)
        self.assertIn("a7e3eb3718820f6fa3183ebc6b8990da2b49f61f", REC)

    def test_helper_changes_only_target_policy_reconciler_and_refresh_receipt(self):
        self.assertIn("REFRESH_PADATASET_SCIENTIFIC_WORKFLOW_V1", HELPER)
        self.assertIn("controller policy changed beyond workflow binding", HELPER)
        self.assertIn("trusted workflow metadata changed beyond blob", HELPER)
        self.assertIn('run_systemctl("stop",TARGET_UNIT)', HELPER)
        self.assertIn('run_systemctl("start",TARGET_UNIT)', HELPER)
        self.assertNotIn('systemctl","restart"', HELPER)
        self.assertNotIn("PROVISIONER_UNIT)", HELPER.split('run_systemctl("stop",TARGET_UNIT)')[1])

    def test_helper_requires_fresh_zero_work_preflight_and_one_shot_authority(self):
        for marker in (
            "PADATASET_SCIENTIFIC_WORKFLOW_REFRESH_PREFLIGHT",
            '"assigned_jobs":0',
            '"running_jobs":0',
            '"active_workflow_runs":0',
            "PREFLIGHT_MAX_SECONDS",
            "consume_authority(authority,authority_raw)",
            "O_EXCL",
        ):
            self.assertIn(marker, HELPER)

    def test_helper_preserves_other_controller_snapshots_and_rolls_back(self):
        self.assertIn("require_snapshot_same(others_before,others_after)", HELPER)
        self.assertIn("ROLLED_BACK_PREVIOUS_WORKFLOW", HELPER)
        self.assertIn("candidate.verify_installed(BASE_MANIFEST)", HELPER)
        self.assertIn("COMMITTED_ACTIVE_WORKFLOW_REFRESH", HELPER)

if __name__ == "__main__":
    unittest.main()
