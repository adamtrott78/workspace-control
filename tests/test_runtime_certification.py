import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "runtime_certification.py"
SPEC = importlib.util.spec_from_file_location("runtime_certification", SCRIPT)
runtime_certification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_certification)


EXECUTION_ID = "sha256:" + "a" * 64
PACKAGE_ID = "sha256:" + "b" * 64
COMPATIBILITY = {
    "driver_api_family": "cuda12-minor-compatible",
    "accelerator_arch": "sm86",
}


def stage_receipt(stage, status="PASS", execution_identity=EXECUTION_ID):
    return {
        "stage": stage,
        "status": status,
        "execution_identity": execution_identity,
    }


def certified_runtime():
    return {
        "schema_version": 1,
        "execution_identity": EXECUTION_ID,
        "package_identity": PACKAGE_ID,
        "compatibility_predicates": dict(COMPATIBILITY),
        "runtime_certified": True,
        "stage_receipts": [
            stage_receipt("C0_STATIC"),
            stage_receipt("C1_IMPORT_ACCELERATOR"),
            stage_receipt("C2A_BACKEND_TOOLCHAIN"),
            stage_receipt("C2B_ENGINE_BOOT"),
            stage_receipt("C3_CANARY"),
        ],
        "reuse_layers": {
            "R0_ENVIRONMENT": "VERIFIED_REUSE",
            "R1_CERTIFICATION": "VERIFIED_REUSE",
            "R2_COMPILED_CACHE": "VERIFIED_HIT",
            "R3_LIVE_SESSION": "NOT_APPLICABLE",
        },
    }


def operation_receipt(status="PASS", operation_id="sha256:" + "c" * 64):
    return {
        "schema_version": 1,
        "operation_id": operation_id,
        "task_id": "task-1",
        "git_sha": "deadbeef",
        "operation_type": "heavy-benchmark",
        "execution_identity": EXECUTION_ID,
        "status": status,
        "terminal_stage": "C4_DOMAIN",
    }


class RuntimeCertificationTests(unittest.TestCase):
    def test_execution_identity_is_canonical(self):
        first = runtime_certification.build_execution_identity(
            {"b": 2, "a": [1, {"x": True}]}
        )
        second = runtime_certification.build_execution_identity(
            {"a": [1, {"x": True}], "b": 2}
        )
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("sha256:"))

    def test_operation_identity_changes_with_material_inputs(self):
        common = dict(
            task_id="task-1",
            git_sha="abc",
            operation_type="benchmark",
            execution_identity=EXECUTION_ID,
        )
        first = runtime_certification.build_operation_id(
            **common,
            material_inputs={"source": "one"},
        )
        second = runtime_certification.build_operation_id(
            **common,
            material_inputs={"source": "two"},
        )
        self.assertNotEqual(first, second)

    def test_runtime_ready_requires_c0_through_c3_pass(self):
        cert = certified_runtime()
        self.assertTrue(runtime_certification.is_runtime_certified(cert))

        cert["runtime_certified"] = False
        cert["stage_receipts"][-1]["status"] = "NOT_RUN"
        self.assertFalse(runtime_certification.is_runtime_certified(cert))

    def test_runtime_certified_flag_cannot_overstate_evidence(self):
        cert = certified_runtime()
        cert["stage_receipts"][-1]["status"] = "FAIL"
        with self.assertRaises(
            runtime_certification.RuntimeCertificationError
        ):
            runtime_certification.validate_certification(cert)

    def test_execution_contract_change_is_typed_without_reinstall(self):
        cert = certified_runtime()
        decision = runtime_certification.evaluate_certification_reuse(
            cert,
            requested_package_identity=PACKAGE_ID,
            requested_execution_identity="sha256:" + "d" * 64,
            requested_compatibility_predicates=COMPATIBILITY,
        )
        self.assertEqual(decision["decision"], "MISS")
        self.assertEqual(
            decision["reason"],
            runtime_certification.MISS_EXECUTION_CONTRACT_CHANGED,
        )
        self.assertTrue(decision["package_environment_compatible"])
        self.assertFalse(decision["install_or_rebuild_required"])
        self.assertEqual(
            decision["revalidate_from_stage"],
            "C1_IMPORT_ACCELERATOR",
        )

    def test_package_change_requires_rebuild(self):
        cert = certified_runtime()
        decision = runtime_certification.evaluate_certification_reuse(
            cert,
            requested_package_identity="sha256:" + "e" * 64,
            requested_execution_identity=EXECUTION_ID,
            requested_compatibility_predicates=COMPATIBILITY,
        )
        self.assertEqual(
            decision["reason"],
            runtime_certification.MISS_PACKAGE_ENVIRONMENT_CHANGED,
        )
        self.assertTrue(decision["install_or_rebuild_required"])
        self.assertEqual(decision["revalidate_from_stage"], "C0_STATIC")

    def test_host_compatibility_change_fails_closed(self):
        cert = certified_runtime()
        decision = runtime_certification.evaluate_certification_reuse(
            cert,
            requested_package_identity=PACKAGE_ID,
            requested_execution_identity=EXECUTION_ID,
            requested_compatibility_predicates={
                "driver_api_family": "different",
                "accelerator_arch": "sm86",
            },
        )
        self.assertEqual(
            decision["reason"],
            runtime_certification.MISS_HOST_COMPATIBILITY_CHANGED,
        )
        self.assertEqual(decision["revalidate_from_stage"], "C0_STATIC")

    def test_incomplete_certification_resumes_at_first_nonpass_stage(self):
        cert = certified_runtime()
        cert["runtime_certified"] = False
        cert["stage_receipts"][3]["status"] = "FAIL"
        cert["stage_receipts"] = cert["stage_receipts"][:4]
        decision = runtime_certification.evaluate_certification_reuse(
            cert,
            requested_package_identity=PACKAGE_ID,
            requested_execution_identity=EXECUTION_ID,
            requested_compatibility_predicates=COMPATIBILITY,
        )
        self.assertEqual(
            decision["reason"],
            runtime_certification.MISS_CERTIFICATION_INCOMPLETE,
        )
        self.assertEqual(
            decision["revalidate_from_stage"],
            "C2B_ENGINE_BOOT",
        )

    def test_success_receipt_prevents_duplicate_execution(self):
        receipt = operation_receipt()
        decision = runtime_certification.recovery_decision(
            receipt,
            expected_operation_id=receipt["operation_id"],
        )
        self.assertEqual(
            decision["decision"],
            runtime_certification.RECOVERY_COMPLETED_REUSE,
        )
        self.assertFalse(decision["repeat_expensive_stage"])

    def test_running_receipt_requires_structural_owner_inspection(self):
        receipt = operation_receipt(status="RUNNING")
        receipt["owner_process"] = {
            "pid": 123,
            "role": "engine",
            "executable": "/usr/bin/python3",
            "argv": ["python3", "/repo/run.py"],
        }
        decision = runtime_certification.recovery_decision(
            receipt,
            expected_operation_id=receipt["operation_id"],
        )
        self.assertEqual(
            decision["decision"],
            runtime_certification.RECOVERY_INSPECT_OWNER,
        )
        self.assertFalse(decision["repeat_expensive_stage"])

    def test_mismatched_operation_receipt_never_blocks_new_identity(self):
        receipt = operation_receipt()
        decision = runtime_certification.recovery_decision(
            receipt,
            expected_operation_id="sha256:" + "f" * 64,
        )
        self.assertEqual(
            decision["decision"],
            runtime_certification.RECOVERY_EXECUTE_NEW_IDENTITY,
        )

    def test_structured_process_match_ignores_shell_wrapper_text(self):
        signature = {
            "executable_basenames": ["bash", "sh"],
            "script_arg_index": 1,
            "script_basenames": ["run-heavy-benchmark.sh"],
        }
        wrapper = [
            "bash",
            "-lc",
            "echo before; bash deploy/run-heavy-benchmark.sh; echo after",
        ]
        actual = ["bash", "deploy/run-heavy-benchmark.sh"]
        self.assertFalse(
            runtime_certification.process_matches_signature(
                wrapper, signature
            )
        )
        self.assertTrue(
            runtime_certification.process_matches_signature(
                actual, signature
            )
        )

    def test_failure_envelope_preserves_causal_child_error(self):
        envelope = {
            "schema_version": 1,
            "stage": "C2B_ENGINE_BOOT",
            "parent_failure": {
                "class": "RuntimeError",
                "message": "engine initialization failed",
            },
            "causal_failure": {
                "class": "RuntimeError",
                "message": "required compiler executable not found",
                "role": "jit-compiler",
            },
            "process": {
                "pid": 456,
                "role": "engine-core",
                "executable": "/usr/bin/python3",
                "argv": ["python3", "engine_core.py"],
            },
            "artifacts": {
                "targeted_log": "/tmp/targeted.log",
                "full_log": "/tmp/full.log",
            },
            "counts": {
                "engine_init_completed": 0,
                "inference_calls_started": 0,
                "inference_calls_completed": 0,
            },
            "state_flags": {
                "scientific_state_materialized": False,
                "production_routing_changed": False,
            },
        }
        self.assertTrue(
            runtime_certification.validate_failure_envelope(envelope)
        )

    def test_failure_envelope_rejects_impossible_call_counts(self):
        envelope = {
            "schema_version": 1,
            "stage": "C2B_ENGINE_BOOT",
            "parent_failure": {
                "class": "RuntimeError",
                "message": "parent",
            },
            "causal_failure": {
                "class": "RuntimeError",
                "message": "cause",
            },
            "counts": {
                "engine_init_completed": 0,
                "inference_calls_started": 0,
                "inference_calls_completed": 1,
            },
            "state_flags": {
                "scientific_state_materialized": False,
                "production_routing_changed": False,
            },
        }
        with self.assertRaises(
            runtime_certification.RuntimeCertificationError
        ):
            runtime_certification.validate_failure_envelope(envelope)

    def test_stage_receipts_reject_out_of_order_evidence(self):
        receipts = [
            stage_receipt("C1_IMPORT_ACCELERATOR"),
            stage_receipt("C0_STATIC"),
        ]
        with self.assertRaises(
            runtime_certification.RuntimeCertificationError
        ):
            runtime_certification.validate_stage_receipts(receipts)

    def test_cli_recovery_works_from_receipt_file(self):
        receipt = operation_receipt()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipt.json"
            path.write_text(json.dumps(receipt))
            rc = runtime_certification.main(
                [
                    "recover",
                    "--receipt",
                    str(path),
                    "--operation-id",
                    receipt["operation_id"],
                ]
            )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
