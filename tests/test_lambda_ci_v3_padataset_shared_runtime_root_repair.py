import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPAIR = ROOT / "scripts/lambda_ci_v3_padataset_shared_runtime_root_repair_v1.py"
CUTOVER = ROOT / "scripts/lambda_ci_v3_padataset_lane_b_runner_identity_cutover_v1.py"


class PadatasetSharedRuntimeRootRepairTests(unittest.TestCase):
    def test_repair_scope_is_exact_and_nonrecursive(self):
        source = REPAIR.read_text()
        for path in (
            "/srv/workspace-ci/padataset/jobs",
            "/srv/workspace-ci/padataset/staging-cache",
            "/srv/workspace-ci/padataset/logs",
        ):
            self.assertIn(path, source)
        self.assertNotIn("os.walk(", source)
        self.assertNotIn("chmod -R", source)
        self.assertNotIn("chown(", source)

    def test_group_receives_traverse_only(self):
        mode = 0o710
        self.assertEqual(mode & 0o070, 0o010)
        self.assertEqual(mode & 0o060, 0)
        self.assertEqual(mode & 0o007, 0)

    def test_cutover_enforces_shared_root_repair_and_verification(self):
        source = CUTOVER.read_text()
        self.assertIn("_repair_shared_project_roots()", source)
        self.assertIn("_verify_shared_project_roots()", source)
        self.assertIn(
            'SHARED_PADATASET_ROOTS=0710 ci-padataset:ci-padataset',
            source,
        )


if __name__ == "__main__":
    unittest.main()
