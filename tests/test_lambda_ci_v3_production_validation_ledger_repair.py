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
    "lambda_ci_v3_production_validation_ledger_repair",
    SCRIPTS / "lambda_ci_v3_production_validation_ledger_repair.py",
)


class ProductionValidationLedgerRepairTests(unittest.TestCase):
    def proof_payload(self):
        return {
            "schema_version": 1,
            "jobs": [
                {
                    "repository": repair.TARGET_REPOSITORY,
                    "workflow_run_id": spec["workflow_run_id"],
                    "workflow_run_status": "completed",
                    "workflow_run_conclusion": spec["github_job_conclusion"],
                    "github_job_id": spec["github_job_id"],
                    "github_job_status": "completed",
                    "github_job_conclusion": spec["github_job_conclusion"],
                }
                for spec in repair.KNOWN_HISTORY
            ],
        }

    def test_exact_github_terminal_proofs_are_accepted(self):
        proofs = repair._validate_proofs(self.proof_payload())
        self.assertEqual(set(proofs), {x["github_job_id"] for x in repair.KNOWN_HISTORY})

    def test_nonterminal_github_proof_is_rejected(self):
        payload = self.proof_payload()
        payload["jobs"][1]["github_job_status"] = "in_progress"
        with self.assertRaises(repair.RepairError):
            repair._validate_proofs(payload)

    def test_unknown_nonterminal_ledger_remains_visible(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            class_root = root / "unknown-v1"
            class_root.mkdir()
            (class_root / "scheduler-99.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "runner_request_id": 99,
                        "state": "ACCEPTED",
                    }
                )
            )
            found = repair._nonterminal_ledgers(
                root, {"runner_classes": {"unknown-v1": {}}}
            )
            self.assertIn(("unknown-v1", 99), found)

    def test_terminal_mapping_is_fail_closed(self):
        self.assertEqual(repair._terminal_state("failure"), "FAILED")
        self.assertEqual(repair._terminal_state("cancelled"), "CANCELED")
        self.assertEqual(repair._terminal_state("success"), "COMPLETED")
        with self.assertRaises(KeyError):
            repair._terminal_state("neutral")

    def test_exact_rolled_back_transaction_binding(self):
        spec = dict(repair.KNOWN_HISTORY[1])
        record = {
            "controller_policy_sha256": "a" * 64,
            "workflow_blob_sha": "b" * 40,
        }
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            tx_dir = root / spec["transaction_id"]
            tx_dir.mkdir()
            (tx_dir / "transaction.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "mode": "V3_PRODUCTION_GENERATION_CUTOVER",
                        "transaction_id": spec["transaction_id"],
                        "source_head": spec["source_head"],
                        "production_generation_sha256": spec[
                            "production_generation_sha256"
                        ],
                        "phase": "ROLLED_BACK_LEGACY_RESTORED",
                        "controller_policy_sha256": {
                            repair.TARGET_CLASS: record[
                                "controller_policy_sha256"
                            ]
                        },
                        "workflow_bindings": {
                            repair.TARGET_ROUTE: {
                                "new_blob_sha": record["workflow_blob_sha"]
                            }
                        },
                    }
                )
            )
            with mock.patch.object(repair.migration, "MIGRATION_ROOT", root):
                self.assertEqual(
                    repair._validate_transaction(spec, record),
                    tx_dir / "transaction.json",
                )

            value = json.loads((tx_dir / "transaction.json").read_text())
            value["phase"] = "V3_PRODUCTION_ACTIVE"
            (tx_dir / "transaction.json").write_text(json.dumps(value))
            with mock.patch.object(repair.migration, "MIGRATION_ROOT", root):
                with self.assertRaises(repair.RepairError):
                    repair._validate_transaction(spec, record)


if __name__ == "__main__":
    unittest.main()
