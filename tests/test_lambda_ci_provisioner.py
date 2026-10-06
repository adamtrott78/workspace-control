import base64
import importlib.util
import json
import pathlib
import sys
import unittest
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "lambda_ci_provisioner.py"
RUNTIME_MODULE_PATH = ROOT / "scripts" / "lambda_ci_runtime.py"

spec = importlib.util.spec_from_file_location("lambda_ci_provisioner", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

runtime_spec = importlib.util.spec_from_file_location("lambda_ci_runtime", RUNTIME_MODULE_PATH)
runtime = importlib.util.module_from_spec(runtime_spec)
sys.modules[runtime_spec.name] = runtime
runtime_spec.loader.exec_module(runtime)

MANIFEST = json.loads(
    (ROOT / "architecture" / "lambda-ci-project-research-engine.v1.json").read_text()
)
PROFILES = json.loads(
    (ROOT / "architecture" / "lambda-ci-systemd-profiles.v1.json").read_text()
)
PINS = json.loads(
    (ROOT / "architecture" / "lambda-ci-upstream-pins.v1.json").read_text()
)


def good_request():
    return {
        "schema_version": 1,
        "request_id": str(uuid.uuid4()),
        "project_id": "research-engine",
        "profile": "cpu-test",
        "runner_name": "lambda-research-engine-test1",
        "jit_config": base64.b64encode(b'{"opaque":"secret"}').decode(),
    }


def test_valid_request_builds_only_fixed_runner_command():
    req = mod.validate_request(good_request(), MANIFEST)
    launch = mod.build_launch_spec(req, MANIFEST, PROFILES, PINS)
    assert launch["runner"]["fixed_command"] == ["./run.sh"]
    assert launch["run_as"]["user"] == "ci-research-engine"
    assert launch["project_id"] == "research-engine"
    assert launch["paths"]["home"] == "/srv/workspace-ci/research-engine/home"
    assert launch["allow_production_services"] is False


def test_extra_command_key_is_rejected():
    req = good_request()
    req["command"] = ["bash", "-lc", "id"]
    try:
        mod.validate_request(req, MANIFEST)
    except mod.PolicyError:
        return
    raise AssertionError("arbitrary command key was accepted")


def test_extra_path_or_environment_keys_are_rejected():
    for key, value in (
        ("path", "/home/atrott"),
        ("environment", {"LD_PRELOAD": "/tmp/x.so"}),
        ("device", "/dev/nvidia1"),
        ("systemd_properties", {"BindReadOnlyPaths": "/home/atrott"}),
    ):
        req = good_request()
        req[key] = value
        try:
            mod.validate_request(req, MANIFEST)
        except mod.PolicyError:
            continue
        raise AssertionError(f"untrusted key accepted: {key}")


def test_unapproved_project_and_profile_are_rejected():
    for key, value in (
        ("project_id", "PADataset"),
        ("profile", "production-acceptance"),
    ):
        req = good_request()
        req[key] = value
        try:
            mod.validate_request(req, MANIFEST)
        except mod.PolicyError:
            continue
        raise AssertionError(f"unauthorized {key} accepted")


def test_invalid_runner_name_and_jit_are_rejected():
    req = good_request()
    req["runner_name"] = "../../root"
    try:
        mod.validate_request(req, MANIFEST)
    except mod.PolicyError:
        pass
    else:
        raise AssertionError("path-like runner name accepted")

    req = good_request()
    req["jit_config"] = "not base64!!"
    try:
        mod.validate_request(req, MANIFEST)
    except mod.PolicyError:
        return
    raise AssertionError("invalid JIT config accepted")


def test_redacted_spec_never_contains_secret():
    req_data = good_request()
    secret = req_data["jit_config"]
    req = mod.validate_request(req_data, MANIFEST)
    launch = mod.build_launch_spec(req, MANIFEST, PROFILES, PINS)
    redacted = mod.redacted_spec(launch)
    assert secret not in json.dumps(redacted)
    assert redacted["runner"]["jit_config_env_value"] == "<REDACTED>"


def test_runner_release_is_checksum_pinned():
    runner = PINS["actions_runner"]
    assert runner["version"] == "2.337.0"
    assert runner["linux_x64_sha256"] == (
        "70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613"
    )


def test_scaleset_client_is_commit_pinned():
    assert PINS["actions_scaleset"]["commit_sha"] == (
        "e6daac702355cdb5b880b4fbdcf6d85dcd9e48e5"
    )


def test_go_toolchain_is_checksum_pinned_and_isolated():
    go = PINS["go_toolchain"]
    assert go["version"] == "1.26.3"
    assert go["source_sha256"] == (
        "2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556"
    )
    assert go["install_prefix"] == "/opt/workspace-ci/go/1.26.3"
    assert go["architecture"] == "linux-amd64"


def test_launch_spec_satisfies_runtime_path_contract():
    req = mod.validate_request(good_request(), MANIFEST)
    launch = mod.build_launch_spec(req, MANIFEST, PROFILES, PINS)
    command = runtime.build_cpu_systemd_command(
        launch,
        pathlib.Path("/srv/workspace-ci/research-engine/jobs/p5-test/runner"),
        pathlib.Path("/srv/workspace-ci/research-engine/staging-cache/p5-test"),
        "134.88.12.0/22",
    )
    assert launch["paths"]["home"] == "/srv/workspace-ci/research-engine/home"
    assert "Environment=HOME=/srv/workspace-ci/research-engine/home" in command
    assert "ReadWritePaths=/srv/workspace-ci/research-engine/home" in command


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite
