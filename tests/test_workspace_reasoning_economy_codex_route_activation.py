from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lambda_ci_policy_compiler as compiler  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "codex_route_activation",
    SCRIPTS / "lambda_ci_v3_workspace_control_codex_route_activation_v1.py",
)
activation = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["codex_route_activation"] = activation
spec.loader.exec_module(activation)

REC = (SCRIPTS / "lambda_ci_v3_reconciler.py").read_text()
HELPER = (
    SCRIPTS / "lambda_ci_v3_workspace_control_codex_route_activation_v1.py"
).read_text()


class WorkspaceControlCodexRouteActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compiled = compiler.compile_policy(ROOT)
        cls.root_policy = cls.compiled["root_projection"]
        cls.target = cls.compiled["controller_projections"][
            activation.TARGET_CLASS
        ]

    def predecessor_policy(self) -> dict:
        value = copy.deepcopy(self.target)
        value["trusted_workflows"] = [
            row
            for row in value["trusted_workflows"]
            if row["route_id"] == "control-validation"
        ]
        return value

    def test_candidate_adds_only_codex_workflow_and_preserves_root_authority(self):
        current = self.predecessor_policy()
        candidate, root = activation.build_candidate_policy(
            repo=ROOT,
            installed_root={
                "root_policy_sha256": self.root_policy["root_policy_sha256"]
            },
            current_policy=current,
        )
        self.assertEqual(
            root["root_policy_sha256"],
            self.root_policy["root_policy_sha256"],
        )
        self.assertEqual(candidate["runner_class_id"], activation.TARGET_CLASS)
        self.assertEqual(candidate["max_runners"], 1)
        by_route = {
            row["route_id"]: row
            for row in candidate["trusted_workflows"]
        }
        self.assertEqual(set(by_route), {"control-validation", "codex-bootstrap"})
        self.assertEqual(
            by_route["control-validation"],
            current["trusted_workflows"][0],
        )
        self.assertEqual(
            by_route["codex-bootstrap"]["blob_sha"],
            activation.candidate.WORKSPACE_CONTROL_CODEX_WORKFLOW_BLOB,
        )

    def test_overlay_change_is_additive_and_preserves_existing_state(self):
        current = {
            "catalog_generation_sha256": "a" * 64,
            "classes": {
                activation.TARGET_CLASS: {
                    "install_state": "INSTALLED",
                    "controller_state": "ACTIVE",
                    "containment": {"state": "CLEAR", "source": None},
                },
                "padataset-scientific-single-gpu-v1": {
                    "install_state": "INSTALLED",
                    "controller_state": "ACTIVE",
                    "containment": {"state": "CLEAR", "source": None},
                },
            },
            "routes": {
                "workspace-control:control-validation": {
                    "admission_state": "ENABLED",
                    "source": "existing",
                },
                "padataset:scientific-single-gpu": {
                    "admission_state": "ENABLED",
                    "source": "existing-science",
                },
            },
            "sentinel": {"preserve": True},
        }
        after = activation.build_overlay(current)
        self.assertEqual(current["sentinel"], after["sentinel"])
        self.assertEqual(
            current["routes"]["padataset:scientific-single-gpu"],
            after["routes"]["padataset:scientific-single-gpu"],
        )
        self.assertEqual(
            after["routes"][
                activation.candidate.WORKSPACE_CONTROL_CODEX_TARGET_ROUTE
            ]["admission_state"],
            "ENABLED",
        )
        self.assertNotIn(
            activation.candidate.WORKSPACE_CONTROL_CODEX_TARGET_ROUTE,
            current["routes"],
        )

    def test_already_enabled_route_fails_closed(self):
        current = {
            "classes": {
                activation.TARGET_CLASS: {"controller_state": "ACTIVE"}
            },
            "routes": {
                "workspace-control:control-validation": {
                    "admission_state": "ENABLED"
                },
                activation.candidate.WORKSPACE_CONTROL_CODEX_TARGET_ROUTE: {
                    "admission_state": "ENABLED"
                },
            },
        }
        with self.assertRaisesRegex(
            activation.RouteActivationError,
            "already enabled",
        ):
            activation.build_overlay(current)

    def test_helper_requires_one_shot_root_authority_and_target_quiescence(self):
        for marker in (
            "ACTIVATE_WORKSPACE_CONTROL_CODEX_BOOTSTRAP_ROUTE_V1",
            "require_target_quiescent()",
            "consume_authority(authority, authority_raw)",
            "os.O_EXCL",
            'run_systemctl("stop", TARGET_UNIT)',
            'run_systemctl("start", TARGET_UNIT)',
            "require_snapshot_same(others_before, others_after)",
            "ROLLED_BACK_PREVIOUS_ROUTE_STATE",
            "COMMITTED_ACTIVE_CODEX_BOOTSTRAP_ROUTE",
        ):
            self.assertIn(marker, HELPER)
        self.assertNotIn('run_systemctl("stop", PROVISIONER_UNIT)', HELPER)
        self.assertNotIn('run_systemctl("restart"', HELPER)

    def test_reconciler_layers_codex_route_after_existing_live_overrides(self):
        for marker in (
            "WORKSPACE_CONTROL_CODEX_ROUTE_ACTIVE_RECEIPT",
            "_workspace_control_codex_route_override(",
            "predecessor_overlay_sha256",
            "workspace_codex_overrides",
            "_verify_workspace_control_codex_route_effective_state(",
            "Workspace Control Codex route reservation drift",
            "Workspace Control Codex bootstrap route not enabled",
        ):
            self.assertIn(marker, REC)
        # The final layer must explicitly account for underlying production,
        # scientific, and dual-lane overlay bindings rather than erasing them.
        self.assertIn(
            "if dual_binding is not None:\n                dual_overrides_seen.add(destination)",
            REC,
        )
        self.assertIn(
            "if scientific_binding is not None:\n                scientific_overrides_seen.add(destination)",
            REC,
        )
        self.assertIn(
            "if production_digest is not None:\n                production_overrides_seen.add(destination)",
            REC,
        )

    def test_activation_never_adds_gpu_or_capacity_authority(self):
        root = self.root_policy
        host = root["host_resource_policy"]
        target = root["runner_classes"][activation.TARGET_CLASS]
        self.assertEqual(
            host["migration_mode"]["host_max_active_runners"],
            3,
        )
        self.assertEqual(
            host["project_limits"]["workspace-control"]["max_active_runners"],
            1,
        )
        self.assertEqual(
            host["project_limits"]["padataset"]["max_active_runners"],
            2,
        )
        self.assertEqual(
            host["reservation_policy"]["reserved_project_slots"],
            {"workspace-control": 1},
        )
        self.assertEqual(target["exclusive_resource_claims"], [])


if __name__ == "__main__":
    unittest.main()
