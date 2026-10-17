import base64
import copy
import importlib.util
import json
import pathlib
import sys
import unittest
import uuid
from datetime import datetime, timezone

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
WORKLOAD_POLICY = json.loads(
    (ROOT / "architecture" / "lambda-ci-workload-policy.v1.json").read_text()
)
V2_NOW = datetime(2026, 10, 6, 20, 0, tzinfo=timezone.utc)
V2_CANDIDATE = "a" * 40


def good_request(profile="cpu-test"):
    return {
        "schema_version": 1,
        "request_id": str(uuid.uuid4()),
        "project_id": "research-engine",
        "profile": profile,
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


def test_gpu_small_launch_spec_carries_stable_uuid_and_bounded_runtime():
    req = mod.validate_request(good_request("gpu-small"), MANIFEST)
    launch = mod.build_launch_spec(req, MANIFEST, PROFILES, PINS)
    assert launch["profile"] == "gpu-small"
    assert launch["resources"]["gpu_indices"] == [0]
    assert launch["resources"]["gpu_uuid"] == "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"
    assert launch["resources"]["runtime_max_seconds"] == 1200
    assert launch["allow_production_services"] is False
    assert "trusted_failure_probe" not in launch
    runtime_binding = launch["runtime_binding"]
    assert runtime_binding["runtime_id"] == "qwen35-vllm-cu129-image-native-sampler-v3"
    assert runtime_binding["tree_digest_sha256"] == (
        "b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63"
    )


def test_gpu_small_systemd_command_binds_runtime_and_uses_job_local_state():
    req = mod.validate_request(good_request("gpu-small"), MANIFEST)
    launch = mod.build_launch_spec(req, MANIFEST, PROFILES, PINS)
    staging = pathlib.Path(
        "/srv/workspace-ci/research-engine/staging-cache/p5-test"
    )
    command = runtime.build_gpu_systemd_command(
        launch,
        pathlib.Path(
            "/srv/workspace-ci/research-engine/jobs/p5-test/runner"
        ),
        staging,
        "134.88.12.0/22",
        {
            "selected_device": "/dev/nvidia0",
            "target_uuid": "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            "denied_devices": ["/dev/nvidia1"],
            "support_devices": ["/dev/nvidia-uvm"],
        },
    )

    binding = launch["runtime_binding"]
    assert f"BindReadOnlyPaths={binding['canonical_path']}" in command
    assert f"Environment=P5_EXPANDED_RUNTIME={binding['canonical_path']}" in command
    assert f"Environment=P5_EXPANDED_RUNTIME_PYTHON={binding['python_path']}" in command
    assert (
        f"Environment=P5_EXPANDED_RUNTIME_TREE_SHA256="
        f"{binding['tree_digest_sha256']}"
    ) in command
    assert f"Environment=HOME={staging / 'home'}" in command
    assert f"Environment=XDG_CACHE_HOME={staging / 'xdg'}" in command
    assert "ReadWritePaths=/srv/workspace-ci/research-engine/home" not in command
    assert "Environment=PYTHONDONTWRITEBYTECODE=1" in command
    assert "Environment=VLLM_USE_FLASHINFER_SAMPLER=0" in command


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
        ("trusted_failure_probe", {"kind": "cuda_oom_acceptance_v1"}),
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



def enabled_v2_manifest():
    value = copy.deepcopy(MANIFEST)
    value["admission_v2"]["enabled"] = True
    return value


def good_v2_request(workload="cpu-test"):
    manifest = enabled_v2_manifest()
    route = manifest["admission_v2"]["routes"][workload]
    trusted = route["trusted_workflow"]
    command = trusted["job_display_claim"]["command"]
    return {
        "schema_version": 2,
        "request_id": str(uuid.uuid4()),
        "project_id": "research-engine",
        "workload_class": workload,
        "runner_name": "lambda-research-engine-v2test",
        "jit_config": base64.b64encode(b'{"opaque":"secret-v2"}').decode(),
        "attestation": {
            "schema_version": 2,
            "source": "github_scale_set_controller",
            "repository": "adamtrott78/research-engine",
            "scale_set_name": route["scale_set_name"],
            "job_message_type": "JobAssigned",
            "runner_request_id": 0,
            "workflow_run_id": 37422040174,
            "job_id": "777",
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


def test_v2_canonical_manifest_enables_root_derived_admission():
    req = mod.validate_request_v2(
        good_v2_request(),
        MANIFEST,
        WORKLOAD_POLICY,
        now=V2_NOW,
    )
    assert req.profile == "cpu-test"
    assert req.workload_class == "cpu-test"


def test_v2_cpu_request_derives_profile_and_admission_from_root_policy():
    request = good_v2_request("cpu-test")
    manifest = enabled_v2_manifest()
    req = mod.validate_request_v2(
        request,
        manifest,
        WORKLOAD_POLICY,
        now=V2_NOW,
        policy_sha256="1" * 64,
    )
    assert req.profile == "cpu-test"
    assert req.workload_class == "cpu-test"
    assert req.admission["candidate_sha"] == V2_CANDIDATE
    assert req.admission["policy"]["policy_sha256"] == "1" * 64
    assert req.request_digest_sha256 == req.admission["request_digest_sha256"]
    launch = mod.build_launch_spec(req, manifest, PROFILES, PINS)
    assert launch["schema_version"] == 2
    assert launch["workload_class"] == "cpu-test"
    assert launch["profile"] == "cpu-test"
    assert launch["admission"]["admission_id"] == req.admission["admission_id"]
    assert request["jit_config"] not in json.dumps(mod.redacted_spec(launch))


def test_v2_gpu_request_cannot_widen_beyond_gpu_small():
    request = good_v2_request("gpu-small")
    manifest = enabled_v2_manifest()
    req = mod.validate_request_v2(
        request,
        manifest,
        WORKLOAD_POLICY,
        now=V2_NOW,
    )
    launch = mod.build_launch_spec(req, manifest, PROFILES, PINS)
    assert launch["profile"] == "gpu-small"
    assert launch["resources"]["gpu_indices"] == [0]
    assert launch["resources"]["gpu_uuid"] == (
        "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"
    )
    assert req.admission["resource_ceiling"]["gpu_uuids"] == [
        "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"
    ]
    assert req.admission["runtime"]["runtime_id"] == (
        "qwen35-vllm-cu129-image-native-sampler-v3"
    )
    assert req.admission["runtime"]["cache_object"]["tree_sha256"] == (
        "b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63"
    )
    assert launch["runtime_binding"]["tree_digest_sha256"] == (
        req.admission["runtime"]["cache_object"]["tree_sha256"]
    )
    assert "trusted_failure_probe" not in launch
    assert req.admission["runtime"]["cache_object"]["object_state"] == "PROMOTED"
    assert req.admission["runtime"]["owning_contracts"]



def test_v2_model_eval_binds_exact_promoted_model_and_runtime():
    request = good_v2_request("model-eval-single-gpu")
    manifest = enabled_v2_manifest()
    req = mod.validate_request_v2(
        request,
        manifest,
        WORKLOAD_POLICY,
        now=V2_NOW,
    )
    assert req.profile == "gpu-small"
    assert req.workload_class == "model-eval-single-gpu"
    assert len(req.admission["models"]) == 1
    model = req.admission["models"][0]
    assert model["model_id"] == "qwen3.5-4b"
    assert model["repository"] == "Qwen/Qwen3.5-4B"
    assert model["revision"] == "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
    assert model["object_state"] == "PROMOTED"
    assert model["object_id"] == (
        "6e28e2560c07e7dabab92c55dbfb6941d5a7a75c8068bdc7a98115d8dc62072c"
    )
    assert model["serialization_risk_class"] == "SAFE"
    assert model["complete_offline"] is True
    assert req.admission["runtime"]["runtime_id"] == (
        "qwen35-vllm-cu129-image-native-sampler-v3"
    )

    launch = mod.build_launch_spec(req, manifest, PROFILES, PINS)
    binding = launch["model_binding"]
    assert binding["model_id"] == "qwen3.5-4b"
    assert binding["object_id"] == model["object_id"]
    assert launch["resources"]["gpu_indices"] == [0]
    assert launch["resources"]["gpu_uuid"] == (
        "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"
    )

    command = runtime.build_gpu_systemd_command(
        launch,
        pathlib.Path("/srv/workspace-ci/research-engine/jobs/p5-test/runner"),
        pathlib.Path("/srv/workspace-ci/research-engine/staging-cache/p5-test"),
        "134.88.12.0/22",
        {
            "selected_device": "/dev/nvidia0",
            "target_uuid": "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            "denied_devices": ["/dev/nvidia1"],
            "support_devices": ["/dev/nvidia-uvm"],
        },
    )
    assert f"Environment=P5_MODEL_ID={binding['model_id']}" in command
    assert f"Environment=P5_MODEL_REPOSITORY={binding['repository']}" in command
    assert f"Environment=P5_MODEL_REVISION={binding['revision']}" in command
    assert f"Environment=P5_MODEL_OBJECT_ID={binding['object_id']}" in command
    assert f"Environment=P5_MODEL_OBJECT_ROOT={binding['object_path']}" in command
    assert (
        f"Environment=P5_MODEL_PATH={binding['object_path']}/payload"
        in command
    )
    assert "Environment=HF_HUB_OFFLINE=1" in command
    assert "Environment=TRANSFORMERS_OFFLINE=1" in command
    assert f"ReadOnlyPaths={binding['object_path']}" in command
    assert "ProtectProc=invisible" in command
    assert "ProcSubset=all" in command
    assert "ProcSubset=pid" not in command


def test_v2_gpu_small_remains_model_forbidden():
    request = good_v2_request("gpu-small")
    manifest = enabled_v2_manifest()
    req = mod.validate_request_v2(
        request,
        manifest,
        WORKLOAD_POLICY,
        now=V2_NOW,
    )
    launch = mod.build_launch_spec(req, manifest, PROFILES, PINS)
    assert req.admission["models"] == []
    assert launch["model_binding"] is None

    command = runtime.build_gpu_systemd_command(
        launch,
        pathlib.Path("/srv/workspace-ci/research-engine/jobs/p5-test/runner"),
        pathlib.Path("/srv/workspace-ci/research-engine/staging-cache/p5-test"),
        "134.88.12.0/22",
        {
            "selected_device": "/dev/nvidia0",
            "target_uuid": "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            "denied_devices": ["/dev/nvidia1"],
            "support_devices": ["/dev/nvidia-uvm"],
        },
    )
    assert "ProtectProc=invisible" in command
    assert "ProcSubset=pid" in command
    assert "ProcSubset=all" not in command


def test_v2_model_binding_change_stales_admission():
    manifest = enabled_v2_manifest()
    req = mod.validate_request_v2(
        good_v2_request("model-eval-single-gpu"),
        manifest,
        WORKLOAD_POLICY,
        now=V2_NOW,
    )
    changed = copy.deepcopy(manifest)
    changed["promoted_model_bindings"]["qwen3.5-4b"]["descriptor_sha256"] = "f" * 64

    try:
        mod.admission_policy.validate_admission_freshness(
            req.admission,
            changed,
            WORKLOAD_POLICY,
            now=V2_NOW,
        )
    except mod.admission_policy.AdmissionError as exc:
        assert (
            "project/profile binding is stale" in str(exc)
            or "promoted model binding is stale" in str(exc)
        )
    else:
        raise AssertionError("model binding change did not stale admission")


def test_v2_runtime_binding_change_stales_admission():
    manifest = enabled_v2_manifest()
    req = mod.validate_request_v2(
        good_v2_request("gpu-small"),
        manifest,
        WORKLOAD_POLICY,
        now=V2_NOW,
    )
    changed = copy.deepcopy(manifest)
    changed["expanded_runtime_bindings"]["gpu-small"]["tree_digest_sha256"] = "f" * 64

    try:
        mod.admission_policy.validate_admission_freshness(
            req.admission,
            changed,
            WORKLOAD_POLICY,
            now=V2_NOW,
        )
    except mod.admission_policy.AdmissionError as exc:
        assert (
            "project/profile binding is stale" in str(exc)
            or "expanded runtime binding is stale" in str(exc)
        )
    else:
        raise AssertionError("runtime binding change did not stale admission")


def test_v2_rejects_profile_or_command_injection_fields():
    request = good_v2_request()
    request["profile"] = "gpu-heavy"
    try:
        mod.validate_request_v2(
            request,
            enabled_v2_manifest(),
            WORKLOAD_POLICY,
            now=V2_NOW,
        )
    except mod.PolicyError as exc:
        assert "keys mismatch" in str(exc)
    else:
        raise AssertionError("v2 accepted controller-supplied profile authority")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite
