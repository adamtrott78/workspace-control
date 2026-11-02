import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_v3_repair_research_gpu_and_resume_roots_v1.py"


class ResearchGPUContainmentRootResumeTests(unittest.TestCase):
    def setUp(self):
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_exact_mutation_boundary(self):
        self.assertIn(
            'RESEARCH_GPU_V2_UNIT = "workspace-ci-controller@research-engine-gpu.service"',
            self.text,
        )
        self.assertIn(
            'RESEARCH_PROJECT_UNIT_PATTERN = "workspace-ci-research-engine-*.service"',
            self.text,
        )
        self.assertIn('["systemctl", "stop", RESEARCH_GPU_V2_UNIT]', self.text)
        self.assertIn('["systemctl", "disable", RESEARCH_GPU_V2_UNIT]', self.text)
        self.assertNotIn("research-engine-cpu.service", self.text)
        self.assertNotIn("ACTIVATE_ONE_V3_CANARY", self.text)
        self.assertNotIn("gh api", self.text)
        self.assertNotIn("scale-set", self.text.lower().split("It does not touch", 1)[-1].split('"""', 1)[0])

    def test_fail_closed_execution_absence_and_root_prestate(self):
        self.assertIn("active_research_execution_units()", self.text)
        self.assertIn("Research execution units are active; refusing", self.text)
        self.assertIn("v3 root services must remain inactive before containment repair", self.text)
        self.assertIn("legacy Research GPU controller is still active after repair", self.text)
        self.assertIn("legacy Research GPU controller is not boot-disabled after repair", self.text)

    def test_fresh_root_authority_only(self):
        self.assertIn('"operation": "ACTIVATE_V3_ROOT_SERVICES"', self.text)
        self.assertIn("uuid.uuid4()", self.text)
        self.assertIn("timedelta(minutes=10)", self.text)
        self.assertIn("O_EXCL", self.text)
        self.assertNotIn("14e58009-7bf3-43d1-8ad8-7616e70edaa3", self.text)
        self.assertNotIn("40396f92-3db3-40f5-83e9-28fdef0370da", self.text)

    def test_containment_is_not_rolled_back_on_activation_failure(self):
        self.assertIn("containment remains fail-safe", self.text)
        self.assertNotIn('["systemctl", "start", RESEARCH_GPU_V2_UNIT]', self.text)
        self.assertNotIn('["systemctl", "enable", RESEARCH_GPU_V2_UNIT]', self.text)

    def test_exact_clean_checkout_and_root_required(self):
        self.assertIn("os.geteuid() != 0", self.text)
        self.assertIn('["rev-parse", "HEAD"]', self.text)
        self.assertIn('["status", "--porcelain=v1", "--untracked-files=normal"]', self.text)
        self.assertIn("checkout HEAD mismatch", self.text)
        self.assertIn("checkout is dirty", self.text)


if __name__ == "__main__":
    unittest.main()
