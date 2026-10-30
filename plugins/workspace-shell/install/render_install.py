#!/usr/bin/env python3
"""Render an exact Workspace Shell installation bundle without applying it."""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
from pathlib import Path
import pwd


HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
CONFIG = PLUGIN / "config"
REPO_ROOT = HERE.parents[2]
AUTHORITY_ARTIFACT = REPO_ROOT / "architecture" / "workspace-shell-mcp-authority-v2.json"

SERVICE_TEMPLATES = (
    "workspace-shell-job-launcher.service.in",
    "workspace-shell-root-broker.service.in",
    "workspace-shell-mcp.service.in",
    "workspace-shell-tunnel.service.in",
)

ALLOWED_UNITS = (
    "workspace-shell-job-launcher.service",
    "workspace-shell-root-broker.service",
    "workspace-shell-mcp.service",
    "workspace-shell-tunnel.service",
)


def fail(message):
    raise SystemExit(f"ERROR: {message}")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def exact_sha(value, field):
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        fail(f"{field} must be a full lowercase Git SHA")
    return value


def digest64(value, field):
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        fail(f"{field} must be a lowercase SHA256")
    return value


def write_bytes(path, data, mode):
    path.write_bytes(data)
    os.chmod(path, mode)
    return sha256_bytes(data)


