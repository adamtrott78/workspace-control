import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_bootstrap_install.py"


def load_module():
    spec = importlib.util.spec_from_file_location("p1_bootstrap", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1BootstrapInstallerTests(unittest.TestCase):
    def test_bootstrap_is_bound_to_exact_preflight_and_maintenance_issue(self):
        module = load_module()
        self.assertEqual(module.MAINTENANCE_ISSUE_NUMBER, 527)
        self.assertEqual(
            module.EXPECTED_INSTALLED_SHA256[
                "/opt/workspace-ci/controller/lambda-ci-controller"
            ],
            "11b0aa8d16eceaabdb5d3cf92d2d9525722bd73ff98960665eb857b39f6ef837",
        )
        self.assertIn(
            "/var/lib/workspace-ci/controller/state",
            module.EXPECTED_ABSENT_PATHS,
        )
        self.assertIn(
            "/etc/workspace-ci/projects/workspace-control.json",
            module.EXPECTED_ABSENT_PATHS,
        )

    def test_bootstrap_keeps_workspace_control_dormant(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        manifest = (
            ROOT / "architecture/lambda-ci-project-workspace-control.v1.json"
        ).read_text(encoding="utf-8")
        registry = (
            ROOT / "architecture/lambda-ci-project-registry.v1.json"
        ).read_text(encoding="utf-8")

        self.assertIn('"status": "MIGRATION_CANDIDATE_NOT_INSTALLED"', manifest)
        self.assertIn('"activation_state": "PLANNED_NOT_BOUND"', manifest)
        self.assertIn('"activation_state": "MIGRATION_CANDIDATE_NOT_INSTALLED"', registry)
        self.assertNotIn(
            'systemctl", "enable", "--now", '
            '"workspace-ci-controller@workspace-control-cpu.service"',
            raw,
        )
        self.assertIn('"activation_performed": False', raw)
        self.assertIn('"capacity_changed": False', raw)
        self.assertIn('"p2_p3_authority_changed": False', raw)

    def test_only_preexisting_broken_controller_is_deliberately_restarted(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('run(["systemctl", "restart", RESEARCH_CPU])', raw)
        for healthy in (
            "workspace-ci-controller@research-engine-gpu.service",
            "workspace-ci-controller@padataset-cpu.service",
            "workspace-ci-controller@padataset-gpu.service",
        ):
            self.assertNotIn(
                f'run(["systemctl", "restart", "{healthy}"])',
                raw,
            )

    def test_automatic_reconciliation_is_frozen_before_policy_install(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        freeze = raw.index('run(["systemctl", "stop", RECONCILE_CONTROLLER])')
        install_registry = raw.index(
            '"architecture/lambda-ci-project-registry.v1.json"'
        )
        self.assertLess(freeze, install_registry)
        self.assertIn('"automatic_reconcile_controller_frozen"', raw)
        self.assertIn('"RECONCILE_CONTROLLER_FROZEN=true"', raw)

    def test_rollback_and_credential_nonexposure_are_explicit(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("def restore_targets(", raw)
        self.assertIn("P1_BOOTSTRAP_ROLLBACK=BEGIN", raw)
        self.assertIn("P1_BOOTSTRAP_ROLLBACK=COMPLETE", raw)
        self.assertIn('"credential_contents_exposed": False', raw)
        self.assertNotIn("print(data)", raw)
        self.assertNotIn(".decode(", raw)

    def test_l0_commissioning_executes_no_historical_commands(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"--once"', raw)
        self.assertIn('"INITIALIZED_NO_COMMANDS_EXECUTED"', raw)
        self.assertIn('"maintenance_controller_active"', raw)


if __name__ == "__main__":
    unittest.main()
