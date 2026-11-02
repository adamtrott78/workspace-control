import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
import uuid
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
    "lambda_ci_policy_compiler_v3_provider_tests",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
provider = load(
    "lambda_ci_v3_provisioner",
    ROOT / "scripts" / "lambda_ci_v3_provisioner.py",
)


class MutableClock:
    def __init__(self):
        self.value = datetime(2026, 10, 30, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


class V3ProvisionerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = compiler.compile_policy(ROOT)["root_projection"]
        cls.class_ids = sorted(cls.root["runner_classes"])
        cls.uid_by_class = {
            class_id: 41000 + index
            for index, class_id in enumerate(cls.class_ids, start=1)
        }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.store = provider.StateStore(
            self.base / "state",
            self.base / "run" / "jit",
        )
        self.clock = MutableClock()
        self.started = []

        def starter(record, jit_path):
            self.started.append((json.loads(json.dumps(record)), pathlib.Path(jit_path)))

        self.service = provider.V3Provisioner(
            root_projection=self.root,
            state_store=self.store,
            controller_uid_by_class=self.uid_by_class,
            clock=self.clock,
            start_supervisor=starter,
            unit_probe=None,
        )

    @staticmethod
    def request_id(index):
        return str(uuid.UUID(int=index))

    def reserve(self, class_id, index, *, suffix="test"):
        cls = self.root["runner_classes"][class_id]
        request = {
            "schema_version": 3,
            "operation": "RESERVE",
            "request_id": self.request_id(index),
            "runner_name": cls["runner_prefix"] + suffix,
        }
        return self.service.handle(self.uid_by_class[class_id], request)

    def launch(self, class_id, index, *, suffix="test", jit="ZmFrZS1qaXQ="):
        cls = self.root["runner_classes"][class_id]
        request = {
            "schema_version": 3,
            "operation": "LAUNCH",
            "request_id": self.request_id(index),
            "runner_name": cls["runner_prefix"] + suffix,
            "jit_config": jit,
        }
        return self.service.handle(self.uid_by_class[class_id], request)

    def status(self, class_id, index):
        return self.service.handle(
            self.uid_by_class[class_id],
            {
                "schema_version": 3,
                "operation": "STATUS",
                "request_id": self.request_id(index),
            },
        )

    def cancel(self, class_id, index):
        return self.service.handle(
            self.uid_by_class[class_id],
            {
                "schema_version": 3,
                "operation": "CANCEL",
                "request_id": self.request_id(index),
            },
        )

    def test_all_nine_controller_uids_reserve_only_their_root_owned_class(self):
        self.assertEqual(len(self.class_ids), 9)
        self.assertEqual(len(set(self.uid_by_class.values())), 9)
        for index, class_id in enumerate(self.class_ids, start=1):
            response = self.reserve(class_id, index)
            self.assertEqual(response["status"], "RESERVED", class_id)
            record = self.store.read(self.request_id(index))
            self.assertEqual(record["runner_class_id"], class_id)
            self.assertEqual(record["peer_uid"], self.uid_by_class[class_id])
            self.assertEqual(
                record["reserved_resources"],
                self.root["runner_classes"][class_id]["exclusive_resource_claims"],
            )
            self.assertEqual(self.cancel(class_id, index)["status"], "CANCELED")

    def test_request_cannot_supply_runner_class_or_resource_authority(self):
        class_id = self.class_ids[0]
        cls = self.root["runner_classes"][class_id]
        response = self.service.handle(
            self.uid_by_class[class_id],
            {
                "schema_version": 3,
                "operation": "RESERVE",
                "request_id": self.request_id(101),
                "runner_name": cls["runner_prefix"] + "x",
                "runner_class_id": self.class_ids[-1],
            },
        )
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertEqual(response["error_code"], "INVALID_REQUEST")
        self.assertIsNone(self.store.read(self.request_id(101)))

    def test_wrong_class_prefix_is_rejected_before_capacity_mutation(self):
        first, second = self.class_ids[:2]
        second_prefix = self.root["runner_classes"][second]["runner_prefix"]
        response = self.service.handle(
            self.uid_by_class[first],
            {
                "schema_version": 3,
                "operation": "RESERVE",
                "request_id": self.request_id(102),
                "runner_name": second_prefix + "cross-class",
            },
        )
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertEqual(response["error_code"], "RUNNER_NAME_INVALID")
        self.assertIsNone(self.store.read(self.request_id(102)))

    def test_unauthorized_peer_is_request_local(self):
        class_id = self.class_ids[0]
        cls = self.root["runner_classes"][class_id]
        response = self.service.handle(
            65530,
            {
                "schema_version": 3,
                "operation": "RESERVE",
                "request_id": self.request_id(103),
                "runner_name": cls["runner_prefix"] + "x",
            },
        )
        self.assertEqual(response["status"], "UNAUTHORIZED_PEER")
        self.assertEqual(response["error_code"], "UNAUTHORIZED_PEER")

    def test_duplicate_reserve_and_replay_conflict(self):
        class_id = self.class_ids[0]
        first = self.reserve(class_id, 104, suffix="same")
        self.assertEqual(first["status"], "RESERVED")
        duplicate = self.reserve(class_id, 104, suffix="same")
        self.assertEqual(duplicate["status"], "DUPLICATE")
        self.assertEqual(duplicate["receipt_status"], "RESERVED")
        conflict = self.reserve(class_id, 104, suffix="different")
        self.assertEqual(conflict["status"], "INVALID_REQUEST")
        self.assertEqual(conflict["error_code"], "REPLAY_CONFLICT")

    def test_host_capacity_busy_is_request_local_and_creates_no_record(self):
        first, second = self.class_ids[:2]
        self.assertEqual(self.reserve(first, 105)["status"], "RESERVED")
        busy = self.reserve(second, 106)
        self.assertEqual(busy["status"], "BUSY")
        self.assertIsNone(self.store.read(self.request_id(106)))

    def test_reservation_expires_and_fresh_request_can_allocate(self):
        first, second = self.class_ids[:2]
        response = self.reserve(first, 107)
        self.assertEqual(response["status"], "RESERVED")
        ttl = int(
            self.root["host_resource_policy"]["reservation_policy"]["ttl_seconds"]
        )
        self.clock.advance(ttl)
        status = self.status(first, 107)
        self.assertEqual(status["status"], "CANCELED")
        fresh = self.reserve(second, 108)
        self.assertEqual(fresh["status"], "RESERVED")

    def test_reserve_contains_no_jit_and_launch_uses_tmpfs_handoff(self):
        class_id = self.class_ids[0]
        self.assertEqual(self.reserve(class_id, 109)["status"], "RESERVED")
        self.assertFalse(self.store.jit_path(self.request_id(109)).exists())

        jit = "c2VjcmV0LWppdA=="
        launch = self.launch(class_id, 109, jit=jit)
        self.assertEqual(launch["status"], "PREPARING")
        self.assertEqual(len(self.started), 1)
        record = self.store.read(self.request_id(109))
        persisted = json.dumps(record, sort_keys=True)
        self.assertNotIn(jit, persisted)
        self.assertEqual(
            record["jit_sha256"],
            __import__("hashlib").sha256(jit.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(self.store.jit_path(self.request_id(109)).read_text(), jit)
        self.assertEqual(self.status(class_id, 109)["status"], "PREPARING")
        self.assertEqual(self.cancel(class_id, 109)["status"], "NOT_CANCELABLE")

    def test_launch_without_reservation_is_invalid_and_does_not_create_jit(self):
        class_id = self.class_ids[0]
        response = self.launch(class_id, 110)
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertEqual(response["error_code"], "RESERVATION_MISSING")
        self.assertFalse(self.store.jit_path(self.request_id(110)).exists())

    def test_launch_replay_is_duplicate_without_second_supervisor_or_jit_write(self):
        class_id = self.class_ids[0]
        self.assertEqual(self.reserve(class_id, 111)["status"], "RESERVED")
        self.assertEqual(self.launch(class_id, 111)["status"], "PREPARING")
        duplicate = self.launch(class_id, 111)
        self.assertEqual(duplicate["status"], "DUPLICATE")
        self.assertEqual(duplicate["receipt_status"], "ACCEPTED")
        self.assertEqual(len(self.started), 1)

    def test_jit_transport_bound_is_enforced(self):
        class_id = self.class_ids[0]
        self.assertEqual(self.reserve(class_id, 112)["status"], "RESERVED")
        response = self.launch(
            class_id,
            112,
            jit="x" * (provider.MAX_JIT_BYTES + 1),
        )
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertEqual(response["error_code"], "JIT_CONFIG_INVALID")
        self.assertEqual(self.store.read(self.request_id(112))["state"], "RESERVED")

    def test_persisted_class_quarantine_blocks_reserve(self):
        class_id = self.class_ids[0]
        self.store.quarantine(
            class_id,
            request_id=self.request_id(113),
            reason="INHERITED_CONTAINMENT",
            now=self.clock(),
        )
        response = self.reserve(class_id, 114)
        self.assertEqual(response["status"], "CLASS_QUARANTINED")
        self.assertIsNone(self.store.read(self.request_id(114)))

    def test_missing_supervisor_and_runner_after_grace_quarantines_and_holds(self):
        class_id = self.class_ids[0]
        self.assertEqual(self.reserve(class_id, 115)["status"], "RESERVED")
        self.assertEqual(self.launch(class_id, 115)["status"], "PREPARING")
        self.service.unit_probe = lambda _unit: False
        self.clock.advance(provider.RECONCILE_GRACE_SECONDS)
        status = self.status(class_id, 115)
        self.assertEqual(status["status"], "FAILED")
        record = self.store.read(self.request_id(115))
        self.assertTrue(record["resource_hold"])
        self.assertFalse(record["cleanup_verified"])
        self.assertIn(class_id, self.store.quarantines())

        other = self.class_ids[1]
        self.assertEqual(self.reserve(other, 116)["status"], "BUSY")

    def test_worker_consumes_jit_and_persists_terminal_without_raw_jit(self):
        class_id = self.class_ids[0]
        self.assertEqual(self.reserve(class_id, 117)["status"], "RESERVED")
        jit = "d29ya2VyLWppdA=="
        self.assertEqual(self.launch(class_id, 117, jit=jit)["status"], "PREPARING")

        calls = []

        def launcher(request, spec):
            calls.append((request.request_id, spec["runner_class_id"]))
            return {"terminal_status": "SUCCEEDED"}

        rc = provider.run_worker(
            root_projection=self.root,
            state_store=self.store,
            request_id=self.request_id(117),
            launcher=launcher,
            unit_probe=None,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [(self.request_id(117), class_id)])
        self.assertFalse(self.store.jit_path(self.request_id(117)).exists())
        record = self.store.read(self.request_id(117))
        self.assertEqual(record["state"], "COMPLETED")
        self.assertTrue(record["cleanup_verified"])
        self.assertFalse(record["resource_hold"])
        self.assertNotIn(jit, json.dumps(record, sort_keys=True))

    def test_worker_cleanup_failure_quarantines_class_and_retains_resource(self):
        class_id = self.class_ids[0]
        self.assertEqual(self.reserve(class_id, 118)["status"], "RESERVED")
        self.assertEqual(self.launch(class_id, 118)["status"], "PREPARING")

        def launcher(_request, _spec):
            raise provider.runtime.RuntimeCleanupError("synthetic cleanup failure")

        rc = provider.run_worker(
            root_projection=self.root,
            state_store=self.store,
            request_id=self.request_id(118),
            launcher=launcher,
            unit_probe=None,
        )
        self.assertEqual(rc, 1)
        record = self.store.read(self.request_id(118))
        self.assertEqual(record["state"], "FAILED")
        self.assertTrue(record["resource_hold"])
        self.assertFalse(record["cleanup_verified"])
        self.assertIn(class_id, self.store.quarantines())

    def test_worker_rejects_root_policy_binding_drift_before_execution(self):
        class_id = self.class_ids[0]
        self.assertEqual(self.reserve(class_id, 119)["status"], "RESERVED")
        self.assertEqual(self.launch(class_id, 119)["status"], "PREPARING")
        drifted = json.loads(json.dumps(self.root))
        drifted["root_policy_sha256"] = "0" * 64
        calls = []

        def launcher(_request, _spec):
            calls.append("executed")
            return {}

        rc = provider.run_worker(
            root_projection=drifted,
            state_store=self.store,
            request_id=self.request_id(119),
            launcher=launcher,
            unit_probe=None,
        )
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])
        self.assertFalse(self.store.jit_path(self.request_id(119)).exists())
        record = self.store.read(self.request_id(119))
        self.assertEqual(record["state"], "FAILED")
        self.assertEqual(record["failure_reason"], "ROOT_POLICY_BINDING_MISMATCH")
        self.assertTrue(record["cleanup_verified"])
        self.assertFalse(record["resource_hold"])

    def test_controller_uid_map_rejects_duplicate_numeric_identity(self):
        users = [
            cls["controller_peer"]["unix_user"]
            for cls in self.root["runner_classes"].values()
        ]
        self.assertEqual(len(users), 9)
        with self.assertRaisesRegex(provider.V3ServiceError, "maps to both"):
            provider.build_controller_uid_map(
                self.root,
                resolver=lambda _user: 42000,
            )


if __name__ == "__main__":
    unittest.main()
