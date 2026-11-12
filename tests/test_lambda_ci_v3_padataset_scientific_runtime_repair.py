import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
HELPER=(ROOT/"scripts/lambda_ci_v3_padataset_scientific_runtime_repair_v1.py").read_text()
RUNTIME=(ROOT/"scripts/lambda_ci_runtime.py").read_text()

class PADatasetScientificRuntimeRepairTests(unittest.TestCase):
    def test_runtime_accepts_scientific_profile_only_through_single_gpu_path(self):
        self.assertIn('SINGLE_GPU_EXECUTION_PROFILES = frozenset({"gpu-small", "gpu-scientific-single"})',RUNTIME)
        self.assertIn('if profile in SINGLE_GPU_EXECUTION_PROFILES:',RUNTIME)
        self.assertIn('GPU_EXECUTION_PROFILES = SINGLE_GPU_EXECUTION_PROFILES',RUNTIME)

    def test_repair_is_one_shot_root_bound_and_runtime_only(self):
        for marker in (
            "REPAIR_PADATASET_SCIENTIFIC_RUNTIME_V1",
            "authority-consumption",
            "candidate_runtime_sha256",
            "current_runtime_sha256",
            "V3_RUNTIME_OVERRIDE",
            "COMMITTED_ACTIVE_RUNTIME_REPAIR",
            "ROLLED_BACK_PREVIOUS_RUNTIME",
        ):
            self.assertIn(marker,HELPER)
        self.assertNotIn("controller_policy",HELPER)
        self.assertNotIn("workflow_blob",HELPER)
        self.assertNotIn("scale_set",HELPER)

    def test_repair_quiesces_all_active_controllers_around_shared_provisioner(self):
        self.assertIn("active_before=[cid for cid,s in before.items()",HELPER)
        self.assertIn('ctl("stop",units[cid])',HELPER)
        self.assertIn('ctl("stop",PROVISIONER_UNIT)',HELPER)
        self.assertIn('ctl("start",PROVISIONER_UNIT)',HELPER)
        self.assertIn('ctl("start",units[cid])',HELPER)
        self.assertIn("require_no_live_provisioner_records()",HELPER)
        self.assertIn("require_no_transients(units)",HELPER)

    def test_repair_preserves_enablement_restart_counters_and_inactive_set(self):
        self.assertIn('now.get("UnitFileState")!=state.get("UnitFileState")',HELPER)
        self.assertIn('now.get("NRestarts")!=state.get("NRestarts")',HELPER)
        self.assertIn("inactive controller unexpectedly activated",HELPER)

if __name__=="__main__":
    unittest.main()
