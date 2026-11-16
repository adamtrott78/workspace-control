import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "workspace-shell"
sys.path.insert(0, str(PLUGIN / "root"))
job_launcher = importlib.import_module("job_launcher")
candidate_materializer = importlib.import_module("candidate_materializer")


class WorkspaceShellMultirepoResearchTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((PLUGIN / "config" / "profiles.v1.json").read_text())

    def test_padataset_profile_matrix_is_fail_closed(self):
        for profile in ("git-read", "candidate-pytest", "file-list", "file-read", "file-hash", "research-bounded"):
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

    def test_candidate_materializer_public_transport_is_credential_free_and_private_mode_exists(self):
        env = candidate_materializer.git_env({
            "transport": "public_https",
            "url": "https://github.com/adamtrott78/PADataset.git",
        })
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertNotIn("GIT_SSH_COMMAND", env)
        with self.assertRaisesRegex(Exception, "SOURCE_CONFIG_INVALID"):
            candidate_materializer.git_env({
                "transport": "public_https",
                "url": "https://token@github.com/adamtrott78/PADataset.git",
            })
        source = (PLUGIN / "root" / "candidate_materializer.py").read_text()
        self.assertIn('"ssh_deploy_key"', source)
        self.assertIn("StrictHostKeyChecking=yes", source)
        self.assertIn("deploy key must be root-private", source)

    def test_candidate_pytest_is_sandbox_copy_only(self):
        resolved = job_launcher.resolve_profile(
            self.manifest,
            "candidate-pytest",
            ["-q", "tests/test_cross_surrogate_dqnguard.py"],
        )
        self.assertEqual(resolved["executable"], "/usr/bin/python3")
        self.assertTrue(resolved["write_scratch"])
        self.assertEqual(resolved["argv"][:3], ["-m", "pytest", "-q"])
        self.assertEqual(self.manifest["profiles"]["candidate-pytest"]["network"], "deny")
        self.assertEqual(resolved["env"]["PYTHONPATH"], "/workspace")
        self.assertIn("/usr/lib/x86_64-linux-gnu/blas", resolved["env"]["LD_LIBRARY_PATH"])

    def test_research_profile_is_sandbox_copy_only(self):
        resolved = job_launcher.resolve_profile(
            self.manifest,
            "research-bounded",
            ["experiments/pa_eval_osr_one.py", "--help"],
        )
        self.assertEqual(resolved["executable"], "/usr/bin/python3")
        self.assertTrue(resolved["write_scratch"])
        self.assertEqual(resolved["argv"][:2], ["-B", "experiments/pa_eval_osr_one.py"])

        contract_test = job_launcher.resolve_profile(
            self.manifest,
            "research-bounded",
            ["tests/test_multisurrogate_dqnguard.py"],
        )
        self.assertEqual(contract_test["argv"], ["-B", "tests/test_multisurrogate_dqnguard.py"])
        self.assertEqual(contract_test["env"]["PYTHONPATH"], "/workspace")
        self.assertEqual(
            contract_test["env"]["LD_LIBRARY_PATH"],
            "/usr/lib/x86_64-linux-gnu/blas:/usr/lib/x86_64-linux-gnu/lapack:/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu",
        )
        with self.assertRaisesRegex(Exception, "PROFILE_ARGV_DENIED"):
            job_launcher.resolve_profile(
                self.manifest,
                "research-bounded",
                ["tests/test_other_research.py"],
            )
        self.assertEqual(self.manifest["profiles"]["research-bounded"]["network"], "deny")
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
        self.assertIn('"candidate_materializer_socket": control_root + "/candidate-materializer.sock"', render)
        self.assertIn('"candidate_store_root": "/var/lib/workspace-shell/candidates"', render)
        self.assertIn('"transport": "public_https"', render)
        self.assertIn('"workspace-shell-candidate-materializer.service"', render)

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
        self.assertIn('EXPECTED_PAD_EXEC_SHA="${3:-}"', upgrade)
        self.assertIn('PAD_EVIDENCE_ROOT="${PADATASET_CHECKOUT:-$HOME/adamArchives/Adam/varMax/PADataset}"', upgrade)
        self.assertIn('git -C "$PAD_FETCH" init --quiet', upgrade)
        self.assertIn('git -C "$PAD_FETCH" remote add origin "$PAD_EXEC_REPO_URL"', upgrade)
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
        self.assertIn('"candidate-pytest"', upgrade)
        self.assertIn("workspace-shell-candidate-materializer.service", upgrade)
        self.assertIn("git_retry() {", upgrade)
        self.assertIn("-c http.version=HTTP/1.1 fetch --quiet --depth=1 --no-tags", upgrade)
        self.assertIn("unable to fetch exact PADataset execution SHA after bounded retries", upgrade)
        self.assertIn("restore /etc/workspace-shell/frontend.json", upgrade)
        self.assertIn('candidate_unit = "workspace-shell-candidate-materializer.service"', upgrade)
        self.assertIn("os.chown(ftmp, fst.st_uid, fst.st_gid)", upgrade)
        self.assertIn("candidate-materializer.sock", upgrade)
        self.assertIn("/var/lib/workspace-shell/candidates", upgrade)
        self.assertIn('"historical_checkout_mutated": False', upgrade)
        self.assertIn('data.setdefault("evidence_roots", {})', upgrade)
        self.assertIn("/srv/workspace-shell/PADataset-evidence", upgrade)
        self.assertIn("attempting rollback", upgrade)

    def test_task_source_falls_back_to_exact_materialization_only_for_authorized_checkpoint(self):
        cfg = {
            "source_roots": {"workspace-control": "/srv/workspace-shell/workspace-control"},
        }
        materialized = {
            "candidate_sha": "b" * 40,
            "repository": "adamtrott78/workspace-control",
            "transport": "public_https",
        }
        with (
            mock.patch.object(job_launcher, "verify_source_tree", side_effect=lambda path, uid: Path(path)),
            mock.patch.object(job_launcher, "hardened_git", side_effect=["a" * 40, "b" * 40]),
            mock.patch.object(
                job_launcher,
                "candidate_materializer_rpc",
                return_value=(Path("/var/lib/workspace-shell/candidates/workspace-control/" + "b" * 40), materialized),
            ) as materialize,
        ):
            source, evidence = job_launcher.resolve_task_source_root(
                cfg,
                "workspace-control",
                "b" * 40,
                "b" * 40,
                41011,
            )
        self.assertEqual(source.name, "b" * 40)
        self.assertEqual(evidence, materialized)
        materialize.assert_called_once_with(cfg, "workspace-control", "b" * 40)

    def test_task_source_never_materializes_a_sha_different_from_task_checkpoint(self):
        cfg = {
            "source_roots": {"workspace-control": "/srv/workspace-shell/workspace-control"},
        }
        with self.assertRaisesRegex(Exception, "TASK_SOURCE_SHA_MISMATCH"):
            job_launcher.resolve_task_source_root(
                cfg,
                "workspace-control",
                "b" * 40,
                "c" * 40,
                41011,
            )

    def test_upgrade_can_enroll_exact_semantic_capsule_without_rebinding_execution(self):
        upgrade = (PLUGIN / "install" / "upgrade_multirepo_padataset_v1.sh").read_text()
        self.assertIn('EXPECTED_SEMANTIC_CAPSULE_SHA="${4:-}"', upgrade)
        self.assertIn('EXPECTED_SEMANTIC_EXEC_SHA="${5:-}"', upgrade)
        self.assertIn('SEMANTIC_TASK_ID="workspace-semantic-execution-migration-v1"', upgrade)
        self.assertIn("SEMANTIC_DURABLE_TASK_BINDING=PASS", upgrade)
        self.assertIn("semantic task execution binding", upgrade)
        self.assertIn("LOCAL_SEMANTIC_TASK_MCP=PASS", upgrade)
        self.assertIn("LOCAL_SEMANTIC_TASK_RECEIPT=PASS", upgrade)
        self.assertIn("LOCAL_SEMANTIC_TASK_AUTHORITY=PASS", upgrade)
        self.assertIn('receipt.get("observed_git_sha") == expected', upgrade)
        self.assertIn('receipt.get("task_checkpoint_sha") == expected', upgrade)
        self.assertIn('receipt.get("source_mode") == "task"', upgrade)
        self.assertIn('receipt.get("privileged") is False', upgrade)
        self.assertNotIn("semantic exact execution SHA missing from live MCP result", upgrade)
        self.assertIn('"profile":"git-read"', upgrade)
        self.assertIn('"argv":["rev-parse","HEAD"]', upgrade)
        self.assertIn("authority snapshot has unexpected changes after semantic enrollment", upgrade)
        self.assertIn("SEMANTIC_EXECUTION_BINDING=", upgrade)

    def test_launcher_binds_evidence_inside_workspace_without_schema_change(self):
        source = (PLUGIN / "root" / "job_launcher.py").read_text()
        self.assertIn('def build_bwrap_command(cfg, workspace_path, cwd, resolved, evidence_root=None):', source)
        self.assertIn('"/workspace/local_artifacts/evidence"', source)
        self.assertIn('"EVIDENCE_NOT_READ_ONLY_MOUNT"', source)
        self.assertIn('cfg.get("evidence_roots", {}).get(request["target"])', source)


if __name__ == "__main__":
    unittest.main()
