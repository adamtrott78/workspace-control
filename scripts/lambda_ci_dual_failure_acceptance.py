#!/usr/bin/env python3
"""Root-authored host acceptance for dormant dual-GPU timeout and CUDA-OOM gates."""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys
import uuid


EXPECTED_UUIDS = [
    "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
    "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
]
EXPECTED_DEVICES = ["/dev/nvidia1", "/dev/nvidia0"]
EXPECTED_RUNTIME_DIGEST = (
    "b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63"
)
EXPECTED_MODEL_OBJECT = (
    "6e28e2560c07e7dabab92c55dbfb6941d5a7a75c8068bdc7a98115d8dc62072c"
)
TIMEOUT_PROBE_BLOB = "3d420d39924b4cd932b70c7303a80eaf8c098c36"
OOM_PROBE_BLOB = "8330b3621f80dbe78e413234deec4b4f433e2ce7"

MANIFEST = pathlib.Path("/etc/workspace-ci/projects/research-engine.json")
PROFILES = pathlib.Path("/etc/workspace-ci/lambda-ci-systemd-profiles.v1.json")
PINS = pathlib.Path("/etc/workspace-ci/lambda-ci-upstream-pins.v1.json")
INSTALLED_MODULES = pathlib.Path("/opt/workspace-ci/provisioner")


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def receipt_path(spec, request_id: str) -> pathlib.Path:
    return pathlib.Path(spec["paths"]["logs"]) / f"p5-{request_id}-receipt.json"


def assert_common(receipt: dict) -> None:
    assert receipt["decision"] == "FAIL"
    assert receipt["automatic_retry_eligible"] is False
    assert receipt["profile"] == "gpu-heavy"
    assert receipt["gpu_target_uuids"] == EXPECTED_UUIDS
    assert receipt["gpu_selected_devices"] == EXPECTED_DEVICES
    assert receipt["cuda_visible_devices"] == ",".join(EXPECTED_UUIDS)
    assert receipt["gpu_prelaunch_idle_verified"] is True
    assert receipt["gpu_prelaunch_processes"] == []
    assert receipt["project_uid_process_cleanup"] is True
    assert receipt["project_uid_gpu_process_cleanup"] is True
    assert receipt["leaked_gpu_processes"] == []
    assert receipt["runner_workspace_destroyed"] is True
    assert receipt["staging_workspace_destroyed"] is True
    assert receipt["expanded_runtime_preverified"] is True
    assert receipt["expanded_runtime_postverified"] is True
    assert receipt["promoted_model_preverified"] is True
    assert receipt["promoted_model_postverified"] is True
    assert receipt["jit_config_persisted"] is False
    assert receipt["github_credential_present"] is False
    assert receipt["expanded_runtime"]["tree_digest_sha256"] == EXPECTED_RUNTIME_DIGEST
    assert receipt["expanded_runtime_post"]["tree_digest_sha256"] == EXPECTED_RUNTIME_DIGEST
    assert receipt["promoted_model"]["object_id"] == EXPECTED_MODEL_OBJECT
    assert receipt["promoted_model_post"]["object_id"] == EXPECTED_MODEL_OBJECT


def assert_timeout_receipt(receipt: dict) -> None:
    assert_common(receipt)
    assert receipt["terminal_status"] == "TIMED_OUT"
    assert receipt["timed_out"] is True
    assert receipt["wrapper_timeout_cleanup"] is True
    assert receipt["resource_exhausted"] is False
    assert receipt["disk_pressure"] is False
    assert receipt["cuda_oom"] is False
    terminal = receipt["systemd_terminal_evidence"]
    assert terminal["available"] is True
    assert terminal["result"] == "timeout"


def assert_oom_receipt(receipt: dict) -> None:
    assert_common(receipt)
    assert receipt["terminal_status"] == "CUDA_OOM"
    assert receipt["timed_out"] is False
    assert receipt["resource_exhausted"] is False
    assert receipt["disk_pressure"] is False
    assert receipt["cuda_oom"] is True
    terminal = receipt["systemd_terminal_evidence"]
    assert terminal["available"] is True
    assert terminal["result"] == "exit-code"
    assert str(terminal["exec_main_code"]) == "1"
    assert str(terminal["exec_main_status"]) == "86"
    evidence = receipt["cuda_oom_evidence"]
    assert evidence["available"] is True
    assert evidence["matched"] is True
    assert evidence["kind"] == "dual_gpu_cuda_oom_acceptance_v1"
    assert evidence["source_blob_sha"] == OOM_PROBE_BLOB
    assert evidence["expected_exit_code"] == 86
    assert evidence["systemd_result"] == "exit-code"
    assert str(evidence["systemd_exec_main_code"]) == "1"
    assert str(evidence["systemd_exec_main_status"]) == "86"


def make_request(provisioner, manifest: dict, suffix: str):
    return provisioner.ValidatedRequest(
        request_id=str(uuid.uuid4()),
        project_id=manifest["project_id"],
        profile="gpu-heavy",
        runner_name=f"lambda-research-engine-root-{suffix}",
        jit_config=base64.b64encode(b"root-synthetic-dual-acceptance").decode(),
        workload_class="model-eval-dual-gpu",
        admission=None,
        request_digest_sha256=None,
    )


