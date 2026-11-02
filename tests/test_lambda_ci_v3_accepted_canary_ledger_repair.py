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


repair = load(
    "lambda_ci_v3_accepted_canary_ledger_repair",
    ROOT / "scripts" / "lambda_ci_v3_accepted_canary_ledger_repair.py",
)


class AcceptedCanaryLedgerRepairTests(unittest.TestCase):
    def proof_payload(self):
        jobs = []
        for spec in repair.CANARIES:
            jobs.append(
                {
                    "repository": spec["repository"],
                    "workflow_run_id": spec["workflow_run_id"],
                    "workflow_run_status": "completed",
                    "workflow_run_conclusion": spec["github_job_conclusion"],
                    "github_job_id": spec["github_job_id"],
                    "github_job_name": spec["github_job_name"],
                    "github_job_status": "completed",
                    "github_job_conclusion": spec["github_job_conclusion"],
                }
            )
        return {"schema_version": 1, "jobs": jobs}

    def record_for(self, spec, state="ACCEPTED"):
        return {
            "schema_version": 1,
            "controller_policy_sha256": "a" * 64,
            "runner_request_id": spec["github_job_id"],
            "github_job_id": spec["github_job_id"],
            "workflow_run_id": spec["workflow_run_id"],
            "workflow_path": ".github/workflows/test.yml",
            "workflow_blob_sha": "b" * 40,
            "request_id": f"request-{spec['github_job_id']}",
            "runner_name": f"runner-{spec['github_job_id']}",
            "provision_attempt": 0,
            "state": state,
            "scheduler_state": state,
            "updated_at": "2026-11-02T00:00:00+00:00",
        }

    def test_terminal_proof_exact_set_is_accepted(self):
        proofs = repair._validate_terminal_proofs(self.proof_payload())
        self.assertEqual(set(proofs), {repair._spec_key(spec) for spec in repair.CANARIES})

    def test_terminal_proof_conclusion_drift_is_rejected(self):
        payload = self.proof_payload()
        payload["jobs"][0]["github_job_conclusion"] = "failure"
        with self.assertRaises(repair.LedgerRepairError):
            repair._validate_terminal_proofs(payload)

    def test_unknown_nonterminal_is_visible_before_mutation(self):
        root_policy = {"runner_classes": {"unknown-class": {}}}
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            class_root = root / "unknown-class"
            class_root.mkdir()
            path = class_root / "scheduler-99.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "runner_request_id": 99,
                        "state": "ACCEPTED",
                    }
                )
            )
            found = repair._load_nonterminal_ledgers(root, root_policy)
            self.assertEqual(set(found), {("unknown-class", 99)})

    def test_terminal_ledgers_are_not_selected_for_repair(self):
        spec = repair.CANARIES[0]
        root_policy = {"runner_classes": {spec["class_id"]: {}}}
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            class_root = root / spec["class_id"]
            class_root.mkdir()
            path = class_root / f"scheduler-{spec['github_job_id']}.json"
            path.write_text(json.dumps(self.record_for(spec, state="COMPLETED")))
            found = repair._load_nonterminal_ledgers(root, root_policy)
            self.assertEqual(found, {})

    def test_exact_transaction_binding_requires_terminal_rollback(self):
        spec = dict(repair.CANARIES[1])
        record = self.record_for(spec)
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            tx = root / spec["transaction_id"]
            tx.mkdir()
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "ROLLED_BACK_LEGACY_RESTORED",
                        "target_runner_class_id": spec["class_id"],
                        "source_head": repair.CANARY_SOURCE_HEAD,
                        "controller_policy_sha256": record["controller_policy_sha256"],
                        "workflow_blob_sha": record["workflow_blob_sha"],
                    }
                )
            )
            with mock.patch.object(repair.migration, "MIGRATION_ROOT", root):
                self.assertEqual(
                    repair._matching_transaction(spec, record),
                    tx / "transaction.json",
                )
            value = json.loads((tx / "transaction.json").read_text())
            value["phase"] = "CANARY_ACTIVE"
            (tx / "transaction.json").write_text(json.dumps(value))
            with mock.patch.object(repair.migration, "MIGRATION_ROOT", root):
                with self.assertRaises(repair.LedgerRepairError):
                    repair._matching_transaction(spec, record)

    def test_success_and_failure_map_to_distinct_terminal_states(self):
        by_conclusion = {
            spec["github_job_conclusion"]:
            ("COMPLETED" if spec["github_job_conclusion"] == "success" else "FAILED")
            for spec in repair.CANARIES
        }
        self.assertEqual(by_conclusion["success"], "COMPLETED")
        self.assertEqual(by_conclusion["failure"], "FAILED")


if __name__ == "__main__":
    unittest.main()
