import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_multirepo as multi
import lambda_ci_reconciler as reconciler

REGISTRY = json.loads((ROOT / "architecture/lambda-ci-project-registry.v1.json").read_text())
CONTRACTS = json.loads((ROOT / "architecture/lambda-ci-execution-contracts.v1.json").read_text())
WORKLOAD = json.loads((ROOT / "architecture/lambda-ci-workload-policy.v1.json").read_text())
RESEARCH = json.loads((ROOT / "architecture/lambda-ci-project-research-engine.v2.json").read_text())
PAD = json.loads((ROOT / "architecture/lambda-ci-project-padataset.v1.json").read_text())
SHA = "a" * 40


def request_for(manifest, route_id, *, runner_suffix="abcdef123456"):
    route = manifest["routes"][route_id]
    lane = manifest["derived_identity"]["lanes"][route["lane"]]
    trusted = route["trusted_workflow"]
    trigger = route["trigger"]
    return {
        "schema_version": 2,
        "request_id": "01234567-89ab-5cde-8fab-0123456789ab",
        "project_id": manifest["project_id"],
        "workload_class": route_id,
        "runner_name": lane["runner_prefix"] + runner_suffix,
        "jit_config": "opaque",
        "attestation": {
            "schema_version": 2,
            "source": "github_scale_set_controller",
            "repository": manifest["repository"],
            "scale_set_name": lane["scale_set_name"],
            "job_message_type": "JobAvailable",
            "runner_request_id": 123,
            "workflow_run_id": 456,
            "job_id": "789",
            "job_workflow_ref": (
                f"{manifest['repository']}/{trusted['path']}@refs/heads/{trusted['default_branch']}"
            ),
            "workflow_path": trusted["path"],
            "workflow_default_branch_commit_sha": SHA,
            "workflow_blob_sha": trusted["blob_sha"],
            "event_name": trigger["event_name"],
            "job_display_name": (
                f"wc-admission-v1|workload={route_id}|pr=17|request="
                f"{trigger['command']} {SHA}"
            ),
            "actor_login": "adamtrott78",
            "triggering_actor_login": "adamtrott78",
            "pr_number": 17,
            "pr_state": "open",
            "pr_head_repository": manifest["repository"],
            "candidate_sha": SHA,
            "candidate_verification": "PR_HEAD_MATCH",
            "verified_at": "2026-10-20T00:00:00Z",
        },
    }


