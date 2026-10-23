import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "architecture/lambda-ci-project-registry.v1.json").read_text())
CONTRACTS = json.loads((ROOT / "architecture/lambda-ci-execution-contracts.v1.json").read_text())
RESEARCH = json.loads((ROOT / "architecture/lambda-ci-project-research-engine.v2.json").read_text())
PAD = json.loads((ROOT / "architecture/lambda-ci-project-padataset.v1.json").read_text())
REGISTRY_SCHEMA = json.loads((ROOT / "schemas/lambda-ci-project-registry.v1.schema.json").read_text())
MANIFEST_SCHEMA = json.loads((ROOT / "schemas/lambda-ci-project-manifest.v2.schema.json").read_text())
CONTRACTS_SCHEMA = json.loads((ROOT / "schemas/lambda-ci-execution-contracts.v1.schema.json").read_text())
RECONCILE_SCHEMA = json.loads((ROOT / "schemas/lambda-ci-reconciliation-request.v1.schema.json").read_text())


def derived(project_id):
    return {
        "runner_user": f"ci-{project_id}",
        "runner_group": f"ci-{project_id}",
        "project_root": f"/srv/workspace-ci/{project_id}",
        "cpu_scale_set": f"lambda-{project_id}",
        "gpu_scale_set": f"lambda-{project_id}-gpu",
        "cpu_runner_prefix": f"lambda-{project_id}-",
        "gpu_runner_prefix": f"lambda-{project_id}-gpu-",
    }


