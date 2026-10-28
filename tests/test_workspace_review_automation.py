#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workspace_review_automation.py"
spec = importlib.util.spec_from_file_location("review_auto", SCRIPT)
review_auto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_auto)


def comment(cid, body, who, edited=False):
    created = "2026-10-28T04:00:00Z"
    return {
        "id": cid,
        "body": body,
        "created_at": created,
        "updated_at": "2026-10-28T04:01:00Z" if edited else created,
        "user": {"login": who},
    }


class ProtocolTests(unittest.TestCase):
    def request(self, sensitivity="authority_sensitive", copilot=False):
        return review_auto.fields_for_request(
            "task-v1", 7, "1" * 40, "2" * 40, "3" * 40,
            "implementation", sensitivity, "4" * 64, copilot,
        )

    def disposition(self, req, cid=100, att="fresh_independent_session",
                    value="NO_BLOCKING_FINDING"):
        return review_auto.block(
            review_auto.DISP_START, review_auto.DISP_END, {
                "request_comment_id": str(cid),
                "request_digest": req["request_digest"],
                "task_id": req["task_id"],
                "pr_number": req["pr_number"],
                "head_sha": req["head_sha"],
                "review_kind": req["review_kind"],
                "sensitivity": req["sensitivity"],
                "reviewer_attestation": att,
                "disposition": value,
            }
        )

    def test_request_digest_round_trip(self):
        req = self.request()
        review_auto.validate_request(req)
        self.assertRegex(req["request_digest"], r"^[0-9a-f]{64}$")

    def test_authority_sensitive_cannot_request_copilot(self):
        with self.assertRaisesRegex(review_auto.ReviewError, "Copilot"):
            self.request(copilot=True)

    def test_duplicate_machine_blocks_fail(self):
        req = self.request()
        body = review_auto.block(review_auto.REQ_START, review_auto.REQ_END, req)
        with self.assertRaisesRegex(review_auto.ReviewError, "exactly one"):
            review_auto.exact_block(
                body + "\n" + body,
                review_auto.REQ_START, review_auto.REQ_END,
                review_auto.REQ_KEYS,
            )

    def test_authority_sensitive_requires_fresh_attestation(self):
        req = self.request()
        fields = review_auto.exact_block(
            self.disposition(req, att="copilot_approval"),
            review_auto.DISP_START, review_auto.DISP_END,
            review_auto.DISP_KEYS,
        )
        with self.assertRaisesRegex(review_auto.ReviewError, "fresh_independent"):
            review_auto.validate_disposition(fields, req, 100)

    def test_matching_unedited_distinct_reviewer(self):
        req = self.request()
        body = self.disposition(req)
        found = review_auto.matching_dispositions(
            [comment(101, body, "reviewer")],
            req, 100, "github-actions[bot]",
        )
        self.assertEqual(len(found), 1)

    def test_matching_edited_fails(self):
        req = self.request()
        with self.assertRaisesRegex(review_auto.ReviewError, "edited"):
            review_auto.matching_dispositions(
                [comment(101, self.disposition(req), "reviewer", True)],
                req, 100, "github-actions[bot]",
            )

    def test_same_request_and_reviewer_principal_fails(self):
        req = self.request()
        with self.assertRaisesRegex(review_auto.ReviewError, "equals request"):
            review_auto.matching_dispositions(
                [comment(101, self.disposition(req), "github-actions[bot]")],
                req, 100, "github-actions[bot]",
            )

    def test_marker_bearing_wrong_digest_fails_closed(self):
        req = self.request()
        body = self.disposition(req).replace(req["request_digest"], "f" * 64)
        with self.assertRaisesRegex(review_auto.ReviewError, "request_digest"):
            review_auto.matching_dispositions(
                [comment(101, body, "reviewer")],
                req, 100, "github-actions[bot]",
            )

    def test_copilot_requires_exact_head_approved(self):
        req = self.request("routine_code", True)
        good = [{
            "id": 9, "state": "APPROVED", "commit_id": req["head_sha"],
            "user": {"login": "copilot-pull-request-reviewer[bot]"},
        }]
        commented = [{
            "id": 9, "state": "COMMENTED", "commit_id": req["head_sha"],
            "user": {"login": "copilot-pull-request-reviewer[bot]"},
        }]
        self.assertEqual(
            review_auto.exact_copilot_approval(good, req)["id"], 9
        )
        self.assertIsNone(review_auto.exact_copilot_approval(commented, req))
        self.assertIsNone(
            review_auto.exact_copilot_approval(good, self.request())
        )


