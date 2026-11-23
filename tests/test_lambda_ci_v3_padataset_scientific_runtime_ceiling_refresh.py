import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_policy_compiler as compiler
import lambda_ci_v3_padataset_scientific_runtime_ceiling_refresh_v1 as refresh


class PADatasetScientificRuntimeCeilingRefreshTests(unittest.TestCase):
    def test_candidate_timeout_hierarchy_is_360_lt_390_lt_392(self):
        compiled = compiler.compile_policy(ROOT)
        classes = compiled["root_projection"]["runner_classes"]
        for class_id in refresh.TARGETS:
            row = classes[class_id]
            self.assertEqual(
                row["resource_class"]["max_runtime_seconds"],
                390 * 60,
            )
            self.assertEqual(
                row["systemd_profile"]["RuntimeMaxSec"],
                "390min",
            )
        workflow_seconds = 360 * 60
        systemd_seconds = refresh.NEW_SECONDS
        wrapper_seconds = refresh.NEW_SECONDS + 120
        self.assertLess(workflow_seconds, systemd_seconds)
        self.assertLess(systemd_seconds, wrapper_seconds)

    def test_delta_accepts_only_the_two_scientific_runtime_envelopes(self):
        compiled = compiler.compile_policy(ROOT)
        candidate = copy.deepcopy(compiled["root_projection"])
        current = copy.deepcopy(candidate)
        for class_id in refresh.TARGETS:
            row = current["runner_classes"][class_id]
            row["resource_class"]["max_runtime_seconds"] = refresh.OLD_SECONDS
            row["systemd_profile"]["RuntimeMaxSec"] = refresh.OLD_SYSTEMD
            row["systemd_profile"]["note"] = "predecessor 4h scientific ceiling"
            row["root_envelope_sha256"] = compiler.sha256_object(
                {
                    key: value
                    for key, value in row.items()
                    if key not in {
                        "control_plane_generation_sha256",
                        "root_envelope_sha256",
                    }
                }
            )
        previous, updated = refresh._validate_delta(current, candidate)
        changed = {
            class_id
            for class_id in previous
            if previous[class_id] != updated[class_id]
        }
        self.assertEqual(changed, set(refresh.TARGETS))

    def test_delta_rejects_unrelated_class_change(self):
        compiled = compiler.compile_policy(ROOT)
        candidate = copy.deepcopy(compiled["root_projection"])
        current = copy.deepcopy(candidate)
        for class_id in refresh.TARGETS:
            row = current["runner_classes"][class_id]
            row["resource_class"]["max_runtime_seconds"] = refresh.OLD_SECONDS
            row["systemd_profile"]["RuntimeMaxSec"] = refresh.OLD_SYSTEMD
            row["systemd_profile"]["note"] = "predecessor 4h scientific ceiling"
            row["root_envelope_sha256"] = compiler.sha256_object(
                {
                    key: value
                    for key, value in row.items()
                    if key not in {
                        "control_plane_generation_sha256",
                        "root_envelope_sha256",
                    }
                }
            )
        unrelated = next(
            class_id
            for class_id in candidate["runner_classes"]
            if class_id not in refresh.TARGETS
        )
        candidate["runner_classes"][unrelated]["max_runners"] += 1
        with self.assertRaises(refresh.RuntimeCeilingRefreshError):
            refresh._validate_delta(current, candidate)

    def test_live_helper_is_quiescent_root_authorized_and_rollback_capable(self):
        source = (
            ROOT
            / "scripts/lambda_ci_v3_padataset_scientific_runtime_ceiling_refresh_v1.py"
        ).read_text()
        for marker in (
            "REFRESH_PADATASET_SCIENTIFIC_RUNTIME_CEILING_V1",
            "base._require_quiescent(systemd)",
            "base._load_authority(",
            "base._backup_paths(",
            "base._restore_paths(backups)",
            "ROLLED_BACK",
            "PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH=PASS",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("merge_pull_request", source)
        self.assertNotIn("workspace_shell", source)

    def test_reconciler_layers_timeout_receipt_after_workflow_refreshes(self):
        source = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
        for marker in (
            "PADATASET_SCIENTIFIC_RUNTIME_CEILING_REFRESH_ACTIVE_RECEIPT",
            "_padataset_scientific_runtime_ceiling_refresh(",
            "lane_a_workflow_refresh_receipt_sha256",
            "lane_b_workflow_refresh_receipt_sha256",
            "runtime_ceiling_overrides",
            "scientific_dual_effective_state",
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
