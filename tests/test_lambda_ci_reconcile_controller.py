import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lambda_ci_reconcile_controller as controller


def git_blob_sha(data: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {len(data)}\0".encode())
    digest.update(data)
    return digest.hexdigest()


class FakeGitHub:
    def __init__(
        self,
        *,
        actor="adamtrott78",
        current_sha=None,
        approved_sha=None,
        policy_changed=False,
        diverged=False,
    ):
        self.actor = actor
        self.current_sha = current_sha or ("a" * 40)
        self.approved_sha = approved_sha or self.current_sha
        self.diverged = diverged
        registry_raw = (
            ROOT / "architecture/lambda-ci-project-registry.v1.json"
        ).read_bytes()
        contracts_raw = (
            ROOT / "architecture/lambda-ci-execution-contracts.v1.json"
        ).read_bytes()
        workflow_raw = (ROOT / controller.WORKFLOW_PATH).read_bytes()
        research_raw = (
            ROOT / "architecture/lambda-ci-project-research-engine.v2.json"
        ).read_bytes()
        pad_raw = (
            ROOT / "architecture/lambda-ci-project-padataset.v1.json"
        ).read_bytes()

        approved = {
            controller.WORKFLOW_PATH: (workflow_raw, git_blob_sha(workflow_raw)),
            "architecture/lambda-ci-project-registry.v1.json": (
                registry_raw,
                git_blob_sha(registry_raw),
            ),
            "architecture/lambda-ci-execution-contracts.v1.json": (
                contracts_raw,
                git_blob_sha(contracts_raw),
            ),
            "architecture/lambda-ci-project-research-engine.v2.json": (
                research_raw,
                git_blob_sha(research_raw),
            ),
            "architecture/lambda-ci-project-padataset.v1.json": (
                pad_raw,
                git_blob_sha(pad_raw),
            ),
        }
        current = copy_docs(approved)
        if policy_changed:
            changed = registry_raw + b"\n"
            current["architecture/lambda-ci-project-registry.v1.json"] = (
                changed,
                git_blob_sha(changed),
            )
        self.docs_by_sha = {
            self.approved_sha: approved,
            self.current_sha: current,
        }

    def get_json(self, path):
        if "/branches/main" in path:
            return {"commit": {"sha": self.current_sha}}
        if "/actions/workflows/" in path:
            return {
                "workflow_runs": [
                    {
                        "id": 123,
                        "status": "completed",
                        "conclusion": "success",
                        "head_branch": "main",
                        "head_sha": self.approved_sha,
                        "event": "push",
                        "actor": {"login": self.actor},
                        "triggering_actor": {"login": self.actor},
                    }
                ]
            }
        if "/compare/" in path:
            return {"status": "diverged" if self.diverged else "ahead"}
        raise AssertionError(path)

    def content_at(self, path, sha):
        return self.docs_by_sha[sha][path]


def copy_docs(value):
    return {
        path: (bytes(raw), blob)
        for path, (raw, blob) in value.items()
    }


class ReconcileControllerTests(unittest.TestCase):
    def test_ceiling_pins_exact_workflow_blob(self):
        raw = (ROOT / controller.WORKFLOW_PATH).read_bytes()
        ceiling = json.loads(
            (ROOT / "architecture/lambda-ci-reconciliation-ceiling.v1.json").read_text()
        )
        self.assertEqual(
            ceiling["trusted_workflow_blob_sha"],
            git_blob_sha(raw),
        )

    def test_current_successful_run_requires_allowed_actor(self):
        good = FakeGitHub()
        run = controller._select_current_successful_run(good, {"adamtrott78"})
        self.assertEqual(run["head_sha"], good.approved_sha)
        self.assertEqual(run["_observed_main_sha"], good.current_sha)
        self.assertTrue(run["_policy_equivalent_to_main"])

        bad = FakeGitHub(actor="other-user")
        self.assertIsNone(
            controller._select_current_successful_run(bad, {"adamtrott78"})
        )

    def test_unrelated_main_commit_keeps_latest_approved_policy_applicable(self):
        fake = FakeGitHub(
            approved_sha="a" * 40,
            current_sha="b" * 40,
        )
        run = controller._select_current_successful_run(
            fake, {"adamtrott78"}
        )
        self.assertIsNotNone(run)
        self.assertEqual(run["head_sha"], "a" * 40)
        self.assertEqual(run["_observed_main_sha"], "b" * 40)
        self.assertTrue(run["_policy_equivalent_to_main"])

    def test_policy_relevant_main_change_requires_fresh_reconciliation_run(self):
        fake = FakeGitHub(
            approved_sha="a" * 40,
            current_sha="b" * 40,
            policy_changed=True,
        )
        self.assertIsNone(
            controller._select_current_successful_run(
                fake, {"adamtrott78"}
            )
        )

    def test_diverged_successful_run_is_not_reused(self):
        fake = FakeGitHub(
            approved_sha="a" * 40,
            current_sha="b" * 40,
            diverged=True,
        )
        self.assertIsNone(
            controller._select_current_successful_run(
                fake, {"adamtrott78"}
            )
        )

    def test_request_contains_only_reviewed_documents_and_attestation(self):
        fake = FakeGitHub()
        run = controller._select_current_successful_run(fake, {"adamtrott78"})
        request = controller.build_request(
            fake,
            run=run,
            allowed_actors={"adamtrott78"},
        )
        self.assertEqual(
            set(request),
            {
                "schema_version",
                "request_id",
                "operation",
                "source_attestation",
                "registry",
                "project_manifests",
                "dry_run",
            },
        )
        self.assertEqual(request["operation"], "APPLY_PROJECT_REGISTRY")
        self.assertFalse(request["dry_run"])
        self.assertEqual(
            request["source_attestation"]["repository"],
            "adamtrott78/workspace-control",
        )
        self.assertEqual(
            request["source_attestation"]["commit_sha"],
            fake.approved_sha,
        )
        self.assertEqual(
            [item["project_id"] for item in request["project_manifests"]],
            ["padataset", "research-engine"],
        )
        # Route documents legitimately contain reviewed trigger commands.
        # What must remain impossible is arbitrary executable/root authority in
        # the reconciliation envelope itself.
        for forbidden in (
            "command",
            "argv",
            "systemd_properties",
            "uid",
            "gid",
            "token",
            "environment",
        ):
            self.assertNotIn(forbidden, request)
            self.assertNotIn(forbidden, request["source_attestation"])
            self.assertNotIn(forbidden, request["registry"])
        for item in request["project_manifests"]:
            self.assertEqual(
                set(item),
                {"project_id", "sha256", "document"},
            )

    def test_existing_success_is_refreshed_to_equivalent_current_main(self):
        import tempfile
        from unittest import mock

        fake = FakeGitHub(
            approved_sha="a" * 40,
            current_sha="b" * 40,
        )
        run = controller._select_current_successful_run(
            fake, {"adamtrott78"}
        )
        request = controller.build_request(
            fake,
            run=run,
            allowed_actors={"adamtrott78"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            success = state_dir / "last-success.json"
            success.write_text(
                json.dumps(
                    {
                        "timestamp_utc": "old",
                        "commit_sha": request["source_attestation"]["commit_sha"],
                        "request_id": request["request_id"],
                        "workflow_run_id": 123,
                        "response": {"status": "PASS"},
                    }
                )
            )
            token = state_dir / "token"
            token.write_text("x")
            token.chmod(0o600)
            with mock.patch.object(
                controller,
                "GitHubClient",
                return_value=fake,
            ):
                result = controller.run_once(
                    token_file=token,
                    socket_path=state_dir / "unused.sock",
                    state_dir=state_dir,
                    allowed_actors={"adamtrott78"},
                )
            self.assertEqual(result["status"], "ALREADY_RECONCILED")
            self.assertEqual(result["approved_policy_sha"], "a" * 40)
            self.assertEqual(result["observed_main_sha"], "b" * 40)
            self.assertTrue(result["policy_equivalent_to_observed_main"])
            refreshed = json.loads(success.read_text())
            self.assertEqual(refreshed["observed_main_sha"], "b" * 40)
            self.assertTrue(
                refreshed["policy_equivalent_to_observed_main"]
            )

    def test_reconciliation_workflow_is_main_only_not_candidate_triggered(self):
        workflow = (ROOT / controller.WORKFLOW_PATH).read_text()
        self.assertIn("branches:", workflow)
        self.assertIn("- main", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("issue_comment:", workflow)
        self.assertNotIn("pull_request_target:", workflow)

    def test_controller_source_cannot_execute_shell_or_subprocess(self):
        source = (ROOT / "scripts/lambda_ci_reconcile_controller.py").read_text()
        for forbidden in (
            "import subprocess",
            "os.system(",
            "subprocess.",
            "shell=True",
            "sudo ",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
