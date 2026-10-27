import importlib.util
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_p1_quiesce_restart_storm.py"


def load_module():
    spec = importlib.util.spec_from_file_location("p1_quiesce", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class P1ResearchCpuQuiesceTests(unittest.TestCase):
    def stable(self, *, active="active", sub="running", restarts="12110", status="0"):
        return {
            "LoadState": "loaded",
            "ActiveState": active,
            "SubState": sub,
            "UnitFileState": "enabled",
            "NRestarts": restarts,
            "ExecMainStatus": status,
            "Restart": "on-failure",
            "Result": "success" if status == "0" else "exit-code",
        }

    def storm(self, restarts):
        return self.stable(
            active="activating",
            sub="auto-restart",
            restarts=str(restarts),
            status="1",
        )

    def test_already_stable_lane_is_noop(self):
        module = load_module()
        state = self.stable()
        with mock.patch.object(
            module, "require_other_control_services_active"
        ), mock.patch.object(
            module, "no_active_research_execution"
        ), mock.patch.object(
            module, "service_snapshot", side_effect=[state, state.copy()]
        ), mock.patch.object(module.time, "sleep"):
            result = module.prove_persistent_restart_storm()
        self.assertEqual(result["status"], "NO_QUIESCE_REQUIRED")

    def test_persistent_restart_storm_requires_two_increasing_intervals(self):
        module = load_module()
        samples = [self.storm(12110), self.storm(12112), self.storm(12113)]
        with mock.patch.object(
            module, "require_other_control_services_active"
        ), mock.patch.object(
            module, "no_active_research_execution"
        ), mock.patch.object(
            module, "service_snapshot", side_effect=samples
        ), mock.patch.object(module.time, "sleep"):
            result = module.prove_persistent_restart_storm()
        self.assertEqual(result["status"], "PERSISTENT_RESTART_STORM")
        self.assertEqual(result["third"]["NRestarts"], "12113")

    def test_storm_must_still_be_advancing_at_mutation_boundary(self):
        module = load_module()
        samples = [self.storm(12110), self.storm(12112), self.storm(12112)]
        with mock.patch.object(
            module, "require_other_control_services_active"
        ), mock.patch.object(
            module, "no_active_research_execution"
        ), mock.patch.object(
            module, "service_snapshot", side_effect=samples
        ), mock.patch.object(module.time, "sleep"):
            with self.assertRaisesRegex(
                module.QuiesceError,
                "stopped increasing before mutation boundary",
            ):
                module.prove_persistent_restart_storm()

    def test_rejects_active_research_execution(self):
        module = load_module()
        completed = module.subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=(
                "workspace-ci-research-engine-test.service loaded active running x\n"
            ),
            stderr="",
        )
        with mock.patch.object(module, "run", return_value=completed):
            with self.assertRaisesRegex(
                module.QuiesceError,
                "research-engine execution is active",
            ):
                module.no_active_research_execution()

    def test_quiesce_stops_only_exact_research_cpu_unit(self):
        module = load_module()
        inactive = self.stable(
            active="inactive",
            sub="dead",
            restarts="12113",
            status="1",
        )
        proof = {
            "status": "PERSISTENT_RESTART_STORM",
            "first": self.storm(12110),
            "second": self.storm(12112),
            "third": self.storm(12113),
        }
        completed = module.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with mock.patch.object(
            module, "prove_persistent_restart_storm", return_value=proof
        ), mock.patch.object(
            module, "run", return_value=completed
        ) as run_call, mock.patch.object(
            module, "service_snapshot", side_effect=[inactive, inactive.copy()]
        ), mock.patch.object(
            module, "require_other_control_services_active"
        ), mock.patch.object(
            module, "no_active_research_execution"
        ), mock.patch.object(module.time, "sleep"):
            result = module.quiesce_and_verify()

        self.assertEqual(result["status"], "QUIESCED_STABLE_INACTIVE")
        commands = [call.args[0] for call in run_call.call_args_list]
        self.assertEqual(
            commands,
            [["systemctl", "stop", module.RESEARCH_CPU]],
        )

    def test_post_stop_state_must_remain_exactly_stable(self):
        module = load_module()
        first = self.stable(
            active="inactive",
            sub="dead",
            restarts="12113",
            status="1",
        )
        second = dict(first)
        second["NRestarts"] = "12114"
        proof = {
            "status": "PERSISTENT_RESTART_STORM",
            "first": self.storm(12110),
            "second": self.storm(12112),
            "third": self.storm(12113),
        }
        completed = module.subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with mock.patch.object(
            module, "prove_persistent_restart_storm", return_value=proof
        ), mock.patch.object(
            module, "run", return_value=completed
        ), mock.patch.object(
            module, "service_snapshot", side_effect=[first, second]
        ), mock.patch.object(module.time, "sleep"):
            with self.assertRaisesRegex(
                module.QuiesceError,
                "changed after explicit quiesce",
            ):
                module.quiesce_and_verify()

    def test_restart_storm_rejects_malformed_or_wrong_policy_state(self):
        module = load_module()
        malformed = self.storm(12110)
        malformed["ExecMainStatus"] = ""
        with self.assertRaises(module.QuiesceError):
            module._restart_storm_sample(malformed)

        wrong_policy = self.storm(12110)
        wrong_policy["Restart"] = "always"
        with self.assertRaisesRegex(module.QuiesceError, "not on-failure"):
            module._restart_storm_sample(wrong_policy)

    def test_script_contains_no_restart_enable_or_file_install_mutation(self):
        raw = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('["systemctl", "restart"', raw)
        self.assertNotIn('["systemctl", "start"', raw)
        self.assertNotIn('["systemctl", "enable"', raw)
        self.assertNotIn("shutil", raw)
        self.assertNotIn("os.replace", raw)
        self.assertIn('["systemctl", "stop", RESEARCH_CPU]', raw)


if __name__ == "__main__":
    unittest.main()
