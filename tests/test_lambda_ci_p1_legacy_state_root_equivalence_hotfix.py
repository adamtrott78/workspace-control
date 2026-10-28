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
                        return_value=repo,
                    ),
                    mock.patch.object(
                        module,
                        "snapshot",
                        side_effect=lambda service: dict(snapshots[service]),
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
