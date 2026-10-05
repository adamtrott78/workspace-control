import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "scope_control.py"
SPEC = importlib.util.spec_from_file_location("scope_control", SCRIPT)
scope_control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scope_control)


ENVELOPE = {
    "schema_version": 1,
    "task_id": "task-1",
    "objective": "Complete the bounded owning task.",
    "next_safe_action": "Run required validation and checkpoint.",
    "allowed_now": [
        "bounded fixes required for correctness",
        "changes required for the recorded next_safe_action",
    ],
    "defer_by_default": [
        "unrelated cleanup",
        "new abstractions",
        "adjacent hardening",
        "extra experiments",
    ],
    "explicit_authorizations": [],
    "closure_policy": {
        "stop_when_objective_satisfied": True,
        "defer_nonblocking_findings": True,
        "require_validation_pass": True,
        "require_durable_checkpoint": True,
    },
}


def finding(**overrides):
    base = {
        "id": "finding-1",
        "summary": "Adjacent improvement.",
        "evidence": ["Observed during current work."],
        "affects_correctness": False,
        "affects_safety": False,
        "affects_durability": False,
        "blocks_next_safe_action": False,
        "required_for_validation": False,
        "new_workstream": False,
        "suggested_owner": "follow-up",
        "urgency": "NORMAL",
    }
    base.update(overrides)
    return base


