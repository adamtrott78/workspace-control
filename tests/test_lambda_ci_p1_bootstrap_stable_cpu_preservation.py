import importlib.util
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_bootstrap_install.py"


def load_module():
    spec = importlib.util.spec_from_file_location("p1_bootstrap_stable_cpu", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1BootstrapStableCpuPreservationTests(unittest.TestCase):
    def test_stable_active_inactive_and_failed_states_are_accepted(self):
        module = load_module()
        states = [
            {
                "LoadState": "loaded",
                "ActiveState": "active",
                "SubState": "running",
                "UnitFileState": "enabled",
                "NRestarts": "11551",
                "ExecMainStatus": "0",
            },
            {
                "LoadState": "loaded",
                "ActiveState": "inactive",
                "SubState": "dead",
                "UnitFileState": "enabled",
                "NRestarts": "11551",
                "ExecMainStatus": "0",
            },
            {
                "LoadState": "loaded",
                "ActiveState": "failed",
                "SubState": "failed",
                "UnitFileState": "enabled",
                "NRestarts": "11551",
                "ExecMainStatus": "1",
            },
        ]
        for state in states:
            with self.subTest(active_state=state["ActiveState"]):
                self.assertTrue(module._research_cpu_stable_state_predicate(state))
                with mock.patch.object(
                    module,
                    "service_snapshot",
                    side_effect=[state, state.copy()],
                ), mock.patch.object(module.time, "sleep") as sleep:
                    self.assertEqual(module.verify_research_cpu_stable_state(), state)
                sleep.assert_called_once_with(module.RESEARCH_CPU_STABILITY_SECONDS)

    def test_transitional_state_is_rejected_before_mutation(self):
        module = load_module()
        transitional = {
            "LoadState": "loaded",
            "ActiveState": "activating",
            "SubState": "auto-restart",
            "UnitFileState": "enabled",
            "NRestarts": "11551",
            "ExecMainStatus": "1",
        }
        with mock.patch.object(module, "service_snapshot", return_value=transitional):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "transitional or outside the reviewed stable preservation states",
            ):
                module.verify_research_cpu_stable_state()

    def test_any_change_during_stability_observation_is_rejected(self):
        module = load_module()
        first = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "enabled",
            "NRestarts": "11551",
            "ExecMainStatus": "0",
        }
        second = dict(first)
        second["NRestarts"] = "11552"
        with mock.patch.object(
            module,
            "service_snapshot",
            side_effect=[first, second],
        ), mock.patch.object(module.time, "sleep"):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "state changed during pre-mutation stability observation",
            ):
                module.verify_research_cpu_stable_state()

    def test_backup_snapshot_must_exactly_match_preflight_state(self):
        module = load_module()
        expected = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "enabled",
            "NRestarts": "11551",
            "ExecMainStatus": "0",
        }
        changed = dict(expected)
        changed["ActiveState"] = "failed"
        changed["SubState"] = "failed"
        changed["ExecMainStatus"] = "1"
        with self.assertRaisesRegex(
            module.BootstrapError,
            "state changed after stability check but before mutation",
        ):
            module.assert_research_cpu_preserved_baseline(
                expected,
                {module.RESEARCH_CPU: changed},
            )

    def test_live_boundary_recheck_requires_exact_research_cpu_state(self):
        module = load_module()
        baseline = {
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "UnitFileState": "enabled",
            "NRestarts": "11551",
            "ExecMainStatus": "0",
        }
        changed = dict(baseline)
        changed["ActiveState"] = "active"
        changed["SubState"] = "running"
        with mock.patch.object(module, "service_snapshot", return_value=changed):
            with self.assertRaisesRegex(
                module.BootstrapError,
                "preserved research-engine CPU state changed",
            ):
                module._verify_preserved_services(
                    {module.RESEARCH_CPU: baseline}
                )

    def test_research_cpu_is_not_required_active_and_never_mutated(self):
        module = load_module()
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(module.RESEARCH_CPU, module.PRESERVED_CONTROLLERS)
        self.assertNotIn(module.RESEARCH_CPU, module.REQUIRED_ACTIVE_CONTROLLERS)
        self.assertNotIn(module.RESEARCH_CPU, module.MUTATED_SERVICES)
        self.assertNotIn('run(["systemctl", "stop", RESEARCH_CPU])', raw)
        self.assertNotIn('run(["systemctl", "restart", RESEARCH_CPU])', raw)

    def test_exact_rechecks_still_immediately_precede_mutation(self):
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


if __name__ == "__main__":
    unittest.main()
