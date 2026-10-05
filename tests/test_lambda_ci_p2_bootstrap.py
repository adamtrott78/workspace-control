import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOT = (ROOT / "scripts" / "bootstrap_lambda_ci_research_engine.sh").read_text()
PLAN = (ROOT / "architecture" / "lambda-ci-p2-plan.v1.md").read_text()


class LambdaCIP2BootstrapTests(unittest.TestCase):
    def test_p2_requires_explicit_authorization_and_exact_sha(self):
        self.assertIn("WORKSPACE_CI_P2_AUTHORIZED", BOOT)
        self.assertIn("WORKSPACE_CI_P2_EXPECTED_SHA", BOOT)
        self.assertIn("UNEXPECTED_WORKSPACE_CONTROL_SHA", BOOT)

    def test_transient_probes_precede_user_creation(self):
        probe = BOOT.index("P2_TRANSIENT_PREFLIGHT=PASS")
        mutate = BOOT.index("groupadd --system workspace-ci-controller")
        self.assertLess(probe, mutate)

    def test_network_policy_blocks_production_boundaries(self):
        for token in (
            "IPAddressDeny=127.0.0.0/8",
            "IPAddressAllow=127.0.0.53/32",
            "IPAddressDeny=100.64.0.0/10",
            "IPAddressDeny=$LOCAL_SUBNET",
            "/dev/tcp/127.0.0.1/5432",
            "/dev/tcp/$host_ip/5432",
        ):
            self.assertIn(token, BOOT)

    def test_device_policy_denies_gpu_by_default(self):
        self.assertIn("DevicePolicy=closed", BOOT)
        self.assertIn("DEVICE_POLICY_DID_NOT_BLOCK_NVIDIA", BOOT)
        self.assertIn("DeviceAllow=/dev/nvidia0 rw", BOOT)
        self.assertNotIn("DeviceAllow=/dev/nvidia1 rw", BOOT)

    def test_no_privilege_shortcuts(self):
        lowered = BOOT.lower()
        self.assertNotIn("usermod -ag docker", lowered)
        self.assertNotIn("usermod -a -g docker", lowered)
        self.assertNotIn("nft add", lowered)
        self.assertNotIn("iptables -a", lowered)
        self.assertNotIn("ufw allow", lowered)
        self.assertNotIn("research-engine-daemon", lowered)

    def test_runner_package_is_exactly_pinned(self):
        self.assertIn('RUNNER_VERSION="2.337.0"', BOOT)
        self.assertIn(
            'RUNNER_SHA256="70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613"',
            BOOT,
        )
        self.assertIn("sha256sum -c -", BOOT)

    def test_p2a_does_not_register_a_runner_or_store_github_credentials(self):
        self.assertNotIn("config.sh --", BOOT)
        self.assertNotIn("generate-jitconfig", BOOT)
        self.assertIn('"runner_registered": False', BOOT)
        self.assertIn("No GitHub runner is registered in P2-A", PLAN)

    def test_plan_preserves_p2b_jit_boundary(self):
        self.assertIn("P2-B — first JIT no-op runner", PLAN)
        self.assertIn("never passed into the job environment", PLAN)
        self.assertIn("Administration:write", PLAN)


if __name__ == "__main__":
    unittest.main()
