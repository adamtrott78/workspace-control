#!/usr/bin/env python3
"""Trusted exact-SHA candidate materializer for Workspace Shell.

This service owns outbound Git access. The execution worker and job launcher
remain network-isolated and never receive repository credentials.
"""

import argparse
import json
import os
import shlex
import shutil
import socket
import stat
import struct
import subprocess
import uuid
from pathlib import Path

REQUEST_LIMIT = 32768
RESPONSE_LIMIT = 65536


class MaterializerError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def fail(code, message):
    raise MaterializerError(code, message)


def load_json(path):
    p = Path(path)
    st = os.lstat(p)
    if not stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
        fail("CONFIG_INVALID", f"{p} must be a regular non-symlink file")
    if st.st_uid != 0 or st.st_mode & 0o022:
        fail("CONFIG_INVALID", f"{p} ownership/mode invalid")
    return json.loads(p.read_text(encoding="utf-8"))


def exact_sha(value):
    return isinstance(value, str) and len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def git_env(source):
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    }
    transport = source.get("transport")
    if transport == "public_https":
        url = source.get("url")
        if not isinstance(url, str) or not url.startswith("https://github.com/") or "@" in url.split("://", 1)[1]:
            fail("SOURCE_CONFIG_INVALID", "public_https URL must be credential-free GitHub HTTPS")
    elif transport == "ssh_deploy_key":
        url = source.get("url")
        key_path = source.get("key_path")
        known_hosts = source.get("known_hosts_path")
        if not isinstance(url, str) or not url.startswith("git@github.com:"):
            fail("SOURCE_CONFIG_INVALID", "ssh_deploy_key URL must be GitHub SSH")
        for field, value in (("key_path", key_path), ("known_hosts_path", known_hosts)):
            if not isinstance(value, str) or not value.startswith("/etc/workspace-shell/candidate-sources/"):
                fail("SOURCE_CONFIG_INVALID", f"{field} must live under candidate-sources policy root")
            p = Path(value)
            if not p.is_file() or p.is_symlink():
                fail("SOURCE_CREDENTIAL_INVALID", f"{field} missing or symlinked")
            st = os.lstat(p)
            if st.st_uid != 0 or st.st_mode & 0o022:
                fail("SOURCE_CREDENTIAL_INVALID", f"{field} ownership/mode invalid")
            if field == "key_path" and st.st_mode & 0o077:
                fail("SOURCE_CREDENTIAL_INVALID", "deploy key must be root-private")
        env["GIT_SSH_COMMAND"] = " ".join([
            "/usr/bin/ssh",
            "-i", shlex.quote(str(key_path)),
            "-o", "IdentitiesOnly=yes",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            "-o", "UserKnownHostsFile=" + shlex.quote(str(known_hosts)),
        ])
    else:
        fail("SOURCE_CONFIG_INVALID", "unsupported candidate transport")
    return env