def write_json(path, value, mode=0o600):
    return write_bytes(
        path,
        (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        mode,
    )


def copy_text(src, dst, mode=0o644):
    return write_bytes(dst, src.read_bytes(), mode)


def resolve_id(value, account, *, group=False):
    if value is not None:
        if value < 1:
            fail(f"invalid numeric identity for {account}")
        return value
    try:
        return grp.getgrnam(account).gr_gid if group else pwd.getpwnam(account).pw_uid
    except KeyError:
        fail(
            f"{account} does not exist; apply the sysusers stage first "
            "or provide an explicit numeric ID"
        )


def load_attestation(path):
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    if data.get("schema") != "workspace-shell-host-attestation.v1":
        fail("unexpected host attestation schema")
    if data.get("decision") != "READY_FOR_INSTALL_PLAN":
        fail("host attestation is not READY_FOR_INSTALL_PLAN")
    if data.get("blockers"):
        fail("host attestation still contains blockers")
    return data, sha256_bytes(raw)


def source_identity(attestation, source_sha_arg):
    source = attestation.get("source") or {}
    head = (source.get("head") or {}).get("stdout")
    tree = (source.get("tree") or {}).get("stdout")
    requested = source.get("requested_sha")
    source_sha = source_sha_arg or requested or head
    exact_sha(source_sha, "source_sha")
    exact_sha(tree, "source_tree")
    if requested and requested != source_sha:
        fail("attested requested SHA differs from renderer source_sha")
    if head and head != source_sha:
        fail("attested source HEAD differs from renderer source_sha")
    return source_sha, tree


def render(args):
    attestation, attestation_digest = load_attestation(args.attestation)
    source_sha, source_tree = source_identity(attestation, args.source_sha)

    authority_sha = exact_sha(args.design_authority_sha, "design_authority_sha")
    policy_digest = digest64(args.policy_artifact_sha256, "policy_artifact_sha256")
    policy_bytes = AUTHORITY_ARTIFACT.read_bytes()
    observed_policy_digest = sha256_bytes(policy_bytes)
    if observed_policy_digest != policy_digest:
        fail("policy_artifact_sha256 does not match repository authority artifact")
    tunnel_cert_digest = digest64(
        args.tunnel_client_cert_sha256,
        "tunnel_client_cert_sha256",
    )

    frontend_uid = resolve_id(args.frontend_uid, "workspace-shell-mcp")
    frontend_gid = resolve_id(args.frontend_gid, "workspace-shell-mcp", group=True)
    worker_uid = resolve_id(args.worker_uid, "workspace-shell-exec")
    worker_gid = resolve_id(args.worker_gid, "workspace-shell-exec", group=True)
    tunnel_uid = resolve_id(args.tunnel_uid, "workspace-shell-tunnel")
    tunnel_gid = resolve_id(args.tunnel_gid, "workspace-shell-tunnel", group=True)

    if len({frontend_uid, worker_uid, tunnel_uid}) != 3:
        fail("frontend, worker, and tunnel UIDs must be distinct")
    if len({frontend_gid, worker_gid, tunnel_gid}) != 3:
        fail("frontend, worker, and tunnel primary GIDs must be distinct")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        fail("output directory must be empty")

    source_root = "/srv/workspace-shell/workspace-control"
    receipt_root = "/var/lib/workspace-shell/receipts"
    control_root = "/run/workspace-shell-control"
    runtime_root = "/opt/workspace-shell/runtime/plugins/workspace-shell"

    frontend = {
        "authority_root": source_root,
        "launcher_socket": control_root + "/job-launcher.sock",
        "broker_socket": control_root + "/root-broker.sock",
        "receipt_root": receipt_root,
        "frontend_signing_key": "/etc/workspace-shell/frontend/request-signing.key",
        "tls_key": "/etc/workspace-shell/frontend/server.key",
        "tls_cert": "/etc/workspace-shell/frontend/server.crt",
        "tls_client_ca": "/etc/workspace-shell/frontend/client-ca.crt",
        "tunnel_client_cert_sha256": tunnel_cert_digest,
        "receipt_uid": 0,
        "frontend_uid": frontend_uid,
        "frontend_gid": frontend_gid,
        "worker_uid": worker_uid,
        "tunnel_uid": tunnel_uid,
        "allowed_units": list(ALLOWED_UNITS),
        "port": 8797,
    }

    launcher = {
        "socket_path": control_root + "/job-launcher.sock",
        "frontend_uid": frontend_uid,
        "frontend_gid": frontend_gid,
        "worker_uid": worker_uid,
        "worker_gid": worker_gid,
        "profile_manifest": "/etc/workspace-shell/profiles.v1.json",
        "source_roots": {"workspace-control": source_root},
        "scratch_root": "/var/lib/workspace-shell/jobs",
        "receipt_root": receipt_root,
        "bwrap_path": "/usr/bin/bwrap",
        "systemd_run_path": "/usr/bin/systemd-run",
        "systemctl_path": "/usr/bin/systemctl",
        "policy_version_sha": authority_sha,
    }

    verifier = {
        "frontend_public_key": "/etc/workspace-shell/frontend/request-signing.pub",
        "trusted_issuers": "/etc/workspace-shell/approval/trusted-issuers.json",
        "revocations": "/etc/workspace-shell/approval/revocations.json",
        "helper_registry": "/etc/workspace-shell/helpers/registry.json",
        "design_authority_sha": authority_sha,
        "policy_artifact_path": "/etc/workspace-shell/policy/workspace-shell-mcp-authority-v2.json",
        "policy_artifact_sha256": policy_digest,
        "source_roots": {"workspace-control": source_root},
    }

    broker = {
        "socket_path": control_root + "/root-broker.sock",
        "frontend_uid": frontend_uid,
        "frontend_gid": frontend_gid,
        "verifier_script": runtime_root + "/bin/verify-broker-request.mjs",
        "verifier_config": "/etc/workspace-shell/broker-verifier.json",
        "replay_db": "/var/lib/workspace-shell/replay/replay.sqlite3",
        "receipt_root": receipt_root,
        "helper_cache_root": "/var/lib/workspace-shell/helper-cache",
        "node_path": "/opt/workspace-shell/node/bin/node",
        "systemd_run_path": "/usr/bin/systemd-run",
        "systemctl_path": "/usr/bin/systemctl",
        "policy_version_sha": authority_sha,
    }

    files = {}
    files["workspace-shell-mcp-authority-v2.json"] = write_bytes(
        out / "workspace-shell-mcp-authority-v2.json",
        policy_bytes,
        0o644,
    )
    for name, payload in (
        ("frontend.json", frontend),
        ("job-launcher.json", launcher),
        ("broker-verifier.json", verifier),
        ("root-broker.json", broker),
    ):
        files[name] = write_json(out / name, payload)

    for source_name, target_name in (
        ("profiles.v1.json", "profiles.v1.json"),
        ("helper-registry.v2.json", "helper-registry.v2.json"),
        ("trusted-issuers.empty.json", "trusted-issuers.empty.json"),
        ("revocations.empty.json", "revocations.empty.json"),
    ):
        files[target_name] = copy_text(CONFIG / source_name, out / target_name)

    files["workspace-shell-sysusers.conf"] = copy_text(
        HERE / "sysusers.conf",
        out / "workspace-shell-sysusers.conf",
    )
    files["workspace-shell-tmpfiles.conf"] = copy_text(
        HERE / "tmpfiles.conf",
        out / "workspace-shell-tmpfiles.conf",
    )

    for template in SERVICE_TEMPLATES:
        target = template.removesuffix(".in")
        files[target] = copy_text(HERE / template, out / target)

    manifest = {
        "schema": "workspace-shell-install-bundle.v1",
        "attestation_sha256": attestation_digest,
        "source_repository": "adamtrott78/workspace-control",
        "source_sha": source_sha,
        "source_tree": source_tree,
        "design_authority_sha": authority_sha,
        "policy_artifact_sha256": policy_digest,
        "policy_artifact_install_path": "/etc/workspace-shell/policy/workspace-shell-mcp-authority-v2.json",
        "identities": {
            "frontend": {"uid": frontend_uid, "gid": frontend_gid},
            "worker": {"uid": worker_uid, "gid": worker_gid},
            "tunnel": {"uid": tunnel_uid, "gid": tunnel_gid},
        },
        "listen": {
            "host": "127.0.0.1",
            "port": 8797,
            "mcp_path": "/mcp",
        },
        "privileged_helpers_enabled": False,
        "operator_trust_store_state": "EMPTY_FAIL_CLOSED",
        "tunnel_runtime_key_included": False,
        "tls_private_keys_included": False,
        "files": files,
    }
    manifest_sha = write_json(out / "install-manifest.json", manifest)
    result = dict(manifest)
    result["install_manifest_sha256"] = manifest_sha
    print(json.dumps(result, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-sha")
    parser.add_argument("--design-authority-sha", required=True)
    parser.add_argument("--policy-artifact-sha256", required=True)
    parser.add_argument("--tunnel-client-cert-sha256", required=True)
    parser.add_argument("--frontend-uid", type=int)
    parser.add_argument("--frontend-gid", type=int)
    parser.add_argument("--worker-uid", type=int)
    parser.add_argument("--worker-gid", type=int)
    parser.add_argument("--tunnel-uid", type=int)
    parser.add_argument("--tunnel-gid", type=int)
    args = parser.parse_args()
    render(args)


if __name__ == "__main__":
    main()
