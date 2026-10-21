import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = json.loads(
    (ROOT / "architecture/lambda-ci-multirepo-install.v1.json").read_text()
)


def git_blob_sha(data: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {len(data)}\0".encode())
    digest.update(data)
    return digest.hexdigest()


class MultiRepoRun3MigrationTests(unittest.TestCase):
    def test_install_manifest_binds_exact_source_blobs(self):
        self.assertEqual(INSTALL["status"], "RUN3_VALIDATED_INSTALL_INPUT")
        self.assertFalse(INSTALL["padataset_activation_allowed"])
        seen = set()
        for item in INSTALL["source_blobs"]:
            path = item["path"]
            self.assertNotIn(path, seen)
            seen.add(path)
            self.assertEqual(
                item["git_blob_sha"],
                git_blob_sha((ROOT / path).read_bytes()),
                path,
            )
        self.assertEqual(
            INSTALL["live_transition"]["required_regression_routes"],
            ["cpu-test", "gpu-small", "model-eval-single-gpu"],
        )

    def test_run3_shell_artifacts_parse(self):
        for name in (
            "scripts/migrate_lambda_ci_multirepo_v1.sh",
            "scripts/activate_lambda_ci_reconcile_controller.sh",
            "scripts/hotfix_lambda_ci_reconcile_controller_race.sh",
            "scripts/lambda_ci_reconciliation_socket_hotfix_v1.sh",
            "scripts/stage_lambda_ci_reconciler_pat.sh",
        ):
            result = subprocess.run(
                ["bash", "-n", str(ROOT / name)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"{name}: {result.stderr}")

    def test_shared_runtime_socket_parent_is_cross_group_traversable(self):
        migration = (ROOT / "scripts" / "migrate_lambda_ci_multirepo_v1.sh").read_text()
        self.assertIn(
            "install -d -o root -g root -m 0711 /run/workspace-ci",
            migration,
        )
        self.assertIn("SOCKET_PARENT_OWNER_DRIFT", migration)
        self.assertIn("SOCKET_PARENT_MODE_DRIFT", migration)
        self.assertIn("RECONCILER_SOCKET_PARENT_NOT_TRAVERSABLE", migration)

    def test_root_reconciler_is_network_closed(self):
        unit = (ROOT / "systemd/workspace-ci-reconciler.service").read_text()
        self.assertIn("RestrictAddressFamilies=AF_UNIX AF_NETLINK", unit)
        self.assertNotIn("AF_INET6", unit)

    def test_generic_provisioner_uses_registry_mode(self):
        unit = (
            ROOT / "templates/lambda-ci/workspace-ci-provisioner-multirepo.service.in"
        ).read_text()
        self.assertIn("lambda-ci-project-registry.v1.json", unit)
        self.assertIn("--manifest-dir /etc/workspace-ci/projects", unit)


if __name__ == "__main__":
    unittest.main()
