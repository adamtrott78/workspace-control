import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

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
    "lambda_ci_policy_compiler_root_activation_tests",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
activation = load(
    "lambda_ci_v3_root_activation",
    ROOT / "scripts" / "lambda_ci_v3_root_activation.py",
)
ROOT_REACTIVATION_UPDATER = ROOT / "scripts" / "lambda_ci_v3_root_reactivation_helper_live_update_v1.py"


class FakeSystemd:
    def __init__(self, states):
        self.states = dict(states)
        self.enabled_states = {unit: False for unit in states}
        self.events = []
        self.extra_units = []
        self.fail_start = set()

    def active(self, unit):
        return bool(self.states.get(unit, False))

    def enabled(self, unit):
        return bool(self.enabled_states.get(unit, False))

    def start(self, unit):
        self.events.append(("start", unit))
        if unit in self.fail_start:
            raise activation.RootActivationError(f"synthetic start failure: {unit}")
        self.states[unit] = True

    def stop(self, unit):
        self.events.append(("stop", unit))
        self.states[unit] = False

    def list_units(self):
        return sorted(set(self.states) | set(self.extra_units))


class RootReactivationUpdaterContractTests(unittest.TestCase):
    def test_updater_is_single_file_transactional_and_non_activating(self):
        text = ROOT_REACTIVATION_UPDATER.read_text()
        self.assertIn(
            'BASE_SOURCE_HEAD = "09c46818252991f6a55aaeedbcf046c554e2ffee"',
            text,
        )
        self.assertIn(
            'EXPECTED_CANDIDATE_GIT_BLOB = "3f617c8d85b3dabf1a6b9b2b82edc0feb1f1b930"',
            text,
        )
        self.assertIn(
            '/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py',
            text,
        )
        self.assertIn("V3_ROOT_REACTIVATION_HELPER_PRESTATE=PASS", text)
        self.assertIn("V3_ROOT_REACTIVATION_HELPER_UPDATE=PASS", text)
        self.assertIn("reviewed inactive-substrate helper mode drift", text)
        self.assertIn("root-reactivation-helper", text)
        self.assertIn("verify_effective_installed_generation", text)
        self.assertNotIn("systemctl", text)
        self.assertNotIn("ACTIVATE_V3_ROOT_SERVICES", text)
        self.assertNotIn("workspace-ci-v3-provisioner.service", text)
        self.assertNotIn("workspace-ci-v3-reconciler.service", text)


