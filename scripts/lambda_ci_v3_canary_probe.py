#!/usr/bin/env python3
"""Bounded non-secret verifier for Lambda CI v3 migration-only canaries.

The probe grants no authority. It reads the installed root projection and the
already-applied runner sandbox, derives the actual class from RUNNER_NAME, and
fails closed when the observed envelope differs. It performs no network access.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
from typing import Any

ROOT_POLICY = pathlib.Path("/etc/workspace-ci/v3/root-policy.json")
PUBLIC_NETWORK = "GITHUB_CONTROL_PLANE_PLUS_PUBLIC_PAYLOAD"
OFFLINE_NETWORK = "GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE"
OFFLINE_RUNNER_CPU_PERCENT = 200
OFFLINE_RUNNER_MEMORY_BYTES = 4 * 1024**3
OFFLINE_RUNNER_TASKS_MAX = 1024
OFFLINE_CLIENT_PATH = "/opt/workspace-ci/v3/payload/lambda_ci_v3_payload_exec.py"
BASE_DENIES = (
    "127.0.0.0/8",
    "::1/128",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "100.64.0.0/10",
    "169.254.0.0/16",
    "fe80::/10",
    "fc00::/7",
)


class CanaryError(RuntimeError):
    pass


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CanaryError(f"{path}: expected JSON object")
    return value


def _memory_bytes(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        if value <= 0:
            raise CanaryError("memory value must be positive")
        return value
    match = re.fullmatch(r"([1-9][0-9]*)([KMG])", str(value))
    if match is None:
        raise CanaryError(f"unsupported memory value {value!r}")
    return int(match.group(1)) * {"K":1024,"M":1024**2,"G":1024**3}[match.group(2)]


def _runtime_seconds(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        if value <= 0:
            raise CanaryError("runtime value must be positive")
        return value
    match = re.fullmatch(r"([1-9][0-9]*)(s|min|h)", str(value))
    if match is None:
        raise CanaryError(f"unsupported runtime value {value!r}")
    return int(match.group(1)) * {"s":1,"min":60,"h":3600}[match.group(2)]


def _human_timespan_seconds(value: str) -> float:
    value = value.strip()
    if value == "infinity":
        raise CanaryError("runtime is unbounded")
    units = {
        "us": 1e-6,
        "ms": 1e-3,
        "s": 1.0,
        "min": 60.0,
        "h": 3600.0,
        "day": 86400.0,
        "week": 604800.0,
    }
    matches = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*(week|day|min|ms|us|h|s)", value)
    if not matches:
        raise CanaryError(f"cannot parse systemd timespan {value!r}")
    return sum(float(number) * units[unit] for number, unit in matches)


def _gpu_uuids(resource: dict[str, Any]) -> list[str]:
    values = list(resource.get("gpu_uuids", []))
    single = resource.get("gpu_uuid")
    if single is not None:
        if values:
            raise CanaryError("resource mixes gpu_uuid and gpu_uuids")
        values = [single]
    return [str(value) for value in values]


def _cpu_percent(profile: dict[str, Any]) -> int:
    raw = str(profile["CPUQuota"])
    if not raw.endswith("%"):
        raise CanaryError("CPUQuota is not percent")
    return int(raw[:-1])


def _cgroup_cpu_percent(raw: str) -> int:
    fields = raw.split()
    if len(fields) != 2 or fields[0] == "max":
        raise CanaryError(f"cpu.max is not a finite quota: {raw!r}")
    quota, period = map(int, fields)
    if period <= 0:
        raise CanaryError("cpu.max period invalid")
    value = quota * 100 / period
    if abs(value - round(value)) > 1e-9:
        raise CanaryError(f"cpu.max percent is not integral: {value}")
    return int(round(value))


def _verify_snapshot(
    cls: dict[str, Any],
    *,
    runner_name: str,
    env: dict[str, str],
    cgroup: dict[str, str],
    unit: dict[str, str],
    payload_cgroup: dict[str, str] | None = None,
    payload_unit: dict[str, str] | None = None,
) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        checks[name] = bool(condition)
        if not condition:
            failures.append(name)

    prefix = str(cls["runner_prefix"])
    check("runner_prefix", runner_name.startswith(prefix))

    profile = cls["systemd_profile"]
    resource = cls["resource_class"]
    contract = cls["execution_contract"]
    roots = cls["project_roots"]
    forbidden = [str(value) for value in cls["forbidden_paths"]]
    bindings = cls["bindings"]

    network_class = str(contract["payload_network_class"])
    if network_class == OFFLINE_NETWORK:
        expected_cpu = OFFLINE_RUNNER_CPU_PERCENT
        expected_memory = OFFLINE_RUNNER_MEMORY_BYTES
        expected_tasks = OFFLINE_RUNNER_TASKS_MAX
    else:
        expected_cpu = _cpu_percent(profile)
        expected_memory = _memory_bytes(profile["MemoryMax"])
        expected_tasks = int(profile["TasksMax"])
    expected_runtime = min(
        _runtime_seconds(profile["RuntimeMaxSec"]),
        int(resource["max_runtime_seconds"]),
    )

    try:
        actual_cpu = _cgroup_cpu_percent(cgroup["cpu.max"])
    except Exception:
        actual_cpu = -1
    check("cpu_quota", actual_cpu == expected_cpu)
    check("memory_max", cgroup.get("memory.max") == str(expected_memory))
    check("tasks_max", cgroup.get("pids.max") == str(expected_tasks))
    try:
        actual_runtime = _human_timespan_seconds(unit.get("RuntimeMaxUSec", ""))
    except Exception:
        actual_runtime = -1.0
    check("runtime_max", abs(actual_runtime - expected_runtime) < 1e-6)

    rw = unit.get("ReadWritePaths", "")
    ro = unit.get("ReadOnlyPaths", "")
    inaccessible = unit.get("InaccessiblePaths", "")
    for key in ("jobs", "staging_cache", "logs"):
        check(f"rw_root_{key}", str(roots[key]) in rw)
    check("trusted_cache_readonly", str(roots["trusted_cache"]) in ro)
    for index, path in enumerate(forbidden):
        check(f"forbidden_path_{index}", path in inaccessible)

    check("device_policy_closed", unit.get("DevicePolicy", "") == "closed")
    expected_gpus = _gpu_uuids(resource)
    expected_gpu_csv = ",".join(expected_gpus)
    device_allow = unit.get("DeviceAllow", "")
    if expected_gpus:
        check("gpu_target_uuids", env.get("P5_GPU_TARGET_UUIDS", "") == expected_gpu_csv)
        selected = [x for x in env.get("P5_GPU_SELECTED_DEVICES", "").split(",") if x]
        denied = [x for x in env.get("P5_GPU_DENIED_DEVICES", "").split(",") if x]
        check("gpu_selected_cardinality", len(selected) == len(expected_gpus))
        if network_class == OFFLINE_NETWORK:
            check("cuda_hidden_from_online_runner", env.get("CUDA_VISIBLE_DEVICES", "") == "")
            check("online_runner_has_no_selected_gpu", all(path not in device_allow for path in selected))
            check("online_runner_has_no_nvidia_control", "/dev/nvidiactl" not in device_allow)
        else:
            check("cuda_visible_devices", env.get("CUDA_VISIBLE_DEVICES", "") == expected_gpu_csv)
            check("gpu_selected_device_allow", all(path in device_allow for path in selected))
            check("gpu_denied_device_absence", all(path not in device_allow for path in denied))
            check("nvidia_control_device", "/dev/nvidiactl" in device_allow)
    else:
        check("cpu_cuda_empty", env.get("CUDA_VISIBLE_DEVICES", "") == "")
        check("cpu_gpu_target_empty", env.get("P5_GPU_TARGET_UUIDS", "") == "")
        check("cpu_no_physical_device_allow", "/dev/nvidia" not in device_allow)

    runtime_binding = bindings.get("runtime")
    bind_ro = unit.get("BindReadOnlyPaths", "")
    if runtime_binding is None:
        check("runtime_binding_absent", env.get("P5_EXPANDED_RUNTIME", "") == "")
    else:
        runtime_path = str(runtime_binding["canonical_path"])
        check("runtime_binding_env", env.get("P5_EXPANDED_RUNTIME", "") == runtime_path)
        if network_class == OFFLINE_NETWORK:
            check("runtime_hidden_from_online_runner", runtime_path not in bind_ro and runtime_path in inaccessible)
        else:
            check("runtime_binding_readonly", runtime_path in bind_ro)

    model_binding = bindings.get("model")
    if model_binding is None:
        check("model_binding_absent", env.get("P5_MODEL_OBJECT_ROOT", "") == "")
    else:
        model_root = str(model_binding["object_path"])
        check("model_binding_env", env.get("P5_MODEL_OBJECT_ROOT", "") == model_root)
        if network_class == OFFLINE_NETWORK:
            check("model_hidden_from_online_runner", model_root not in ro and model_root in inaccessible)
        else:
            check("model_binding_readonly", model_root in ro)

    address_families = unit.get("RestrictAddressFamilies", "")
    for family in ("AF_UNIX", "AF_INET", "AF_INET6"):
        check(f"address_family_{family}", family in address_families)
    deny = unit.get("IPAddressDeny", "")
    allow = unit.get("IPAddressAllow", "")
    if network_class == PUBLIC_NETWORK:
        for index, token in enumerate(BASE_DENIES):
            check(f"public_private_deny_{index}", token in deny)
        check("public_dns_allow", "127.0.0.53/32" in allow)
        check("public_not_broadly_denied_v4", "0.0.0.0/0" not in deny)
        check("public_not_broadly_denied_v6", "::/0" not in deny)
    elif network_class == OFFLINE_NETWORK:
        check("payload_exec_required", env.get("P5_PAYLOAD_EXEC_REQUIRED", "") == "1")
        check("payload_exec_client", env.get("P5_PAYLOAD_EXEC_CLIENT", "") == OFFLINE_CLIENT_PATH)
        check(
            "payload_exec_workdir",
            env.get("P5_PAYLOAD_EXEC_WORKDIR", "").startswith(
                str(roots["staging_cache"]) + "/"
            ),
        )
        socket_path = env.get("P5_PAYLOAD_EXEC_SOCKET", "")
        check(
            "payload_exec_socket",
            socket_path.startswith("/run/workspace-ci/v3/payload/")
            and socket_path.endswith("/exec.sock"),
        )
        check("online_runner_no_af_netlink", "AF_NETLINK" not in address_families)

        payload_cgroup = payload_cgroup or {}
        payload_unit = payload_unit or {}
        check("payload_broker_present", bool(payload_unit))
        broker_identity = cls.get("payload_broker_identity") or {}
        check(
            "payload_broker_identity_bound",
            set(broker_identity) == {"user", "group"},
        )
        check(
            "payload_broker_distinct_user",
            payload_unit.get("User", "") == broker_identity.get("user")
            and payload_unit.get("User", "") != unit.get("User", ""),
        )
        check(
            "payload_broker_project_group",
            payload_unit.get("Group", "") == broker_identity.get("group"),
        )
        check("payload_private_network", payload_unit.get("PrivateNetwork", "") == "yes")
        payload_families = payload_unit.get("RestrictAddressFamilies", "")
        for family in ("AF_UNIX", "AF_INET", "AF_INET6", "AF_NETLINK"):
            check(f"payload_address_family_{family}", family in payload_families)
        payload_deny = payload_unit.get("IPAddressDeny", "")
        payload_allow = payload_unit.get("IPAddressAllow", "")
        check(
            "payload_network_deny_all",
            "any" in payload_deny or "0.0.0.0/0" in payload_deny,
        )
        check("payload_loopback_v4_only", "127.0.0.0/8" in payload_allow)
        check("payload_loopback_v6_only", "::1/128" in payload_allow)

        payload_device_allow = payload_unit.get("DeviceAllow", "")
        check("payload_nvidia_control_device", "/dev/nvidiactl" in payload_device_allow)
        check(
            "payload_selected_gpu_device_allow",
            all(path in payload_device_allow for path in selected),
        )
        if runtime_binding is not None:
            check(
                "payload_runtime_readonly",
                str(runtime_binding["canonical_path"])
                in payload_unit.get("BindReadOnlyPaths", ""),
            )
        if model_binding is not None:
            check(
                "payload_model_readonly",
                str(model_binding["object_path"])
                in payload_unit.get("ReadOnlyPaths", ""),
            )

        total_cpu = _cpu_percent(profile)
        broker_cpu = total_cpu - OFFLINE_RUNNER_CPU_PERCENT
        try:
            actual_broker_cpu = _cgroup_cpu_percent(payload_cgroup["cpu.max"])
        except Exception:
            actual_broker_cpu = -1
        check("payload_cpu_remainder", actual_broker_cpu == broker_cpu)
        broker_memory = _memory_bytes(profile["MemoryMax"]) - OFFLINE_RUNNER_MEMORY_BYTES
        check("payload_memory_remainder", payload_cgroup.get("memory.max") == str(broker_memory))
        broker_tasks = int(profile["TasksMax"]) - OFFLINE_RUNNER_TASKS_MAX
        check("payload_tasks_remainder", payload_cgroup.get("pids.max") == str(broker_tasks))
    else:
        check("known_payload_network_class", False)

    return {
        "status": "PASS" if not failures else "FAIL",
        "runner_class_id": cls["runner_class_id"],
        "network_class": network_class,
        "gpu_count": len(expected_gpus),
        "checks": sorted(checks),
        "failures": failures,
    }


def _current_cgroup() -> tuple[pathlib.Path, str]:
    for line in pathlib.Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0" and parts[1] == "":
            relative = pathlib.PurePosixPath(parts[2])
            unit_name = relative.name
            if not unit_name.endswith(".service"):
                raise CanaryError(f"unexpected runner cgroup unit {unit_name!r}")
            return pathlib.Path("/sys/fs/cgroup") / str(relative).lstrip("/"), unit_name
    raise CanaryError("unified cgroup v2 path not found")


def _show(unit_name: str, property_name: str) -> str:
    proc = subprocess.run(
        ["systemctl", "show", unit_name, f"--property={property_name}", "--value"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise CanaryError(
            f"systemctl show {property_name} failed rc={proc.returncode}: "
            f"{proc.stderr.strip()[:240]}"
        )
    return proc.stdout.strip()


def _live_snapshot(unit_name: str, cgroup_path: pathlib.Path) -> tuple[dict[str,str], dict[str,str]]:
    cgroup = {}
    for name in ("cpu.max", "memory.max", "pids.max"):
        cgroup[name] = (cgroup_path / name).read_text(encoding="utf-8").strip()
    unit = {}
    for name in (
        "RuntimeMaxUSec",
        "ReadWritePaths",
        "ReadOnlyPaths",
        "InaccessiblePaths",
        "BindReadOnlyPaths",
        "DevicePolicy",
        "DeviceAllow",
        "RestrictAddressFamilies",
        "IPAddressAllow",
        "IPAddressDeny",
        "PrivateNetwork",
        "User",
        "Group",
        "ControlGroup",
    ):
        unit[name] = _show(unit_name, name)
    return cgroup, unit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-class", required=True)
    parser.add_argument("--root-policy", type=pathlib.Path, default=ROOT_POLICY)
    args = parser.parse_args()

    policy = _load_json(args.root_policy)
    classes = policy.get("runner_classes")
    if not isinstance(classes, dict) or args.expected_class not in classes:
        raise CanaryError("expected class is not present in installed root policy")

    runner_name = os.environ.get("RUNNER_NAME", "")
    matches = [
        class_id
        for class_id, cls in classes.items()
        if runner_name.startswith(str(cls["runner_prefix"]))
    ]
    if matches != [args.expected_class]:
        raise CanaryError(
            f"runner identity does not bind exactly to expected class: {matches!r}"
        )

    cgroup_path, unit_name = _current_cgroup()
    expected_unit_prefix = f"workspace-ci-v3-{args.expected_class}-"
    if not unit_name.startswith(expected_unit_prefix):
        raise CanaryError(
            f"runner unit {unit_name!r} does not match {expected_unit_prefix!r}"
        )
    cgroup, unit = _live_snapshot(unit_name, cgroup_path)
    payload_cgroup = None
    payload_unit = None
    network_class = classes[args.expected_class]["execution_contract"]["payload_network_class"]
    if network_class == OFFLINE_NETWORK:
        payload_unit_name = unit_name.removesuffix(".service") + "-payload.service"
        payload_control_group = _show(payload_unit_name, "ControlGroup")
        if not payload_control_group.startswith("/"):
            raise CanaryError("offline payload broker control group is unavailable")
        payload_cgroup_path = pathlib.Path("/sys/fs/cgroup") / payload_control_group.lstrip("/")
        payload_cgroup, payload_unit = _live_snapshot(
            payload_unit_name,
            payload_cgroup_path,
        )
    result = _verify_snapshot(
        classes[args.expected_class],
        runner_name=runner_name,
        env=dict(os.environ),
        cgroup=cgroup,
        unit=unit,
        payload_cgroup=payload_cgroup,
        payload_unit=payload_unit,
    )
    result["unit_name"] = unit_name
    result["root_policy_sha256"] = policy.get("root_policy_sha256")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
