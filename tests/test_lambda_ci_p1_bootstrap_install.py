import importlib.util
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_bootstrap_install.py"


def load_module():
    spec = importlib.util.spec_from_file_location("p1_bootstrap", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1BootstrapInstallerTests(unittest.TestCase):
    def test_runuser_is_absolute_and_independent_of_narrow_child_path(self):
        module = load_module()
        self.assertEqual(module.RUNUSER_BIN, pathlib.Path("/usr/sbin/runuser"))

        completed = mock.Mock()
        completed.returncode = 0
        completed.stdout = ""
        completed.stderr = ""
        with mock.patch.object(module.RUNUSER_BIN, "is_file", return_value=True), mock.patch.object(
            module.subprocess, "run", return_value=completed
        ) as proc:
            module.run(
                ["/opt/workspace-ci/go/1.26.3/bin/go", "version"],
                user="ci-controller",
                env={"PATH": "/opt/workspace-ci/go/1.26.3/bin:/usr/bin:/bin"},
            )

        command = proc.call_args.args[0]
        self.assertEqual(command[0], "/usr/sbin/runuser")
        self.assertEqual(command[1:4], ["-u", "ci-controller", "--"])

    def test_missing_absolute_runuser_fails_before_subprocess(self):
        module = load_module()
        with mock.patch.object(module.RUNUSER_BIN, "is_file", return_value=False), mock.patch.object(
            module.subprocess, "run"
        ) as proc:
            with self.assertRaisesRegex(
                module.BootstrapError,
                "required runuser binary is missing",
            ):
                module.run(["true"], user="ci-controller")
        proc.assert_not_called()

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
        self.assertNotIn("print(token)", raw)
        self.assertNotIn("repr(token)", raw)
        self.assertNotIn('"token": token', raw)

    def test_credential_scope_is_probed_before_first_mutation(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        scope = raw.index("verify_credential_scope()")
        freeze = raw.index('run(["systemctl", "stop", RECONCILE_CONTROLLER])')
        self.assertLess(scope, freeze)
        self.assertIn(
            '"/repos/adamtrott78/workspace-control/actions/runners?per_page=1"',
            raw,
        )
        self.assertIn(
            'f"/repos/adamtrott78/workspace-control/issues/{MAINTENANCE_ISSUE_NUMBER}"',
            raw,
        )

    def test_broken_cpu_lane_is_quiesced_before_binary_replacement(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        stop_cpu = raw.index('run(["systemctl", "stop", RESEARCH_CPU])')
        install_binary = raw.index(
            "install_file(\n            built_controller,"
        )
        self.assertLess(stop_cpu, install_binary)

    def test_research_cpu_must_still_match_unhealthy_preflight(self):
        module = load_module()
        healthy = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": str(module.RESEARCH_CPU_PREFLIGHT_MIN_RESTARTS + 10),
            "ExecMainStatus": "0",
        }
        with mock.patch.object(module, "service_snapshot", return_value=healthy):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "no longer matches reviewed unhealthy preflight",
            ):
                module.verify_research_cpu_still_unhealthy()

        unhealthy = {
            "LoadState": "loaded",
            "ActiveState": "activating",
            "SubState": "auto-restart",
            "UnitFileState": "enabled",
            "NRestarts": str(module.RESEARCH_CPU_PREFLIGHT_MIN_RESTARTS),
            "ExecMainStatus": "1",
        }
        with mock.patch.object(module, "service_snapshot", return_value=unhealthy):
            self.assertEqual(
                module.verify_research_cpu_still_unhealthy(),
                unhealthy,
            )

    def test_failure_at_first_stop_boundary_rolls_back(self):
        module = load_module()
        manifest = {"sentinel": True}
        with mock.patch.object(
            module,
            "run",
            side_effect=module.BootstrapError("first stop failed"),
        ), mock.patch.object(module, "restore_targets") as restore:
            with self.assertRaisesRegex(module.BootstrapError, "first stop failed"):
                module.begin_mutation_phase(manifest)
        restore.assert_called_once_with(manifest)

    def test_failure_at_second_stop_boundary_rolls_back(self):
        module = load_module()
        manifest = {"sentinel": True}
        calls = {"count": 0}

        def fake_run(*_args, **_kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise module.BootstrapError("second stop failed")
            return object()

        with mock.patch.object(module, "run", side_effect=fake_run), mock.patch.object(
            module, "restore_targets"
        ) as restore:
            with self.assertRaisesRegex(module.BootstrapError, "second stop failed"):
                module.begin_mutation_phase(manifest)
        restore.assert_called_once_with(manifest)

    def test_rollback_cannot_restart_preserved_controllers(self):
        module = load_module()
        self.assertTrue(set(module.HEALTHY_CONTROLLERS).isdisjoint(module.MUTATED_SERVICES))
        raw = SCRIPT.read_text(encoding="utf-8")
        restore_body = raw.split("def restore_targets(", 1)[1].split(
            "def rollback_after_failure(", 1
        )[0]
        self.assertNotIn("*HEALTHY_CONTROLLERS", restore_body)
        self.assertNotIn("restart", restore_body.split("_verify_preserved_services", 1)[-1])

    def test_incomplete_rollback_is_reported_and_not_claimed_complete(self):
        module = load_module()
        with mock.patch.object(
            module,
            "restore_targets",
            side_effect=module.BootstrapError("restore failed"),
        ), mock.patch.object(module, "print") as printed:
            with self.assertRaisesRegex(module.BootstrapError, "rollback was incomplete"):
                module.rollback_after_failure({}, RuntimeError("bootstrap failed"))
        rendered = [" ".join(str(arg) for arg in call.args) for call in printed.call_args_list]
        self.assertTrue(any("P1_BOOTSTRAP_ROLLBACK=INCOMPLETE" in x for x in rendered))
        self.assertFalse(any("P1_BOOTSTRAP_ROLLBACK=COMPLETE" in x for x in rendered))

    def test_commissioning_pass_is_rejected(self):
        module = load_module()
        with self.assertRaisesRegex(
            module.BootstrapError,
            "first-poll invariant failed",
        ):
            module.validate_commissioning_result({"status": "PASS"})
        module.validate_commissioning_result(
            {"status": "INITIALIZED_NO_COMMANDS_EXECUTED"}
        )

    def test_final_reconcile_controller_gate_fails_closed(self):
        module = load_module()
        with mock.patch.object(module, "service_active", return_value=True):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "active at bootstrap success gate",
            ):
                module.assert_reconcile_controller_frozen()
        with mock.patch.object(module, "service_active", return_value=False):
            module.assert_reconcile_controller_frozen()

    def test_l0_commissioning_executes_no_historical_commands(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"--once"', raw)
        self.assertIn('"INITIALIZED_NO_COMMANDS_EXECUTED"', raw)
        self.assertIn('"maintenance_controller_active"', raw)
        self.assertIn("if cursor_path.exists():", raw)
        self.assertIn("validate_commissioning_result(once_json)", raw)


if __name__ == "__main__":
    unittest.main()
