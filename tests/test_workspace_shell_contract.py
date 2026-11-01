import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "workspace-shell"
ROOT_CODE = PLUGIN / "root"
HOST_ATTEST = PLUGIN / "install" / "host_attest.py"
RENDER_INSTALL = PLUGIN / "install" / "render_install.py"
SEAL_INSTALL = PLUGIN / "install" / "seal_install.py"
RENDER_TUNNEL_PROFILE = PLUGIN / "install" / "render_tunnel_profile.py"
ACTIVATE_LIVE = PLUGIN / "install" / "activate_live.sh"
SYSUSERS = PLUGIN / "install" / "sysusers.conf"
FINAL_HOST_ATTEST = PLUGIN / "install" / "evidence" / "lambda-host-attestation.f999b25a.json"
COMMISSIONING_SOURCE_SHA = "f999b25a866f25c95243cbbd6d1377a799fafb78"
COMMISSIONING_ATTEST_SHA256 = "d44cda1f6f13f814e093bef9228410f319d504c76cf80ba8e6d2ecbb8d321353"
DESIGN_AUTHORITY_SHA = "0c24e42ea57a3e23af01351a5974d5f09f3ce319"
TEST_RUNTIME_SOURCE_SHA = "d" * 40
AUTHORITY_ARTIFACT = ROOT / "architecture" / "workspace-shell-mcp-authority-v2.json"
sys.path.insert(0, str(ROOT_CODE))

job_launcher = importlib.import_module("job_launcher")
root_broker = importlib.import_module("root_broker")
runtime_common = importlib.import_module("runtime_common")


