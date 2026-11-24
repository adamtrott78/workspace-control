from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "benchmarks/workspace-semantic-execution/live_research_iterate_e1.py"


def text() -> str:
    return HARNESS.read_text(encoding="utf-8")


def test_live_e1_harness_compiles() -> None:
    source = text()
    compile(source, str(HARNESS), "exec")


def test_live_e1_has_required_real_topology() -> None:
    source = text()
    for marker in (
        "E1_ROOT_DECOMPOSE=PASS",
        "E1_EXACT_SOURCE=PASS",
        "E1_ANALYSIS=PASS",
        "E1_WORKSPACE_SHELL_READ_ONLY_PROBE=PASS",
        "E1_FAN_IN=PASS",
        "E1_RESEARCH_ITERATE=",
    ):
        assert marker in source


def test_live_e1_workspace_shell_is_literal_and_read_only() -> None:
    source = text()
    assert 'WORKSPACE_SHELL_PLUGIN_MENTION = "@Workspace Shell"' in source
    assert '"@Workspace Shell\\n@github\\n\\n"' in source
    assert "operation=runtime_inventory" in source
    assert "workspace_shell_exec and workspace_shell_run_reviewed_helper are prohibited" in source
    assert "E1_WORKSPACE_SHELL_EXPECTED_VALUES_HIDDEN=PASS" in source


def test_live_e1_binds_frozen_research_engine_source() -> None:
    source = text()
    assert 'RESEARCH_ENGINE_SHA = "1031861c03b2af8cff5cf72939bbbc83a95e65a4"' in source
    assert 'SOURCE_BLOB_SHA = "0d051fa50960708e0e773f6871c7e924c5796394"' in source
    assert "ReadOnlyRepositoryExecutor" in source
    assert "RepositoryReadPostconditionValidator" in source
