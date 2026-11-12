import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = ROOT / "architecture" / "lambda-ci-v3-offline-producer-cutover-plan.v1.json"
BRIDGE = ROOT / "architecture" / "lambda-ci-v3-offline-payload-producer-bridge.v1.json"
CATALOG = ROOT / "architecture" / "lambda-ci-runner-class-catalog.v1.json"


class V3OfflineProducerCutoverPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN.read_text())
        cls.bridge = json.loads(BRIDGE.read_text())
        cls.catalog = json.loads(CATALOG.read_text())

    def test_cutover_is_explicitly_not_ready_or_authorized(self):
        self.assertEqual(
            self.plan["status"],
            "DESIGN_ONLY_NOT_AUTHORIZED_FOR_DEFAULT_BRANCH_OR_LIVE_EXECUTION",
        )
        self.assertEqual(self.plan["live_authority"], "NONE")
        readiness = self.plan["current_readiness"]
        self.assertTrue(readiness["github_hosted_ci_executed_repository_steps"])
        self.assertFalse(readiness["offline_class_canaries_live_accepted"])
        self.assertFalse(readiness["research_gpu_containment_recovery_authorized"])
        self.assertFalse(readiness["default_branch_cutover_authorized"])
        self.assertFalse(readiness["lambda_live_activation_authorized"])
        self.assertFalse(readiness["ready_for_cutover"])

    def test_hosted_ci_satisfied_does_not_imply_cutover_authority(self):
        readiness = self.plan["current_readiness"]
        self.assertTrue(readiness["github_hosted_ci_executed_repository_steps"])
        self.assertFalse(readiness["offline_class_canaries_live_accepted"])
        self.assertFalse(readiness["research_gpu_containment_recovery_authorized"])
        self.assertFalse(readiness["default_branch_cutover_authorized"])
        self.assertFalse(readiness["lambda_live_activation_authorized"])
        self.assertFalse(readiness["ready_for_cutover"])

    def test_candidate_and_old_blobs_match_bridge_and_current_catalog(self):
        bridge_workflows = self.bridge["research_engine"]["workflows"]
        routes = self.catalog["projects"]["research-engine"]["routes"]
        plan_routes = {item["route_id"]: item for item in self.plan["scope"]["routes"]}
        for route_id in ("model-eval-single-gpu", "model-eval-dual-gpu"):
            plan = plan_routes[route_id]
            bridge = bridge_workflows[route_id]
            current = routes[route_id]["trusted_workflow"]
            self.assertEqual(plan["workflow_path"], bridge["path"])
            self.assertEqual(
                plan["reviewed_candidate_blob_sha"],
                bridge["proposed_blob_sha"],
            )
            self.assertEqual(plan["old_blob_sha"], bridge["current_default_branch_blob_sha"])
            self.assertEqual(plan["old_blob_sha"], current["blob_sha"])
            self.assertNotEqual(
                plan["reviewed_candidate_blob_sha"],
                current["blob_sha"],
            )

    def test_cutover_binds_exact_homogeneous_runner_classes(self):
        classes = self.catalog["projects"]["research-engine"]["runner_classes"]
        for entry in self.plan["scope"]["routes"]:
            cls = classes[entry["runner_class_id"]]
            self.assertEqual(entry["target_scale_set"], cls["scale_set_name"])
            self.assertEqual(
                cls["execution_contract_id"],
                (
                    "model-single-offline-v1"
                    if entry["route_id"] == "model-eval-single-gpu"
                    else "model-dual-offline-v1"
                ),
            )

    def test_rollback_never_resurrects_legacy_research_gpu(self):
        encoded = json.dumps(self.plan["rollback"], sort_keys=True).lower()
        self.assertIn("keep legacy research gpu controller stopped/contained", encoded)
        self.assertIn("do not restore the old crash loop", encoded)
        forbidden = "\n".join(self.plan["forbidden"]).lower()
        self.assertIn(
            "do not restart the legacy research-engine gpu v2 controller",
            forbidden,
        )
        self.assertIn("do not clear or recreate ready_for_single_retry", forbidden)

    def test_no_proposal_blob_can_be_installed_as_trust_before_default_branch_proof(self):
        rules = "\n".join(self.plan["immutable_candidate_rules"]).lower()
        self.assertIn(
            "default-branch workflow blobs must equal the exact reviewed candidate blob shas",
            rules,
        )
        forbidden = "\n".join(self.plan["forbidden"]).lower()
        self.assertIn(
            "do not install a controller projection that trusts proposal blobs before those exact blobs are present on the owning default branch",
            forbidden,
        )

    def test_cutover_helper_never_dispatches_candidate_or_scientific_work(self):
        forbidden = "\n".join(self.plan["forbidden"]).lower()
        self.assertIn(
            "do not dispatch candidate/scientific work as part of the cutover helper itself",
            forbidden,
        )


if __name__ == "__main__":
    unittest.main()
