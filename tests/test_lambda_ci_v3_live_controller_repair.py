import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
HELPER=(ROOT/"scripts/lambda_ci_v3_live_controller_repair_v1.py").read_text()
CONTROLLER=(ROOT/"controller/lambda-ci-controller/v3/controller.go").read_text()

class LiveControllerRepairTests(unittest.TestCase):
    def test_controller_source_contains_terminal_rest_revival(self):
        self.assertIn(
            "Revived terminal local record for still-queued REST-attested GitHub job",
            CONTROLLER,
        )
        self.assertIn(
            "REST_ATTESTED_QUEUED_RETRY",
            CONTROLLER,
        )

    def test_repair_is_exact_one_shot_and_controller_only(self):
        for marker in (
            "REFRESH_V3_CONTROLLER_BINARY_LIVE_V1",
            "authority-consumption",
            "current_controller_sha256",
            "candidate_controller_sha256",
            "previous_controller_refresh_sha256",
            "V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE",
            "COMMITTED_ACTIVE_CONTROLLER_REPAIR",
            "ROLLED_BACK_PREVIOUS_CONTROLLER",
        ):
            self.assertIn(marker,HELPER)
        self.assertNotIn("lambda_ci_runtime.py",HELPER)
        self.assertNotIn("controller_policy_sha256",HELPER)
        self.assertNotIn("workflow_blob_sha",HELPER)

    def test_repair_quiesces_active_controllers_but_preserves_root_services(self):
        self.assertIn('ctl("stop",units[cid])',HELPER)
        self.assertIn("require_no_live_provisioner_records()",HELPER)
        self.assertIn("require_no_transients(units)",HELPER)
        self.assertIn('ctl("start",units[cid])',HELPER)
        self.assertNotIn('ctl("stop",PROVISIONER_UNIT)',HELPER)
        self.assertNotIn('ctl("stop",RECONCILER_UNIT)',HELPER)

    def test_post_restore_allows_existing_queued_smoke_to_revive(self):
        marker="Do not require post-restore scheduler emptiness"
        self.assertIn(marker,HELPER)
        post=HELPER.index(marker)
        commit=HELPER.index('tx.update({',post)
        self.assertNotIn(
            "require_no_live_provisioner_records()",
            HELPER[post:commit],
        )

    def test_repair_receipt_is_reconciler_compatible(self):
        for marker in (
            '"mode":MODE',
            '"phase":"ACTIVE"',
            '"base_source_head":base_head',
            '"controller_source_head":args.expected_head',
            '"base_install_manifest_sha256":base_sha',
            '"root_policy_sha256":root_policy_sha',
            '"controller_binary_sha256":candidate_sha',
            '"non_controller_generation_equivalent":True',
        ):
            self.assertIn(marker,HELPER)

    def test_topology_and_restart_deltas_are_bounded(self):
        self.assertIn("previously-stable controller restarted during refresh",HELPER)
        self.assertIn("pre-existing restarting controller exceeded bounded restart delta",HELPER)
        self.assertIn('"controller_restart_deltas":deltas',HELPER)

if __name__=="__main__":
    unittest.main()