def run_git(args, *, env, timeout=45):
    proc = subprocess.run(
        ["/usr/bin/git", *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=timeout,
        close_fds=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip() or "git operation failed"
        fail("FETCH_FAILED", msg[:1200])
    return proc.stdout.strip()


def harden_tree(root):
    for current, dirs, files in os.walk(root, topdown=False, followlinks=False):
        for name in files + dirs:
            p = Path(current) / name
            try:
                st = os.lstat(p)
                if stat.S_ISSOCK(st.st_mode) or stat.S_ISFIFO(st.st_mode) or stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode):
                    fail("SOURCE_SPECIAL_FILE_DENIED", f"special file in candidate: {p}")
                os.chmod(p, st.st_mode & ~0o022, follow_symlinks=False)
                os.chown(p, 0, 0, follow_symlinks=False)
            except (FileNotFoundError, NotImplementedError):
                pass
    st = os.lstat(root)
    os.chmod(root, st.st_mode & ~0o022)
    os.chown(root, 0, 0)


def materialize(cfg, target, sha):
    if not exact_sha(sha):
        fail("INVALID_SHA", "candidate_sha must be an exact lowercase Git SHA")
    source = (cfg.get("sources") or {}).get(target)
    if not isinstance(source, dict):
        fail("SOURCE_UNCONFIGURED", f"no candidate source configured for {target}")
    expected_repo = {
        "workspace-control": "adamtrott78/workspace-control",
        "PADataset": "adamtrott78/PADataset",
    }.get(target)
    if source.get("repository") != expected_repo:
        fail("SOURCE_CONFIG_INVALID", "repository identity mismatch")

    store = Path(cfg["candidate_store_root"]).resolve()
    st = os.lstat(store)
    if not store.is_dir() or st.st_uid != 0 or st.st_mode & 0o022:
        fail("STORE_INVALID", "candidate store ownership/mode invalid")
    target_root = store / target
    target_root.mkdir(mode=0o700, exist_ok=True)
    os.chown(target_root, 0, 0)
    os.chmod(target_root, 0o700)

    final = target_root / sha
    if final.exists():
        observed = run_git(["-C", str(final), "rev-parse", "HEAD"], env=git_env(source), timeout=5)
        dirty = run_git(["-C", str(final), "status", "--porcelain=v1", "--untracked-files=normal"], env=git_env(source), timeout=5)
        if observed != sha or dirty:
            fail("STORE_CORRUPT", "cached candidate does not match exact clean SHA")
        tree = run_git(["-C", str(final), "rev-parse", "HEAD^{tree}"], env=git_env(source), timeout=5)
        return {
            "path": str(final),
            "candidate_sha": sha,
            "candidate_tree": tree,
            "repository": source["repository"],
            "transport": source["transport"],
            "cache_hit": True,
        }

    temp = target_root / f".tmp-{sha}-{uuid.uuid4().hex}"
    temp.mkdir(mode=0o700)
    env = git_env(source)
    try:
        run_git(["init", "--quiet", str(temp)], env=env, timeout=10)
        run_git(["-C", str(temp), "remote", "add", "origin", source["url"]], env=env, timeout=5)
        run_git(["-C", str(temp), "fetch", "--quiet", "--depth=1", "--no-tags", "origin", sha], env=env, timeout=45)
        run_git(["-C", str(temp), "-c", "advice.detachedHead=false", "checkout", "--quiet", "--detach", "FETCH_HEAD"], env=env, timeout=15)
        observed = run_git(["-C", str(temp), "rev-parse", "HEAD"], env=env, timeout=5)
        dirty = run_git(["-C", str(temp), "status", "--porcelain=v1", "--untracked-files=normal"], env=env, timeout=5)
        if observed != sha or dirty:
            fail("SOURCE_MISMATCH", "materialized source does not equal requested clean SHA")
        harden_tree(temp)
        try:
            temp.rename(final)
        except FileExistsError:
            shutil.rmtree(temp, ignore_errors=True)
        observed = run_git(["-C", str(final), "rev-parse", "HEAD"], env=env, timeout=5)
        tree = run_git(["-C", str(final), "rev-parse", "HEAD^{tree}"], env=env, timeout=5)
        if observed != sha:
            fail("STORE_CORRUPT", "final candidate SHA mismatch")
        return {
            "path": str(final),
            "candidate_sha": sha,
            "candidate_tree": tree,
            "repository": source["repository"],
            "transport": source["transport"],
            "cache_hit": False,
        }
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def recv_json(conn):
    data = bytearray()
    while True:
        chunk = conn.recv(8192)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > REQUEST_LIMIT:
            fail("REQUEST_TOO_LARGE", "materializer request exceeds limit")
        if b"\n" in chunk:
            break
    raw = bytes(data).split(b"\n", 1)[0]
    return json.loads(raw.decode("utf-8"))


def serve(config_path):
    cfg = load_json(config_path)
    sock_path = cfg["socket_path"]
    Path(sock_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        os.unlink(sock_path)
    except FileNotFoundError:
        pass
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_path)
    os.chmod(sock_path, 0o600)
    server.listen(8)
    while True:
        conn, _ = server.accept()
        try:
            raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
            _pid, uid, _gid = struct.unpack("3i", raw)
            if uid != 0:
                fail("PEER_DENIED", "candidate materializer accepts only root job-launcher peer")
            req = recv_json(conn)
            if req.get("schema") != "workspace-shell-candidate-materialize.v1":
                fail("REQUEST_SCHEMA_INVALID", "unexpected request schema")
            result = materialize(cfg, req.get("target"), req.get("candidate_sha"))
            payload = {"ok": True, "result": result}
        except MaterializerError as exc:
            payload = {"ok": False, "code": exc.code, "message": exc.message}
        except Exception as exc:
            payload = {"ok": False, "code": "INTERNAL_ERROR", "message": str(exc)[:1200]}
        body = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        conn.sendall(body[:RESPONSE_LIMIT])
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    serve(args.config)


if __name__ == "__main__":
    main()