class LambdaCIMultiRepoContractTests(unittest.TestCase):
    def test_run4_activates_padataset_after_run3_acceptance(self):
        self.assertEqual(REGISTRY["status"], "ACTIVE")
        self.assertEqual(REGISTRY["registry_epoch"], 5)
        self.assertEqual(CONTRACTS["status"], "CONTRACT_ONLY_NOT_INSTALLED")
        self.assertEqual(RESEARCH["status"], "ACTIVE")
        self.assertEqual(PAD["status"], "ACTIVE")
        self.assertEqual(
            REGISTRY["projects"]["research-engine"]["activation_state"],
            "ACTIVE",
        )
        self.assertEqual(
            REGISTRY["projects"]["padataset"]["activation_state"],
            "ACTIVE",
        )

    def test_registry_is_root_owned_and_candidate_cannot_reconcile(self):
        authority = REGISTRY["authority"]
        self.assertEqual(authority["owner"], "workspace-control")
        self.assertFalse(authority["target_repository_policy_authority"])
        self.assertFalse(authority["candidate_invocable_reconciliation"])
        reconcile = REGISTRY["reconciliation"]
        self.assertEqual(reconcile["source_repository"], "adamtrott78/workspace-control")
        self.assertFalse(reconcile["target_repository_candidate_invocable"])
        self.assertFalse(reconcile["arbitrary_commands_allowed"])
        self.assertFalse(reconcile["arbitrary_paths_allowed"])
        self.assertFalse(reconcile["arbitrary_systemd_properties_allowed"])

    def test_project_identity_is_deterministic_and_distinct(self):
        for project_id, manifest in (("research-engine", RESEARCH), ("padataset", PAD)):
            want = derived(project_id)
            got = manifest["derived_identity"]
            self.assertEqual(got["runner_user"], want["runner_user"])
            self.assertEqual(got["runner_group"], want["runner_group"])
            self.assertEqual(got["project_root"], want["project_root"])
            self.assertEqual(got["lanes"]["cpu"]["scale_set_name"], want["cpu_scale_set"])
            self.assertEqual(got["lanes"]["gpu"]["scale_set_name"], want["gpu_scale_set"])
            self.assertEqual(got["lanes"]["cpu"]["runner_prefix"], want["cpu_runner_prefix"])
            self.assertEqual(got["lanes"]["gpu"]["runner_prefix"], want["gpu_runner_prefix"])
        self.assertNotEqual(RESEARCH["derived_identity"]["runner_user"], PAD["derived_identity"]["runner_user"])
        self.assertNotEqual(RESEARCH["derived_identity"]["project_root"], PAD["derived_identity"]["project_root"])

    def test_registry_references_exact_manifest_candidates(self):
        projects = REGISTRY["projects"]
        self.assertEqual(projects["research-engine"]["repository"], "adamtrott78/research-engine")
        self.assertEqual(projects["research-engine"]["manifest_source_path"], "architecture/lambda-ci-project-research-engine.v2.json")
        self.assertEqual(projects["padataset"]["repository"], "adamtrott78/PADataset")
        self.assertEqual(projects["padataset"]["manifest_source_path"], "architecture/lambda-ci-project-padataset.v1.json")

    def test_route_name_is_not_privileged_authority(self):
        authority = CONTRACTS["authority"]
        self.assertFalse(authority["route_id_is_privilege"])
        self.assertEqual(authority["privileged_runtime_dispatch_key"], "resolved_execution_contract")
        self.assertEqual(authority["unknown_route_action"], "REJECT")
        self.assertFalse(authority["source_code_change_required_for_new_route_using_existing_contract"])

    def test_every_route_resolves_to_known_execution_contract(self):
        known = set(CONTRACTS["contracts"])
        for manifest in (RESEARCH, PAD):
            for route in manifest["routes"].values():
                self.assertIn(route["execution_contract_id"], known)

    def test_research_engine_migration_preserves_exact_workflow_blobs(self):
        expected = {
            "cpu-test": "eca9f11373a591a34a2e19c0eafe31e9e171f785",
            "gpu-small": "e02e35306ae82c4ba393631cbaa1521ca53a28b4",
            "model-eval-single-gpu": "31d77703d434b248aa50adf93568f9a13b89dc07",
            "model-eval-dual-gpu": "a961158615269797837e036fb4cc4a3358f60189",
            "model-eval-local-extract-wave1": "a5be693f750c481db21d86d239a505083aae40aa",
            "model-eval-local-extract-wave2": "cb7fd59bcb6f857bd6148ecbc7e2eb320dc9a1fb",
            "model-eval-local-extract-wave3": "db45f163e9e8b342d78c04540f0ace10fcba5906",
            "model-eval-local-extract-wave4": "71641ec390a514c5f6f046a1cb00eed9e43f839e",
            "model-eval-local-extract-wave5": "2ef10f5b0940ff3c2238f74c0f0efbaf5bd61d6d",
            "model-eval-local-extract-wave6": "c81e7cbb31f1731ada483a9b1f9256a4e6d78312",
            "model-eval-local-extract-reranker-v1": "774322780331bdc98407724bc6c5ea4c91882051",
            "model-eval-local-extract-oracle-query-v1": "9ee22449510d425381e30aa3fc330764d8cb6464",
        }
        self.assertEqual(set(RESEARCH["routes"]), set(expected))
        for route_id, sha in expected.items():
            self.assertEqual(RESEARCH["routes"][route_id]["trusted_workflow"]["blob_sha"], sha)

    def test_padataset_public_repo_gate_is_fail_closed(self):
        self.assertEqual(PAD["repository_visibility"], "public")
        expected_blobs = {
            "cpu-ci": "5e6a1d4a47ecdfa8b40d3bea23fa8739cc12cd9e",
            "gpu-ci": "3e0c79dc1b8bed7b1480cc745c478c190a3c7da4",
        }
        self.assertEqual(set(PAD["routes"]), set(expected_blobs))
        for route_id, route in PAD["routes"].items():
            trigger = route["trigger"]
            self.assertEqual(trigger["allowed_actor_logins"], ["adamtrott78"])
            self.assertTrue(trigger["require_open_same_repository_pr_head"])
            self.assertFalse(trigger["fork_pr_execution_allowed"])
            self.assertEqual(
                route["trusted_workflow"]["blob_sha"],
                expected_blobs[route_id],
            )
            self.assertEqual(route["activation_state"], "ACTIVE")

    def test_generic_dual_gpu_compute_remains_unaccepted(self):
        generic_heavy = CONTRACTS["contracts"]["gpu-dual-public-ci-v1"]
        self.assertEqual(generic_heavy["lifecycle"], "PLANNED_NOT_ACCEPTED")
        self.assertFalse(generic_heavy["admission_enabled_after_generic_activation"])
        self.assertEqual(generic_heavy["gpu_count"], 2)

    def test_existing_dual_model_contracts_remain_bounded(self):
        for name in ("model-dual-offline-v1", "model-dual-public-v1"):
            contract = CONTRACTS["contracts"][name]
            self.assertEqual(contract["execution_profile"], "gpu-heavy")
            self.assertEqual(contract["resource_class"], "model_eval_dual_gpu_v1")
            self.assertEqual(contract["gpu_count"], 2)
            self.assertEqual(contract["model_binding_mode"], "REQUIRED_PROMOTED_EXACT")
            self.assertEqual(contract["runtime_binding_mode"], "REQUIRED_EXPANDED_RUNTIME_EXACT")

    def test_third_project_is_structurally_manifest_only(self):
        project_id = "future-research"
        self.assertRegex(project_id, r"^[a-z][a-z0-9-]{1,20}$")
        want = derived(project_id)
        self.assertEqual(want["runner_user"], "ci-future-research")
        self.assertEqual(want["cpu_scale_set"], "lambda-future-research")
        self.assertEqual(want["gpu_runner_prefix"], "lambda-future-research-gpu-")
        project_pattern = next(iter(REGISTRY_SCHEMA["properties"]["projects"]["patternProperties"]))
        manifest_project_pattern = MANIFEST_SCHEMA["properties"]["project_id"]["pattern"]
        self.assertTrue(re.fullmatch(project_pattern, project_id))
        self.assertTrue(re.fullmatch(manifest_project_pattern, project_id))
        self.assertIn("cpu-public-ci-v1", CONTRACTS["contracts"])
        self.assertIn("gpu-single-public-ci-v1", CONTRACTS["contracts"])

    def test_schemas_encode_no_project_enum(self):
        project_schema = REGISTRY_SCHEMA["properties"]["projects"]
        self.assertIn("patternProperties", project_schema)
        self.assertNotIn("properties", project_schema)
        self.assertNotIn("enum", MANIFEST_SCHEMA["properties"]["project_id"])
        self.assertEqual(CONTRACTS_SCHEMA["properties"]["contracts"]["additionalProperties"], False)

    def test_reconciliation_request_cannot_carry_command_or_path_fields(self):
        required = set(RECONCILE_SCHEMA["required"])
        self.assertEqual(required, {
            "schema_version", "request_id", "operation", "source_attestation",
            "registry", "project_manifests", "dry_run",
        })
        self.assertFalse(RECONCILE_SCHEMA["additionalProperties"])
        source = RECONCILE_SCHEMA["properties"]["source_attestation"]["properties"]
        self.assertEqual(source["repository"]["const"], "adamtrott78/workspace-control")
        self.assertEqual(source["default_branch"]["const"], "main")


if __name__ == "__main__":
    unittest.main()
