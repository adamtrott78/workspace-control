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
    def test_user_switch_uses_absolute_runuser_with_sanitized_path(self):
        module = load_module()
        completed = module.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with mock.patch.object(
            module.subprocess, "run", return_value=completed
        ) as subprocess_run:
            module.run(
                ["echo", "ok"],
                user="ci-controller",
                env={"PATH": "/usr/bin:/bin"},
            )

        command = subprocess_run.call_args.args[0]
        self.assertEqual(command[0], "/usr/sbin/runuser")
        self.assertEqual(
            command,
            ["/usr/sbin/runuser", "-u", "ci-controller", "--", "echo", "ok"],
        )

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

    def test_bootstrap_itself_does_not_activate_workspace_control(self):
        raw = SCRIPT.read_text(encoding="utf-8")

        self.assertNotIn(
            'systemctl", "enable", "--now", '
            '"workspace-ci-controller@workspace-control-cpu.service"',
            raw,
        )
        self.assertIn('"activation_performed": False', raw)
        self.assertIn('"capacity_changed": False', raw)
        self.assertIn('"p2_p3_authority_changed": False', raw)

    def test_recovered_research_cpu_is_preserved_not_mutated(self):
        module = load_module()
        self.assertIn(module.RESEARCH_CPU, module.HEALTHY_CONTROLLERS)
        self.assertNotIn(module.RESEARCH_CPU, module.MUTATED_SERVICES)

        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('run(["systemctl", "restart", RESEARCH_CPU])', raw)
        self.assertNotIn('run(["systemctl", "stop", RESEARCH_CPU])', raw)
        self.assertIn(
            '_verify_preserved_services(manifest["preserved_services"])',
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

    def test_only_reconcile_controller_is_frozen_before_binary_replacement(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        freeze = raw.index('run(["systemctl", "stop", RECONCILE_CONTROLLER])')
        install_binary = raw.index(
            "install_file(\n            built_controller,"
        )
        self.assertLess(freeze, install_binary)
        self.assertNotIn('run(["systemctl", "stop", RESEARCH_CPU])', raw)

    def test_research_cpu_must_be_recovered_and_stable_before_mutation(self):
        module = load_module()
        stable = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": str(module.RESEARCH_CPU_RECOVERED_MIN_RESTARTS),
            "ExecMainStatus": "0",
        }
        with mock.patch.object(
            module,
            "service_snapshot",
            side_effect=[stable, stable.copy()],
        ), mock.patch.object(module.time, "sleep") as sleep:
            self.assertEqual(
                module.verify_research_cpu_recovered_and_stable(),
                stable,
            )
        sleep.assert_called_once_with(module.RESEARCH_CPU_STABILITY_SECONDS)

        unhealthy = dict(stable)
        unhealthy["ActiveState"] = "activating"
        unhealthy["SubState"] = "auto-restart"
        unhealthy["ExecMainStatus"] = "1"
        with mock.patch.object(module, "service_snapshot", return_value=unhealthy):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "does not match reviewed recovered state",
            ):
                module.verify_research_cpu_recovered_and_stable()

        changed = dict(stable)
        changed["NRestarts"] = str(
            module.RESEARCH_CPU_RECOVERED_MIN_RESTARTS + 1
        )
        with mock.patch.object(
            module,
            "service_snapshot",
            side_effect=[stable, changed],
        ), mock.patch.object(module.time, "sleep"):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "restart count changed",
            ):
                module.verify_research_cpu_recovered_and_stable()

    def test_recovered_cpu_baseline_cannot_rebase_before_mutation(self):
        module = load_module()
        expected = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "11551",
            "ExecMainStatus": "0",
        }
        rebased = dict(expected)
        rebased["NRestarts"] = "11552"
        with self.assertRaisesRegex(
            module.BootstrapError,
            "restart count changed after stability check",
        ):
            module.assert_research_cpu_preserved_baseline(
                expected,
                {module.RESEARCH_CPU: rebased},
            )

    def test_recovered_cpu_failure_at_backup_boundary_aborts(self):
        module = load_module()
        expected = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "11551",
            "ExecMainStatus": "0",
        }
        failed = dict(expected)
        failed["ActiveState"] = "failed"
        failed["SubState"] = "failed"
        failed["ExecMainStatus"] = "1"
        with self.assertRaisesRegex(
            module.BootstrapError,
            "no longer satisfies recovered predicate",
        ):
            module.assert_research_cpu_preserved_baseline(
                expected,
                {module.RESEARCH_CPU: failed},
            )

    def test_preserved_live_recheck_catches_post_backup_restart(self):
        module = load_module()
        baseline = {
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "UnitFileState": "enabled",
            "NRestarts": "11551",
            "ExecMainStatus": "0",
        }
        restarted = dict(baseline)
        restarted["NRestarts"] = "11552"
        with mock.patch.object(
            module,
            "service_snapshot",
            return_value=restarted,
        ):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "preserved controller restart count changed",
            ):
                module._verify_preserved_services(
                    {module.RESEARCH_CPU: baseline}
                )

    def test_recovered_cpu_rechecks_are_immediately_before_mutation(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        backup = raw.index("manifest = backup_targets(backup)")
        bind = raw.index("assert_research_cpu_preserved_baseline(", backup)
        live = raw.index(
            '_verify_preserved_services(manifest["preserved_services"])',
            bind,
        )
        mutate = raw.index("begin_mutation_phase(manifest)", live)
        self.assertLess(backup, bind)
        self.assertLess(bind, live)
        self.assertLess(live, mutate)
        between = raw[live:mutate]
        self.assertNotIn("install_file(", between)
        self.assertNotIn("systemctl", between)

    def test_failure_freezing_reconcile_controller_rolls_back(self):
        module = load_module()
        manifest = {"sentinel": True}
        with mock.patch.object(
            module,
            "run",
            side_effect=module.BootstrapError("freeze failed"),
        ), mock.patch.object(module, "restore_targets") as restore:
            with self.assertRaisesRegex(module.BootstrapError, "freeze failed"):
                module.begin_mutation_phase(manifest)
        restore.assert_called_once_with(manifest)

    def test_mutation_phase_has_no_second_project_controller_stop(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        freeze_body = raw.split("def freeze_for_install()", 1)[1].split(
            "def begin_mutation_phase(", 1
        )[0]
        self.assertIn(
            'run(["systemctl", "stop", RECONCILE_CONTROLLER])',
            freeze_body,
        )
        self.assertNotIn("RESEARCH_CPU", freeze_body)

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

    def test_maintenance_socket_waits_for_actual_readiness(self):
        module = load_module()
        path = mock.Mock()
        path.is_socket.side_effect = [False, False, True]
        with mock.patch.object(
            module, "service_active", return_value=True
        ), mock.patch.object(
            module.time, "monotonic", side_effect=[0.0, 0.1, 0.2]
        ), mock.patch.object(module.time, "sleep") as sleep:
            module.wait_for_socket_ready(
                module.MAINTENANCE_ROOT,
                path,
                timeout_seconds=1,
            )
        self.assertEqual(sleep.call_count, 2)
        sleep.assert_has_calls(
            [
                mock.call(module.MAINTENANCE_SOCKET_READY_POLL_SECONDS),
                mock.call(module.MAINTENANCE_SOCKET_READY_POLL_SECONDS),
            ]
        )

    def test_maintenance_socket_wait_fails_if_service_exits(self):
        module = load_module()
        path = mock.Mock()
        path.is_socket.return_value = False
        failed = {
            "LoadState": "loaded",
            "ActiveState": "failed",
            "SubState": "failed",
            "UnitFileState": "enabled",
            "NRestarts": "0",
            "ExecMainStatus": "1",
        }
        with mock.patch.object(
            module, "service_active", return_value=False
        ), mock.patch.object(
            module, "service_snapshot", return_value=failed
        ):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "exited before socket became ready",
            ):
                module.wait_for_socket_ready(
                    module.MAINTENANCE_ROOT,
                    path,
                    timeout_seconds=1,
                )

    def test_maintenance_socket_wait_is_bounded(self):
        module = load_module()
        path = mock.Mock()
        path.is_socket.return_value = False
        with mock.patch.object(
            module, "service_active", return_value=True
        ), mock.patch.object(
            module.time, "monotonic", side_effect=[0.0, 1.0]
        ), mock.patch.object(module.time, "sleep") as sleep:
            with self.assertRaisesRegex(
                module.BootstrapError,
                "socket did not become ready within 1s",
            ):
                module.wait_for_socket_ready(
                    module.MAINTENANCE_ROOT,
                    path,
                    timeout_seconds=1,
                )
        sleep.assert_not_called()

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
