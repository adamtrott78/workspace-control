from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
PROBE_PATH = (
    ROOT / "scripts" / "lambda_ci_v3_workspace_control_codex_zero_tool_probe_v1.py"
)


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "workspace_control_zero_tool_probe",
        PROBE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("probe import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


probe = _load_probe()


class WorkspaceControlCodexZeroToolProbeTests(unittest.TestCase):
    def test_probe_command_uses_app_server_and_local_non_auth_provider(self):
        command = probe._build_app_server_command(
            codex_bin="/trusted/codex",
            model="gpt-6-astra",
            model_catalog=Path("/trusted/models.json"),
            port=43123,
        )

        self.assertEqual(command[0], "/trusted/codex")
        self.assertIn("app-server", command)
        self.assertIn("stdio://", command)
        self.assertNotIn("exec", command)
        rendered = "\n".join(command)
        self.assertIn('model_provider="zero_tool_probe"', rendered)
        self.assertIn('http://127.0.0.1:43123/v1', rendered)
        self.assertIn('requires_openai_auth = false', rendered)
        self.assertIn('request_max_retries = 0', rendered)
        self.assertIn('stream_max_retries = 0', rendered)
        self.assertIn('supports_websockets = false', rendered)

    def test_probe_child_environment_strips_api_keys_and_python_injection(self):
        env = probe._child_environment(
            {
                "OPENAI_API_KEY": "secret",
                "CODEX_API_KEY": "secret",
                "PYTHONPATH": "/candidate",
                "PYTHONHOME": "/candidate-python",
                "SAFE": "yes",
            },
            probe_home=Path("/trusted/probe-home"),
        )

        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("CODEX_API_KEY", env)
        self.assertNotIn("PYTHONPATH", env)
        self.assertNotIn("PYTHONHOME", env)
        self.assertEqual(env["CODEX_HOME"], "/trusted/probe-home")
        self.assertEqual(env["SAFE"], "yes")

    def test_probe_request_validation_requires_exact_zero_tool_surface(self):
        good = {
            "path": "/v1/responses",
            "authorization_header_present": False,
            "body": {"model": "gpt-6-astra", "tools": []},
        }
        probe._validate_observed_request(good, model="gpt-6-astra")

        bad_cases = [
            {
                **good,
                "authorization_header_present": True,
            },
            {
                **good,
                "body": {
                    "model": "gpt-6-astra",
                    "tools": [{"type": "function", "name": "skills.list"}],
                },
            },
            {
                **good,
                "body": {"model": "gpt-6-astra"},
            },
            {
                **good,
                "path": "/unexpected",
            },
            {
                **good,
                "body": {"model": "other", "tools": []},
            },
        ]
        for case in bad_cases:
            with self.subTest(case=case):
                with self.assertRaises(probe.ProbeError):
                    probe._validate_observed_request(
                        case,
                        model="gpt-6-astra",
                    )

    def test_probe_home_copies_only_trusted_config_not_auth(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trusted = root / "trusted"
            temp_root = root / "temp"
            trusted.mkdir()
            temp_root.mkdir()
            (trusted / "config.toml").write_text(
                'forced_login_method = "chatgpt"\n'
                'cli_auth_credentials_store = "file"\n'
                '[orchestrator.skills]\n'
                'enabled = false\n',
                encoding="utf-8",
            )
            (trusted / "auth.json").write_text("SECRET", encoding="utf-8")

            home = probe._prepare_probe_home(
                trusted_codex_home=trusted,
                temp_root=temp_root,
            )

            self.assertFalse((home / "auth.json").exists())
            config = (home / "config.toml").read_text(encoding="utf-8")
            self.assertNotIn("forced_login_method", config)
            self.assertNotIn("cli_auth_credentials_store", config)
            self.assertIn("[orchestrator.skills]", config)
            self.assertIn("enabled = false", config)

    def test_python_isolated_self_test_does_not_execute_candidate_sitecustomize(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "candidate-executed"
            (root / "sitecustomize.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('BAD', encoding='utf-8')\n",
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                [sys.executable, "-I", str(PROBE_PATH), "--self-test"],
                cwd=root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(
                "WORKSPACE_CONTROL_CODEX_ZERO_TOOL_PROBE_SELF_TEST=PASS",
                completed.stdout,
            )
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
