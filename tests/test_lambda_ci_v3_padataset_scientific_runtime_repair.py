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

    def test_repair_preserves_enablement_and_bounds_restart_delta(self):
        self.assertIn('now.get("UnitFileState")!=state.get("UnitFileState")',HELPER)
        self.assertIn("previously-stable controller restarted during repair",HELPER)
        self.assertIn("pre-existing restarting controller exceeded bounded restart delta",HELPER)
        self.assertIn('"controller_restart_deltas":restart_deltas',HELPER)
        self.assertIn("inactive controller unexpectedly activated",HELPER)

    def test_scheduler_emptiness_is_required_before_swap_not_after_restore(self):
        pre_swap = HELPER.index('ctl("stop",PROVISIONER_UNIT)')
        post_restore = HELPER.index('for cid in active_before:\n            ctl("start",units[cid])')
        self.assertLess(
            HELPER.rfind("require_no_live_provisioner_records()", 0, pre_swap),
            pre_swap,
        )
        self.assertNotIn(
            "require_no_live_provisioner_records()",
            HELPER[post_restore:HELPER.index('tx.update({', post_restore)],
        )
        self.assertIn(
            "queued GitHub demand may legitimately",
            HELPER,
        )

    def test_rollback_is_verified_before_claiming_completion(self):
        self.assertIn('wait_state(PROVISIONER_UNIT,"active")',HELPER)
        self.assertIn('wait_state(units[cid],"active")',HELPER)
        self.assertIn("rollback_controller_snapshot_after",HELPER)
        self.assertIn("rollback_provisioner_after",HELPER)
        self.assertIn("reconciler.verify_installed(BASE_MANIFEST)",HELPER)

if __name__=="__main__":
    unittest.main()
