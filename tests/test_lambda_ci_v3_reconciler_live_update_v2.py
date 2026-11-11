import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_v3_reconciler_live_update_v2.py"


class V3ReconcilerLiveUpdateV2Tests(unittest.TestCase):
    def setUp(self):
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_update_is_reconciler_only(self):
        self.assertIn(
            'INSTALLED_RECONCILER = Path(',
            self.text,
        )
        self.assertIn(
            'RECONCILER_OVERRIDE = Path(',
            self.text,
        )
        self.assertNotIn("INSTALLED_PROVISIONER", self.text)
        self.assertNotIn("INSTALLED_ACTIVATOR", self.text)
        self.assertIn('"class_controller_mutation": False', self.text)
        self.assertIn('"workflow_mutation": False', self.text)
        self.assertIn('"scale_set_mutation": False', self.text)
        self.assertIn('"v2_mutation": False', self.text)

    def test_live_boundary_requires_active_roots_and_no_class_controller(self):
        self.assertIn(
            'provisioner.get("ActiveState") != "active"',
            self.text,
        )
        self.assertIn(
            'provisioner.get("SubState") != "running"',
            self.text,
        )
        self.assertIn(
            'reconciler.get("SubState") != "exited"',
            self.text,
        )
        self.assertIn(
            'if state.get("ActiveState") in {"active", "activating", "reloading"}',
            self.text,
        )
        self.assertIn(
            'if state.get("SubState") == "auto-restart"',
            self.text,
        )

    def test_research_gpu_containment_is_required(self):
        self.assertIn(
            'RESEARCH_GPU_UNIT = "workspace-ci-controller@research-engine-gpu.service"',
            self.text,
        )
        self.assertIn(
            'research.get("ActiveState") != "inactive"',
            self.text,
        )
        self.assertIn(
            'research.get("UnitFileState") != "disabled"',
            self.text,
        )
        self.assertIn(
            '"research_gpu_containment_preserved": True',
            self.text,
        )

    def test_candidate_verifier_proves_current_generation_before_replacement(self):
        verify = self.text.index("candidate.verify_installed(BASE_MANIFEST)")
        replace = self.text.index(
            "atomic_file(INSTALLED_RECONCILER, candidate_rec, mode)"
        )
        self.assertLess(verify, replace)
        self.assertIn(
            "installed reconciler self-verification failed",
            self.text,
        )

    def test_no_service_restart_enable_or_start_is_performed(self):
        for forbidden in (
            '["systemctl", "restart"',
            '["systemctl", "start"',
            '["systemctl", "stop"',
            '["systemctl", "enable"',
            '["systemctl", "disable"',
        ):
            self.assertNotIn(forbidden, self.text)
        self.assertIn('"PROVISIONER_RESTARTED=false"', self.text)
        self.assertIn('"RECONCILER_RESTARTED=false"', self.text)

    def test_failure_restores_previous_reconciler_and_override(self):
        self.assertIn(
            "atomic_file(INSTALLED_RECONCILER, old_rec, mode)",
            self.text,
        )
        self.assertIn(
            "atomic_file(RECONCILER_OVERRIDE, old_override_raw, 0o600)",
            self.text,
        )
        self.assertIn(
            "RECONCILER_OVERRIDE.unlink()",
            self.text,
        )


if __name__ == "__main__":
    unittest.main()
