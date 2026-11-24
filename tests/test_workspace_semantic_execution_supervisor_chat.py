from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "architecture/workspace-semantic-execution-supervisor-chat.v0.1.md"


def text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_supervisor_is_explicitly_non_authoritative() -> None:
    t = text()
    assert "PROPOSED / NON-AUTHORITATIVE INTERFACE" in t
    assert "The Supervisor owns no task truth and no execution authority." in t
    assert "Conversation context is a cache only." in t
    assert "never directly execute an effect or alter authority state" in t


def test_supervisor_is_distinct_from_mechanical_operator_console() -> None:
    t = text()
    assert "Operator Console" in t
    assert "Workspace Supervisor" in t
    assert "Mechanical worker servicing remains the Operator Bridge's job." in t


def test_supervisor_defaults_to_instant_and_recovers_from_durable_state() -> None:
    t = text()
    assert "Use ChatGPT Instant / the lowest adequate reasoning tier by default." in t
    assert "After a lost/reset/replaced Supervisor session" in t
    assert "re-read durable mission state" in t


def test_supervisor_has_read_projection_and_proposal_only_port() -> None:
    t = text()
    assert "SupervisorReadModelPort" in t
    assert "SupervisorProposalPort" in t
    assert "SubmitCandidateObjective" in t
    assert "GetCriticalPath" in t
