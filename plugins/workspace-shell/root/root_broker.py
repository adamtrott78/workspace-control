#!/usr/bin/env python3
import argparse
import errno
import hashlib
import json
import os
import select
import signal
import socket
import sqlite3
import stat
import struct
import subprocess
import time
import uuid
from pathlib import Path

from runtime_common import (
    ShellRuntimeError,
    bounded_run,
    canonical_json_bytes,
    fail,
    read_json_protected,
    require_protected_path,
    require_secure_directory,
    sha256_hex,
    write_receipt,
)


REQUEST_LIMIT = 65536
RESPONSE_LIMIT = 1024 * 1024


def peer_credentials(conn):
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    return struct.unpack("3i", raw)


def verify_request(cfg, raw_request):
    verifier = cfg["verifier_script"]
    require_protected_path(verifier)
    node = cfg.get("node_path", "/usr/bin/node")
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
    }
    proc = subprocess.run(
        [node, verifier, cfg["verifier_config"]],
        input=raw_request,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        close_fds=True,
        env=env,
    )
    if len(proc.stdout) > 262144:
        fail("VERIFIER_RESPONSE_TOO_LARGE", "broker verifier response exceeded bound")
    try:
        result = json.loads(proc.stdout.decode("utf-8"))
    except Exception:
        fail("VERIFIER_RESPONSE_INVALID", "broker verifier did not return valid JSON")
    if not result.get("ok"):
        error = result.get("error") or {}
        fail(error.get("code", "BROKER_VERIFY_REJECTED"), error.get("message", "broker verification rejected"))
    return result


