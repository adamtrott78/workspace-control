from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "lambda-ci-workspace-control-codex-bootstrap.yml"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


class WorkspaceReasoningEconomyCodexRuntimeTests(unittest.TestCase):
    def test_codex_bootstrap_targets_only_workspace_control_control_small(self):
        text = _workflow()

        runs_on = [
            line.split(":", 1)[1].strip()
            for line in text.splitlines()
            if line.lstrip().startswith("runs-on:")
        ]
        self.assertEqual(runs_on, ["lambda-workspace-control-control-small"])
        self.assertIn("workspace-control-control-small-v1", text)

        self.assertNotIn("lambda-padataset-scientific-single-gpu", text)
        self.assertNotIn("lambda-padataset-scientific-single-gpu-2", text)
        self.assertNotIn("runs-on: self-hosted", text)

    def test_codex_bootstrap_proves_no_gpu_docker_or_sibling_project_access(self):
        text = _workflow()

        for forbidden_path in (
            "/home/atrott",
            "/srv/workspace-ci/research-engine",
            "/srv/workspace-ci/padataset",
        ):
            self.assertEqual(text.count(forbidden_path), 1)
        self.assertIn('[[ ! -r "$forbidden" ]]', text)
        self.assertNotIn("/home/atrott/.codex", text)

        self.assertIn("/var/run/docker.sock", text)
        self.assertIn("/run/docker.sock", text)
        self.assertIn('[[ ! -r "$socket" && ! -w "$socket" ]]', text)
        for docker_command in (
            "docker run",
            "docker exec",
            "docker build",
            "docker pull",
            "docker compose",
        ):
            self.assertNotIn(docker_command, text)

        self.assertIn("command -v nvidia-smi", text)
        self.assertIn("nvidia-smi -L", text)
        self.assertIn("unexpectedly has NVIDIA access", text)
        for gpu_enablement in (
            "CUDA_VISIBLE_DEVICES=",
            "NVIDIA_VISIBLE_DEVICES=",
            "--gpus",
            "/dev/nvidia",
        ):
            self.assertNotIn(gpu_enablement, text)

    def test_codex_bootstrap_is_checksum_pinned_and_persists_only_in_project_home(self):
        text = _workflow()

        self.assertIn('CODEX_VERSION: "0.155.1"', text)
        self.assertIn(
            'CODEX_ARCHIVE_SHA256: '
            '"a0ef8b2debc3bf747e07b1a039354de31300ac0dcc2276498ba281470b5d9115"',
            text,
        )
        self.assertIn(
            'CODEX_ARCHIVE_URL: '
            '"https://github.com/openai/codex/releases/download/rust-v0.155.1/'
            'codex-x86_64-unknown-linux-musl.tar.gz"',
            text,
        )
        self.assertIn('PROJECT_HOME: "/srv/workspace-ci/workspace-control/home"', text)
        self.assertIn(
            'runtime_root="$PROJECT_HOME/.local/share/workspace-reasoning-economy/codex"',
            text,
        )
        self.assertIn('bin_dir="$PROJECT_HOME/.local/bin"', text)
        self.assertIn('codex_home="$PROJECT_HOME/.codex-reasoning-economy"', text)
        self.assertIn('archive="$RUNNER_TEMP/codex-$CODEX_VERSION.tar.gz"', text)
        self.assertIn(
            'receipt="$RUNNER_TEMP/workspace-control-codex-bootstrap-receipt.json"',
            text,
        )

        self.assertNotIn("~/.codex", text)
        self.assertNotIn("$HOME/.codex", text)
        self.assertNotIn("/tmp/.codex", text)

    def test_codex_bootstrap_forces_chatgpt_auth_and_strips_api_key(self):
        text = _workflow()

        self.assertGreaterEqual(text.count("unset OPENAI_API_KEY"), 3)
        for line in text.splitlines():
            stripped = line.strip()
            self.assertFalse(stripped.startswith("OPENAI_API_KEY="))
            self.assertFalse(stripped.startswith("export OPENAI_API_KEY="))

        self.assertIn('forced_login_method = "chatgpt"', text)
        self.assertIn('cli_auth_credentials_store = "file"', text)
        self.assertIn('"$CODEX_BIN" login --device-auth', text)
        self.assertGreaterEqual(text.count("Logged in using ChatGPT"), 2)
        self.assertIn("[[ ! -v OPENAI_API_KEY ]]", text)

        for forbidden_auth in (
            "login --with-api-key",
            "login --api-key",
            "OPENAI_API_KEY:",
            "api_key =",
        ):
            self.assertNotIn(forbidden_auth, text)

    def test_codex_bootstrap_performs_zero_model_inference_and_emits_redacted_receipt(self):
        text = _workflow()

        self.assertIn('"model_inference_performed": False', text)
        self.assertIn('"credential_material_in_receipt": False', text)
        self.assertIn('"auth_mode": "chatgpt"', text)
        self.assertIn('"api_key_present": False', text)
        self.assertIn("workspace-control-codex-bootstrap-receipt.json", text)

        for inference_command in (
            '"$CODEX_BIN" exec',
            '"$CODEX_BIN" run',
            '"$CODEX_BIN" chat',
            "codex exec",
            "codex run",
        ):
            self.assertNotIn(inference_command, text)

        for sensitive_material in (
            '"email"',
            '"user_id"',
            '"account_id"',
            '"access_token"',
            '"refresh_token"',
            '"device_code"',
            '"token"',
        ):
            self.assertNotIn(sensitive_material, text)

        self.assertIn(
            'path: ${{ runner.temp }}/workspace-control-codex-bootstrap-receipt.json',
            text,
        )

    def test_codex_bootstrap_does_not_widen_capacity_or_root_authority(self):
        text = _workflow()

        for capacity_marker in (
            "reserved_project_slots",
            "max_active_runners",
            "host_concurrency",
            "project_concurrency",
            "max_concurrency",
            "PADataset concurrency",
            "Workspace Control concurrency",
        ):
            self.assertNotIn(capacity_marker, text)

        for authority_marker in (
            "sudo ",
            "systemctl ",
            "root_policy",
            "root-policy",
            "workspace_shell",
            "run_reviewed_helper",
            "contents: write",
            "actions: write",
            "-X POST",
            "-X PUT",
            "-X PATCH",
            "-X DELETE",
        ):
            self.assertNotIn(authority_marker, text)

        for root_path in (
            "/var/lib/workspace-ci/provisioner",
            "/var/lib/workspace-ci/reconciler",
            "/var/lib/workspace-ci/controller",
            "/run/workspace-ci",
        ):
            self.assertEqual(text.count(root_path), 1)


    def test_codex_preflight_uses_fresh_verified_runtime_and_reads_only_redacted_account_usage(self):
        text = _workflow()

        self.assertIn("/workspace-codex-preflight ", text)
        self.assertIn("steps.gate.outputs.mode == 'preflight'", text)
        self.assertNotIn("- name: Checkout exact candidate SHA", text)
        self.assertNotIn("ref: ${{ steps.gate.outputs.expected_sha }}", text)
        self.assertIn(
            "- name: Bind fresh checksum-pinned Codex runtime to persistent ChatGPT auth",
            text,
        )
        self.assertIn(
            'archive="$RUNNER_TEMP/codex-$CODEX_VERSION-trusted.tar.gz"',
            text,
        )
        self.assertGreaterEqual(text.count("sha256sum -c -"), 2)
        self.assertIn(
            'runtime_dir="$(mktemp -d "$RUNNER_TEMP/codex-trusted-runtime.XXXXXX")"',
            text,
        )
        self.assertIn(
            'codex_home="$(mktemp -d "$RUNNER_TEMP/codex-trusted-home.XXXXXX")"',
            text,
        )
        self.assertIn(
            'install -m 0600 "$persistent_auth" "$codex_home/auth.json"',
            text,
        )
        self.assertNotIn(
            'codex_home="$PROJECT_HOME/.codex-reasoning-economy"\n'
            '          codex_bin="$install_dir/codex"',
            text,
        )
        self.assertIn('web_search = "disabled"', text)
        self.assertIn("[agents]\n          enabled = false", text)
        self.assertIn("[orchestrator.mcp]\\n          enabled = false", text)
        self.assertIn("[orchestrator.skills]\\n          enabled = false", text)
        for disabled_feature in (
            "apps = false",
            "plugins = false",
            "tool_suggest = false",
            "shell_tool = false",
            "unified_exec = false",
            "view_image = false",
            "sleep_tool = false",
            "multi_agent = false",
            "image_generation = false",
            "code_mode = false",
            "memories = false",
            "goals = false",
            "skill_search = false",
            "executor_capability_discovery = false",
            "skip_host_skill_discovery = true",
            "deferred_executor = false",
            "current_time_reminder = false",
        ):
            self.assertIn(disabled_feature, text)
        self.assertIn("[tools.update_plan]", text)
        self.assertIn("[tools.experimental_request_user_input]", text)
        self.assertIn('"account/read"', text)
        self.assertIn('"account/rateLimits/read"', text)
        self.assertIn('"account/usage/read"', text)
        self.assertIn('"account_type": "chatgpt"', text)
        self.assertIn('"plan_type": plan_type.lower()', text)
        self.assertIn('account_result.get("requiresOpenaiAuth")', text)
        self.assertNotIn('account_result.get("requiresOpenAIAuth")', text)
        self.assertIn('"api_key_present": False', text)
        self.assertIn('"model_inference_performed": False', text)
        self.assertIn('"credential_material_in_receipt": False', text)
        self.assertIn("workspace-control-codex-preflight-receipt.json", text)
        self.assertIn("workspace-control-codex-preflight-receipt", text)
        self.assertIn("stderr=subprocess.DEVNULL", text)
        self.assertIn("/usr/bin/python3 -I - <<'PY'", text)
        self.assertIn('actual_sha="$EXPECTED_SHA"', text)

        install_index = text.index(
            "- name: Install checksum-pinned Codex CLI in Workspace Control home"
        )
        install_guard = text.index(
            "if: steps.gate.outputs.mode == 'bootstrap'",
            install_index,
        )
        self.assertGreater(install_guard, install_index)

        preflight_index = text.index(
            "- name: Bind fresh checksum-pinned Codex runtime to persistent ChatGPT auth"
        )
        preflight_guard = text.index(
            "if: steps.gate.outputs.mode == 'preflight' || steps.gate.outputs.mode == 'calibrate'",
            preflight_index,
        )
        self.assertGreater(preflight_guard, preflight_index)

        for forbidden in (
            '"email"',
            '"user_id"',
            '"account_id"',
            '"access_token"',
            '"refresh_token"',
            '"device_code"',
            '"threadUsage"',
        ):
            self.assertNotIn(forbidden, text)

    def test_codex_calibration_uses_only_pinned_trusted_source(self):
        text = _workflow()

        self.assertIn("/workspace-codex-calibrate ", text)
        self.assertIn('/workspace-codex-calibrate) mode="calibrate"', text)
        self.assertNotIn(
            "- name: Checkout exact candidate SHA",
            text,
        )
        self.assertNotIn(
            "ref: ${{ steps.gate.outputs.expected_sha }}",
            text,
        )
        self.assertIn(
            "- name: Checkout trusted calibration source",
            text,
        )
        self.assertIn(
            "if: steps.gate.outputs.mode == 'calibrate'",
            text,
        )
        self.assertIn("ref: ${{ github.workflow_sha }}", text)
        self.assertIn("path: .trusted-calibration", text)
        self.assertIn(
            'TRUSTED_HELPER_BLOB: "9076fc7598671b17546a6df60f7091d15e851bb4"',
            text,
        )
        self.assertIn(
            'helper_rel="scripts/lambda_ci_v3_workspace_control_codex_calibration_v1.py"',
            text,
        )
        self.assertIn(
            'git -C "$trusted_repo" rev-parse "HEAD:$helper_rel"',
            text,
        )
        self.assertIn(
            '[[ "$helper_blob" == "$TRUSTED_HELPER_BLOB" ]]',
            text,
        )
        self.assertIn(
            "unset OPENAI_API_KEY PYTHONPATH PYTHONHOME",
            text,
        )
        self.assertIn('/usr/bin/python3 -I "$helper"', text)
        self.assertIn(
            "- name: Bind fresh checksum-pinned Codex runtime to persistent ChatGPT auth",
            text,
        )
        self.assertIn('shell_tool = false', text)
        self.assertIn('multi_agent = false', text)
        self.assertIn('web_search = "disabled"', text)
        self.assertIn(
            "workspace-control-codex-calibration-receipt.json",
            text,
        )
        self.assertIn(
            "workspace-control-codex-calibration-receipt",
            text,
        )
        self.assertNotIn(
            "workspace_semantic_execution.adapters.codex_subscription",
            text,
        )
        self.assertNotIn(
            "workspace_semantic_execution.economics.codex_trace",
            text,
        )
        self.assertNotIn("sys.path.insert", text)
        self.assertNotIn("scored_replicate_plan_v1", text)
        self.assertNotIn("matrix-v1/", text)


    def test_codex_calibration_gates_inference_on_exact_bound_zero_tool_probe(self):
        text = _workflow()

        probe = text.index(
            "- name: Prove zero model-visible Codex tools with pinned runtime"
        )
        calibration = text.index(
            "- name: Run one bounded Codex allowance calibration quantum"
        )
        self.assertLess(probe, calibration)
        self.assertIn(
            'TRUSTED_PROBE_BLOB: "57df76db70a4e2d6d8ad68d298177db85750e0be"',
            text,
        )
        self.assertIn(
            'probe_rel="scripts/lambda_ci_v3_workspace_control_codex_zero_tool_probe_v1.py"',
            text,
        )
        self.assertIn(
            'git -C "$trusted_repo" rev-parse "HEAD:$probe_rel"',
            text,
        )
        self.assertIn(
            '[[ "$probe_blob" == "$TRUSTED_PROBE_BLOB" ]]',
            text,
        )
        self.assertIn(
            '/usr/bin/python3 -I "$probe" --helper "$helper"',
            text,
        )
        probe_block = text[probe:calibration]
        self.assertNotIn('"$CODEX_BIN" exec', probe_block)
        self.assertNotIn("codex exec", probe_block)


if __name__ == "__main__":
    unittest.main()
