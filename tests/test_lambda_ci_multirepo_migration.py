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
        frozen_run3_policy = {
            "controller/lambda-ci-controller/main.go":
                "a1f05f3c69a8168fb6cbeeb981ed7d28299d9324",
            "scripts/lambda_ci_runtime.py":
                "89cdc45f7f96129a315e0c00253d547a23fb17fb",
            "scripts/lambda_ci_reconciler.py":
                "e58d0ccd3e11df99dc22b9069d16b1a03c4d3a2d",
            "systemd/workspace-ci-reconciler.service":
                "a81b758dd2f735fbe72085e3ae3c7529e10152a1",
            "systemd/workspace-ci-tmpfiles.conf":
                "eb6ddec43bdeead39c7af91f052c3f1a2602ebf2",
            "architecture/lambda-ci-project-registry.v1.json":
                "762805a1d33bbd7e666377b13680116d1051b4ab",
            "architecture/lambda-ci-execution-contracts.v1.json":
                "9eeb0ef9223821f1768350e24891eeb3bc72a940",
            "architecture/lambda-ci-reconciliation-ceiling.v1.json":
                "b22be2d12de0a1ea948c1224c20f27396ca0f4c8",
            "architecture/lambda-ci-project-padataset.v1.json":
                "63ba5e54e0489426efda3a05259792f22c95f85f",
            "architecture/lambda-ci-systemd-profiles.v1.json":
                "976a715efc5a3ef3c07bceeff39f5e751316e5c0",
            "architecture/lambda-ci-workload-policy.v1.json":
                "71bd0bb9c63436964462b1f9b889686ac328ee1d",
            ".github/workflows/lambda-ci-project-reconcile.yml":
                "c8b8baef1955ad2a8bd409756298f0703b85f270",
        }
        seen = set()
        for item in INSTALL["source_blobs"]:
            path = item["path"]
            self.assertNotIn(path, seen)
            seen.add(path)
            if path in frozen_run3_policy:
                self.assertEqual(
                    item["git_blob_sha"],
                    frozen_run3_policy[path],
                    path,
                )
                self.assertNotEqual(
                    item["git_blob_sha"],
                    git_blob_sha((ROOT / path).read_bytes()),
                    f"{path} is frozen historical Run-3 input and must not be silently rewritten",
                )
            else:
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
            "scripts/lambda_ci_run3_boot_recovery_hotfix_v1.sh",
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

    def test_run3_boot_runtime_directory_is_persistent_and_services_enableable(self):
        tmpfiles = (ROOT / "systemd" / "workspace-ci-tmpfiles.conf").read_text()
        self.assertIn("d /run/workspace-ci 0711 root root - -", tmpfiles)

        provisioner = (
            ROOT / "templates/lambda-ci/workspace-ci-provisioner-multirepo.service.in"
        ).read_text()
        controller = (
            ROOT / "templates/lambda-ci/workspace-ci-controller@.service.in"
        ).read_text()
        for unit in (provisioner, controller):
            self.assertIn("[Install]", unit)
            self.assertIn("WantedBy=multi-user.target", unit)

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
