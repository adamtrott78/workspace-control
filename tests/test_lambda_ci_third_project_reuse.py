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
import lambda_ci_provisioner as provisioner
import lambda_ci_reconciler as reconciler

REGISTRY = json.loads(
    (ROOT / "architecture/lambda-ci-project-registry.v1.json").read_text()
)
CONTRACTS = json.loads(
    (ROOT / "architecture/lambda-ci-execution-contracts.v1.json").read_text()
)
WORKLOAD = json.loads(
    (ROOT / "architecture/lambda-ci-workload-policy.v1.json").read_text()
)
PROFILES = json.loads(
    (ROOT / "architecture/lambda-ci-systemd-profiles.v1.json").read_text()
)
PINS = json.loads(
    (ROOT / "architecture/lambda-ci-upstream-pins.v1.json").read_text()
)
RESEARCH = json.loads(
    (ROOT / "architecture/lambda-ci-project-research-engine.v2.json").read_text()
)
PAD = json.loads(
    (ROOT / "architecture/lambda-ci-project-padataset.v1.json").read_text()
)
WORKSPACE = json.loads(
    (ROOT / "architecture/lambda-ci-project-workspace-control.v1.json").read_text()
)
FUTURE = json.loads(
    (ROOT / "tests/fixtures/lambda-ci-project-future-research.v2.json").read_text()
)
SHA = "a" * 40


def request_for(manifest, route_id):
    route = manifest["routes"][route_id]
    lane = manifest["derived_identity"]["lanes"][route["lane"]]
    trusted = route["trusted_workflow"]
    trigger = route["trigger"]
    return {
        "schema_version": 2,
        "request_id": "01234567-89ab-5cde-8fab-0123456789ab",
        "project_id": manifest["project_id"],
        "workload_class": route_id,
        "runner_name": lane["runner_prefix"] + "abcdef123456",
        "jit_config": "b3BhcXVl",
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
                f"{manifest['repository']}/{trusted['path']}"
                f"@refs/heads/{trusted['default_branch']}"
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
            "verified_at": "2026-10-22T00:00:00Z",
        },
    }


def registry_with_future():
    registry = copy.deepcopy(REGISTRY)
    registry["registry_epoch"] += 1
    registry["projects"]["future-research"] = {
        "repository": FUTURE["repository"],
        "repository_visibility": FUTURE["repository_visibility"],
        "manifest_source_path": (
            "architecture/lambda-ci-project-future-research.v2.json"
        ),
        "activation_state": "ACTIVE",
        "lanes": ["cpu", "gpu"],
    }
    return registry


class ThirdProjectReuseContractTests(unittest.TestCase):
    def test_future_project_identity_is_entirely_derived(self):
        multi.validate_project_manifest_derivations(FUTURE)
        self.assertEqual(
            FUTURE["derived_identity"],
            multi.derive_project_identity("future-research"),
        )
        self.assertEqual(
            FUTURE["derived_identity"]["runner_user"],
            "ci-future-research",
        )
        self.assertEqual(
            FUTURE["derived_identity"]["lanes"]["cpu"]["scale_set_name"],
            "lambda-future-research",
        )
        self.assertEqual(
            FUTURE["derived_identity"]["lanes"]["gpu"]["scale_set_name"],
            "lambda-future-research-gpu",
        )

    def test_registry_plus_manifest_is_enough_for_reconciliation_plan(self):
        registry = registry_with_future()
        manifests = {
            "research-engine": RESEARCH,
            "padataset": PAD,
            "workspace-control": WORKSPACE,
            "future-research": FUTURE,
        }
        resolved = multi.resolve_project_manifest(
            registry,
            manifests,
            "future-research",
        )
        self.assertEqual(resolved, FUTURE)

        plan = reconciler.plan_reconciliation(registry, manifests)
        self.assertEqual(
            plan["active_projects"],
            ["future-research", "padataset", "research-engine", "workspace-control"],
        )
        self.assertEqual(plan["planned_projects_skipped"], [])

        serialized = json.dumps(plan, sort_keys=True)
        self.assertIn("ci-future-research", serialized)
        self.assertIn("/srv/workspace-ci/future-research", serialized)
        self.assertIn("lambda-future-research", serialized)
        self.assertNotIn('"shell"', serialized)
        self.assertNotIn('"argv"', serialized)

        services = {
            action["service_instance"]
            for action in plan["actions"]
            if action["kind"] == "install_controller_instance_config"
        }
        self.assertIn(
            "workspace-ci-controller@future-research-cpu.service",
            services,
        )
        self.assertIn(
            "workspace-ci-controller@future-research-gpu.service",
            services,
        )

    def test_existing_cpu_and_gpu_contracts_admit_future_project(self):
        expected = {
            "cpu-ci": ("cpu-test", "cpu-public-ci-v1", []),
            "gpu-ci": (
                "gpu-small",
                "gpu-single-public-ci-v1",
                ["GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"],
            ),
        }

        for route_id, (profile, contract_id, gpu_uuids) in expected.items():
            req_data = request_for(FUTURE, route_id)
            admission = multi.mint_admission(
                req_data,
                FUTURE,
                CONTRACTS,
                WORKLOAD,
                now=datetime(2026, 10, 22, tzinfo=timezone.utc),
            )
            self.assertEqual(admission["project"]["project_id"], "future-research")
            self.assertEqual(admission["execution_profile"], profile)
            self.assertEqual(
                admission["_generic"]["execution_contract_id"],
                contract_id,
            )

            req = provisioner.validate_request_v2_generic(
                req_data,
                FUTURE,
                CONTRACTS,
                WORKLOAD,
                now=datetime(2026, 10, 22, tzinfo=timezone.utc),
            )
            spec = provisioner.build_launch_spec(
                req,
                FUTURE,
                PROFILES,
                PINS,
            )
            self.assertEqual(spec["run_as"]["user"], "ci-future-research")
            self.assertEqual(
                spec["paths"]["job_root"],
                "/srv/workspace-ci/future-research/jobs",
            )
            self.assertEqual(spec["profile"], profile)
            self.assertEqual(spec["resources"]["gpu_uuids"], gpu_uuids)
            self.assertIsNone(spec["model_binding"])
            self.assertIsNone(spec["runtime_binding"])

    def test_public_future_project_retains_fork_denial(self):
        req = request_for(FUTURE, "cpu-ci")
        req["attestation"]["pr_head_repository"] = "someone/fork"
        with self.assertRaisesRegex(
            multi.MultiRepoPolicyError,
            "fork or foreign",
        ):
            multi.mint_admission(
                req,
                FUTURE,
                CONTRACTS,
                WORKLOAD,
            )

    def test_future_project_controller_env_is_generic_and_non_secret(self):
        cpu = reconciler.render_controller_env(FUTURE, "cpu")
        gpu = reconciler.render_controller_env(FUTURE, "gpu")

        self.assertIn("WORKSPACE_CI_PROJECT_ID=future-research\n", cpu)
        self.assertIn("WORKSPACE_CI_LANE=cpu\n", cpu)
        self.assertIn(
            "WORKSPACE_CI_SCALESET_NAME=lambda-future-research\n",
            cpu,
        )
        self.assertIn("WORKSPACE_CI_LANE=gpu\n", gpu)
        self.assertIn(
            "WORKSPACE_CI_SCALESET_NAME=lambda-future-research-gpu\n",
            gpu,
        )

        for forbidden in (
            "TOKEN=",
            "PRIVATE_KEY=",
            "PASSWORD=",
            "sudo",
            "ExecStart",
        ):
            self.assertNotIn(forbidden, cpu + gpu)


if __name__ == "__main__":
    unittest.main()
