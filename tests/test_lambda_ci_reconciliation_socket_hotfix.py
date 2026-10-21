import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "architecture" / "lambda-ci-reconciliation-socket-hotfix.v1.json").read_text()
)


def git_blob_sha(data: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {len(data)}\0".encode())
    digest.update(data)
    return digest.hexdigest()


class ReconciliationSocketHotfixTests(unittest.TestCase):
    def test_manifest_binds_exact_repair_sources(self):
        self.assertEqual(MANIFEST["status"], "VALIDATED_HOTFIX_INPUT")
        for item in MANIFEST["source_blobs"]:
            path = ROOT / item["path"]
            self.assertEqual(item["git_blob_sha"], git_blob_sha(path.read_bytes()), item["path"])

    def test_hotfix_shell_parses(self):
        path = ROOT / "scripts" / "lambda_ci_reconciliation_socket_hotfix_v1.sh"
        result = subprocess.run(
            ["bash", "-n", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_parent_is_search_only_and_socket_groups_remain_distinct(self):
        provisioner = (ROOT / "scripts" / "lambda_ci_provisioner_service.py").read_text()
        reconciler = (ROOT / "scripts" / "lambda_ci_reconciler.py").read_text()
        migration = (ROOT / "scripts" / "migrate_lambda_ci_multirepo_v1.sh").read_text()
        helper = (ROOT / "scripts" / "lambda_ci_reconciliation_socket_hotfix_v1.sh").read_text()

        for source in (provisioner, reconciler):
            self.assertIn("os.chmod(socket_path.parent, 0o711)", source)
            self.assertIn("os.chown(socket_path.parent, 0, 0)", source)

        self.assertIn(
            "install -d -o root -g root -m 0711 /run/workspace-ci",
            migration,
        )
        self.assertIn("RECONCILER_CAN_WRITE_PROVISIONER_SOCKET", helper)
        self.assertIn("CONTROLLER_CAN_WRITE_RECONCILER_SOCKET", helper)
        self.assertNotIn(
            "systemctl restart workspace-ci-provisioner.service",
            helper,
        )
        self.assertNotIn(
            "systemctl restart workspace-ci-controller@research-engine",
            helper,
        )

    def test_root_activation_git_preflights_cannot_rewrite_operator_index(self):
        for name in (
            "scripts/activate_lambda_ci_reconcile_controller.sh",
            "scripts/hotfix_lambda_ci_reconcile_controller_race.sh",
            "scripts/lambda_ci_reconciliation_socket_hotfix_v1.sh",
        ):
            source = (ROOT / name).read_text()
            self.assertIn('runuser -u "$SUDO_USER"', source, name)
            self.assertIn("GIT_OPTIONAL_LOCKS=0", source, name)
            self.assertIn("WORKSPACE_CONTROL_STATUS_FAILED", source, name)


if __name__ == "__main__":
    unittest.main()
