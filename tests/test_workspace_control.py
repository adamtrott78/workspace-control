#!/usr/bin/env python3
"""workspace-control compatibility and v2 validation/render tests."""

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "scripts" / "workspace_control.py"

spec = importlib.util.spec_from_file_location("workspace_control", SCRIPT)
workspace_control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace_control)

REPOS = json.loads((ROOT / "repos.json").read_text())["repositories"]


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def git_blob_sha(data):
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


class SchemaScaffoldingTests(unittest.TestCase):
    def test_v1_schema_frozen_blob_identity(self):
        data = (SCHEMAS / "task_capsule.v1.schema.json").read_bytes()
        self.assertEqual(
            git_blob_sha(data),
            "40fa76125f61c0ad8e11a10a45347dbb36c63a84",
        )

    def test_dispatch_schema_references_v1_and_v2(self):
        dispatch = load_json(SCHEMAS / "task_capsule.schema.json")
        refs = [entry["$ref"] for entry in dispatch["oneOf"]]
        self.assertEqual(
            refs,
            [
                "task_capsule.v1.schema.json",
                "task_capsule.v2.schema.json",
            ],
        )

    def test_schema_versions_are_explicit(self):
        self.assertEqual(
            load_json(SCHEMAS / "task_capsule.v1.schema.json")
            ["properties"]["schema_version"]["const"],
            1,
        )
        self.assertEqual(
            load_json(SCHEMAS / "task_capsule.v2.schema.json")
            ["properties"]["schema_version"]["const"],
            2,
        )


