import copy
import importlib.util
import json
import pathlib
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "lambda_ci_admission.py"

spec = importlib.util.spec_from_file_location("lambda_ci_admission", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

MANIFEST = json.loads(
    (ROOT / "architecture" / "lambda-ci-project-research-engine.v1.json").read_text()
)
POLICY = json.loads(
    (ROOT / "architecture" / "lambda-ci-workload-policy.v1.json").read_text()
)
NOW = datetime(2026, 10, 6, 20, 0, tzinfo=timezone.utc)
CANDIDATE = "a" * 40
WORKFLOW_HEAD = "b" * 40


def enabled_manifest():
    value = copy.deepcopy(MANIFEST)
    value["admission_v2"]["enabled"] = True
    return value


def good_attestation(workload="cpu-test"):
    route = MANIFEST["admission_v2"]["routes"][workload]
    trusted = route["trusted_workflow"]
    command = trusted["job_display_claim"]["command"]
    return {
        "schema_version": 2,
        "source": "github_scale_set_controller",
        "repository": "adamtrott78/research-engine",
        "scale_set_name": route["scale_set_name"],
        "job_message_type": "JobAssigned",
        "runner_request_id": 0,
        "workflow_run_id": 37422040174,
        "job_id": "777",
        "job_workflow_ref": trusted["job_workflow_ref"],
        "workflow_path": trusted["path"],
        "workflow_default_branch_commit_sha": WORKFLOW_HEAD,
        "workflow_blob_sha": trusted["blob_sha"],
        "event_name": trusted["event_name"],
        "job_display_name": (
            f"wc-admission-v1|workload={workload}|pr=101|request={command} {CANDIDATE}"
        ),
        "actor_login": "adamtrott78",
        "triggering_actor_login": "adamtrott78",
        "pr_number": 101,
        "pr_state": "open",
        "pr_head_repository": "adamtrott78/research-engine",
        "candidate_sha": CANDIDATE,
        "candidate_verification": "PR_HEAD_MATCH",
        "verified_at": NOW.isoformat().replace("+00:00", "Z"),
    }


def good_request(workload="cpu-test"):
    return {
        "schema_version": 2,
        "request_id": str(uuid.uuid4()),
        "project_id": "research-engine",
        "workload_class": workload,
        "runner_name": "lambda-research-engine-test",
        "jit_config": "opaque-jit-secret",
        "attestation": good_attestation(workload),
    }


class AdmissionContractTests(unittest.TestCase):
    def test_canonical_project_manifest_enables_only_accepted_p5_classes(self):
        admission = MANIFEST["admission_v2"]
        self.assertTrue(admission["enabled"])
        self.assertEqual(
            admission["live_enabled_workload_classes"],
            ["cpu-test", "gpu-small"],
        )
        self.assertNotIn("gpu-heavy", admission["live_enabled_workload_classes"])

    def test_disabled_v2_fails_closed(self):
        disabled = copy.deepcopy(MANIFEST)
        disabled["admission_v2"]["enabled"] = False
        with self.assertRaisesRegex(mod.AdmissionError, "not enabled"):
            mod.mint_admission(good_request(), disabled, POLICY, now=NOW)

    def test_cpu_admission_is_root_derived_and_nonsecret(self):
        request = good_request("cpu-test")
        admission = mod.mint_admission(
            request,
            enabled_manifest(),
            POLICY,
            now=NOW,
            policy_sha256="1" * 64,
        )
        self.assertEqual(admission["workload_class"], "cpu-test")
        self.assertEqual(admission["execution_profile"], "cpu-test")
        self.assertEqual(admission["candidate_sha"], CANDIDATE)
        self.assertEqual(
            admission["capability_classes"]["cache_access"],
            "NO_PERSISTENT_CACHE_AUTHORITY",
        )
        self.assertEqual(admission["resource_ceiling"]["gpu_uuids"], [])
        self.assertTrue(admission["lifecycle"]["single_use"])
        self.assertEqual(admission["policy"]["policy_sha256"], "1" * 64)
        self.assertNotIn(request["jit_config"], json.dumps(admission))

    def test_gpu_admission_binds_only_accepted_uuid(self):
        request = good_request("gpu-small")
        admission = mod.mint_admission(
            request,
            enabled_manifest(),
            POLICY,
            now=NOW,
        )
        self.assertEqual(admission["execution_profile"], "gpu-small")
        self.assertEqual(
            admission["resource_ceiling"]["gpu_uuids"],
            ["GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"],
        )

    def test_model_and_gpu_heavy_cannot_be_minted_in_current_policy(self):
        manifest = enabled_manifest()
        manifest["admission_v2"]["live_enabled_workload_classes"].extend(
            ["model-eval-single-gpu", "gpu-heavy"]
        )
        manifest["admission_v2"]["routes"]["model-eval-single-gpu"] = copy.deepcopy(
            manifest["admission_v2"]["routes"]["gpu-small"]
        )
        manifest["admission_v2"]["routes"]["gpu-heavy"] = copy.deepcopy(
            manifest["admission_v2"]["routes"]["gpu-small"]
        )

        request = good_request("gpu-small")
        request["workload_class"] = "model-eval-single-gpu"
        request["attestation"]["job_display_name"] = (
            f"wc-admission-v1|workload=model-eval-single-gpu|pr=101"
            f"|request=/lambda-ci-p5-gpu {CANDIDATE}"
        )
        with self.assertRaisesRegex(mod.AdmissionError, "not an accepted live capability"):
            mod.mint_admission(request, manifest, POLICY, now=NOW)

        request["workload_class"] = "gpu-heavy"
        request["attestation"]["job_display_name"] = (
            f"wc-admission-v1|workload=gpu-heavy|pr=101"
            f"|request=/lambda-ci-p5-gpu {CANDIDATE}"
        )
        with self.assertRaisesRegex(mod.AdmissionError, "not an accepted live capability"):
            mod.mint_admission(request, manifest, POLICY, now=NOW)

    def test_trusted_workflow_identity_mismatch_fails_closed(self):
        for key, value in (
            ("workflow_blob_sha", "c" * 40),
            ("workflow_path", ".github/workflows/evil.yml"),
            (
                "job_workflow_ref",
                "adamtrott78/research-engine/.github/workflows/evil.yml@refs/heads/main",
            ),
            ("event_name", "pull_request_target"),
        ):
            request = good_request()
            request["attestation"][key] = value
            with self.assertRaises(mod.AdmissionError, msg=key):
                mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

    def test_candidate_claim_must_match_pr_attestation(self):
        request = good_request()
        request["attestation"]["candidate_sha"] = "c" * 40
        with self.assertRaisesRegex(mod.AdmissionError, "display claim disagrees"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

    def test_foreign_actor_or_fork_head_is_rejected(self):
        request = good_request()
        request["attestation"]["actor_login"] = "someone-else"
        with self.assertRaisesRegex(mod.AdmissionError, "actor"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

        request = good_request()
        request["attestation"]["pr_head_repository"] = "attacker/fork"
        with self.assertRaisesRegex(mod.AdmissionError, "fork or foreign"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

    def test_closed_pr_is_rejected(self):
        request = good_request()
        request["attestation"]["pr_state"] = "closed"
        with self.assertRaisesRegex(mod.AdmissionError, "not open"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

    def test_stale_and_future_attestations_are_rejected(self):
        request = good_request()
        request["attestation"]["verified_at"] = (
            NOW - timedelta(seconds=901)
        ).isoformat().replace("+00:00", "Z")
        with self.assertRaisesRegex(mod.AdmissionError, "stale"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

        request = good_request()
        request["attestation"]["verified_at"] = (
            NOW + timedelta(seconds=61)
        ).isoformat().replace("+00:00", "Z")
        with self.assertRaisesRegex(mod.AdmissionError, "future"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

    def test_request_digest_ignores_recoverable_jit_transport_secret(self):
        manifest = enabled_manifest()
        first = good_request()
        first["attestation"]["job_message_type"] = "JobAvailable"
        first["attestation"]["runner_request_id"] = 12345
        second = copy.deepcopy(first)
        second["jit_config"] = "different-jit-secret"
        second["attestation"]["verified_at"] = (
            NOW + timedelta(seconds=5)
        ).isoformat().replace("+00:00", "Z")
        second["attestation"]["job_message_type"] = "JobAssigned"
        second["attestation"]["runner_request_id"] = 0

        a = mod.mint_admission(first, manifest, POLICY, now=NOW)
        b = mod.mint_admission(second, manifest, POLICY, now=NOW)
        self.assertEqual(
            a["request_digest_sha256"],
            b["request_digest_sha256"],
        )
        self.assertNotIn(first["jit_config"], json.dumps(a))
        self.assertNotIn(second["jit_config"], json.dumps(b))

    def test_route_cannot_widen_underlying_profile(self):
        manifest = enabled_manifest()
        manifest["admission_v2"]["routes"]["gpu-small"]["execution_profile"] = "gpu-heavy"
        with self.assertRaises(mod.AdmissionError):
            mod.mint_admission(good_request("gpu-small"), manifest, POLICY, now=NOW)

    def test_extra_request_or_attestation_keys_are_rejected(self):
        request = good_request()
        request["command"] = ["bash", "-lc", "id"]
        with self.assertRaisesRegex(mod.AdmissionError, "keys mismatch"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

        request = good_request()
        request["attestation"]["credential"] = "secret"
        with self.assertRaisesRegex(mod.AdmissionError, "keys mismatch"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)


    def test_consumption_binds_single_use_and_rejects_reuse(self):
        manifest = enabled_manifest()
        admission = mod.mint_admission(
            good_request(),
            manifest,
            POLICY,
            now=NOW,
            policy_sha256="1" * 64,
        )
        consumed = mod.consume_admission(
            admission,
            manifest,
            POLICY,
            now=NOW + timedelta(seconds=1),
            policy_sha256="1" * 64,
        )
        self.assertIsNotNone(consumed["lifecycle"]["consumed_at"])
        self.assertIsNone(admission["lifecycle"]["consumed_at"])
        with self.assertRaisesRegex(mod.AdmissionError, "already consumed"):
            mod.consume_admission(
                consumed,
                manifest,
                POLICY,
                now=NOW + timedelta(seconds=2),
                policy_sha256="1" * 64,
            )

    def test_stale_policy_digest_epoch_profile_and_kill_switch_fail_closed(self):
        manifest = enabled_manifest()
        admission = mod.mint_admission(
            good_request(),
            manifest,
            POLICY,
            now=NOW,
            policy_sha256="1" * 64,
        )

        with self.assertRaisesRegex(mod.AdmissionError, "policy digest"):
            mod.consume_admission(
                admission,
                manifest,
                POLICY,
                now=NOW + timedelta(seconds=1),
                policy_sha256="2" * 64,
            )

        changed_policy = copy.deepcopy(POLICY)
        changed_policy["policy_epoch"] += 1
        with self.assertRaisesRegex(mod.AdmissionError, "policy epoch"):
            mod.consume_admission(
                admission,
                manifest,
                changed_policy,
                now=NOW + timedelta(seconds=1),
                policy_sha256="1" * 64,
            )

        changed_manifest = copy.deepcopy(manifest)
        changed_manifest["profiles"]["cpu-test"]["cpu_quota_percent"] -= 1
        with self.assertRaisesRegex(mod.AdmissionError, "project/profile"):
            mod.consume_admission(
                admission,
                changed_manifest,
                POLICY,
                now=NOW + timedelta(seconds=1),
                policy_sha256="1" * 64,
            )

        killed_manifest = copy.deepcopy(manifest)
        killed_manifest["admission_v2"]["kill_switch_epoch"] += 1
        with self.assertRaisesRegex(mod.AdmissionError, "kill-switch"):
            mod.consume_admission(
                admission,
                killed_manifest,
                POLICY,
                now=NOW + timedelta(seconds=1),
                policy_sha256="1" * 64,
            )

    def test_expired_admission_cannot_be_consumed(self):
        manifest = enabled_manifest()
        admission = mod.mint_admission(
            good_request(),
            manifest,
            POLICY,
            now=NOW,
        )
        with self.assertRaisesRegex(mod.AdmissionError, "expired"):
            mod.consume_admission(
                admission,
                manifest,
                POLICY,
                now=NOW + timedelta(seconds=901),
            )

    def test_lifecycle_identity_requires_available_handle_or_assigned_job(self):
        request = good_request()
        request["attestation"]["job_message_type"] = "JobAvailable"
        request["attestation"]["runner_request_id"] = 0
        with self.assertRaisesRegex(mod.AdmissionError, "JobAvailable runner_request_id"):
            mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)

        request = good_request()
        request["attestation"]["job_message_type"] = "JobAssigned"
        request["attestation"]["runner_request_id"] = 0
        admission = mod.mint_admission(request, enabled_manifest(), POLICY, now=NOW)
        self.assertEqual(admission["candidate_sha"], CANDIDATE)


if __name__ == "__main__":
    unittest.main()
