from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "architecture/workspace-semantic-execution-e3-live-binding-manifest.v0.1.json"
ROUTE = ROOT / "benchmarks/workspace-semantic-execution/private_route_research_iterate_e3_a10_v1.sh"
WRAPPER = ROOT / "benchmarks/workspace-semantic-execution/live_research_iterate_e3_a10_v1.py"
CLOSURE = ROOT / "benchmarks/workspace-semantic-execution/e3_live_binding_closure_v1.py"
LAUNCHER = ROOT / "operator-bridge/tools/run-research-iterate-e3-a10-wop.ps1"
BOOTSTRAP = ROOT / "operator-bridge/tools/run-research-iterate-e3-a10-remote-bootstrap.sh"


def _load_closure():
    spec = importlib.util.spec_from_file_location("e3_binding_closure_test", CLOSURE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_manifest_closes_repo_blob_bindings() -> None:
    closure = _load_closure()
    manifest = closure.load_manifest(MANIFEST)
    closure.validate_repo_manifest(ROOT, manifest)

    assert manifest["candidate_branch"] == "worker-result-candidates-v1"
    assert manifest["candidate_baseline"] == "968db0800e9dcdee6e5a784889d74653276fb184"
    assert manifest["root_packet_sha256"] == (
        "f104a451c60ee168f9236b0075b1a00c20b2bb12f40dbd23b414dff6ae74d60b"
    )


def test_a10_consumers_do_not_duplicate_manifest_sha_values() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    route = ROUTE.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    launcher = LAUNCHER.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    forbidden = {
        manifest["candidate_baseline"],
        manifest["provenance"]["semantic_sha"],
        manifest["provenance"]["a8_frontend_review_head"],
        manifest["provenance"]["a8_frontend_source_head"],
        manifest["provenance"]["a8_frontend_src_tree"],
        manifest["provenance"]["accepted_a7_dev_harness_blob"],
        manifest["provenance"]["worker_result_schema_review_head"],
        manifest["provenance"]["worker_result_schema_blob"],
    }
    for source in (route, wrapper, launcher, bootstrap):
        for value in forbidden:
            assert value not in source

    assert "CANDIDATE_BASELINE =" not in wrapper
    assert "--candidate-baseline" not in route
    assert "--candidate-baseline" not in wrapper
    assert "workspace-semantic-execution-e3-live-binding-manifest.v0.1.json" in route
    assert "workspace-semantic-execution-e3-live-binding-manifest.v0.1.json" in launcher
    assert "--binding-manifest" in wrapper
    assert "--binding-manifest" in route


def test_a10_consumption_is_after_deterministic_binding_and_runtime_preflight() -> None:
    route = ROUTE.read_text(encoding="utf-8")
    closure = route.index('echo "E3_A10_BINDING_CLOSURE=PASS"')
    candidate = route.index('echo "E3_A10_CANDIDATE_BASELINE=PASS"')
    dependency = route.index('PSYCOPG_DEPENDENCY_PIN=PASS')
    postgres = route.index('POSTGRES_STARTED=1')
    route_verified = route.index('TAILSCALE_E3_A10_ROUTE_EXACT_BINDING=PASS')
    wrapper_preflight = route.index('E3_A10_WRAPPER_DETERMINISTIC_PREFLIGHT_FAILED')
    deterministic = route.index('echo "E3_A10_DETERMINISTIC_PREFLIGHT=PASS"')
    consumed = route.index('echo "E3_A10_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS"')
    live = route.index("set +e", consumed)

    assert closure < candidate < dependency < postgres < route_verified
    assert route_verified < wrapper_preflight < deterministic < consumed < live
    assert route.count("E3_A10_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS") == 1


def test_a10_route_and_bootstrap_parse_cleanly() -> None:
    for path in (ROUTE, BOOTSTRAP):
        cp = subprocess.run(
            ["bash", "-n", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert cp.returncode == 0, cp.stderr


def test_a10_wrapper_and_closure_compile_cleanly() -> None:
    for path in (WRAPPER, CLOSURE):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")


def test_a10_windows_launcher_gets_frontend_bindings_from_manifest() -> None:
    launcher = LAUNCHER.read_text(encoding="utf-8")
    assert "$bindingManifest.provenance.a8_frontend_review_head" in launcher
    assert "$bindingManifest.provenance.a8_frontend_source_head" in launcher
    assert "$bindingManifest.provenance.a8_frontend_src_tree" in launcher
    assert "$bindingManifest.provenance.accepted_a7_dev_harness_blob" in launcher
    assert "E3_A10_FRONTEND_DETERMINISTIC_PREFLIGHT=PASS" in launcher
