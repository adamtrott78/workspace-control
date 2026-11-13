import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "workspace-shell" / "install" / "refresh_padataset_checkpoint_v1.sh"
TASK = ROOT / "tasks" / "active" / "mth602-final-multisurrogate-dqnguard-v1.json"
TARGET = "db8e2a1a97b69b73e3602e83ebd196686ceaaa95"


class PadatasetCheckpointRefreshContractTests(unittest.TestCase):
    def test_refresh_operator_shell_syntax_and_fail_closed_markers(self):
        cp = subprocess.run(
            ["/usr/bin/bash", "-n", str(SCRIPT)],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        source = SCRIPT.read_text()
        for marker in (
            'EXPECTED_OLD_AUTHORITY_SHA="\${1:-}"',
            'EXPECTED_NEW_AUTHORITY_SHA="\${2:-}"',
            'EXPECTED_OLD_PAD_SHA="\${3:-}"',
            'EXPECTED_NEW_PAD_SHA="\${4:-}"',
            'AUTHORITY_ROOT="/etc/workspace-shell/authority"',
            'PAD_ROOT="/srv/workspace-shell/PADataset"',
            'merge-base --is-ancestor "$EXPECTED_OLD_AUTHORITY_SHA" "$EXPECTED_NEW_AUTHORITY_SHA"',
            'merge-base --is-ancestor "$EXPECTED_OLD_PAD_SHA" "$EXPECTED_NEW_PAD_SHA"',
            'live authority snapshot is dirty',
            'live PADataset execution snapshot is dirty',
            'candidate checkpoint',
            'remote PADataset branch head',
            'BACKUP="/var/lib/workspace-shell/upgrades/padataset-checkpoint-',
            'Checkpoint refresh failed; rolling back',
            'sudo cp -a "$BACKUP/authority" "$AUTHORITY_ROOT"',
            'sudo cp -a "$BACKUP/PADataset" "$PAD_ROOT"',
            'PADATASET_CHECKPOINT_REFRESH=PASS',
        ):
            self.assertIn(marker, source)
        self.assertNotIn("git reset", source)
        self.assertNotIn("git clean", source)
        self.assertNotIn("git stash", source)

    def test_task_authority_binds_exact_repaired_padataset_head(self):
        data = json.loads(TASK.read_text())
        repo = next(r for r in data["repositories"] if r["name"] == "PADataset")
        self.assertEqual(repo["remote"]["checkpoint_sha"], TARGET)
        self.assertEqual(data["status"], "IN_PROGRESS")
        self.assertIn(TARGET, data["next_safe_action"])
        self.assertTrue(any(c.get("identity") == TARGET for c in data["checkpoints"]))


if __name__ == "__main__":
    unittest.main()
