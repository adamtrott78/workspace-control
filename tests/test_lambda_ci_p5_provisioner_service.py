import base64
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

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
WORKLOAD_POLICY = json.loads(
    (ROOT / "architecture" / "lambda-ci-workload-policy.v1.json").read_text()
)
V2_NOW = datetime(2026, 10, 6, 20, 0, tzinfo=timezone.utc)
V2_CANDIDATE = "a" * 40


def request(profile="cpu-test"):
    return {
        "schema_version": 1,
        "request_id": str(uuid.uuid4()),
        "project_id": "research-engine",
        "profile": profile,
        "runner_name": "lambda-research-engine-p5test",
        "jit_config": base64.b64encode(b'{"opaque":"secret"}').decode(),
    }


def build_service(
    tmp,
    launcher,
    controller_uid=12345,
    manifest=MANIFEST,
    workload_policy=WORKLOAD_POLICY,
    clock=None,
):
    return service_mod.ProvisionerService(
        manifest=manifest,
        profiles=PROFILES,
        pins=PINS,
        workload_policy=workload_policy,
        state_store=service_mod.StateStore(pathlib.Path(tmp)),
        controller_uid=controller_uid,
        launcher=launcher,
        clock=clock,
    )



def enabled_v2_manifest():
    value = copy.deepcopy(MANIFEST)
    value["admission_v2"]["enabled"] = True
    return value


def v2_request(workload="cpu-test"):
    manifest = enabled_v2_manifest()
    route = manifest["admission_v2"]["routes"][workload]
    trusted = route["trusted_workflow"]
    command = trusted["job_display_claim"]["command"]
    return {
        "schema_version": 2,
        "request_id": str(uuid.uuid4()),
        "project_id": "research-engine",
        "workload_class": workload,
        "runner_name": "lambda-research-engine-v2service",
        "jit_config": base64.b64encode(b'{"opaque":"v2-secret"}').decode(),
        "attestation": {
            "schema_version": 1,
            "source": "github_scale_set_controller",
            "repository": "adamtrott78/research-engine",
            "scale_set_name": route["scale_set_name"],
            "runner_request_id": 12345,
            "workflow_run_id": 37422040174,
            "job_id": "job-v2-service",
            "job_workflow_ref": trusted["job_workflow_ref"],
            "workflow_path": trusted["path"],
            "workflow_default_branch_commit_sha": "b" * 40,
            "workflow_blob_sha": trusted["blob_sha"],
            "event_name": trusted["event_name"],
            "job_display_name": (
                f"wc-admission-v1|workload={workload}|pr=101"
                f"|request={command} {V2_CANDIDATE}"
            ),
            "actor_login": "adamtrott78",
            "triggering_actor_login": "adamtrott78",
            "pr_number": 101,
            "pr_state": "open",
            "pr_head_repository": "adamtrott78/research-engine",
            "candidate_sha": V2_CANDIDATE,
            "candidate_verification": "PR_HEAD_MATCH",
            "verified_at": V2_NOW.isoformat().replace("+00:00", "Z"),
        },
    }


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


def test_v2_identical_replay_returns_original_admission_without_reexecution():
    calls = []
    done = threading.Event()

    def launcher(req, spec):
        calls.append((req, spec))
        done.set()
        return {
            "decision": "RUNNER_EXITED_CLEANLY",
            "admission_identity": service_mod.runtime.admission_receipt_identity(spec).get(
                "admission_identity"
            ),
        }

    with tempfile.TemporaryDirectory() as tmp:
        req = v2_request()
        svc = build_service(
            tmp,
            launcher,
            manifest=enabled_v2_manifest(),
            clock=lambda: V2_NOW,
        )
        accepted = svc.handle_request(req, peer_uid=12345)
        assert accepted["status"] == "ACCEPTED"
        admission_id = accepted["admission_identity"]["admission_id"]
        assert accepted["admission_identity"]["candidate_sha"] == V2_CANDIDATE
        assert accepted["admission_identity"]["consumed_at"] is not None
        assert done.wait(1)
        wait_for(
            lambda: json.loads(svc.state_store.path(req["request_id"]).read_text())[
                "status"
            ]
            == "COMPLETED"
        )

        duplicate = svc.handle_request(req, peer_uid=12345)
        assert duplicate["status"] == "DUPLICATE"
        assert duplicate["admission_id"] == admission_id
        assert duplicate["receipt_status"] == "COMPLETED"
        assert len(calls) == 1

        # A consumed terminal request returns its durable receipt identity even
        # after the original attestation/admission TTL has elapsed.
        svc.clock = lambda: V2_NOW + timedelta(seconds=2000)
        late_duplicate = svc.handle_request(req, peer_uid=12345)
        assert late_duplicate["status"] == "DUPLICATE"
        assert late_duplicate["admission_id"] == admission_id
        assert len(calls) == 1

        state_text = svc.state_store.path(req["request_id"]).read_text()
        assert req["jit_config"] not in state_text
        state = json.loads(state_text)
        assert state["request_digest_sha256"] == accepted["request_digest_sha256"]
        assert state["admission_identity"]["admission_id"] == admission_id
        assert state["result"]["admission_identity"]["admission_id"] == admission_id