def make_spec(provisioner, runtime, manifest, profiles, pins, request, kind: str):
    spec = provisioner.build_launch_spec(request, manifest, profiles, pins)
    spec["model_binding"] = manifest["promoted_model_bindings"]["qwen3.5-4b"]

    if kind == "timeout":
        spec["resources"]["runtime_max_seconds"] = 5
        spec["trusted_failure_probe"] = {
            "kind": runtime.TRUSTED_DUAL_TIMEOUT_PROBE_KIND,
            "authority": runtime.TRUSTED_FAILURE_PROBE_AUTHORITY,
            "path": str(runtime.TRUSTED_DUAL_TIMEOUT_PROBE_PATH),
            "source_blob_sha": TIMEOUT_PROBE_BLOB,
            "expected_exit_code": runtime.TRUSTED_DUAL_TIMEOUT_PROBE_EXIT,
        }
    else:
        # Bound a hung synthetic OOM probe without changing the accepted GPU
        # resource envelope. A timeout here is a hard acceptance failure.
        spec["resources"]["runtime_max_seconds"] = 120
        spec["trusted_failure_probe"] = {
            "kind": runtime.TRUSTED_DUAL_CUDA_OOM_PROBE_KIND,
            "authority": runtime.TRUSTED_FAILURE_PROBE_AUTHORITY,
            "path": str(runtime.TRUSTED_DUAL_CUDA_OOM_PROBE_PATH),
            "source_blob_sha": OOM_PROBE_BLOB,
            "expected_exit_code": runtime.TRUSTED_DUAL_CUDA_OOM_PROBE_EXIT,
        }

    assert spec["resources"]["gpu_uuids"] == EXPECTED_UUIDS
    assert spec["resources"]["gpu_indices"] == [0, 1]
    assert spec["resources"].get("gpu_uuid") in (None, "")
    assert spec["runtime_binding"]["tree_digest_sha256"] == EXPECTED_RUNTIME_DIGEST
    assert spec["model_binding"]["object_id"] == EXPECTED_MODEL_OBJECT
    assert spec["admission"] is None
    return spec


def run_gate(provisioner, runtime, manifest, profiles, pins, kind: str):
    suffix = "dual-timeout" if kind == "timeout" else "dual-oom"
    request = make_request(provisioner, manifest, suffix)
    spec = make_spec(provisioner, runtime, manifest, profiles, pins, request, kind)

    expected_error = (
        runtime.RuntimeTimeoutError
        if kind == "timeout"
        else runtime.RuntimeCudaOomError
    )

    caught = None
    try:
        runtime.launch_runner(request, spec)
    except expected_error as exc:
        caught = exc

    if caught is None:
        raise AssertionError(f"{kind} gate did not raise {expected_error.__name__}")

    path = receipt_path(spec, request.request_id)
    if not path.is_file():
        raise AssertionError(f"{kind} receipt missing: {path}")
    receipt = load(path)

    if kind == "timeout":
        assert_timeout_receipt(receipt)
    else:
        assert_oom_receipt(receipt)

    return path, receipt, type(caught).__name__


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--installed-modules",
        type=pathlib.Path,
        default=INSTALLED_MODULES,
    )
    args = parser.parse_args()

    sys.path.insert(0, str(args.installed_modules))
    import lambda_ci_provisioner as provisioner
    import lambda_ci_runtime as runtime

    manifest = load(MANIFEST)
    profiles = load(PROFILES)
    pins = load(PINS)

    live = manifest["admission_v2"]["live_enabled_workload_classes"]
    assert "model-eval-dual-gpu" not in live
    assert "gpu-heavy" not in live
    route = manifest["admission_v2"]["routes"]["model-eval-dual-gpu"]
    assert route["admission_enabled_after_enforcement"] is False

    timeout_path, timeout_receipt, timeout_error = run_gate(
        provisioner, runtime, manifest, profiles, pins, "timeout"
    )
    print(f"TIMEOUT_EXPECTED_ERROR={timeout_error}")
    print(f"TIMEOUT_RECEIPT={timeout_path}")
    print(
        "TIMEOUT_SYSTEMD_RESULT="
        + str(timeout_receipt["systemd_terminal_evidence"]["result"])
    )
    print("DUAL_TIMEOUT_ACCEPTANCE=PASS")

    oom_path, oom_receipt, oom_error = run_gate(
        provisioner, runtime, manifest, profiles, pins, "oom"
    )
    print(f"OOM_EXPECTED_ERROR={oom_error}")
    print(f"OOM_RECEIPT={oom_path}")
    print(
        "OOM_SYSTEMD_RESULT="
        + str(oom_receipt["systemd_terminal_evidence"]["result"])
    )
    print(
        "OOM_EXEC_MAIN_STATUS="
        + str(oom_receipt["systemd_terminal_evidence"]["exec_main_status"])
    )
    print("DUAL_CUDA_OOM_ACCEPTANCE=PASS")

    print("DUAL_FAILURE_HOST_ACCEPTANCE=PASS")
    print("DUAL_ADMISSION_LIVE=false")
    print("GENERIC_GPU_HEAVY_LIVE=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
