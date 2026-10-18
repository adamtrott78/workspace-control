#!/usr/bin/env python3
"""Privileged runtime primitives for bounded Lambda CI project runners.

This module contains no GitHub authentication and performs no GitHub API calls.
Authority is supplied only through a launch spec produced from root-owned
workspace-control policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import pwd
import shutil
import stat
import subprocess
import threading
from datetime import datetime, timezone
from typing import Any


class RuntimeLaunchError(RuntimeError):
    pass


class RuntimeCleanupError(RuntimeLaunchError):
    """Raised when post-execution cleanup or integrity verification fails."""


class RuntimeTimeoutError(RuntimeLaunchError):
    """Raised after a bounded runner exceeds the root wrapper timeout."""


class RuntimeResourceExhaustedError(RuntimeLaunchError):
    """Raised when systemd proves CPU/RAM resource exhaustion."""


class RuntimeDiskPressureError(RuntimeLaunchError):
    """Raised when root-owned filesystem evidence proves disk pressure."""


class RuntimeCudaOomError(RuntimeLaunchError):
    """Raised only when a root-bound trusted CUDA OOM probe proves CUDA OOM."""


TRUSTED_CUDA_OOM_PROBE_PATH = pathlib.Path(
    "/opt/workspace-ci/provisioner/trusted-probes/lambda_ci_cuda_oom_probe.py"
)
TRUSTED_CUDA_OOM_PROBE_KIND = "cuda_oom_acceptance_v1"
TRUSTED_CUDA_OOM_PROBE_AUTHORITY = "ROOT_SYNTHETIC_CANARY_ONLY"
TRUSTED_CUDA_OOM_PROBE_EXIT = 86
TRUSTED_DUAL_TIMEOUT_PROBE_PATH = pathlib.Path(
    "/opt/workspace-ci/provisioner/trusted-probes/lambda_ci_dual_timeout_probe.py"
)
TRUSTED_DUAL_TIMEOUT_PROBE_KIND = "dual_gpu_timeout_acceptance_v1"
TRUSTED_DUAL_TIMEOUT_PROBE_EXIT = 0
TRUSTED_DUAL_CUDA_OOM_PROBE_PATH = pathlib.Path(
    "/opt/workspace-ci/provisioner/trusted-probes/lambda_ci_dual_cuda_oom_probe.py"
)
TRUSTED_DUAL_CUDA_OOM_PROBE_KIND = "dual_gpu_cuda_oom_acceptance_v1"
TRUSTED_DUAL_CUDA_OOM_PROBE_EXIT = 86
TRUSTED_FAILURE_PROBE_AUTHORITY = "ROOT_SYNTHETIC_CANARY_ONLY"
TRUSTED_CACHE_MANAGER_PATH = pathlib.Path(
    "/opt/workspace-ci/cache-manager/lambda_ci_trusted_cache.py"
)
TRUSTED_CACHE_MANAGER_BLOB = "a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807"


def run(argv: list[str], *, check: bool = True):
    proc = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeLaunchError(
            f"command failed rc={proc.returncode}: {argv[0]}: {proc.stderr.strip()}"
        )
    return proc


def project_identity(user: str) -> tuple[int, int]:
    try:
        row = pwd.getpwnam(user)
    except KeyError as exc:
        raise RuntimeLaunchError(f"project runner identity missing: {user}") from exc

    active = run(["pgrep", "-u", str(row.pw_uid)], check=False)
    if active.returncode == 0 and active.stdout.strip():
        raise RuntimeLaunchError(
            f"existing project process detected for {user}; refusing concurrency"
        )
    if active.returncode not in (0, 1):
        raise RuntimeLaunchError(f"unable to inspect process state for {user}")
    return row.pw_uid, row.pw_gid


def expanded_runtime_tree_digest(root: pathlib.Path) -> str:
    """Hash the accepted expanded-runtime tree without following symlinks."""
    tree_hash = hashlib.sha256()
    for path in sorted(
        root.rglob("*"),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        rel = path.relative_to(root).as_posix()
        st = path.lstat()
        mode = stat.S_IMODE(st.st_mode)

        if stat.S_ISDIR(st.st_mode):
            tree_hash.update(f"D\0{rel}\0{mode:o}\n".encode())
            continue

        if stat.S_ISLNK(st.st_mode):
            tree_hash.update(f"L\0{rel}\0{os.readlink(path)}\n".encode())
            continue

        if not stat.S_ISREG(st.st_mode):
            raise RuntimeLaunchError(f"expanded runtime contains special file: {path}")

        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                block = handle.read(8 * 1024 * 1024)
                if not block:
                    break
                digest.update(block)
        tree_hash.update(
            (
                f"F\0{rel}\0{mode:o}\0{st.st_size}\0"
                f"{digest.hexdigest()}\n"
            ).encode()
        )
    return tree_hash.hexdigest()


def verify_expanded_runtime_binding(spec: dict[str, Any]) -> dict[str, Any]:
    """Verify the exact root-owned expanded runtime before/after gpu-small execution."""
    binding = spec.get("runtime_binding")
    if not isinstance(binding, dict):
        raise RuntimeLaunchError("gpu-small requires exact expanded runtime binding")

    required = {
        "runtime_id",
        "canonical_path",
        "python_path",
        "receipt_path",
        "tree_digest_sha256",
        "manifest_identity_sha256",
        "source_trusted_runtime_object",
        "required_controls",
    }
    if set(binding) != required:
        raise RuntimeLaunchError("expanded runtime binding keys drift")

    runtime = pathlib.Path(binding["canonical_path"])
    python = pathlib.Path(binding["python_path"])
    receipt_path = pathlib.Path(binding["receipt_path"])

    if not runtime.is_absolute() or not receipt_path.is_absolute():
        raise RuntimeLaunchError("expanded runtime paths must be absolute")
    if python != runtime / "bin/python":
        raise RuntimeLaunchError("expanded runtime python path drift")
    if not runtime.is_dir() or not python.is_file():
        raise RuntimeLaunchError("expanded runtime or Python executable missing")
    if not receipt_path.is_file():
        raise RuntimeLaunchError("expanded runtime receipt missing")

    receipt_stat = receipt_path.stat()
    if receipt_stat.st_uid != 0 or receipt_stat.st_gid != 0:
        raise RuntimeLaunchError("expanded runtime receipt is not root-owned")
    if stat.S_IMODE(receipt_stat.st_mode) & 0o222:
        raise RuntimeLaunchError("expanded runtime receipt is writable")

    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeLaunchError("expanded runtime receipt is invalid JSON") from exc

    expected_receipt = {
        "runtime_path": binding["canonical_path"],
        "runtime_contract_version": binding["runtime_id"],
        "source_manifest_identity_sha256": binding["manifest_identity_sha256"],
        "source_trusted_runtime_object": binding["source_trusted_runtime_object"],
        "tree_digest_sha256": binding["tree_digest_sha256"],
        "read_only_hardened": True,
        "receipt_committed_after_all_assertions": True,
        "model_weights_loaded": False,
        "model_inference_performed": False,
    }
    for key, expected in expected_receipt.items():
        if receipt.get(key) != expected:
            raise RuntimeLaunchError(
                f"expanded runtime receipt mismatch for {key}: "
                f"{receipt.get(key)!r} != {expected!r}"
            )

    allowed_external_symlinks = {
        pathlib.Path("/usr/bin/python3"),
        pathlib.Path("/usr/bin/python3.12"),
    }
    file_count = 0
    directory_count = 1
    symlink_count = 0

    root_stat = runtime.lstat()
    if root_stat.st_uid != 0 or root_stat.st_gid != 0:
        raise RuntimeLaunchError("expanded runtime root ownership drift")
    if stat.S_IMODE(root_stat.st_mode) & 0o222:
        raise RuntimeLaunchError("expanded runtime root write bits drift")

    for path in runtime.rglob("*"):
        st = path.lstat()
        if st.st_uid != 0 or st.st_gid != 0:
            raise RuntimeLaunchError(f"expanded runtime ownership drift: {path}")

        if stat.S_ISLNK(st.st_mode):
            symlink_count += 1
            resolved = path.resolve(strict=False)
            try:
                resolved.relative_to(runtime)
            except ValueError:
                if resolved not in allowed_external_symlinks:
                    raise RuntimeLaunchError(
                        f"expanded runtime external symlink drift: {path} -> {resolved}"
                    )
            continue

        if stat.S_ISREG(st.st_mode):
            file_count += 1
        elif stat.S_ISDIR(st.st_mode):
            directory_count += 1
        else:
            raise RuntimeLaunchError(f"expanded runtime special file detected: {path}")

        if stat.S_IMODE(st.st_mode) & 0o222:
            raise RuntimeLaunchError(f"expanded runtime writable inode detected: {path}")

    if file_count != int(receipt.get("file_count", -1)):
        raise RuntimeLaunchError("expanded runtime file count drift")
    if directory_count != int(receipt.get("directory_count", -1)):
        raise RuntimeLaunchError("expanded runtime directory count drift")
    if symlink_count != int(receipt.get("symlink_count", -1)):
        raise RuntimeLaunchError("expanded runtime symlink count drift")

    actual_digest = expanded_runtime_tree_digest(runtime)
    if actual_digest != binding["tree_digest_sha256"]:
        raise RuntimeLaunchError(
            f"expanded runtime tree digest mismatch: {actual_digest}"
        )

    return {
        "runtime_id": binding["runtime_id"],
        "runtime_path": str(runtime),
        "python_path": str(python),
        "receipt_path": str(receipt_path),
        "tree_digest_sha256": actual_digest,
        "manifest_identity_sha256": binding["manifest_identity_sha256"],
        "file_count": file_count,
        "directory_count": directory_count,
        "symlink_count": symlink_count,
        "read_only_hardened": True,
        "receipt_verified": True,
    }


def verify_promoted_model_binding(spec: dict[str, Any]) -> dict[str, Any] | None:
    """Verify the exact promoted model object before/after model-eval execution."""
    binding = spec.get("model_binding")
    workload_class = spec.get("workload_class")
    if binding is None:
        if workload_class == "model-eval-single-gpu":
            raise RuntimeLaunchError("model-eval-single-gpu requires promoted model binding")
        return None
    if workload_class != "model-eval-single-gpu":
        raise RuntimeLaunchError("promoted model binding is forbidden for this workload")
    if not isinstance(binding, dict):
        raise RuntimeLaunchError("promoted model binding must be an object")

    required = {
        "model_id",
        "repository",
        "revision",
        "object_path",
        "object_id",
        "tree_sha256",
        "manifest_sha256",
        "descriptor_sha256",
        "promotion_receipt_sha256",
        "serialization_risk_class",
        "complete_offline",
    }
    if set(binding) != required:
        raise RuntimeLaunchError("promoted model binding keys drift")
    if binding["serialization_risk_class"] != "SAFE":
        raise RuntimeLaunchError("promoted model serialization risk is not SAFE")
    if binding["complete_offline"] is not True:
        raise RuntimeLaunchError("promoted model is not complete offline")
    if binding["object_id"] != binding["tree_sha256"]:
        raise RuntimeLaunchError("promoted model object/tree identity mismatch")
    if binding["manifest_sha256"] != binding["tree_sha256"]:
        raise RuntimeLaunchError("promoted model manifest/tree identity mismatch")

    object_path = pathlib.Path(binding["object_path"])
    trusted_root = pathlib.Path(spec["paths"]["trusted_cache"])
    if not object_path.is_absolute() or not trusted_root.is_absolute():
        raise RuntimeLaunchError("promoted model paths must be absolute")
    try:
        object_path.resolve().relative_to(trusted_root.resolve())
    except ValueError as exc:
        raise RuntimeLaunchError("promoted model path escapes trusted cache") from exc
    if object_path.name != binding["object_id"]:
        raise RuntimeLaunchError("promoted model object path identity drift")
    if not object_path.is_dir():
        raise RuntimeLaunchError("promoted model object is missing")
    payload_path = object_path / "payload"
    if not payload_path.is_dir():
        raise RuntimeLaunchError("promoted model payload is missing")

    manager = TRUSTED_CACHE_MANAGER_PATH
    if not manager.is_file():
        raise RuntimeLaunchError("trusted cache manager is missing")
    st = manager.stat()
    if st.st_uid != 0 or st.st_gid != 0:
        raise RuntimeLaunchError("trusted cache manager is not root-owned")
    if stat.S_IMODE(st.st_mode) & 0o222:
        raise RuntimeLaunchError("trusted cache manager is writable")
    manager_blob = run(["git", "hash-object", str(manager)]).stdout.strip()
    if manager_blob != TRUSTED_CACHE_MANAGER_BLOB:
        raise RuntimeLaunchError("trusted cache manager blob drift")

    verified = run(
        [
            str(manager),
            "verify",
            "--object",
            str(object_path),
        ]
    )
    try:
        result = json.loads(verified.stdout)
    except Exception as exc:
        raise RuntimeLaunchError("trusted model verifier returned invalid JSON") from exc

    expected = {
        "decision": "PASS",
        "object_id": binding["object_id"],
        "project_id": spec["project_id"],
        "artifact_kind": "model",
        "tree_digest_sha256": binding["tree_sha256"],
        "descriptor_sha256": binding["descriptor_sha256"],
        "offline_complete": True,
        "read_only": True,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise RuntimeLaunchError(
                f"promoted model verification mismatch for {key}: "
                f"{result.get(key)!r} != {value!r}"
            )

    source = result.get("source")
    if not isinstance(source, dict):
        raise RuntimeLaunchError("promoted model verifier source identity is missing")
    if source.get("identifier") != binding["repository"]:
        raise RuntimeLaunchError("promoted model repository identity drift")
    if source.get("immutable_revision") != binding["revision"]:
        raise RuntimeLaunchError("promoted model revision identity drift")

    serialization = result.get("serialization")
    if not isinstance(serialization, dict):
        raise RuntimeLaunchError("promoted model serialization identity is missing")
    if serialization.get("unsafe_deserialization") is not False:
        raise RuntimeLaunchError("promoted model unsafe deserialization drift")
    if serialization.get("custom_code") is not False:
        raise RuntimeLaunchError("promoted model custom-code drift")

    return {
        "model_id": binding["model_id"],
        "repository": binding["repository"],
        "revision": binding["revision"],
        "object_path": str(object_path),
        "payload_path": str(payload_path),
        "object_id": binding["object_id"],
        "tree_sha256": binding["tree_sha256"],
        "manifest_sha256": binding["manifest_sha256"],
        "descriptor_sha256": binding["descriptor_sha256"],
        "serialization_risk_class": binding["serialization_risk_class"],
        "complete_offline": True,
        "read_only": True,
        "cache_manager_blob": manager_blob,
    }


def primary_subnet() -> str:
    proc = run(["ip", "-4", "route", "show"])
    for line in proc.stdout.splitlines():
        parts = line.split()
        if (
            parts
            and "/" in parts[0]
            and "proto" in parts
            and "kernel" in parts
            and "scope" in parts
            and "link" in parts
            and parts[0][0].isdigit()
            and not parts[0].startswith(("127.", "169.254.", "172.17.", "172.18.", "100."))
        ):
            return parts[0]
    raise RuntimeLaunchError("unable to resolve directly connected primary IPv4 subnet")


def chown_tree(path: pathlib.Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chown(pathlib.Path(root) / name, uid, gid, follow_symlinks=False)
        for name in files:
            os.chown(pathlib.Path(root) / name, uid, gid, follow_symlinks=False)


def verify_foundation(spec: dict[str, Any]) -> tuple[pathlib.Path, int, int]:
    runner_version = spec["runner"]["version"]
    runner_base = pathlib.Path("/opt/workspace-ci/actions-runner") / runner_version
    if not (runner_base / "run.sh").is_file():
        raise RuntimeLaunchError(f"pinned Actions runner missing: {runner_base}")

    paths = spec["paths"]
    for key in ("job_root", "staging_cache", "trusted_cache", "home", "logs"):
        path = pathlib.Path(paths[key])
        if not path.is_dir():
            raise RuntimeLaunchError(f"required project path missing: {key}={path}")

    user = spec["run_as"]["user"]
    uid, gid = project_identity(user)

    isolation = run(
        [
            "runuser",
            "-u",
            user,
            "--",
            "/bin/bash",
            "-ceu",
            """
            test ! -r /home/atrott
            test ! -r /home/atrott/.ssh
            if [[ -e /var/run/docker.sock ]]; then
              test ! -r /var/run/docker.sock
              test ! -w /var/run/docker.sock
            fi
            """,
        ],
        check=False,
    )
    if isolation.returncode != 0:
        raise RuntimeLaunchError("project identity isolation no longer matches acceptance")

    return runner_base, uid, gid


def nvidia_gpu_inventory() -> list[dict[str, object]]:
    """Resolve the root-observed NVIDIA UUID/device inventory."""
    gpu_root = pathlib.Path("/proc/driver/nvidia/gpus")
    if not gpu_root.is_dir():
        raise RuntimeLaunchError("NVIDIA driver GPU metadata directory is missing")

    inventory: list[dict[str, object]] = []
    for info_path in sorted(gpu_root.glob("*/information")):
        fields: dict[str, str] = {}
        for raw_line in info_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            fields[key.strip()] = value.strip()

        gpu_uuid = fields.get("GPU UUID")
        minor_text = fields.get("Device Minor")
        if not gpu_uuid or minor_text is None:
            raise RuntimeLaunchError(
                f"NVIDIA information file missing GPU UUID/Device Minor: {info_path}"
            )
        try:
            minor = int(minor_text)
        except ValueError as exc:
            raise RuntimeLaunchError(
                f"invalid NVIDIA Device Minor in {info_path}: {minor_text!r}"
            ) from exc

        device = pathlib.Path(f"/dev/nvidia{minor}")
        if not device.exists() or not stat.S_ISCHR(device.stat().st_mode):
            raise RuntimeLaunchError(f"NVIDIA device node invalid for {gpu_uuid}: {device}")

        inventory.append(
            {
                "uuid": gpu_uuid,
                "minor": minor,
                "device": str(device),
                "bus_location": fields.get("Bus Location"),
                "model": fields.get("Model"),
                "information_path": str(info_path),
            }
        )

    if not inventory:
        raise RuntimeLaunchError("NVIDIA driver reported no GPUs")

    nvidiactl = pathlib.Path("/dev/nvidiactl")
    if not nvidiactl.exists() or not stat.S_ISCHR(nvidiactl.stat().st_mode):
        raise RuntimeLaunchError("/dev/nvidiactl missing or not a character device")

    return inventory


def resolve_gpu_assignments(target_uuids: list[str]) -> dict[str, object]:
    """Resolve an exact ordered UUID set to current NVIDIA device nodes."""
    if not isinstance(target_uuids, list) or not target_uuids:
        raise RuntimeLaunchError("GPU target UUID set must be a non-empty list")
    if any(not isinstance(value, str) or not value for value in target_uuids):
        raise RuntimeLaunchError("GPU target UUID set contains an invalid UUID")
    normalized = [value.lower() for value in target_uuids]
    if len(set(normalized)) != len(normalized):
        raise RuntimeLaunchError("GPU target UUID set contains duplicates")

    inventory = nvidia_gpu_inventory()
    selected_rows: list[dict[str, object]] = []
    for target_uuid in target_uuids:
        matches = [
            row
            for row in inventory
            if str(row["uuid"]).lower() == target_uuid.lower()
        ]
        if len(matches) != 1:
            raise RuntimeLaunchError(
                f"expected exactly one GPU matching {target_uuid}, found {len(matches)}"
            )
        selected_rows.append(matches[0])

    selected_uuid_set = {value.lower() for value in target_uuids}
    denied_devices = [
        str(row["device"])
        for row in inventory
        if str(row["uuid"]).lower() not in selected_uuid_set
    ]

    selected_devices = [str(row["device"]) for row in selected_rows]
    selected_minors = [int(row["minor"]) for row in selected_rows]
    return {
        "target_uuid": target_uuids[0],
        "selected_device": selected_devices[0],
        "selected_minor": selected_minors[0],
        "target_uuids": list(target_uuids),
        "selected_devices": selected_devices,
        "selected_minors": selected_minors,
        "denied_devices": denied_devices,
        "inventory": inventory,
    }


def resolve_gpu_assignment(target_uuid: str) -> dict[str, object]:
    """Resolve the accepted single GPU while preserving the P5 receipt contract."""
    assignment = resolve_gpu_assignments([target_uuid])
    denied_devices = list(assignment["denied_devices"])
    if not denied_devices:
        raise RuntimeLaunchError("gpu-small requires at least one non-selected GPU denial target")

    return {
        "target_uuid": target_uuid,
        "selected_device": assignment["selected_devices"][0],
        "selected_minor": assignment["selected_minors"][0],
        "denied_devices": denied_devices,
        "inventory": assignment["inventory"],
        "target_uuids": assignment["target_uuids"],
        "selected_devices": assignment["selected_devices"],
        "selected_minors": assignment["selected_minors"],
    }


def resolve_cuda_support_devices() -> list[str]:
    """Return only the shared NVIDIA compute-support devices accepted by P4."""
    allowed = (
        pathlib.Path("/dev/nvidia-uvm"),
        pathlib.Path("/dev/nvidia-uvm-tools"),
    )
    resolved: list[str] = []
    for path in allowed:
        if not path.exists():
            continue
        if not stat.S_ISCHR(path.stat().st_mode):
            raise RuntimeLaunchError(f"NVIDIA support path is not a character device: {path}")
        resolved.append(str(path))
    if "/dev/nvidia-uvm" not in resolved:
        raise RuntimeLaunchError("CUDA UVM device /dev/nvidia-uvm is missing")
    return resolved


def gpu_processes_on_uuids(target_uuids: list[str]) -> list[dict[str, object]]:
    """Return all NVIDIA compute processes on the exact target UUID set."""
    normalized = {value.lower() for value in target_uuids}
    proc = run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,gpu_uuid,used_memory",
            "--format=csv,noheader,nounits",
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeLaunchError(
            "unable to inspect selected-GPU compute processes: "
            + proc.stderr.strip()
        )

    rows: list[dict[str, object]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3 or parts[1].lower() not in normalized:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        try:
            owner_uid: int | None = os.stat(f"/proc/{pid}").st_uid
        except FileNotFoundError:
            owner_uid = None
        try:
            used_memory: int | None = int(parts[2])
        except ValueError:
            used_memory = None
        rows.append(
            {
                "pid": pid,
                "gpu_uuid": parts[1],
                "used_memory_mib": used_memory,
                "owner_uid": owner_uid,
            }
        )
    return rows


def verify_gpu_targets_idle(
    target_uuids: list[str],
    *,
    project_uid: int | None = None,
) -> list[dict[str, object]]:
    """Fail closed on busy targets; quarantine project-owned stale residue."""
    processes = gpu_processes_on_uuids(target_uuids)
    if not processes:
        return processes

    if project_uid is not None and any(
        row.get("owner_uid") == project_uid for row in processes
    ):
        raise RuntimeCleanupError(
            "dual-GPU target has pre-existing project-owned compute residue: "
            + json.dumps(processes, sort_keys=True)
        )

    raise RuntimeLaunchError(
        "dual-GPU target has pre-existing compute processes: "
        + json.dumps(processes, sort_keys=True)
    )


def project_gpu_processes(uid: int) -> list[dict[str, object]]:
    """Return active NVIDIA compute processes owned by the project UID."""
    proc = run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,gpu_uuid,used_memory",
            "--format=csv,noheader,nounits",
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeLaunchError(
            "unable to inspect NVIDIA compute processes: " + proc.stderr.strip()
        )

    rows: list[dict[str, object]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        try:
            owner_uid = os.stat(f"/proc/{pid}").st_uid
        except FileNotFoundError:
            continue
        if owner_uid != uid:
            continue
        try:
            used_memory = int(parts[2])
        except ValueError:
            used_memory = None
        rows.append(
            {
                "pid": pid,
                "gpu_uuid": parts[1],
                "used_memory_mib": used_memory,
            }
        )
    return rows


def git_blob_sha(path: pathlib.Path) -> str:
    data = path.read_bytes()
    digest = hashlib.sha1()
    digest.update(f"blob {len(data)}\0".encode())
    digest.update(data)
    return digest.hexdigest()


def trusted_probe_file_identity(path: pathlib.Path) -> dict[str, object]:
    st = path.stat()
    return {
        "regular": stat.S_ISREG(st.st_mode),
        "uid": int(st.st_uid),
        "gid": int(st.st_gid),
        "mode": stat.S_IMODE(st.st_mode),
        "source_blob_sha": git_blob_sha(path),
    }


def trusted_failure_probe_contracts() -> dict[str, dict[str, object]]:
    return {
        TRUSTED_CUDA_OOM_PROBE_KIND: {
            "path": TRUSTED_CUDA_OOM_PROBE_PATH,
            "expected_exit_code": TRUSTED_CUDA_OOM_PROBE_EXIT,
            "profiles": {"gpu-small"},
        },
        TRUSTED_DUAL_TIMEOUT_PROBE_KIND: {
            "path": TRUSTED_DUAL_TIMEOUT_PROBE_PATH,
            "expected_exit_code": TRUSTED_DUAL_TIMEOUT_PROBE_EXIT,
            "profiles": {"gpu-heavy"},
        },
        TRUSTED_DUAL_CUDA_OOM_PROBE_KIND: {
            "path": TRUSTED_DUAL_CUDA_OOM_PROBE_PATH,
            "expected_exit_code": TRUSTED_DUAL_CUDA_OOM_PROBE_EXIT,
            "profiles": {"gpu-heavy"},
        },
    }


def verify_trusted_failure_probe_binding(
    spec: dict[str, Any],
) -> dict[str, object] | None:
    """Verify a root-authored immutable synthetic failure probe binding."""
    binding = spec.get("trusted_failure_probe")
    if binding is None:
        return None
    if not isinstance(binding, dict):
        raise RuntimeLaunchError("trusted failure probe binding is invalid")

    required = {
        "kind",
        "authority",
        "path",
        "source_blob_sha",
        "expected_exit_code",
    }
    if set(binding) != required:
        raise RuntimeLaunchError("trusted failure probe binding keys drift")

    kind = str(binding.get("kind"))
    contract = trusted_failure_probe_contracts().get(kind)
    if contract is None:
        raise RuntimeLaunchError("trusted failure probe kind is not accepted")
    if binding["authority"] != TRUSTED_FAILURE_PROBE_AUTHORITY:
        raise RuntimeLaunchError("trusted failure probe authority is not accepted")

    expected_exit = int(contract["expected_exit_code"])
    if binding["expected_exit_code"] != expected_exit:
        raise RuntimeLaunchError("trusted failure probe exit code drift")

    profile = str(spec.get("profile"))
    if profile not in contract["profiles"]:
        raise RuntimeLaunchError(
            f"trusted failure probe kind {kind} is not accepted for profile {profile}"
        )

    path = pathlib.Path(str(binding["path"]))
    if path != contract["path"]:
        raise RuntimeLaunchError("trusted failure probe path drift")

    source_blob_sha = str(binding["source_blob_sha"])
    if len(source_blob_sha) != 40 or any(
        ch not in "0123456789abcdef" for ch in source_blob_sha
    ):
        raise RuntimeLaunchError("trusted failure probe source blob is invalid")

    try:
        identity = trusted_probe_file_identity(path)
    except OSError as exc:
        raise RuntimeLaunchError("trusted failure probe is unavailable") from exc
    if identity["regular"] is not True:
        raise RuntimeLaunchError("trusted failure probe is not a regular file")
    if identity["uid"] != 0 or identity["gid"] != 0:
        raise RuntimeLaunchError("trusted failure probe is not root-owned")
    if int(identity["mode"]) & 0o222:
        raise RuntimeLaunchError("trusted failure probe is writable")

    actual_blob_sha = str(identity["source_blob_sha"])
    if actual_blob_sha != source_blob_sha:
        raise RuntimeLaunchError("trusted failure probe source identity mismatch")

    return {
        "available": True,
        "kind": kind,
        "authority": TRUSTED_FAILURE_PROBE_AUTHORITY,
        "path": str(path),
        "source_blob_sha": actual_blob_sha,
        "expected_exit_code": expected_exit,
    }


def verify_trusted_cuda_oom_probe_binding(
    spec: dict[str, Any],
) -> dict[str, object] | None:
    """Backward-compatible single-GPU trusted CUDA OOM verifier."""
    binding = verify_trusted_failure_probe_binding(spec)
    if binding is None:
        return None
    if binding["kind"] != TRUSTED_CUDA_OOM_PROBE_KIND:
        raise RuntimeLaunchError("trusted CUDA OOM probe kind is not accepted")
    return binding

def trusted_cuda_oom_probe_terminal_evidence(
    binding: dict[str, object] | None,
    unit_evidence: dict[str, object],
) -> dict[str, object]:
    evidence: dict[str, object] = {
        "available": binding is not None,
        "matched": False,
        "kind": None,
        "source_blob_sha": None,
        "expected_exit_code": None,
        "systemd_result": unit_evidence.get("result"),
        "systemd_exec_main_code": unit_evidence.get("exec_main_code"),
        "systemd_exec_main_status": unit_evidence.get("exec_main_status"),
    }
    if binding is None:
        return evidence

    expected = int(binding["expected_exit_code"])
    evidence.update(
        {
            "kind": binding["kind"],
            "source_blob_sha": binding["source_blob_sha"],
            "expected_exit_code": expected,
        }
    )
    evidence["matched"] = (
        unit_evidence.get("available") is True
        and unit_evidence.get("result") == "exit-code"
        and str(unit_evidence.get("exec_main_code")) == "1"
        and str(unit_evidence.get("exec_main_status")) == str(expected)
    )
    return evidence


def build_cpu_systemd_command(
    spec: dict[str, Any],
    runner_dir: pathlib.Path,
    staging_dir: pathlib.Path,
    subnet: str,
) -> list[str]:
    resources = spec["resources"]
    paths = spec["paths"]
    bash_script = r"""
        IFS= read -r jit
        [[ -n "$jit" ]]
        export ACTIONS_RUNNER_INPUT_JITCONFIG="$jit"
        unset jit
        exec ./run.sh
    """

    memory_max = int(resources["memory_max_bytes"])
    memory_high = max(1, memory_max - (4 * 1024**3))

    return [
        "systemd-run",
        "--quiet",
        "--wait",
        "--pipe",
        f"--unit={spec['unit_name']}",
        "-p", "Type=exec",
        "-p", f"User={spec['run_as']['user']}",
        "-p", f"Group={spec['run_as']['group']}",
        "-p", f"WorkingDirectory={runner_dir}",
        "-p", "NoNewPrivileges=yes",
        "-p", "CapabilityBoundingSet=",
        "-p", "AmbientCapabilities=",
        "-p", "RestrictSUIDSGID=yes",
        "-p", "PrivateTmp=yes",
        "-p", "ProtectSystem=strict",
        "-p", "ProtectHome=yes",
        "-p", "ProtectKernelTunables=yes",
        "-p", "ProtectKernelModules=yes",
        "-p", "ProtectKernelLogs=yes",
        "-p", "ProtectControlGroups=yes",
        "-p", "ProtectClock=yes",
        "-p", "ProtectHostname=yes",
        "-p", "RestrictRealtime=yes",
        "-p", "LockPersonality=yes",
        "-p", "ProtectProc=invisible",
        "-p", "ProcSubset=pid",
        "-p", "UMask=0077",
        "-p", f"ReadWritePaths={paths['job_root']}",
        "-p", f"ReadWritePaths={staging_dir}",
        "-p", f"ReadWritePaths={paths['home']}",
        "-p", f"ReadWritePaths={paths['logs']}",
        "-p", f"ReadOnlyPaths={paths['trusted_cache']}",
        "-p", "InaccessiblePaths=/var/run/docker.sock",
        "-p", "InaccessiblePaths=/run/docker.sock",
        "-p", "DevicePolicy=closed",
        "-p", "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
        "-p", "IPAddressAllow=127.0.0.53/32",
        "-p", "IPAddressDeny=127.0.0.0/8",
        "-p", "IPAddressDeny=::1/128",
        "-p", "IPAddressDeny=10.0.0.0/8",
        "-p", "IPAddressDeny=172.16.0.0/12",
        "-p", "IPAddressDeny=192.168.0.0/16",
        "-p", "IPAddressDeny=100.64.0.0/10",
        "-p", "IPAddressDeny=169.254.0.0/16",
        "-p", "IPAddressDeny=fe80::/10",
        "-p", "IPAddressDeny=fc00::/7",
        "-p", f"IPAddressDeny={subnet}",
        "-p", f"CPUQuota={int(resources['cpu_quota_percent'])}%",
        "-p", f"MemoryHigh={memory_high}",
        "-p", f"MemoryMax={memory_max}",
        "-p", f"TasksMax={int(resources['tasks_max'])}",
        "-p", f"RuntimeMaxSec={int(resources['runtime_max_seconds'])}s",
        "-p", "KillMode=control-group",
        "-p", "SendSIGKILL=yes",
        "-p", "TimeoutStopSec=20s",
        "-p", f"Environment=HOME={paths['home']}",
        "-p", f"Environment=XDG_CACHE_HOME={staging_dir}",
        "-p", f"Environment=HF_HOME={staging_dir / 'huggingface'}",
        "/bin/bash",
        "-ceu",
        bash_script,
    ]


def build_gpu_systemd_command(
    spec: dict[str, Any],
    runner_dir: pathlib.Path,
    staging_dir: pathlib.Path,
    subnet: str,
    assignment: dict[str, object],
) -> list[str]:
    resources = spec["resources"]
    paths = spec["paths"]
    runtime_binding = spec.get("runtime_binding")
    if not isinstance(runtime_binding, dict):
        raise RuntimeLaunchError("gpu-small systemd command requires runtime binding")

    runtime_path = pathlib.Path(runtime_binding["canonical_path"])
    runtime_python = pathlib.Path(runtime_binding["python_path"])
    job_home = staging_dir / "home"
    xdg_cache = staging_dir / "xdg"
    hf_home = staging_dir / "huggingface"
    torch_home = staging_dir / "torch"
    triton_cache = staging_dir / "triton"
    inductor_cache = staging_dir / "inductor"
    cuda_cache = staging_dir / "cuda"
    vllm_config = staging_dir / "vllm-config"
    vllm_cache = staging_dir / "vllm-cache"
    pycache = staging_dir / "pycache"

    bash_script = r"""
        IFS= read -r jit
        [[ -n "$jit" ]]
        export ACTIONS_RUNNER_INPUT_JITCONFIG="$jit"
        unset jit
        exec ./run.sh
    """

    raw_target_uuids = assignment.get("target_uuids")
    if raw_target_uuids is None:
        target_uuids = [str(assignment["target_uuid"])]
    else:
        target_uuids = [str(value) for value in raw_target_uuids]
    raw_selected_devices = assignment.get("selected_devices")
    if raw_selected_devices is None:
        selected_devices = [str(assignment["selected_device"])]
    else:
        selected_devices = [str(value) for value in raw_selected_devices]

    if not target_uuids or len(target_uuids) != len(selected_devices):
        raise RuntimeLaunchError("GPU UUID/device assignment cardinality mismatch")
    if len({value.lower() for value in target_uuids}) != len(target_uuids):
        raise RuntimeLaunchError("GPU UUID/device assignment contains duplicate UUIDs")
    if len(set(selected_devices)) != len(selected_devices):
        raise RuntimeLaunchError("GPU UUID/device assignment contains duplicate devices")

    selected_device = selected_devices[0]
    target_uuid = target_uuids[0]
    target_uuid_csv = ",".join(target_uuids)
    selected_device_csv = ",".join(selected_devices)
    denied_devices = ",".join(str(path) for path in assignment["denied_devices"])
    support_devices = [str(path) for path in assignment["support_devices"]]

    memory_max = int(resources["memory_max_bytes"])
    memory_high = max(1, memory_max - (8 * 1024**3))

    command = [
        "systemd-run",
        "--quiet",
        "--wait",
        "--pipe",
        f"--unit={spec['unit_name']}",
        "-p", "Type=exec",
        "-p", f"User={spec['run_as']['user']}",
        "-p", f"Group={spec['run_as']['group']}",
        "-p", f"WorkingDirectory={runner_dir}",
        "-p", "NoNewPrivileges=yes",
        "-p", "CapabilityBoundingSet=",
        "-p", "AmbientCapabilities=",
        "-p", "RestrictSUIDSGID=yes",
        "-p", "PrivateTmp=yes",
        "-p", "ProtectSystem=strict",
        "-p", "ProtectHome=yes",
        "-p", "ProtectKernelTunables=yes",
        "-p", "ProtectKernelModules=yes",
        "-p", "ProtectKernelLogs=yes",
        "-p", "ProtectControlGroups=yes",
        "-p", "ProtectClock=yes",
        "-p", "ProtectHostname=yes",
        "-p", "RestrictRealtime=yes",
        "-p", "LockPersonality=yes",
        "-p", "ProtectProc=invisible",
        "-p", "ProcSubset=pid",
        "-p", "UMask=0077",
        "-p", f"ReadWritePaths={paths['job_root']}",
        "-p", f"ReadWritePaths={staging_dir}",
        "-p", f"ReadWritePaths={paths['logs']}",
        "-p", f"ReadOnlyPaths={paths['trusted_cache']}",
        "-p", f"BindReadOnlyPaths={runtime_path}",
        "-p", "InaccessiblePaths=/var/run/docker.sock",
        "-p", "InaccessiblePaths=/run/docker.sock",
        "-p", "DevicePolicy=closed",
        "-p", "DeviceAllow=/dev/nvidiactl rw",
        "-p", f"DeviceAllow={selected_device} rw",
        "-p", "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
        "-p", "IPAddressAllow=127.0.0.53/32",
        "-p", "IPAddressDeny=127.0.0.0/8",
        "-p", "IPAddressDeny=::1/128",
        "-p", "IPAddressDeny=10.0.0.0/8",
        "-p", "IPAddressDeny=172.16.0.0/12",
        "-p", "IPAddressDeny=192.168.0.0/16",
        "-p", "IPAddressDeny=100.64.0.0/10",
        "-p", "IPAddressDeny=169.254.0.0/16",
        "-p", "IPAddressDeny=fe80::/10",
        "-p", "IPAddressDeny=fc00::/7",
        "-p", f"IPAddressDeny={subnet}",
        "-p", f"CPUQuota={int(resources['cpu_quota_percent'])}%",
        "-p", f"MemoryHigh={memory_high}",
        "-p", f"MemoryMax={memory_max}",
        "-p", f"TasksMax={int(resources['tasks_max'])}",
        "-p", f"RuntimeMaxSec={int(resources['runtime_max_seconds'])}s",
        "-p", "KillMode=control-group",
        "-p", "SendSIGKILL=yes",
        "-p", "TimeoutStopSec=20s",
        "-p", f"Environment=HOME={job_home}",
        "-p", f"Environment=XDG_CACHE_HOME={xdg_cache}",
        "-p", f"Environment=HF_HOME={hf_home}",
        "-p", f"Environment=TORCH_HOME={torch_home}",
        "-p", f"Environment=TRITON_CACHE_DIR={triton_cache}",
        "-p", f"Environment=TORCHINDUCTOR_CACHE_DIR={inductor_cache}",
        "-p", f"Environment=CUDA_CACHE_PATH={cuda_cache}",
        "-p", f"Environment=VLLM_CONFIG_ROOT={vllm_config}",
        "-p", f"Environment=VLLM_CACHE_ROOT={vllm_cache}",
        "-p", f"Environment=PYTHONPYCACHEPREFIX={pycache}",
        "-p", "Environment=PYTHONDONTWRITEBYTECODE=1",
        "-p", "Environment=VLLM_USE_FLASHINFER_SAMPLER=0",
        "-p", f"Environment=P5_EXPANDED_RUNTIME={runtime_path}",
        "-p", f"Environment=P5_EXPANDED_RUNTIME_PYTHON={runtime_python}",
        "-p", (
            "Environment=P5_EXPANDED_RUNTIME_TREE_SHA256="
            f"{runtime_binding['tree_digest_sha256']}"
        ),
        "-p", (
            "Environment=P5_EXPANDED_RUNTIME_MANIFEST_SHA256="
            f"{runtime_binding['manifest_identity_sha256']}"
        ),
        "-p", f"Environment=CUDA_VISIBLE_DEVICES={target_uuid_csv}",
        "-p", f"Environment=P5_GPU_TARGET_UUID={target_uuid}",
        "-p", f"Environment=P5_GPU_TARGET_UUIDS={target_uuid_csv}",
        "-p", f"Environment=P5_GPU_SELECTED_DEVICE={selected_device}",
        "-p", f"Environment=P5_GPU_SELECTED_DEVICES={selected_device_csv}",
        "-p", f"Environment=P5_GPU_DENIED_DEVICES={denied_devices}",
        "-p", f"Environment=P5_GPU_SUPPORT_DEVICES={','.join(support_devices)}",
        "/bin/bash",
        "-ceu",
        bash_script,
    ]

    model_binding = spec.get("model_binding")
    if model_binding is not None:
        # vLLM/psutil require read access to non-process procfs files such as
        # /proc/meminfo during engine initialization. Keep ProtectProc=invisible
        # for process privacy, but expose the normal non-process procfs subset
        # only for the exact promoted-model workload.
        command[command.index("ProcSubset=pid")] = "ProcSubset=all"
        # Gloo resolves GLOO_SOCKET_IFNAME via getifaddrs(3). On Linux,
        # getifaddrs uses AF_NETLINK to enumerate interface addresses. Keep
        # the base AF_UNIX/AF_INET/AF_INET6 restriction for ordinary GPU jobs,
        # and add AF_NETLINK only for the exact promoted-model workload.
        command[
            command.index("RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6")
        ] = "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK"

        model_object_root = pathlib.Path(model_binding["object_path"])
        model_path = model_object_root / "payload"
        executable_index = command.index("/bin/bash")
        model_properties = [
            "-p", f"ReadOnlyPaths={model_object_root}",
            "-p", f"Environment=P5_MODEL_ID={model_binding['model_id']}",
            "-p", f"Environment=P5_MODEL_REPOSITORY={model_binding['repository']}",
            "-p", f"Environment=P5_MODEL_REVISION={model_binding['revision']}",
            "-p", f"Environment=P5_MODEL_OBJECT_ID={model_binding['object_id']}",
            "-p", f"Environment=P5_MODEL_OBJECT_ROOT={model_object_root}",
            "-p", f"Environment=P5_MODEL_PATH={model_path}",
            "-p", "Environment=HF_HUB_OFFLINE=1",
            "-p", "Environment=TRANSFORMERS_OFFLINE=1",
            "-p", "Environment=HF_HUB_DISABLE_TELEMETRY=1",
            "-p", "Environment=VLLM_NO_USAGE_STATS=1",
            "-p", "Environment=VLLM_MEDIA_URL_ALLOW_REDIRECTS=0",
            # vLLM creates world-size-1 Gloo/NCCL process groups even for one
            # GPU. Pin their bootstrap traffic to loopback and allow only the
            # loopback endpoints through the existing IPAddressDeny policy.
            "-p", "IPAddressAllow=127.0.0.1/32",
            "-p", "IPAddressAllow=::1/128",
            "-p", "Environment=GLOO_SOCKET_IFNAME=lo",
            "-p", "Environment=NCCL_SOCKET_IFNAME=lo",
        ]
        command[executable_index:executable_index] = model_properties

    insert_at = command.index("-p", command.index(f"DeviceAllow={selected_device} rw") + 1)
    for extra_device in selected_devices[1:]:
        command[insert_at:insert_at] = ["-p", f"DeviceAllow={extra_device} rw"]
        insert_at += 2
    for support_device in support_devices:
        command[insert_at:insert_at] = ["-p", f"DeviceAllow={support_device} rw"]
        insert_at += 2
    return command

def build_trusted_failure_probe_systemd_command(
    spec: dict[str, Any],
    runner_dir: pathlib.Path,
    staging_dir: pathlib.Path,
    subnet: str,
    assignment: dict[str, object],
    binding: dict[str, object],
) -> list[str]:
    command = build_gpu_systemd_command(
        spec,
        runner_dir,
        staging_dir,
        subnet,
        assignment,
    )
    probe_path = pathlib.Path(str(binding["path"]))
    runtime_python = pathlib.Path(spec["runtime_binding"]["python_path"])

    try:
        executable_index = command.index("/bin/bash")
    except ValueError as exc:
        raise RuntimeLaunchError("GPU command executable boundary drift") from exc

    command[executable_index:executable_index] = [
        "-p",
        f"ReadOnlyPaths={probe_path}",
    ]
    executable_index += 2
    command[executable_index:] = [
        str(runtime_python),
        str(probe_path),
    ]
    return command


def build_trusted_cuda_oom_probe_systemd_command(
    spec: dict[str, Any],
    runner_dir: pathlib.Path,
    staging_dir: pathlib.Path,
    subnet: str,
    assignment: dict[str, object],
) -> list[str]:
    binding = verify_trusted_cuda_oom_probe_binding(spec)
    if binding is None:
        raise RuntimeLaunchError("trusted CUDA OOM probe binding is required")
    return build_trusted_failure_probe_systemd_command(
        spec,
        runner_dir,
        staging_dir,
        subnet,
        assignment,
        binding,
    )

def _pump(stream, log) -> None:
    try:
        for line in iter(stream.readline, ""):
            log.write(line)
            log.flush()
    finally:
        stream.close()



def wait_for_transient_runner(
    proc: subprocess.Popen,
    unit_name: str,
    timeout_seconds: int,
) -> tuple[int | None, bool, bool]:
    """Wait for systemd-run and fail closed if the wrapper itself exceeds its bound.

    Returns (return_code, timed_out, timeout_cleanup_pass).
    """
    try:
        return proc.wait(timeout=timeout_seconds), False, True
    except subprocess.TimeoutExpired:
        run(["systemctl", "stop", unit_name], check=False)

        try:
            rc = proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                rc = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    rc = proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    rc = None

        active = run(["systemctl", "is-active", unit_name], check=False)
        state = active.stdout.strip()
        unit_stopped = state not in {
            "active",
            "activating",
            "deactivating",
            "reloading",
        }
        wrapper_reaped = proc.poll() is not None
        run(["systemctl", "reset-failed", unit_name], check=False)
        return rc, True, bool(unit_stopped and wrapper_reaped)


def transient_unit_terminal_evidence(unit_name: str) -> dict[str, object]:
    """Read root-owned systemd terminal state before clearing a failed transient unit."""
    observed = run(
        [
            "systemctl",
            "show",
            unit_name,
            "--property=Result",
            "--property=ExecMainCode",
            "--property=ExecMainStatus",
            "--no-pager",
        ],
        check=False,
    )
    evidence: dict[str, object] = {
        "available": observed.returncode == 0,
        "result": None,
        "exec_main_code": None,
        "exec_main_status": None,
    }
    if observed.returncode == 0:
        values = {}
        for line in observed.stdout.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value
        evidence["result"] = values.get("Result")
        evidence["exec_main_code"] = values.get("ExecMainCode")
        evidence["exec_main_status"] = values.get("ExecMainStatus")
    run(["systemctl", "reset-failed", unit_name], check=False)
    return evidence


def systemd_proves_runtime_timeout(
    evidence: dict[str, object],
) -> bool:
    return evidence.get("result") == "timeout"


def systemd_proves_cpu_or_ram_exhaustion(
    evidence: dict[str, object],
) -> bool:
    return evidence.get("result") == "oom-kill"


def filesystem_pressure_evidence(
    paths: dict[str, pathlib.Path],
) -> dict[str, object]:
    """Capture root-owned terminal free-space/inode evidence before cleanup."""
    entries: dict[str, dict[str, object]] = {}
    pressure = False

    for label, path in paths.items():
        try:
            statvfs = os.statvfs(path)
        except OSError as exc:
            entries[label] = {
                "path": str(path),
                "available": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
            continue

        fragment = statvfs.f_frsize or statvfs.f_bsize
        available_blocks = int(statvfs.f_bavail)
        available_bytes = available_blocks * int(fragment)
        available_inodes = int(statvfs.f_favail)
        inode_accounting = int(statvfs.f_files) > 0
        blocks_exhausted = available_blocks == 0
        inodes_exhausted = inode_accounting and available_inodes == 0

        if blocks_exhausted or inodes_exhausted:
            pressure = True

        entries[label] = {
            "path": str(path),
            "available": True,
            "fragment_size": int(fragment),
            "available_blocks": available_blocks,
            "available_bytes": available_bytes,
            "available_inodes": available_inodes,
            "inode_accounting": inode_accounting,
            "blocks_exhausted": blocks_exhausted,
            "inodes_exhausted": inodes_exhausted,
        }

    return {
        "available": all(
            isinstance(value, dict) and value.get("available") is True
            for value in entries.values()
        ),
        "pressure": pressure,
        "filesystems": entries,
    }


def filesystem_proves_disk_pressure(
    evidence: dict[str, object],
) -> bool:
    return evidence.get("pressure") is True


def cleanup_project_uid_processes(uid: int) -> tuple[bool, bool]:
    """Kill project-UID residue if present and verify the UID is empty afterward."""
    before = run(["pgrep", "-u", str(uid)], check=False)
    if before.returncode not in (0, 1):
        return False, False
    residue_detected = before.returncode == 0 and bool(before.stdout.strip())
    if residue_detected:
        run(["pkill", "-KILL", "-u", str(uid)], check=False)

    after = run(["pgrep", "-u", str(uid)], check=False)
    if after.returncode not in (0, 1):
        return residue_detected, False
    clean = after.returncode == 1 or not after.stdout.strip()
    return residue_detected, clean


def remove_tree_and_verify(path: pathlib.Path) -> bool:
    """Best-effort removal followed by an authoritative existence check."""
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return True
    except OSError:
        pass
    return not path.exists()


def admission_receipt_identity(spec: dict[str, Any]) -> dict[str, Any]:
    admission = spec.get("admission")
    if not isinstance(admission, dict):
        return {}
    policy_binding = admission.get("policy")
    workflow = admission.get("trusted_workflow")
    if not isinstance(policy_binding, dict) or not isinstance(workflow, dict):
        raise RuntimeLaunchError("v2 launch spec admission identity is incomplete")
    lifecycle = admission.get("lifecycle")
    if not isinstance(lifecycle, dict) or lifecycle.get("consumed_at") is None:
        raise RuntimeLaunchError("v2 launch spec admission is not consumed")
    return {
        "admission_identity": {
            "admission_id": admission["admission_id"],
            "request_digest_sha256": admission["request_digest_sha256"],
            "candidate_sha": admission["candidate_sha"],
            "workload_class": admission["workload_class"],
            "execution_profile": admission["execution_profile"],
            "resource_class": admission["resource_class"],
            "policy_id": policy_binding["policy_id"],
            "policy_epoch": policy_binding["policy_epoch"],
            "policy_sha256": policy_binding["policy_sha256"],
            "project_profile_sha256": policy_binding["project_profile_sha256"],
            "kill_switch_epoch": policy_binding["kill_switch_epoch"],
            "workflow_path": workflow["path"],
            "workflow_default_branch_commit_sha": workflow[
                "default_branch_commit_sha"
            ],
            "workflow_blob_sha": workflow["workflow_blob_sha"],
            "consumed_at": lifecycle["consumed_at"],
        }
    }

def launch_cpu_runner(request, spec: dict[str, Any]) -> dict[str, Any]:
    """Launch one accepted CPU runner and return a non-secret cleanup receipt."""
    if spec["profile"] != "cpu-test":
        raise RuntimeLaunchError("P5 pilot runtime accepts cpu-test only")
    if spec["resources"]["gpu_indices"]:
        raise RuntimeLaunchError("cpu-test spec unexpectedly contains GPU authority")
    if spec["allow_production_services"]:
        raise RuntimeLaunchError("production-service access is forbidden")

    runner_base, uid, gid = verify_foundation(spec)
    subnet = primary_subnet()
    request_id = request.request_id

    job_root = pathlib.Path(spec["paths"]["job_root"])
    staging_root = pathlib.Path(spec["paths"]["staging_cache"])
    logs_root = pathlib.Path(spec["paths"]["logs"])
    job_dir = job_root / f"p5-{request_id}"
    runner_dir = job_dir / "runner"
    staging_dir = staging_root / f"p5-{request_id}"

    if job_dir.exists() or staging_dir.exists():
        raise RuntimeLaunchError("request workspace already exists")

    job_dir.mkdir(mode=0o700)
    staging_dir.mkdir(mode=0o700)
    shutil.copytree(runner_base, runner_dir, symlinks=True)
    chown_tree(job_dir, uid, gid)
    chown_tree(staging_dir, uid, gid)

    console_log = logs_root / f"p5-{request_id}-runner.log"
    journal_log = logs_root / f"p5-{request_id}-journal.log"
    receipt_path = logs_root / f"p5-{request_id}-receipt.json"
    command = build_cpu_systemd_command(spec, runner_dir, staging_dir, subnet)

    result = "FAIL"
    terminal_status = "FAILED"
    rc = None
    timed_out = False
    wrapper_cleanup_pass = True
    unit_terminal_evidence: dict[str, object] = {
        "available": False,
        "result": None,
        "exec_main_code": None,
        "exec_main_status": None,
    }
    resource_exhausted = False
    disk_pressure = False
    disk_pressure_evidence: dict[str, object] = {
        "available": False,
        "pressure": False,
        "filesystems": {},
    }
    execution_error: Exception | None = None
    residue_detected = False
    cleanup_pass = False
    runner_workspace_destroyed = False
    staging_workspace_destroyed = False
    jit = request.jit_config

    try:
        with console_log.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert proc.stdin is not None
            assert proc.stdout is not None
            output_thread = threading.Thread(target=_pump, args=(proc.stdout, log), daemon=True)
            output_thread.start()
            proc.stdin.write(jit + "\n")
            proc.stdin.flush()
            proc.stdin.close()
            jit = ""
            rc, timed_out, wrapper_cleanup_pass = wait_for_transient_runner(
                proc,
                spec["unit_name"],
                int(spec["resources"]["runtime_max_seconds"]) + 120,
            )
            output_thread.join(timeout=10)
        if timed_out:
            terminal_status = "TIMED_OUT"
            execution_error = RuntimeTimeoutError(
                "runner exceeded root wrapper timeout "
                f"unit={spec['unit_name']}"
            )
        elif rc != 0:
            execution_error = RuntimeLaunchError(f"runner/systemd unit exited rc={rc}")
        else:
            result = "RUNNER_EXITED_CLEANLY"
            terminal_status = "SUCCEEDED"
    except Exception as exc:
        execution_error = exc
    finally:
        jit = ""

        if not timed_out and rc not in (None, 0):
            unit_terminal_evidence = transient_unit_terminal_evidence(
                spec["unit_name"]
            )
            if systemd_proves_runtime_timeout(unit_terminal_evidence):
                terminal_status = "TIMED_OUT"
                timed_out = True
                execution_error = RuntimeTimeoutError(
                    "systemd reported bounded runtime timeout "
                    f"unit={spec['unit_name']}"
                )
            elif systemd_proves_cpu_or_ram_exhaustion(unit_terminal_evidence):
                terminal_status = "CPU_OR_RAM_RESOURCE_EXHAUSTED"
                resource_exhausted = True
                execution_error = RuntimeResourceExhaustedError(
                    "systemd reported CPU/RAM resource exhaustion "
                    f"result={unit_terminal_evidence.get('result')} "
                    f"unit={spec['unit_name']}"
                )

            else:
                disk_pressure_evidence = filesystem_pressure_evidence(
                    {
                        "job": job_dir,
                        "staging": staging_dir,
                    }
                )
                if filesystem_proves_disk_pressure(disk_pressure_evidence):
                    terminal_status = "DISK_PRESSURE"
                    disk_pressure = True
                    execution_error = RuntimeDiskPressureError(
                        "root-owned filesystem evidence reported disk pressure "
                        f"unit={spec['unit_name']}"
                    )

        residue_detected, cleanup_pass = cleanup_project_uid_processes(uid)

        journal = run(
            ["journalctl", "-u", spec["unit_name"], "--no-pager", "-n", "1000"],
            check=False,
        )
        journal_log.write_text(
            journal.stdout + ("\n" + journal.stderr if journal.stderr else ""),
            encoding="utf-8",
        )

        diag = runner_dir / "_diag"
        if diag.is_dir():
            target = logs_root / f"p5-{request_id}-diag"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(diag, target, symlinks=True)

        runner_workspace_destroyed = remove_tree_and_verify(job_dir)
        staging_workspace_destroyed = remove_tree_and_verify(staging_dir)

        receipt = {
            "schema_version": 2,
            "phase": "P5-provisioner-runtime",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "decision": result,
            "terminal_status": terminal_status,
            "timed_out": timed_out,
            "wrapper_timeout_cleanup": wrapper_cleanup_pass,
            "automatic_retry_eligible": False,
            "resource_exhausted": resource_exhausted,
            "systemd_terminal_evidence": unit_terminal_evidence,
            "disk_pressure": disk_pressure,
            "disk_pressure_evidence": disk_pressure_evidence,
            "request_id": request_id,
            "project_id": spec["project_id"],
            "profile": spec["profile"],
            "runner_name": spec["runner_name"],
            "unit_name": spec["unit_name"],
            "runner_exit_code": rc,
            "project_uid_process_residue_detected": residue_detected,
            "project_uid_process_cleanup": cleanup_pass,
            "runner_workspace_destroyed": runner_workspace_destroyed,
            "staging_workspace_destroyed": staging_workspace_destroyed,
            "network_local_subnet_denied": subnet,
            "jit_config_persisted": False,
            "github_credential_present": False,
        }
        receipt.update(admission_receipt_identity(spec))
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    cleanup_failures = []
    if not wrapper_cleanup_pass:
        cleanup_failures.append("timed-out systemd wrapper/unit did not terminate cleanly")
    if not cleanup_pass:
        cleanup_failures.append("project UID processes remain or could not be verified")
    if not runner_workspace_destroyed:
        cleanup_failures.append("runner workspace removal failed")
    if not staging_workspace_destroyed:
        cleanup_failures.append("staging workspace removal failed")
    if cleanup_failures:
        raise RuntimeCleanupError("; ".join(cleanup_failures))
    if execution_error is not None:
        raise execution_error
    if result != "RUNNER_EXITED_CLEANLY":
        raise RuntimeLaunchError(f"runner did not complete cleanly result={result}")
    return receipt

def launch_gpu_runner(request, spec: dict[str, Any]) -> dict[str, Any]:
    """Launch only the explicitly bounded accepted GPU workload/profile pair."""
    profile = spec["profile"]
    workload = spec.get("workload_class")
    resources = spec["resources"]
    prelaunch_gpu_processes: list[dict[str, object]] = []
    prelaunch_gpu_idle_verified = False

    if spec["allow_production_services"]:
        raise RuntimeLaunchError("production-service access is forbidden")

    if profile == "gpu-small":
        if resources["gpu_indices"] != [0]:
            raise RuntimeLaunchError("gpu-small authority must remain exactly one GPU")
        target_uuid = resources.get("gpu_uuid")
        if target_uuid != "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea":
            raise RuntimeLaunchError("gpu-small target UUID drift")
        target_uuids = resources.get("gpu_uuids", [target_uuid])
        if target_uuids != [target_uuid]:
            raise RuntimeLaunchError("gpu-small UUID set drift")
        assignment = resolve_gpu_assignment(target_uuid)
    elif profile == "gpu-heavy":
        if workload != "model-eval-dual-gpu":
            raise RuntimeLaunchError(
                "gpu-heavy is accepted only for model-eval-dual-gpu"
            )
        if spec.get("model_binding") is None:
            raise RuntimeLaunchError("dual-GPU model eval requires promoted model binding")
        if resources["gpu_indices"] != [0, 1]:
            raise RuntimeLaunchError("dual-GPU authority requires exactly two GPU slots")
        expected_uuids = [
            "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
            "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
        ]
        target_uuids = resources.get("gpu_uuids")
        if target_uuids != expected_uuids:
            raise RuntimeLaunchError("dual-GPU target UUID set drift")
        if resources.get("gpu_uuid") not in (None, ""):
            raise RuntimeLaunchError("dual-GPU profile must not use singular GPU authority")
        assignment = resolve_gpu_assignments(target_uuids)
        if len(assignment["inventory"]) != 2 or assignment["denied_devices"]:
            raise RuntimeLaunchError(
                "dual-GPU host inventory must be exactly the two accepted GPUs"
            )
        project_uid, _ = project_identity(spec["run_as"]["user"])
        prelaunch_gpu_processes = verify_gpu_targets_idle(
            target_uuids,
            project_uid=project_uid,
        )
        prelaunch_gpu_idle_verified = True
    else:
        raise RuntimeLaunchError(f"GPU runtime profile rejected: {profile}")

    runtime_pre = verify_expanded_runtime_binding(spec)
    model_pre = verify_promoted_model_binding(spec)
    trusted_failure_probe = verify_trusted_failure_probe_binding(spec)
    trusted_cuda_oom_probe = None
    if trusted_failure_probe is not None:
        probe_kind = trusted_failure_probe["kind"]
        if probe_kind in {
            TRUSTED_CUDA_OOM_PROBE_KIND,
            TRUSTED_DUAL_CUDA_OOM_PROBE_KIND,
        }:
            trusted_cuda_oom_probe = trusted_failure_probe

        if profile == "gpu-small" and probe_kind != TRUSTED_CUDA_OOM_PROBE_KIND:
            raise RuntimeLaunchError("single-GPU profile received a dual failure probe")
        if profile == "gpu-heavy" and probe_kind not in {
            TRUSTED_DUAL_TIMEOUT_PROBE_KIND,
            TRUSTED_DUAL_CUDA_OOM_PROBE_KIND,
        }:
            raise RuntimeLaunchError("dual-GPU profile received an unaccepted failure probe")

    runner_base, uid, gid = verify_foundation(spec)
    subnet = primary_subnet()
    assignment["support_devices"] = resolve_cuda_support_devices()
    request_id = request.request_id

    job_root = pathlib.Path(spec["paths"]["job_root"])
    staging_root = pathlib.Path(spec["paths"]["staging_cache"])
    logs_root = pathlib.Path(spec["paths"]["logs"])
    job_dir = job_root / f"p5-{request_id}"
    runner_dir = job_dir / "runner"
    staging_dir = staging_root / f"p5-{request_id}"

    if job_dir.exists() or staging_dir.exists():
        raise RuntimeLaunchError("request workspace already exists")

    job_dir.mkdir(mode=0o700)
    staging_dir.mkdir(mode=0o700)
    for name in (
        "home",
        "xdg",
        "huggingface",
        "torch",
        "triton",
        "inductor",
        "cuda",
        "vllm-config",
        "vllm-cache",
        "pycache",
    ):
        (staging_dir / name).mkdir(mode=0o700)

    shutil.copytree(runner_base, runner_dir, symlinks=True)
    chown_tree(job_dir, uid, gid)
    chown_tree(staging_dir, uid, gid)

    console_log = logs_root / f"p5-{request_id}-runner.log"
    journal_log = logs_root / f"p5-{request_id}-journal.log"
    receipt_path = logs_root / f"p5-{request_id}-receipt.json"
    if trusted_failure_probe is None:
        command = build_gpu_systemd_command(
            spec,
            runner_dir,
            staging_dir,
            subnet,
            assignment,
        )
    else:
        command = build_trusted_failure_probe_systemd_command(
            spec,
            runner_dir,
            staging_dir,
            subnet,
            assignment,
            trusted_failure_probe,
        )

    result = "FAIL"
    terminal_status = "FAILED"
    rc = None
    timed_out = False
    wrapper_cleanup_pass = True
    unit_terminal_evidence: dict[str, object] = {
        "available": False,
        "result": None,
        "exec_main_code": None,
        "exec_main_status": None,
    }
    resource_exhausted = False
    disk_pressure = False
    disk_pressure_evidence: dict[str, object] = {
        "available": False,
        "pressure": False,
        "filesystems": {},
    }
    cuda_oom = False
    cuda_oom_evidence: dict[str, object] = {
        "available": False,
        "matched": False,
        "kind": None,
        "source_blob_sha": None,
        "expected_exit_code": None,
        "systemd_result": None,
        "systemd_exec_main_code": None,
        "systemd_exec_main_status": None,
    }
    execution_error: Exception | None = None
    residue_detected = False
    cleanup_pass = False
    gpu_residue_detected: list[dict[str, object]] = []
    leaked_gpu_processes: list[dict[str, object]] = []
    gpu_cleanup_pass = False
    runtime_post_verified = False
    runtime_post_error: str | None = None
    runtime_post: dict[str, Any] | None = None
    model_post_verified = model_pre is None
    model_post_error: str | None = None
    model_post: dict[str, Any] | None = None
    runner_workspace_destroyed = False
    staging_workspace_destroyed = False
    jit = request.jit_config

    try:
        with console_log.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert proc.stdin is not None
            assert proc.stdout is not None
            output_thread = threading.Thread(target=_pump, args=(proc.stdout, log), daemon=True)
            output_thread.start()
            proc.stdin.write(jit + "\n")
            proc.stdin.flush()
            proc.stdin.close()
            jit = ""
            rc, timed_out, wrapper_cleanup_pass = wait_for_transient_runner(
                proc,
                spec["unit_name"],
                int(spec["resources"]["runtime_max_seconds"]) + 120,
            )
            output_thread.join(timeout=10)
        if timed_out:
            terminal_status = "TIMED_OUT"
            execution_error = RuntimeTimeoutError(
                "runner exceeded root wrapper timeout "
                f"unit={spec['unit_name']}"
            )
        elif rc != 0:
            execution_error = RuntimeLaunchError(f"runner/systemd unit exited rc={rc}")
        else:
            result = "RUNNER_EXITED_CLEANLY"
            terminal_status = "SUCCEEDED"
    except Exception as exc:
        execution_error = exc
    finally:
        jit = ""

        if not timed_out and rc not in (None, 0):
            unit_terminal_evidence = transient_unit_terminal_evidence(
                spec["unit_name"]
            )
            if systemd_proves_runtime_timeout(unit_terminal_evidence):
                terminal_status = "TIMED_OUT"
                timed_out = True
                execution_error = RuntimeTimeoutError(
                    "systemd reported bounded runtime timeout "
                    f"unit={spec['unit_name']}"
                )
            elif systemd_proves_cpu_or_ram_exhaustion(unit_terminal_evidence):
                terminal_status = "CPU_OR_RAM_RESOURCE_EXHAUSTED"
                resource_exhausted = True
                execution_error = RuntimeResourceExhaustedError(
                    "systemd reported CPU/RAM resource exhaustion "
                    f"result={unit_terminal_evidence.get('result')} "
                    f"unit={spec['unit_name']}"
                )
            else:
                disk_pressure_evidence = filesystem_pressure_evidence(
                    {
                        "job": job_dir,
                        "staging": staging_dir,
                    }
                )
                if filesystem_proves_disk_pressure(disk_pressure_evidence):
                    terminal_status = "DISK_PRESSURE"
                    disk_pressure = True
                    execution_error = RuntimeDiskPressureError(
                        "root-owned filesystem evidence reported disk pressure "
                        f"unit={spec['unit_name']}"
                    )

        if (
            not timed_out
            and rc not in (None, 0)
            and not resource_exhausted
            and not disk_pressure
        ):
            cuda_oom_evidence = trusted_cuda_oom_probe_terminal_evidence(
                trusted_cuda_oom_probe,
                unit_terminal_evidence,
            )
            if cuda_oom_evidence.get("matched") is True:
                terminal_status = "CUDA_OOM"
                cuda_oom = True
                execution_error = RuntimeCudaOomError(
                    "root-bound trusted CUDA OOM probe reported allocation OOM "
                    f"unit={spec['unit_name']}"
                )

        try:
            gpu_residue_detected = project_gpu_processes(uid)
        except Exception as exc:
            gpu_residue_detected = [{"inspection_error": str(exc)}]

        residue_detected, cleanup_pass = cleanup_project_uid_processes(uid)

        try:
            leaked_gpu_processes = project_gpu_processes(uid)
        except Exception as exc:
            leaked_gpu_processes = [{"inspection_error": str(exc)}]
            gpu_cleanup_pass = False
        else:
            gpu_cleanup_pass = not leaked_gpu_processes

        try:
            runtime_post = verify_expanded_runtime_binding(spec)
        except Exception as exc:
            runtime_post_error = f"{type(exc).__name__}: {exc}"
        else:
            runtime_post_verified = True

        if model_pre is not None:
            try:
                model_post = verify_promoted_model_binding(spec)
            except Exception as exc:
                model_post_error = f"{type(exc).__name__}: {exc}"
                model_post_verified = False
            else:
                model_post_verified = True

        journal = run(
            ["journalctl", "-u", spec["unit_name"], "--no-pager", "-n", "1000"],
            check=False,
        )
        journal_log.write_text(
            journal.stdout + ("\n" + journal.stderr if journal.stderr else ""),
            encoding="utf-8",
        )

        diag = runner_dir / "_diag"
        if diag.is_dir():
            target = logs_root / f"p5-{request_id}-diag"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(diag, target, symlinks=True)

        runner_workspace_destroyed = remove_tree_and_verify(job_dir)
        staging_workspace_destroyed = remove_tree_and_verify(staging_dir)

        receipt = {
            "schema_version": 2,
            "phase": "P5-provisioner-runtime",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "decision": result,
            "terminal_status": terminal_status,
            "timed_out": timed_out,
            "wrapper_timeout_cleanup": wrapper_cleanup_pass,
            "automatic_retry_eligible": False,
            "resource_exhausted": resource_exhausted,
            "systemd_terminal_evidence": unit_terminal_evidence,
            "disk_pressure": disk_pressure,
            "disk_pressure_evidence": disk_pressure_evidence,
            "cuda_oom": cuda_oom,
            "cuda_oom_evidence": cuda_oom_evidence,
            "request_id": request_id,
            "project_id": spec["project_id"],
            "profile": spec["profile"],
            "runner_name": spec["runner_name"],
            "unit_name": spec["unit_name"],
            "runner_exit_code": rc,
            "project_uid_process_residue_detected": residue_detected,
            "project_uid_process_cleanup": cleanup_pass,
            "project_uid_gpu_process_residue_detected": gpu_residue_detected,
            "project_uid_gpu_process_cleanup": gpu_cleanup_pass,
            "leaked_gpu_processes": leaked_gpu_processes,
            "runner_workspace_destroyed": runner_workspace_destroyed,
            "staging_workspace_destroyed": staging_workspace_destroyed,
            "network_local_subnet_denied": subnet,
            "jit_config_persisted": False,
            "github_credential_present": False,
            "gpu_target_uuid": assignment["target_uuid"],
            "gpu_target_uuids": assignment["target_uuids"],
            "gpu_selected_device": assignment["selected_device"],
            "gpu_selected_devices": assignment["selected_devices"],
            "gpu_selected_minor": assignment["selected_minor"],
            "gpu_selected_minors": assignment["selected_minors"],
            "gpu_denied_devices": assignment["denied_devices"],
            "gpu_inventory": assignment["inventory"],
            "gpu_support_devices": assignment["support_devices"],
            "gpu_prelaunch_idle_verified": prelaunch_gpu_idle_verified,
            "gpu_prelaunch_processes": prelaunch_gpu_processes,
            "cuda_visible_devices": ",".join(assignment["target_uuids"]),
            "expanded_runtime_preverified": True,
            "expanded_runtime_postverified": runtime_post_verified,
            "expanded_runtime_postverify_error": runtime_post_error,
            "expanded_runtime": runtime_pre,
            "expanded_runtime_post": runtime_post,
            "promoted_model_preverified": model_pre is not None,
            "promoted_model_postverified": model_post_verified,
            "promoted_model_postverify_error": model_post_error,
            "promoted_model": model_pre,
            "promoted_model_post": model_post,
            "models": (
                spec["admission"].get("models", [])
                if isinstance(spec.get("admission"), dict)
                else []
            ),
            "runtime": (
                spec["admission"].get("runtime")
                if isinstance(spec.get("admission"), dict)
                else None
            ),
            "mutable_state_root": str(staging_dir),
            "persistent_project_home_writable": False,
        }
        receipt.update(admission_receipt_identity(spec))
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    cleanup_failures = []
    if not wrapper_cleanup_pass:
        cleanup_failures.append("timed-out systemd wrapper/unit did not terminate cleanly")
    if not cleanup_pass:
        cleanup_failures.append("project UID processes remain or could not be verified")
    if not gpu_cleanup_pass:
        cleanup_failures.append("GPU process residue remains or could not be verified")
    if not runtime_post_verified:
        cleanup_failures.append("expanded runtime post-verification failed")
    if model_pre is not None and not model_post_verified:
        cleanup_failures.append("promoted model post-verification failed")
    if not runner_workspace_destroyed:
        cleanup_failures.append("runner workspace removal failed")
    if not staging_workspace_destroyed:
        cleanup_failures.append("staging workspace removal failed")
    if cleanup_failures:
        raise RuntimeCleanupError("; ".join(cleanup_failures))
    if execution_error is not None:
        raise execution_error
    if result != "RUNNER_EXITED_CLEANLY":
        raise RuntimeLaunchError(f"GPU runner did not complete cleanly result={result}")
    return receipt

def launch_runner(request, spec: dict[str, Any]) -> dict[str, Any]:
    """Dispatch only explicitly bounded autonomous P5 workload/profile pairs."""
    profile = spec["profile"]
    if profile == "cpu-test":
        return launch_cpu_runner(request, spec)
    if profile == "gpu-small":
        return launch_gpu_runner(request, spec)
    if profile == "gpu-heavy" and spec.get("workload_class") == "model-eval-dual-gpu":
        return launch_gpu_runner(request, spec)
    raise RuntimeLaunchError(f"autonomous profile rejected: {profile}")
