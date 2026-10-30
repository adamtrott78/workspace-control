import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "architecture" / "lambda-ci-v3-offline-payload-producer-bridge.v1.json"
CATALOG = ROOT / "architecture" / "lambda-ci-runner-class-catalog.v1.json"
CANARIES = ROOT / "architecture" / "lambda-ci-v3-migration-canaries.v1.json"

HEX40 = re.compile(r"^[0-9a-f]{40}$")


class V3OfflinePayloadProducerBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = json.loads(BRIDGE.read_text())
        cls.catalog = json.loads(CATALOG.read_text())
        cls.canaries = json.loads(CANARIES.read_text())

    def test_bridge_is_proposal_only_and_grants_no_live_authority(self):
        self.assertEqual(
            self.bridge["status"],
            "PROPOSED_CROSS_REPO_NOT_DEFAULT_BRANCH_NOT_LIVE",
        )
        self.assertEqual(self.bridge["live_authority"], "NONE")
        research = self.bridge["research_engine"]
        self.assertFalse(research["default_branch_modified"])
        self.assertNotEqual(research["proposal_branch"], research["base_branch"])
        self.assertTrue(research["pull_request_state"] == "DRAFT")
        gate = self.bridge["migration_gate"]
        self.assertFalse(gate["research_gpu_inherited_containment_resolved"])
        self.assertFalse(gate["production_workflow_default_branch_cutover_resolved"])
        self.assertFalse(gate["live_activation_authorized"])

    def test_proposed_workflow_blobs_are_not_silently_promoted_into_live_catalog(self):
        routes = self.catalog["projects"]["research-engine"]["routes"]
        bridge_routes = self.bridge["research_engine"]["workflows"]
        for route_id in ("model-eval-single-gpu", "model-eval-dual-gpu"):
            proposal = bridge_routes[route_id]
            current = routes[route_id]["trusted_workflow"]
            self.assertRegex(proposal["proposed_blob_sha"], HEX40)
            self.assertRegex(proposal["current_default_branch_blob_sha"], HEX40)
            self.assertNotEqual(
                proposal["proposed_blob_sha"],
                proposal["current_default_branch_blob_sha"],
            )
            self.assertEqual(
                current["blob_sha"],
                proposal["current_default_branch_blob_sha"],
            )
            self.assertEqual(current["path"], proposal["path"])
            self.assertEqual(current["default_branch"], "main")

    def test_proposed_scale_sets_match_exact_offline_runner_classes(self):
        classes = self.catalog["projects"]["research-engine"]["runner_classes"]
        workflows = self.bridge["research_engine"]["workflows"]
        expected = {
            "model-eval-single-gpu": "research-model-single-offline-v1",
            "model-eval-dual-gpu": "research-model-dual-offline-v1",
        }
        for route_id, class_id in expected.items():
            self.assertEqual(
                workflows[route_id]["target_scale_set"],
                classes[class_id]["scale_set_name"],
            )

    def test_repository_network_blocker_is_resolved_without_resolving_containment(self):
        network = self.canaries["network_verification"]
        self.assertIn(
            "GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE",
            network["supported_payload_network_classes"],
        )
        self.assertEqual(network["unresolved_payload_network_classes"], [])
        gate = self.bridge["migration_gate"]
        self.assertTrue(gate["offline_payload_network_repository_blocker_resolved"])
        self.assertFalse(gate["research_gpu_inherited_containment_resolved"])

    def test_runtime_and_producer_bind_distinct_broker_staging_boundary(self):
        runtime = "\n".join(self.bridge["workspace_control"]["invariants"]).lower()
        producer = "\n".join(self.bridge["research_engine"]["producer_invariants"]).lower()
        self.assertIn("each offline runner class receives its own", runtime)
        self.assertIn("runner job/checkout tree is inaccessible", runtime)
        self.assertIn("runner-private home/tmp/cache", runtime)
        self.assertIn("dedicated per-request payload-exchange", runtime)
        self.assertIn("persist-credentials false", producer)
        self.assertIn("payload-exchange", producer)
        self.assertIn("execution cwd never requires the checkout/job tree", producer)

    def test_workspace_runtime_boundary_is_bound_to_green_validation(self):
        validation = self.bridge["workspace_control"]["runtime_boundary_validation"]
        self.assertRegex(validation["exact_head"], HEX40)
        self.assertEqual(validation["run_number"], 1326)
        self.assertEqual(validation["run_id"], 41005440005)
        self.assertEqual(validation["conclusion"], "success")


if __name__ == "__main__":
    unittest.main()
