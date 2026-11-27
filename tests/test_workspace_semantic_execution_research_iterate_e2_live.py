"""Static acceptance checks for the live E2 recovery harness."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "benchmarks/workspace-semantic-execution/live_research_iterate_e2.py"


def test_e2_live_harness_injects_and_fences_real_serviced_generation() -> None:
    text = HARNESS.read_text(encoding="utf-8")
    assert "E2_ANALYSIS_G0_READY=" in text
    assert "runtime.recover(" in text
    assert "e2_deliberate_worker_session_process_loss" in text
    assert "OperatorActionState.STALE" in text
    assert "ExecutorSessionState.NEEDS_REPLACEMENT" in text
    assert "E2_WORKER_PROCESS_SESSION_FENCE=PASS" in text


def test_e2_live_harness_rehydrates_from_postgres_and_replaces_session() -> None:
    text = HARNESS.read_text(encoding="utf-8")
    assert "E2_RUNTIME_REHYDRATION_FROM_POSTGRES=PASS" in text
    assert "source_validation_evidence" in text
    assert "broker.replace(" in text
    assert 'session_id=f"e2-chat:{token}:g1"' in text
    assert "E2_SESSION_REPLACEMENT=PASS" in text
    assert "session_generation=1" in text


def test_e2_live_harness_rejects_late_stale_worker_candidate() -> None:
    text = HARNESS.read_text(encoding="utf-8")
    assert "analysis-g0-stale.json" in text
    assert "version_before_stale" in text
    assert "e2_stale_worker_candidate_accepted" in text
    assert "e2_stale_worker_candidate_mutated_state" in text
    assert "E2_STALE_RESULT_REJECTED_WITHOUT_MUTATION=PASS" in text


def test_e2_live_harness_finishes_replacement_generation_and_existing_e1_safety() -> None:
    text = HARNESS.read_text(encoding="utf-8")
    assert "E2_ANALYSIS_G1_REPLACEMENT_READY=" in text
    assert "E2_ANALYSIS_RECOVERY=PASS" in text
    assert "E2_WORKSPACE_SHELL_READ_ONLY_PROBE=PASS" in text
    assert "E2_FAN_IN=PASS" in text
    assert "E2_SYNTHESIS_READY=" in text
    assert '"manual_durable_state_relay": False' in text
    assert '"browser_page_content_scraping": False' in text
    assert '"automatic_typing_or_submission": False' in text
    assert '"workspace_shell_exec_used": False' in text


def test_e2_live_harness_imports_cleanly_and_exposes_run_entrypoint() -> None:
    spec = importlib.util.spec_from_file_location("live_research_iterate_e2", HARNESS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert callable(module.run_e2)
    params = module._operator_params(
        task_id="test",
        action_id="action:test",
        slot_id="slot:test",
        sequence=9,
        target_ref="github-candidate://example/test.json",
        session_generation=1,
    )
    assert params.session_generation == 1