class BindingTests(unittest.TestCase):
    def run_git(self, cwd, *args):
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

    def test_bindings_include_exact_blobs_and_deleted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.run_git(root, "init")
            self.run_git(root, "config", "user.email", "t@example.com")
            self.run_git(root, "config", "user.name", "T")
            (root / "a").write_text("a\n")
            (root / "gone").write_text("x\n")
            self.run_git(root, "add", ".")
            self.run_git(root, "commit", "-m", "base")
            base = self.run_git(root, "rev-parse", "HEAD")
            (root / "a").write_text("b\n")
            (root / "gone").unlink()
            self.run_git(root, "add", "-A")
            self.run_git(root, "commit", "-m", "head")
            head = self.run_git(root, "rev-parse", "HEAD")
            old = Path.cwd()
            try:
                os.chdir(root)
                rows, bound = review_auto.changed_bindings(base, head)
            finally:
                os.chdir(old)
            values = {x["path"]: x["blob"] for x in rows}
            self.assertEqual(values["gone"], "DELETED")
            self.assertRegex(values["a"], r"^[0-9a-f]{40}$")
            self.assertRegex(bound, r"^[0-9a-f]{64}$")


class ConsumeTests(unittest.TestCase):
    def req(self):
        return review_auto.fields_for_request(
            "task-v1", 7, "1" * 40, "2" * 40, "3" * 40,
            "implementation", "authority_sensitive", "4" * 64, False,
        )

    def request_comment(self, req):
        return comment(
            100, review_auto.render_request(req, []),
            "github-actions[bot]",
        )

    def disp(self, req, cid=101):
        fields = {
            "request_comment_id": "100",
            "request_digest": req["request_digest"],
            "task_id": req["task_id"],
            "pr_number": req["pr_number"],
            "head_sha": req["head_sha"],
            "review_kind": req["review_kind"],
            "sensitivity": req["sensitivity"],
            "reviewer_attestation": "fresh_independent_session",
            "disposition": "NO_BLOCKING_FINDING",
        }
        return comment(
            cid,
            review_auto.block(
                review_auto.DISP_START, review_auto.DISP_END, fields
            ),
            "reviewer",
        )

    def args(self, **kw):
        data = dict(
            repo="owner/repo", pr_number=7, task_id="task-v1",
            request_comment_id=100, disposition_comment_id=None,
            token_env="TOKEN", trusted_requester=["github-actions[bot]"],
            post_receipt=False,
        )
        data.update(kw)
        return type("Args", (), data)()

    def common(self, req, comments):
        return (
            mock.patch.dict(os.environ, {"TOKEN": "x"}),
            mock.patch.object(
                review_auto, "get_comment",
                return_value=self.request_comment(req),
            ),
            mock.patch.object(
                review_auto, "get_pr",
                return_value={"head": {"sha": req["head_sha"]}},
            ),
            mock.patch.object(
                review_auto, "list_pages",
                return_value=comments,
            ),
        )

    def test_unique_exact_disposition_is_accepted(self):
        req = self.req()
        patches = self.common(req, [self.request_comment(req), self.disp(req)])
        with patches[0], patches[1], patches[2], patches[3]:
            with mock.patch("builtins.print") as out:
                self.assertEqual(review_auto.command_consume(self.args()), 0)
        self.assertEqual(json.loads(out.call_args.args[0])["status"], "ACCEPTED")

    def test_stale_head_fails_closed(self):
        req = self.req()
        with (
            mock.patch.dict(os.environ, {"TOKEN": "x"}),
            mock.patch.object(
                review_auto, "get_comment",
                return_value=self.request_comment(req),
            ),
            mock.patch.object(
                review_auto, "get_pr",
                return_value={"head": {"sha": "9" * 40}},
            ),
        ):
            with self.assertRaisesRegex(review_auto.ReviewError, "stale"):
                review_auto.command_consume(self.args())

    def test_duplicate_dispositions_fail_closed(self):
        req = self.req()
        patches = self.common(
            req,
            [self.request_comment(req), self.disp(req, 101), self.disp(req, 102)],
        )
        with patches[0], patches[1], patches[2], patches[3]:
            with self.assertRaisesRegex(review_auto.ReviewError, "ambiguous"):
                review_auto.command_consume(self.args())


class RepositoryContractTests(unittest.TestCase):
    def test_workflow_is_github_only(self):
        text = (
            ROOT / ".github" / "workflows"
            / "workspace-control-review-automation.yml"
        ).read_text()
        self.assertIn("issue_comment:", text)
        self.assertIn("WORKSPACE_CONTROL_REVIEW_DISPOSITION_V1", text)
        self.assertIn("github.event.comment.user.login != 'github-actions[bot]'", text)
        self.assertIn("--post-receipt", text)
        self.assertNotIn("systemctl", text)
        self.assertNotIn("/var/lib/workspace-ci", text)

    def test_architecture_forbids_authority_copilot_and_auto_merge(self):
        data = json.loads(
            (ROOT / "architecture" / "workspace-review-automation.v1.json")
            .read_text()
        )
        self.assertFalse(
            data["review_classes"]["authority_sensitive"]["copilot_may_satisfy"]
        )
        self.assertFalse(data["consumption"]["automatic_merge"])


if __name__ == "__main__":
    unittest.main()
