import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = (ROOT / "scripts/lambda_ci_runtime.py").read_text()
HELPER = (ROOT / "scripts/lambda_ci_v3_padataset_lane_b_runtime_profile_hotfix_v1.py").read_text()

class PADatasetLaneBRuntimeProfileHotfixTests(unittest.TestCase):
    def test_lane_b_profile_is_single_gpu_runtime_profile(self):
        self.assertIn(
            'SINGLE_GPU_EXECUTION_PROFILES = frozenset({"gpu-small", "gpu-scientific-single", "gpu-scientific-single-2"})',
            RUNTIME,
        )
        self.assertIn('if profile in SINGLE_GPU_EXECUTION_PROFILES:', RUNTIME)

    def test_hotfix_is_exact_one_line_additive_delta(self):
        self.assertIn("candidate != expected_candidate", HELPER)
        self.assertIn("current.replace(OLD_LINE, NEW_LINE, 1)", HELPER)
        self.assertIn("ADD_PADATASET_SCIENTIFIC_SINGLE_GPU_2_PROFILE_ONLY", HELPER)

    def test_hotfix_does_not_restart_shared_services(self):
        self.assertNotIn('systemctl", "restart"', HELPER)
        self.assertNotIn('systemctl", "stop"', HELPER)
        self.assertNotIn('systemctl", "start"', HELPER)
        self.assertIn('"PROVISIONER_RESTARTED=0"', HELPER)
        self.assertIn('"CONTROLLERS_RESTARTED=0"', HELPER)

    def test_hotfix_binds_exact_operator_authority_and_rolls_back(self):
        for marker in (
            "HOTFIX_PADATASET_LANE_B_RUNTIME_PROFILE_V1",
            "current_runtime_sha256",
            "candidate_runtime_sha256",
            "previous_runtime_override_sha256",
            "target_class_id",
            "target_profile",
            "authority-consumption",
            "ROLLED_BACK",
        ):
            self.assertIn(marker, HELPER)

    def test_hotfix_preserves_live_process_identity(self):
        self.assertIn('("ActiveState", "SubState", "MainPID", "InvocationID")', HELPER)
        self.assertIn("changed during runtime hotfix", HELPER)

if __name__ == "__main__":
    unittest.main()