class WorkspaceShellContractTests(unittest.TestCase):
    @staticmethod
    def _ready_attestation():
        identities = []
        for name, ident in (
            ("workspace-shell-mcp", 41010),
            ("workspace-shell-exec", 41011),
            ("workspace-shell-tunnel", 41012),
        ):
            identities.append({
                "name": name,
                "uid": ident,
                "gid": ident,
                "name_user": {"exists": False, "name": name},
                "name_group": {"exists": False, "name": name},
                "numeric_uid": {"exists": False, "uid": ident},
                "numeric_gid": {"exists": False, "gid": ident},
            })
        return {
            "schema": "workspace-shell-host-attestation.v1",
            "decision": "READY_FOR_INSTALL_PLAN",
            "blockers": [],
            "planned_identities": identities,
            "source": {
                "head": {"stdout": "a" * 40},
                "tree": {"stdout": "b" * 40},
                "requested_sha": "a" * 40,
            },
        }

    @staticmethod
    def _node20_binary():
        candidates = []
        override = os.environ.get("WORKSPACE_SHELL_NODE")
        if override:
            candidates.append(Path(override))

        runner_temp = os.environ.get("RUNNER_TEMP")
        if runner_temp:
            runner_root = Path(runner_temp).resolve().parents[1]
            candidates.extend([
                runner_root / "externals" / "node24" / "bin" / "node",
                runner_root / "externals" / "node20" / "bin" / "node",
            ])

        system_node = shutil.which("node")
        if system_node:
            candidates.append(Path(system_node))

        checked = []
        for candidate in candidates:
            value = str(candidate)
            if value in checked or not candidate.is_file():
                continue
            checked.append(value)
            proc = subprocess.run(
                [value, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if proc.returncode != 0:
                continue
            version = proc.stdout.strip().lstrip("v")
            try:
                major = int(version.split(".", 1)[0])
            except (ValueError, IndexError):
                continue
            if major >= 20:
                return value
        raise AssertionError(
            "Workspace Shell tests require Node >=20; checked: "
            + ", ".join(checked)
        )

    def test_node_policy_and_approval_adversarial_suite(self):
        node = self._node20_binary()
        files = [
            "server.js",
            "src/core.js",
            "bin/verify-broker-request.mjs",
        ]
        for relative in files:
            proc = subprocess.run(
                [node, "--check", str(PLUGIN / relative)],
                cwd=PLUGIN,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

        proc = subprocess.run(
            [
                node,
                "--test",
                str(PLUGIN / "test" / "core.test.js"),
                str(PLUGIN / "test" / "broker-verifier.test.js"),
            ],
            cwd=PLUGIN,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)

    def test_host_attestation_is_read_only_and_secret_averse(self):
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(HOST_ATTEST)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

        source = HOST_ATTEST.read_text()
        forbidden = (
            "/proc/*/environ",
            "/proc/{pid}/environ",
            "os.environ",
            ".ssh/id_",
            "read_text(\"/home/atrott/.config",
            "cat /home/atrott",
        )
        for needle in forbidden:
            self.assertNotIn(needle, source)
        self.assertIn('"process_environments_read": False', source)
        self.assertIn('"secret_file_contents_read": False', source)
        self.assertIn('"api_tokens_read": False', source)
        self.assertIn('"ssh_material_read": False', source)
        self.assertIn('"workspace-shell-host-attestation.v1"', source)
        self.assertIn('"--unshare-all"', source)
        self.assertIn('"--cap-drop"', source)
        self.assertIn("PLANNED_IDENTITIES", source)
        self.assertIn('"numeric_uid"', source)
        self.assertIn("41010", source)
        self.assertIn("41011", source)
        self.assertIn("41012", source)

        sysusers = SYSUSERS.read_text()
        self.assertIn("workspace-shell-mcp    41010", sysusers)
        self.assertIn("workspace-shell-exec   41011", sysusers)
        self.assertIn("workspace-shell-tunnel 41012", sysusers)

    def test_host_attestation_functions_bound_output_and_do_not_mutate(self):
        spec = importlib.util.spec_from_file_location("workspace_shell_host_attest", HOST_ATTEST)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sample"
            p.write_text("x")
            p.chmod(0o644)
            meta = module.path_meta(p)
            self.assertTrue(meta["exists"])
            self.assertEqual(meta["type"], "file")
            self.assertEqual(meta["mode"], "0644")

        with patch.object(module.os, "lstat", side_effect=PermissionError(13, "denied")):
            hidden = module.path_meta("/host-hidden/example")
        self.assertIsNone(hidden["exists"])
        self.assertEqual(hidden["access_error"], "PermissionError")
        self.assertEqual(hidden["errno"], 13)

        result = module.run(
            [sys.executable, "-c", "print('x' * 9000)"],
            timeout=3,
        )
        self.assertEqual(result["returncode"], 0)
        self.assertLessEqual(len(result["stdout"]), 8192)

    def test_install_renderer_is_non_mutating_and_fail_closed(self):
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(RENDER_INSTALL)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            attestation = td / "attestation.json"
            out = td / "bundle"
            fake = self._ready_attestation()
            attestation.write_text(json.dumps(fake))
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_INSTALL),
                    "--attestation", str(attestation),
                    "--output-dir", str(out),
                    "--source-sha", "a" * 40,
                    "--runtime-source-sha", TEST_RUNTIME_SOURCE_SHA,
                    "--design-authority-sha", "c" * 40,
                    "--policy-artifact-sha256", hashlib.sha256(AUTHORITY_ARTIFACT.read_bytes()).hexdigest(),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            manifest = json.loads((out / "install-manifest.json").read_text())
            self.assertEqual(manifest["source_sha"], "a" * 40)
            self.assertEqual(manifest["runtime_source_sha"], TEST_RUNTIME_SOURCE_SHA)
            self.assertFalse(manifest["privileged_helpers_enabled"])
            self.assertEqual(
                manifest["operator_trust_store_state"],
                "EMPTY_FAIL_CLOSED",
            )
            self.assertFalse(manifest["tunnel_runtime_key_included"])
            self.assertFalse(manifest["tls_private_keys_included"])
            self.assertFalse(manifest["activation_sealed"])
            self.assertTrue(manifest["requires_activation_seal"])
            self.assertIsNone(manifest["tunnel_client_cert_sha256"])
            self.assertFalse((out / "frontend.json").exists())
            self.assertTrue((out / "frontend.unsealed.json").is_file())
            self.assertEqual(
                manifest["identities"],
                {
                    "frontend": {"uid": 41010, "gid": 41010},
                    "worker": {"uid": 41011, "gid": 41011},
                    "tunnel": {"uid": 41012, "gid": 41012},
                },
            )
            self.assertEqual(
                manifest["policy_artifact_sha256"],
                hashlib.sha256(AUTHORITY_ARTIFACT.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                (out / "workspace-shell-mcp-authority-v2.json").read_bytes(),
                AUTHORITY_ARTIFACT.read_bytes(),
            )
            verifier = json.loads((out / "broker-verifier.json").read_text())
            self.assertEqual(
                verifier["policy_artifact_path"],
                "/etc/workspace-shell/policy/workspace-shell-mcp-authority-v2.json",
            )
            self.assertTrue((out / "workspace-shell-mcp.service").is_file())
            self.assertTrue((out / "workspace-shell-sysusers.conf").is_file())
            self.assertEqual(
                json.loads((out / "helper-registry.v2.json").read_text())["helpers"],
                {},
            )

            contents = "\n".join(
                p.read_text(errors="ignore")
                for p in out.iterdir()
                if p.is_file()
            )
            self.assertNotIn("sk-", contents)
            self.assertNotIn("BEGIN PRIVATE KEY", contents)
            self.assertNotIn("tunnel-runtime-key", contents)


    def test_activation_seal_requires_valid_public_x509_and_pins_der_digest(self):
        openssl = shutil.which("openssl")
        if not openssl:
            self.skipTest("openssl unavailable")
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SEAL_INSTALL)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            attestation = td / "attestation.json"
            bundle = td / "bundle"
            attestation.write_text(json.dumps(self._ready_attestation()))
            render = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_INSTALL),
                    "--attestation", str(attestation),
                    "--output-dir", str(bundle),
                    "--source-sha", "a" * 40,
                    "--runtime-source-sha", TEST_RUNTIME_SOURCE_SHA,
                    "--design-authority-sha", "c" * 40,
                    "--policy-artifact-sha256",
                    hashlib.sha256(AUTHORITY_ARTIFACT.read_bytes()).hexdigest(),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            self.assertEqual(render.returncode, 0, render.stderr)

            key = td / "client.key"
            cert = td / "client.crt"
            make_cert = subprocess.run(
                [
                    openssl, "req", "-x509", "-newkey", "rsa:2048",
                    "-keyout", str(key), "-out", str(cert),
                    "-nodes", "-days", "1", "-subj", "/CN=workspace-shell-test",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
            )
            self.assertEqual(make_cert.returncode, 0, make_cert.stderr)

            sealed = subprocess.run(
                [
                    sys.executable,
                    str(SEAL_INSTALL),
                    "--bundle-dir", str(bundle),
                    "--tunnel-client-cert", str(cert),
                    "--openssl-path", openssl,
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            self.assertEqual(sealed.returncode, 0, sealed.stderr)

            der = subprocess.run(
                [openssl, "x509", "-in", str(cert), "-outform", "DER"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout
            expected = hashlib.sha256(der).hexdigest()
            manifest = json.loads((bundle / "install-manifest.json").read_text())
            frontend = json.loads((bundle / "frontend.json").read_text())
            self.assertTrue(manifest["activation_sealed"])
            self.assertFalse(manifest["requires_activation_seal"])
            self.assertEqual(manifest["tunnel_client_cert_sha256"], expected)
            self.assertEqual(frontend["tunnel_client_cert_sha256"], expected)
            self.assertFalse((bundle / "frontend.unsealed.json").exists())

    def test_install_renderer_rejects_identity_collision(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            attestation = td / "attestation.json"
            out = td / "bundle"
            fake = self._ready_attestation()
            fake["planned_identities"][0]["numeric_uid"] = {
                "exists": True,
                "uid": 41010,
                "name": "already-used",
            }
            attestation.write_text(json.dumps(fake))
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_INSTALL),
                    "--attestation", str(attestation),
                    "--output-dir", str(out),
                    "--source-sha", "a" * 40,
                    "--runtime-source-sha", TEST_RUNTIME_SOURCE_SHA,
                    "--design-authority-sha", "c" * 40,
                    "--policy-artifact-sha256",
                    hashlib.sha256(AUTHORITY_ARTIFACT.read_bytes()).hexdigest(),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("collision evidence", proc.stderr)

    def test_final_lambda_attestation_renders_unsealed_commissioning_bundle(self):
        self.assertTrue(FINAL_HOST_ATTEST.is_file())
        self.assertEqual(
            hashlib.sha256(FINAL_HOST_ATTEST.read_bytes()).hexdigest(),
            COMMISSIONING_ATTEST_SHA256,
        )
        evidence = json.loads(FINAL_HOST_ATTEST.read_text())
        self.assertEqual(evidence["decision"], "READY_FOR_INSTALL_PLAN")
        self.assertEqual(evidence["blockers"], [])
        self.assertEqual(
            evidence["source"]["head"]["stdout"],
            COMMISSIONING_SOURCE_SHA,
        )
        self.assertEqual(
            evidence["source"]["requested_sha"],
            COMMISSIONING_SOURCE_SHA,
        )
        self.assertEqual(evidence["source"]["status"]["stdout"], "")
        self.assertFalse(evidence["planned_listener"]["occupied"])
        self.assertEqual(
            [
                (x["name"], x["uid"], x["gid"],
                 x["numeric_uid"]["exists"], x["numeric_gid"]["exists"])
                for x in evidence["planned_identities"]
            ],
            [
                ("workspace-shell-mcp", 41010, 41010, False, False),
                ("workspace-shell-exec", 41011, 41011, False, False),
                ("workspace-shell-tunnel", 41012, 41012, False, False),
            ],
        )

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "bundle"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_INSTALL),
                    "--attestation", str(FINAL_HOST_ATTEST),
                    "--output-dir", str(out),
                    "--source-sha", COMMISSIONING_SOURCE_SHA,
                    "--runtime-source-sha", TEST_RUNTIME_SOURCE_SHA,
                    "--design-authority-sha", DESIGN_AUTHORITY_SHA,
                    "--policy-artifact-sha256",
                    hashlib.sha256(AUTHORITY_ARTIFACT.read_bytes()).hexdigest(),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            manifest = json.loads((out / "install-manifest.json").read_text())
            self.assertEqual(
                manifest["attestation_sha256"],
                COMMISSIONING_ATTEST_SHA256,
            )
            self.assertEqual(
                manifest["source_sha"],
                COMMISSIONING_SOURCE_SHA,
            )
            self.assertEqual(
                manifest["runtime_source_sha"],
                TEST_RUNTIME_SOURCE_SHA,
            )
            self.assertEqual(
                manifest["design_authority_sha"],
                DESIGN_AUTHORITY_SHA,
            )
            self.assertEqual(
                manifest["identities"],
                {
                    "frontend": {"uid": 41010, "gid": 41010},
                    "worker": {"uid": 41011, "gid": 41011},
                    "tunnel": {"uid": 41012, "gid": 41012},
                },
            )
            self.assertFalse(manifest["activation_sealed"])
            self.assertTrue(manifest["requires_activation_seal"])
            self.assertIsNone(manifest["tunnel_client_cert_sha256"])
            self.assertFalse(manifest["privileged_helpers_enabled"])
            self.assertEqual(
                manifest["operator_trust_store_state"],
                "EMPTY_FAIL_CLOSED",
            )
            self.assertTrue((out / "frontend.unsealed.json").is_file())
            self.assertFalse((out / "frontend.json").exists())

    def test_install_renderer_rejects_blocked_attestation(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            attestation = td / "attestation.json"
            out = td / "bundle"
            attestation.write_text(json.dumps({
                "schema": "workspace-shell-host-attestation.v1",
                "decision": "BLOCKED",
                "blockers": ["missing bwrap"],
                "source": {
                    "head": {"stdout": "a" * 40},
                    "tree": {"stdout": "b" * 40},
                },
            }))
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_INSTALL),
                    "--attestation", str(attestation),
                    "--output-dir", str(out),
                    "--source-sha", "a" * 40,
                    "--runtime-source-sha", TEST_RUNTIME_SOURCE_SHA,
                    "--design-authority-sha", "c" * 40,
                    "--policy-artifact-sha256", hashlib.sha256(AUTHORITY_ARTIFACT.read_bytes()).hexdigest(),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("READY_FOR_INSTALL_PLAN", proc.stderr)

    def test_tunnel_profile_renderer_matches_v0018_schema(self):
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(RENDER_TUNNEL_PROFILE)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_TUNNEL_PROFILE),
                    "--profile", "workspace-shell-production",
                    "--profile-dir", str(td),
                    "--tunnel-id", "tunnel_" + "a" * 32,
                    "--force",
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            profile = (td / "workspace-shell-production.yaml").read_text()
            self.assertIn('ca_bundle: "/etc/workspace-shell/tunnel/ca.crt"', profile)
            self.assertIn('url: "https://127.0.0.1:8797/mcp"', profile)
            self.assertIn('client_cert: "/etc/workspace-shell/tunnel/client.crt"', profile)
            self.assertIn('client_key: "/etc/workspace-shell/tunnel/client.key"', profile)
            self.assertIn('api_key: "file:/etc/workspace-shell/tunnel/runtime-key"', profile)
            self.assertNotIn("sk-", profile)
            self.assertNotIn("channel=main,url=", profile)

    def test_live_lambda_host_attestation_when_explicitly_requested(self):
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if not event_path or not Path(event_path).is_file():
            self.skipTest("not a GitHub Actions event")
        try:
            event = json.loads(Path(event_path).read_text())
        except (OSError, json.JSONDecodeError):
            self.skipTest("GitHub event unavailable")
        body = ((event.get("comment") or {}).get("body") or "").strip()
        issue = event.get("issue") or {}
        actual_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
        expected_body = f"/workspace-control-validate {actual_sha} host-attest"
        if not issue.get("pull_request") or body != expected_body:
            self.skipTest(
                "live host attestation not explicitly requested for exact Workspace Shell PR head"
            )

        proc = subprocess.run(
            [
                sys.executable,
                str(HOST_ATTEST),
                "--source-root", str(ROOT),
                "--source-sha", actual_sha,
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        attestation = json.loads(proc.stdout)
        self.assertEqual(
            attestation["schema"],
            "workspace-shell-host-attestation.v1",
        )
        self.assertEqual(
            (attestation["source"]["head"] or {}).get("stdout"),
            actual_sha,
        )
        self.assertFalse(attestation["secret_policy"]["process_environments_read"])
        self.assertFalse(attestation["secret_policy"]["secret_file_contents_read"])
        self.assertFalse(attestation["secret_policy"]["api_tokens_read"])
        self.assertFalse(attestation["secret_policy"]["ssh_material_read"])
        print(
            "WORKSPACE_SHELL_HOST_ATTESTATION_JSON="
            + json.dumps(attestation, sort_keys=True, separators=(",", ":"))
        )

    def test_live_activation_operator_is_fail_closed_and_boot_disabled(self):
        proc = subprocess.run(
            ["bash", "-n", str(ACTIVATE_LIVE)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        source = ACTIVATE_LIVE.read_text()

        self.assertIn(
            'SOURCE_HEAD="f999b25a866f25c95243cbbd6d1377a799fafb78"',
            source,
        )
        self.assertIn(
            'ATTEST_SHA256="d44cda1f6f13f814e093bef9228410f319d504c76cf80ba8e6d2ecbb8d321353"',
            source,
        )
        self.assertIn('SCRIPT_DIR="$(cd -- "$(dirname -- "', source)
        self.assertIn('BASH_SOURCE[0]', source)
        self.assertIn('ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd -P)"', source)
        self.assertNotIn('git rev-parse --show-toplevel', source)
        self.assertIn('OPERATOR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"', source)
        self.assertIn(
            'SOURCE_REPO_URL="https://github.com/adamtrott78/workspace-control.git"',
            source,
        )
        self.assertIn('SOURCE_BRANCH="workspace-shell-mcp-v1-current-main"', source)
        self.assertIn('GIT_TERMINAL_PROMPT=0 git -c credential.helper= clone', source)
        self.assertNotIn('git clone --no-hardlinks --no-checkout "$ROOT"', source)
        self.assertIn('--runtime-source-sha "$OPERATOR_HEAD"', source)
        self.assertIn(
            'cp -a "$SOURCE" /srv/workspace-shell/workspace-control',
            source,
        )
        self.assertIn(
            'cp -a "$ROOT/plugins/workspace-shell" /opt/workspace-shell/runtime/plugins/workspace-shell',
            source,
        )
        self.assertIn('Type ACTIVATE_WORKSPACE_SHELL to continue', source)
        self.assertIn('read -rsp "Runtime key: " RUNTIME_KEY', source)
        self.assertIn('TUNNEL_PROFILE_SECRET_SCAN=PASS', source)
        self.assertIn('render_tunnel_profile.py', source)
        self.assertIn('--ca-bundle /etc/workspace-shell/tunnel/ca.crt', source)
        self.assertIn('--client-cert /etc/workspace-shell/tunnel/client.crt', source)
        self.assertIn('--client-key /etc/workspace-shell/tunnel/client.key', source)
        self.assertNotIn('tunnel-client init', source)
        self.assertNotIn('--mcp-server-url "channel=main,url=', source)
        self.assertIn('LOCAL_MTLS_HEALTH=PASS', source)
        self.assertIn('TUNNEL_DOCTOR=PASS', source)
        self.assertIn('TUNNEL_READY=PASS', source)
        self.assertIn('SERVICES_ACTIVE_BOOT_DISABLED=PASS', source)
        self.assertIn('workspace-shell-disable', source)
        self.assertIn('rollback()', source)
        self.assertIn('userdel "$user"', source)
        self.assertIn('groupdel "$group"', source)
        self.assertIn('COMMITTED=1', source)
        self.assertNotIn("systemctl enable ", source)
        self.assertNotIn("sudo bash", source)
        self.assertNotIn("BEGIN PRIVATE KEY", source)
        self.assertNotIn("\\\\$" + "{", source)

    def test_independent_filtered_remote_clone_can_materialize_historical_source(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            work = td / "work"
            remote = td / "remote.git"
            caller = td / "caller"
            source = td / "source"

            subprocess.run(
                ["git", "init", "-b", "main", str(work)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(work), "config", "user.name", "Workspace Shell Test"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(work), "config", "user.email", "workspace-shell-test@example.invalid"],
                check=True,
            )
            historical = work / "historical.txt"
            historical.write_text("historical-payload\n")
            subprocess.run(["git", "-C", str(work), "add", "historical.txt"], check=True)
            subprocess.run(
                ["git", "-C", str(work), "commit", "-m", "historical"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            historical_sha = subprocess.check_output(
                ["git", "-C", str(work), "rev-parse", "HEAD"],
                text=True,
            ).strip()

            historical.write_text("current-payload\n")
            (work / "current-only.txt").write_text("current\n")
            subprocess.run(["git", "-C", str(work), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(work), "commit", "-m", "current"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            subprocess.run(
                ["git", "clone", "--bare", str(work), str(remote)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(remote), "config", "uploadpack.allowFilter", "true"],
                check=True,
            )

            remote_url = remote.resolve().as_uri()
            subprocess.run(
                [
                    "git", "clone", "--filter=blob:none", "--no-checkout",
                    "--branch", "main", remote_url, str(caller),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(caller), "checkout", "--detach", "main"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Source preparation must be independent of the caller's partial
            # object store. It clones the canonical remote again, then lets
            # checkout materialize the historical blobs before removing origin.
            subprocess.run(
                [
                    "git", "-c", "credential.helper=", "clone",
                    "--no-checkout", "--filter=blob:none", "--branch", "main",
                    remote_url, str(source),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            subprocess.run(
                [
                    "git", "-C", str(source), "-c", "credential.helper=",
                    "checkout", "--detach", historical_sha,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            subprocess.run(
                ["git", "-C", str(source), "remote", "remove", "origin"],
                check=True,
            )
            self.assertEqual(
                (source / "historical.txt").read_text(),
                "historical-payload\n",
            )
            self.assertEqual(
                subprocess.check_output(
                    ["git", "-C", str(source), "status", "--porcelain=v1"],
                    text=True,
                ),
                "",
            )

    def test_launcher_duplicates_profile_grammar_and_denies_escape_shapes(self):
        manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())
        good = job_launcher.resolve_profile(
            manifest, "git-read", ["rev-parse", "HEAD"]
        )
        self.assertEqual(good["executable"], "/usr/bin/git")
        self.assertFalse(good["write_scratch"])
        self.assertEqual(
            good["argv"][:8],
            [
                "-c", "core.hooksPath=/dev/null",
                "-c", "core.fsmonitor=false",
                "-c", "diff.external=",
                "-c", "credential.helper=",
            ],
        )
        self.assertEqual(good["argv"][-2:], ["rev-parse", "HEAD"])
        self.assertIn("safe.directory=/workspace", good["argv"])
        self.assertEqual(good["env"]["GIT_TERMINAL_PROMPT"], "0")

        with self.assertRaisesRegex(
            runtime_common.ShellRuntimeError, "PROFILE_ARGV_DENIED"
        ):
            job_launcher.resolve_profile(
                manifest,
                "git-read",
                ["-c", "alias.pwn=!sh", "pwn"],
            )
        with self.assertRaises(runtime_common.ShellRuntimeError):
            job_launcher.resolve_profile(
                manifest,
                "pytest-bounded",
                ["../../etc/passwd"],
            )
        with self.assertRaisesRegex(
            runtime_common.ShellRuntimeError, "PROFILE_ARGV_DENIED"
        ):
            job_launcher.resolve_profile(
                manifest,
                "validation-bounded",
                ["preflight", "--repo", "workspace-control"],
            )

    def test_git_read_overrides_local_execution_hooks(self):
        manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())
        resolved = job_launcher.resolve_profile(
            manifest,
            "git-read",
            ["status", "--porcelain=v1", "--untracked-files=normal"],
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "fsmonitor-ran"
            hook = root / "fsmonitor.sh"
            hook.write_text(f"#!/bin/sh\ntouch {marker}\necho\n", encoding="utf-8")
            hook.chmod(0o755)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "--local", "core.fsmonitor", str(hook)],
                cwd=root,
                check=True,
            )
            proc = subprocess.run(
                [resolved["executable"], *resolved["argv"]],
                cwd=root,
                env={
                    "PATH": "/usr/bin:/bin",
                    "LANG": "C.UTF-8",
                    "LC_ALL": "C.UTF-8",
                    **resolved["env"],
                },
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(marker.exists())

    def test_worker_sandbox_command_excludes_control_plane_and_network(self):
        manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())
        resolved = job_launcher.resolve_profile(
            manifest,
            "pytest-bounded",
            ["tests/test_workspace_shell_contract.py", "-q"],
        )
        with tempfile.TemporaryDirectory() as td:
            command = job_launcher.build_bwrap_command(
                {"bwrap_path": "/usr/bin/true"},
                Path(td),
                ".",
                resolved,
            )

        joined = "\n".join(command)
        self.assertIn("--unshare-all", command)
        self.assertIn("--cap-drop", command)
        self.assertIn("ALL", command)
        self.assertNotIn("/run/workspace-shell-control", joined)
        self.assertNotIn("/etc/workspace-shell", joined)
        self.assertNotIn("SSH_AUTH_SOCK", joined)
        self.assertNotIn("GITHUB_TOKEN", joined)
        self.assertEqual(
            command[-len(resolved["argv"]) - 1],
            resolved["executable"],
        )

    def test_systemd_job_wrapper_fixes_uid_cgroup_and_host_controls(self):
        command = job_launcher.build_systemd_run_command(
            {"systemd_run_path": "/usr/bin/true"},
            "workspace-shell-job-test",
            ["/usr/bin/true"],
            41001,
            41001,
            Path("/var/lib/workspace-shell/jobs/test"),
        )
        joined = "\n".join(command)
        self.assertIn("--uid=41001", command)
        self.assertIn("--gid=41001", command)
        self.assertIn("--property=PrivateNetwork=yes", command)
        self.assertIn("--property=NoNewPrivileges=yes", command)
        self.assertIn("--property=CapabilityBoundingSet=", command)
        self.assertIn("--property=KillMode=control-group", command)
        self.assertIn("--property=TasksMax=48", command)
        self.assertIn("--property=MemoryMax=1G", command)
        self.assertIn("--property=CPUAccounting=yes", command)
        self.assertIn("--property=CPUQuota=100%", command)
        self.assertIn("--property=RuntimeMaxSec=90s", command)
        self.assertNotIn("workspace-shell-exec", joined)

    def test_worker_cleanup_uses_cgroup_kill_for_residual_descendants(self):
        state = {"ActiveState": "inactive", "ControlGroup": "/workspace-shell-test"}
        with patch.object(job_launcher, "_unit_state", return_value=state), \
             patch.object(job_launcher, "_cgroup_pids", side_effect=[["123"], []]), \
             patch.object(job_launcher, "_cgroup_kill", return_value=True) as kill:
            self.assertEqual(
                job_launcher.cleanup_state({}, "workspace-shell-job-test"),
                "EMPTY",
            )
        kill.assert_called_once_with("/workspace-shell-test")

    def test_cgroup_kill_writes_kernel_kill_switch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "cgroup.kill").write_text("", encoding="ascii")
            with patch.object(job_launcher, "_cgroup_path", return_value=root):
                self.assertTrue(job_launcher._cgroup_kill("/workspace-shell-test"))
            self.assertEqual((root / "cgroup.kill").read_text(), "1\n")

    def test_privileged_helper_wrapper_has_same_cpu_ceiling(self):
        command = root_broker.build_helper_systemd_command(
            {"systemd_run_path": "/usr/bin/true"},
            "workspace-shell-helper-test",
            Path("/usr/bin/true"),
            {
                "task_id": "task-abc",
                "target": "workspace-control",
                "expected_source_commit": "a" * 40,
                "approval_id": "approval-12345678",
                "operation": "noop",
                "confinement": {
                    "capabilities": [],
                    "read_write_paths": [],
                    "network": "deny",
                },
            },
        )
        self.assertIn("--property=CPUAccounting=yes", command)
        self.assertIn("--property=CPUQuota=100%", command)
        self.assertIn("--property=RuntimeMaxSec=90s", command)
        self.assertIn("--property=KillMode=control-group", command)

    def test_helper_cleanup_uses_cgroup_kill_for_residual_descendants(self):
        state = {"ActiveState": "inactive", "ControlGroup": "/workspace-shell-helper-test"}
        with patch.object(root_broker, "helper_unit_state", return_value=state), \
             patch.object(
                 root_broker,
                 "helper_cgroup_pids",
                 side_effect=[["123"], ["123"], ["123"], []],
             ), \
             patch.object(root_broker, "helper_unit_killer", return_value=lambda _sig: None), \
             patch.object(root_broker, "helper_cgroup_kill", return_value=True) as kill, \
             patch.object(root_broker.time, "sleep", return_value=None):
            self.assertEqual(
                root_broker.cleanup_helper_unit({}, "workspace-shell-helper-test"),
                "EMPTY",
            )
        kill.assert_called_once_with("/workspace-shell-helper-test")

    def test_receipt_files_are_root_service_owned_and_frontend_group_readable(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = runtime_common.write_receipt(
                td,
                {
                    "schema": "workspace-shell-receipt.v1",
                    "receipt_id": "receipt-test-1234",
                    "task_id": "task-abc",
                },
                reader_gid=os.getgid(),
                owner_uid=os.getuid(),
            )
            path = Path(td) / "receipt-test-1234.json"
            st = path.stat()
            self.assertEqual(st.st_gid, os.getgid())
            self.assertEqual(st.st_mode & 0o777, 0o640)
            self.assertEqual(receipt["receipt_id"], "receipt-test-1234")
            self.assertTrue(receipt["receipt_sha256"])

    def test_dirty_checkout_is_inspectable_but_not_executable(self):
        manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())
        expected = "a" * 40

        def fake_git(_root, args):
            if args == ["rev-parse", "HEAD"]:
                return expected
            if args == ["rev-parse", "HEAD^{tree}"]:
                return "b" * 40
            if args == ["status", "--porcelain=v1", "--untracked-files=normal"]:
                return " M tracked.txt"
            raise AssertionError(args)

        fake_result = {
            "exit_code": 0,
            "signal": None,
            "timed_out": False,
            "cancelled": False,
            "stdout": b" M tracked.txt\n",
            "stderr": b"",
            "stdout_bytes_seen": 15,
            "stderr_bytes_seen": 0,
            "stdout_sha256": hashlib.sha256(b" M tracked.txt\n").hexdigest(),
            "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "stdout_truncated": False,
            "stderr_truncated": False,
            "duration_ms": 1,
        }
        cfg = {
            "source_roots": {"workspace-control": "/repo"},
            "worker_uid": 41001,
            "worker_gid": 41001,
            "scratch_root": "/scratch",
            "receipt_root": "/receipts",
            "frontend_gid": os.getgid(),
        }
        inspect_request = {
            "schema": "workspace-shell-job-request.v1",
            "operation": "exec",
            "task_id": "task-abc",
            "target": "workspace-control",
            "expected_sha": expected,
            "profile": "git-read",
            "argv": ["status", "--porcelain=v1", "--untracked-files=normal"],
            "cwd": ".",
            "timeout_ms": 1000,
            "request_id": "request-one",
        }

        with patch.object(job_launcher, "verify_source_tree", return_value=Path("/repo")), \
             patch.object(job_launcher, "hardened_git", side_effect=fake_git), \
             patch.object(job_launcher, "require_secure_directory", return_value=Path("/scratch")), \
             patch.object(job_launcher, "build_bwrap_command", return_value=["/usr/bin/true"]), \
             patch.object(job_launcher, "build_systemd_run_command", return_value=["/usr/bin/true"]), \
             patch.object(job_launcher, "bounded_run", return_value=fake_result), \
             patch.object(job_launcher, "cleanup_state", return_value="COLLECTED"), \
             patch.object(job_launcher, "write_receipt", side_effect=lambda _root, receipt, **_kw: receipt):
            result = job_launcher.run_request(cfg, manifest, inspect_request)
        self.assertTrue(result["source_dirty"])

        executable_request = dict(inspect_request)
        executable_request.update({
            "profile": "pytest-bounded",
            "argv": ["tests/test_workspace_shell_contract.py", "-q"],
        })
        with patch.object(job_launcher, "verify_source_tree", return_value=Path("/repo")), \
             patch.object(job_launcher, "hardened_git", side_effect=fake_git):
            with self.assertRaisesRegex(
                runtime_common.ShellRuntimeError,
                "SOURCE_DIRTY",
            ):
                job_launcher.run_request(cfg, manifest, executable_request)

    def test_receipt_argv_redacts_pytest_expression(self):
        redacted = job_launcher.redact_argv(
            "pytest-bounded",
            ["-k", "secret_customer_name", "tests/test_example.py"],
        )
        self.assertEqual(
            redacted,
            ["-k", "[redacted-expression]", "tests/test_example.py"],
        )

    def test_replay_journal_is_single_use_before_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            db = root_broker.ensure_replay_db(
                {"replay_db": str(Path(td) / "replay.sqlite3")},
                expected_owner_uid=os.getuid(),
            )
            verified = {
                "approval_id": "approval-one",
                "nonce": "nonce-one",
                "idempotency_key": "idem-one",
            }
            root_broker.consume_replay(db, verified)
            with self.assertRaisesRegex(
                runtime_common.ShellRuntimeError, "APPROVAL_REPLAY"
            ):
                root_broker.consume_replay(db, verified)

    def test_bounded_output_hashes_full_stream_even_when_return_is_truncated(self):
        payload = b"a" * 100_000
        result = runtime_common.bounded_run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "sys.stdout.buffer.write(b'a'*100000); "
                    "sys.stdout.flush()"
                ),
            ],
            timeout_s=5,
            stdout_limit=1024,
            stderr_limit=1024,
        )
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout_bytes_seen"], len(payload))
        self.assertTrue(result["stdout_truncated"])
        self.assertEqual(len(result["stdout"]), 1024)
        self.assertEqual(
            result["stdout_sha256"],
            hashlib.sha256(payload).hexdigest(),
        )

    def test_timeout_kills_nested_process_group(self):
        script = (
            "import subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-c',"
            "'import time; time.sleep(30)']); "
            "print(p.pid, flush=True); time.sleep(30)"
        )
        result = runtime_common.bounded_run(
            [sys.executable, "-c", script],
            timeout_s=0.35,
            stdout_limit=4096,
            stderr_limit=4096,
        )
        self.assertTrue(result["timed_out"])
        child_pid = int(result["stdout"].decode().splitlines()[0])

        ended = False
        for _ in range(50):
            proc_path = Path(f"/proc/{child_pid}")
            if not proc_path.exists():
                ended = True
                break
            try:
                state = (proc_path / "stat").read_text().split()[2]
                if state == "Z":
                    ended = True
                    break
            except FileNotFoundError:
                ended = True
                break
            time.sleep(0.02)
        self.assertTrue(
            ended,
            f"nested child {child_pid} survived timeout process-group kill",
        )

    def test_root_broker_exec_fd_rejects_final_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            helper = td / "helper"
            helper.write_text("#!/bin/sh\nexit 0\n")
            helper.chmod(0o755)
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            fd = root_broker.open_verified_helper(str(helper), digest)
            os.close(fd)

            link = td / "link"
            link.symlink_to(helper)
            with self.assertRaises(OSError):
                root_broker.open_verified_helper(str(link), digest)

    def test_control_plane_code_freezes_peer_identity_and_ordering(self):
        launcher = (ROOT_CODE / "job_launcher.py").read_text()
        broker = (ROOT_CODE / "root_broker.py").read_text()
        server = (PLUGIN / "server.js").read_text()
        verifier = (
            PLUGIN / "bin" / "verify-broker-request.mjs"
        ).read_text()

        self.assertIn("SO_PEERCRED", launcher)
        self.assertIn("SO_PEERCRED", broker)
        self.assertIn('uid != int(cfg["frontend_uid"])', launcher)
        self.assertIn('peer_uid != int(cfg["frontend_uid"])', broker)
        handle = broker[broker.index("def handle_request"):broker.index("def serve")]
        self.assertLess(
            handle.index("consume_replay(replay_db, verified)"),
            handle.index("execute_helper(cfg, verified, cancel_check=cancel_check)"),
        )
        self.assertIn("requestCert: true", server)
        self.assertIn("rejectUnauthorized: true", server)
        self.assertIn(
            "process.getuid() !== config.frontend_uid",
            server,
        )
        self.assertIn(
            "process.getgid() !== config.frontend_gid",
            server,
        )
        self.assertIn("expectedGid: config.frontend_gid", server)
        self.assertNotIn("WORKSPACE_SHELL_DEV_INSECURE", server)
        self.assertIn("FRONTEND_SIGNATURE_INVALID", verifier)
        self.assertIn("APPROVAL_SIGNATURE_INVALID", verifier)
        self.assertIn("APPROVAL_REVOKED", verifier)
        self.assertIn("HELPER_PATH_ESCAPE", verifier)
        self.assertNotIn("shell=True", launcher)
        self.assertNotIn("shell=True", broker)


if __name__ == "__main__":
    unittest.main()