class TaskValidationTests(unittest.TestCase):
    def validate_fixture(self, name):
        data = load_json(FIXTURES / name)
        virtual_path = Path(f"{data['task_id']}.json")
        return workspace_control.validate_task_capsule_data(
            data,
            virtual_path,
            REPOS,
        )

    def test_v1_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v1_minimal.json"),
            [],
        )

    def test_v2_remote_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v2_remote.json"),
            [],
        )

    def test_v2_local_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v2_local.json"),
            [],
        )

    def test_v2_composed_fixture_validates(self):
        self.assertEqual(
            self.validate_fixture("task_capsule_v2_composed.json"),
            [],
        )

    def test_unknown_schema_version_fails_explicitly(self):
        data = load_json(FIXTURES / "task_capsule_v2_remote.json")
        data["schema_version"] = 99
        errors = workspace_control.validate_task_capsule_data(
            data,
            Path(f"{data['task_id']}.json"),
            REPOS,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("unsupported value 99", errors[0])

    def test_remote_only_rejects_local_state(self):
        data = load_json(FIXTURES / "task_capsule_v2_remote.json")
        data["repositories"][0]["local"] = {
            "checkout_path": "/tmp/example",
            "branch": "example",
            "head_sha": "0" * 40,
            "clean": True,
        }
        errors = workspace_control.validate_task_capsule_data(
            data,
            Path(f"{data['task_id']}.json"),
            REPOS,
        )
        self.assertIn(
            "execution_topology: remote_only must not require "
            "local repository state",
            errors,
        )


class TaskRenderTests(unittest.TestCase):
    def test_render_is_deterministic_and_derived(self):
        path = FIXTURES / "task_capsule_v2_remote.json"
        data = load_json(path)
        first = workspace_control.render_task_handoff(
            path,
            data,
            ROOT,
        )
        second = workspace_control.render_task_handoff(
            path,
            data,
            ROOT,
        )
        self.assertEqual(first, second)
        self.assertTrue(
            first.startswith(
                workspace_control.DERIVED_HANDOFF_MARKER
            )
        )
        self.assertIn(data["next_safe_action"], first)
        self.assertIn(
            "tests/fixtures/task_capsule_v2_remote.json",
            first,
        )


class PreflightTopologyTests(unittest.TestCase):
    REMOTE_SHA = "77c7355bbafeb674dd35b55bcfdb542d50c6079c"

    def remote_record(self):
        with patch.object(
            workspace_control,
            "query_remote_branch_url",
            return_value={
                "status": "FOUND",
                "branch": "control-plane-v2-refactor",
                "sha": self.REMOTE_SHA,
                "error": None,
            },
        ):
            return workspace_control.inspect_remote(
                "workspace-control",
                REPOS["workspace-control"],
                "control-plane-v2-refactor",
            )

    def test_existing_preflight_invocation_defaults_to_local(self):
        args = workspace_control.build_parser().parse_args(
            [
                "preflight",
                "--repo",
                "workspace-control",
                "--intent",
                "mutate",
            ]
        )
        self.assertEqual(args.topology, "local")
        self.assertIsNone(args.branch)
        self.assertIsNone(args.expected_parent)

    def test_remote_inspection_uses_registered_remote_without_checkout(self):
        with patch.object(
            workspace_control,
            "query_remote_branch_url",
            return_value={
                "status": "FOUND",
                "branch": "control-plane-v2-refactor",
                "sha": self.REMOTE_SHA,
                "error": None,
            },
        ) as query:
            record = workspace_control.inspect_remote(
                "workspace-control",
                REPOS["workspace-control"],
                "control-plane-v2-refactor",
            )

        query.assert_called_once_with(
            REPOS["workspace-control"]["remote"],
            "control-plane-v2-refactor",
        )
        self.assertEqual(record["topology"], "remote")
        self.assertNotIn("requested_path", record)
        self.assertNotIn("git_root", record)
        self.assertNotIn("worktrees", record)

    def test_remote_mutation_ready_at_expected_parent(self):
        state, code, reasons = workspace_control.remote_preflight_state(
            self.remote_record(),
            "mutate",
            self.REMOTE_SHA,
            True,
            "reversible",
            [
                "scripts/workspace_control.py",
                "procedures/repo_preflight.md",
                "tests/test_workspace_control.py",
                "tests/fixtures/**",
            ],
            [
                "scripts/workspace_control.py",
                "procedures/repo_preflight.md",
                "tests/test_workspace_control.py",
            ],
        )
        self.assertEqual((state, code, reasons), ("READY", 0, []))

    def test_remote_parent_mismatch_requires_review(self):
        state, code, reasons = workspace_control.remote_preflight_state(
            self.remote_record(),
            "mutate",
            "0" * 40,
            True,
            "reversible",
            ["scripts/workspace_control.py"],
            ["scripts/workspace_control.py"],
        )
        self.assertEqual(state, "REVIEW_REQUIRED")
        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertIn("expected parent", reasons[0])

    def test_remote_scope_violation_is_policy_block(self):
        state, code, reasons = workspace_control.remote_preflight_state(
            self.remote_record(),
            "mutate",
            self.REMOTE_SHA,
            True,
            "reversible",
            ["scripts/workspace_control.py"],
            ["README.md"],
        )
        self.assertEqual(state, "BLOCKED_POLICY")
        self.assertEqual(code, workspace_control.EXIT_POLICY)
        self.assertIn("README.md", reasons[0])

    def test_remote_mutation_requires_surface_capability(self):
        state, code, reasons = workspace_control.remote_preflight_state(
            self.remote_record(),
            "mutate",
            self.REMOTE_SHA,
            False,
            "reversible",
            ["scripts/workspace_control.py"],
            ["scripts/workspace_control.py"],
        )
        self.assertEqual(state, "REVIEW_REQUIRED")
        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertTrue(
            any("write capability" in reason for reason in reasons)
        )

    def test_remote_non_writable_repository_is_policy_block(self):
        record = self.remote_record()
        record["writable"] = False
        state, code, reasons = workspace_control.remote_preflight_state(
            record,
            "mutate",
            self.REMOTE_SHA,
            True,
            "reversible",
            ["scripts/workspace_control.py"],
            ["scripts/workspace_control.py"],
        )
        self.assertEqual(state, "BLOCKED_POLICY")
        self.assertEqual(code, workspace_control.EXIT_POLICY)
        self.assertIn("non-writable", reasons[0])

    def test_composed_is_not_an_opaque_preflight_mode(self):
        parser = workspace_control.build_parser()
        with self.assertRaises(SystemExit) as raised:
            parser.parse_args(
                [
                    "preflight",
                    "--repo",
                    "workspace-control",
                    "--topology",
                    "composed",
                ]
            )
        self.assertEqual(raised.exception.code, 2)


class HandoffTopologyTests(unittest.TestCase):
    def virtual_fixture(self, name):
        data = load_json(FIXTURES / name)
        return Path(f"{data['task_id']}.json"), data

    def matching_local_record(self, data):
        entry = data["repositories"][0]
        local = entry["local"]
        return {
            "name": entry["name"],
            "exists": True,
            "git": True,
            "git_root": local["checkout_path"],
            "identity_matches": True,
            "branch": local["branch"],
            "head": local["head_sha"],
            "clean": True,
        }

    def test_v1_handoff_behavior_remains_on_v1_dispatch(self):
        path, data = self.virtual_fixture(
            "task_capsule_v1_minimal.json"
        )
        entry = data["repositories"][0]
        record = {
            "exists": True,
            "git": True,
            "git_root": entry["checkout_path"],
            "identity_matches": True,
            "branch": entry["branch"],
            "head": entry["checkpoint_sha"],
            "clean": True,
        }

        with (
            patch.object(
                workspace_control,
                "inspect_checkout",
                return_value=record,
            ),
            patch.object(
                workspace_control,
                "check_commit_exists",
                return_value=True,
            ),
            patch.object(
                workspace_control,
                "check_ancestor",
                return_value=True,
            ),
        ):
            payload, code = workspace_control.handoff_assessment(
                path,
                data,
                ROOT,
                REPOS,
            )

        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["result"], "HANDOFF_SAFE")
        self.assertNotIn("execution_readiness", payload)

    def test_remote_only_handoff_safe_without_local_or_live_remote_access(self):
        path, data = self.virtual_fixture(
            "task_capsule_v2_remote.json"
        )

        with (
            patch.object(
                workspace_control,
                "inspect_checkout",
                side_effect=AssertionError(
                    "remote-only handoff inspected local state"
                ),
            ),
            patch.object(
                workspace_control,
                "query_remote_branch_url",
                side_effect=AssertionError(
                    "HANDOFF_SAFE used transient live remote access"
                ),
            ),
        ):
            payload, code = workspace_control.handoff_assessment(
                path,
                data,
                ROOT,
                REPOS,
            )

        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertTrue(payload["handoff_safe"])
        self.assertEqual(payload["result"], "HANDOFF_SAFE")
        self.assertEqual(
            payload["execution_topology"],
            "remote_only",
        )
        self.assertIsNone(payload["repositories"][0]["local"])

    def test_local_handoff_safe_uses_recorded_local_checkpoint(self):
        path, data = self.virtual_fixture(
            "task_capsule_v2_local.json"
        )

        with (
            patch.object(
                workspace_control,
                "inspect_checkout",
                return_value=self.matching_local_record(data),
            ),
            patch.object(
                workspace_control,
                "check_commit_exists",
                return_value=True,
            ),
            patch.object(
                workspace_control,
                "check_ancestor",
                return_value=True,
            ),
        ):
            payload, code = workspace_control.handoff_assessment(
                path,
                data,
                ROOT,
                REPOS,
            )

        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(payload["result"], "HANDOFF_SAFE")
        self.assertTrue(payload["repositories"][0]["local"]["ready"])

    def test_composed_handoff_safe_proves_synchronization_boundary(self):
        path, data = self.virtual_fixture(
            "task_capsule_v2_composed.json"
        )

        with (
            patch.object(
                workspace_control,
                "inspect_checkout",
                return_value=self.matching_local_record(data),
            ),
            patch.object(
                workspace_control,
                "check_commit_exists",
                return_value=True,
            ),
            patch.object(
                workspace_control,
                "check_ancestor",
                return_value=True,
            ),
        ):
            payload, code = workspace_control.handoff_assessment(
                path,
                data,
                ROOT,
                REPOS,
            )

        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(payload["result"], "HANDOFF_SAFE")
        self.assertTrue(payload["workflow_resolution"]["resolved"])
        self.assertTrue(
            payload["synchronization_boundary"]["ready"]
        )

    def test_missing_workflow_checkpoint_binding_blocks_handoff(self):
        path, data = self.virtual_fixture(
            "task_capsule_v2_composed.json"
        )
        data["workflow"]["checkpoint_sha"] = "1" * 40

        with (
            patch.object(
                workspace_control,
                "inspect_checkout",
                return_value=self.matching_local_record(data),
            ),
            patch.object(
                workspace_control,
                "check_commit_exists",
                return_value=True,
            ),
            patch.object(
                workspace_control,
                "check_ancestor",
                return_value=True,
            ),
        ):
            payload, code = workspace_control.handoff_assessment(
                path,
                data,
                ROOT,
                REPOS,
            )

        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertFalse(payload["handoff_safe"])
        self.assertTrue(
            any(
                "workflow checkpoint" in reason
                for reason in payload["reasons"]
            )
        )

    def test_composed_without_sync_boundary_blocks_handoff(self):
        path, data = self.virtual_fixture(
            "task_capsule_v2_composed.json"
        )
        data["repositories"][0]["local"]["head_sha"] = "1" * 40
        data["stages"][1]["inputs"] = []

        with (
            patch.object(
                workspace_control,
                "inspect_checkout",
                return_value=self.matching_local_record(data),
            ),
            patch.object(
                workspace_control,
                "check_commit_exists",
                return_value=True,
            ),
            patch.object(
                workspace_control,
                "check_ancestor",
                return_value=True,
            ),
        ):
            payload, code = workspace_control.handoff_assessment(
                path,
                data,
                ROOT,
                REPOS,
            )

        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertFalse(payload["handoff_safe"])
        self.assertFalse(
            payload["synchronization_boundary"]["ready"]
        )

    def test_handoff_safe_can_be_receiver_not_execution_ready(self):
        path, data = self.virtual_fixture(
            "task_capsule_v2_remote.json"
        )

        payload, code = workspace_control.handoff_assessment(
            path,
            data,
            ROOT,
            REPOS,
            receiver="codex",
            receiver_checks=[
                {"name": "github", "ready": True},
                {"name": "local-runtime", "ready": False},
            ],
        )

        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(payload["result"], "HANDOFF_SAFE")
        readiness = payload["execution_readiness"]
        self.assertTrue(readiness["assessed"])
        self.assertFalse(readiness["ready"])
        self.assertEqual(
            readiness["result"],
            "NOT_EXECUTION_READY",
        )

    def test_receiver_checks_are_generic_and_deterministic(self):
        checks = workspace_control.parse_receiver_checks(
            [
                "github=ready",
                "local-runtime=missing",
            ]
        )
        self.assertEqual(
            checks,
            [
                {"name": "github", "ready": True},
                {"name": "local-runtime", "ready": False},
            ],
        )

        readiness = workspace_control.execution_readiness_assessment(
            "chatgpt",
            checks,
        )
        self.assertEqual(
            readiness["result"],
            "NOT_EXECUTION_READY",
        )


class WorktreePrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bare = self.root / "remote.git"
        self.source = self.root / "source"
        self.target = self.root / "task-worktree"

        self.run_git_raw(
            "init",
            "--bare",
            str(self.bare),
        )
        self.run_git_raw(
            "init",
            str(self.source),
        )
        self.git(self.source, "config", "user.name", "Phase7 Test")
        self.git(
            self.source,
            "config",
            "user.email",
            "phase7@example.invalid",
        )
        self.git(self.source, "checkout", "-b", "main")
        (self.source / "README.md").write_text("fixture\n")
        self.git(self.source, "add", "README.md")
        self.git(self.source, "commit", "-m", "base")
        self.git(
            self.source,
            "remote",
            "add",
            "origin",
            str(self.bare),
        )
        self.git(self.source, "push", "-u", "origin", "main")

        self.git(self.source, "checkout", "-b", "phase7-task")
        (self.source / "task.txt").write_text("task\n")
        self.git(self.source, "add", "task.txt")
        self.git(self.source, "commit", "-m", "task")
        self.expected = self.git(
            self.source,
            "rev-parse",
            "HEAD",
        )
        self.git(
            self.source,
            "push",
            "-u",
            "origin",
            "phase7-task",
        )
        self.git(self.source, "checkout", "main")

        self.cfg = {
            "path": "source",
            "remote": str(self.bare),
            "role": "managed",
            "writable": True,
            "canonical_branch": "main",
            "context_entry": "README.md",
            "authority": "phase7 test repository",
            "worktree_policy": "isolated_task_worktrees_preferred",
            "recursive_mutation_forbidden": False,
        }
        self.repos = {"fixture": self.cfg}

    def tearDown(self):
        self.temp.cleanup()

    def run_git_raw(self, *args):
        proc = subprocess.run(
            ["git", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode != 0:
            self.fail(
                "git command failed: git "
                + " ".join(args)
                + "\n"
                + proc.stderr
            )
        return proc.stdout.strip()

    def git(self, path, *args):
        proc = subprocess.run(
            ["git", "-C", str(path), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode != 0:
            self.fail(
                "git command failed: git -C "
                + str(path)
                + " "
                + " ".join(args)
                + "\n"
                + proc.stderr
            )
        return proc.stdout.strip()

    def assess(self, create=False, cfg=None, expected=None):
        cfg = cfg or self.cfg
        return workspace_control.worktree_prepare_assessment(
            "fixture",
            cfg,
            self.source,
            self.target,
            "phase7-task",
            expected or self.expected,
            self.root,
            {"fixture": cfg},
            create=create,
        )

    def test_missing_worktree_is_create_available_without_mutation(self):
        payload, code = self.assess()

        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertEqual(payload["result"], "CREATE_AVAILABLE")
        self.assertFalse(self.target.exists())
        self.assertFalse(payload["create_requested"])

    def test_explicit_create_produces_exact_clean_worktree(self):
        payload, code = self.assess(create=True)

        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(payload["result"], "READY")
        self.assertTrue(self.target.is_dir())
        self.assertEqual(
            self.git(self.target, "branch", "--show-current"),
            "phase7-task",
        )
        self.assertEqual(
            self.git(self.target, "rev-parse", "HEAD"),
            self.expected,
        )
        self.assertEqual(
            self.git(self.target, "status", "--porcelain"),
            "",
        )

    def test_dirty_source_blocks_creation_without_normalization(self):
        dirty = self.source / "unrelated.txt"
        dirty.write_text("preserve me\n")

        payload, code = self.assess(create=True)

        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertEqual(payload["result"], "BLOCKED_DIRTY")
        self.assertTrue(dirty.exists())
        self.assertFalse(self.target.exists())
        self.assertIn(
            "?? unrelated.txt",
            self.git(self.source, "status", "--porcelain"),
        )

    def test_remote_divergence_blocks_without_moving_local_branch(self):
        old_local = self.git(
            self.source,
            "rev-parse",
            "refs/heads/phase7-task",
        )
        self.git(self.source, "checkout", "phase7-task")
        (self.source / "task.txt").write_text("changed\n")
        self.git(self.source, "add", "task.txt")
        self.git(self.source, "commit", "-m", "remote moves")
        new_remote = self.git(self.source, "rev-parse", "HEAD")
        self.git(self.source, "push", "origin", "phase7-task")
        self.git(self.source, "checkout", "main")

        payload, code = self.assess(
            create=True,
            expected=old_local,
        )

        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertEqual(payload["result"], "BLOCKED_DIVERGED")
        self.assertEqual(
            self.git(
                self.source,
                "rev-parse",
                "refs/heads/phase7-task",
            ),
            new_remote,
        )
        self.assertFalse(self.target.exists())

    def test_dirty_existing_worktree_is_blocked_and_preserved(self):
        created, code = self.assess(create=True)
        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(created["result"], "READY")

        dirty = self.target / "local-only.txt"
        dirty.write_text("preserve me\n")

        payload, code = self.assess()

        self.assertEqual(code, workspace_control.EXIT_REVIEW)
        self.assertEqual(payload["result"], "BLOCKED_DIRTY")
        self.assertTrue(dirty.exists())
        self.assertIn(
            "?? local-only.txt",
            self.git(self.target, "status", "--porcelain"),
        )

    def test_non_writable_repository_cannot_create_missing_worktree(self):
        cfg = dict(self.cfg)
        cfg["writable"] = False

        payload, code = self.assess(
            create=True,
            cfg=cfg,
        )

        self.assertEqual(code, workspace_control.EXIT_POLICY)
        self.assertEqual(payload["result"], "BLOCKED_POLICY")
        self.assertFalse(self.target.exists())

    def test_existing_exact_worktree_is_ready_without_creation(self):
        created, code = self.assess(create=True)
        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(created["result"], "READY")

        payload, code = self.assess(create=False)

        self.assertEqual(code, workspace_control.EXIT_READY)
        self.assertEqual(payload["result"], "READY")
        self.assertFalse(payload["create_requested"])


if __name__ == "__main__":
    unittest.main()
