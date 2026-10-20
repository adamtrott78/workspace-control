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
    def __init__(self, *, actor="adamtrott78"):
        self.actor = actor
        self.sha = "a" * 40
        self.docs = {
            controller.WORKFLOW_PATH: (
                (ROOT / controller.WORKFLOW_PATH).read_bytes(),
                "b" * 40,
            ),
            "architecture/lambda-ci-project-registry.v1.json": (
                (ROOT / "architecture/lambda-ci-project-registry.v1.json").read_bytes(),
                "c" * 40,
            ),
            "architecture/lambda-ci-project-research-engine.v2.json": (
                (ROOT / "architecture/lambda-ci-project-research-engine.v2.json").read_bytes(),
                "d" * 40,
            ),
            "architecture/lambda-ci-project-padataset.v1.json": (
                (ROOT / "architecture/lambda-ci-project-padataset.v1.json").read_bytes(),
                "e" * 40,
            ),
        }

    def get_json(self, path):
        if "/branches/main" in path:
            return {"commit": {"sha": self.sha}}
        if "/actions/workflows/" in path:
            return {
                "workflow_runs": [
                    {
                        "id": 123,
                        "status": "completed",
                        "conclusion": "success",
                        "head_branch": "main",
                        "head_sha": self.sha,
                        "event": "push",
                        "actor": {"login": self.actor},
                        "triggering_actor": {"login": self.actor},
                    }
                ]
            }
        raise AssertionError(path)

    def content_at(self, path, sha):
        assert sha == self.sha
        return self.docs[path]


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

    def test_current_successful_run_requires_allowed_actor_and_current_main(self):
        good = FakeGitHub()
        run = controller._select_current_successful_run(good, {"adamtrott78"})
        self.assertEqual(run["head_sha"], good.sha)

        bad = FakeGitHub(actor="other-user")
        self.assertIsNone(
            controller._select_current_successful_run(bad, {"adamtrott78"})
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
            fake.sha,
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
