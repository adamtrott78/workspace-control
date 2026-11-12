import importlib.util
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


broker = load(
    "lambda_ci_v3_payload_broker",
    ROOT / "scripts" / "lambda_ci_v3_payload_broker.py",
)
client = load(
    "lambda_ci_v3_payload_exec",
    ROOT / "scripts" / "lambda_ci_v3_payload_exec.py",
)


class V3PayloadProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.runtime = self.base / "runtime"
        (self.runtime / "bin").mkdir(parents=True)
        self.python = self.runtime / "bin/python"
        self.python.write_text("#!/bin/sh\n")
        self.python.chmod(0o555)
        self.job = self.base / "job"
        self.staging = self.base / "staging"
        self.job.mkdir()
        self.staging.mkdir()

    def test_request_accepts_only_exact_runtime_python_and_bounded_cwd(self):
        argv, cwd = broker.validate_request(
            {
                "argv": [str(self.python), "script.py", "--model", "/model"],
                "cwd": str(self.job),
            },
            runtime_python=self.python,
            allowed_cwd_roots=(self.job, self.staging),
        )
        self.assertEqual(argv[0], str(self.python))
        self.assertEqual(cwd, self.job.resolve())

        other = self.base / "other"
        other.mkdir()
        with self.assertRaisesRegex(broker.PayloadBrokerError, "cwd escapes"):
            broker.validate_request(
                {"argv": [str(self.python), "script.py"], "cwd": str(other)},
                runtime_python=self.python,
                allowed_cwd_roots=(self.job, self.staging),
            )
        with self.assertRaisesRegex(broker.PayloadBrokerError, "root-bound runtime"):
            broker.validate_request(
                {"argv": ["/usr/bin/python3", "script.py"], "cwd": str(self.job)},
                runtime_python=self.python,
                allowed_cwd_roots=(self.job, self.staging),
            )

    def test_cwd_symlink_escape_is_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        escape = self.job / "escape"
        escape.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(broker.PayloadBrokerError, "cwd escapes"):
            broker.validate_request(
                {"argv": [str(self.python)], "cwd": str(escape)},
                runtime_python=self.python,
                allowed_cwd_roots=(self.job, self.staging),
            )

    def test_broker_environment_filters_runner_credentials(self):
        source = {
            "PATH": "/usr/bin",
            "HOME": "/tmp/home",
            "P5_MODEL_PATH": "/model",
            "HF_HUB_OFFLINE": "1",
            "GH_TOKEN": "secret",
            "GITHUB_TOKEN": "secret2",
            "ACTIONS_RUNTIME_TOKEN": "secret3",
            "UNRELATED": "drop",
        }
        filtered = broker.safe_environment(source)
        self.assertEqual(
            filtered,
            {
                "PATH": "/usr/bin",
                "HOME": "/tmp/home",
                "P5_MODEL_PATH": "/model",
                "HF_HUB_OFFLINE": "1",
            },
        )

    def test_peer_pid_must_be_member_of_exact_runner_unit(self):
        proc = self.base / "proc"
        pid_dir = proc / "321"
        pid_dir.mkdir(parents=True)
        expected = (
            "workspace-ci-v3-research-model-single-offline-v1-"
            "11111111-2222-3333-4444-555555555555.service"
        )
        pid_dir.joinpath("cgroup").write_text(
            f"0::/system.slice/{expected}\n"
        )
        self.assertTrue(
            broker.peer_in_expected_unit(321, expected, proc_root=proc)
        )
        self.assertFalse(
            broker.peer_in_expected_unit(
                321,
                "workspace-ci-v3-research-model-dual-offline-v1-"
                "11111111-2222-3333-4444-555555555555.service",
                proc_root=proc,
            )
        )

    def test_broker_main_exposes_exchange_only_not_job_or_staging_root(self):
        source = (
            ROOT / "scripts" / "lambda_ci_v3_payload_broker.py"
        ).read_text()
        self.assertIn("--exchange-root", source)
        self.assertNotIn("--job-root", source)
        self.assertNotIn("--staging-root", source)

    def test_client_source_never_serializes_runner_environment(self):
        source = (ROOT / "scripts" / "lambda_ci_v3_payload_exec.py").read_text()
        self.assertNotIn("os.environ.items", source)
        self.assertNotIn('"env":', source)
        self.assertIn('{"argv": argv, "cwd":', source)


if __name__ == "__main__":
    unittest.main()
