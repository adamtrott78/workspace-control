import importlib.util
import json
import os
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
    def proof(self):
        return {
            "schema_version": 1,
            "repository": repair.TARGET_REPOSITORY,
            "workflow_run_id": repair.TARGET_WORKFLOW_RUN_ID,
            "workflow_run_status": "completed",
            "workflow_run_conclusion": "success",
            "github_job_id": repair.TARGET_GITHUB_JOB_ID,
            "github_job_name": repair.TARGET_GITHUB_JOB_NAME,
            "github_job_status": "completed",
            "github_job_conclusion": "success",
        }

    def record(self):
        return {
            "schema_version": 1,
            "controller_policy_sha256": "a" * 64,
            "runner_request_id": repair.TARGET_GITHUB_JOB_ID,
            "github_job_id": repair.TARGET_GITHUB_JOB_ID,
            "workflow_run_id": repair.TARGET_WORKFLOW_RUN_ID,
            "workflow_path": ".github/workflows/workspace-ci-v3-migration-canary-workspace-control-control-small-v1.yml",
            "workflow_blob_sha": "b" * 40,
            "request_id": "11111111-2222-5333-8444-555555555555",
            "runner_name": "lambda-wc-control-deadbeef",
            "provision_attempt": 0,
            "state": "ACCEPTED",
            "scheduler_state": "ACCEPTED",
            "updated_at": "2026-11-02T00:00:00+00:00",
        }

    def test_github_proof_exact_success_is_accepted(self):
        repair._validate_github_proof(self.proof())

    def test_github_proof_nonterminal_is_rejected(self):
        proof = self.proof()
        proof["github_job_status"] = "in_progress"
        with self.assertRaises(repair.LedgerRepairError):
            repair._validate_github_proof(proof)

    def test_matching_transaction_requires_exact_accepted_source_and_terminal_phase(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            tx = root / "one"
            tx.mkdir()
            record = self.record()
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "ROLLED_BACK_LEGACY_RESTORED",
                        "target_runner_class_id": repair.TARGET_CLASS,
                        "source_head": repair.TARGET_CANARY_SOURCE_HEAD,
                        "controller_policy_sha256": record["controller_policy_sha256"],
                        "workflow_blob_sha": record["workflow_blob_sha"],
                    }
                )
            )
            with mock.patch.object(repair.migration, "MIGRATION_ROOT", root):
                self.assertEqual(repair._matching_canary_transactions(record), [tx / "transaction.json"])

            value = json.loads((tx / "transaction.json").read_text())
            value["phase"] = "CANARY_ACTIVE"
            (tx / "transaction.json").write_text(json.dumps(value))
            with mock.patch.object(repair.migration, "MIGRATION_ROOT", root):
                with self.assertRaises(repair.LedgerRepairError):
                    repair._matching_canary_transactions(record)

    def test_repair_terminalizes_only_exact_accepted_record_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            repo = root / "repo"
            repo.mkdir()
            proof_path = root / "proof.json"
            proof_path.write_text(json.dumps(self.proof()))

            config = root / "etc"
            config.mkdir()
            root_policy = {
                "runner_classes": {
                    repair.TARGET_CLASS: {
                        "repository": repair.TARGET_REPOSITORY,
                    }
                }
            }
            root_policy_path = config / "root-policy.json"
            root_policy_path.write_text(json.dumps(root_policy))

            state_root = root / "controller-state"
            class_root = state_root / repair.TARGET_CLASS
            class_root.mkdir(parents=True)
            ledger = class_root / f"scheduler-{repair.TARGET_GITHUB_JOB_ID}.json"
            ledger.write_text(json.dumps(self.record()) + "\n")
            os.chmod(ledger, 0o600)

            migration_root = root / "migration"
            tx = migration_root / "accepted"
            tx.mkdir(parents=True)
            record = self.record()
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "ROLLED_BACK_LEGACY_RESTORED",
                        "target_runner_class_id": repair.TARGET_CLASS,
                        "source_head": repair.TARGET_CANARY_SOURCE_HEAD,
                        "controller_policy_sha256": record["controller_policy_sha256"],
                        "workflow_blob_sha": record["workflow_blob_sha"],
                    }
                )
            )

            repair_root = root / "repairs"

            def simple_rewrite(path, payload):
                path.write_bytes(payload)
                os.chmod(path, 0o600)

            with (
                mock.patch.object(repair.os, "geteuid", return_value=0),
                mock.patch.object(repair, "ROOT_POLICY", root_policy_path),
                mock.patch.object(repair, "CONTROLLER_STATE_ROOT", state_root),
                mock.patch.object(repair, "REPAIR_ROOT", repair_root),
                mock.patch.object(repair.migration, "MIGRATION_ROOT", migration_root),
                mock.patch.object(repair, "_git_exact_head"),
                mock.patch.object(repair, "_assert_runtime_boundary"),
                mock.patch.object(repair, "_remove_stale_unconsumed_authority", return_value=True),
                mock.patch.object(repair, "_atomic_rewrite_preserving_owner", side_effect=simple_rewrite),
                mock.patch.object(repair.migration, "v3_resource_claims", return_value=[]),
                mock.patch.object(repair.production, "_assert_controller_ledgers_terminal"),
            ):
                receipt = repair.repair(
                    repo_root=repo,
                    expected_source_head="c" * 40,
                    github_proof_path=proof_path,
                    systemd=mock.Mock(),
                )

            self.assertIsNotNone(receipt)
            repaired = json.loads(ledger.read_text())
            self.assertEqual(repaired["state"], "COMPLETED")
            self.assertEqual(repaired["scheduler_state"], "GITHUB_JOB_COMPLETED_SUCCESS")
            self.assertEqual(
                repaired["terminalization_provenance"]["workflow_run_id"],
                repair.TARGET_WORKFLOW_RUN_ID,
            )
            receipt_data = json.loads(pathlib.Path(receipt).read_text())
            self.assertEqual(receipt_data["phase"], "COMMITTED")
            self.assertTrue(receipt_data["stale_unconsumed_production_authority_removed"])

    def test_live_resource_claim_blocks_terminalization(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            repo = root / "repo"
            repo.mkdir()
            proof_path = root / "proof.json"
            proof_path.write_text(json.dumps(self.proof()))
            config = root / "etc"
            config.mkdir()
            root_policy_path = config / "root-policy.json"
            root_policy_path.write_text(
                json.dumps(
                    {
                        "runner_classes": {
                            repair.TARGET_CLASS: {
                                "repository": repair.TARGET_REPOSITORY,
                            }
                        }
                    }
                )
            )
            state_root = root / "controller-state"
            class_root = state_root / repair.TARGET_CLASS
            class_root.mkdir(parents=True)
            ledger = class_root / f"scheduler-{repair.TARGET_GITHUB_JOB_ID}.json"
            record = self.record()
            ledger.write_text(json.dumps(record))
            os.chmod(ledger, 0o600)
            migration_root = root / "migration"
            tx = migration_root / "accepted"
            tx.mkdir(parents=True)
            (tx / "transaction.json").write_text(
                json.dumps(
                    {
                        "mode": "V3_ONE_CLASS_CANARY_GENERATION_EXCLUSION",
                        "phase": "ROLLED_BACK_LEGACY_RESTORED",
                        "target_runner_class_id": repair.TARGET_CLASS,
                        "source_head": repair.TARGET_CANARY_SOURCE_HEAD,
                        "controller_policy_sha256": record["controller_policy_sha256"],
                        "workflow_blob_sha": record["workflow_blob_sha"],
                    }
                )
            )
            with (
                mock.patch.object(repair.os, "geteuid", return_value=0),
                mock.patch.object(repair, "ROOT_POLICY", root_policy_path),
                mock.patch.object(repair, "CONTROLLER_STATE_ROOT", state_root),
                mock.patch.object(repair.migration, "MIGRATION_ROOT", migration_root),
                mock.patch.object(repair, "_git_exact_head"),
                mock.patch.object(repair, "_assert_runtime_boundary"),
                mock.patch.object(
                    repair.migration,
                    "v3_resource_claims",
                    return_value=[record["request_id"]],
                ),
            ):
                with self.assertRaisesRegex(repair.LedgerRepairError, "resource claim"):
                    repair.repair(
                        repo_root=repo,
                        expected_source_head="d" * 40,
                        github_proof_path=proof_path,
                        systemd=mock.Mock(),
                    )


if __name__ == "__main__":
    unittest.main()
