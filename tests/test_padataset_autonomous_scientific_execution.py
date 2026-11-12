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
        self.assertIn("Python venv", text)
        self.assertIn("No generic shell", text)

    def test_installer_has_valid_bash_syntax(self):
        proc = subprocess.run(
            ["/bin/bash", "-n", str(INSTALLER)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_installer_discovers_dnns_from_runtime_path_registry_and_standard_locations(self):
        text = INSTALLER.read_text()
        self.assertNotIn("CONDA_PREFIX is missing", text)
        self.assertNotIn("CONDA_DEFAULT_ENV", text)
        self.assertIn("declare -a DNNS_CANDIDATES=()", text)
        self.assertIn("add_dnns_candidate()", text)
        self.assertIn('for pycmd in python python3', text)
        self.assertIn("PATH_PARTS", text)
        self.assertIn('"$CONDA_EXE_PATH" env list --json', text)
        self.assertIn('"$HOME/miniconda3/envs/DNNs"', text)
        self.assertIn('"$HOME/anaconda3/envs/DNNs"', text)
        self.assertIn('"$HOME/.conda/envs/DNNs"', text)
        self.assertIn('"$HOME/adamArchives/venvs/DNNs"', text)
        self.assertIn("expected exactly one valid DNNs Python prefix", text)
        self.assertIn("pathlib.Path(sys.prefix).resolve()", text)
        self.assertIn('"environment_type":"PYTHON_VENV"', text)
        self.assertIn('cfg=expected/"pyvenv.cfg"', text)
        self.assertIn('conda_meta=expected/"conda-meta"', text)
        self.assertIn("SOURCE_DNNS_PREFIX_BINDING=PASS", text)
        self.assertIn("SOURCE_DNNS_VENV_BINDING=PASS", text)
        self.assertNotIn("SOURCE_DNNS_CONDA_BINDING=PASS", text)
        self.assertIn("SOURCE_DNNS_PREFIX=", text)

    def test_installer_is_exact_source_to_root_owned_runtime_promotion(self):
        text = INSTALLER.read_text()
        for marker in (
            '"$CONDA_EXE_PATH" env list --json',
            "SOURCE_DNNS_PREFIX_BINDING=PASS",
            "SOURCE_DNNS_VENV_BINDING=PASS",
            'RUNTIME_BASE="$PROJECT_ROOT/expanded-runtimes/padataset-dnns-v1"',
            'sudo cp -a --reflink=auto "$SOURCE_PREFIX/." "$RUNTIME_STAGING/"',
            "SOURCE_DNNS_COPY_EQUIVALENCE=PASS",
            "SOURCE_DNNS_PRE_POST_INTEGRITY=PASS",
            'RUNTIME_STAGING="$RUNTIME_BASE/.${MANIFEST_SHA}.next.$$"',
            '"promotion_method":"python-venv-copy-rewrite-v1"',
            'sudo chown -hR root:root "$RUNTIME_STAGING"',
            "PROMOTED_DNNS_RUNTIME_INTEGRITY=PASS",
            "PADATASET_DNNS_RUNTIME_BINDING_JSON=",
            "PADATASET_SCIENTIFIC_DATA_JSON=",
            "PADATASET_SCIENTIFIC_PROMOTION=PASS",
        ):
            self.assertIn(marker, text)
        self.assertIn(
            'SOURCE_OBJECT_BASE="/var/lib/workspace-ci/padataset-runtime-sources/sha256"',
            text,
        )
        self.assertNotIn('SOURCE_OBJECT_BASE="$TRUSTED_CACHE', text)
        self.assertIn(
            'install -o root -g root -m 0400 "$SOURCE_MANIFEST" "$SOURCE_OBJECT/runtime-manifest.json"',
            text,
        )
        self.assertIn('"base_python_sha256":base_python_sha', text)
        self.assertIn('"schema":"padataset.expanded-runtime-receipt.v2"', text)
        self.assertIn("if st.st_uid != 0 or st.st_gid != 0:", text)
        self.assertNotIn('CONDA_OFFLINE=true', text)
        self.assertNotIn('--clone "$SOURCE_PREFIX"', text)
        self.assertNotIn('list --prefix "$SOURCE_PREFIX"', text)
        self.assertNotIn("sudo bash -c", text)
        self.assertNotIn("chmod 777", text)
        self.assertNotIn('RUNTIME_STAGING="$RUNTIME_BASE/.\\${MANIFEST_SHA}.next.$$"', text)

    def test_installer_venv_relocation_fails_closed_on_private_or_external_refs(self):
        text = INSTALLER.read_text()
        for marker in (
            "source prefix remains in non-text runtime content",
            "promoted venv contains unsupported symlink targets",
            "promoted venv still discloses mutable source prefix",
            "staging venv exposes external import paths",
            "final venv exposes external import paths",
            "base Python changed during promotion",
            "base Python digest no longer matches promoted runtime receipt",
        ):
            self.assertIn(marker, text)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", text)
        self.assertIn('PYTHONPATH=""', text)
        self.assertIn("PYTHONNOUSERSITE=1", text)

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
        self.assertEqual(scientific["lifecycle"], "ACCEPTED_SCIENTIFIC_V1")
        self.assertTrue(scientific["admission_enabled_after_generic_activation"])
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

    def test_scientific_route_is_active_with_exact_promoted_bindings(self):
        route = PAD["routes"]["scientific-single-gpu"]
        self.assertEqual(route["activation_state"], "ACTIVE")
        self.assertEqual(route["execution_contract_id"], "scientific-single-gpu-v1")
        self.assertEqual(
            route["trusted_workflow"]["blob_sha"],
            "555c2bd1f824519281f149017898d4923439d6cc",
        )
        self.assertEqual(route["trigger"]["command"], "/lambda-scientific")
        self.assertFalse(route["trigger"]["fork_pr_execution_allowed"])
        self.assertEqual(route["bindings"]["runtime_id"], "padataset-dnns-v1")
        self.assertIsNone(route["bindings"]["model_id"])
        binding = PAD["bindings"]["runtimes"]["padataset-dnns-v1"]
        self.assertEqual(
            binding["manifest_identity_sha256"],
            "57b0cd8d0f3d2c5f353891237ad52d118458a4cff1f9b403321754ae4fcbe579",
        )
        self.assertEqual(
            binding["tree_digest_sha256"],
            "6922847a7ea87c318a36e1fd2cd3af5283e768ff06de90c4cb2558ea0d48cdaa",
        )
        self.assertEqual(binding["promotion_method"], "python-venv-copy-rewrite-v1")
        self.assertEqual(binding["base_python_path"], "/usr/bin/python3.12")
        self.assertEqual(
            binding["base_python_sha256"],
            "1217953cf9b9b0bb25fb75f60fe2c59d91a578ab194f7f3f5956e1aec6814e74",
        )
        self.assertEqual(
            binding["scientific_data"],
            {
                "profile_id": "ota_core_high_run01_len16384_v1",
                "path": "/srv/workspace-ci/padataset/trusted-cache/scientific-data/ota_core_high_run01_len16384_v1",
                "tree_digest_sha256": "a76730a886909f9896e7cb7e9d1aede3d2301240f9ce08a4080e24d637406bf5",
                "file_count": 360,
            },
        )


if __name__ == "__main__":
    unittest.main()
