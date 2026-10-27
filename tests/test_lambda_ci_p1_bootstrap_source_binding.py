import importlib.util
import types
import unittest
from unittest import mock

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_bootstrap_install.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "p1_bootstrap_source_binding", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1BootstrapSourceBindingTests(unittest.TestCase):
    def test_external_installer_fails_before_any_preflight_or_mutation_path(self):
        module = load_module()
        invoker = types.SimpleNamespace(pw_dir="/home/atrott")

        with mock.patch.object(
            module.os, "geteuid", return_value=0
        ), mock.patch.dict(
            module.os.environ, {"SUDO_USER": "atrott"}, clear=False
        ), mock.patch.object(
            module.sys,
            "argv",
            ["copied-installer.py", "--expected-head", "deadbeef"],
        ), mock.patch.object(
            module, "__file__", "/tmp/copied-installer.py"
        ), mock.patch.object(
            module.pwd, "getpwnam", return_value=invoker
        ), mock.patch.object(
            module, "verify_live_fingerprint"
        ) as fingerprint, mock.patch.object(
            module, "verify_credential_scope"
        ) as credentials, mock.patch.object(
            module, "build_controller"
        ) as build, mock.patch.object(
            module, "backup_targets"
        ) as backup, mock.patch.object(
            module, "begin_mutation_phase"
        ) as mutation:
            with self.assertRaisesRegex(
                module.BootstrapError,
                "outside the reviewed tracked installer path",
            ):
                module.main()

        fingerprint.assert_not_called()
        credentials.assert_not_called()
        build.assert_not_called()
        backup.assert_not_called()
        mutation.assert_not_called()


if __name__ == "__main__":
    unittest.main()
