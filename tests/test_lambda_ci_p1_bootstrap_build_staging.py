import importlib.util
import os
import pathlib
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_bootstrap_install.py"


def load_module():
    spec = importlib.util.spec_from_file_location("p1_bootstrap_build_staging", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1BootstrapBuildStagingTests(unittest.TestCase):
    def test_build_root_is_private_and_owned_before_runuser_build(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            repo = root / "repo"
            src = repo / "controller" / "lambda-ci-controller"
            src.mkdir(parents=True)
            (src / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
            (src / "go.mod").write_text("module example.invalid/test\ngo 1.26.3\n", encoding="utf-8")

            fake_go = root / "go"
            fake_go.write_text("", encoding="utf-8")
            module.GO_BIN = fake_go

            build_root = root / "build"
            build_root.mkdir(mode=0o700)

            controller = types.SimpleNamespace(pw_uid=1234, pw_gid=5678)
            events = []
            real_chmod = os.chmod

            def fake_chown(path, uid, gid):
                events.append(("chown", pathlib.Path(path), uid, gid))

            def fake_chmod(path, mode, *args, **kwargs):
                events.append(("chmod", pathlib.Path(path), mode))
                real_chmod(path, mode, *args, **kwargs)

            def fake_run(argv, **kwargs):
                if argv == [str(fake_go), "env", "GOVERSION"]:
                    return module.subprocess.CompletedProcess(
                        args=argv, returncode=0, stdout="go1.26.3\n", stderr=""
                    )

                self.assertEqual(kwargs.get("user"), "ci-controller")
                self.assertIn(
                    ("chown", build_root, controller.pw_uid, controller.pw_gid),
                    events,
                )
                self.assertIn(("chmod", build_root, 0o700), events)

                out = pathlib.Path(argv[argv.index("-o") + 1])
                out.touch()
                return module.subprocess.CompletedProcess(
                    args=argv, returncode=0, stdout="", stderr=""
                )

            with mock.patch.object(
                module.tempfile, "mkdtemp", return_value=str(build_root)
            ), mock.patch.object(
                module.pwd, "getpwnam", return_value=controller
            ), mock.patch.object(
                module.os, "chown", side_effect=fake_chown
            ), mock.patch.object(
                module.os, "chmod", side_effect=fake_chmod
            ), mock.patch.object(
                module, "run", side_effect=fake_run
            ):
                output = module.build_controller(repo)

            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
