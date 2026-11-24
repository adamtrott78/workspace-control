from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py"
TX = ROOT / "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"


def test_v114_restores_literal_github_packet_invariant() -> None:
    text = HARNESS.read_text(encoding="utf-8")
    assert 'GITHUB_PLUGIN_MENTION = "@github"' in text
    assert "objective=_objective_with_plugin_mentions(" in text
    assert "plugin_mentions=plugin_mentions" in text


def test_v114_candidate_observation_is_remote_first_and_fail_closed() -> None:
    text = HARNESS.read_text(encoding="utf-8")
    assert '"ls-remote"' in text
    assert "candidate_branch_fetch_visibility_mismatch" in text
    assert text.index("observed = self._remote_head()") < text.index('"fetch"')


def test_v114_q1_exposes_observation_and_durable_ingest_boundaries() -> None:
    text = HARNESS.read_text(encoding="utf-8")
    observed = text.index("STAGE12_Q1_CANDIDATE_OBSERVED=")
    ingested = text.index("STAGE12_Q1_DURABLE_INGEST=PASS")
    q2 = text.index("STAGE12_Q2_REUSE_READY=")
    assert observed < ingested < q2


def test_v115_advances_latest_append_only_candidate_as_next_baseline() -> None:
    text = TX.read_text(encoding="utf-8")
    assert 'CANDIDATE_BASELINE="d9f636ef508245459b3dd0a35b8d5587f533bac6"' in text
    assert "git ls-remote" in text
