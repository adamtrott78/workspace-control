import contextlib
import importlib.util
import hashlib
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/lambda_ci_p1_install_legacy_state_root_equivalence_hotfix.py"


def load_module():
    spec = importlib.util.spec_from_file_location("legacy_state_root_hotfix", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class LegacyStateRootEquivalenceHotfixTests(unittest.TestCase):
    def rejected_marker(self, module):
        return {
            "approved_policy_sha": module.EXPECTED_POLICY_SHA,
            "commit_sha": module.EXPECTED_POLICY_SHA,
            "observed_main_sha": module.EXPECTED_POLICY_SHA,
            "policy_equivalent_to_observed_main": True,
            "request_id": module.EXPECTED_REQUEST_ID,
            "response": {
                "error": (
                    "derived controller transaction differs from reviewed "
                    "expected transaction: "
                    "workspace-ci-controller@padataset-cpu.service "
                    "workspace-ci-controller@padataset-gpu.service "
                    "workspace-ci-controller@research-engine-cpu.service "
                    "workspace-ci-controller@research-engine-gpu.service "
                    "workspace-ci-controller@workspace-control-cpu.service"
                ),
                "error_type": "ReconcileError",
                "schema_version": 1,
                "status": "REJECTED",
            },
            "status": "REJECTED",
            "timestamp_utc": "2026-10-28T01:07:54.830294+00:00",
            "workflow_run_id": module.EXPECTED_WORKFLOW_RUN_ID,
        }

    def test_exact_live_rejection_and_controller_binary_are_pinned(self):
        module = load_module()
        self.assertEqual(
            module.EXPECTED_POLICY_SHA,
            "e8a458a8ce922ac89ad91354b29f5dc4ecbd5e91",
        )
        self.assertEqual(
            module.EXPECTED_REQUEST_ID,
            "94e3e5ae-d1a7-541b-9185-7acb5c5b7103",
        )
        self.assertEqual(module.EXPECTED_WORKFLOW_RUN_ID, 40587498629)
        self.assertEqual(
            module.EXPECTED_CONTROLLER_BINARY_SHA256,
            "6acd290f2312f0908d17443a2f5ee8d31711fbdb3f0bf9318171e9edd0ddee12",
        )
        self.assertEqual(
            module.EXPECTED_ONE_SHOT["InvocationID"],
            "9659518ca16b4596a6936d72bd5e1e34",
        )
        self.assertEqual(module.EXPECTED_ONE_SHOT["ExecMainStatus"], "70")

    def review_comments(
        self,
        module,
        *,
        head,
        helper_blob,
        request_id=6459200001,
        approval_id=6459200002,
        edited=False,
    ):
        request_body = (
            "Fresh independent exact-head re-review request for durable task "
            + module.EXPECTED_REVIEW_TASK_ID
            + ".\n\nReview exact head: "
            + head
        )
        approval_body = "\n".join(
            [
                module.REVIEW_AUTHORITY_MARKER,
                f"task_id={module.EXPECTED_REVIEW_TASK_ID}",
                f"pr_number={module.EXPECTED_REVIEW_PR_NUMBER}",
                f"head_sha={head}",
                f"installer_blob={helper_blob}",
                (
                    "reconciler_blob="
                    + module.EXPECTED_REVIEWED_RECONCILER_GIT_BLOB
                ),
                (
                    "prior_blocking_comment_id="
                    + str(module.EXPECTED_PRIOR_BLOCKING_REVIEW_COMMENT_ID)
                ),
                f"review_request_comment_id={request_id}",
                "disposition=NO_BLOCKING_FINDING",
                module.REVIEW_AUTHORITY_END,
            ]
        )
        return [
            {
                "id": request_id,
                "body": request_body,
                "user": {"login": module.EXPECTED_REVIEW_OWNER},
                "author_association": "OWNER",
                "created_at": "2026-10-28T03:00:00Z",
                "updated_at": "2026-10-28T03:00:00Z",
            },
            {
                "id": approval_id,
                "body": approval_body,
                "user": {"login": module.EXPECTED_REVIEW_OWNER},
                "author_association": "OWNER",
                "created_at": "2026-10-28T03:01:00Z",
                "updated_at": (
                    "2026-10-28T03:02:00Z"
                    if edited
                    else "2026-10-28T03:01:00Z"
                ),
            },
        ]

    def attest_context(
        self,
        module,
        **kwargs,
    ):
        head = kwargs.pop("head", "reviewed-head")
        helper_blob = kwargs.pop(
            "head_helper_blob",
            "1111111111111111111111111111111111111111",
        )
        review_comments = kwargs.pop(
            "review_comments",
            self.review_comments(module, head=head, helper_blob=helper_blob),
        )
        reviewed_blob = kwargs.pop(
            "reviewed_blob",
            module.EXPECTED_REVIEWED_RECONCILER_GIT_BLOB,
        )
        head_reconciler_blob = kwargs.pop(
            "head_reconciler_blob",
            module.EXPECTED_REVIEWED_RECONCILER_GIT_BLOB,
        )
        symbolic_rc = kwargs.pop("symbolic_rc", 1)
        symbolic_stdout = kwargs.pop("symbolic_stdout", "")
        if kwargs:
            raise AssertionError(f"unused attest kwargs: {kwargs}")

        def fake_run(argv, check=True):
            if argv[-2:] == ["rev-parse", "--show-toplevel"]:
                return types.SimpleNamespace(
                    returncode=0,
                    stdout=str(ROOT) + "\n",
                    stderr="",
                )
            if argv[-2:] == ["rev-parse", "HEAD"]:
                return types.SimpleNamespace(
                    returncode=0,
                    stdout=head + "\n",
                    stderr="",
                )
            if "symbolic-ref" in argv:
                return types.SimpleNamespace(
                    returncode=symbolic_rc,
                    stdout=symbolic_stdout,
                    stderr="",
                )
            if "status" in argv:
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")
            if "ls-files" in argv:
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")
            if "cat-file" in argv:
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")
            if "rev-parse" in argv:
                spec = argv[-1]
                if spec.startswith(module.EXPECTED_REVIEWED_SOURCE_HEAD + ":"):
                    return types.SimpleNamespace(
                        returncode=0,
                        stdout=reviewed_blob + "\n",
                        stderr="",
                    )
                if spec == f"HEAD:{module.SOURCE_ROOT}":
                    return types.SimpleNamespace(
                        returncode=0,
                        stdout=head_reconciler_blob + "\n",
                        stderr="",
                    )
                if spec == f"HEAD:{module.EXPECTED_HELPER}":
                    return types.SimpleNamespace(
                        returncode=0,
                        stdout=helper_blob + "\n",
                        stderr="",
                    )
            raise AssertionError(f"unexpected git command: {argv!r}")

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(module, "run", side_effect=fake_run))
        stack.enter_context(
            mock.patch.object(
                module,
                "fetch_review_comments",
                return_value=review_comments,
            )
        )
        return stack

    def test_attest_source_rejects_different_clean_descendant_changing_only_installer(self):
        module = load_module()
        reviewed_head = "reviewed-head"
        reviewed_helper_blob = "1111111111111111111111111111111111111111"
        descendant_head = "different-clean-descendant"
        descendant_helper_blob = "2222222222222222222222222222222222222222"
        authority = self.review_comments(
            module,
            head=reviewed_head,
            helper_blob=reviewed_helper_blob,
        )
        with self.attest_context(
            module,
            head=descendant_head,
            head_helper_blob=descendant_helper_blob,
            review_comments=authority,
        ):
            with self.assertRaisesRegex(
                module.HotfixError,
                "external independent review authority missing",
            ):
                module.attest_source(descendant_head, "atrott")

    def test_attest_source_rejects_attached_branch(self):
        module = load_module()
        with self.attest_context(
            module,
            symbolic_rc=0,
            symbolic_stdout="refs/heads/p1-preserve-legacy-state-root-env\n",
        ):
            with self.assertRaisesRegex(module.HotfixError, "HEAD must be detached"):
                module.attest_source("reviewed-head", "atrott")

    def test_attest_source_rejects_reconciler_source_byte_drift(self):
        module = load_module()
        with self.attest_context(
            module,
            head_reconciler_blob="0000000000000000000000000000000000000000",
        ):
            with self.assertRaisesRegex(
                module.HotfixError,
                "reconciler source blob mismatch",
            ):
                module.attest_source("reviewed-head", "atrott")

    def test_attest_source_rejects_edited_review_authority(self):
        module = load_module()
        helper_blob = "1111111111111111111111111111111111111111"
        comments = self.review_comments(
            module,
            head="reviewed-head",
            helper_blob=helper_blob,
            edited=True,
        )
        with self.attest_context(
            module,
            head_helper_blob=helper_blob,
            review_comments=comments,
        ):
            with self.assertRaisesRegex(
                module.HotfixError,
                "review authority comment was edited",
            ):
                module.attest_source("reviewed-head", "atrott")

    def test_attest_source_accepts_exact_external_review_authority(self):
        module = load_module()
        helper_blob = "1111111111111111111111111111111111111111"
        with self.attest_context(
            module,
            head="reviewed-head",
            head_helper_blob=helper_blob,
        ):
            repo, authority = module.attest_source("reviewed-head", "atrott")
        self.assertEqual(repo, ROOT)
        self.assertEqual(authority["head_sha"], "reviewed-head")
        self.assertEqual(authority["installer_blob"], helper_blob)
        self.assertEqual(
            authority["reconciler_blob"],
            module.EXPECTED_REVIEWED_RECONCILER_GIT_BLOB,
        )

    def test_legacy_env_renderer_omits_only_explicit_default_state_root(self):
        module = load_module()
        manifest = {
            "repository": "adamtrott78/research-engine",
            "project_id": "research-engine",
            "derived_identity": {
                "lanes": {
                    "gpu": {
                        "runner_prefix": "lambda-research-engine-gpu-",
                        "scale_set_name": "lambda-research-engine-gpu",
                    }
                }
            },
        }
        raw = module.render_legacy_controller_env(manifest, "gpu").decode()
        self.assertNotIn("WORKSPACE_CI_CONTROLLER_STATE_ROOT=", raw)
        self.assertIn(
            "WORKSPACE_CI_ADMISSION_V2_ENABLED=YES\n",
            raw,
        )
        self.assertIn(
            "WORKSPACE_CI_PROJECT_ID=research-engine\n",
            raw,
        )
        self.assertIn(
            "WORKSPACE_CI_SCALESET_NAME=lambda-research-engine-gpu\n",
            raw,
        )

    def test_rejected_marker_validator_is_exact_and_fail_closed(self):
        module = load_module()
        value = self.rejected_marker(module)
        raw = (json.dumps(value, sort_keys=True) + "\n").encode()
        parsed = module.validate_rejected_marker(raw)
        self.assertEqual(parsed["request_id"], module.EXPECTED_REQUEST_ID)

        bad = dict(value)
        bad["request_id"] = "00000000-0000-4000-8000-000000000000"
        with self.assertRaisesRegex(module.HotfixError, "request ID mismatch"):
            module.validate_rejected_marker(
                (json.dumps(bad, sort_keys=True) + "\n").encode()
            )

    def _exercise_main(self, *, fail_after_root_replace=False):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            repo = root / "repo"
            (repo / "scripts").mkdir(parents=True)
            source_root = repo / module.SOURCE_ROOT
            source_root.write_bytes(b"NEW_ROOT\n")

            installed_root = root / "installed-root.py"
            installed_reconcile_controller = root / "reconcile-controller.py"
            installed_one_shot = root / "one-shot.service"
            installed_controller_binary = root / "lambda-ci-controller"
            state = root / "state"
            state.mkdir()
            last_rejected = state / "last-rejected.json"
            archived = state / "last-rejected.pre-hotfix.json"

            old_root = b"OLD_ROOT\n"
            reconcile_controller = b"RECONCILE_CONTROLLER\n"
            one_shot = b"ONE_SHOT\n"
            controller_binary = b"CONTROLLER_BINARY\n"
            installed_root.write_bytes(old_root)
            installed_reconcile_controller.write_bytes(reconcile_controller)
            installed_one_shot.write_bytes(one_shot)
            installed_controller_binary.write_bytes(controller_binary)
            rejected_raw = (
                json.dumps(self.rejected_marker(module), sort_keys=True) + "\n"
            ).encode()
            last_rejected.write_bytes(rejected_raw)

            snapshots = {
                module.ROOT_SERVICE: {
                    "LoadState": "loaded",
                    "ActiveState": "active",
                    "SubState": "running",
                    "UnitFileState": "enabled",
                    "NRestarts": "0",
                    "ExecMainStatus": "0",
                    "MainPID": "123",
                    "InvocationID": "root-generation",
                },
                module.AUTO_CONTROLLER: dict(module.EXPECTED_AUTO),
                module.ONE_SHOT: dict(module.EXPECTED_ONE_SHOT),
                module.WORKSPACE_CPU: dict(module.EXPECTED_WORKSPACE_CPU),
                **{
                    service: dict(value)
                    for service, value in module.EXPECTED_SIBLINGS.items()
                },
            }
            systemctl_calls = []

            def fake_run(argv, check=True):
                systemctl_calls.append(list(argv))
                return types.SimpleNamespace(
                    returncode=0,
                    stdout="",
                    stderr="",
                )

            real_atomic_write = module.atomic_write
            forward_failed = False

            def maybe_fault(path, raw, mode):
                nonlocal forward_failed
                real_atomic_write(path, raw, mode)
                if (
                    fail_after_root_replace
                    and path == installed_root
                    and raw == b"NEW_ROOT\n"
                    and not forward_failed
                ):
                    forward_failed = True
                    raise OSError("synthetic failure after root replace")

            with contextlib.ExitStack() as stack:
                for patcher in (
                    mock.patch.object(module, "INSTALLED_ROOT", installed_root),
                    mock.patch.object(
                        module,
                        "INSTALLED_RECONCILE_CONTROLLER",
                        installed_reconcile_controller,
                    ),
                    mock.patch.object(
                        module,
                        "INSTALLED_ONE_SHOT_UNIT",
                        installed_one_shot,
                    ),
                    mock.patch.object(
                        module,
                        "INSTALLED_CONTROLLER_BINARY",
                        installed_controller_binary,
                    ),
                    mock.patch.object(module, "LAST_REJECTED", last_rejected),
                    mock.patch.object(module, "ARCHIVED_REJECTED", archived),
                    mock.patch.object(
                        module,
                        "EXPECTED_OLD_ROOT_SHA256",
                        hashlib.sha256(old_root).hexdigest(),
                    ),
                    mock.patch.object(
                        module,
                        "EXPECTED_RECONCILE_CONTROLLER_SHA256",
                        hashlib.sha256(reconcile_controller).hexdigest(),
                    ),
                    mock.patch.object(
                        module,
                        "EXPECTED_ONE_SHOT_UNIT_SHA256",
                        hashlib.sha256(one_shot).hexdigest(),
                    ),
                    mock.patch.object(
                        module,
                        "EXPECTED_CONTROLLER_BINARY_SHA256",
                        hashlib.sha256(controller_binary).hexdigest(),
                    ),
                    mock.patch.object(
                        module,
                        "attest_source",
                        return_value=(
                            repo,
                            {
                                "comment_id": 6459200002,
                                "review_request_comment_id": 6459200001,
                                "created_at": "2026-10-28T03:01:00Z",
                                "body_sha256": "review-body",
                                "head_sha": "reviewed-head",
                                "installer_blob": "reviewed-installer-blob",
                                "reconciler_blob": (
                                    module.EXPECTED_REVIEWED_RECONCILER_GIT_BLOB
                                ),
                            },
                        ),
                    ),
                    mock.patch.object(
                        module,
                        "snapshot",
                        side_effect=lambda service: dict(snapshots[service]),
                    ),
                    mock.patch.object(
                        module,
                        "verify_exact_legacy_sibling_material",
                        return_value={"verified": {"env_sha256": "a", "dropin_sha256": "b"}},
                    ),
                    mock.patch.object(module, "run", side_effect=fake_run),
                    mock.patch.object(module, "wait_socket"),
                    mock.patch.object(
                        module,
                        "atomic_write",
                        side_effect=maybe_fault,
                    ),
                    mock.patch.object(module.os, "geteuid", return_value=0),
                    mock.patch.dict(
                        module.os.environ,
                        {"SUDO_USER": "atrott"},
                    ),
                    mock.patch.object(module.pwd, "getpwnam"),
                    mock.patch.object(module.os, "chown"),
                    mock.patch.object(
                        sys,
                        "argv",
                        ["hotfix", "--expected-head", "reviewed-head"],
                    ),
                ):
                    stack.enter_context(patcher)

                if fail_after_root_replace:
                    with self.assertRaisesRegex(
                        module.HotfixError,
                        "rollback completed",
                    ):
                        module.main()
                else:
                    self.assertEqual(module.main(), 0)

            return {
                "old_root": old_root,
                "source_root": source_root.read_bytes(),
                "installed_root": installed_root.read_bytes(),
                "last_rejected_exists": last_rejected.exists(),
                "last_rejected": (
                    last_rejected.read_bytes()
                    if last_rejected.exists()
                    else None
                ),
                "archive_exists": archived.exists(),
                "archive": archived.read_bytes() if archived.exists() else None,
                "rejected_raw": rejected_raw,
                "calls": systemctl_calls,
            }

    def test_success_installs_only_root_and_archives_exact_rejected_marker(self):
        result = self._exercise_main()
        self.assertEqual(result["installed_root"], result["source_root"])
        self.assertFalse(result["last_rejected_exists"])
        self.assertTrue(result["archive_exists"])
        self.assertEqual(result["archive"], result["rejected_raw"])
        self.assertIn(
            [
                "systemctl",
                "--job-mode=ignore-dependencies",
                "restart",
                "workspace-ci-reconciler.service",
            ],
            result["calls"],
        )
        self.assertFalse(
            any(
                call[-1:] in [
                    ["workspace-ci-reconcile-controller.service"],
                    ["workspace-ci-reconcile-controller-once.service"],
                    ["workspace-ci-controller@workspace-control-cpu.service"],
                ]
                and ("start" in call or "restart" in call)
                for call in result["calls"]
            )
        )

    def test_failure_after_root_replace_restores_root_and_rejected_marker(self):
        result = self._exercise_main(fail_after_root_replace=True)
        self.assertEqual(result["installed_root"], result["old_root"])
        self.assertTrue(result["last_rejected_exists"])
        self.assertEqual(result["last_rejected"], result["rejected_raw"])
        self.assertFalse(result["archive_exists"])


if __name__ == "__main__":
    unittest.main()
