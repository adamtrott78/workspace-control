import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PINS = json.loads((ROOT / "architecture/lambda-ci-upstream-pins.v1.json").read_text())
PROJECT = json.loads((ROOT / "architecture/lambda-ci-project-research-engine.v1.json").read_text())
PROFILES = json.loads((ROOT / "architecture/lambda-ci-systemd-profiles.v1.json").read_text())
PROTOCOL = (ROOT / "architecture/lambda-ci-provisioner-protocol.v1.md").read_text()
CONTROLLER = (ROOT / "architecture/lambda-ci-controller-adapter.v1.md").read_text()
CACHE = (ROOT / "architecture/lambda-ci-trusted-cache-policy.v1.md").read_text()
UNIT = (ROOT / "templates/lambda-ci/workspace-ci-runner@.service.in").read_text()
KILL = (ROOT / "scripts/lambda_ci_kill_switch.sh").read_text()


def test_upstream_dependencies_are_exactly_pinned():
    assert PINS["actions_scaleset"]["commit_sha"] == "e6daac702355cdb5b880b4fbdcf6d85dcd9e48e5"
    assert PINS["actions_runner"]["version"] == "2.337.0"
    assert PINS["actions_runner"]["linux_x64_sha256"] == (
        "70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613"
    )
    assert "@latest" not in json.dumps(PINS)


def test_research_engine_is_the_only_v1_project_and_no_prod_profile():
    assert PROJECT["project_id"] == "research-engine"
    assert PROJECT["concurrency"] == 1
    assert "production-acceptance" not in PROJECT["profiles"]
    assert PROJECT["production_acceptance_profile"] == "not_authorized_in_v1_pilot"


def test_project_identity_has_no_atrott_or_docker_authority():
    assert PROJECT["runner_user"] == "ci-research-engine"
    assert "/home/atrott" in PROJECT["forbidden_paths"]
    assert "/var/run/docker.sock" in PROJECT["forbidden_paths"]
    assert "docker" not in PROJECT["runner_group"].lower()


def test_profiles_deny_production_services():
    for profile in PROJECT["profiles"].values():
        assert profile["allow_production_services"] is False


def test_systemd_template_has_core_sandbox_and_no_docker():
    for required in (
        "NoNewPrivileges=yes",
        "CapabilityBoundingSet=",
        "ProtectSystem=strict",
        "ProtectHome=yes",
        "ProtectControlGroups=yes",
        "ProtectProc=invisible",
        "DevicePolicy=closed",
        "KillMode=control-group",
        "InaccessiblePaths=/var/run/docker.sock",
    ):
        assert required in UNIT


def test_jit_secret_is_environment_only_and_protocol_rejects_arbitrary_shell():
    assert "ACTIONS_RUNNER_INPUT_JITCONFIG" in UNIT
    assert "never appear in command-line arguments" in PROTOCOL
    assert "execute a command supplied by the controller" in PROTOCOL
    assert "accept a path supplied by the controller" in PROTOCOL


def test_controller_is_unprivileged_and_provisioner_has_no_github_credential():
    assert "unprivileged" in CONTROLLER
    assert "root provisioner" in CONTROLLER.lower()
    assert "no GitHub credential" in PROTOCOL


def test_persistent_cache_is_not_candidate_writable():
    assert "Candidate jobs may write only staging" in CACHE
    assert "Trusted cache is read-only to the runner" in CACHE
    assert "Candidate workflow code cannot invoke promotion directly" in CACHE


def test_kill_switch_targets_workspace_ci_units_only():
    assert "workspace-ci-*.service" in KILL
    assert "research-engine-daemon" not in KILL
    assert "postgresql" not in KILL
    assert "docker" not in KILL.lower()


def test_gpu_policy_requires_real_device_boundary_before_activation():
    unresolved = PROFILES["unresolved_before_activation"]
    assert any("DevicePolicy=closed" in item for item in unresolved)
