import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "progress_heartbeat.py"
SPEC = importlib.util.spec_from_file_location("progress_heartbeat", SCRIPT)
heartbeat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(heartbeat)


def snapshot(**overrides):
    data = {
        "schema_version": 1,
        "task_id": "task-1",
        "objective": "Complete the bounded correction.",
        "state": "VALIDATING",
        "milestones": [
            {"id": "diagnose", "label": "Diagnose failure", "status": "DONE"},
            {"id": "fix", "label": "Implement bounded fix", "status": "DONE"},
            {"id": "ci", "label": "Validate exact head", "status": "CURRENT"},
            {"id": "merge", "label": "Promote validated head", "status": "PENDING"},
        ],
        "current_operation": "CI is validating the exact reviewed head.",
        "scope_progress": {
            "completed_execute_now": 2,
            "total_execute_now": 3,
            "required_corrections_remaining": 0,
            "bounded_enabling_remaining": 0,
            "authorized_expansion_remaining": 0,
            "deferred_followups": 2,
        },
        "next_milestone": "CI PASS enables exact-head promotion.",
        "wait_state": {
            "active": True,
            "reason": "The implementation is complete and validation is authoritative.",
            "dependency": "GitHub Actions CI",
        },
        "meaningful_change": False,
    }
    data.update(overrides)
    return data


class ProgressHeartbeatTests(unittest.TestCase):
    def test_valid_snapshot(self):
        self.assertTrue(heartbeat.validate_snapshot(snapshot()))

    def test_rejects_two_current_milestones(self):
        data = snapshot()
        data["milestones"][3]["status"] = "CURRENT"
        with self.assertRaises(heartbeat.ProgressHeartbeatError):
            heartbeat.validate_snapshot(data)

    def test_rejects_completed_above_total(self):
        data = snapshot()
        data["scope_progress"]["completed_execute_now"] = 4
        with self.assertRaises(heartbeat.ProgressHeartbeatError):
            heartbeat.validate_snapshot(data)

    def test_active_wait_requires_reason_and_dependency(self):
        data = snapshot()
        data["wait_state"]["reason"] = None
        with self.assertRaises(heartbeat.ProgressHeartbeatError):
            heartbeat.validate_snapshot(data)

    def test_meaningful_change_emits(self):
        self.assertTrue(
            heartbeat.should_emit(
                event=None,
                tool_calls_since_update=0,
                elapsed_seconds=0,
                meaningful_change=True,
            )
        )

    def test_milestone_event_without_semantic_delta_suppresses(self):
        self.assertFalse(
            heartbeat.should_emit(
                event="MILESTONE_COMPLETED",
                tool_calls_since_update=0,
                elapsed_seconds=0,
                meaningful_change=False,
            )
        )

    def test_milestone_event_with_semantic_delta_emits(self):
        self.assertTrue(
            heartbeat.should_emit(
                event="MILESTONE_COMPLETED",
                tool_calls_since_update=0,
                elapsed_seconds=0,
                meaningful_change=True,
            )
        )

    def test_three_tool_calls_do_not_force_emit(self):
        self.assertFalse(
            heartbeat.should_emit(
                event="POLL_UNCHANGED",
                tool_calls_since_update=3,
                elapsed_seconds=5,
                meaningful_change=False,
            )
        )

    def test_tenth_tool_exhausts_silence_backstop(self):
        self.assertEqual(
            heartbeat.tool_gate(
                event="POLL_UNCHANGED",
                tool_calls_since_heartbeat=10,
                elapsed_seconds=5,
                meaningful_change=False,
            ),
            "HEARTBEAT_REQUIRED",
        )

    def test_tool_allowed_before_silence_backstop(self):
        self.assertEqual(
            heartbeat.tool_gate(
                event="POLL_UNCHANGED",
                tool_calls_since_heartbeat=9,
                elapsed_seconds=5,
                meaningful_change=False,
            ),
            "ALLOW_TOOL",
        )

    def test_state_change_expires_lease_early(self):
        self.assertEqual(
            heartbeat.tool_gate(
                event="MILESTONE_COMPLETED",
                tool_calls_since_heartbeat=1,
                elapsed_seconds=2,
                meaningful_change=False,
            ),
            "HEARTBEAT_REQUIRED",
        )

    def test_elapsed_time_alone_does_not_force_emit(self):
        self.assertFalse(
            heartbeat.should_emit(
                event="POLL_UNCHANGED",
                tool_calls_since_update=1,
                elapsed_seconds=600,
                meaningful_change=False,
            )
        )

    def test_short_unchanged_poll_suppresses(self):
        self.assertFalse(
            heartbeat.should_emit(
                event="POLL_UNCHANGED",
                tool_calls_since_update=1,
                elapsed_seconds=5,
                meaningful_change=False,
            )
        )

    def test_render_explains_external_wait_and_no_change(self):
        text = heartbeat.render_snapshot(snapshot())
        self.assertIn("Objective:", text)
        self.assertIn("2/3 execute-now items complete", text)
        self.assertIn("GitHub Actions CI", text)
        self.assertIn("No meaningful state change", text)
        self.assertIn("no additional implementation is justified", text)

    def test_render_scope_counts(self):
        text = heartbeat.render_snapshot(snapshot())
        self.assertIn("required=0", text)
        self.assertIn("enabling=0", text)
        self.assertIn("deferred=2", text)

    def test_cli_validate_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "heartbeat.json"
            path.write_text(json.dumps(snapshot()))
            self.assertEqual(
                heartbeat.main(["validate", "--file", str(path)]),
                0,
            )
            self.assertEqual(
                heartbeat.main(["render", "--file", str(path)]),
                0,
            )
            self.assertEqual(
                heartbeat.main([
                    "gate",
                    "--event", "POLL_UNCHANGED",
                    "--tool-calls", "10",
                    "--elapsed-seconds", "5",
                ]),
                0,
            )


if __name__ == "__main__":
    unittest.main()
