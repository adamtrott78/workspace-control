from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lambda_ci_policy_compiler as compiler  # noqa: E402

CATALOG = ROOT / "architecture" / "lambda-ci-runner-class-catalog.v1.json"
PROJECT = ROOT / "architecture" / "lambda-ci-project-workspace-control.v1.json"
EVIDENCE = ROOT / "architecture" / "lambda-ci-trusted-workflow-evidence.v1.json"
OVERLAY = ROOT / "architecture" / "lambda-ci-deployment-overlay.v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "lambda-ci-workspace-control-codex-bootstrap.yml"

ROUTE_ID = "codex-bootstrap"
CLASS_ID = "workspace-control-control-small-v1"
WORKFLOW_BLOB = "520da69cfb9b28c81fb1121a16c12d3715892cc7"


class WorkspaceCodexBootstrapAdditiveRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.project = json.loads(PROJECT.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
        cls.compiled = compiler.compile_policy(ROOT)

    def test_exact_default_branch_workflow_blob_is_bound(self) -> None:
        actual = subprocess.check_output(
            ["git", "rev-parse", "HEAD:.github/workflows/lambda-ci-workspace-control-codex-bootstrap.yml"],
            cwd=ROOT,
            text=True,
        ).strip()
        self.assertEqual(actual, WORKFLOW_BLOB)

        route = self.catalog["projects"]["workspace-control"]["routes"][ROUTE_ID]
        self.assertEqual(route["runner_class_id"], CLASS_ID)
        self.assertEqual(route["trusted_workflow"]["blob_sha"], WORKFLOW_BLOB)
        self.assertEqual(
            route["trusted_workflow"]["path"],
            ".github/workflows/lambda-ci-workspace-control-codex-bootstrap.yml",
        )
        self.assertEqual(route["trusted_workflow"]["job_key"], "codex-bootstrap")
        self.assertEqual(route["ingress"]["command"], "/workspace-codex-bootstrap")

        ev = next(
            item
            for item in self.evidence["entries"]
            if item["project_id"] == "workspace-control"
            and item["route_id"] == ROUTE_ID
        )
        self.assertEqual(ev["workflow_blob_sha"], WORKFLOW_BLOB)
        self.assertEqual(
            ev["target_scale_set_name"],
            "lambda-workspace-control-control-small",
        )

    def test_route_is_additive_and_not_live_by_repository_change(self) -> None:
        route = self.project["routes"][ROUTE_ID]
        self.assertEqual(route["activation_state"], "PLANNED_NOT_BOUND")
        self.assertEqual(route["lane"], "cpu")
        self.assertEqual(route["execution_contract_id"], "control-small-ci-v1")
        self.assertEqual(route["bindings"], {"model_id": None, "runtime_id": None})

        overlay = self.overlay["routes"]["workspace-control:codex-bootstrap"]
        self.assertEqual(overlay["admission_state"], "DISABLED")

        existing = self.project["routes"]["control-validation"]
        self.assertEqual(existing["activation_state"], "ACTIVE")
        self.assertEqual(existing["trusted_workflow"]["blob_sha"], "7e361db3a8ead667c047e9dc3fe12908c10eb96a")

    def test_compiler_places_both_routes_on_same_cpu_only_controller(self) -> None:
        controller = self.compiled["controller_projections"][CLASS_ID]
        routes = {
            item["route_id"]: item
            for item in controller["trusted_workflows"]
        }
        self.assertIn("control-validation", routes)
        self.assertIn(ROUTE_ID, routes)
        self.assertEqual(routes[ROUTE_ID]["blob_sha"], WORKFLOW_BLOB)

        root_class = self.compiled["root_projection"]["runner_classes"][CLASS_ID]
        self.assertEqual(root_class["scale_set_name"], "lambda-workspace-control-control-small")
        self.assertEqual(root_class["exclusive_resource_claims"], [])

    def test_reserved_capacity_invariants_are_unchanged(self) -> None:
        host = self.compiled["root_projection"]["host_resource_policy"]
        self.assertEqual(host["migration_mode"]["host_max_active_runners"], 3)
        self.assertEqual(host["project_limits"]["padataset"]["max_active_runners"], 2)
        self.assertEqual(host["project_limits"]["workspace-control"]["max_active_runners"], 1)
        self.assertEqual(
            host["reservation_policy"]["reserved_project_slots"],
            {"workspace-control": 1},
        )


if __name__ == "__main__":
    unittest.main()