class ScopeControlTests(unittest.TestCase):
    def test_correctness_issue_is_required_correction(self):
        decision = scope_control.classify_finding(
            ENVELOPE,
            finding(affects_correctness=True),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.REQUIRED_CORRECTION,
        )
        self.assertTrue(decision["execute_now"])

    def test_safety_issue_is_required_correction(self):
        decision = scope_control.classify_finding(
            ENVELOPE,
            finding(affects_safety=True),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.REQUIRED_CORRECTION,
        )

    def test_durability_issue_is_required_correction(self):
        decision = scope_control.classify_finding(
            ENVELOPE,
            finding(affects_durability=True),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.REQUIRED_CORRECTION,
        )

    def test_next_action_blocker_is_bounded_enabling_change(self):
        decision = scope_control.classify_finding(
            ENVELOPE,
            finding(blocks_next_safe_action=True),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.BOUNDED_ENABLING_CHANGE,
        )
        self.assertTrue(decision["execute_now"])

    def test_validation_blocker_is_bounded_enabling_change(self):
        decision = scope_control.classify_finding(
            ENVELOPE,
            finding(required_for_validation=True),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.BOUNDED_ENABLING_CHANGE,
        )

    def test_nonblocking_adjacent_work_is_deferred(self):
        decision = scope_control.classify_finding(
            ENVELOPE,
            finding(new_workstream=True),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.DEFERRED_FOLLOWUP,
        )
        self.assertFalse(decision["execute_now"])

    def test_explicit_authorization_allows_scope_expansion(self):
        envelope = json.loads(json.dumps(ENVELOPE))
        envelope["explicit_authorizations"] = ["finding-1"]
        decision = scope_control.classify_finding(
            envelope,
            finding(new_workstream=True),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.AUTHORIZED_SCOPE_EXPANSION,
        )
        self.assertTrue(decision["execute_now"])
        self.assertTrue(decision["scope_expansion"])

    def test_required_correction_overrides_scope_expansion_label(self):
        envelope = json.loads(json.dumps(ENVELOPE))
        envelope["explicit_authorizations"] = ["finding-1"]
        decision = scope_control.classify_finding(
            envelope,
            finding(
                new_workstream=True,
                affects_correctness=True,
            ),
        )
        self.assertEqual(
            decision["classification"],
            scope_control.REQUIRED_CORRECTION,
        )

    def test_deferred_finding_builds_followup_record(self):
        item = finding()
        decision = scope_control.classify_finding(ENVELOPE, item)
        record = scope_control.build_followup(item, decision)
        self.assertEqual(record["finding_id"], item["id"])
        self.assertEqual(record["urgency"], "NORMAL")
        self.assertEqual(record["evidence"], item["evidence"])

    def test_followup_rejects_execute_now_decision(self):
        item = finding(affects_correctness=True)
        decision = scope_control.classify_finding(ENVELOPE, item)
        with self.assertRaises(scope_control.ScopeControlError):
            scope_control.build_followup(item, decision)

    def test_closure_requires_durable_checkpoint_first(self):
        state = {
            "objective_satisfied": True,
            "required_validation_passed": True,
            "mutation_durable": False,
            "blockers": [],
            "finding_decisions": [],
        }
        result = scope_control.scope_closure_decision(ENVELOPE, state)
        self.assertEqual(
            result["decision"],
            scope_control.CHECKPOINT_REQUIRED,
        )
        self.assertFalse(result["stop"])

    def test_execute_now_finding_keeps_work_bounded(self):
        item = finding(blocks_next_safe_action=True)
        decision = scope_control.classify_finding(ENVELOPE, item)
        state = {
            "objective_satisfied": False,
            "required_validation_passed": False,
            "mutation_durable": True,
            "blockers": [],
            "finding_decisions": [decision],
        }
        result = scope_control.scope_closure_decision(ENVELOPE, state)
        self.assertEqual(
            result["decision"],
            scope_control.CONTINUE_BOUNDED_WORK,
        )
        self.assertEqual(result["finding_ids"], [item["id"]])

    def test_unsatisfied_objective_continues_owning_task(self):
        state = {
            "objective_satisfied": False,
            "required_validation_passed": False,
            "mutation_durable": True,
            "blockers": [],
            "finding_decisions": [],
        }
        result = scope_control.scope_closure_decision(ENVELOPE, state)
        self.assertEqual(
            result["decision"],
            scope_control.CONTINUE_OWNING_TASK,
        )

    def test_required_validation_must_pass_before_closure(self):
        state = {
            "objective_satisfied": True,
            "required_validation_passed": False,
            "mutation_durable": True,
            "blockers": [],
            "finding_decisions": [],
        }
        result = scope_control.scope_closure_decision(ENVELOPE, state)
        self.assertEqual(
            result["decision"],
            scope_control.CONTINUE_OWNING_TASK,
        )

    def test_deferred_findings_do_not_block_scope_closure(self):
        item = finding(id="adjacent-1")
        decision = scope_control.classify_finding(ENVELOPE, item)
        state = {
            "objective_satisfied": True,
            "required_validation_passed": True,
            "mutation_durable": True,
            "blockers": [],
            "finding_decisions": [decision],
        }
        result = scope_control.scope_closure_decision(ENVELOPE, state)
        self.assertEqual(
            result["decision"],
            scope_control.CHECKPOINT_AND_STOP,
        )
        self.assertTrue(result["stop"])
        self.assertEqual(
            result["deferred_followup_ids"],
            ["adjacent-1"],
        )

    def test_blockers_prevent_scope_closure(self):
        state = {
            "objective_satisfied": True,
            "required_validation_passed": True,
            "mutation_durable": True,
            "blockers": ["canonical CI still running"],
            "finding_decisions": [],
        }
        result = scope_control.scope_closure_decision(ENVELOPE, state)
        self.assertEqual(
            result["decision"],
            scope_control.CONTINUE_OWNING_TASK,
        )
        self.assertFalse(result["stop"])

    def test_cli_classification(self):
        item = finding()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            envelope_path = root / "envelope.json"
            finding_path = root / "finding.json"
            envelope_path.write_text(json.dumps(ENVELOPE))
            finding_path.write_text(json.dumps(item))
            rc = scope_control.main(
                [
                    "classify",
                    "--envelope",
                    str(envelope_path),
                    "--finding",
                    str(finding_path),
                ]
            )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
