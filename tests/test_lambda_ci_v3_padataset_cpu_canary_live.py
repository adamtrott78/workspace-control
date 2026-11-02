import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lambda_ci_v3_padataset_cpu_canary_live.sh"


class PadatasetCpuCanaryOperatorTests(unittest.TestCase):
    def setUp(self):
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_exact_target_and_owning_repository(self):
        self.assertIn('TARGET_CLASS="padataset-cpu-public-v1"', self.text)
        self.assertIn('TARGET_SCALE_SET="lambda-padataset-cpu-public"', self.text)
        self.assertIn('REPOSITORY="adamtrott78/PADataset"', self.text)
        self.assertIn('TARGET_GITHUB_URL="https://github.com/adamtrott78/PADataset"', self.text)
        self.assertIn('EXPECTED_WORKFLOW_BLOB="f42c165ef6dc658f026976984c87d2eb28f5cd17"', self.text)

    def test_controller_generation_is_decoupled_from_operator_head(self):
        self.assertIn('CONTROLLER_SOURCE_HEAD="3e8a231483413ba3a16d405ba61b55d0ab9ff3aa"', self.text)
        self.assertIn('OPERATOR_HEAD="$(git -C "$ROOT" rev-parse HEAD)"', self.text)
        self.assertIn('SOURCE_HEAD="$CONTROLLER_SOURCE_HEAD"', self.text)
        self.assertIn('"$GO_BIN" -C "$ROOT/controller/lambda-ci-controller"', self.text)
        self.assertNotIn('"$GO_BIN" -C "$SOURCE_TREE/controller/lambda-ci-controller"', self.text)
        self.assertIn('EXPECTED_TX_HELPER_BLOB="0c02ca17cf267f1c3986bfee75ebfc6172ca592a"', self.text)

    def test_preflight_target_repository_is_explicit_and_operator_bound(self):
        self.assertIn('--target-url "$TARGET_GITHUB_URL"', self.text)
        self.assertIn('TARGET_GITHUB_URL="https://github.com/adamtrott78/PADataset"', self.text)
        build = self.text.index('V3_CANARY_PREFLIGHT_BUILD=BEGIN')
        target = self.text.index('--target-url "$TARGET_GITHUB_URL"')
        authority = self.text.index('CANARY_AUTHORITY_CREATED=PASS')
        self.assertLess(build, target)
        self.assertLess(target, authority)


    def test_inactive_preflight_rejects_systemd_auto_restart_window(self):
        self.assertIn('active_state="$(systemctl show "$unit" -p ActiveState --value', self.text)
        self.assertIn('sub_state="$(systemctl show "$unit" -p SubState --value', self.text)
        self.assertIn('"$active_state" == "activating"', self.text)
        self.assertIn('"$sub_state" == "auto-restart"', self.text)


    def test_padataset_credentials_are_repository_scoped(self):
        self.assertIn('/var/lib/workspace-ci/v3/credentials/padataset', self.text)
        self.assertIn('ci-gh-padataset', self.text)
        self.assertNotIn('ci-gh-workspace-control', self.text)

    def test_authority_remains_fresh_and_one_class(self):
        self.assertIn('"operation": "ACTIVATE_ONE_V3_CANARY"', self.text)
        self.assertIn('AUTH_ID="$(python3 - <<', self.text)
        self.assertIn('"target_runner_class_id": os.environ["TARGET_CLASS"]', self.text)
        self.assertIn('"expires_at": (now + timedelta(minutes=15)).isoformat()', self.text)

    def test_generation_exclusion_and_rollback_are_preserved(self):
        self.assertIn('GENERATION_EXCLUSION=BEGIN', self.text)
        self.assertIn('--apply-canary', self.text)
        self.assertIn('--rollback "$TX_RECEIPT"', self.text)
        self.assertIn('GENERATION_EXCLUSION_ROLLBACK=PASS', self.text)
        self.assertIn('RESEARCH_GPU_CONTAINMENT=PRESERVED', self.text)

    def test_canary_requires_exact_default_branch_blob_before_authority(self):
        blob_check = self.text.index('CANARY_DEFAULT_BRANCH_BLOB=PASS')
        authority = self.text.index('CANARY_AUTHORITY_CREATED=PASS')
        self.assertLess(blob_check, authority)

    def test_transient_status_query_failure_does_not_immediately_cancel(self):
        self.assertIn('CANARY_STATUS_QUERY_FAILURE_LIMIT=6', self.text)
        self.assertIn('CANARY_RUN_STATUS_QUERY_RETRY=PASS', self.text)
        self.assertIn('STOP_CANARY_RUN_STATUS_QUERY_RETRY_EXHAUSTED', self.text)
        retry = self.text.index('CANARY_RUN_STATUS_QUERY_RETRY=PASS')
        exhausted = self.text.index('STOP_CANARY_RUN_STATUS_QUERY_RETRY_EXHAUSTED')
        self.assertLess(retry, exhausted)

    def test_queued_run_emits_controller_diagnostics_before_terminal_timeout(self):
        self.assertIn('CANARY_QUEUED_DIAGNOSTIC_THRESHOLD=REACHED', self.text)
        self.assertIn('CANARY_CONTROLLER_DIAGNOSTICS=BEGIN', self.text)
        self.assertIn('systemctl show "$target_unit"', self.text)
        self.assertIn('-u "$target_unit"', self.text)


    def test_effective_generation_preflight_runs_before_class_mutation(self):
        verify = self.text.index('LIVE_EFFECTIVE_GENERATION_VERIFY=PASS')
        apply = self.text.index('--apply-canary')
        self.assertLess(verify, apply)


if __name__ == "__main__":
    unittest.main()
