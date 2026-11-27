from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.14.json"
FROZEN_HANDOFF_HEAD = "992542dbdfabb70c25d00704f97db634a781dd01"
Q1_BASELINE = "daa18627982a1d406eb88d44145113f0e99561e0"


def git(spec: str) -> str:
    return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()


def authority() -> dict:
    return json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))


def test_v114_authority_is_consumed_and_non_reusable() -> None:
    a = authority()
    assert a["status"] == "CONSUMED_PUBLICATION_PATH_PASS_Q2_CONTINUITY_CLAIM_INVALID"
    assert a["attempt_contract"]["attempts_authorized"] == 1
    assert a["attempt_contract"]["consumed"] is True
    assert a["attempt_contract"]["reusable"] is False
    assert a["attempt_contract"]["no_silent_retry"] is True


def test_v114_historical_authority_bindings_remain_exact() -> None:
    a = authority()
    b = a["exact_execution_bindings"]
    source = b["authority_parent_head"]
    assert source == FROZEN_HANDOFF_HEAD
    assert b["candidate_baseline"] == Q1_BASELINE
    for path in (
        "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh",
        "benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py",
        "tests/test_workspace_semantic_execution_stage12_v114.py",
        "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.14.json",
        "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.14.md",
        "operator-bridge/tools/workspace-operator-dev.ps1",
        "operator-bridge/tools/run-stage12-wop.ps1",
        "operator-bridge/tools/run-stage12-remote-bootstrap.sh",
    ):
        assert git(f"{source}:{path}") == b[path]
    assert git(f"{source}:operator-bridge/src") == b["operator-bridge/src_tree"]


def test_v114_closeout_preserves_exact_candidate_chain_and_invalidates_only_continuity_claim() -> None:
    c = authority()["live_closeout"]
    chain = c["candidate_chain"]
    assert chain["baseline"] == Q1_BASELINE
    assert chain["q1"] == "35d1e95be1ec544845cc2170dd57a6b36f86d0fa"
    assert chain["q2"] == "71f72bd6acf2d5217f026e9139b5af0dd1714925"
    assert chain["q3_replacement"] == "d9f636ef508245459b3dd0a35b8d5587f533bac6"
    assert chain["append_only_three_commits"] is True
    assert c["observed_results"]["q1_publication"] == "PASS"
    assert c["observed_results"]["q2_publication"] == "PASS"
    assert c["observed_results"]["q3_replacement_publication"] == "PASS"
    assert c["observed_results"]["persistent_session_continuity_claim"] == "INVALID_TEST_FIXTURE"
    assert c["continuity_invalidation"]["repair_required"] is True


def test_v114_security_and_a7_contract_remain_historical_truth() -> None:
    a = authority()
    f = a["accepted_frontend"]
    assert f["checkpoint"] == "a9532ca8b86b7839822939a970e16af1d4a41864"
    assert f["literal_plugin_prefix"] == "@github"
    assert f["autocomplete_selection_required"] is False
    assert f["tab_required"] is False
    assert f["click_required"] is False
    p = a["retained_prohibitions"]
    assert p["automatic_typing"] is False
    assert p["automatic_paste"] is False
    assert p["automatic_submission"] is False
    assert p["dom_or_page_content_scraping"] is False
    assert p["workspace_shell_authority_widening"] is False
    assert p["candidate_history_rewrite"] is False
