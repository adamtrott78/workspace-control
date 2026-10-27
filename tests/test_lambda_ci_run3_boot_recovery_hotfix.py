import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "architecture" / "lambda-ci-run3-boot-recovery-hotfix.v1.json").read_text()
)


def git_blob_sha(data: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {len(data)}\0".encode())
    digest.update(data)
    return digest.hexdigest()


class Run3BootRecoveryHotfixTests(unittest.TestCase):
    def test_manifest_binds_exact_recovery_sources(self):
        self.assertEqual(MANIFEST["status"], "VALIDATED_HOTFIX_INPUT")
        evolved_after_recovery = {
            "scripts/lambda_ci_reconciler.py":
                "e58d0ccd3e11df99dc22b9069d16b1a03c4d3a2d",
            "systemd/workspace-ci-reconciler.service":
                "a81b758dd2f735fbe72085e3ae3c7529e10152a1",
            "systemd/workspace-ci-tmpfiles.conf":
                "eb6ddec43bdeead39c7af91f052c3f1a2602ebf2",
        }
        for item in MANIFEST["source_blobs"]:
            path = ROOT / item["path"]
            current = git_blob_sha(path.read_bytes())
            if item["path"] in evolved_after_recovery:
                self.assertEqual(
                    item["git_blob_sha"],
                    evolved_after_recovery[item["path"]],
                    item["path"],
                )
                self.assertNotEqual(
                    item["git_blob_sha"],
                    current,
                    f"{item['path']} is historical recovery input and now intentionally evolved",
                )
            else:
                self.assertEqual(
                    item["git_blob_sha"],
                    current,
                    item["path"],
                )

    def test_tmpfiles_contract_recreates_shared_runtime_parent(self):
        value = (ROOT / "systemd" / "workspace-ci-tmpfiles.conf").read_text()
        self.assertIn("d /run/workspace-ci 0711 root root - -", value)

    def test_generic_services_have_real_boot_install_contracts(self):
        provisioner = (
            ROOT / "templates" / "lambda-ci" / "workspace-ci-provisioner-multirepo.service.in"
        ).read_text()
        controller = (
            ROOT / "templates" / "lambda-ci" / "workspace-ci-controller@.service.in"
        ).read_text()
        reconciler = (ROOT / "systemd" / "workspace-ci-reconciler.service").read_text()

        for unit in (provisioner, controller, reconciler):
            self.assertIn("[Install]", unit)
            self.assertIn("WantedBy=multi-user.target", unit)

        self.assertIn("After=local-fs.target systemd-tmpfiles-setup.service", provisioner)
        self.assertIn("After=local-fs.target systemd-tmpfiles-setup.service", reconciler)

    def test_recovery_helper_parses_and_stays_bounded(self):
        path = ROOT / "scripts" / "lambda_ci_run3_boot_recovery_hotfix_v1.sh"
        result = subprocess.run(
            ["bash", "-n", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        source = path.read_text()
        self.assertIn("systemd-tmpfiles --create", source)
        self.assertIn("SERVICE_NOT_BOOT_ENABLED", source)
        self.assertIn("RUN3_BOOT_SOCKET_ISOLATION=PASS", source)
        self.assertIn("RUN3_BOOT_RECOVERY=PASS", source)
        self.assertIn("RUN3_RECONCILIATION_PLANE=PASS", source)
        self.assertIn("RECONCILER_CAN_WRITE_PROVISIONER_SOCKET", source)
        self.assertIn("CONTROLLER_CAN_WRITE_RECONCILER_SOCKET", source)
        self.assertIn("GIT_OPTIONAL_LOCKS=0", source)
        self.assertIn('runuser -u "$SUDO_USER"', source)
        self.assertIn(
            '"$REPO_ROOT/scripts/lambda_ci_reconcile_controller.py"',
            source,
        )
        self.assertIn("INSTALLED_RECONCILE_CONTROLLER_BLOB_DRIFT", source)
        self.assertIn("seq 1 150", source)

        for forbidden in (
            "registry_epoch",
            "groupmod",
            "usermod",
            "useradd ci-padataset",
            "groupadd ci-padataset",
            "mkdir /srv/workspace-ci/padataset",
        ):
            self.assertNotIn(forbidden, source)

    def test_recovery_uses_only_accepted_predecessor_blobs(self):
        predecessors = MANIFEST["accepted_predecessor_blobs"]
        poller_predecessors = predecessors[
            "/opt/workspace-ci/reconcile-controller/lambda_ci_reconcile_controller.py"
        ]
        self.assertIn(
            "8469569ea0864e24d1c219fc3fea438367a8efc8",
            poller_predecessors,
        )
        self.assertIn(
            "1229a29c40a08a100dcdda2a4e276e616b27d219",
            poller_predecessors,
        )
        self.assertIn(
            "85a341527fa951ac6a88a4e8e15141d54f728f5a",
            predecessors[
                "/opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py"
            ],
        )
        self.assertIn(
            "0d189505d7ddb42522e261dff9f2c1e5193fa882",
            predecessors["/opt/workspace-ci/reconciler/lambda_ci_reconciler.py"],
        )

    def test_migration_installs_and_validates_boot_contract(self):
        source = (ROOT / "scripts" / "migrate_lambda_ci_multirepo_v1.sh").read_text()
        self.assertIn(
            'install -o root -g root -m 0644 "$REPO_ROOT/systemd/workspace-ci-tmpfiles.conf" /etc/tmpfiles.d/workspace-ci.conf',
            source,
        )
        self.assertIn(
            "systemd-tmpfiles --create /etc/tmpfiles.d/workspace-ci.conf",
            source,
        )
        self.assertIn("POSTMIGRATION_SERVICE_NOT_ENABLED", source)
        self.assertIn('runuser -u "$SUDO_USER"', source)
        self.assertIn("GIT_OPTIONAL_LOCKS=0", source)


if __name__ == "__main__":
    unittest.main()
