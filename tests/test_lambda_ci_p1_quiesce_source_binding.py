import importlib.util
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_quiesce_restart_storm.py"


def load_module():
    spec = importlib.util.spec_from_file_location("p1_quiesce_source_binding", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1QuiesceSourceBindingTests(unittest.TestCase):
    def test_external_helper_cannot_pass_attestation_or_reach_quiesce(self):
        module = load_module()
        with mock.patch.object(
            module.os, "geteuid", return_value=0
        ), mock.patch.dict(
            module.os.environ, {"SUDO_USER": "atrott"}, clear=False
        ), mock.patch.object(
            module.sys,
            "argv",
            ["copied-helper.py", "--expected-head", "deadbeef"],
        ), mock.patch.object(
            module, "__file__", "/tmp/copied-helper.py"
        ), mock.patch.object(
            module, "quiesce_and_verify"
        ) as quiesce:
            with self.assertRaisesRegex(
                module.QuiesceError,
                "outside the reviewed tracked helper path",
            ):
                module.main()
        quiesce.assert_not_called()


if __name__ == "__main__":
    unittest.main()
