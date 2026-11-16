import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import inspect
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compiler = load(
    "lambda_ci_policy_compiler_science_activation_tests",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
reconciler = load(
    "lambda_ci_v3_reconciler_science_activation_tests",
    ROOT / "scripts" / "lambda_ci_v3_reconciler.py",
)
activation = load(
    "lambda_ci_v3_padataset_scientific_activation_v1",
    ROOT / "scripts" / "lambda_ci_v3_padataset_scientific_activation_v1.py",
)


class PADatasetScientificActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)

    def predecessor_root(self):
        value = copy.deepcopy(self.compiled["root_projection"])
        value["runner_classes"].pop(activation.TARGET_CLASS)
        return value

    def predecessor_overlay(self):
        value = json.loads(
            (ROOT / "architecture/lambda-ci-deployment-overlay.v1.json").read_text()
        )
        value["classes"].pop(activation.TARGET_CLASS)
        value["routes"].pop(activation.TARGET_ROUTE)
        return value

    def test_candidate_generation_is_exact_plus_one_and_preserves_old_envelopes(self):
        current = self.predecessor_root()
        for policy in current["runner_classes"].values():
            policy["control_plane_generation_sha256"] = "f" * 64
        compiled, artifacts, preserved = activation._candidate_generation(
            ROOT,
            current,
            self.predecessor_overlay(),
        )
        self.assertEqual(
            set(compiled["root_projection"]["runner_classes"]),
            set(current["runner_classes"]) | {activation.TARGET_CLASS},
        )
        self.assertEqual(set(preserved), set(current["runner_classes"]))
        self.assertEqual(len(preserved), 10)
        for class_id, digest in preserved.items():
            self.assertEqual(
                digest,
                current["runner_classes"][class_id]["root_envelope_sha256"],
            )

        overlay = json.loads(artifacts[activation.DEPLOYMENT_OVERLAY][0])
        self.assertEqual(
            overlay["classes"][activation.TARGET_CLASS]["install_state"],
            "INSTALLED",
        )
        self.assertEqual(
            overlay["classes"][activation.TARGET_CLASS]["controller_state"],
            "INACTIVE",
        )
        self.assertEqual(
            overlay["routes"][activation.TARGET_ROUTE]["admission_state"],
            "DISABLED",
        )

    def test_candidate_generation_rejects_preexisting_class_authority_drift(self):
        current = self.predecessor_root()
        class_id = "padataset-gpu-single-public-v1"
        current["runner_classes"][class_id]["max_runners"] += 1
        with self.assertRaisesRegex(
            activation.ScientificActivationError,
            "pre-existing runner class authority drift",
        ):
            activation._candidate_generation(
                ROOT,
                current,
                self.predecessor_overlay(),
            )

    def test_frozen_scientific_target_runtime_and_workflow_bindings(self):
        target = self.compiled["root_projection"]["runner_classes"][
            activation.TARGET_CLASS
        ]
        activation._validate_target_root(target)
        self.assertEqual(
            target["execution_contract"]["execution_profile"],
            "gpu-scientific-single",
        )
        self.assertEqual(target["systemd_profile"]["RuntimeMaxSec"], "4h")
        existing = self.compiled["root_projection"]["runner_classes"][
            "padataset-gpu-single-public-v1"
        ]
        self.assertEqual(
            existing["execution_contract"]["execution_profile"],
            "gpu-small",
        )
        self.assertEqual(existing["systemd_profile"]["RuntimeMaxSec"], "20min")
        runtime = target["bindings"]["runtime"]
        self.assertEqual(runtime["runtime_id"], "padataset-dnns-v1")
        self.assertEqual(runtime["manifest_identity_sha256"], activation.RUNTIME_MANIFEST)
        self.assertEqual(runtime["tree_digest_sha256"], activation.RUNTIME_TREE)
        self.assertEqual(runtime["base_python_sha256"], activation.BASE_PYTHON_SHA)
        self.assertEqual(
            runtime["scientific_data"]["profile_id"],
            activation.DATA_PROFILE,
        )
        self.assertEqual(
            runtime["scientific_data"]["tree_digest_sha256"],
            activation.DATA_DIGEST,
        )
        policy = self.compiled["controller_projections"][activation.TARGET_CLASS]
        self.assertEqual(len(policy["trusted_workflows"]), 1)
        self.assertEqual(policy["trusted_workflows"][0]["path"], activation.WORKFLOW_PATH)
        self.assertEqual(
            policy["trusted_workflows"][0]["blob_sha"],
            activation.WORKFLOW_BLOB,
        )

    def test_authority_requires_exact_operation_bindings_and_fresh_window(self):
        now = datetime.now(timezone.utc)
        expected = {
            "source_head": "a" * 40,
            "target_class_id": activation.TARGET_CLASS,
        }
        payload = {
            "schema_version": 1,
            "authority": "workspace-control-operator",
            "operation": "TEST_OPERATION",
            "authorization_id": "11111111-1111-4111-8111-111111111111",
            "issued_at": (now - timedelta(minutes=1)).isoformat(),
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
            **expected,
        }
        raw = (json.dumps(payload) + "\n").encode()
        with mock.patch.object(
            activation,
            "_require_root_private_file",
            return_value=raw,
        ):
            parsed, parsed_raw = activation._load_authority(
                pathlib.Path("/fake"),
                operation="TEST_OPERATION",
                expected=expected,
            )
        self.assertEqual(parsed, payload)
        self.assertEqual(parsed_raw, raw)

        stale = dict(payload)
        stale["issued_at"] = (now - timedelta(minutes=20)).isoformat()
        stale["expires_at"] = (now - timedelta(minutes=10)).isoformat()
        raw = (json.dumps(stale) + "\n").encode()
        with mock.patch.object(
            activation,
            "_require_root_private_file",
            return_value=raw,
        ):
            with self.assertRaisesRegex(
                activation.ScientificActivationError,
                "not currently valid",
            ):
                activation._load_authority(
                    pathlib.Path("/fake"),
                    operation="TEST_OPERATION",
                    expected=expected,
                )

    def preflight_payload(self, *, confirmed_at=None):
        if confirmed_at is None:
            confirmed_at = datetime.now(timezone.utc).isoformat()
        return {
            "schema_version": 1,
            "mode": "PADATASET_SCIENTIFIC_ACTIVATION_PREFLIGHT_CONFIRMED",
            "repository": "adamtrott78/PADataset",
            "workflow_path": activation.WORKFLOW_PATH,
            "workflow_blob_sha": activation.WORKFLOW_BLOB,
            "active_workflow_runs": 0,
            "scale_set_name": activation.TARGET_SCALE_SET,
            "scale_set_id": 123,
            "assigned_jobs": 0,
            "running_jobs": 0,
            "runtime_manifest_identity_sha256": activation.RUNTIME_MANIFEST,
            "runtime_tree_digest_sha256": activation.RUNTIME_TREE,
            "base_python_sha256": activation.BASE_PYTHON_SHA,
            "scientific_data_profile_id": activation.DATA_PROFILE,
            "scientific_data_tree_digest_sha256": activation.DATA_DIGEST,
            "confirmed_at": confirmed_at,
        }

    def test_activation_preflight_is_exact_and_fresh(self):
        payload = self.preflight_payload()
        raw = (json.dumps(payload) + "\n").encode()
        with mock.patch.object(
            activation,
            "_require_root_private_file",
            return_value=raw,
        ):
            parsed, parsed_raw = activation._validate_preflight(
                pathlib.Path("/fake")
            )
        self.assertEqual(parsed, payload)
        self.assertEqual(parsed_raw, raw)

        stale = self.preflight_payload(
            confirmed_at=(
                datetime.now(timezone.utc) - timedelta(hours=1)
            ).isoformat()
        )
        with mock.patch.object(
            activation,
            "_require_root_private_file",
            return_value=(json.dumps(stale) + "\n").encode(),
        ):
            with self.assertRaisesRegex(
                activation.ScientificActivationError,
                "preflight is stale",
            ):
                activation._validate_preflight(pathlib.Path("/fake"))

    def test_scientific_override_receipt_binds_exact_prior_chain(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            receipt_path = root / "active.json"
            base_source = "1" * 40
            base_root = "2" * 64
            manifest = {
                "source_head": base_source,
                "root_policy_sha256": base_root,
                "entries": [
                    {
                        "destination": destination,
                        "sha256": "a" * 64,
                        "mode": "0644",
                    }
                    for destination in sorted(
                        reconciler.PADATASET_SCIENTIFIC_OVERRIDE_DESTINATIONS
                    )
                ],
            }
            manifest_raw = reconciler._canonical(manifest)
            production = {
                str(reconciler.V3_CONFIG_ROOT / "deployment-overlay.json"):
                    "b" * 64
            }
            overrides = {}
            for destination in sorted(
                reconciler.PADATASET_SCIENTIFIC_OVERRIDE_DESTINATIONS
            ):
                overrides[destination] = {
                    "prior_sha256": production.get(destination, "a" * 64),
                    "sha256": "c" * 64,
                    "mode": "0644",
                }
            additions = {
                destination: {"sha256": "d" * 64, "mode": "0644"}
                for destination in sorted(
                    reconciler.PADATASET_SCIENTIFIC_ADDITION_DESTINATIONS
                )
            }
            payload = {
                "schema_version": 1,
                "mode": "V3_PADATASET_SCIENTIFIC_ADDITIVE_OVERRIDE",
                "phase": "INSTALLED_INACTIVE",
                "base_source_head": base_source,
                "base_install_manifest_sha256": reconciler._sha256(manifest_raw),
                "base_root_policy_sha256": base_root,
                "source_head": "3" * 40,
                "catalog_generation_sha256": "4" * 64,
                "root_policy_sha256": "5" * 64,
                "target_class_id": reconciler.PADATASET_SCIENTIFIC_TARGET_CLASS,
                "target_route_key": reconciler.PADATASET_SCIENTIFIC_TARGET_ROUTE,
                "target_scale_set_name":
                    reconciler.PADATASET_SCIENTIFIC_TARGET_SCALE_SET,
                "target_controller_policy_sha256": "6" * 64,
                "trusted_workflow_blob_sha":
                    reconciler.PADATASET_SCIENTIFIC_WORKFLOW_BLOB,
                "runtime_manifest_identity_sha256":
                    reconciler.PADATASET_SCIENTIFIC_RUNTIME_MANIFEST,
                "runtime_tree_digest_sha256":
                    reconciler.PADATASET_SCIENTIFIC_RUNTIME_TREE,
                "base_python_sha256":
                    reconciler.PADATASET_SCIENTIFIC_BASE_PYTHON_SHA,
                "scientific_data_profile_id":
                    reconciler.PADATASET_SCIENTIFIC_DATA_PROFILE,
                "scientific_data_tree_digest_sha256":
                    reconciler.PADATASET_SCIENTIFIC_DATA_DIGEST,
                "installed_inactive_overlay_sha256": "7" * 64,
                "preserved_root_envelope_sha256": {"legacy-class": "8" * 64},
                "prior_production_overrides": production,
                "managed_artifact_overrides": overrides,
                "managed_artifact_additions": additions,
            }
            receipt_path.write_text(json.dumps(payload) + "\n")
            receipt_path.chmod(0o600)
            with mock.patch.object(
                reconciler,
                "PADATASET_SCIENTIFIC_ACTIVE_RECEIPT",
                receipt_path,
            ):
                parsed = reconciler._padataset_scientific_additive_override(
                    manifest_raw,
                    manifest,
                    production,
                )
            self.assertEqual(parsed, payload)

            payload["managed_artifact_overrides"][
                str(reconciler.V3_CONFIG_ROOT / "root-policy.json")
            ]["prior_sha256"] = "9" * 64
            receipt_path.write_text(json.dumps(payload) + "\n")
            receipt_path.chmod(0o600)
            with mock.patch.object(
                reconciler,
                "PADATASET_SCIENTIFIC_ACTIVE_RECEIPT",
                receipt_path,
            ):
                with self.assertRaisesRegex(
                    reconciler.ReconcileError,
                    "prior digest mismatch",
                ):
                    reconciler._padataset_scientific_additive_override(
                        manifest_raw,
                        manifest,
                        production,
                    )

    def test_effective_state_verifier_checks_target_and_preserved_envelopes(self):
        compiled = self.compiled
        with tempfile.TemporaryDirectory() as td:
            config = pathlib.Path(td)
            (config / "controllers").mkdir()
            root_policy = compiled["root_projection"]
            (config / "root-policy.json").write_text(
                json.dumps(root_policy, indent=2, sort_keys=True) + "\n"
            )
            policy = compiled["controller_projections"][activation.TARGET_CLASS]
            (config / "controllers" / f"{activation.TARGET_CLASS}.json").write_text(
                json.dumps(policy, indent=2, sort_keys=True) + "\n"
            )
            overlay = self.predecessor_overlay()
            overlay["catalog_generation_sha256"] = compiled[
                "catalog_generation_sha256"
            ]
            template = json.loads(
                (ROOT / "architecture/lambda-ci-deployment-overlay.v1.json").read_text()
            )
            overlay["classes"][activation.TARGET_CLASS] = copy.deepcopy(
                template["classes"][activation.TARGET_CLASS]
            )
            overlay["classes"][activation.TARGET_CLASS]["install_state"] = "INSTALLED"
            overlay["classes"][activation.TARGET_CLASS]["controller_state"] = "INACTIVE"
            overlay["routes"][activation.TARGET_ROUTE] = copy.deepcopy(
                template["routes"][activation.TARGET_ROUTE]
            )
            overlay["routes"][activation.TARGET_ROUTE]["admission_state"] = "DISABLED"
            (config / "deployment-overlay.json").write_text(
                json.dumps(overlay, indent=2, sort_keys=True) + "\n"
            )
            receipt = {
                "phase": "INSTALLED_INACTIVE",
                "root_policy_sha256": root_policy["root_policy_sha256"],
                "catalog_generation_sha256": compiled["catalog_generation_sha256"],
                "target_controller_policy_sha256":
                    policy["controller_policy_sha256"],
                "preserved_root_envelope_sha256": {
                    class_id: value["root_envelope_sha256"]
                    for class_id, value in root_policy["runner_classes"].items()
                    if class_id != activation.TARGET_CLASS
                },
            }
            with mock.patch.object(reconciler, "V3_CONFIG_ROOT", config):
                reconciler._verify_padataset_scientific_effective_state(receipt)
                receipt["phase"] = "ACTIVE"
                with self.assertRaisesRegex(
                    reconciler.ReconcileError,
                    "controller overlay state mismatch",
                ):
                    reconciler._verify_padataset_scientific_effective_state(receipt)

    def test_expansion_never_stops_existing_class_controllers(self):
        source = inspect.getsource(activation.expand_inactive)
        stop_lines = [
            line.strip()
            for line in source.splitlines()
            if "systemd.stop(" in line
        ]
        self.assertEqual(stop_lines, ["systemd.stop(PROVISIONER_UNIT)"])
        self.assertNotIn("lambda_ci_v3_production_cutover", source)
        self.assertNotIn("lambda_ci_v3_migration_transaction", source)

    def test_activation_rollback_never_stops_shared_provisioner(self):
        source = inspect.getsource(activation.activate)
        self.assertNotIn("systemd.stop(PROVISIONER_UNIT)", source)
        self.assertIn("systemd.stop(TARGET_CONTROLLER_UNIT)", source)
        self.assertNotIn("workspace-ci-controller@", source)


if __name__ == "__main__":
    unittest.main()
