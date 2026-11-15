import copy
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "lane_b_identity_cutover_test_module",
    ROOT / "scripts/lambda_ci_v3_padataset_lane_b_runner_identity_cutover_v1.py",
)
cutover = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = cutover
spec.loader.exec_module(cutover)


def row(user, envelope):
    return {
        "runner_class_id": "x",
        "project_id": "padataset",
        "project_runner_identity": {"user": user, "group": "ci-padataset"},
        "systemd_common": {
            "User": user,
            "Group": "ci-padataset",
            "CPUQuota": "400%",
        },
        "resource_class": {"gpu_uuids": ["GPU-x"], "gpu_count": 1},
        "control_plane_generation_sha256": "g" * 64,
        "root_envelope_sha256": envelope,
    }


class LaneBRunnerIdentityCutoverTests(unittest.TestCase):
    def roots(self):
        a = row("ci-padataset", "a" * 64)
        b_old = row("ci-padataset", "b" * 64)
        b_new = row("ci-padataset-2", "c" * 64)
        current = {
            "host_resource_policy": {"migration_mode": {"host_max_active_runners": 3}},
            "upstream_pins": {"x": 1},
            "runner_classes": {
                "lane-a": a,
                cutover.TARGET_CLASS: b_old,
            },
        }
        candidate = copy.deepcopy(current)
        candidate["runner_classes"][cutover.TARGET_CLASS] = b_new
        candidate["runner_classes"]["lane-a"][
            "control_plane_generation_sha256"
        ] = "h" * 64
        candidate["runner_classes"][cutover.TARGET_CLASS][
            "control_plane_generation_sha256"
        ] = "h" * 64
        return current, candidate

    def test_accepts_only_lane_b_runner_uid_specialization(self):
        current, candidate = self.roots()
        before, after = cutover._validate_identity_delta(current, candidate)
        self.assertEqual(before["lane-a"], after["lane-a"])
        self.assertNotEqual(
            before[cutover.TARGET_CLASS],
            after[cutover.TARGET_CLASS],
        )

    def test_rejects_non_target_semantic_change(self):
        current, candidate = self.roots()
        candidate["runner_classes"]["lane-a"]["systemd_common"]["CPUQuota"] = "500%"
        with self.assertRaisesRegex(
            cutover.RunnerIdentityCutoverError,
            "non-target runner class changed",
        ):
            cutover._validate_identity_delta(current, candidate)

    def test_rejects_lane_b_change_beyond_uid(self):
        current, candidate = self.roots()
        candidate["runner_classes"][cutover.TARGET_CLASS]["resource_class"][
            "gpu_count"
        ] = 2
        with self.assertRaisesRegex(
            cutover.RunnerIdentityCutoverError,
            "beyond runner UID specialization",
        ):
            cutover._validate_identity_delta(current, candidate)

    def test_rejects_wrong_predecessor_identity(self):
        current, candidate = self.roots()
        current["runner_classes"][cutover.TARGET_CLASS][
            "project_runner_identity"
        ]["user"] = "unexpected"
        with self.assertRaisesRegex(
            cutover.RunnerIdentityCutoverError,
            "not predecessor",
        ):
            cutover._validate_identity_delta(current, candidate)


if __name__ == "__main__":
    unittest.main()
