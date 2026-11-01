#!/usr/bin/env python3
import fcntl
import hashlib
import json
import os
import selectors
import signal
import stat
import subprocess
import tempfile
import time
from pathlib import Path


class ShellRuntimeError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


def fail(code, message):
    raise ShellRuntimeError(code, message)


def canonical_json_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_json_protected(path, *, require_root=True):
    p = Path(path)
    st = p.stat()
    if not stat.S_ISREG(st.st_mode):
        fail("TRUST_FILE_INVALID", f"{p} is not a regular file")
    if require_root:
        if st.st_uid != 0:
            fail("TRUST_FILE_OWNER", f"{p} must be root-owned")
        if st.st_mode & 0o022:
            fail("TRUST_FILE_MODE", f"{p} must not be group/world writable")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        fail("TRUST_FILE_PARSE", f"could not parse {p}: {exc}")


def require_protected_path(path, *, require_root=True, regular=True):
    p = Path(path)
    st = p.stat()
    if regular and not stat.S_ISREG(st.st_mode):
        fail("PROTECTED_PATH_TYPE", f"{p} must be a regular file")
    if require_root:
        if st.st_uid != 0:
            fail("PROTECTED_PATH_OWNER", f"{p} must be root-owned")
        if st.st_mode & 0o022:
            fail("PROTECTED_PATH_MODE", f"{p} must not be group/world writable")
    return st


def require_secure_directory(path, *, owner_uid=0, owner_gid=None):
    p = Path(path)
    st = os.lstat(p)
    if not stat.S_ISDIR(st.st_mode):
        fail("SECURE_DIR_TYPE", f"{p} must be a real directory")
    if st.st_uid != owner_uid:
        fail("SECURE_DIR_OWNER", f"{p} must be owned by uid {owner_uid}")
    if owner_gid is not None and st.st_gid != owner_gid:
        fail("SECURE_DIR_GROUP", f"{p} must be owned by gid {owner_gid}")
    if st.st_mode & 0o022:
        fail("SECURE_DIR_MODE", f"{p} must not be group/world writable")
    return p


def _atomic_write(path, data, mode=0o600, *, group_gid=None):
    path = Path(path)
    parent = path.parent
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(parent))
    try:
        os.fchmod(fd, mode)
        if group_gid is not None:
            os.fchown(fd, -1, int(group_gid))
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        dirfd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def write_receipt(receipt_root, receipt, *, reader_gid=None, owner_uid=0):
    root = require_secure_directory(
        receipt_root,
        owner_uid=owner_uid,
        owner_gid=reader_gid,
    )
    lock_path = root / ".chain.lock"
    head_path = root / ".chain-head"

    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        previous = None
        try:
            previous = head_path.read_text(encoding="ascii").strip() or None
        except FileNotFoundError:
            previous = None

        material = dict(receipt)
        material["previous_receipt_sha256"] = previous
        material.pop("receipt_sha256", None)
        digest = sha256_hex(canonical_json_bytes(material))
        material["receipt_sha256"] = digest

        receipt_id = material.get("receipt_id")
        if not isinstance(receipt_id, str) or not receipt_id:
            fail("RECEIPT_ID_INVALID", "receipt_id is required")
        final_path = root / f"{receipt_id}.json"
        if final_path.exists():
            fail("RECEIPT_COLLISION", f"receipt {receipt_id} already exists")

        _atomic_write(
            final_path,
            canonical_json_bytes(material) + b"\n",
            0o640,
            group_gid=reader_gid,
        )
        _atomic_write(head_path, (digest + "\n").encode("ascii"), 0o600)
        return material
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def bounded_run(
    argv,
    *,
    cwd="/",
    env=None,
    timeout_s=90.0,
    stdout_limit=65536,
    stderr_limit=65536,
    kill_callback=None,
    cancel_check=None,
    stdin_bytes=None,
    pass_fds=(),
):
    if not isinstance(argv, list) or not argv:
        fail("RUN_ARGV_INVALID", "argv must be nonempty list")
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        close_fds=True,
        pass_fds=tuple(pass_fds),
        bufsize=0,
    )
    if stdin_bytes is not None:
        try:
            proc.stdin.write(stdin_bytes)
            proc.stdin.flush()
        finally:
            proc.stdin.close()

    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
    selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
    kept = {"stdout": bytearray(), "stderr": bytearray()}
    seen = {"stdout": 0, "stderr": 0}
    digests = {"stdout": hashlib.sha256(), "stderr": hashlib.sha256()}
    limits = {"stdout": stdout_limit, "stderr": stderr_limit}
    start = time.monotonic()
    timed_out = False
    cancelled = False
    termination_requested = False

    def retain(stream, data):
        seen[stream] += len(data)
        digests[stream].update(data)
        room = max(0, limits[stream] - len(kept[stream]))
        if room:
            kept[stream].extend(data[:room])

    def terminate(reason):
        nonlocal timed_out, cancelled, termination_requested
        if termination_requested:
            return
        termination_requested = True
        timed_out = reason == "timeout"
        cancelled = reason == "cancel"
        if kill_callback is not None:
            try:
                kill_callback(signal.SIGTERM)
            except Exception:
                pass
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline and proc.poll() is None:
            time.sleep(0.02)
        if proc.poll() is None:
            if kill_callback is not None:
                try:
                    kill_callback(signal.SIGKILL)
                except Exception:
                    pass
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    try:
        while selector.get_map():
            if proc.poll() is None and cancel_check is not None:
                try:
                    if cancel_check():
                        terminate("cancel")
                except Exception:
                    terminate("cancel")

            remaining = timeout_s - (time.monotonic() - start)
            if remaining <= 0 and proc.poll() is None:
                terminate("timeout")
                remaining = 0.1

            events = selector.select(
                timeout=max(0.0, min(0.25, remaining if remaining > 0 else 0.1))
            )
            if not events and proc.poll() is not None:
                for item in list(selector.get_map().values()):
                    try:
                        data = item.fileobj.read()
                    except Exception:
                        data = b""
                    if data:
                        retain(item.data, data)
                    selector.unregister(item.fileobj)
                break

            for key, _ in events:
                try:
                    data = key.fileobj.read(16384)
                except BlockingIOError:
                    continue
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                retain(key.data, data)

            if proc.poll() is None and time.monotonic() - start >= timeout_s:
                terminate("timeout")

        rc = proc.wait(timeout=2.0)
    finally:
        selector.close()
        if proc.stdout is not None:
            proc.stdout.close()
        if proc.stderr is not None:
            proc.stderr.close()

    duration_ms = int((time.monotonic() - start) * 1000)
    sig = -rc if rc < 0 else None
    return {
        "exit_code": rc if rc >= 0 else None,
        "signal": sig,
        "timed_out": timed_out,
        "cancelled": cancelled,
        "duration_ms": duration_ms,
        "stdout": bytes(kept["stdout"]),
        "stderr": bytes(kept["stderr"]),
        "stdout_bytes_seen": seen["stdout"],
        "stderr_bytes_seen": seen["stderr"],
        "stdout_truncated": seen["stdout"] > len(kept["stdout"]),
        "stderr_truncated": seen["stderr"] > len(kept["stderr"]),
        "stdout_sha256": digests["stdout"].hexdigest(),
        "stderr_sha256": digests["stderr"].hexdigest(),
    }
