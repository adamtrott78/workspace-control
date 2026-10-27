import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_maintenance_service as maintenance


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def git_blob_sha(path):
    raw = (ROOT / path).read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


class ControlPlaneP1ContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_json(
            "architecture/lambda-ci-project-workspace-control.v1.json"
        )
        self.registry = load_json("architecture/lambda-ci-project-registry.v1.json")
        self.contracts = load_json(
            "architecture/lambda-ci-execution-contracts.v1.json"
        )
        self.workload = load_json("architecture/lambda-ci-workload-policy.v1.json")
        self.profiles = load_json("architecture/lambda-ci-systemd-profiles.v1.json")

    def test_workspace_control_remains_not_installed_and_cpu_only(self):
        entry = self.registry["projects"]["workspace-control"]
        self.assertEqual(entry["activation_state"], "MIGRATION_CANDIDATE_NOT_INSTALLED")
        self.assertEqual(entry["lanes"], ["cpu"])
        self.assertEqual(
            entry["manifest_source_path"],
            "architecture/lambda-ci-project-workspace-control.v1.json",
        )

        self.assertEqual(
            self.manifest["status"],
            "MIGRATION_CANDIDATE_NOT_INSTALLED",
        )
        self.assertEqual(self.manifest["concurrency"], 1)
        route = self.manifest["routes"]["control-validation"]
        self.assertEqual(route["activation_state"], "PLANNED_NOT_BOUND")
        self.assertEqual(route["lane"], "cpu")
        self.assertFalse(route["trigger"]["fork_pr_execution_allowed"])
        self.assertEqual(route["trigger"]["allowed_actor_logins"], ["adamtrott78"])

    def test_manifest_pins_exact_owner_commanded_workflow_blob(self):
        route = self.manifest["routes"]["control-validation"]
        workflow = route["trusted_workflow"]
        path = workflow["path"]
        self.assertEqual(
            path,
            ".github/workflows/lambda-ci-workspace-control-validation.yml",
        )
        self.assertEqual(workflow["default_branch"], "main")
        self.assertEqual(workflow["blob_sha"], git_blob_sha(path))

        raw = (ROOT / path).read_text(encoding="utf-8")
        self.assertIn("github.actor == 'adamtrott78'", raw)
        self.assertIn("github.event.comment.author_association == 'OWNER'", raw)
        self.assertIn("startsWith(github.event.comment.body, '/workspace-control-validate ')", raw)
        self.assertIn("runs-on: lambda-workspace-control", raw)
        self.assertNotIn("pull_request:\n", raw)
        self.assertNotIn("push:\n", raw)

    def test_control_small_contract_is_bounded_and_gpu_free(self):
        route = self.manifest["routes"]["control-validation"]
        contract = self.contracts["contracts"][route["execution_contract_id"]]
        self.assertEqual(contract["lifecycle"], "P1_CONTROL_PILOT_REVIEW_REQUIRED")
        self.assertEqual(contract["execution_profile"], "control-small")
        self.assertEqual(contract["resource_class"], "control_small_v1")
        self.assertEqual(contract["gpu_count"], 0)
        self.assertEqual(contract["model_binding_mode"], "FORBIDDEN")

        resource = self.workload["resource_classes"]["control_small_v1"]
        self.assertEqual(resource["execution_profile"], "control-small")
        self.assertEqual(resource["max_runtime_seconds"], 600)
        self.assertEqual(resource["gpu_count"], 0)

        profile = self.profiles["profiles"]["control-small"]
        self.assertEqual(profile["CPUQuota"], "200%")
        self.assertEqual(profile["MemoryHigh"], "4G")
        self.assertEqual(profile["MemoryMax"], "8G")
        self.assertEqual(profile["RuntimeMaxSec"], "10min")
        self.assertEqual(profile["DeviceAllow"], [])
        self.assertEqual(profile["CUDA_VISIBLE_DEVICES"], "")

    def test_workspace_control_isolation_forbidden_paths_are_preserved(self):
        forbidden = set(self.manifest["forbidden_paths"])
        for required in {
            "/home/atrott",
            "/var/run/docker.sock",
            "/run/docker.sock",
            "/srv/workspace-ci/research-engine",
            "/srv/workspace-ci/padataset",
            "/var/lib/workspace-ci/provisioner",
            "/var/lib/workspace-ci/reconciler",
            "/var/lib/workspace-ci/controller",
            "/run/workspace-ci",
        }:
            self.assertIn(required, forbidden)
        isolation = self.manifest["isolation"]
        self.assertTrue(isolation["unique_project_uid_required"])
        self.assertTrue(isolation["sibling_project_roots_inaccessible"])
        self.assertTrue(isolation["control_plane_state_inaccessible"])

    def test_maintenance_root_surface_is_finite_and_not_shell_shaped(self):
        self.assertEqual(
            maintenance.ALLOWED_OPERATIONS,
            {
                "DIAGNOSE_LANE",
                "RESTART_CONTROLLER",
                "QUIESCE_LANE_FOR_RECOVERY",
                "RESUME_LANE_AFTER_RESET",
            },
        )
        source = (ROOT / "scripts/lambda_ci_maintenance_service.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("shell=True", source)
        self.assertNotIn('"command"', source)
        root_unit = (
            ROOT / "systemd/workspace-ci-maintenance.service"
        ).read_text(encoding="utf-8")
        self.assertIn("RestrictAddressFamilies=AF_UNIX", root_unit)
        self.assertNotIn("AF_INET", root_unit)
        self.assertIn("DevicePolicy=closed", root_unit)

    def test_maintenance_controller_is_not_l1_and_has_no_gpu_or_research_root_access(self):
        unit = (
            ROOT / "systemd/workspace-ci-maintenance-controller.service"
        ).read_text(encoding="utf-8")
        self.assertIn("User=ci-maintenance", unit)
        self.assertIn("Group=workspace-ci-maintenance", unit)
        self.assertIn("DevicePolicy=closed", unit)
        self.assertIn("InaccessiblePaths=/home/atrott", unit)
        self.assertIn("/srv/workspace-ci", unit)
        self.assertNotIn("runs-on", unit)

    def test_controller_capacity_remains_one(self):
        source = (
            ROOT / "controller/lambda-ci-controller/main.go"
        ).read_text(encoding="utf-8")
        self.assertRegex(source, r"maxRunners\s*=\s*1")


if __name__ == "__main__":
    unittest.main()
