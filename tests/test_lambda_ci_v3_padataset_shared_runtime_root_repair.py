import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPAIR = ROOT / "scripts/lambda_ci_v3_padataset_shared_runtime_root_repair_v1.py"
CUTOVER = ROOT / "scripts/lambda_ci_v3_padataset_lane_b_runner_identity_cutover_v1.py"

spec = importlib.util.spec_from_file_location("padataset_shared_root_repair", REPAIR)
repair = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = repair
spec.loader.exec_module(repair)


class PadatasetSharedRuntimeRootRepairTests(unittest.TestCase):
    def test_repair_scope_is_exact_and_nonrecursive(self):
        self.assertEqual(
            repair.ROOT_MODES,
            {
                pathlib.Path("/srv/workspace-ci/padataset/jobs"): 0o750,
                pathlib.Path("/srv/workspace-ci/padataset/staging-cache"): 0o710,
                pathlib.Path("/srv/workspace-ci/padataset/logs"): 0o710,
            },
        )
        source = REPAIR.read_text()
        self.assertNotIn("os.walk(", source)
        self.assertNotIn("chmod -R", source)
        self.assertNotIn("chown(", source)

    def test_known_predecessor_jobs_0710_is_accepted(self):
        self.assertIn(0o710, repair.ACCEPTED_PRE_MODES[repair.JOBS])
        self.assertIn(0o700, repair.ACCEPTED_PRE_MODES[repair.JOBS])
        self.assertIn(0o750, repair.ACCEPTED_PRE_MODES[repair.JOBS])

    def test_jobs_parent_is_group_readable_and_traversable(self):
        mode = repair.ROOT_MODES[repair.JOBS]
        self.assertEqual(mode & 0o070, 0o050)
        self.assertEqual(mode & 0o020, 0)
        self.assertEqual(mode & 0o007, 0)

    def test_cache_and_logs_remain_traverse_only_for_group(self):
        for path in (repair.STAGING_CACHE, repair.LOGS):
            mode = repair.ROOT_MODES[path]
            self.assertEqual(mode & 0o070, 0o010)
            self.assertEqual(mode & 0o060, 0)
            self.assertEqual(mode & 0o007, 0)

    def test_mutation_uses_per_path_expected_mode(self):
        source = REPAIR.read_text()
        self.assertIn("os.chmod(path, expected_mode)", source)
        self.assertNotIn("os.chmod(path, 0o710)", source)

    def test_cutover_accepts_intermediate_jobs_0710_and_enforces_modes(self):
        source = CUTOVER.read_text()
        self.assertIn('if path.name == "jobs":', source)
        self.assertIn("accepted_modes.add(0o710)", source)
        self.assertIn("os.chmod(path, expected_mode)", source)
        self.assertIn(
            'SHARED_PADATASET_JOBS=0750 ci-padataset:ci-padataset',
            source,
        )
        self.assertIn(
            'SHARED_PADATASET_STAGING_CACHE=0710 ci-padataset:ci-padataset',
            source,
        )
        self.assertIn(
            'SHARED_PADATASET_LOGS=0710 ci-padataset:ci-padataset',
            source,
        )


if __name__ == "__main__":
    unittest.main()
