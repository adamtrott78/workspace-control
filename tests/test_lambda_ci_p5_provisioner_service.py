import base64
import importlib.util
import json
import pathlib
import sys
import tempfile
import threading
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]

for name in ("lambda_ci_provisioner", "lambda_ci_runtime", "lambda_ci_provisioner_service"):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

policy = sys.modules["lambda_ci_provisioner"]
service_mod = sys.modules["lambda_ci_provisioner_service"]

MANIFEST = json.loads(
    (ROOT / "architecture" / "lambda-ci-project-research-engine.v1.json").read_text()
)
PROFILES = json.loads(
    (ROOT / "architecture" / "lambda-ci-systemd-profiles.v1.json").read_text()
)
PINS = json.loads(
    (ROOT / "architecture" / "lambda-ci-upstream-pins.v1.json").read_text()
)


def request(profile="cpu-test"):
    return {
        "schema_version": 1,
        "request_id": str(uuid.uuid4()),
        "project_id": "research-engine",
        "profile": profile,
        "runner_name": "lambda-research-engine-p5test",
        "jit_config": base64.b64encode(b'{"opaque":"secret"}').decode(),
    }


def build_service(tmp, launcher, controller_uid=12345):
    return service_mod.ProvisionerService(
        manifest=MANIFEST,
        profiles=PROFILES,
        pins=PINS,
        state_store=service_mod.StateStore(pathlib.Path(tmp)),
        controller_uid=controller_uid,
        launcher=launcher,
    )


def wait_for(predicate, timeout=2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition not reached")


def test_accepted_request_is_launched_once_and_jit_not_persisted():
    calls = []
    done = threading.Event()

    def launcher(req, spec):
        calls.append((req, spec))
        done.set()
        return {"decision": "RUNNER_EXITED_CLEANLY"}

    with tempfile.TemporaryDirectory() as tmp:
        svc = build_service(tmp, launcher)
        req = request()
        response = svc.handle_request(req, peer_uid=12345)
        assert response["status"] == "ACCEPTED"
        assert done.wait(1)

        wait_for(lambda: len(list(pathlib.Path(tmp).glob("*.json"))) == 1)
        state_text = next(pathlib.Path(tmp).glob("*.json")).read_text()
        assert req["jit_config"] not in state_text

        duplicate = svc.handle_request(req, peer_uid=12345)
        assert duplicate["status"] == "DUPLICATE"
        assert len(calls) == 1


def test_wrong_peer_uid_is_rejected_before_launch():
    calls = []

    def launcher(req, spec):
        calls.append(req)
        return {}

    with tempfile.TemporaryDirectory() as tmp:
        svc = build_service(tmp, launcher)
        try:
            svc.handle_request(request(), peer_uid=999)
        except service_mod.ServiceError:
            pass
        else:
            raise AssertionError("unauthorized peer UID accepted")
        assert calls == []


def test_gpu_small_is_accepted_but_gpu_heavy_is_rejected():
    calls = []
    done = threading.Event()

    def launcher(req, spec):
        calls.append((req.profile, spec["profile"], spec["resources"].get("gpu_uuid")))
        done.set()
        return {"decision": "RUNNER_EXITED_CLEANLY"}

    with tempfile.TemporaryDirectory() as tmp:
        svc = build_service(tmp, launcher)
        accepted = svc.handle_request(request("gpu-small"), peer_uid=12345)
        assert accepted["status"] == "ACCEPTED"
        assert done.wait(1)
        assert calls == [
            (
                "gpu-small",
                "gpu-small",
                "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            )
        ]

    with tempfile.TemporaryDirectory() as tmp:
        svc = build_service(tmp, lambda req, spec: {})
        try:
            svc.handle_request(request("gpu-heavy"), peer_uid=12345)
        except service_mod.ServiceError:
            return
    raise AssertionError("gpu-heavy was enabled without explicit authorization")


def test_busy_request_is_not_claimed_and_can_be_retried():
    entered = threading.Event()
    release = threading.Event()

    def launcher(req, spec):
        entered.set()
        release.wait(1)
        return {"decision": "RUNNER_EXITED_CLEANLY"}

    with tempfile.TemporaryDirectory() as tmp:
        svc = build_service(tmp, launcher)
        first = request()
        second = request()
        assert svc.handle_request(first, peer_uid=12345)["status"] == "ACCEPTED"
        assert entered.wait(1)

        busy = svc.handle_request(second, peer_uid=12345)
        assert busy["status"] == "BUSY"
        assert not svc.state_store.path(second["request_id"]).exists()

        release.set()
        wait_for(lambda: not svc._active)


def test_runtime_module_contains_no_github_credential_or_api_client():
    source = (ROOT / "scripts" / "lambda_ci_runtime.py").read_text()
    for forbidden in (
        "Authorization: Bearer",
        "api.github.com",
        "getpass",
        "GITHUB_TOKEN",
        "GH_TOKEN",
    ):
        assert forbidden not in source


def test_transport_authenticates_peer_and_never_accepts_policy_fields():
    source = (ROOT / "scripts" / "lambda_ci_provisioner_service.py").read_text()
    assert "SO_PEERCRED" in source
    assert "workspace-ci-controller" in source
    for forbidden in (
        '"command"',
        '"environment"',
        '"device"',
        '"systemd_properties"',
    ):
        assert forbidden not in service_mod.policy._ALLOWED_REQUEST_KEYS
