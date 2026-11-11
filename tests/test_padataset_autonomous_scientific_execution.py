import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = json.loads((ROOT / "architecture/lambda-ci-execution-contracts.v1.json").read_text())
WORKLOAD = json.loads((ROOT / "architecture/lambda-ci-workload-policy.v1.json").read_text())
PAD = json.loads((ROOT / "architecture/lambda-ci-project-padataset.v1.json").read_text())
PROFILES = json.loads((ROOT / "architecture/lambda-ci-systemd-profiles.v1.json").read_text())
DESIGN = ROOT / "architecture/padataset-autonomous-scientific-execution.v0.1.md"
INSTALLER = ROOT / "scripts/install_padataset_scientific_runtime_v1.sh"


class PADatasetAutonomousScientificExecutionTests(unittest.TestCase):
    def test_design_and_installer_exist(self):
        self.assertTrue(DESIGN.is_file())
        self.assertTrue(INSTALLER.is_file())
        text = DESIGN.read_text()
        self.assertIn("scientific-single-gpu-v1", text)
        self.assertIn("DNNs", text)
        self.assertIn("No generic shell", text)

    def test_installer_has_valid_bash_syntax(self):
        proc = subprocess.run(
            ["/bin/bash", "-n", str(INSTALLER)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_installer_is_exact_source_to_root_owned_runtime_promotion(self):
        text = INSTALLER.read_text()
        for marker in (
            'CONDA_DEFAULT_ENV:-}" == "DNNs"',
            'CONDA_OFFLINE=true',
            '--clone "$SOURCE_PREFIX"',
            'RUNTIME_BASE="$PROJECT_ROOT/expanded-runtimes/padataset-dnns-v1"',
            'sudo chown -R root:root "$RUNTIME_PATH"',
            'sudo chmod -R a-w "$RUNTIME_PATH"',
            'PADATASET_DNNS_RUNTIME_BINDING_JSON=',
            'PADATASET_SCIENTIFIC_DATA_JSON=',
            'PADATASET_SCIENTIFIC_PROMOTION=PASS',
        ):
            self.assertIn(marker, text)
        self.assertNotIn("sudo bash -c", text)
        self.assertNotIn("chmod 777", text)

    def test_installer_promotes_only_stage03_cache_profile(self):
        text = INSTALLER.read_text()
        self.assertIn(
            "_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01",
            text,
        )
        self.assertIn('DATA_PROFILE_ID="ota_core_high_run01_len16384_v1"', text)
        self.assertIn('"read_only_hardened":True', text)

    def test_scientific_contract_is_separate_from_ci_canary(self):
        scientific = CONTRACTS["contracts"]["scientific-single-gpu-v1"]
        canary = CONTRACTS["contracts"]["gpu-single-public-ci-v1"]
        self.assertEqual(scientific["lifecycle"], "PLANNED_NOT_ACCEPTED")
        self.assertFalse(scientific["admission_enabled_after_generic_activation"])
        self.assertEqual(
            scientific["state_effect_class"],
            "SCIENTIFIC_EXPERIMENT_EPHEMERAL_ARTIFACTS",
        )
        self.assertEqual(canary["state_effect_class"], "CI_VALIDATION_ONLY")
        self.assertEqual(scientific["runtime_binding_mode"], "REQUIRED_EXPANDED_RUNTIME_EXACT")
        self.assertEqual(canary["runtime_binding_mode"], "OPTIONAL_EXACT_IF_ROUTE_BINDS")

    def test_existing_gpu_canary_effective_runtime_ceiling_stays_twenty_minutes(self):
        self.assertEqual(PROFILES["profiles"]["gpu-small"]["RuntimeMaxSec"], "4h")
        self.assertEqual(
            WORKLOAD["resource_classes"]["gpu_small_v1"]["max_runtime_seconds"],
            1200,
        )
        self.assertEqual(
            WORKLOAD["resource_classes"]["scientific_gpu_single_v1"]["max_runtime_seconds"],
            14400,
        )

    def test_scientific_route_is_planned_unbound(self):
        route = PAD["routes"]["scientific-single-gpu"]
        self.assertEqual(route["activation_state"], "PLANNED_NOT_BOUND")
        self.assertEqual(route["execution_contract_id"], "scientific-single-gpu-v1")
        self.assertEqual(
            route["trusted_workflow"]["blob_sha"],
            "555c2bd1f824519281f149017898d4923439d6cc",
        )
        self.assertEqual(route["trigger"]["command"], "/lambda-scientific")
        self.assertFalse(route["trigger"]["fork_pr_execution_allowed"])
        self.assertEqual(route["bindings"]["runtime_id"], "padataset-dnns-v1")
        self.assertIsNone(route["bindings"]["model_id"])


if __name__ == "__main__":
    unittest.main()
