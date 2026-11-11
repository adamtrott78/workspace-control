#!/usr/bin/env python3
"""Seal a validated Workspace Shell bundle for activation.

This step consumes only the public tunnel client certificate. It does not read
or copy any private key. The resulting frontend.json contains the SHA-256 of
the certificate's DER encoding, matching the runtime peer-certificate pin.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


def fail(message):
    raise SystemExit(f"ERROR: {message}")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value, mode=0o600):
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(data)
    os.chmod(path, mode)
    return sha256_bytes(data)


def require_regular_no_symlink(path, label):
    path = Path(path)
    try:
        st = os.lstat(path)
    except OSError as exc:
        fail(f"{label} is unavailable: {exc}")
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        fail(f"{label} must be a regular non-symlink file")
    return path


def certificate_der(cert_path, openssl_path):
    proc = subprocess.run(
        [openssl_path, "x509", "-in", str(cert_path), "-outform", "DER"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        close_fds=True,
    )
    if proc.returncode != 0 or not proc.stdout:
        fail(
            "tunnel client certificate is not a valid X.509 certificate: "
            + proc.stderr.decode("utf-8", errors="replace")[:1024]
        )
    return proc.stdout


def seal(args):
    bundle = Path(args.bundle_dir)
    if not bundle.is_dir():
        fail("bundle directory is unavailable")

    manifest_path = require_regular_no_symlink(
        bundle / "install-manifest.json",
        "install manifest",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "workspace-shell-install-bundle.v1":
        fail("unexpected install bundle schema")
    if manifest.get("activation_sealed") is not False:
        fail("install bundle is already sealed or malformed")
    if manifest.get("requires_activation_seal") is not True:
        fail("install bundle does not require activation seal")
    if manifest.get("tunnel_client_cert_sha256") is not None:
        fail("unsealed manifest already carries a tunnel certificate pin")

    unsealed_path = require_regular_no_symlink(
        bundle / "frontend.unsealed.json",
        "unsealed frontend config",
    )
    frontend = json.loads(unsealed_path.read_text(encoding="utf-8"))
    if frontend.get("tunnel_client_cert_sha256") is not None:
        fail("unsealed frontend config already carries a tunnel certificate pin")

    cert_path = require_regular_no_symlink(
        args.tunnel_client_cert,
        "tunnel client certificate",
    )
    der = certificate_der(cert_path, args.openssl_path)
    cert_digest = sha256_bytes(der)
    frontend["tunnel_client_cert_sha256"] = cert_digest

    frontend_path = bundle / "frontend.json"
    if frontend_path.exists():
        fail("frontend.json already exists")
    frontend_digest = write_json(frontend_path, frontend)

    files = manifest.get("files")
    if not isinstance(files, dict):
        fail("install manifest files map is invalid")
    recorded_unsealed = files.pop("frontend.unsealed.json", None)
    if not isinstance(recorded_unsealed, str):
        fail("install manifest lacks unsealed frontend digest")
    if sha256_bytes(unsealed_path.read_bytes()) != recorded_unsealed:
        fail("unsealed frontend config digest does not match install manifest")
    files["frontend.json"] = frontend_digest

    manifest["activation_sealed"] = True
    manifest["requires_activation_seal"] = False
    manifest["tunnel_client_cert_sha256"] = cert_digest
    manifest["tunnel_client_cert_source"] = "PUBLIC_X509_DER_SHA256"
    manifest_sha = write_json(manifest_path, manifest)
    unsealed_path.unlink()

    result = dict(manifest)
    result["install_manifest_sha256"] = manifest_sha
    print(json.dumps(result, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--tunnel-client-cert", required=True)
    parser.add_argument("--openssl-path", default="/usr/bin/openssl")
    args = parser.parse_args()
    seal(args)


if __name__ == "__main__":
    main()