class MultiRepoGenericAdmissionTests(unittest.TestCase):
    def test_registry_resolves_distinct_projects(self):
        manifests = {"research-engine": RESEARCH, "padataset": PAD}
        self.assertEqual(
            multi.resolve_project_manifest(REGISTRY, manifests, "research-engine")["repository"],
            "adamtrott78/research-engine",
        )
        self.assertEqual(
            multi.resolve_project_manifest(REGISTRY, manifests, "padataset")["repository"],
            "adamtrott78/PADataset",
        )
        with self.assertRaises(multi.MultiRepoPolicyError):
            multi.resolve_project_manifest(REGISTRY, manifests, "unregistered")

    def test_padataset_unbound_route_fails_closed(self):
        req = request_for(PAD, "cpu-ci")
        with self.assertRaisesRegex(multi.MultiRepoPolicyError, "route is not active"):
            multi.mint_admission(req, PAD, CONTRACTS, WORKLOAD)

    def test_research_route_resolves_semantic_contract_not_route_name(self):
        req = request_for(RESEARCH, "cpu-test")
        admission = multi.mint_admission(
            req,
            RESEARCH,
            CONTRACTS,
            WORKLOAD,
            now=datetime(2026, 10, 20, tzinfo=timezone.utc),
        )
        self.assertEqual(admission["workload_class"], "cpu-test")
        self.assertEqual(admission["execution_profile"], "cpu-test")
        self.assertEqual(
            admission["_generic"]["execution_contract_id"],
            "cpu-public-ci-v1",
        )
        semantic = multi.execution_semantics_from_admission(admission)
        self.assertEqual(semantic["execution_profile"], "cpu-test")
        self.assertEqual(semantic["gpu_count"], 0)
        self.assertEqual(semantic["model_binding_mode"], "FORBIDDEN")

    def test_arbitrary_route_can_reuse_existing_contract_without_source_enum(self):
        manifest = copy.deepcopy(RESEARCH)
        route = copy.deepcopy(manifest["routes"]["cpu-test"])
        route["trusted_workflow"]["path"] = ".github/workflows/new-benchmark.yml"
        route["trusted_workflow"]["blob_sha"] = "b" * 40
        route["trigger"]["command"] = "/lambda-ci-new-benchmark"
        manifest["routes"]["new-benchmark-17"] = route
        req = request_for(manifest, "new-benchmark-17")
        admission = multi.mint_admission(req, manifest, CONTRACTS, WORKLOAD)
        self.assertEqual(admission["workload_class"], "new-benchmark-17")
        self.assertEqual(
            admission["_generic"]["execution_contract_id"], "cpu-public-ci-v1"
        )

    def test_public_repo_fork_head_is_rejected_even_for_allowed_actor(self):
        manifest = copy.deepcopy(PAD)
        route = manifest["routes"]["cpu-ci"]
        route["activation_state"] = "ACTIVE"
        route["trusted_workflow"]["blob_sha"] = "c" * 40
        req = request_for(manifest, "cpu-ci")
        req["attestation"]["pr_head_repository"] = "someone/fork"
        with self.assertRaisesRegex(multi.MultiRepoPolicyError, "fork or foreign"):
            multi.mint_admission(req, manifest, CONTRACTS, WORKLOAD)

    def test_cross_project_scale_set_is_rejected(self):
        req = request_for(RESEARCH, "cpu-test")
        req["attestation"]["scale_set_name"] = "lambda-padataset"
        with self.assertRaisesRegex(multi.MultiRepoPolicyError, "scale-set"):
            multi.mint_admission(req, RESEARCH, CONTRACTS, WORKLOAD)

    def test_generic_heavy_contract_is_still_disabled(self):
        manifest = copy.deepcopy(RESEARCH)
        route = copy.deepcopy(manifest["routes"]["cpu-test"])
        route["lane"] = "gpu"
        route["execution_contract_id"] = "gpu-dual-public-ci-v1"
        route["trusted_workflow"]["path"] = ".github/workflows/heavy.yml"
        route["trusted_workflow"]["blob_sha"] = "d" * 40
        route["trigger"]["command"] = "/lambda-ci-heavy"
        manifest["routes"]["heavy"] = route
        req = request_for(manifest, "heavy")
        with self.assertRaisesRegex(multi.MultiRepoPolicyError, "not admission-enabled"):
            multi.mint_admission(req, manifest, CONTRACTS, WORKLOAD)

    def test_reconciler_is_deterministic_dry_run_and_has_no_commands(self):
        plan = reconciler.plan_reconciliation(
            REGISTRY,
            {"research-engine": RESEARCH, "padataset": PAD},
        )
        self.assertEqual(plan["mode"], "DRY_RUN_ONLY_RUN2")
        self.assertEqual(plan["project_count"], 2)
        serialized = json.dumps(plan, sort_keys=True)
        self.assertNotIn("shell", serialized)
        self.assertNotIn("argv", serialized)
        kinds = {a["kind"] for a in plan["actions"]}
        self.assertEqual(
            kinds,
            {
                "ensure_group",
                "ensure_user",
                "ensure_project_root",
                "install_project_manifest",
                "install_controller_instance_config",
            },
        )

    def test_legacy_admission_semantics_are_derived_without_route_name(self):
        admission = {
            "execution_profile": "gpu-heavy",
            "resource_class": "model_eval_dual_gpu_v1",
            "capability_classes": {
                "payload_network": "GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE",
                "payload_secrets": "CONTROL_PLANE_EPHEMERAL_ONLY",
                "filesystem": "EPHEMERAL_JOB_PLUS_TRUSTED_CACHE_READONLY",
                "cache_access": "TRUSTED_MODEL_RUNTIME_READONLY",
                "state_effect": "NON_SCIENTIFIC_MODEL_EVAL_ONLY",
            },
            "resource_ceiling": {"gpu_uuids": ["g1", "g2"]},
            "models": [{"model_id": "x"}],
            "runtime": {"runtime_id": "y"},
        }
        semantics = multi.execution_semantics_from_admission(admission)
        self.assertEqual(semantics["gpu_count"], 2)
        self.assertEqual(semantics["model_binding_mode"], "REQUIRED_PROMOTED_EXACT")
        self.assertEqual(
            semantics["execution_contract_id"], "legacy-admission-derived-v1"
        )


if __name__ == "__main__":
    unittest.main()
