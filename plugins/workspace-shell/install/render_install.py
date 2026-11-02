#!/usr/bin/env python3
"""Render an exact Workspace Shell installation bundle without applying it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


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
    "workspace-ci-controller@workspace-control-cpu.service",
    "workspace-ci-maintenance-controller.service",
    "workspace-ci-maintenance.service",
    "workspace-ci-v3-provisioner.service",
    "workspace-ci-v3-reconciler.service",
    "workspace-ci-v3-controller@workspace-control-control-small-v1.service",
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


EXPECTED_IDENTITIES = {
    "workspace-shell-mcp": {"uid": 41010, "gid": 41010, "role": "frontend"},
    "workspace-shell-exec": {"uid": 41011, "gid": 41011, "role": "worker"},
    "workspace-shell-tunnel": {"uid": 41012, "gid": 41012, "role": "tunnel"},
}


def attested_identities(attestation):
    entries = attestation.get("planned_identities")
    if not isinstance(entries, list):
        fail("host attestation lacks planned_identities")
    by_name = {
        item.get("name"): item
        for item in entries
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if set(by_name) != set(EXPECTED_IDENTITIES):
        fail("host attestation planned identities do not match Workspace Shell policy")

    result = {}
    for name, expected in EXPECTED_IDENTITIES.items():
        item = by_name[name]
        if item.get("uid") != expected["uid"] or item.get("gid") != expected["gid"]:
            fail(f"host attestation identity mismatch for {name}")
        for field in ("name_user", "name_group", "numeric_uid", "numeric_gid"):
            evidence = item.get(field)
            if not isinstance(evidence, dict) or evidence.get("exists") is not False:
                fail(f"host attestation collision evidence is not clean for {name}: {field}")
        result[expected["role"]] = {
            "uid": expected["uid"],
            "gid": expected["gid"],
        }
    return result


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

    runtime_source_sha = exact_sha(
        args.runtime_source_sha,
        "runtime_source_sha",
    )
    authority_sha = exact_sha(args.design_authority_sha, "design_authority_sha")
    policy_digest = digest64(args.policy_artifact_sha256, "policy_artifact_sha256")
    policy_bytes = AUTHORITY_ARTIFACT.read_bytes()
    observed_policy_digest = sha256_bytes(policy_bytes)
    if observed_policy_digest != policy_digest:
        fail("policy_artifact_sha256 does not match repository authority artifact")
    identities = attested_identities(attestation)
    frontend_uid = identities["frontend"]["uid"]
    frontend_gid = identities["frontend"]["gid"]
    worker_uid = identities["worker"]["uid"]
    worker_gid = identities["worker"]["gid"]
    tunnel_uid = identities["tunnel"]["uid"]
    tunnel_gid = identities["tunnel"]["gid"]

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
        "tunnel_client_cert_sha256": None,
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
        "node_openssl_conf": "/opt/workspace-shell/node/ssl/openssl.cnf",
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
        ("frontend.unsealed.json", frontend),
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
        "runtime_source_sha": runtime_source_sha,
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
        "activation_sealed": False,
        "requires_activation_seal": True,
        "tunnel_client_cert_sha256": None,
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
    parser.add_argument("--runtime-source-sha", required=True)
    parser.add_argument("--design-authority-sha", required=True)
    parser.add_argument("--policy-artifact-sha256", required=True)
    args = parser.parse_args()
    render(args)


if __name__ == "__main__":
    main()
