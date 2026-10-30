import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compiler = load(
    "lambda_ci_policy_compiler_v3_reconciler_tests",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
reconciler = load(
    "lambda_ci_v3_reconciler",
    ROOT / "scripts" / "lambda_ci_v3_reconciler.py",
)
provider = load(
    "lambda_ci_v3_provisioner_for_reconciler_tests",
    ROOT / "scripts" / "lambda_ci_v3_provisioner.py",
)


class V3ReconcilerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stage = pathlib.Path(self.temp.name) / "stage"
        self.result = reconciler.build_stage(
            ROOT,
            self.stage,
            controller_binary=b"synthetic-v3-controller",
            source_head="f" * 40,
        )

    def staged(self, absolute):
        return self.stage / pathlib.Path(absolute).relative_to("/")

    def test_all_nine_class_identities_and_projection_files_are_generated(self):
        compiled = self.result["compiled"]
        classes = compiled["root_projection"]["runner_classes"]
        self.assertEqual(len(classes), 9)
        users = {
            policy["controller_peer"]["unix_user"]
            for policy in classes.values()
        }
        self.assertEqual(len(users), 9)

        sysusers = self.staged("/etc/sysusers.d/workspace-ci-v3.conf").read_text()
        for class_id, policy in classes.items():
            user = policy["controller_peer"]["unix_user"]
            self.assertIn(f"u {user} -", sysusers)
            self.assertIn(f"m {user} workspace-ci-v3-provisioner", sysusers)
            self.assertTrue(
                self.staged(
                    f"/etc/workspace-ci/v3/controllers/{class_id}.json"
                ).is_file()
            )
            dropin = self.staged(
                f"/etc/systemd/system/workspace-ci-v3-controller@{class_id}.service.d/identity.conf"
            ).read_text()
            self.assertIn(f"User={user}", dropin)
            self.assertIn("SupplementaryGroups=workspace-ci-v3-provisioner", dropin)

    def test_offline_payload_broker_identity_is_installed_without_credential_groups(self):
        compiled = self.result["compiled"]
        classes = compiled["root_projection"]["runner_classes"]
        identities = {
            policy["payload_broker_identity"]["user"]:
                policy["payload_broker_identity"]["group"]
            for policy in classes.values()
            if policy["payload_broker_identity"] is not None
        }
        self.assertEqual(len(identities), 2)
        self.assertEqual(set(identities.values()), {"ci-research-engine"})
        sysusers = self.staged("/etc/sysusers.d/workspace-ci-v3.conf").read_text()
        for broker_user in identities:
            self.assertTrue(broker_user.startswith("ci-payload-"))
            self.assertIn(f"u {broker_user} -", sysusers)
            self.assertIn(
                f"m {broker_user} ci-research-engine",
                sysusers,
            )
            self.assertNotIn(
                f"m {broker_user} workspace-ci-v3-provisioner",
                sysusers,
            )
            for group in self.result["migration"]["controller_identity"][
                "project_credential_groups"
            ].values():
                self.assertNotIn(f"m {broker_user} {group}", sysusers)

    def test_project_credential_groups_are_exact_and_repository_scoped(self):
        migration = self.result["migration"]
        expected = migration["controller_identity"]["project_credential_groups"]
        sysusers = self.staged("/etc/sysusers.d/workspace-ci-v3.conf").read_text()
        tmpfiles = self.staged("/etc/tmpfiles.d/workspace-ci-v3.conf").read_text()
        for project, group in expected.items():
            self.assertIn(f"g {group} -", sysusers)
            self.assertIn(
                f"/var/lib/workspace-ci/v3/credentials/{project} 0750 root {group}",
                tmpfiles,
            )

    def test_private_migration_state_roots_are_staged_by_inactive_substrate(self):
        tmpfiles = self.staged("/etc/tmpfiles.d/workspace-ci-v3.conf").read_text()
        self.assertIn(
            "d /var/lib/workspace-ci/v3/migration 0700 root root -",
            tmpfiles,
        )
        self.assertIn(
            "d /var/lib/workspace-ci/v3/migration-authority 0700 root root -",
            tmpfiles,
        )

    def test_payload_socket_root_is_staged_outside_control_plane_runtime(self):
        tmpfiles = self.staged("/etc/tmpfiles.d/workspace-ci-v3.conf").read_text()
        self.assertIn(
            "d /run/workspace-ci-v3-payload 0711 root root -",
            tmpfiles,
        )
        self.assertNotIn("/run/workspace-ci/v3/payload", tmpfiles)

    def test_migration_plan_binds_current_repository_readiness_without_live_authority(self):
        migration = self.result["migration"]
        self.assertEqual(
            migration["side_by_side_paths"]["payload_socket_root"],
            "/run/workspace-ci-v3-payload",
        )
        readiness = migration["repository_readiness"]
        self.assertEqual(
            readiness["workspace_control_repository_boundary"]["exact_head"],
            "01019177fcb46e5ab9864ea9b764b533dcf0be81",
        )
        producer = readiness["research_engine_offline_producer"]
        self.assertEqual(
            producer["exact_head"],
            "6165556086b73d2076f205f11ec7b988150f23dd",
        )
        self.assertEqual(producer["hosted_ci_run_number"], 642)
        self.assertEqual(producer["hosted_ci_run_id"], 41007835081)
        self.assertTrue(producer["repository_steps_executed"])
        self.assertFalse(producer["default_branch_cutover_authorized"])
        self.assertFalse(readiness["live_activation_authorized"])
        self.assertEqual(migration["live_authority"], "NONE")

    def test_install_overlay_changes_only_install_generation(self):
        before = json.loads(
            (ROOT / "architecture/lambda-ci-deployment-overlay.v1.json").read_text()
        )
        after = self.result["overlay"]
        self.assertEqual(after["routes"], before["routes"])
        self.assertEqual(after["legacy"], before["legacy"])
        for class_id, prior in before["classes"].items():
            current = after["classes"][class_id]
            self.assertEqual(current["install_state"], "INSTALLED")
            self.assertEqual(
                current["controller_state"],
                prior["controller_state"],
            )
            self.assertEqual(current["containment"], prior["containment"])
        self.assertTrue(
            all(route["admission_state"] == "DISABLED"
                for route in after["routes"].values())
        )

    def test_managed_destinations_are_v3_disjoint(self):
        allowed = (
            "/etc/workspace-ci/v3/",
            "/opt/workspace-ci/v3/",
            "/etc/systemd/system/workspace-ci-v3-",
            "/etc/sysusers.d/workspace-ci-v3.conf",
            "/etc/tmpfiles.d/workspace-ci-v3.conf",
        )
        for entry in self.result["manifest"]["entries"]:
            destination = entry["destination"]
            self.assertTrue(
                any(destination.startswith(prefix) for prefix in allowed),
                destination,
            )
            self.assertNotIn("/var/lib/workspace-ci/controller", destination)
            self.assertNotIn("/run/workspace-ci/provisioner.sock", destination)

    def test_runtime_probe_bindings_are_v3_without_mutating_v2_module(self):
        import lambda_ci_runtime as v2_runtime

        self.assertTrue(
            str(provider.runtime.TRUSTED_CUDA_OOM_PROBE_PATH).startswith(
                "/opt/workspace-ci/v3/"
            )
        )
        self.assertTrue(
            str(provider.runtime.TRUSTED_CACHE_MANAGER_PATH).startswith(
                "/opt/workspace-ci/v3/"
            )
        )
        self.assertTrue(
            str(v2_runtime.TRUSTED_CUDA_OOM_PROBE_PATH).startswith(
                "/opt/workspace-ci/provisioner/"
            )
        )
        self.assertTrue(
            str(v2_runtime.TRUSTED_CACHE_MANAGER_PATH).startswith(
                "/opt/workspace-ci/cache-manager/"
            )
        )

    def test_controller_template_fails_closed_without_generated_identity_dropin(self):
        unit = self.staged(
            "/etc/systemd/system/workspace-ci-v3-controller@.service"
        ).read_text()
        self.assertIn("User=workspace-ci-v3-invalid", unit)
        self.assertIn("Group=workspace-ci-v3-invalid", unit)
        self.assertNotIn("User=root", unit)

    def test_inactive_installer_contains_no_activation_commands(self):
        source = (ROOT / "scripts/lambda_ci_v3_reconciler.py").read_text()
        for forbidden in (
            '["systemctl", "start"',
            '["systemctl", "restart"',
            '["systemctl", "enable"',
            "systemctl start ",
            "systemctl restart ",
            "systemctl enable ",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn('["systemctl", "daemon-reload"]', source)

    def test_root_activation_helper_is_installed_immutable_in_reconciler_tree(self):
        helper = self.staged(
            "/opt/workspace-ci/v3/reconciler/lambda_ci_v3_root_activation.py"
        )
        self.assertTrue(helper.is_file())
        self.assertEqual(helper.stat().st_mode & 0o777, 0o555)

    def test_offline_payload_helpers_are_installed_immutable_in_v3_tree(self):
        broker = self.staged(
            "/opt/workspace-ci/v3/payload/lambda_ci_v3_payload_broker.py"
        )
        client = self.staged(
            "/opt/workspace-ci/v3/payload/lambda_ci_v3_payload_exec.py"
        )
        self.assertTrue(broker.is_file())
        self.assertTrue(client.is_file())
        self.assertEqual(broker.stat().st_mode & 0o777, 0o555)
        self.assertEqual(client.stat().st_mode & 0o777, 0o555)

    def test_manifest_is_digest_bound_and_verifiable_in_staging_projection(self):
        manifest = self.result["manifest"]
        self.assertEqual(manifest["runner_class_count"], 9)
        self.assertEqual(manifest["controller_state"], "INACTIVE")
        self.assertEqual(manifest["route_state"], "DISABLED")
        self.assertEqual(manifest["source_head"], "f" * 40)
        self.assertGreater(len(manifest["entries"]), 30)


if __name__ == "__main__":
    unittest.main()
