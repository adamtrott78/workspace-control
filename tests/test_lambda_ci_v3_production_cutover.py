import copy
from datetime import datetime, timedelta, timezone
import importlib.util
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
    "lambda_ci_policy_compiler_prod_cutover_tests",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
production = load(
    "lambda_ci_v3_production_cutover_tests",
    ROOT / "scripts" / "lambda_ci_v3_production_cutover.py",
)


class FakeSystemd:
    def __init__(self, active, enabled):
        self.active_state = dict(active)
        self.enabled_state = dict(enabled)
        self.events = []

    def active(self, unit):
        return bool(self.active_state.get(unit, False))

    def enabled(self, unit):
        return bool(self.enabled_state.get(unit, False))

    def start(self, unit):
        self.events.append(("start", unit))
        self.active_state[unit] = True

    def stop(self, unit):
        self.events.append(("stop", unit))
        self.active_state[unit] = False

    def enable(self, unit):
        self.events.append(("enable", unit))
        self.enabled_state[unit] = True

    def disable(self, unit):
        self.events.append(("disable", unit))
        self.enabled_state[unit] = False

    def list_units(self):
        return sorted(
            set(self.active_state)
            | set(self.enabled_state)
        )


class ProductionCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_inputs = compiler.load_inputs(ROOT)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.source_head = "a" * 40
        self.workflow_raw = {
            "workspace-control:control-validation": (
                b"name: test\njobs:\n  control-validation:\n"
                b"    runs-on: lambda-workspace-control\n"
            ),
            "padataset:cpu-ci": (
                b"name: test\njobs:\n  padataset-cpu:\n"
                b"    runs-on: lambda-padataset\n"
            ),
            "padataset:gpu-ci": (
                b"name: test\njobs:\n  padataset-gpu:\n"
                b"    runs-on: lambda-padataset-gpu\n"
            ),
        }
        self.inputs = copy.deepcopy(self.real_inputs)
        for route_key, spec in production.ROUTES.items():
            blob = production._git_blob_sha(self.workflow_raw[route_key])
            route = self.inputs["catalog"]["projects"][
                spec["project_id"]
            ]["routes"][spec["route_id"]]
            route["trusted_workflow"]["blob_sha"] = blob
            matches = [
                item
                for item in self.inputs["workflow_evidence"]["entries"]
                if item["project_id"] == spec["project_id"]
                and item["route_id"] == spec["route_id"]
            ]
            self.assertEqual(len(matches), 1)
            matches[0]["workflow_blob_sha"] = blob

        self.base_compiled = compiler.compile_from_inputs(
            copy.deepcopy(self.inputs)
        )
        overlay = json.loads(
            (
                ROOT
                / "architecture/lambda-ci-deployment-overlay.v1.json"
            ).read_text()
        )
        for state in overlay["classes"].values():
            state["install_state"] = "INSTALLED"
            state["controller_state"] = "INACTIVE"
        for state in overlay["routes"].values():
            state["admission_state"] = "DISABLED"
        self.live_overlay = overlay

        with mock.patch.object(
            production.compiler,
            "load_inputs",
            return_value=self.inputs,
        ):
            self.result = production.build_generation(
                ROOT,
                self.workflow_raw,
                self.live_overlay,
                source_head=self.source_head,
            )

    def test_retarget_changes_only_exact_runs_on_line(self):
        for route_key, spec in production.ROUTES.items():
            old = self.workflow_raw[route_key].decode()
            new = self.result["rendered_workflows"][route_key].decode()
            expected = old.replace(
                f"runs-on: {spec['legacy_scale_set_name']}",
                f"runs-on: {spec['target_scale_set_name']}",
            )
            self.assertEqual(new, expected)
            self.assertNotEqual(
                production._git_blob_sha(self.workflow_raw[route_key]),
                production._git_blob_sha(
                    self.result["rendered_workflows"][route_key]
                ),
            )

    def test_generation_changes_controller_workflow_pins_not_root_authority(self):
        manifest = self.result["manifest"]
        self.assertEqual(
            manifest["root_policy_sha256"],
            self.base_compiled["root_projection"]["root_policy_sha256"],
        )
        self.assertEqual(
            manifest["accepted_runner_class_ids"],
            list(production.ACCEPTED_CLASSES),
        )
        for route_key, spec in production.ROUTES.items():
            policy = self.result["controller_policies"][
                spec["runner_class_id"]
            ]
            self.assertEqual(len(policy["trusted_workflows"]), 1)
            self.assertEqual(
                policy["trusted_workflows"][0]["blob_sha"],
                manifest["workflow_bindings"][route_key]["new_blob_sha"],
            )

    def test_overlay_activates_only_accepted_v3_and_never_research(self):
        active = self.result["active_overlay"]
        committed = self.result["committed_overlay"]
        for class_id, state in active["classes"].items():
            self.assertEqual(
                state["controller_state"],
                "ACTIVE"
                if class_id in production.ACCEPTED_CLASSES
                else "INACTIVE",
            )
        for route_key, state in active["routes"].items():
            self.assertEqual(
                state["admission_state"],
                "ENABLED"
                if route_key in production.ROUTES
                else "DISABLED",
            )
        for spec in production.ROUTES.values():
            self.assertEqual(
                active["legacy"]["controllers"][
                    spec["legacy_controller_key"]
                ],
                "PRESENT_INACTIVE",
            )
            self.assertEqual(
                active["legacy"]["scale_sets"][
                    spec["legacy_scale_set_name"]
                ],
                "DRAINING",
            )
            self.assertEqual(
                committed["legacy"]["controllers"][
                    spec["legacy_controller_key"]
                ],
                "RETIRED",
            )
            self.assertEqual(
                committed["legacy"]["scale_sets"][
                    spec["legacy_scale_set_name"]
                ],
                "RETIRED",
            )
        self.assertEqual(
            committed["legacy"]["controllers"]["research-engine-cpu"],
            self.live_overlay["legacy"]["controllers"]["research-engine-cpu"],
        )
        self.assertEqual(
            committed["legacy"]["controllers"]["research-engine-gpu"],
            "PRESENT_INACTIVE",
        )
        self.assertEqual(
            committed["legacy"]["scale_sets"]["lambda-research-engine"],
            "PRESENT",
        )
        self.assertEqual(
            committed["legacy"]["scale_sets"][
                "lambda-research-engine-gpu"
            ],
            "PRESENT",
        )

    def test_duplicate_or_missing_runs_on_fails_closed(self):
        spec = production.ROUTES["padataset:cpu-ci"]
        with self.assertRaisesRegex(
            production.CutoverError,
            "expected exactly one",
        ):
            production._retarget_workflow(
                b"jobs:\n  x:\n    runs-on: elsewhere\n",
                legacy_scale_set_name=spec["legacy_scale_set_name"],
                target_scale_set_name=spec["target_scale_set_name"],
            )
        duplicate = (
            b"jobs:\n  a:\n    runs-on: lambda-padataset\n"
            b"  b:\n    runs-on: lambda-padataset\n"
        )
        with self.assertRaisesRegex(
            production.CutoverError,
            "expected exactly one",
        ):
            production._retarget_workflow(
                duplicate,
                legacy_scale_set_name=spec["legacy_scale_set_name"],
                target_scale_set_name=spec["target_scale_set_name"],
            )

    def _install_fixture(self):
        config = self.base / "etc"
        state = self.base / "state"
        config.mkdir()
        state.mkdir()
        migration_root = state / "migration"
        authority_root = state / "authority"
        provisioner = state / "provisioner"
        migration_root.mkdir(mode=0o700)
        authority_root.mkdir(mode=0o700)
        provisioner.mkdir()

        root_policy = self.base_compiled["root_projection"]
        (config / "controllers").mkdir()
        (config / "root-policy.json").write_text(
            json.dumps(root_policy, indent=2, sort_keys=True) + "\n"
        )
        (config / "deployment-overlay.json").write_text(
            json.dumps(self.live_overlay, indent=2, sort_keys=True) + "\n"
        )
        for class_id in production.ACCEPTED_CLASSES:
            (config / "controllers" / f"{class_id}.json").write_text(
                json.dumps(
                    self.base_compiled["controller_projections"][class_id],
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

        base_manifest = {
            "schema_version": 1,
            "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
            "source_head": "b" * 40,
            "root_policy_sha256": root_policy["root_policy_sha256"],
            "runner_class_count": 9,
            "entries": [],
        }
        (config / "install-manifest.json").write_text(
            json.dumps(base_manifest, indent=2, sort_keys=True) + "\n"
        )

        generation = self.base / "generation"
        production.write_generation(self.result, generation)

        authority = {
            "schema_version": 1,
            "authority": "workspace-control-operator",
            "operation": "CUTOVER_V3_PRODUCTION_GENERATION",
            "authorization_id": "11111111-2222-3333-4444-555555555555",
            "source_head": self.source_head,
            "production_generation_sha256":
                self.result["manifest"][
                    "production_generation_sha256"
                ],
            "root_policy_sha256": root_policy["root_policy_sha256"],
            "accepted_runner_class_ids":
                list(production.ACCEPTED_CLASSES),
            "workflow_blob_shas": {
                key: value["new_blob_sha"]
                for key, value in self.result["manifest"][
                    "workflow_bindings"
                ].items()
            },
            "controller_policy_sha256":
                self.result["manifest"]["controller_policy_sha256"],
            "issued_at": (
                datetime.now(timezone.utc) - timedelta(seconds=5)
            ).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=20)
            ).isoformat(),
        }
        authority_path = self.base / "authority.json"
        authority_path.write_text(
            json.dumps(authority, indent=2, sort_keys=True) + "\n"
        )
        authority_path.chmod(0o600)

        registry = self.inputs["registry"]
        v2_units = production.migration.v2_controller_units(registry)
        v3_units = production.migration.v3_controller_units(root_policy)
        active = {unit: False for unit in [*v2_units, *v3_units]}
        enabled = {unit: False for unit in [*v2_units, *v3_units]}
        active[production.migration.V3_RECONCILER_UNIT] = True
        active[production.migration.V3_PROVISIONER_UNIT] = True
        enabled[production.migration.V3_RECONCILER_UNIT] = False
        enabled[production.migration.V3_PROVISIONER_UNIT] = False
        for unit in (
            "workspace-ci-controller@workspace-control-cpu.service",
            "workspace-ci-controller@padataset-cpu.service",
            "workspace-ci-controller@padataset-gpu.service",
            "workspace-ci-controller@research-engine-cpu.service",
        ):
            active[unit] = True
            enabled[unit] = True
        active[production.migration.RESEARCH_GPU_V2_UNIT] = False
        enabled[production.migration.RESEARCH_GPU_V2_UNIT] = False
        systemd = FakeSystemd(active, enabled)

        workflow_confirmation = {
            "schema_version": 1,
            "mode": "V3_PRODUCTION_WORKFLOW_CUTOVER_CONFIRMED",
            "production_generation_sha256":
                self.result["manifest"][
                    "production_generation_sha256"
                ],
            "workflow_bindings": {
                key: {
                    "repository": binding["repository"],
                    "path": binding["path"],
                    "blob_sha": binding["new_blob_sha"],
                    "commit_sha": str(index + 1) * 40,
                }
                for index, (key, binding) in enumerate(
                    self.result["manifest"]["workflow_bindings"].items()
                )
            },
        }
        workflow_confirmation_path = self.base / "workflow-confirm.json"
        workflow_confirmation_path.write_text(
            json.dumps(
                workflow_confirmation,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        workflow_confirmation_path.chmod(0o600)

        validation = {
            "schema_version": 1,
            "mode": "V3_PRODUCTION_VALIDATION_CONFIRMED",
            "production_generation_sha256":
                self.result["manifest"][
                    "production_generation_sha256"
                ],
            "routes": {},
        }
        for index, (route_key, spec) in enumerate(
            production.ROUTES.items(),
            start=1,
        ):
            validation["routes"][route_key] = {
                "conclusion": "success",
                "run_id": 1000 + index,
                "job_id": 2000 + index,
                "workflow_blob_sha":
                    self.result["manifest"]["workflow_bindings"][
                        route_key
                    ]["new_blob_sha"],
                "runner_class_id": spec["runner_class_id"],
                "scale_set_name": spec["target_scale_set_name"],
                "runner_name":
                    spec["target_scale_set_name"] + "-abcdef123456",
            }
        validation_path = self.base / "validation.json"
        validation_path.write_text(
            json.dumps(validation, indent=2, sort_keys=True) + "\n"
        )
        validation_path.chmod(0o600)

        rollback_confirmation = {
            "schema_version": 1,
            "mode": "V3_PRODUCTION_WORKFLOW_ROLLBACK_CONFIRMED",
            "production_generation_sha256":
                self.result["manifest"][
                    "production_generation_sha256"
                ],
            "workflow_bindings": {
                key: {
                    "repository": binding["repository"],
                    "path": binding["path"],
                    "blob_sha": binding["old_blob_sha"],
                    "commit_sha": str(index + 4) * 40,
                }
                for index, (key, binding) in enumerate(
                    self.result["manifest"]["workflow_bindings"].items()
                )
            },
        }
        rollback_path = self.base / "rollback-confirm.json"
        rollback_path.write_text(
            json.dumps(
                rollback_confirmation,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        rollback_path.chmod(0o600)

        patches = [
            mock.patch.object(production, "V3_CONFIG_ROOT", config),
            mock.patch.object(
                production,
                "BASE_MANIFEST",
                config / "install-manifest.json",
            ),
            mock.patch.object(
                production,
                "PRODUCTION_OVERRIDE",
                state / "production-cutover" / "active.json",
            ),
            mock.patch.object(
                production,
                "MIGRATION_ROOT",
                migration_root,
            ),
            mock.patch.object(
                production,
                "AUTHORITY_ROOT",
                authority_root,
            ),
            mock.patch.object(
                production,
                "PROVISIONER_STATE",
                provisioner,
            ),
            mock.patch.object(
                production.compiler,
                "load_inputs",
                return_value=self.inputs,
            ),
            mock.patch.object(
                production.reconciler,
                "verify_installed",
                return_value=None,
            ),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        return {
            "config": config,
            "state": state,
            "migration_root": migration_root,
            "authority_root": authority_root,
            "provisioner": provisioner,
            "generation": generation,
            "authority_path": authority_path,
            "systemd": systemd,
            "workflow_confirmation": workflow_confirmation_path,
            "validation": validation_path,
            "rollback_confirmation": rollback_path,
            "v2_units": v2_units,
            "v3_units": v3_units,
        }

    def test_prepare_activate_commit_and_rollback_preserve_generation_exclusion(self):
        fx = self._install_fixture()
        systemd = fx["systemd"]
        pre_active = dict(systemd.active_state)
        pre_enabled = dict(systemd.enabled_state)

        receipt = production.prepare(
            systemd=systemd,
            repo_root=ROOT,
            generation_dir=fx["generation"],
            authorization_receipt=fx["authority_path"],
            transaction_root=fx["migration_root"],
            authority_root=fx["authority_root"],
            provisioner_state_root=fx["provisioner"],
        )
        self.assertTrue(receipt.is_file())
        self.assertFalse(
            any(systemd.active(unit) for unit in fx["v2_units"])
        )
        self.assertFalse(
            any(systemd.active(unit) for unit in fx["v3_units"])
        )

        production.activate(
            systemd=systemd,
            repo_root=ROOT,
            receipt_path=receipt,
            workflow_confirmation=fx["workflow_confirmation"],
            provisioner_state_root=fx["provisioner"],
        )
        self.assertEqual(
            {
                unit
                for unit in fx["v3_units"]
                if systemd.active(unit)
            },
            set(production.ACCEPTED_V3_UNITS),
        )
        self.assertFalse(
            any(systemd.active(unit) for unit in fx["v2_units"])
        )

        production.commit(
            systemd=systemd,
            repo_root=ROOT,
            receipt_path=receipt,
            validation_confirmation=fx["validation"],
            provisioner_state_root=fx["provisioner"],
        )
        self.assertTrue(
            all(systemd.enabled(unit) for unit in production.ROOT_UNITS)
        )
        self.assertTrue(
            all(
                systemd.enabled(unit)
                for unit in production.ACCEPTED_V3_UNITS
            )
        )
        self.assertTrue(
            all(
                not systemd.enabled(unit)
                for unit in fx["v3_units"]
                if unit not in production.ACCEPTED_V3_UNITS
            )
        )
        self.assertTrue(
            all(not systemd.enabled(unit) for unit in fx["v2_units"])
        )
        self.assertFalse(
            systemd.active(
                "workspace-ci-controller@research-engine-cpu.service"
            )
        )
        self.assertFalse(
            systemd.active(production.migration.RESEARCH_GPU_V2_UNIT)
        )

        production.rollback(
            systemd=systemd,
            repo_root=ROOT,
            receipt_path=receipt,
            workflow_rollback_confirmation=fx[
                "rollback_confirmation"
            ],
            provisioner_state_root=fx["provisioner"],
        )
        for unit, wanted in pre_active.items():
            self.assertEqual(systemd.active(unit), wanted, unit)
        for unit, wanted in pre_enabled.items():
            self.assertEqual(systemd.enabled(unit), wanted, unit)
        self.assertFalse(production.PRODUCTION_OVERRIDE.exists())
        receipt_value = json.loads(receipt.read_text())
        self.assertEqual(
            receipt_value["phase"],
            "ROLLED_BACK_LEGACY_RESTORED",
        )

    def test_bad_workflow_rollback_confirmation_still_isolates_v3(self):
        fx = self._install_fixture()
        receipt = production.prepare(
            systemd=fx["systemd"],
            repo_root=ROOT,
            generation_dir=fx["generation"],
            authorization_receipt=fx["authority_path"],
            transaction_root=fx["migration_root"],
            authority_root=fx["authority_root"],
            provisioner_state_root=fx["provisioner"],
        )
        production.activate(
            systemd=fx["systemd"],
            repo_root=ROOT,
            receipt_path=receipt,
            workflow_confirmation=fx["workflow_confirmation"],
            provisioner_state_root=fx["provisioner"],
        )
        bad = json.loads(fx["rollback_confirmation"].read_text())
        key = next(iter(production.ROUTES))
        bad["workflow_bindings"][key]["blob_sha"] = "f" * 40
        fx["rollback_confirmation"].write_text(
            json.dumps(bad, indent=2, sort_keys=True) + "\n"
        )
        fx["rollback_confirmation"].chmod(0o600)

        with self.assertRaisesRegex(
            production.CutoverError,
            "workflow confirmation blob mismatch",
        ):
            production.rollback(
                systemd=fx["systemd"],
                repo_root=ROOT,
                receipt_path=receipt,
                workflow_rollback_confirmation=fx[
                    "rollback_confirmation"
                ],
                provisioner_state_root=fx["provisioner"],
            )
        self.assertFalse(
            any(
                fx["systemd"].active(unit)
                for unit in fx["v3_units"]
            )
        )
        self.assertFalse(
            any(
                fx["systemd"].active(unit)
                for unit in fx["v2_units"]
            )
        )
        self.assertEqual(
            json.loads(receipt.read_text())["phase"],
            "ROLLBACK_V3_QUIESCED",
        )

    def test_nonterminal_transaction_blocks_before_authority_consumption(self):
        fx = self._install_fixture()
        blocking = fx["migration_root"] / "existing"
        blocking.mkdir()
        (blocking / "transaction.json").write_text(
            json.dumps({"phase": "V2_QUIESCED"}) + "\n"
        )
        with self.assertRaisesRegex(
            production.CutoverError,
            "nonterminal migration transaction",
        ):
            production.prepare(
                systemd=fx["systemd"],
                repo_root=ROOT,
                generation_dir=fx["generation"],
                authorization_receipt=fx["authority_path"],
                transaction_root=fx["migration_root"],
                authority_root=fx["authority_root"],
                provisioner_state_root=fx["provisioner"],
            )
        marker = (
            fx["authority_root"]
            / "11111111-2222-3333-4444-555555555555.json"
        )
        self.assertFalse(marker.exists())

    def test_boot_enabled_v3_class_blocks_before_authority_consumption(self):
        fx = self._install_fixture()
        unit = production.ACCEPTED_V3_UNITS[0]
        fx["systemd"].enabled_state[unit] = True
        with self.assertRaisesRegex(
            production.CutoverError,
            "boot-enabled before cutover",
        ):
            production.prepare(
                systemd=fx["systemd"],
                repo_root=ROOT,
                generation_dir=fx["generation"],
                authorization_receipt=fx["authority_path"],
                transaction_root=fx["migration_root"],
                authority_root=fx["authority_root"],
                provisioner_state_root=fx["provisioner"],
            )
        marker = (
            fx["authority_root"]
            / "11111111-2222-3333-4444-555555555555.json"
        )
        self.assertFalse(marker.exists())

    def test_validation_confirmation_is_bound_to_v3_class_and_workflow(self):
        receipt = {
            "production_generation_sha256": "a" * 64,
            "workflow_bindings": {
                key: {
                    "new_blob_sha": str(index + 1) * 40,
                }
                for index, key in enumerate(production.ROUTES)
            },
        }
        confirmation = {
            "schema_version": 1,
            "mode": "V3_PRODUCTION_VALIDATION_CONFIRMED",
            "production_generation_sha256": "a" * 64,
            "routes": {},
        }
        for index, (route_key, spec) in enumerate(
            production.ROUTES.items(),
            start=1,
        ):
            confirmation["routes"][route_key] = {
                "conclusion": "success",
                "run_id": index,
                "job_id": 100 + index,
                "workflow_blob_sha":
                    receipt["workflow_bindings"][route_key][
                        "new_blob_sha"
                    ],
                "runner_class_id": spec["runner_class_id"],
                "scale_set_name": spec["target_scale_set_name"],
                "runner_name":
                    spec["target_scale_set_name"] + "-abcdef",
            }
        production._validate_validation_confirmation(
            confirmation,
            receipt,
        )
        bad = copy.deepcopy(confirmation)
        first = next(iter(production.ROUTES))
        bad["routes"][first]["runner_class_id"] = "research-cpu-public-v1"
        with self.assertRaisesRegex(
            production.CutoverError,
            "runner class mismatch",
        ):
            production._validate_validation_confirmation(bad, receipt)


if __name__ == "__main__":
    unittest.main()
