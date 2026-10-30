import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

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
    "lambda_ci_policy_compiler_v3_tx_tests",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
canary = load(
    "lambda_ci_v3_canary_for_tx_tests",
    ROOT / "scripts" / "lambda_ci_v3_canary.py",
)
tx = load(
    "lambda_ci_v3_migration_transaction",
    ROOT / "scripts" / "lambda_ci_v3_migration_transaction.py",
)


class FakeSystemd:
    def __init__(self, active):
        self.states = dict(active)
        self.events = []
        self.extra_units = []

    def active(self, unit):
        return bool(self.states.get(unit, False))

    def start(self, unit):
        self.events.append(("start", unit))
        self.states[unit] = True

    def stop(self, unit):
        self.events.append(("stop", unit))
        self.states[unit] = False

    def list_units(self):
        return sorted(set(self.states) | set(self.extra_units))


class V3MigrationTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)
        cls.root_policy = cls.compiled["root_projection"]
        cls.registry = compiler.load_inputs(ROOT)["registry"]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.generated = self.base / "canaries"
        self.manifest = canary.generate(ROOT, self.generated)
        self.target = "workspace-control-control-small-v1"
        self.entry = self.manifest["classes"][self.target]
        self.canary_policy_path = (
            self.generated / self.entry["controller_policy_path"]
        )
        self.canary_policy_raw = self.canary_policy_path.read_bytes()
        self.canary_policy = json.loads(self.canary_policy_raw)
        self.production_policy = self.base / "production.json"
        self.production_policy.write_text(
            json.dumps(
                self.compiled["controller_projections"][self.target],
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        self.original_policy = self.production_policy.read_bytes()
        self.migration_root = self.base / "migration"
        self.migration_root.mkdir(mode=0o700)
        self.provisioner_state = self.base / "provisioner"
        self.provisioner_state.mkdir()
        self.source_head = "a" * 40
        self.authority = {
            "schema_version": 1,
            "authority": "workspace-control-operator",
            "operation": "ACTIVATE_ONE_V3_CANARY",
            "authorization_id": "11111111-2222-3333-4444-555555555555",
            "source_head": self.source_head,
            "canary_generation_sha256": self.manifest["canary_generation_sha256"],
            "target_runner_class_id": self.target,
            "controller_policy_sha256": self.canary_policy["controller_policy_sha256"],
            "workflow_blob_sha": self.entry["workflow_blob_sha"],
            "issued_at": "2026-10-30T00:00:00+00:00",
            "expires_at": "2026-10-30T00:30:00+00:00",
        }
        self.authority_raw = tx._canonical(self.authority)
        self.authority_consumption_root = self.base / "authority-used"
        self.authority_consumption_root.mkdir(mode=0o700)
        active = {
            unit: False
            for unit in (
                tx.v2_controller_units(self.registry)
                + tx.v3_controller_units(self.root_policy)
                + list(tx.COMPATIBILITY_V2_UNITS)
            )
        }
        active[tx.V3_PROVISIONER_UNIT] = True
        active[tx.V3_RECONCILER_UNIT] = True
        active["workspace-ci-controller@padataset-cpu.service"] = True
        active["workspace-ci-controller@padataset-gpu.service"] = True
        active["workspace-ci-controller@workspace-control-cpu.service"] = True
        # Research CPU and Research GPU are intentionally inactive in this fixture.
        self.systemd = FakeSystemd(active)

    def apply(self):
        return tx.apply_canary(
            systemd=self.systemd,
            registry=self.registry,
            root_policy=self.root_policy,
            canary_manifest=self.manifest,
            canary_policy=self.canary_policy,
            canary_policy_raw=self.canary_policy_raw,
            authority_receipt=self.authority,
            authority_receipt_raw=self.authority_raw,
            target_class=self.target,
            source_head=self.source_head,
            production_policy_path=self.production_policy,
            transaction_root=self.migration_root,
            provisioner_state_root=self.provisioner_state,
            authority_consumption_root=self.authority_consumption_root,
        )

    def test_authority_payload_requires_current_bounded_one_shot_window(self):
        now = datetime(2026, 10, 30, 0, 15, tzinfo=timezone.utc)
        validated = tx._validate_authority_payload(
            dict(self.authority),
            expected_head=self.source_head,
            target_class=self.target,
            manifest=self.manifest,
            canary_policy=self.canary_policy,
            now=now,
        )
        self.assertEqual(validated["authorization_id"], self.authority["authorization_id"])

        expired = dict(self.authority)
        expired["expires_at"] = "2026-10-30T00:14:59+00:00"
        with self.assertRaisesRegex(tx.MigrationError, "expired"):
            tx._validate_authority_payload(
                expired,
                expected_head=self.source_head,
                target_class=self.target,
                manifest=self.manifest,
                canary_policy=self.canary_policy,
                now=now,
            )

        future = dict(self.authority)
        future["issued_at"] = "2026-10-30T00:16:00+00:00"
        future["expires_at"] = "2026-10-30T00:30:00+00:00"
        with self.assertRaisesRegex(tx.MigrationError, "not yet valid"):
            tx._validate_authority_payload(
                future,
                expected_head=self.source_head,
                target_class=self.target,
                manifest=self.manifest,
                canary_policy=self.canary_policy,
                now=now,
            )

        overlong = dict(self.authority)
        overlong["expires_at"] = "2026-10-30T00:30:01+00:00"
        with self.assertRaisesRegex(tx.MigrationError, "lifetime exceeds"):
            tx._validate_authority_payload(
                overlong,
                expected_head=self.source_head,
                target_class=self.target,
                manifest=self.manifest,
                canary_policy=self.canary_policy,
                now=now,
            )

    def test_authority_is_consumed_once_and_rollback_never_reopens_it(self):
        receipt_path = self.apply()
        marker = (
            self.authority_consumption_root
            / f"{self.authority['authorization_id']}.json"
        )
        self.assertTrue(marker.is_file())
        self.assertEqual(marker.stat().st_mode & 0o777, 0o600)
        consumed = json.loads(marker.read_text())
        self.assertEqual(
            consumed["authorization_receipt_sha256"],
            tx._sha256(self.authority_raw),
        )
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(
            receipt["authorization_id"],
            self.authority["authorization_id"],
        )
        self.assertEqual(
            receipt["authorization_consumption_marker"],
            str(marker),
        )

        tx.rollback(
            systemd=self.systemd,
            registry=self.registry,
            root_policy=self.root_policy,
            receipt_path=receipt_path,
            provisioner_state_root=self.provisioner_state,
        )
        self.assertTrue(marker.is_file())
        with self.assertRaisesRegex(tx.MigrationError, "already consumed"):
            self.apply()

    def test_private_migration_state_roots_are_precreated_and_fail_closed_on_drift(self):
        self.migration_root.chmod(0o755)
        with self.assertRaisesRegex(tx.MigrationError, "transaction root must be mode 0700"):
            self.apply()
        marker = (
            self.authority_consumption_root
            / f"{self.authority['authorization_id']}.json"
        )
        self.assertFalse(marker.exists())
        self.assertEqual(self.systemd.events, [])

        self.migration_root.chmod(0o700)
        self.authority_consumption_root.chmod(0o755)
        with self.assertRaisesRegex(tx.MigrationError, "consumption root must be mode 0700"):
            self.apply()
        self.assertFalse(marker.exists())
        self.assertEqual(self.systemd.events, [])

    def test_exact_five_v2_and_nine_v3_controller_sets(self):
        self.assertEqual(
            tx.v2_controller_units(self.registry),
            [
                "workspace-ci-controller@padataset-cpu.service",
                "workspace-ci-controller@padataset-gpu.service",
                "workspace-ci-controller@research-engine-cpu.service",
                "workspace-ci-controller@research-engine-gpu.service",
                "workspace-ci-controller@workspace-control-cpu.service",
            ],
        )
        self.assertEqual(len(tx.v3_controller_units(self.root_policy)), 9)

    def test_apply_stops_active_v2_before_starting_exactly_one_v3(self):
        receipt_path = self.apply()
        target_unit = f"workspace-ci-v3-controller@{self.target}.service"
        self.assertTrue(self.systemd.active(target_unit))
        self.assertFalse(any(
            self.systemd.active(unit)
            for unit in tx.v2_controller_units(self.registry)
        ))
        starts = [event for event in self.systemd.events if event[0] == "start"]
        self.assertEqual(starts, [("start", target_unit)])
        start_index = self.systemd.events.index(("start", target_unit))
        for unit in (
            "workspace-ci-controller@padataset-cpu.service",
            "workspace-ci-controller@padataset-gpu.service",
            "workspace-ci-controller@workspace-control-cpu.service",
        ):
            self.assertLess(
                self.systemd.events.index(("stop", unit)),
                start_index,
            )
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(receipt["phase"], "CANARY_ACTIVE")
        self.assertFalse(receipt["workflow_dispatched"])
        self.assertFalse(receipt["quarantine_or_retry_authority_mutated"])
        self.assertTrue(receipt["research_gpu_containment_preserved"])

    def test_apply_installs_exact_canary_policy_but_never_dispatches(self):
        self.apply()
        self.assertEqual(self.production_policy.read_bytes(), self.canary_policy_raw)
        source = (ROOT / "scripts/lambda_ci_v3_migration_transaction.py").read_text()
        for forbidden in (
            "workflow_dispatches",
            "actions/workflows",
            "host-attest",
            "RECOVERY_RETRY_ACQUIRED",
            "RECOVERY_RETRY_READY",
        ):
            self.assertNotIn(forbidden, source)

    def test_rollback_drains_v3_then_restores_exact_legacy_active_set_and_policy(self):
        receipt_path = self.apply()
        self.systemd.events.clear()
        tx.rollback(
            systemd=self.systemd,
            registry=self.registry,
            root_policy=self.root_policy,
            receipt_path=receipt_path,
            provisioner_state_root=self.provisioner_state,
        )
        target_unit = f"workspace-ci-v3-controller@{self.target}.service"
        self.assertFalse(self.systemd.active(target_unit))
        self.assertEqual(self.production_policy.read_bytes(), self.original_policy)
        expected_active = {
            "workspace-ci-controller@padataset-cpu.service",
            "workspace-ci-controller@padataset-gpu.service",
            "workspace-ci-controller@workspace-control-cpu.service",
        }
        actual_active = {
            unit
            for unit in tx.v2_controller_units(self.registry)
            if self.systemd.active(unit)
        }
        self.assertEqual(actual_active, expected_active)
        self.assertFalse(self.systemd.active(tx.RESEARCH_GPU_V2_UNIT))
        stop_target = self.systemd.events.index(("stop", target_unit))
        first_legacy_start = min(
            i for i, event in enumerate(self.systemd.events)
            if event[0] == "start"
        )
        self.assertLess(stop_target, first_legacy_start)
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(receipt["phase"], "ROLLED_BACK_LEGACY_RESTORED")

    def test_research_gpu_containment_is_not_consumed_by_transaction(self):
        self.systemd.states[tx.RESEARCH_GPU_V2_UNIT] = True
        with self.assertRaisesRegex(tx.MigrationError, "research-engine GPU"):
            self.apply()
        target_unit = f"workspace-ci-v3-controller@{self.target}.service"
        self.assertFalse(self.systemd.active(target_unit))
        self.assertEqual(self.systemd.events, [])
        marker = (
            self.authority_consumption_root
            / f"{self.authority['authorization_id']}.json"
        )
        self.assertFalse(marker.exists())

    def test_untracked_legacy_compatibility_controller_blocks_before_mutation(self):
        self.systemd.states["workspace-ci-controller.service"] = True
        with self.assertRaisesRegex(tx.MigrationError, "compatibility controller"):
            self.apply()
        self.assertEqual(self.systemd.events, [])

    def test_blocked_research_gpu_class_cannot_be_selected_even_with_receipt(self):
        target = "research-gpu-single-public-v1"
        entry = self.manifest["classes"][target]
        policy = json.loads(
            (self.generated / entry["controller_policy_path"]).read_text()
        )
        with self.assertRaisesRegex(tx.MigrationError, "blocked"):
            tx.validate_canary_target(
                self.manifest,
                target_class=target,
                canary_policy=policy,
            )

    def test_offline_model_class_remains_blocked_only_by_inherited_containment(self):
        target = "research-model-single-offline-v1"
        entry = self.manifest["classes"][target]
        self.assertNotIn(
            "PAYLOAD_NETWORK_ISOLATION_UNIMPLEMENTED",
            entry["blockers"],
        )
        self.assertEqual(
            entry["blockers"],
            ["INHERITED_CONTAINMENT_REQUIRES_SEPARATE_AUTHORITY"],
        )
        policy = json.loads(
            (self.generated / entry["controller_policy_path"]).read_text()
        )
        with self.assertRaises(tx.MigrationError):
            tx.validate_canary_target(
                self.manifest,
                target_class=target,
                canary_policy=policy,
            )

    def test_legacy_transient_blocks_v3_start_after_v2_stop(self):
        unit = (
            "workspace-ci-padataset-"
            "11111111-2222-3333-4444-555555555555.service"
        )
        self.systemd.states[unit] = True
        with self.assertRaisesRegex(tx.MigrationError, "legacy transient"):
            self.apply()
        target_unit = f"workspace-ci-v3-controller@{self.target}.service"
        self.assertFalse(self.systemd.active(target_unit))
        receipt_paths = list(self.migration_root.glob("*/transaction.json"))
        self.assertEqual(len(receipt_paths), 1)
        receipt = json.loads(receipt_paths[0].read_text())
        self.assertEqual(receipt["phase"], "ROLLBACK_REQUIRED")
        self.assertFalse(any(
            self.systemd.active(x)
            for x in tx.v2_controller_units(self.registry)
        ))

    def test_v3_transient_or_resource_claim_blocks_before_v2_mutation(self):
        unit = (
            f"workspace-ci-v3-{self.target}-"
            "11111111-2222-3333-4444-555555555555.service"
        )
        self.systemd.states[unit] = True
        with self.assertRaisesRegex(tx.MigrationError, "v3 transient"):
            self.apply()
        self.assertEqual(self.systemd.events, [])

        self.systemd.states[unit] = False
        (self.provisioner_state / "11111111-2222-3333-4444-555555555555.json").write_text(
            json.dumps({
                "request_id": "11111111-2222-3333-4444-555555555555",
                "state": "RESERVED",
                "resource_hold": False,
            })
        )
        with self.assertRaisesRegex(tx.MigrationError, "resource claims"):
            self.apply()
        self.assertEqual(self.systemd.events, [])

    def test_rollback_refuses_to_restore_v2_while_v3_transient_exists(self):
        receipt_path = self.apply()
        target_unit = f"workspace-ci-v3-controller@{self.target}.service"
        self.systemd.states[target_unit] = False
        transient = (
            f"workspace-ci-v3-{self.target}-"
            "11111111-2222-3333-4444-555555555555.service"
        )
        self.systemd.states[transient] = True
        self.systemd.events.clear()
        with self.assertRaisesRegex(tx.MigrationError, "v3 transient"):
            tx.rollback(
                systemd=self.systemd,
                registry=self.registry,
                root_policy=self.root_policy,
                receipt_path=receipt_path,
                provisioner_state_root=self.provisioner_state,
            )
        self.assertFalse(any(
            event[0] == "start"
            and event[1].startswith("workspace-ci-controller@")
            for event in self.systemd.events
        ))

    def test_transaction_sources_do_not_reference_quarantine_or_retry_receipt_paths(self):
        source = (ROOT / "scripts/lambda_ci_v3_migration_transaction.py").read_text()
        self.assertNotIn("quarantine_receipts", source)
        self.assertNotIn("retry_receipts", source)
        self.assertNotIn("RECOVERY_RETRY_INVALIDATED", source)


if __name__ == "__main__":
    unittest.main()
