from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

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
        value["controller_policy_sha256"] = activation._controller_policy_digest(
            value
        )
        return value

    def test_candidate_adds_only_codex_workflow_and_preserves_installed_generation(self):
        current = self.predecessor_policy()
        current["control_plane_generation_sha256"] = "9" * 64
        current["controller_policy_sha256"] = activation._controller_policy_digest(
            current
        )
        installed = copy.deepcopy(self.root_policy)
        installed["root_policy_sha256"] = "8" * 64

        candidate_policy, returned_root = activation.build_candidate_policy(
            repo=ROOT,
            installed_root=installed,
            current_policy=current,
        )

        self.assertIs(returned_root, installed)
        self.assertEqual(
            candidate_policy["control_plane_generation_sha256"],
            current["control_plane_generation_sha256"],
        )
        self.assertEqual(candidate_policy["runner_class_id"], activation.TARGET_CLASS)
        self.assertEqual(candidate_policy["max_runners"], 1)
        by_route = {
            row["route_id"]: row
            for row in candidate_policy["trusted_workflows"]
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
        changed = {
            key
            for key in set(current) | set(candidate_policy)
            if current.get(key) != candidate_policy.get(key)
        }
        self.assertEqual(
            changed,
            {"trusted_workflows", "controller_policy_sha256"},
        )

    def test_unrelated_installed_root_digest_does_not_block_controller_local_route(self):
        current = self.predecessor_policy()
        installed = copy.deepcopy(self.root_policy)
        installed["root_policy_sha256"] = "a" * 64
        # Simulate unrelated accepted scientific/runtime evolution.
        installed["runner_classes"][
            activation.candidate.PADATASET_SCIENTIFIC_TARGET_CLASS
        ]["root_envelope_sha256"] = "1" * 64
        installed["runner_classes"][
            activation.candidate.PADATASET_SCIENTIFIC_DUAL_TARGET_CLASS
        ]["root_envelope_sha256"] = "2" * 64

        candidate_policy, _ = activation.build_candidate_policy(
            repo=ROOT,
            installed_root=installed,
            current_policy=current,
        )
        self.assertEqual(
            {row["route_id"] for row in candidate_policy["trusted_workflows"]},
            {"control-validation", "codex-bootstrap"},
        )

    def test_installed_control_small_root_binding_drift_fails_closed(self):
        current = self.predecessor_policy()
        installed = copy.deepcopy(self.root_policy)
        installed["runner_classes"][activation.TARGET_CLASS][
            "scale_set_name"
        ] = "unexpected-scale-set"
        with self.assertRaisesRegex(
            activation.RouteActivationError,
            "installed control-small root binding drift: scale_set_name",
        ):
            activation.build_candidate_policy(
                repo=ROOT,
                installed_root=installed,
                current_policy=current,
            )

    def test_installed_controller_must_match_live_control_small_root(self):
        current = self.predecessor_policy()
        current["runner_prefix"] = "wrong-prefix"
        with self.assertRaisesRegex(
            activation.RouteActivationError,
            "installed control-small controller/root mismatch: runner_prefix",
        ):
            activation.build_candidate_policy(
                repo=ROOT,
                installed_root=copy.deepcopy(self.root_policy),
                current_policy=current,
            )

    def test_helper_no_longer_reconstructs_historical_runtime390_root_predecessor(self):
        self.assertNotIn("_require_root_authority_equivalent(", HELPER)
        self.assertNotIn(
            "previous_root_policy_sha256",
            HELPER[HELPER.index("def build_candidate_policy("):HELPER.index("def build_overlay(")],
        )
        self.assertIn(
            "installed control-small root binding drift",
            HELPER,
        )
        self.assertIn(
            "Codex bootstrap candidate changed non-controller-local fields",
            HELPER,
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

    def test_activation_receipt_binds_effective_root_separately_from_base_manifest(self):
        self.assertIn(
            '"root_policy_sha256": installed_root.get("root_policy_sha256")',
            HELPER,
        )
        self.assertIn(
            '"base_root_policy_sha256": manifest.get("root_policy_sha256")',
            HELPER,
        )
        self.assertNotIn(
            '"authorization_id": authority["authorization_id"],\n'
            '        "root_policy_sha256": manifest.get("root_policy_sha256")',
            HELPER,
        )
        self.assertIn(
            '"base_root_policy_sha256": manifest.get("root_policy_sha256")',
            REC,
        )
        self.assertIn(
            'root_policy.get("root_policy_sha256") != active["root_policy_sha256"]',
            REC,
        )

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
