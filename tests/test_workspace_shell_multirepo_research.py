import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "workspace-shell"
sys.path.insert(0, str(PLUGIN / "root"))
job_launcher = importlib.import_module("job_launcher")


class WorkspaceShellMultirepoResearchTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())

    def test_padataset_profile_matrix_is_fail_closed(self):
        for profile in ("git-read", "file-list", "file-read", "file-hash", "research-bounded"):
            job_launcher.assert_target_profile("PADataset", profile)
        with self.assertRaisesRegex(Exception, "TARGET_PROFILE_DENIED"):
            job_launcher.assert_target_profile("PADataset", "validation-bounded")
        with self.assertRaisesRegex(Exception, "TARGET_PROFILE_DENIED"):
            job_launcher.assert_target_profile("workspace-control", "research-bounded")
        with self.assertRaisesRegex(Exception, "TARGET_PROFILE_DENIED"):
            job_launcher.assert_target_profile("unknown", "git-read")

    def test_evidence_profiles_are_read_only_and_bounded(self):
        listing = job_launcher.resolve_profile(
            self.manifest,
            "file-list",
            ["results", "-maxdepth", "4", "-type", "f", "-name", "*.csv", "-print"],
        )
        self.assertEqual(listing["executable"], "/usr/bin/find")
        self.assertFalse(listing["write_scratch"])

        reader = job_launcher.resolve_profile(
            self.manifest,
            "file-read",
            ["-c", "65536", "--", "results/example.csv"],
        )
        self.assertEqual(reader["executable"], "/usr/bin/head")
        self.assertFalse(reader["write_scratch"])

        hasher = job_launcher.resolve_profile(
            self.manifest,
            "file-hash",
            ["results/example.csv"],
        )
        self.assertEqual(hasher["executable"], "/usr/bin/sha256sum")
        self.assertFalse(hasher["write_scratch"])

        with self.assertRaisesRegex(Exception, "PROFILE_ARGV_DENIED"):
            job_launcher.resolve_profile(
                self.manifest,
                "file-read",
                ["-c", "65537", "--", "results/example.csv"],
            )

    def test_research_profile_is_sandbox_copy_only(self):
        resolved = job_launcher.resolve_profile(
            self.manifest,
            "research-bounded",
            ["experiments/pa_eval_osr_one.py", "--help"],
        )
        self.assertEqual(resolved["executable"], "/usr/bin/python3")
        self.assertTrue(resolved["write_scratch"])
        self.assertEqual(resolved["argv"][:2], ["-B", "experiments/pa_eval_osr_one.py"])
        self.assertEqual(self.manifest["profiles"]["research-bounded"]["network"], "deny")

        contract_test = job_launcher.resolve_profile(
            self.manifest,
            "research-bounded",
            ["tests/test_multisurrogate_dqnguard.py"],
        )
        self.assertEqual(
            contract_test["argv"],
            ["-B", "tests/test_multisurrogate_dqnguard.py"],
        )
        self.assertEqual(
            contract_test["env"]["LD_LIBRARY_PATH"],
            "/usr/lib/x86_64-linux-gnu/blas:"
            "/usr/lib/x86_64-linux-gnu/lapack:"
            "/usr/lib/x86_64-linux-gnu:"
            "/lib/x86_64-linux-gnu",
        )
        with self.assertRaisesRegex(Exception, "PROFILE_ARGV_DENIED"):
            job_launcher.resolve_profile(
                self.manifest,
                "research-bounded",
                ["tests/test_other_research.py"],
            )
        with self.assertRaisesRegex(Exception, "PROFILE_ARGV_DENIED"):
            job_launcher.resolve_profile(
                self.manifest,
                "research-bounded",
                ["papers/not-authorized.py"],
            )

    def test_task_capsules_validate_and_handoffs_match_renderer(self):
        for stem in (
            "workspace-shell-multirepo-research-v1",
            "mth602-final-multisurrogate-dqnguard-v1",
        ):
            task = ROOT / "tasks" / "active" / f"{stem}.json"
            handoff = task.with_suffix(".md")
            validated = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "workspace_control.py"),
                    "task-validate",
                    "--file",
                    str(task),
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            with tempfile.TemporaryDirectory() as td:
                rendered = Path(td) / "handoff.md"
                cp = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "workspace_control.py"),
                        "task-render",
                        "--file",
                        str(task),
                        "--output",
                        str(rendered),
                    ],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
                self.assertEqual(handoff.read_text(), rendered.read_text())

    def test_upgrade_operator_shell_syntax(self):
        upgrade = PLUGIN / "install" / "upgrade_multirepo_padataset_v1.sh"
        cp = subprocess.run(
            ["/usr/bin/bash", "-n", str(upgrade)],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)

    def test_install_and_upgrade_separate_clean_execution_from_historical_evidence(self):
        render = (PLUGIN / "install" / "render_install.py").read_text()
        self.assertIn('padataset_root = "/srv/workspace-shell/PADataset"', render)
        self.assertIn('padataset_evidence_root = "/srv/workspace-shell/PADataset-evidence"', render)
        self.assertIn('"PADataset": padataset_root', render)
        self.assertIn('"evidence_roots": {"PADataset": padataset_evidence_root}', render)

        upgrade = (PLUGIN / "install" / "upgrade_multirepo_padataset_v1.sh").read_text()
        self.assertIn('AUTHORITY_ROOT="/etc/workspace-shell/authority"', upgrade)
        self.assertIn('EXPECTED_AUTHORITY_SHA="${1:-}"', upgrade)
        self.assertIn('EXPECTED_EXEC_SHA="${2:-}"', upgrade)
        self.assertIn('DURABLE_TASK_BINDINGS=PASS', upgrade)
        self.assertIn('sudo cp -a --reflink=auto "$ROOT/." "$AUTH_NEXT/"', upgrade)
        self.assertIn('sudo cp -a --reflink=auto "$WC_FETCH/." "$WC_NEXT/"', upgrade)
        self.assertIn('restore "$AUTHORITY_ROOT"', upgrade)
        self.assertIn('sudo cp -a "$WC_FETCH/plugins/workspace-shell" "$RUNTIME_PLUGIN"', upgrade)
        self.assertIn("workspace-shell-multirepo-research-v1", upgrade)
        self.assertIn("mth602-final-multisurrogate-dqnguard-v1", upgrade)
        self.assertIn("LOCAL_TASK_AUTHORITY=PASS", upgrade)
        self.assertIn("17e1147614f27702e43565089d618182ff71c5af", upgrade)
        self.assertIn('PAD_EVIDENCE_ROOT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"', upgrade)
        self.assertIn('git clone --filter=blob:none --no-checkout "$PAD_EXEC_REPO_URL" "$PAD_FETCH"', upgrade)
        self.assertIn('mount --bind "$PAD_EVIDENCE_ROOT" "$EVIDENCE_MOUNT"', upgrade)
        self.assertIn('remount,bind,ro,nosuid,nodev,noexec', upgrade)
        self.assertIn('EVIDENCE_MOUNT_PREEXISTING=0', upgrade)
        self.assertIn("verify_existing_evidence_mount()", upgrade)
        self.assertIn("stat -Lc '%d:%i'", upgrade)
        self.assertIn('existing bind is not read-only', upgrade)
        self.assertIn('existing bind is missing $required', upgrade)
        self.assertIn('already present and verified safe; reusing it', upgrade)
        self.assertIn('chmod -R a+rX,go-w "$AUTH_NEXT" "$WC_NEXT" "$PAD_NEXT"', upgrade)
        self.assertIn('trap \'rollback "$?"\' EXIT', upgrade)
        self.assertIn("rollback() {", upgrade)
        self.assertIn('rc="$1"', upgrade)
        self.assertIn("MCP_READY=0", upgrade)
        self.assertIn("for attempt in $(seq 1 20)", upgrade)
        self.assertIn("LOCAL_MCP_READY=PASS", upgrade)
        self.assertIn('rollback "$rc"', upgrade)
        self.assertIn('BACKUP_NODE_MODULES="$BACKUP_RUNTIME_PLUGIN/node_modules"', upgrade)
        self.assertIn('sudo cp -a "$BACKUP_NODE_MODULES" "$RUNTIME_PLUGIN/node_modules"', upgrade)
        self.assertIn('"@modelcontextprotocol/ext-apps"', upgrade)
        self.assertIn('RUNTIME_NODE_DEPENDENCIES=PASS', upgrade)
        self.assertIn('LOCAL_MCP_DISCOVERY=PASS', upgrade)
        self.assertIn('"method":"tools/list"', upgrade)
        self.assertIn('"PADataset"', upgrade)
        self.assertIn('"research-bounded"', upgrade)
        self.assertIn('"historical_checkout_mutated": False', upgrade)
        self.assertIn('data.setdefault("evidence_roots", {})', upgrade)
        self.assertIn("/srv/workspace-shell/PADataset-evidence", upgrade)
        self.assertIn("attempting rollback", upgrade)

    def test_launcher_binds_evidence_inside_workspace_without_schema_change(self):
        source = (PLUGIN / "root" / "job_launcher.py").read_text()
        self.assertIn('def build_bwrap_command(cfg, workspace_path, cwd, resolved, evidence_root=None):', source)
        self.assertIn('"/workspace/local_artifacts/evidence"', source)
        self.assertIn('"EVIDENCE_NOT_READ_ONLY_MOUNT"', source)
        self.assertIn('cfg.get("evidence_roots", {}).get(request["target"])', source)


if __name__ == "__main__":
    unittest.main()
