import importlib.util
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compiler = load_module(
    "lambda_ci_policy_compiler_runner_identity_test",
    "scripts/lambda_ci_policy_compiler.py",
)
sys.modules["lambda_ci_policy_compiler"] = compiler
reconciler = load_module(
    "lambda_ci_v3_reconciler_runner_identity_test",
    "scripts/lambda_ci_v3_reconciler.py",
)


class PADatasetDualLaneRunnerIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)
        cls.root = cls.compiled["root_projection"]
        cls.a = cls.root["runner_classes"]["padataset-scientific-single-gpu-v1"]
        cls.b = cls.root["runner_classes"]["padataset-scientific-single-gpu-2-v1"]
        cls.migration = json.loads(
            (ROOT / "architecture/lambda-ci-v3-migration-plan.v1.json").read_text()
        )

    def test_scientific_lanes_have_distinct_runner_uids(self):
        self.assertEqual(
            self.a["project_runner_identity"],
            {"user": "ci-padataset", "group": "ci-padataset"},
        )
        self.assertEqual(
            self.b["project_runner_identity"],
            {"user": "ci-padataset-2", "group": "ci-padataset"},
        )
        self.assertNotEqual(
            self.a["project_runner_identity"]["user"],
            self.b["project_runner_identity"]["user"],
        )

    def test_lane_b_systemd_envelope_uses_dedicated_runner_uid(self):
        self.assertEqual(self.a["systemd_common"]["User"], "ci-padataset")
        self.assertEqual(self.a["systemd_common"]["Group"], "ci-padataset")
        self.assertEqual(self.b["systemd_common"]["User"], "ci-padataset-2")
        self.assertEqual(self.b["systemd_common"]["Group"], "ci-padataset")

    def test_sysusers_materializes_lane_b_with_project_primary_group(self):
        rendered = reconciler.render_sysusers(self.compiled, self.migration)
        self.assertIn(
            'u ci-padataset-2 -:ci-padataset "Workspace CI v3 runner padataset" - /usr/sbin/nologin',
            rendered,
        )

    def test_runner_uid_does_not_collide_with_lane_b_controller_uid(self):
        self.assertNotEqual(
            self.b["project_runner_identity"]["user"],
            self.b["controller_peer"]["unix_user"],
        )
        self.assertEqual(
            self.b["controller_peer"]["unix_user"],
            "ci-ctl-pad-science-2",
        )

    def test_runtime_keeps_uid_scoped_concurrency_and_cleanup_guards(self):
        source = (ROOT / "scripts/lambda_ci_runtime.py").read_text()
        self.assertIn('run(["pgrep", "-u", str(row.pw_uid)], check=False)', source)
        self.assertIn(
            'f"existing project process detected for {user}; refusing concurrency"',
            source,
        )
        self.assertIn('run(["pkill", "-KILL", "-u", str(uid)], check=False)', source)


if __name__ == "__main__":
    unittest.main()
