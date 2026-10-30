import copy
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

compiler_spec = importlib.util.spec_from_file_location(
    "lambda_ci_policy_compiler",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
compiler = importlib.util.module_from_spec(compiler_spec)
assert compiler_spec.loader is not None
sys.modules["lambda_ci_policy_compiler"] = compiler
compiler_spec.loader.exec_module(compiler)

planes_spec = importlib.util.spec_from_file_location(
    "lambda_ci_v3_control_planes",
    ROOT / "scripts" / "lambda_ci_v3_control_planes.py",
)
planes = importlib.util.module_from_spec(planes_spec)
assert planes_spec.loader is not None
sys.modules["lambda_ci_v3_control_planes"] = planes
planes_spec.loader.exec_module(planes)

overlay = __import__("json").loads(
    (ROOT / "architecture/lambda-ci-deployment-overlay.v1.json").read_text()
)


class V3ControlPlanePlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)

    def model(self, *, overlay_state=None, receipts=None):
        return planes.MaintenancePlaneModel(
            root_projection=self.compiled["root_projection"],
            overlay=copy.deepcopy(overlay_state or overlay),
            class_quarantine_receipts=receipts,
        )

    def test_diagnose_is_read_only(self):
        m = self.model()
        before = copy.deepcopy(m.overlay)
        result = m.execute(
            operation="DIAGNOSE_RUNNER_CLASS",
            runner_class_id="workspace-control-control-small-v1",
        )
        self.assertEqual(result.status, "OK")
        self.assertFalse(result.mutated)
        self.assertEqual(result.authority, "READ_ONLY")
        self.assertEqual(m.overlay, before)

    def test_host_attest_is_read_only_and_never_enables_execution(self):
        m = self.model()
        before = copy.deepcopy(m.overlay)
        result = m.execute(
            operation="HOST_ATTEST_RUNNER_CLASS",
            runner_class_id="research-model-dual-public-v1",
        )
        self.assertEqual(result.status, "OK")
        self.assertFalse(result.mutated)
        self.assertEqual(m.overlay, before)
        self.assertEqual(
            result.detail["execution_contract_id"],
            "model-dual-public-v1",
        )

    def test_restart_cannot_activate_inactive_controller(self):
        m = self.model()
        result = m.execute(
            operation="RESTART_RUNNER_CLASS_CONTROLLER",
            runner_class_id="workspace-control-control-small-v1",
        )
        self.assertEqual(result.status, "NOT_INSTALLED")
        self.assertFalse(result.mutated)

        active = copy.deepcopy(overlay)
        cid = "workspace-control-control-small-v1"
        active["classes"][cid]["install_state"] = "INSTALLED"
        m = self.model(overlay_state=active)
        result = m.execute(
            operation="RESTART_RUNNER_CLASS_CONTROLLER",
            runner_class_id=cid,
        )
        self.assertEqual(result.status, "NOT_ACTIVE")

    def test_restart_active_clear_class_preserves_all_route_state(self):
        active = copy.deepcopy(overlay)
        cid = "workspace-control-control-small-v1"
        active["classes"][cid]["install_state"] = "INSTALLED"
        active["classes"][cid]["controller_state"] = "ACTIVE"
        before_routes = copy.deepcopy(active["routes"])
        m = self.model(overlay_state=active)
        result = m.execute(
            operation="RESTART_RUNNER_CLASS_CONTROLLER",
            runner_class_id=cid,
        )
        self.assertEqual(result.status, "RESTART_AUTHORIZED")
        self.assertEqual(m.overlay["routes"], before_routes)
        self.assertEqual(m.overlay["classes"][cid]["controller_state"], "ACTIVE")

    def test_restart_contained_class_is_denied(self):
        state = copy.deepcopy(overlay)
        cid = "research-model-dual-public-v1"
        state["classes"][cid]["install_state"] = "INSTALLED"
        state["classes"][cid]["controller_state"] = "ACTIVE"
        # This is intentionally inconsistent input to prove maintenance refuses
        # to act on a contained class even if another layer marked it active.
        m = self.model(overlay_state=state)
        result = m.execute(
            operation="RESTART_RUNNER_CLASS_CONTROLLER",
            runner_class_id=cid,
        )
        self.assertEqual(result.status, "CONTAINED")

    def test_reset_stale_requires_exact_v3_class_quarantine_receipt(self):
        cid = "research-model-dual-public-v1"
        state = copy.deepcopy(overlay)
        state["classes"][cid]["install_state"] = "INSTALLED"
        state["classes"][cid]["containment"] = {
            "state": "CLASS_QUARANTINED",
            "source": "v3 cleanup failure",
        }
        receipt = "11111111-2222-3333-4444-555555555555"
        m = self.model(overlay_state=state, receipts={cid: receipt})

        mismatch = m.execute(
            operation="RESET_STALE_RUNNER_CLASS",
            runner_class_id=cid,
            quarantine_receipt_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )
        self.assertEqual(mismatch.status, "QUARANTINE_RECEIPT_MISMATCH")
        self.assertEqual(
            m.overlay["classes"][cid]["containment"]["state"],
            "CLASS_QUARANTINED",
        )

        good = m.execute(
            operation="RESET_STALE_RUNNER_CLASS",
            runner_class_id=cid,
            quarantine_receipt_id=receipt,
        )
        self.assertEqual(good.status, "CONTAINMENT_CLEARED")
        self.assertTrue(good.mutated)
        self.assertEqual(m.overlay["classes"][cid]["containment"]["state"], "CLEAR")
        self.assertEqual(m.overlay["classes"][cid]["controller_state"], "INACTIVE")
        self.assertTrue(all(
            route["admission_state"] == "DISABLED"
            for route in m.overlay["routes"].values()
        ))

    def test_legacy_inherited_containment_cannot_be_cleared_by_v3_reset_stale(self):
        cid = "research-model-dual-public-v1"
        m = self.model()
        result = m.execute(
            operation="RESET_STALE_RUNNER_CLASS",
            runner_class_id=cid,
            quarantine_receipt_id="a7880e15-b29c-4b2b-bccd-3a34745f9ded",
        )
        self.assertEqual(result.status, "NO_CLASS_QUARANTINE_RECEIPT")
        self.assertEqual(
            m.overlay["classes"][cid]["containment"]["state"],
            "INHERITED_CONTAINED",
        )

    def test_unknown_maintenance_class_and_operation_fail_closed(self):
        m = self.model()
        with self.assertRaisesRegex(planes.PlaneError, "UNKNOWN_RUNNER_CLASS"):
            m.execute(
                operation="DIAGNOSE_RUNNER_CLASS",
                runner_class_id="research-infinite-gpu-v1",
            )
        with self.assertRaisesRegex(planes.PlaneError, "UNKNOWN_MAINTENANCE_OPERATION"):
            m.execute(
                operation="START_SCIENCE_NOW",
                runner_class_id="workspace-control-control-small-v1",
            )

    def test_reconciliation_binds_generation_and_installs_without_activation(self):
        before = copy.deepcopy(overlay)
        r = planes.ReconciliationPlaneModel(
            compiled=self.compiled,
            overlay=before,
        )
        after = r.install_generation()
        self.assertEqual(
            after["catalog_generation_sha256"],
            self.compiled["catalog_generation_sha256"],
        )
        self.assertTrue(all(
            state["install_state"] == "INSTALLED"
            for state in after["classes"].values()
        ))
        self.assertTrue(all(
            state["controller_state"] == "INACTIVE"
            for state in after["classes"].values()
        ))
        self.assertTrue(all(
            route["admission_state"] == "DISABLED"
            for route in after["routes"].values()
        ))
        r.assert_no_activation_delta(before, after)

    def test_reconciliation_preserves_legacy_quarantine_and_retry_receipts_exactly(self):
        before = copy.deepcopy(overlay)
        r = planes.ReconciliationPlaneModel(
            compiled=self.compiled,
            overlay=before,
        )
        after = r.install_generation()
        self.assertEqual(after["legacy"], before["legacy"])
        self.assertEqual(
            after["classes"]["research-model-dual-public-v1"]["containment"],
            before["classes"]["research-model-dual-public-v1"]["containment"],
        )

    def test_reconciliation_subset_install_still_cannot_activate(self):
        before = copy.deepcopy(overlay)
        r = planes.ReconciliationPlaneModel(
            compiled=self.compiled,
            overlay=before,
        )
        target = "padataset-cpu-public-v1"
        after = r.install_generation(runner_class_ids=[target])
        self.assertEqual(after["classes"][target]["install_state"], "INSTALLED")
        for cid, state in after["classes"].items():
            if cid != target:
                self.assertEqual(state["install_state"], "NOT_INSTALLED")
            self.assertEqual(state["controller_state"], "INACTIVE")
        r.assert_no_activation_delta(before, after)

    def test_reconciliation_unknown_class_fails_before_state_return(self):
        r = planes.ReconciliationPlaneModel(
            compiled=self.compiled,
            overlay=overlay,
        )
        with self.assertRaisesRegex(planes.PlaneError, "UNKNOWN_RUNNER_CLASSES"):
            r.install_generation(runner_class_ids=["made-up-class"])

    def test_reconciliation_fault_is_atomic_to_caller_state(self):
        before = copy.deepcopy(overlay)
        r = planes.ReconciliationPlaneModel(
            compiled=self.compiled,
            overlay=before,
        )
        with self.assertRaisesRegex(
            planes.PlaneError,
            "SIMULATED_RECONCILIATION_FAILURE",
        ):
            r.install_generation(fault_after=3)
        self.assertEqual(before, overlay)
        self.assertEqual(r.overlay, overlay)

    def test_reconciliation_activation_delta_detector_fails_closed(self):
        before = copy.deepcopy(overlay)
        after = copy.deepcopy(before)
        cid = "workspace-control-control-small-v1"
        after["classes"][cid]["controller_state"] = "ACTIVE"
        with self.assertRaisesRegex(
            planes.PlaneError,
            "changed controller state",
        ):
            planes.ReconciliationPlaneModel.assert_no_activation_delta(before, after)

        after = copy.deepcopy(before)
        after["routes"]["workspace-control:control-validation"]["admission_state"] = "ENABLED"
        with self.assertRaisesRegex(
            planes.PlaneError,
            "changed route admission",
        ):
            planes.ReconciliationPlaneModel.assert_no_activation_delta(before, after)


if __name__ == "__main__":
    unittest.main()
