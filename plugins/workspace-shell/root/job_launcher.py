#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path

from runtime_common import (
    ShellRuntimeError,
    bounded_run,
    fail,
    read_json_protected,
    sha256_hex,
    write_receipt,
)


REQUEST_LIMIT = 65536
RESPONSE_LIMIT = 1024 * 1024


def peer_credentials(conn):
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    return struct.unpack("3i", raw)


def safe_relative(value, field):
    if not isinstance(value, str) or not value or len(value) > 512 or "\x00" in value:
        fail("INVALID_PATH", f"{field} must be a bounded relative path")
    normalized = value.replace("\\", "/")
    p = Path(normalized)
    if p.is_absolute() or any(part == ".." for part in p.parts):
        fail("PATH_ESCAPE", f"{field} escapes workspace")
    return "." if normalized in (".", "./") else str(Path(normalized))


def validate_argv_shape(argv):
    if not isinstance(argv, list) or not (1 <= len(argv) <= 32):
        fail("INVALID_ARGV", "argv must contain 1..32 entries")
    total = 0
    for arg in argv:
        if not isinstance(arg, str) or len(arg) > 512 or any(ch in arg for ch in ("\x00", "\n", "\r")):
            fail("INVALID_ARGV", "argv entries must be bounded single-line strings without NUL")
        total += len(arg.encode("utf-8"))
    if total > 16384:
        fail("INVALID_ARGV", "argv exceeds v1 byte budget")


def validate_git_read(argv):
    exact = {
        ("rev-parse", "HEAD"),
        ("rev-parse", "HEAD^{tree}"),
        ("status", "--porcelain=v1", "--untracked-files=normal"),
        ("diff", "--name-status", "--no-ext-diff"),
        ("diff", "--stat", "--no-ext-diff"),
    }
    t = tuple(argv)
    if t in exact:
        return
    if len(argv) >= 4 and argv[:4] == ["diff", "--name-status", "--no-ext-diff", "--"]:
        for item in argv[4:]:
            safe_relative(item, "git path")
        return
    fail("PROFILE_ARGV_DENIED", "git-read argv is outside frozen grammar")


def validate_pytest(argv):
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-q", "-x", "--disable-warnings"):
            i += 1
            continue
        if arg.startswith("--maxfail=") and arg.split("=", 1)[1].isdigit() and 1 <= int(arg.split("=", 1)[1]) <= 99:
            i += 1
            continue
        if arg == "-k":
            i += 1
            if i >= len(argv) or not argv[i] or len(argv[i]) > 160:
                fail("PROFILE_ARGV_DENIED", "-k requires bounded expression")
            i += 1
            continue
        p = safe_relative(arg, "pytest path").replace("\\", "/")
        if not (
            p == "tests"
            or p.startswith("tests/")
            or p == "plugins/workspace-shell/test"
            or p.startswith("plugins/workspace-shell/test/")
        ):
            fail("PROFILE_ARGV_DENIED", "pytest-bounded may address only repository test paths")
        i += 1


def validate_workspace_control(argv):
    if not argv or argv[0] not in ("task-validate", "workflow-validate"):
        fail("PROFILE_ARGV_DENIED", "validation-bounded exposes only task-validate/workflow-validate")
    allowed = {"--file", "--profile", "--json"}
    i = 1
    while i < len(argv):
        flag = argv[i]
        if flag not in allowed:
            fail("PROFILE_ARGV_DENIED", f"unsupported validation flag {flag}")
        if flag == "--json":
            i += 1
            continue
        i += 1
        if i >= len(argv):
            fail("PROFILE_ARGV_DENIED", f"{flag} requires value")
        safe_relative(argv[i], flag)
        i += 1


