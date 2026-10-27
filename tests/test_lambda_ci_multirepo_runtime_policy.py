import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_multirepo as multi
import lambda_ci_provisioner as provisioner
import lambda_ci_provisioner_service as provisioner_service
import lambda_ci_reconciler as reconciler
import lambda_ci_runtime as runtime

REGISTRY = json.loads((ROOT / "architecture/lambda-ci-project-registry.v1.json").read_text())
CONTRACTS = json.loads((ROOT / "architecture/lambda-ci-execution-contracts.v1.json").read_text())
WORKLOAD = json.loads((ROOT / "architecture/lambda-ci-workload-policy.v1.json").read_text())
PROFILES = json.loads((ROOT / "architecture/lambda-ci-systemd-profiles.v1.json").read_text())
PINS = json.loads((ROOT / "architecture/lambda-ci-upstream-pins.v1.json").read_text())
RESEARCH = json.loads((ROOT / "architecture/lambda-ci-project-research-engine.v2.json").read_text())
PAD = json.loads((ROOT / "architecture/lambda-ci-project-padataset.v1.json").read_text())
WORKSPACE = json.loads((ROOT / "architecture/lambda-ci-project-workspace-control.v1.json").read_text())
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
        manifests = {
            "research-engine": RESEARCH,
            "padataset": PAD,
            "workspace-control": WORKSPACE,
        }
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
        manifest = copy.deepcopy(PAD)
        manifest["routes"]["cpu-ci"]["activation_state"] = "PLANNED_NOT_BOUND"
        manifest["routes"]["cpu-ci"]["trusted_workflow"]["blob_sha"] = None
        req = request_for(manifest, "cpu-ci")
        with self.assertRaisesRegex(multi.MultiRepoPolicyError, "route is not active"):
            multi.mint_admission(req, manifest, CONTRACTS, WORKLOAD)

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

    def _workspace_control_cpu_launch(self):
        manifest = copy.deepcopy(WORKSPACE)
        manifest["status"] = "ACTIVE"
        manifest["routes"]["control-validation"]["activation_state"] = "ACTIVE"
        request = request_for(manifest, "control-validation")
        validated = provisioner.validate_request_v2_generic(
            request,
            manifest,
            CONTRACTS,
            WORKLOAD,
            now=datetime(2026, 10, 20, 0, 0, 5, tzinfo=timezone.utc),
        )
        spec = provisioner.build_generic_launch_spec(
            validated,
            manifest,
            PROFILES,
            PINS,
        )
        runner_dir = Path(spec["paths"]["job_root"]) / validated.request_id / "runner"
        staging_dir = (
            Path(spec["paths"]["staging_cache"]) / validated.request_id
        )
        command = runtime.build_cpu_systemd_command(
            spec,
            runner_dir,
            staging_dir,
            "192.0.2.0/24",
        )
        return manifest, spec, runner_dir, staging_dir, command

    def test_workspace_control_cpu_launch_enforces_exact_forbidden_paths(self):
        manifest, _spec, _runner_dir, _staging_dir, command = (
            self._workspace_control_cpu_launch()
        )
        properties = [
            command[index + 1]
            for index, value in enumerate(command[:-1])
            if value == "-p"
        ]
        inaccessible = [
            value.split("=", 1)[1]
            for value in properties
            if value.startswith("InaccessiblePaths=")
        ]
        self.assertEqual(len(inaccessible), 1)
        denied = inaccessible[0].split(" ")
        self.assertEqual(denied, manifest["forbidden_paths"])

        # Hiding each sibling project root also hides exact descendant trusted
        # caches even though those host directories are intentionally 0755.
        for sibling_cache in (
            RESEARCH["roots"]["trusted_cache"],
            PAD["roots"]["trusted_cache"],
        ):
            self.assertTrue(
                any(
                    sibling_cache == path
                    or sibling_cache.startswith(path.rstrip("/") + "/")
                    for path in denied
                ),
                sibling_cache,
            )

        # The same mount namespace must preserve this project's own roots.
        for own_path in manifest["roots"].values():
            self.assertFalse(
                any(
                    own_path == path
                    or own_path.startswith(path.rstrip("/") + "/")
                    for path in denied
                ),
                own_path,
            )

        self.assertIn("DevicePolicy=closed", properties)
        self.assertIn("ProtectHome=yes", properties)

    def test_workspace_control_cpu_launch_rejects_forbidden_ancestor_of_own_root(self):
        _manifest, spec, runner_dir, staging_dir, _command = (
            self._workspace_control_cpu_launch()
        )
        bad = copy.deepcopy(spec)
        bad["forbidden_paths"] = ["/srv/workspace-ci/workspace-control"]
        with self.assertRaisesRegex(
            runtime.RuntimeLaunchError,
            "overlaps a required project path",
        ):
            runtime.build_cpu_systemd_command(
                bad,
                runner_dir,
                staging_dir,
                "192.0.2.0/24",
            )

    def test_workspace_control_cpu_launch_rejects_malformed_forbidden_path(self):
        _manifest, spec, runner_dir, staging_dir, _command = (
            self._workspace_control_cpu_launch()
        )
        bad = copy.deepcopy(spec)
        bad["forbidden_paths"] = [
            "/srv/workspace-ci/research-engine\nMemoryMax=infinity"
        ]
        with self.assertRaisesRegex(
            runtime.RuntimeLaunchError,
            "unsafe characters",
        ):
            runtime.build_cpu_systemd_command(
                bad,
                runner_dir,
                staging_dir,
                "192.0.2.0/24",
            )

    def test_reconciler_is_deterministic_for_active_projects_and_has_no_commands(self):
        plan = reconciler.plan_reconciliation(
            REGISTRY,
            {
                "research-engine": RESEARCH,
                "padataset": PAD,
                "workspace-control": WORKSPACE,
            },
        )
        self.assertEqual(plan["mode"], "APPLY_READY_V1")
        self.assertEqual(
            plan["active_projects"],
            ["padataset", "research-engine", "workspace-control"],
        )
        self.assertEqual(plan["planned_projects_skipped"], [])
        serialized = json.dumps(plan, sort_keys=True)
        self.assertNotIn("shell", serialized)
        self.assertNotIn("argv", serialized)
        self.assertIn("ci-padataset", serialized)
        self.assertIn("/srv/workspace-ci/padataset", serialized)

    def test_reconciler_plans_only_active_projects(self):
        registry = copy.deepcopy(REGISTRY)
        manifests = {
            "research-engine": copy.deepcopy(RESEARCH),
            "padataset": copy.deepcopy(PAD),
            "workspace-control": copy.deepcopy(WORKSPACE),
        }
        registry["status"] = "ACTIVE"
        registry["projects"]["research-engine"]["activation_state"] = "ACTIVE"
        manifests["research-engine"]["status"] = "ACTIVE"
        registry["projects"]["padataset"]["activation_state"] = (
            "P6_PILOT_PLANNED_NOT_INSTALLED"
        )
        manifests["padataset"]["status"] = "P6_PILOT_PLANNED_NOT_INSTALLED"
        for route in manifests["padataset"]["routes"].values():
            route["activation_state"] = "PLANNED_NOT_BOUND"
            route["trusted_workflow"]["blob_sha"] = None
        plan = reconciler.plan_reconciliation(registry, manifests)
        self.assertEqual(
            plan["active_projects"],
            ["research-engine", "workspace-control"],
        )
        self.assertEqual(plan["planned_projects_skipped"], ["padataset"])
        serialized = json.dumps(plan, sort_keys=True)
        self.assertNotIn("ci-padataset", serialized)
        self.assertNotIn("/srv/workspace-ci/padataset", serialized)
        services = [
            action["service_instance"]
            for action in plan["actions"]
            if action["kind"] == "install_controller_instance_config"
        ]
        self.assertEqual(
            services,
            [
                "workspace-ci-controller@research-engine-cpu.service",
                "workspace-ci-controller@research-engine-gpu.service",
                "workspace-ci-controller@workspace-control-cpu.service",
            ],
        )

    def test_reconciliation_request_rejects_untrusted_workflow_and_removal(self):
        registry = copy.deepcopy(REGISTRY)
        manifests = {
            "research-engine": copy.deepcopy(RESEARCH),
            "padataset": copy.deepcopy(PAD),
            "workspace-control": copy.deepcopy(WORKSPACE),
        }
        registry["status"] = "ACTIVE"
        registry["projects"]["research-engine"]["activation_state"] = "ACTIVE"
        manifests["research-engine"]["status"] = "ACTIVE"
        ceiling = {
            "source_repository": "adamtrott78/workspace-control",
            "source_default_branch": "main",
            "trusted_workflow_path": ".github/workflows/lambda-ci-project-reconcile.yml",
            "trusted_workflow_blob_sha": "b" * 40,
            "allowed_actor_logins": ["adamtrott78"],
        }
        request = {
            "schema_version": 1,
            "request_id": "01234567-89ab-5cde-8fab-0123456789ab",
            "operation": "APPLY_PROJECT_REGISTRY",
            "source_attestation": {
                "repository": "adamtrott78/workspace-control",
                "default_branch": "main",
                "commit_sha": "a" * 40,
                "workflow_path": ".github/workflows/lambda-ci-project-reconcile.yml",
                "workflow_blob_sha": "b" * 40,
                "actor_login": "adamtrott78",
                "verified_at": "2026-10-20T00:00:00Z",
            },
            "registry": {
                "sha256": multi.sha256_json(registry),
                "document": registry,
            },
            "project_manifests": [
                {
                    "project_id": project_id,
                    "sha256": multi.sha256_json(manifest),
                    "document": manifest,
                }
                for project_id, manifest in sorted(manifests.items())
            ],
            "dry_run": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            installed = Path(tmp) / "registry.json"
            validated = reconciler.validate_reconciliation_request(
                request,
                ceiling=ceiling,
                execution_contracts=CONTRACTS,
                installed_registry_path=installed,
            )
            self.assertEqual(
                validated["plan"]["active_projects"],
                ["padataset", "research-engine", "workspace-control"],
            )
            bad = copy.deepcopy(request)
            bad["source_attestation"]["workflow_blob_sha"] = "c" * 40
            with self.assertRaisesRegex(reconciler.ReconcileError, "workflow blob"):
                reconciler.validate_reconciliation_request(
                    bad,
                    ceiling=ceiling,
                    execution_contracts=CONTRACTS,
                    installed_registry_path=installed,
                )

            installed.write_text(json.dumps(registry))
            removed = copy.deepcopy(request)
            del removed["registry"]["document"]["projects"]["padataset"]
            removed["registry"]["sha256"] = multi.sha256_json(
                removed["registry"]["document"]
            )
            removed["project_manifests"] = [
                item
                for item in removed["project_manifests"]
                if item["project_id"] != "padataset"
            ]
            with self.assertRaisesRegex(reconciler.ReconcileError, "removal"):
                reconciler.validate_reconciliation_request(
                    removed,
                    ceiling=ceiling,
                    execution_contracts=CONTRACTS,
                    installed_registry_path=installed,
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


    def test_request_digest_is_stable_across_github_lifecycle_metadata(self):
        available = request_for(RESEARCH, "cpu-test")
        assigned = copy.deepcopy(available)
        assigned["jit_config"] = "different-ephemeral-jit"
        assigned["attestation"]["verified_at"] = "2026-10-20T00:01:00Z"
        assigned["attestation"]["job_message_type"] = "JobAssigned"
        assigned["attestation"]["runner_request_id"] = 0
        self.assertEqual(
            multi.request_digest(available),
            multi.request_digest(assigned),
        )

    def test_generic_launch_spec_derives_project_identity_and_paths(self):
        req_data = request_for(RESEARCH, "cpu-test")
        req = provisioner.validate_request_v2_generic(
            req_data,
            RESEARCH,
            CONTRACTS,
            WORKLOAD,
            now=datetime(2026, 10, 20, tzinfo=timezone.utc),
        )
        spec = provisioner.build_launch_spec(req, RESEARCH, PROFILES, PINS)
        self.assertEqual(spec["run_as"]["user"], "ci-research-engine")
        self.assertEqual(spec["run_as"]["group"], "ci-research-engine")
        self.assertEqual(
            spec["paths"]["job_root"],
            "/srv/workspace-ci/research-engine/jobs",
        )
        self.assertEqual(
            spec["execution_contract"]["execution_contract_id"],
            "cpu-public-ci-v1",
        )
        self.assertEqual(spec["resources"]["gpu_uuids"], [])
        self.assertIsNone(spec["model_binding"])
        self.assertIsNone(spec["runtime_binding"])

    def test_padataset_gpu_canary_contract_needs_no_runtime_or_model_binding(self):
        manifest = copy.deepcopy(PAD)
        route = manifest["routes"]["gpu-ci"]
        route["activation_state"] = "ACTIVE"
        route["trusted_workflow"]["blob_sha"] = "c" * 40
        req_data = request_for(manifest, "gpu-ci")
        req = provisioner.validate_request_v2_generic(
            req_data,
            manifest,
            CONTRACTS,
            WORKLOAD,
            now=datetime(2026, 10, 20, tzinfo=timezone.utc),
        )
        spec = provisioner.build_launch_spec(req, manifest, PROFILES, PINS)
        self.assertEqual(spec["run_as"]["user"], "ci-padataset")
        self.assertEqual(spec["profile"], "gpu-small")
        self.assertEqual(
            spec["resources"]["gpu_uuids"],
            ["GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"],
        )
        self.assertIsNone(spec["model_binding"])
        self.assertIsNone(spec["runtime_binding"])
        self.assertEqual(
            spec["execution_contract"]["execution_contract_id"],
            "gpu-single-public-ci-v1",
        )

    def test_lane_quarantine_is_project_scoped_in_generic_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = provisioner_service.StateStore(Path(tmp))
            research = store.lane_quarantine_path(
                "gpu-small", project_id="research-engine"
            )
            padataset = store.lane_quarantine_path(
                "gpu-small", project_id="padataset"
            )
            legacy = store.lane_quarantine_path("gpu-small")
            self.assertNotEqual(research, padataset)
            self.assertNotEqual(research, legacy)
            self.assertEqual(
                research.name,
                "_lane-quarantine-research-engine-gpu-small.json",
            )
            self.assertEqual(
                padataset.name,
                "_lane-quarantine-padataset-gpu-small.json",
            )

    def test_generic_provisioner_reloads_registry_manifests_without_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = root / "registry.json"
            manifest_dir = root / "projects"
            manifest_dir.mkdir()
            registry = copy.deepcopy(REGISTRY)
            research = copy.deepcopy(RESEARCH)
            padataset = copy.deepcopy(PAD)
            workspace = copy.deepcopy(WORKSPACE)
            registry["projects"]["padataset"]["activation_state"] = (
                "P6_PILOT_PLANNED_NOT_INSTALLED"
            )
            padataset["status"] = "P6_PILOT_PLANNED_NOT_INSTALLED"
            for route in padataset["routes"].values():
                route["activation_state"] = "PLANNED_NOT_BOUND"
                route["trusted_workflow"]["blob_sha"] = None
            registry_path.write_text(json.dumps(registry))
            (manifest_dir / "research-engine.json").write_text(json.dumps(research))
            (manifest_dir / "padataset.json").write_text(json.dumps(padataset))
            (manifest_dir / "workspace-control.json").write_text(json.dumps(workspace))
            service = provisioner_service.ProvisionerService(
                manifest=None,
                profiles=PROFILES,
                pins=PINS,
                workload_policy=WORKLOAD,
                state_store=provisioner_service.StateStore(root / "state"),
                controller_uid=1000,
                registry=registry,
                project_manifests={
                    "research-engine": research,
                    "padataset": padataset,
                    "workspace-control": workspace,
                },
                execution_contracts=CONTRACTS,
                registry_path=registry_path,
                manifest_dir=manifest_dir,
            )
            first = service._manifest_for_request({"project_id": "padataset"})
            self.assertEqual(first["status"], "P6_PILOT_PLANNED_NOT_INSTALLED")
            padataset["status"] = "ACTIVE"
            registry["projects"]["padataset"]["activation_state"] = "ACTIVE"
            registry_path.write_text(json.dumps(registry))
            (manifest_dir / "padataset.json").write_text(json.dumps(padataset))
            second = service._manifest_for_request({"project_id": "padataset"})
            self.assertEqual(second["status"], "ACTIVE")
            self.assertEqual(
                service.registry["projects"]["padataset"]["activation_state"],
                "ACTIVE",
            )

    def test_generic_provisioner_service_resolves_registry_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = provisioner_service.ProvisionerService(
                manifest=None,
                profiles=PROFILES,
                pins=PINS,
                workload_policy=WORKLOAD,
                state_store=provisioner_service.StateStore(Path(tmp)),
                controller_uid=1000,
                registry=REGISTRY,
                project_manifests={
                    "research-engine": RESEARCH,
                    "padataset": PAD,
                    "workspace-control": WORKSPACE,
                },
                execution_contracts=CONTRACTS,
            )
            self.assertEqual(
                service._manifest_for_request({"project_id": "padataset"})[
                    "repository"
                ],
                "adamtrott78/PADataset",
            )
            with self.assertRaises(provisioner.PolicyError):
                service._manifest_for_request({"project_id": "unknown"})

    def test_reconciler_renders_deterministic_non_secret_controller_env(self):
        cpu = reconciler.render_controller_env(PAD, "cpu")
        gpu = reconciler.render_controller_env(PAD, "gpu")
        self.assertIn("WORKSPACE_CI_PROJECT_ID=padataset\n", cpu)
        self.assertIn("WORKSPACE_CI_LANE=cpu\n", cpu)
        self.assertIn("WORKSPACE_CI_SCALESET_NAME=lambda-padataset\n", cpu)
        self.assertIn("WORKSPACE_CI_LANE=gpu\n", gpu)
        self.assertIn(
            "WORKSPACE_CI_SCALESET_NAME=lambda-padataset-gpu\n",
            gpu,
        )
        for forbidden in ("TOKEN=", "PRIVATE_KEY=", "PASSWORD=", "sudo", "ExecStart"):
            self.assertNotIn(forbidden, cpu + gpu)
        self.assertEqual(
            reconciler.controller_env_sha256(PAD, "cpu"),
            reconciler.controller_env_sha256(PAD, "cpu"),
        )


if __name__ == "__main__":
    unittest.main()