class EffectiveGenerationVerificationTests(unittest.TestCase):
    def test_base_generation_accepts_exact_controller(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            controller = root / "lambda-ci-controller-v3"
            controller.write_bytes(b"base")
            controller.chmod(0o755)
            reconciler_script = root / "lambda_ci_v3_reconciler.py"
            reconciler_script.write_bytes(b"base-reconciler")
            reconciler_script.chmod(0o755)
            runtime_script = root / "lambda_ci_runtime.py"
            runtime_script.write_bytes(b"base-runtime")
            runtime_script.chmod(0o644)
            manifest = root / "install-manifest.json"
            payload = {
                "schema_version": 1,
                "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
                "source_head": "a" * 40,
                "root_policy_sha256": "b" * 64,
                "runner_class_count": 9,
                "entries": [
                    {
                        "destination": str(controller),
                        "sha256": activation._sha256(b"base"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(reconciler_script),
                        "sha256": activation._sha256(b"base-reconciler"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(runtime_script),
                        "sha256": activation._sha256(b"base-runtime"),
                        "mode": "0644",
                    },
                ],
            }
            manifest.write_bytes(activation._canonical(payload))
            old_controller = activation.reconciler.V3_CONTROLLER_BINARY
            old_reconciler = activation.RECONCILER_SCRIPT
            old_runtime = activation.V3_RUNTIME_SCRIPT
            try:
                activation.reconciler.V3_CONTROLLER_BINARY = controller
                activation.RECONCILER_SCRIPT = reconciler_script
                activation.V3_RUNTIME_SCRIPT = runtime_script
                self.assertIsNone(
                    activation.verify_effective_installed_generation(manifest)
                )
            finally:
                activation.reconciler.V3_CONTROLLER_BINARY = old_controller
                activation.RECONCILER_SCRIPT = old_reconciler
                activation.V3_RUNTIME_SCRIPT = old_runtime

    def test_controller_override_is_bound_to_base_manifest_and_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            controller = root / "lambda-ci-controller-v3"
            controller.write_bytes(b"override")
            controller.chmod(0o755)
            reconciler_script = root / "lambda_ci_v3_reconciler.py"
            reconciler_script.write_bytes(b"base-reconciler")
            reconciler_script.chmod(0o755)
            runtime_script = root / "lambda_ci_runtime.py"
            runtime_script.write_bytes(b"base-runtime")
            runtime_script.chmod(0o644)
            manifest = root / "install-manifest.json"
            payload = {
                "schema_version": 1,
                "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
                "source_head": "a" * 40,
                "root_policy_sha256": "b" * 64,
                "runner_class_count": 9,
                "entries": [
                    {
                        "destination": str(controller),
                        "sha256": activation._sha256(b"base"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(reconciler_script),
                        "sha256": activation._sha256(b"base-reconciler"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(runtime_script),
                        "sha256": activation._sha256(b"base-runtime"),
                        "mode": "0644",
                    },
                ],
            }
            manifest.write_bytes(activation._canonical(payload))
            receipt = root / "active.json"
            receipt.write_bytes(
                activation._canonical(
                    {
                        "mode": "V3_INACTIVE_CONTROLLER_BINARY_OVERRIDE",
                        "phase": "ACTIVE",
                        "base_source_head": "a" * 40,
                        "controller_source_head": "c" * 40,
                        "base_install_manifest_sha256": activation._sha256(
                            manifest.read_bytes()
                        ),
                        "controller_binary_sha256": activation._sha256(b"override"),
                        "root_policy_sha256": "b" * 64,
                        "non_controller_generation_equivalent": True,
                    }
                )
            )
            receipt.chmod(0o600)
            old_controller = activation.reconciler.V3_CONTROLLER_BINARY
            old_receipt = activation.CONTROLLER_REFRESH_ACTIVE_RECEIPT
            old_reconciler = activation.RECONCILER_SCRIPT
            old_runtime = activation.V3_RUNTIME_SCRIPT
            try:
                activation.reconciler.V3_CONTROLLER_BINARY = controller
                activation.CONTROLLER_REFRESH_ACTIVE_RECEIPT = receipt
                activation.RECONCILER_SCRIPT = reconciler_script
                activation.V3_RUNTIME_SCRIPT = runtime_script
                result = activation.verify_effective_installed_generation(manifest)
            finally:
                activation.reconciler.V3_CONTROLLER_BINARY = old_controller
                activation.CONTROLLER_REFRESH_ACTIVE_RECEIPT = old_receipt
                activation.RECONCILER_SCRIPT = old_reconciler
                activation.V3_RUNTIME_SCRIPT = old_runtime
            self.assertEqual(result["controller_source_head"], "c" * 40)

    def test_root_activation_helper_override_is_bound_to_base_manifest_and_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            controller = root / "lambda-ci-controller-v3"
            controller.write_bytes(b"base-controller")
            controller.chmod(0o755)
            helper = root / "lambda_ci_v3_root_activation.py"
            helper.write_bytes(b"candidate-helper")
            helper.chmod(0o555)
            reconciler_script = root / "lambda_ci_v3_reconciler.py"
            reconciler_script.write_bytes(b"base-reconciler")
            reconciler_script.chmod(0o755)
            runtime_script = root / "lambda_ci_runtime.py"
            runtime_script.write_bytes(b"base-runtime")
            runtime_script.chmod(0o644)
            manifest = root / "install-manifest.json"
            payload = {
                "schema_version": 1,
                "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
                "source_head": "a" * 40,
                "root_policy_sha256": "b" * 64,
                "runner_class_count": 9,
                "entries": [
                    {
                        "destination": str(controller),
                        "sha256": activation._sha256(b"base-controller"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(helper),
                        "sha256": activation._sha256(b"base-helper"),
                        "mode": "0555",
                    },
                    {
                        "destination": str(reconciler_script),
                        "sha256": activation._sha256(b"base-reconciler"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(runtime_script),
                        "sha256": activation._sha256(b"base-runtime"),
                        "mode": "0644",
                    },
                ],
            }
            manifest.write_bytes(activation._canonical(payload))
            receipt = root / "helper-active.json"
            receipt.write_bytes(
                activation._canonical(
                    {
                        "schema_version": 1,
                        "mode": "V3_ROOT_REACTIVATION_HELPER_OVERRIDE",
                        "phase": "ACTIVE",
                        "base_source_head": "a" * 40,
                        "helper_source_head": "d" * 40,
                        "base_install_manifest_sha256": activation._sha256(
                            manifest.read_bytes()
                        ),
                        "base_helper_sha256": activation._sha256(b"base-helper"),
                        "helper_sha256": activation._sha256(b"candidate-helper"),
                        "helper_git_blob": "e" * 40,
                        "helper_mode": "0555",
                        "root_policy_sha256": "b" * 64,
                        "non_helper_generation_equivalent": True,
                    }
                )
            )
            receipt.chmod(0o600)

            old_controller = activation.reconciler.V3_CONTROLLER_BINARY
            old_helper = activation.ROOT_ACTIVATION_HELPER
            old_helper_receipt = activation.ROOT_ACTIVATION_HELPER_ACTIVE_RECEIPT
            old_reconciler = activation.RECONCILER_SCRIPT
            old_runtime = activation.V3_RUNTIME_SCRIPT
            try:
                activation.reconciler.V3_CONTROLLER_BINARY = controller
                activation.ROOT_ACTIVATION_HELPER = helper
                activation.ROOT_ACTIVATION_HELPER_ACTIVE_RECEIPT = receipt
                activation.RECONCILER_SCRIPT = reconciler_script
                activation.V3_RUNTIME_SCRIPT = runtime_script
                result = activation.verify_effective_installed_generation(manifest)
            finally:
                activation.reconciler.V3_CONTROLLER_BINARY = old_controller
                activation.ROOT_ACTIVATION_HELPER = old_helper
                activation.ROOT_ACTIVATION_HELPER_ACTIVE_RECEIPT = old_helper_receipt
                activation.RECONCILER_SCRIPT = old_reconciler
                activation.V3_RUNTIME_SCRIPT = old_runtime

            self.assertEqual(
                result["root_activation_helper_override"]["helper_source_head"],
                "d" * 40,
            )

    def test_runtime_override_is_bound_to_base_manifest_and_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            controller = root / "lambda-ci-controller-v3"
            controller.write_bytes(b"base-controller")
            controller.chmod(0o755)
            reconciler_script = root / "lambda_ci_v3_reconciler.py"
            reconciler_script.write_bytes(b"base-reconciler")
            reconciler_script.chmod(0o755)
            runtime_script = root / "lambda_ci_runtime.py"
            runtime_script.write_bytes(b"candidate-runtime")
            runtime_script.chmod(0o644)
            manifest = root / "install-manifest.json"
            payload = {
                "schema_version": 1,
                "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
                "source_head": "a" * 40,
                "root_policy_sha256": "b" * 64,
                "runner_class_count": 9,
                "entries": [
                    {
                        "destination": str(controller),
                        "sha256": activation._sha256(b"base-controller"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(reconciler_script),
                        "sha256": activation._sha256(b"base-reconciler"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(runtime_script),
                        "sha256": activation._sha256(b"base-runtime"),
                        "mode": "0644",
                    },
                ],
            }
            manifest.write_bytes(activation._canonical(payload))
            receipt = root / "runtime-active.json"
            receipt.write_bytes(
                activation._canonical(
                    {
                        "schema_version": 1,
                        "mode": "V3_RUNTIME_OVERRIDE",
                        "phase": "ACTIVE",
                        "base_source_head": "a" * 40,
                        "runtime_source_head": "d" * 40,
                        "base_install_manifest_sha256": activation._sha256(
                            manifest.read_bytes()
                        ),
                        "base_runtime_sha256": activation._sha256(b"base-runtime"),
                        "runtime_sha256": activation._sha256(b"candidate-runtime"),
                        "runtime_mode": "0644",
                        "runtime_git_blob": "e" * 40,
                        "root_policy_sha256": "b" * 64,
                        "non_runtime_generation_equivalent": True,
                    }
                )
            )
            receipt.chmod(0o600)

            old_controller = activation.reconciler.V3_CONTROLLER_BINARY
            old_reconciler = activation.RECONCILER_SCRIPT
            old_runtime = activation.V3_RUNTIME_SCRIPT
            old_runtime_receipt = activation.RUNTIME_OVERRIDE_ACTIVE_RECEIPT
            try:
                activation.reconciler.V3_CONTROLLER_BINARY = controller
                activation.RECONCILER_SCRIPT = reconciler_script
                activation.V3_RUNTIME_SCRIPT = runtime_script
                activation.RUNTIME_OVERRIDE_ACTIVE_RECEIPT = receipt
                result = activation.verify_effective_installed_generation(manifest)
            finally:
                activation.reconciler.V3_CONTROLLER_BINARY = old_controller
                activation.RECONCILER_SCRIPT = old_reconciler
                activation.V3_RUNTIME_SCRIPT = old_runtime
                activation.RUNTIME_OVERRIDE_ACTIVE_RECEIPT = old_runtime_receipt

            self.assertEqual(
                result["runtime_override"]["runtime_source_head"],
                "d" * 40,
            )

    def test_root_activation_helper_drift_without_active_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            controller = root / "lambda-ci-controller-v3"
            controller.write_bytes(b"base-controller")
            controller.chmod(0o755)
            helper = root / "lambda_ci_v3_root_activation.py"
            helper.write_bytes(b"candidate-helper")
            helper.chmod(0o555)
            manifest = root / "install-manifest.json"
            payload = {
                "schema_version": 1,
                "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
                "source_head": "a" * 40,
                "root_policy_sha256": "b" * 64,
                "runner_class_count": 9,
                "entries": [
                    {
                        "destination": str(controller),
                        "sha256": activation._sha256(b"base-controller"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(helper),
                        "sha256": activation._sha256(b"base-helper"),
                        "mode": "0555",
                    },
                ],
            }
            manifest.write_bytes(activation._canonical(payload))

            old_controller = activation.reconciler.V3_CONTROLLER_BINARY
            old_helper = activation.ROOT_ACTIVATION_HELPER
            old_helper_receipt = activation.ROOT_ACTIVATION_HELPER_ACTIVE_RECEIPT
            try:
                activation.reconciler.V3_CONTROLLER_BINARY = controller
                activation.ROOT_ACTIVATION_HELPER = helper
                activation.ROOT_ACTIVATION_HELPER_ACTIVE_RECEIPT = root / "missing.json"
                with self.assertRaisesRegex(
                    activation.RootActivationError,
                    "active root-reactivation helper override receipt missing",
                ):
                    activation.verify_effective_installed_generation(manifest)
            finally:
                activation.reconciler.V3_CONTROLLER_BINARY = old_controller
                activation.ROOT_ACTIVATION_HELPER = old_helper
                activation.ROOT_ACTIVATION_HELPER_ACTIVE_RECEIPT = old_helper_receipt


class V3RootActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)
        cls.root_policy = cls.compiled["root_projection"]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.migration_root = self.base / "migration"
        self.migration_root.mkdir(mode=0o700)
        self.authority_root = self.base / "authority"
        self.authority_root.mkdir(mode=0o700)
        self.provisioner_state = self.base / "provisioner"
        self.provisioner_state.mkdir(mode=0o700)

        self.source_head = "b" * 40
        self.manifest = {
            "schema_version": 1,
            "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
            "source_head": self.source_head,
            "catalog_generation_sha256": self.compiled["catalog_generation_sha256"],
            "root_policy_sha256": self.root_policy["root_policy_sha256"],
            "runner_class_count": 9,
            "controller_state": "INACTIVE",
            "route_state": "DISABLED",
            "entries": [],
        }
        self.manifest_raw = activation._canonical(self.manifest)
        self.manifest_sha = activation._sha256(self.manifest_raw)

        now = datetime.now(timezone.utc)
        self.authority = {
            "schema_version": 1,
            "authority": "workspace-control-operator",
            "operation": "ACTIVATE_V3_ROOT_SERVICES",
            "authorization_id": "22222222-3333-4444-8555-666666666666",
            "source_head": self.source_head,
            "install_manifest_sha256": self.manifest_sha,
            "root_policy_sha256": self.root_policy["root_policy_sha256"],
            "issued_at": (now - timedelta(seconds=5)).isoformat(),
            "expires_at": (now + timedelta(minutes=25)).isoformat(),
        }
        self.authority_raw = activation._canonical(self.authority)

        states = {
            activation.PROVISIONER_UNIT: False,
            activation.RECONCILER_UNIT: False,
            activation.RESEARCH_GPU_V2_UNIT: False,
        }
        for unit in activation._class_units(self.root_policy):
            states[unit] = False
        self.systemd = FakeSystemd(states)
        self.socket_evidence = {
            "path": str(activation.PROVISIONER_SOCKET),
            "uid": 0,
            "gid": 123,
            "mode": "0660",
            "group": activation.PROVISIONER_SOCKET_GROUP,
        }

    def apply(self, *, socket_probe=None):
        return activation.activate_root_services(
            systemd=self.systemd,
            root_policy=self.root_policy,
            install_manifest=self.manifest,
            install_manifest_sha256=self.manifest_sha,
            authority_receipt=self.authority,
            authority_receipt_raw=self.authority_raw,
            socket_probe=socket_probe or (lambda: dict(self.socket_evidence)),
            transaction_root=self.migration_root,
            authority_consumption_root=self.authority_root,
            provisioner_state_root=self.provisioner_state,
        )

    def marker(self):
        return self.authority_root / f"{self.authority['authorization_id']}.json"

    def receipt_path(self):
        return (
            self.migration_root
            / f"root-activation-{self.authority['authorization_id']}.json"
        )

    def test_activation_starts_only_reconciler_then_provisioner_and_proves_no_class_activation(self):
        receipt_path = self.apply()
        self.assertTrue(self.systemd.active(activation.RECONCILER_UNIT))
        self.assertTrue(self.systemd.active(activation.PROVISIONER_UNIT))
        self.assertEqual(
            self.systemd.events,
            [
                ("start", activation.RECONCILER_UNIT),
                ("start", activation.PROVISIONER_UNIT),
            ],
        )
        self.assertFalse(
            any(
                self.systemd.active(unit)
                for unit in activation._class_units(self.root_policy)
            )
        )
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(receipt["phase"], "ROOT_SERVICES_ACTIVE")
        self.assertFalse(receipt["class_controllers_activated"])
        self.assertFalse(receipt["workflow_mutated"])
        self.assertFalse(receipt["legacy_v2_mutated"])
        self.assertFalse(receipt["containment_or_retry_authority_mutated"])
        self.assertTrue(receipt["research_gpu_containment_preserved"])
        self.assertFalse(receipt["v3_units_enabled"])
        self.assertEqual(receipt["provisioner_socket"], self.socket_evidence)
        self.assertTrue(self.marker().is_file())
        self.assertEqual(self.marker().stat().st_mode & 0o777, 0o600)

    def test_rollback_stops_provisioner_then_reconciler_and_never_reopens_authority(self):
        receipt_path = self.apply()
        self.systemd.events.clear()
        activation.rollback_root_services(
            systemd=self.systemd,
            root_policy=self.root_policy,
            receipt_path=receipt_path,
            provisioner_state_root=self.provisioner_state,
        )
        self.assertEqual(
            self.systemd.events,
            [
                ("stop", activation.PROVISIONER_UNIT),
                ("stop", activation.RECONCILER_UNIT),
            ],
        )
        self.assertFalse(self.systemd.active(activation.PROVISIONER_UNIT))
        self.assertFalse(self.systemd.active(activation.RECONCILER_UNIT))
        self.assertTrue(self.marker().is_file())
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(receipt["phase"], "ROOT_SERVICES_ROLLED_BACK")
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "already consumed",
        ):
            self.apply()

    def test_socket_failure_rolls_back_both_root_services_and_burns_authority(self):
        def fail_socket():
            raise activation.RootActivationError("synthetic socket failure")

        with self.assertRaisesRegex(
            activation.RootActivationError,
            "synthetic socket failure",
        ):
            self.apply(socket_probe=fail_socket)
        self.assertFalse(self.systemd.active(activation.PROVISIONER_UNIT))
        self.assertFalse(self.systemd.active(activation.RECONCILER_UNIT))
        self.assertEqual(
            self.systemd.events,
            [
                ("start", activation.RECONCILER_UNIT),
                ("start", activation.PROVISIONER_UNIT),
                ("stop", activation.PROVISIONER_UNIT),
                ("stop", activation.RECONCILER_UNIT),
            ],
        )
        self.assertTrue(self.marker().is_file())
        receipt = json.loads(self.receipt_path().read_text())
        self.assertEqual(receipt["phase"], "ROLLED_BACK_AFTER_ACTIVATION_FAILURE")

    def test_class_controller_or_execution_state_blocks_before_authority_consumption(self):
        class_unit = activation._class_units(self.root_policy)[0]
        self.systemd.states[class_unit] = True
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "class controller unexpectedly active",
        ):
            self.apply()
        self.assertFalse(self.marker().exists())
        self.assertEqual(self.systemd.events, [])

        self.systemd.states[class_unit] = False
        request_id = "11111111-2222-3333-8444-555555555555"
        (self.provisioner_state / f"{request_id}.json").write_text(
            json.dumps(
                {
                    "request_id": request_id,
                    "state": "RESERVED",
                    "resource_hold": True,
                }
            )
        )
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "resource claims",
        ):
            self.apply()
        self.assertFalse(self.marker().exists())
        self.assertEqual(self.systemd.events, [])

    def test_private_state_root_drift_blocks_before_authority_consumption(self):
        self.migration_root.chmod(0o755)
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "transaction root must be mode 0700",
        ):
            self.apply()
        self.assertFalse(self.marker().exists())
        self.assertEqual(self.systemd.events, [])

        self.migration_root.chmod(0o700)
        self.authority_root.chmod(0o755)
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "consumption root must be mode 0700",
        ):
            self.apply()
        self.assertFalse(self.marker().exists())
        self.assertEqual(self.systemd.events, [])

    def test_authority_is_exact_generation_bound_and_short_lived(self):
        fixed_now = datetime(2026, 10, 30, 1, 15, tzinfo=timezone.utc)
        fixed = dict(self.authority)
        fixed["issued_at"] = "2026-10-30T01:00:00+00:00"
        fixed["expires_at"] = "2026-10-30T01:30:00+00:00"
        activation._validate_authority_payload(
            fixed,
            expected_source_head=self.source_head,
            expected_install_manifest_sha256=self.manifest_sha,
            expected_root_policy_sha256=self.root_policy["root_policy_sha256"],
            now=fixed_now,
        )

        wrong_manifest = dict(fixed)
        wrong_manifest["install_manifest_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "manifest mismatch",
        ):
            activation._validate_authority_payload(
                wrong_manifest,
                expected_source_head=self.source_head,
                expected_install_manifest_sha256=self.manifest_sha,
                expected_root_policy_sha256=self.root_policy["root_policy_sha256"],
                now=fixed_now,
            )

        expired = dict(fixed)
        expired["expires_at"] = "2026-10-30T01:14:59+00:00"
        with self.assertRaisesRegex(activation.RootActivationError, "expired"):
            activation._validate_authority_payload(
                expired,
                expected_source_head=self.source_head,
                expected_install_manifest_sha256=self.manifest_sha,
                expected_root_policy_sha256=self.root_policy["root_policy_sha256"],
                now=fixed_now,
            )

        overlong = dict(fixed)
        overlong["expires_at"] = "2026-10-30T01:30:01+00:00"
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "lifetime exceeds",
        ):
            activation._validate_authority_payload(
                overlong,
                expected_source_head=self.source_head,
                expected_install_manifest_sha256=self.manifest_sha,
                expected_root_policy_sha256=self.root_policy["root_policy_sha256"],
                now=fixed_now,
            )

    def test_research_gpu_containment_drift_blocks_before_authority_consumption(self):
        self.systemd.states[activation.RESEARCH_GPU_V2_UNIT] = True
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "inherited containment drifted",
        ):
            self.apply()
        self.assertFalse(self.marker().exists())
        self.assertEqual(self.systemd.events, [])

    def test_enabled_v3_unit_blocks_transient_activation_before_authority_consumption(self):
        self.systemd.enabled_states[activation.PROVISIONER_UNIT] = True
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "enabled for boot persistence",
        ):
            self.apply()
        self.assertFalse(self.marker().exists())
        self.assertEqual(self.systemd.events, [])

    def test_helper_source_never_enables_or_restarts_v3_services(self):
        source = (ROOT / "scripts/lambda_ci_v3_root_activation.py").read_text()
        for forbidden in (
            '["systemctl", "enable"',
            '["systemctl", "restart"',
            "systemctl enable ",
            "systemctl restart ",
        ):
            self.assertNotIn(forbidden, source)

    def test_existing_root_service_blocks_without_mutation_or_authority_consumption(self):
        self.systemd.states[activation.RECONCILER_UNIT] = True
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "must both be inactive",
        ):
            self.apply()
        self.assertFalse(self.marker().exists())
        self.assertEqual(self.systemd.events, [])

    def test_rollback_refuses_while_class_execution_exists(self):
        receipt_path = self.apply()
        class_unit = activation._class_units(self.root_policy)[0]
        self.systemd.states[class_unit] = True
        self.systemd.events.clear()
        with self.assertRaisesRegex(
            activation.RootActivationError,
            "class controller unexpectedly active",
        ):
            activation.rollback_root_services(
                systemd=self.systemd,
                root_policy=self.root_policy,
                receipt_path=receipt_path,
                provisioner_state_root=self.provisioner_state,
            )
        self.assertEqual(self.systemd.events, [])
        self.assertTrue(self.systemd.active(activation.PROVISIONER_UNIT))
        self.assertTrue(self.systemd.active(activation.RECONCILER_UNIT))


if __name__ == "__main__":
    unittest.main()