def test_v2_same_request_id_different_digest_is_replay_conflict():
    done = threading.Event()

    def launcher(req, spec):
        done.set()
        return {"decision": "RUNNER_EXITED_CLEANLY"}

    with tempfile.TemporaryDirectory() as tmp:
        req = v2_request()
        svc = build_service(
            tmp,
            launcher,
            manifest=enabled_v2_manifest(),
            clock=lambda: V2_NOW,
        )
        assert svc.handle_request(req, peer_uid=12345)["status"] == "ACCEPTED"
        assert done.wait(1)
        wait_for(lambda: not svc._active)

        # Regenerated JIT for the same trusted job is recovery-stable.
        retry = copy.deepcopy(req)
        retry["jit_config"] = base64.b64encode(b'{"opaque":"regenerated"}').decode()
        duplicate = svc.handle_request(retry, peer_uid=12345)
        assert duplicate["status"] == "DUPLICATE"

        # Changing an authoritative candidate claim under the same request ID
        # is a real replay conflict.
        conflict = copy.deepcopy(req)
        conflict_sha = "c" * 40
        conflict["attestation"]["candidate_sha"] = conflict_sha
        conflict["attestation"]["job_display_name"] = (
            "wc-admission-v1|workload=cpu-test|pr=101"
            f"|request=/lambda-ci-p5 {conflict_sha}"
        )
        rejected = svc.handle_request(conflict, peer_uid=12345)
        assert rejected["status"] == "REJECTED"
        assert rejected["error_type"] == "ReplayConflict"


def test_v2_disabled_manifest_rejects_before_state_claim():
    with tempfile.TemporaryDirectory() as tmp:
        disabled = copy.deepcopy(MANIFEST)
        disabled["admission_v2"]["enabled"] = False
        svc = build_service(
            tmp,
            lambda req, spec: {},
            manifest=disabled,
            clock=lambda: V2_NOW,
        )
        req = v2_request()
        try:
            svc.handle_request(req, peer_uid=12345)
        except policy.PolicyError as exc:
            assert "not enabled" in str(exc)
        else:
            raise AssertionError("disabled v2 request unexpectedly accepted")
        assert not svc.state_store.path(req["request_id"]).exists()


def test_v2_busy_request_is_not_consumed_or_claimed():
    entered = threading.Event()
    release = threading.Event()

    def launcher(req, spec):
        entered.set()
        release.wait(1)
        return {"decision": "RUNNER_EXITED_CLEANLY"}

    with tempfile.TemporaryDirectory() as tmp:
        svc = build_service(
            tmp,
            launcher,
            manifest=enabled_v2_manifest(),
            clock=lambda: V2_NOW,
        )
        first = v2_request()
        second = v2_request()
        assert svc.handle_request(first, peer_uid=12345)["status"] == "ACCEPTED"
        assert entered.wait(1)
        busy = svc.handle_request(second, peer_uid=12345)
        assert busy["status"] == "BUSY"
        assert not svc.state_store.path(second["request_id"]).exists()
        release.set()
        wait_for(lambda: not svc._active)

def test_v2_status_query_reports_missing_and_existing_without_execution_material():
    with tempfile.TemporaryDirectory() as tmp:
        entered = threading.Event()
        release = threading.Event()

        def launcher(req, spec):
            entered.set()
            release.wait(1)
            return {"decision": "RUNNER_EXITED_CLEANLY"}

        svc = build_service(
            tmp,
            launcher,
            manifest=enabled_v2_manifest(),
            clock=lambda: V2_NOW,
        )
        request_id = str(uuid.uuid4())
        missing = svc.handle_request(
            {
                "schema_version": 2,
                "operation": "STATUS",
                "request_id": request_id,
            },
            peer_uid=12345,
        )
        assert missing == {
            "schema_version": 2,
            "status": "MISSING",
            "request_id": request_id,
        }

        req = v2_request()
        # Keep this test aligned with the current controller attestation schema.
        req["attestation"]["schema_version"] = 2
        req["attestation"]["job_message_type"] = "JobAssigned"
        req["attestation"]["runner_request_id"] = 0
        req["attestation"]["job_id"] = "777"
        accepted = svc.handle_request(req, peer_uid=12345)
        assert accepted["status"] == "ACCEPTED"
        assert entered.wait(1)

        status = svc.handle_request(
            {
                "schema_version": 2,
                "operation": "STATUS",
                "request_id": req["request_id"],
            },
            peer_uid=12345,
        )
        assert status["status"] == "ACCEPTED"
        assert status["request_id"] == req["request_id"]
        assert status["runner_name"] == req["runner_name"]
        assert "admission_id" in status
        assert "jit_config" not in status
        assert "attestation" not in status

        release.set()
        wait_for(lambda: not svc._active)