def ensure_replay_db(cfg, *, expected_owner_uid=0):
    db_path = Path(cfg["replay_db"])
    require_secure_directory(db_path.parent, owner_uid=expected_owner_uid)
    conn = sqlite3.connect(db_path, timeout=5, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consumed (
              approval_id TEXT PRIMARY KEY,
              nonce TEXT NOT NULL UNIQUE,
              idempotency_key TEXT NOT NULL UNIQUE,
              consumed_at TEXT NOT NULL
            )
            """
        )
    finally:
        conn.close()
    os.chmod(db_path, 0o600)
    return db_path


def consume_replay(db_path, verified):
    conn = sqlite3.connect(db_path, timeout=5, isolation_level=None)
    try:
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                "INSERT INTO consumed(approval_id,nonce,idempotency_key,consumed_at) VALUES(?,?,?,?)",
                (
                    verified["approval_id"],
                    verified["nonce"],
                    verified["idempotency_key"],
                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                ),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            fail("APPROVAL_REPLAY", "approval_id, nonce, or idempotency key was already consumed")
    finally:
        conn.close()


def open_verified_helper(path, expected_sha256):
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            fail("HELPER_NOT_REGULAR", "verified helper is not a regular file")
        h = hashlib.sha256()
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            h.update(chunk)
        observed = h.hexdigest()
        if observed != expected_sha256:
            fail("HELPER_TOCTOU_DIGEST_MISMATCH", "helper digest changed after broker verification")
        os.lseek(fd, 0, os.SEEK_SET)
        return fd
    except Exception:
        os.close(fd)
        raise


def decode_output(data):
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "[non-UTF8 output omitted]"


def stage_verified_helper(cfg, verified):
    cache_root = require_secure_directory(cfg["helper_cache_root"], owner_uid=0)
    digest = verified["helper_sha256"]
    target = cache_root / f"{digest}.helper"

    if os.path.lexists(target):
        st = os.lstat(target)
        if not stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
            fail("HELPER_CACHE_INVALID", "cached helper is not a regular non-symlink file")
        if st.st_uid != 0 or st.st_mode & 0o222:
            fail("HELPER_CACHE_MODE", "cached helper must be root-owned and immutable")
        observed = sha256_hex(target.read_bytes())
        if observed != digest:
            fail("HELPER_CACHE_DIGEST_MISMATCH", "cached helper digest mismatch")
        return target

    source_fd = open_verified_helper(verified["helper_path"], digest)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        try:
            target_fd = os.open(target, flags, 0o500)
        except FileExistsError:
            os.close(source_fd)
            return stage_verified_helper(cfg, verified)

        try:
            while True:
                chunk = os.read(source_fd, 65536)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    written = os.write(target_fd, view)
                    view = view[written:]
            os.fsync(target_fd)
        finally:
            os.close(target_fd)

        os.chmod(target, 0o500)
        observed = sha256_hex(target.read_bytes())
        if observed != digest:
            try:
                target.unlink()
            finally:
                fail("HELPER_CACHE_DIGEST_MISMATCH", "staged helper digest mismatch")
        dirfd = os.open(cache_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
        return target
    finally:
        try:
            os.close(source_fd)
        except OSError:
            pass


def build_helper_systemd_command(cfg, unit, helper_path, verified):
    systemd_run = cfg.get("systemd_run_path", "/usr/bin/systemd-run")
    if not Path(systemd_run).is_file():
        fail("CGROUP_BACKEND_MISSING", f"required systemd-run missing: {systemd_run}")

    confinement = verified.get("confinement") or {}
    capabilities = confinement.get("capabilities") or []
    read_write_paths = confinement.get("read_write_paths") or []
    network = confinement.get("network", "deny")

    props = [
        "NoNewPrivileges=yes",
        "PrivateDevices=yes",
        "PrivateTmp=yes",
        "ProtectHome=yes",
        "ProtectSystem=strict",
        "ProtectKernelLogs=yes",
        "ProtectKernelModules=yes",
        "ProtectKernelTunables=yes",
        "ProtectControlGroups=yes",
        "RestrictSUIDSGID=yes",
        "KillMode=control-group",
        "ExitType=cgroup",
        "TimeoutStopSec=2s",
        "TasksMax=64",
        "MemoryMax=1G",
        "UMask=0077",
        "CapabilityBoundingSet=" + " ".join(capabilities),
    ]
    if network == "deny":
        props.append("PrivateNetwork=yes")
    elif network != "host-reviewed":
        fail("HELPER_CONFINEMENT_INVALID", "unknown helper network confinement")

    if read_write_paths:
        props.append("ReadWritePaths=" + " ".join(read_write_paths))

    env_args = [
        "/usr/bin/env",
        "-i",
        "PATH=/usr/bin:/bin",
        "LANG=C.UTF-8",
        "LC_ALL=C.UTF-8",
        "TZ=UTC",
        "HOME=/var/empty",
        f"WORKSPACE_SHELL_TASK_ID={verified['task_id']}",
        f"WORKSPACE_SHELL_TARGET={verified['target']}",
        f"WORKSPACE_SHELL_EXPECTED_SHA={verified['expected_source_commit']}",
        f"WORKSPACE_SHELL_APPROVAL_ID={verified['approval_id']}",
        f"WORKSPACE_SHELL_OPERATION={verified['operation']}",
        str(helper_path),
    ]

    command = [
        systemd_run,
        "--quiet",
        "--wait",
        "--pipe",
        "--collect",
        f"--unit={unit}",
    ]
    for prop in props:
        command.append(f"--property={prop}")
    command.extend(["--", *env_args])
    return command


def helper_unit_killer(cfg, unit):
    systemctl = cfg.get("systemctl_path", "/usr/bin/systemctl")

    def kill(sig):
        name = "TERM" if sig == signal.SIGTERM else "KILL"
        subprocess.run(
            [systemctl, "kill", f"--signal={name}", "--kill-whom=all", unit],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            close_fds=True,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )

    return kill


def helper_unit_state(cfg, unit):
    systemctl = cfg.get("systemctl_path", "/usr/bin/systemctl")
    proc = subprocess.run(
        [
            systemctl,
            "show",
            unit,
            "--property=ActiveState",
            "--property=ControlGroup",
            "--no-pager",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        close_fds=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
    )
    if proc.returncode != 0:
        return None
    values = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def helper_cgroup_pids(control_group):
    if not control_group:
        return []
    base = Path("/sys/fs/cgroup").resolve()
    candidate = (base / control_group.lstrip("/")).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        fail("CGROUP_PATH_ESCAPE", "systemd returned helper cgroup outside cgroup root")
    try:
        return [
            line.strip()
            for line in (candidate / "cgroup.procs").read_text().splitlines()
            if line.strip()
        ]
    except FileNotFoundError:
        return []


def cleanup_helper_unit(cfg, unit):
    killer = helper_unit_killer(cfg, unit)
    observed = helper_unit_state(cfg, unit)
    if observed is None:
        return "COLLECTED"

    if observed.get("ActiveState") not in {"inactive", "failed"} or helper_cgroup_pids(observed.get("ControlGroup")):
        killer(signal.SIGTERM)
        time.sleep(0.1)
        observed = helper_unit_state(cfg, unit)
        if observed is not None and (
            observed.get("ActiveState") not in {"inactive", "failed"}
            or helper_cgroup_pids(observed.get("ControlGroup"))
        ):
            killer(signal.SIGKILL)

    deadline = time.monotonic() + 2.0
    last = None
    while time.monotonic() < deadline:
        observed = helper_unit_state(cfg, unit)
        if observed is None:
            return "COLLECTED"
        last = observed
        pids = helper_cgroup_pids(observed.get("ControlGroup"))
        if observed.get("ActiveState") in {"inactive", "failed"} and not pids:
            return "EMPTY"
        time.sleep(0.02)

    fail(
        "CGROUP_CLEANUP_FAILED",
        f"privileged helper unit {unit} retained state={(last or {}).get('ActiveState')} pids={helper_cgroup_pids((last or {}).get('ControlGroup'))}",
    )


def peer_disconnected(conn):
    try:
        readable, _, exceptional = select.select([conn], [], [conn], 0)
        if exceptional:
            return True
        if not readable:
            return False
        try:
            data = conn.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
            return data == b""
        except BlockingIOError:
            return False
        except (ConnectionResetError, BrokenPipeError):
            return True
    except OSError:
        return True


def execute_helper(cfg, verified, cancel_check=None):
    helper_path = stage_verified_helper(cfg, verified)
    params = canonical_json_bytes(verified["parameters"]) + b"\n"
    unit = f"workspace-shell-helper-{sha256_hex(verified['approval_id'])[:16]}"
    command = build_helper_systemd_command(cfg, unit, helper_path, verified)
    result = bounded_run(
        command,
        cwd="/",
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"},
        timeout_s=min(float(verified["timeout_ms"]) / 1000.0, 90.0),
        stdout_limit=65536,
        stderr_limit=65536,
        stdin_bytes=params,
        kill_callback=helper_unit_killer(cfg, unit),
        cancel_check=cancel_check,
    )
    result["cgroup_cleanup_status"] = cleanup_helper_unit(cfg, unit)
    return result

def success_receipt(cfg, verified, peer_uid, result, request):
    now = time.time()
    receipt_id = f"priv-{uuid.uuid4()}"
    receipt = {
        "schema": "workspace-shell-receipt.v1",
        "receipt_id": receipt_id,
        "request_id": request.get("frontend_request", {}).get("payload", {}).get("request_id"),
        "task_id": verified["task_id"],
        "caller_id": "workspace-shell-mcp",
        "tool_name": "workspace_shell.run_reviewed_helper",
        "target": verified["target"],
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "policy_version_sha": cfg.get("policy_version_sha"),
        "review_approval_sha": verified["design_authority_sha"],
        "expected_git_sha": verified["expected_source_commit"],
        "observed_git_sha": verified["expected_source_commit"],
        "argv_profile": None,
        "argv_hash": None,
        "redacted_argv": None,
        "cwd_policy_path": None,
        "timeout_ms": verified["timeout_ms"],
        "started_at": now - (result["duration_ms"] / 1000.0),
        "finished_at": now,
        "duration_ms": result["duration_ms"],
        "exit_code": result["exit_code"],
        "signal": result["signal"],
        "stdout_bytes_seen": result["stdout_bytes_seen"],
        "stderr_bytes_seen": result["stderr_bytes_seen"],
        "stdout_sha256": result["stdout_sha256"],
        "stderr_sha256": result["stderr_sha256"],
        "stdout_truncated": result["stdout_truncated"],
        "stderr_truncated": result["stderr_truncated"],
        "privileged": True,
        "operation": verified["operation"],
        "helper_receipt_id": None,
        "cgroup_cleanup_status": result["cgroup_cleanup_status"],
        "authorization_decision": "ALLOW",
        "approval_id": verified["approval_id"],
        "approval_issuer_key_id": request.get("approval", {}).get("payload", {}).get("issuer_key_id"),
        "approval_design_head_sha": verified["design_authority_sha"],
        "approval_review_record_id": verified["design_review_record_id"],
        "approval_expires_at": request.get("approval", {}).get("payload", {}).get("expires_at"),
        "approval_signature_verified": True,
        "approval_revocation_checked": True,
        "approval_replay_state": "CONSUMED_BEFORE_MUTATION",
        "frontend_peer_uid": peer_uid,
        "frontend_request_signature_verified": True,
        "helper_id": verified["helper_id"],
        "helper_sha256": verified["helper_sha256"],
        "helper_review_record_id": verified["helper_review_record_id"],
        "expected_source_tree": verified["expected_source_tree"],
        "parameter_digest_sha256": verified["parameter_digest_sha256"],
        "timed_out": result["timed_out"],
        "cancelled": result["cancelled"],
    }
    return write_receipt(
        cfg["receipt_root"],
        receipt,
        reader_gid=int(cfg["frontend_gid"]),
    )


def rejection_receipt(cfg, request, peer_uid, code, message):
    receipt_id = f"reject-{uuid.uuid4()}"
    payload = request.get("approval", {}).get("payload", {}) if isinstance(request, dict) else {}
    frontend = request.get("frontend_request", {}).get("payload", {}) if isinstance(request, dict) else {}
    receipt = {
        "schema": "workspace-shell-receipt.v1",
        "receipt_id": receipt_id,
        "request_id": frontend.get("request_id"),
        "task_id": frontend.get("task_id") or payload.get("task_id") or "unknown",
        "caller_id": f"uid:{peer_uid}",
        "tool_name": "workspace_shell.run_reviewed_helper",
        "target": frontend.get("target") or payload.get("target"),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy_version_sha": cfg.get("policy_version_sha"),
        "privileged": True,
        "operation": payload.get("operation"),
        "authorization_decision": "DENY",
        "authorization_reason": f"{code}: {message}",
        "approval_id": payload.get("approval_id"),
        "frontend_peer_uid": peer_uid,
    }
    try:
        return write_receipt(
            cfg["receipt_root"],
            receipt,
            reader_gid=int(cfg["frontend_gid"]),
        )["receipt_id"]
    except Exception:
        return None


def handle_request(cfg, replay_db, raw, peer_uid, cancel_check=None):
    if peer_uid != int(cfg["frontend_uid"]):
        fail("PEER_UID_DENIED", "root broker accepts workspace-shell-mcp UID only")
    if len(raw) > REQUEST_LIMIT:
        fail("REQUEST_TOO_LARGE", "broker request exceeds 64 KiB")
    request = json.loads(raw.decode("utf-8"))
    verified = verify_request(cfg, raw)
    if cancel_check is not None and cancel_check():
        fail("CONTROL_CANCELLED", "frontend disconnected before privileged approval consumption")
    consume_replay(replay_db, verified)
    result = execute_helper(cfg, verified, cancel_check=cancel_check)
    receipt = success_receipt(cfg, verified, peer_uid, result, request)
    return {
        "ok": True,
        "receipt_id": receipt["receipt_id"],
        "exit_code": result["exit_code"],
        "signal": result["signal"],
        "timed_out": result["timed_out"],
        "cancelled": result["cancelled"],
        "stdout": decode_output(result["stdout"]),
        "stderr": decode_output(result["stderr"]),
        "stdout_bytes_seen": result["stdout_bytes_seen"],
        "stderr_bytes_seen": result["stderr_bytes_seen"],
        "stdout_truncated": result["stdout_truncated"],
        "stderr_truncated": result["stderr_truncated"],
        "stdout_sha256": result["stdout_sha256"],
        "stderr_sha256": result["stderr_sha256"],
    }


def serve(config_path):
    if os.geteuid() != 0:
        fail("ROOT_REQUIRED", "root broker must run as root")
    cfg = read_json_protected(config_path)
    cfg["verifier_config"] = str(Path(cfg["verifier_config"]).resolve())
    require_protected_path(cfg["verifier_config"])
    require_secure_directory(Path(cfg["replay_db"]).parent, owner_uid=0)
    require_secure_directory(
        cfg["receipt_root"],
        owner_uid=0,
        owner_gid=int(cfg["frontend_gid"]),
    )
    require_secure_directory(cfg["helper_cache_root"], owner_uid=0)
    replay_db = ensure_replay_db(cfg)

    socket_path = Path(cfg["socket_path"])
    require_secure_directory(socket_path.parent, owner_uid=0)
    if socket_path.exists():
        st = socket_path.lstat()
        if not stat.S_ISSOCK(st.st_mode):
            fail("SOCKET_PATH_COLLISION", "broker socket path exists and is not a socket")
        socket_path.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(socket_path))
    os.chown(socket_path, 0, int(cfg["frontend_gid"]))
    os.chmod(socket_path, 0o660)
    server.listen(8)

    try:
        while True:
            conn, _ = server.accept()
            with conn:
                pid, uid, gid = peer_credentials(conn)
                request = {}
                try:
                    raw = bytearray()
                    while b"\n" not in raw:
                        chunk = conn.recv(8192)
                        if not chunk:
                            break
                        raw.extend(chunk)
                        if len(raw) > REQUEST_LIMIT:
                            fail("REQUEST_TOO_LARGE", "broker request exceeds 64 KiB")
                    line = bytes(raw).split(b"\n", 1)[0]
                    try:
                        request = json.loads(line.decode("utf-8"))
                    except Exception:
                        request = {}
                    response = handle_request(
                        cfg,
                        replay_db,
                        line,
                        uid,
                        cancel_check=lambda: peer_disconnected(conn),
                    )
                except Exception as exc:
                    code = exc.code if isinstance(exc, ShellRuntimeError) else "ROOT_BROKER_FAILED"
                    message = str(exc)
                    receipt_id = rejection_receipt(cfg, request, uid, code, message)
                    response = {"ok": False, "error": {"code": code, "message": message}, "receipt_id": receipt_id}
                data = json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
                if len(data) > RESPONSE_LIMIT:
                    data = b'{"ok":false,"error":{"code":"RESPONSE_TOO_LARGE","message":"broker response exceeded bound"}}\n'
                try:
                    conn.sendall(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass
    finally:
        server.close()
        try:
            socket_path.unlink()
        except FileNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/etc/workspace-shell/root-broker.json")
    args = parser.parse_args()
    serve(args.config)


if __name__ == "__main__":
    main()
