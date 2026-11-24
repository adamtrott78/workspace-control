from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-review.v1.15.json"
PROCEDURE = ROOT / "architecture/workspace-semantic-execution-stage12-real-instant-retry-procedure.v1.15.md"


def review() -> dict:
    return json.loads(REVIEW.read_text(encoding="utf-8"))


def test_v115_review_is_non_authority_and_binds_green_repair() -> None:
    r = review()
    assert r["status"] == "REVIEW_CANDIDATE_NON_AUTHORITY"
    assert r["predecessor"]["consumed"] is True
    assert r["predecessor"]["reusable"] is False
    assert r["repair"]["exact_head"] == "3058e98bc95087d3759631cd9b2c23065c8b1da4"
    assert r["repair"]["candidate_baseline"] == "d9f636ef508245459b3dd0a35b8d5587f533bac6"
    assert r["repair"]["exact_validation"]["workspace_control"]["result"] == "SUCCESS"
    assert r["repair"]["exact_validation"]["semantic_execution"]["result"] == "SUCCESS"
    assert r["repair"]["exact_validation"]["operator_bridge"]["result"] == "SUCCESS"
    assert r["approval_context"]["grants_this_review_execution_authority"] is False


def test_v115_review_records_true_hidden_continuity_contract() -> None:
    r = review()
    assert "validator_evidence_refs" in " ".join(r["repair"]["changes"])
    assert "STAGE12_Q2_CONTINUITY_TOKEN_HIDDEN=PASS" in " ".join(r["repair"]["changes"])
    text = PROCEDURE.read_text(encoding="utf-8")
    assert "q2_continuity_token_disclosed_in_worker_packet" in text
    assert "STAGE12_Q2_CONTINUITY_TOKEN_HIDDEN=PASS" in text
    assert "MUST NOT contain the continuity token value" in text


def test_v115_connected_tool_mentions_preserve_empirical_boundary() -> None:
    p = review()["plugin_mentions"]
    assert p["github"]["literal"] == "@github"
    assert p["github"]["empirical_status"] == "LIVE_PROVEN"
    assert p["workspace_shell"]["literal"] == "@Workspace Shell"
    assert p["workspace_shell"]["empirical_status"] == "NOT_YET_LIVE_PROVEN"
    assert "read-only Workspace Shell leaf" in p["workspace_shell"]["next_safe_probe"]
