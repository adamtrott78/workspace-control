import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROVISIONER_UNIT = (ROOT / "systemd" / "workspace-ci-provisioner.service").read_text()
CONTROLLER_UNIT = (ROOT / "systemd" / "workspace-ci-controller.service").read_text()
GPU_CONTROLLER_UNIT = (ROOT / "systemd" / "workspace-ci-controller-gpu.service").read_text()
BOOTSTRAP = (ROOT / "scripts" / "bootstrap_lambda_ci_p5.sh").read_text()
GO_BOOTSTRAP = (ROOT / "scripts" / "bootstrap_lambda_ci_go_toolchain.sh").read_text()
PINS = json.loads((ROOT / "architecture" / "lambda-ci-upstream-pins.v1.json").read_text())
STAGE = (ROOT / "scripts" / "stage_lambda_ci_controller_pat.sh").read_text()
KILL = (ROOT / "scripts" / "lambda_ci_kill_switch.sh").read_text()
REMOVE = (ROOT / "scripts" / "remove_lambda_ci.sh").read_text()


class LambdaCIP5InstallTests(unittest.TestCase):
    def test_shell_artifacts_parse(self):
        for rel in (
            "scripts/bootstrap_lambda_ci_p5.sh",
            "scripts/bootstrap_lambda_ci_go_toolchain.sh",
            "scripts/stage_lambda_ci_controller_pat.sh",
            "scripts/lambda_ci_kill_switch.sh",
            "scripts/remove_lambda_ci.sh",
        ):
            proc = subprocess.run(
                ["bash", "-n", str(ROOT / rel)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, f"{rel}: {proc.stderr}")

    def test_provisioner_unit_has_no_github_credential_or_external_network(self):
        self.assertIn("User=root", PROVISIONER_UNIT)
        self.assertIn("Group=root", PROVISIONER_UNIT)
        self.assertIn("RestrictAddressFamilies=AF_UNIX AF_NETLINK", PROVISIONER_UNIT)
        self.assertIn("DevicePolicy=closed", PROVISIONER_UNIT)
        self.assertIn("PrivateDevices=no", PROVISIONER_UNIT)
        for allowed in (
            "DeviceAllow=/dev/nvidiactl rw",
            "DeviceAllow=/dev/nvidia0 rw",
            "DeviceAllow=/dev/nvidia1 rw",
        ):
            self.assertIn(allowed, PROVISIONER_UNIT)
        for forbidden_device in (
            "DeviceAllow=/dev/nvidia-uvm rw",
            "DeviceAllow=/dev/nvidia-uvm-tools rw",
            "DeviceAllow=/dev/nvidia-modeset rw",
        ):
            self.assertNotIn(forbidden_device, PROVISIONER_UNIT)
        self.assertIn(
            "CapabilityBoundingSet=CAP_CHOWN CAP_DAC_OVERRIDE CAP_FOWNER CAP_SETUID CAP_SETGID",
            PROVISIONER_UNIT,
        )
        for forbidden in (
            "WORKSPACE_CI_PAT_FILE",
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "AF_INET ",
            "AF_INET6",
            "AF_PACKET",
            "curl ",
        ):
            self.assertNotIn(forbidden, PROVISIONER_UNIT)

    def test_controller_unit_is_unprivileged_and_local_network_denied(self):
        self.assertIn("User=ci-controller", CONTROLLER_UNIT)
        self.assertIn("Group=workspace-ci-controller", CONTROLLER_UNIT)
        self.assertIn("Requires=workspace-ci-provisioner.service", CONTROLLER_UNIT)
        self.assertIn(
            "Environment=WORKSPACE_CI_PAT_FILE=/var/lib/workspace-ci/controller/github-token",
            CONTROLLER_UNIT,
        )
        self.assertIn("RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6", CONTROLLER_UNIT)
        for deny in (
            "IPAddressDeny=127.0.0.0/8",
            "IPAddressDeny=10.0.0.0/8",
            "IPAddressDeny=172.16.0.0/12",
            "IPAddressDeny=192.168.0.0/16",
            "IPAddressDeny=100.64.0.0/10",
        ):
            self.assertIn(deny, CONTROLLER_UNIT)
        self.assertNotIn("User=root", CONTROLLER_UNIT)
        self.assertNotIn("sudo", CONTROLLER_UNIT)
        self.assertIn("Environment=WORKSPACE_CI_ADMISSION_V2_ENABLED=YES", CONTROLLER_UNIT)

    def test_gpu_controller_unit_is_unprivileged_and_fixed_to_gpu_small(self):
        self.assertIn("User=ci-controller", GPU_CONTROLLER_UNIT)
        self.assertIn("Group=workspace-ci-controller", GPU_CONTROLLER_UNIT)
        self.assertIn("Requires=workspace-ci-provisioner.service", GPU_CONTROLLER_UNIT)
        self.assertIn(
            "Environment=WORKSPACE_CI_SCALESET_NAME=lambda-research-engine-gpu",
            GPU_CONTROLLER_UNIT,
        )
        self.assertIn("Environment=WORKSPACE_CI_PROFILE=gpu-small", GPU_CONTROLLER_UNIT)
        self.assertIn(
            "Environment=WORKSPACE_CI_PAT_FILE=/var/lib/workspace-ci/controller/github-token",
            GPU_CONTROLLER_UNIT,
        )
        self.assertIn("RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6", GPU_CONTROLLER_UNIT)
        self.assertIn("DevicePolicy=closed", GPU_CONTROLLER_UNIT)
        self.assertNotIn("User=root", GPU_CONTROLLER_UNIT)
        self.assertIn("Environment=WORKSPACE_CI_ADMISSION_V2_ENABLED=YES", GPU_CONTROLLER_UNIT)

    def test_bootstrap_never_reads_or_accepts_token_material(self):
        self.assertIn("github_credential_handled_by_bootstrap", BOOTSTRAP)
        self.assertIn('"github_credential_handled_by_bootstrap": False', BOOTSTRAP)
        self.assertNotIn("read -r -s TOKEN", BOOTSTRAP)
        self.assertNotIn("WORKSPACE_CI_GITHUB_TOKEN", BOOTSTRAP)
        self.assertNotIn("GH_TOKEN=", BOOTSTRAP)
        self.assertNotIn("GITHUB_TOKEN=", BOOTSTRAP)
        self.assertIn("CONTROLLER_CREDENTIAL_NOT_READY", BOOTSTRAP)

    def test_staging_helper_runs_as_controller_and_uses_hidden_tty(self):
        self.assertIn('$(id -un)" != "ci-controller"', STAGE)
        self.assertIn("read -r -s TOKEN </dev/tty", STAGE)
        self.assertIn("chmod 0600", STAGE)
        self.assertIn("/var/lib/workspace-ci/controller/github-token", STAGE)
        self.assertNotIn("$1", STAGE)
        self.assertNotIn("GITHUB_TOKEN", STAGE)
        self.assertNotIn("GH_TOKEN", STAGE)

    def test_bootstrap_is_exact_sha_guarded_and_rollback_capable(self):
        guard = BOOTSTRAP.index("UNEXPECTED_WORKSPACE_CONTROL_SHA")
        first_install = BOOTSTRAP.index("install -d -o root")
        self.assertLess(guard, first_install)
        self.assertIn("trap rollback ERR", BOOTSTRAP)
        self.assertIn("P5_INSTALL_ROLLBACK=COMPLETE", BOOTSTRAP)
        self.assertIn("systemd-analyze verify", BOOTSTRAP)
        self.assertIn("ISOLATED_GO_TOOLCHAIN_REQUIRED:/opt/workspace-ci/go/1.26.3", BOOTSTRAP)
        self.assertIn('GO_BIN=/opt/workspace-ci/go/1.26.3/bin/go', BOOTSTRAP)
        self.assertNotIn("command -v go", BOOTSTRAP)
        self.assertIn("IPAddressDeny=$LOCAL_SUBNET", BOOTSTRAP)
        self.assertIn("workspace-ci-controller-gpu.service", BOOTSTRAP)
        self.assertIn('"gpu_controller_state": gpu_controller_state', BOOTSTRAP)
        self.assertIn(
            "/opt/workspace-ci/cache-manager/lambda_ci_trusted_cache.py",
            BOOTSTRAP,
        )
        self.assertIn(
            "/opt/workspace-ci/provisioner/trusted-probes/lambda_ci_cuda_oom_probe.py",
            BOOTSTRAP,
        )
        self.assertIn(
            'install -o root -g root -m 0555 "$REPO_ROOT/scripts/lambda_ci_cuda_oom_probe.py"',
            BOOTSTRAP,
        )
        self.assertIn(
            "install -d -o root -g root -m 0700 /var/lib/workspace-ci/cache-manager",
            BOOTSTRAP,
        )
        self.assertIn(
            "install -d -o root -g root -m 0755 /srv/workspace-ci/research-engine/trusted-cache",
            BOOTSTRAP,
        )



    def test_admission_v2_install_payload_and_static_activation_are_complete(self):
        self.assertIn(
            "/opt/workspace-ci/provisioner/lambda_ci_admission.py",
            BOOTSTRAP,
        )
        self.assertIn(
            "/etc/workspace-ci/lambda-ci-workload-policy.v1.json",
            BOOTSTRAP,
        )
        self.assertIn(
            "--workload-policy /etc/workspace-ci/lambda-ci-workload-policy.v1.json",
            PROVISIONER_UNIT,
        )
        project = json.loads(
            (ROOT / "architecture" / "lambda-ci-project-research-engine.v1.json").read_text()
        )
        self.assertTrue(project["admission_v2"]["enabled"])
        self.assertEqual(
            project["admission_v2"]["live_enabled_workload_classes"],
            ["cpu-test", "gpu-small", "model-eval-single-gpu"],
        )
        self.assertEqual(
            project["admission_v2"]["routes"]["cpu-test"]["trusted_workflow"]["blob_sha"],
            "eca9f11373a591a34a2e19c0eafe31e9e171f785",
        )
        self.assertEqual(
            project["admission_v2"]["routes"]["gpu-small"]["trusted_workflow"]["blob_sha"],
            "e02e35306ae82c4ba393631cbaa1521ca53a28b4",
        )
        self.assertEqual(
            project["admission_v2"]["routes"]["model-eval-single-gpu"][
                "trusted_workflow"
            ]["blob_sha"],
            "33373b6c9f73adf17b65adf37ceed82df5ade6bb",
        )
        self.assertEqual(
            project["admission_v2"]["routes"]["model-eval-single-gpu"][
                "model_binding_id"
            ],
            "qwen3.5-4b",
        )
        self.assertNotIn("gpu-heavy", project["admission_v2"]["live_enabled_workload_classes"])

    def test_go_toolchain_pin_is_exact_official_release(self):
        pin = PINS["go_toolchain"]
        self.assertEqual(pin["version"], "1.26.3")
        self.assertEqual(
            pin["source_url"],
            "https://go.dev/dl/go1.26.3.linux-amd64.tar.gz",
        )
        self.assertEqual(
            pin["source_sha256"],
            "2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556",
        )
        self.assertEqual(pin["install_prefix"], "/opt/workspace-ci/go/1.26.3")

    def test_go_toolchain_bootstrap_is_unprivileged_download_and_root_promotion(self):
        self.assertIn("WORKSPACE_CI_GO_BOOTSTRAP_AUTHORIZED", GO_BOOTSTRAP)
        self.assertIn("WORKSPACE_CI_GO_EXPECTED_SHA", GO_BOOTSTRAP)
        self.assertIn("runuser -u ci-controller --", GO_BOOTSTRAP)
        self.assertIn("curl --fail --location --silent --show-error", GO_BOOTSTRAP)
        self.assertIn("ACTUAL_SHA=", GO_BOOTSTRAP)
        self.assertIn('[[ "$ACTUAL_SHA" == "$SHA256" ]]', GO_BOOTSTRAP)
        self.assertIn('mv -- "$STAGE/go" "$TARGET"', GO_BOOTSTRAP)
        self.assertIn('chown -R root:root "$TARGET"', GO_BOOTSTRAP)
        self.assertIn('chmod -R a+rX,go-w "$TARGET"', GO_BOOTSTRAP)
        self.assertIn("P5_GO_TOOLCHAIN_ROLLBACK=COMPLETE", GO_BOOTSTRAP)
        self.assertIn('"host_package_database_modified": False', GO_BOOTSTRAP)
        self.assertIn('"system_go_replaced": False', GO_BOOTSTRAP)
        for forbidden in (
            "apt ",
            "apt-get",
            "dpkg ",
            "/usr/bin/go",
            "/usr/local/go",
        ):
            self.assertNotIn(forbidden, GO_BOOTSTRAP)

    def test_p5_install_uses_only_isolated_go_toolchain(self):
        self.assertIn('GO_BIN=/opt/workspace-ci/go/1.26.3/bin/go', BOOTSTRAP)
        self.assertIn('[[ "$GO_VERSION" == "go1.26.3" ]]', BOOTSTRAP)
        self.assertNotIn("command -v go", BOOTSTRAP)

    def test_socket_contract_is_checked_before_controller_activation(self):
        socket_check = BOOTSTRAP.index("SOCKET_MODE_DRIFT")
        controller_start = BOOTSTRAP.index("systemctl restart workspace-ci-controller.service")
        self.assertLess(socket_check, controller_start)
        self.assertIn("root:workspace-ci-controller", BOOTSTRAP)
        self.assertIn('"660"', BOOTSTRAP)

    def test_kill_switch_removes_stale_socket(self):
        self.assertIn("systemctl stop workspace-ci-controller-gpu.service", KILL)
        self.assertIn("systemctl stop workspace-ci-controller.service", KILL)
        self.assertIn("systemctl stop workspace-ci-provisioner.socket workspace-ci-provisioner.service", KILL)
        self.assertIn("rm -f -- /run/workspace-ci/provisioner.sock", KILL)

    def test_uninstall_is_bounded_and_preserves_credential_state(self):
        for target in (
            "/opt/workspace-ci/controller/lambda-ci-controller",
            "/opt/workspace-ci/controller/stage-pat",
            "/opt/workspace-ci/provisioner/lambda_ci_admission.py",
            "/opt/workspace-ci/provisioner/lambda_ci_provisioner_service.py",
            "/opt/workspace-ci/provisioner/trusted-probes/lambda_ci_cuda_oom_probe.py",
            "/opt/workspace-ci/cache-manager/lambda_ci_trusted_cache.py",
            "/etc/workspace-ci/projects/research-engine.json",
            "/etc/workspace-ci/lambda-ci-workload-policy.v1.json",
            "/etc/systemd/system/workspace-ci-controller.service",
            "/etc/systemd/system/workspace-ci-controller-gpu.service",
            "/etc/systemd/system/workspace-ci-provisioner.service",
        ):
            self.assertIn(target, REMOVE)
        self.assertNotIn(
            "/var/lib/workspace-ci/controller/github-token",
            REMOVE,
        )
        self.assertIn("credential and provisioner evidence/state are intentionally preserved", REMOVE)


if __name__ == "__main__":
    unittest.main()
