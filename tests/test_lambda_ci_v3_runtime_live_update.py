import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reconciler = load(
    "lambda_ci_v3_reconciler_runtime_override_tests",
    SCRIPTS / "lambda_ci_v3_reconciler.py",
)
UPDATER = SCRIPTS / "lambda_ci_v3_runtime_live_update_v1.py"


class RuntimeLiveUpdateContractTests(unittest.TestCase):
    def test_updater_is_narrow_transactional_and_provisioner_only(self):
        text = UPDATER.read_text(encoding="utf-8")
        self.assertIn(
            'BASE_SOURCE_HEAD = "09c46818252991f6a55aaeedbcf046c554e2ffee"',
            text,
        )
        self.assertIn(
            '/opt/workspace-ci/v3/provisioner/lambda_ci_runtime.py',
            text,
        )
        self.assertIn("V3_RUNTIME_OVERRIDE", text)
        self.assertIn("runtime-refresh", text)
        self.assertIn("verify_effective_installed_generation", text)
        self.assertIn("run_installed_reconciler_verify", text)
        self.assertIn("assert_no_class_controller_state", text)
        self.assertIn("assert_generation_drained", text)
        self.assertIn('systemctl("stop", PROVISIONER_UNIT)', text)
        self.assertIn('systemctl("start", PROVISIONER_UNIT)', text)
        self.assertNotIn('systemctl("start", RECONCILER_UNIT)', text)
        self.assertNotIn('systemctl("stop", RECONCILER_UNIT)', text)
        self.assertNotIn("ACTIVATE_ONE_V3_CANARY", text)
        self.assertNotIn("ACTIVATE_V3_ROOT_SERVICES", text)
        self.assertNotIn("gh api", text)
        self.assertNotIn("workflow_dispatch", text)

    def test_reconciler_accepts_exact_root_attested_runtime_override(self):
        with tempfile.TemporaryDirectory() as raw:
            root = pathlib.Path(raw)
            controller = root / "lambda-ci-controller-v3"
            controller.write_bytes(b"base-controller")
            controller.chmod(0o755)

            rec = root / "lambda_ci_v3_reconciler.py"
            rec.write_bytes(b"base-reconciler")
            rec.chmod(0o755)

            runtime = root / "lambda_ci_runtime.py"
            runtime.write_bytes(b"candidate-runtime")
            runtime.chmod(0o644)

            manifest = root / "install-manifest.json"
            payload = {
                "schema_version": 1,
                "mode": "V3_SUBSTRATE_INSTALL_INACTIVE",
                "source_head": "a" * 40,
                "root_policy_sha256": "b" * 64,
                "runner_class_count": 9,
                "entries": [
                    {
                        "destination": str(controller),
                        "sha256": reconciler._sha256(b"base-controller"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(rec),
                        "sha256": reconciler._sha256(b"base-reconciler"),
                        "mode": "0755",
                    },
                    {
                        "destination": str(runtime),
                        "sha256": reconciler._sha256(b"base-runtime"),
                        "mode": "0644",
                    },
                ],
            }
            manifest.write_bytes(reconciler._canonical(payload))

            receipt = root / "runtime-active.json"
            receipt.write_bytes(
                reconciler._canonical(
                    {
                        "schema_version": 1,
                        "mode": "V3_RUNTIME_OVERRIDE",
                        "phase": "ACTIVE",
                        "base_source_head": "a" * 40,
                        "runtime_source_head": "d" * 40,
                        "base_install_manifest_sha256": reconciler._sha256(
                            manifest.read_bytes()
                        ),
                        "base_runtime_sha256": reconciler._sha256(b"base-runtime"),
                        "runtime_sha256": reconciler._sha256(b"candidate-runtime"),
                        "runtime_mode": "0644",
                        "runtime_git_blob": "e" * 40,
                        "root_policy_sha256": "b" * 64,
                        "non_runtime_generation_equivalent": True,
                    }
                )
            )
            receipt.chmod(0o600)

            old_controller = reconciler.V3_CONTROLLER_BINARY
            old_rec = reconciler.RECONCILER_SCRIPT
            old_runtime = reconciler.V3_RUNTIME_SCRIPT
            old_receipt = reconciler.RUNTIME_OVERRIDE_ACTIVE_RECEIPT
            try:
                reconciler.V3_CONTROLLER_BINARY = controller
                reconciler.RECONCILER_SCRIPT = rec
                reconciler.V3_RUNTIME_SCRIPT = runtime
                reconciler.RUNTIME_OVERRIDE_ACTIVE_RECEIPT = receipt
                reconciler.verify_installed(manifest)
            finally:
                reconciler.V3_CONTROLLER_BINARY = old_controller
                reconciler.RECONCILER_SCRIPT = old_rec
                reconciler.V3_RUNTIME_SCRIPT = old_runtime
                reconciler.RUNTIME_OVERRIDE_ACTIVE_RECEIPT = old_receipt


if __name__ == "__main__":
    unittest.main()