def resolve_profile(manifest, profile, argv):
    validate_argv_shape(argv)
    entry = manifest.get("profiles", {}).get(profile)
    if not entry:
        fail("PROFILE_NOT_AUTHORIZED", "profile absent from root-owned manifest")

    expected = {
        "git-read": ("/usr/bin/git", False),
        "pytest-bounded": ("/usr/bin/python3", True),
        "validation-bounded": ("/usr/bin/python3", True),
    }
    if profile not in expected:
        fail("PROFILE_NOT_AUTHORIZED", "profile absent from frozen launcher grammar")
    if (entry.get("executable"), bool(entry.get("write_scratch"))) != expected[profile]:
        fail("PROFILE_MANIFEST_MISMATCH", "root-owned profile manifest differs from frozen grammar")
    if entry.get("network") != "deny":
        fail("PROFILE_MANIFEST_MISMATCH", "v1 profiles must deny network")

    if profile == "git-read":
        validate_git_read(argv)
        resolved = argv
        env = {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    elif profile == "pytest-bounded":
        validate_pytest(argv)
        resolved = ["-m", "pytest", *argv]
        env = {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    else:
        validate_workspace_control(argv)
        resolved = ["scripts/workspace_control.py", *argv]
        env = {"PYTHONDONTWRITEBYTECODE": "1"}

    return {
        "executable": entry["executable"],
        "argv": resolved,
        "write_scratch": bool(entry["write_scratch"]),
        "max_timeout_ms": min(int(entry.get("max_timeout_ms", 90000)), 90000),
        "env": env,
    }


def hardened_git(source_root, args):
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    proc = subprocess.run(
        ["/usr/bin/git", "-C", str(source_root), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=3,
        close_fds=True,
        text=True,
    )
    if proc.returncode != 0:
        fail("SOURCE_GIT_FAILED", proc.stderr.strip() or "git inspection failed")
    return proc.stdout.strip()


def verify_source_tree(source_root, worker_uid):
    source_root = Path(source_root).resolve()
    if not source_root.is_dir():
        fail("SOURCE_ROOT_INVALID", "configured source root missing")
    for root, dirs, files in os.walk(source_root, followlinks=False):
        for name in dirs + files:
            p = Path(root) / name
            st = os.lstat(p)
            if stat.S_ISSOCK(st.st_mode) or stat.S_ISFIFO(st.st_mode) or stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode):
                fail("SOURCE_SPECIAL_FILE_DENIED", f"special file in source: {p}")
            if st.st_mode & 0o022:
                fail("SOURCE_WRITABLE_BY_UNTRUSTED", f"group/world-writable source entry: {p}")
            if st.st_uid == worker_uid and st.st_mode & 0o200:
                fail("SOURCE_WRITABLE_BY_WORKER", f"worker owns writable source entry: {p}")
    return source_root


def chown_tree(root, uid, gid):
    for current, dirs, files in os.walk(root, topdown=False, followlinks=False):
        for name in files + dirs:
            p = Path(current) / name
            try:
                os.lchown(p, uid, gid)
            except FileNotFoundError:
                pass
    os.lchown(root, uid, gid)


def build_bwrap_command(cfg, workspace_path, cwd, resolved):
    bwrap = cfg.get("bwrap_path", "/usr/bin/bwrap")
    if not Path(bwrap).is_file():
        fail("SANDBOX_BACKEND_MISSING", f"required bubblewrap binary missing: {bwrap}")

    cmd = [
        bwrap,
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        "--cap-drop",
        "ALL",
        "--clearenv",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/home",
        "--dir",
        "/home/worker",
        "--bind" if resolved["write_scratch"] else "--ro-bind",
        str(workspace_path),
        "/workspace",
        "--chdir",
        "/workspace" if cwd == "." else f"/workspace/{cwd}",
    ]
    for host_path in ("/usr", "/bin", "/lib", "/lib64"):
        if Path(host_path).exists():
            cmd.extend(["--ro-bind", host_path, host_path])
    cmd.extend(["--setenv", "HOME", "/home/worker"])
    cmd.extend(["--setenv", "PATH", "/usr/bin:/bin"])
    cmd.extend(["--setenv", "LANG", "C.UTF-8", "--setenv", "LC_ALL", "C.UTF-8", "--setenv", "TZ", "UTC"])
    for key, value in resolved["env"].items():
        cmd.extend(["--setenv", key, value])
    cmd.extend(["--", resolved["executable"], *resolved["argv"]])
    return cmd


def build_systemd_run_command(cfg, unit, bwrap_cmd, worker_uid, worker_gid, scratch_path):
    systemd_run = cfg.get("systemd_run_path", "/usr/bin/systemd-run")
    if not Path(systemd_run).is_file():
        fail("CGROUP_BACKEND_MISSING", f"required systemd-run missing: {systemd_run}")
    props = [
        "NoNewPrivileges=yes",
        "PrivateNetwork=yes",
        "PrivateDevices=yes",
        "ProtectHome=yes",
        "ProtectProc=invisible",
        "ProcSubset=pid",
        "RestrictSUIDSGID=yes",
        "CapabilityBoundingSet=",
        "TasksMax=48",
        "MemoryMax=1G",
        "KillMode=control-group",
        "TimeoutStopSec=2s",
        "UMask=0077",
    ]
    cmd = [
        systemd_run,
        "--quiet",
        "--wait",
        "--pipe",
        "--collect",
        f"--unit={unit}",
        f"--uid={worker_uid}",
        f"--gid={worker_gid}",
    ]
    for prop in props:
        cmd.append(f"--property={prop}")
    if scratch_path is not None:
        cmd.append(f"--property=ReadWritePaths={scratch_path}")
    cmd.extend(["--", *bwrap_cmd])
    return cmd


def unit_killer(cfg, unit):
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


def cleanup_state(cfg, unit):
    systemctl = cfg.get("systemctl_path", "/usr/bin/systemctl")
    proc = subprocess.run(
        [systemctl, "show", unit, "--property=ActiveState", "--value"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=2,
        close_fds=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
    )
    if proc.returncode != 0:
        return "unit-not-found-or-collected"
    state = proc.stdout.strip()
    return f"active-state:{state}"


def decode_output(data):
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "[non-UTF8 output omitted]"


def run_request(cfg, manifest, request):
    if request.get("schema") != "workspace-shell-job-request.v1":
        fail("JOB_SCHEMA_INVALID", "unexpected job request schema")
    if request.get("operation") != "exec":
        fail("JOB_OPERATION_DENIED", "v1 launcher accepts exec only")
    if request.get("target") != "workspace-control":
        fail("TARGET_NOT_AUTHORIZED", "v1 launcher target is workspace-control only")

    expected_sha = request.get("expected_sha")
    if not isinstance(expected_sha, str) or not expected_sha.islower() or len(expected_sha) != 40 or any(c not in "0123456789abcdef" for c in expected_sha):
        fail("INVALID_SHA", "expected_sha must be full lowercase Git SHA")

    profile = request.get("profile")
    resolved = resolve_profile(manifest, profile, request.get("argv"))
    cwd = safe_relative(request.get("cwd"), "cwd")
    timeout_ms = int(request.get("timeout_ms"))
    if not 1000 <= timeout_ms <= resolved["max_timeout_ms"]:
        fail("TIMEOUT_DENIED", "timeout exceeds profile ceiling")

    source_root = cfg.get("source_roots", {}).get(request["target"])
    if not isinstance(source_root, str):
        fail("SOURCE_ROOT_UNTRUSTED", "target source root is not pinned by launcher config")
    worker_uid = int(cfg["worker_uid"])
    worker_gid = int(cfg["worker_gid"])
    source_root = verify_source_tree(source_root, worker_uid)

    observed_sha = hardened_git(source_root, ["rev-parse", "HEAD"])
    if observed_sha != expected_sha:
        fail("SOURCE_SHA_MISMATCH", "observed source HEAD differs from expected_sha")

    receipt_id = f"job-{uuid.uuid4()}"
    scratch_root = Path(cfg["scratch_root"])
    scratch_root.mkdir(parents=True, exist_ok=True)
    job_root = scratch_root / receipt_id
    workspace_path = source_root
    scratch_path = None

    if resolved["write_scratch"]:
        job_root.mkdir(mode=0o700)
        workspace_path = job_root / "workspace"
        shutil.copytree(source_root, workspace_path, symlinks=True)
        chown_tree(job_root, worker_uid, worker_gid)
        scratch_path = job_root

    unit = f"workspace-shell-job-{receipt_id[4:20]}"
    bwrap_cmd = build_bwrap_command(cfg, workspace_path, cwd, resolved)
    command = build_systemd_run_command(cfg, unit, bwrap_cmd, worker_uid, worker_gid, scratch_path)

    started = time.time()
    result = bounded_run(
        command,
        cwd="/",
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC"},
        timeout_s=timeout_ms / 1000.0,
        stdout_limit=65536,
        stderr_limit=65536,
        kill_callback=unit_killer(cfg, unit),
    )
    cleanup = cleanup_state(cfg, unit)

    receipt = {
        "schema": "workspace-shell-receipt.v1",
        "receipt_id": receipt_id,
        "request_id": request.get("request_id"),
        "task_id": request.get("task_id"),
        "caller_id": "workspace-shell-mcp",
        "tool_name": "workspace_shell.exec",
        "target": request.get("target"),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "policy_version_sha": cfg.get("policy_version_sha"),
        "review_approval_sha": None,
        "expected_git_sha": expected_sha,
        "observed_git_sha": observed_sha,
        "argv_profile": profile,
        "argv_hash": sha256_hex(json.dumps(request.get("argv"), separators=(",", ":"), ensure_ascii=False)),
        "redacted_argv": request.get("argv"),
        "cwd_policy_path": cwd,
        "timeout_ms": timeout_ms,
        "started_at": started,
        "finished_at": time.time(),
        "duration_ms": result["duration_ms"],
        "exit_code": result["exit_code"],
        "signal": result["signal"],
        "stdout_bytes_seen": result["stdout_bytes_seen"],
        "stderr_bytes_seen": result["stderr_bytes_seen"],
        "stdout_sha256": result["stdout_sha256"],
        "stderr_sha256": result["stderr_sha256"],
        "stdout_truncated": result["stdout_truncated"],
        "stderr_truncated": result["stderr_truncated"],
        "privileged": False,
        "operation": "exec",
        "helper_receipt_id": None,
        "cgroup_cleanup_status": cleanup,
        "authorization_decision": "ALLOW",
        "timed_out": result["timed_out"],
    }
    stored = write_receipt(cfg["receipt_root"], receipt)

    if scratch_path is not None:
        shutil.rmtree(scratch_path, ignore_errors=True)

    return {
        "ok": True,
        "receipt_id": receipt_id,
        "exit_code": result["exit_code"],
        "signal": result["signal"],
        "timed_out": result["timed_out"],
        "stdout": decode_output(result["stdout"]),
        "stderr": decode_output(result["stderr"]),
        "stdout_bytes_seen": result["stdout_bytes_seen"],
        "stderr_bytes_seen": result["stderr_bytes_seen"],
        "stdout_truncated": result["stdout_truncated"],
        "stderr_truncated": result["stderr_truncated"],
        "stdout_sha256": stored.get("stdout_sha256"),
        "stderr_sha256": stored.get("stderr_sha256"),
        "cgroup_cleanup_status": cleanup,
    }


def rejection_receipt(cfg, request, code, message, peer_uid):
    receipt_id = f"reject-{uuid.uuid4()}"
    task_id = request.get("task_id") if isinstance(request, dict) else None
    receipt = {
        "schema": "workspace-shell-receipt.v1",
        "receipt_id": receipt_id,
        "request_id": request.get("request_id") if isinstance(request, dict) else None,
        "task_id": task_id or "unknown",
        "caller_id": f"uid:{peer_uid}",
        "tool_name": "workspace_shell.exec",
        "target": request.get("target") if isinstance(request, dict) else None,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy_version_sha": cfg.get("policy_version_sha"),
        "privileged": False,
        "operation": "exec",
        "authorization_decision": "DENY",
        "authorization_reason": f"{code}: {message}",
    }
    try:
        return write_receipt(cfg["receipt_root"], receipt)["receipt_id"]
    except Exception:
        return None


def serve(config_path):
    if os.geteuid() != 0:
        fail("ROOT_REQUIRED", "job launcher must run as root")
    cfg = read_json_protected(config_path)
    if int(cfg["frontend_uid"]) == int(cfg["worker_uid"]):
        fail("IDENTITY_COLLAPSE", "frontend_uid and worker_uid must be distinct")
    manifest = read_json_protected(cfg["profile_manifest"])
    if manifest.get("schema_version") != 1 or manifest.get("grammar_version") != "workspace-shell-profile-grammar.v1":
        fail("PROFILE_MANIFEST_INVALID", "unexpected profile manifest schema/grammar")

    socket_path = Path(cfg["socket_path"])
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        st = socket_path.lstat()
        if not stat.S_ISSOCK(st.st_mode):
            fail("SOCKET_PATH_COLLISION", "launcher socket path exists and is not a socket")
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
                    if uid != int(cfg["frontend_uid"]):
                        fail("PEER_UID_DENIED", "job launcher accepts workspace-shell-mcp UID only")
                    raw = bytearray()
                    while b"\n" not in raw:
                        chunk = conn.recv(8192)
                        if not chunk:
                            break
                        raw.extend(chunk)
                        if len(raw) > REQUEST_LIMIT:
                            fail("REQUEST_TOO_LARGE", "launcher request exceeds 64 KiB")
                    line = bytes(raw).split(b"\n", 1)[0]
                    request = json.loads(line.decode("utf-8"))
                    response = run_request(cfg, manifest, request)
                except Exception as exc:
                    code = exc.code if isinstance(exc, ShellRuntimeError) else "JOB_LAUNCH_FAILED"
                    message = str(exc)
                    receipt_id = rejection_receipt(cfg, request, code, message, uid)
                    response = {"ok": False, "error": {"code": code, "message": message}, "receipt_id": receipt_id}
                data = json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
                if len(data) > RESPONSE_LIMIT:
                    data = b'{"ok":false,"error":{"code":"RESPONSE_TOO_LARGE","message":"launcher response exceeded bound"}}\n'
                conn.sendall(data)
    finally:
        server.close()
        try:
            socket_path.unlink()
        except FileNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/etc/workspace-shell/job-launcher.json")
    args = parser.parse_args()
    serve(args.config)


if __name__ == "__main__":
    main()
