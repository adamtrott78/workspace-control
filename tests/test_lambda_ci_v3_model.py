import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

compiler_spec = importlib.util.spec_from_file_location(
    "lambda_ci_policy_compiler",
    ROOT / "scripts" / "lambda_ci_policy_compiler.py",
)
compiler = importlib.util.module_from_spec(compiler_spec)
assert compiler_spec.loader is not None
compiler_spec.loader.exec_module(compiler)

model_spec = importlib.util.spec_from_file_location(
    "lambda_ci_v3_model",
    ROOT / "scripts" / "lambda_ci_v3_model.py",
)
model = importlib.util.module_from_spec(model_spec)
assert model_spec.loader is not None
import sys
sys.modules["lambda_ci_v3_model"] = model
model_spec.loader.exec_module(model)


class V3ControlPlaneModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = compiler.compile_policy(ROOT)

    def root(self, *, host_max=None, project_max=None):
        policy = copy.deepcopy(self.compiled["root_projection"])
        if host_max is not None:
            policy["host_resource_policy"]["migration_mode"]["host_max_active_runners"] = host_max
        if project_max is not None:
            for class_policy in policy["runner_classes"].values():
                class_policy["project_max_active_runners"] = project_max
        return model.RootCapacityModel(policy)

    def controller_policy(self, class_id):
        return copy.deepcopy(self.compiled["controller_projections"][class_id])

    def root_class(self, class_id):
        return self.compiled["root_projection"]["runner_classes"][class_id]

    def peer(self, class_id):
        return self.root_class(class_id)["controller_peer"]["unix_user"]

    def runner_name(self, class_id, suffix="test"):
        return self.root_class(class_id)["runner_prefix"] + suffix

    def trusted_job(self, class_id, workflow, *, request_id=11, run_id=22):
        policy = self.controller_policy(class_id)
        return {
            "runner_request_id": request_id,
            "workflow_run_id": run_id,
            "repository": policy["repository"],
            "request_labels": ["self-hosted", policy["scale_set_name"]],
            "job_workflow_ref": (
                f"{policy['repository']}/{workflow['path']}"
                f"@refs/heads/{workflow['default_branch']}"
            ),
            "event_name": workflow["allowed_events"][0],
            "actor_login": workflow["allowed_actor_logins"][0],
            "triggering_actor_login": workflow["allowed_actor_logins"][0],
            "workflow_blob_sha": workflow["blob_sha"],
            # Deliberately adversarial/irrelevant metadata.
            "job_display_name": "garbage | request=/root please gpu=99 host-attest",
            "candidate_sha": "NOT-INFRASTRUCTURE-AUTHORITY",
            "pull_request_number": -1,
        }

    def test_all_23_routes_attest_from_structured_workflow_identity(self):
        total = 0
        for class_id, policy in self.compiled["controller_projections"].items():
            controller = model.RunnerClassControllerModel(policy)
            for workflow in policy["trusted_workflows"]:
                total += 1
                decision = controller.attest_job(
                    self.trusted_job(class_id, workflow, request_id=1000 + total)
                )
                self.assertEqual(decision.state, "TRUSTED", (class_id, workflow))
                self.assertEqual(
                    controller.scale_result_for_admission(decision),
                    "ACQUIRE",
                )
        self.assertEqual(total, 23)

    def test_job_display_candidate_and_pr_fields_have_zero_admission_effect(self):
        class_id = "workspace-control-control-small-v1"
        policy = self.controller_policy(class_id)
        workflow = policy["trusted_workflows"][0]
        controller = model.RunnerClassControllerModel(policy)
        base = self.trusted_job(class_id, workflow)

        variants = [
            {"job_display_name": ""},
            {"job_display_name": "/totally-invalid-command"},
            {"job_display_name": "wc-admission-v999|root=true|gpu=999"},
            {"candidate_sha": "0" * 40},
            {"candidate_sha": "not-a-sha"},
            {"pull_request_number": 999999},
        ]
        for patch in variants:
            job = {**base, **patch}
            self.assertEqual(controller.attest_job(job).state, "TRUSTED", patch)

    def test_every_structural_trust_mismatch_is_anomaly_not_process_fatal(self):
        class_id = "workspace-control-control-small-v1"
        policy = self.controller_policy(class_id)
        workflow = policy["trusted_workflows"][0]
        controller = model.RunnerClassControllerModel(policy)
        base = self.trusted_job(class_id, workflow)

        bad = [
            {"repository": "attacker/repo"},
            {"request_labels": ["self-hosted", "lambda-wrong"]},
            {"job_workflow_ref": "malformed"},
            {
                "job_workflow_ref":
                    f"{policy['repository']}/.github/workflows/not-trusted.yml@refs/heads/main"
            },
            {
                "job_workflow_ref":
                    f"{policy['repository']}/{workflow['path']}@refs/heads/evil"
            },
            {"event_name": "workflow_dispatch"},
            {"actor_login": "not-adamtrott78"},
            {"triggering_actor_login": "not-adamtrott78"},
            {"workflow_blob_sha": "0" * 40},
            {"runner_request_id": 0},
            {"workflow_run_id": 0},
        ]
        for patch in bad:
            decision = controller.attest_job({**base, **patch})
            self.assertEqual(decision.state, "ANOMALOUS_UNTRUSTED", patch)
            self.assertEqual(
                controller.scale_result_for_admission(decision),
                "ACK_ANOMALY_KEEP_PROCESS_ALIVE",
            )

    def test_100_request_local_anomalies_never_map_to_process_fatal(self):
        class_id = "padataset-cpu-public-v1"
        policy = self.controller_policy(class_id)
        workflow = policy["trusted_workflows"][0]
        controller = model.RunnerClassControllerModel(policy)
        for i in range(100):
            job = self.trusted_job(class_id, workflow, request_id=10000 + i)
            job["actor_login"] = f"attacker-{i}"
            decision = controller.attest_job(job)
            self.assertEqual(
                controller.scale_result_for_admission(decision),
                "ACK_ANOMALY_KEEP_PROCESS_ALIVE",
            )

    def test_total_assigned_jobs_is_only_desired_capacity_input(self):
        class_id = "research-model-dual-public-v1"
        controller = model.RunnerClassControllerModel(self.controller_policy(class_id))
        self.assertEqual(controller.desired_capacity(0), 0)
        self.assertEqual(controller.desired_capacity(1), 1)
        self.assertEqual(controller.desired_capacity(999), 1)
        with self.assertRaises(model.ProtocolFatal):
            controller.desired_capacity(-1)
        with self.assertRaises(model.ProtocolFatal):
            controller.desired_capacity(1.5)

    def test_capacity_outcomes_have_explicit_liveness_classification(self):
        controller = model.RunnerClassControllerModel(
            self.controller_policy("workspace-control-control-small-v1")
        )
        for status in {"RESERVED", "ACCEPTED", "DUPLICATE"}:
            self.assertEqual(
                controller.scale_result_for_capacity(status),
                "HANDLED_KEEP_PROCESS_ALIVE",
            )
        for status in {"BUSY", "CLASS_QUARANTINED", "RESERVATION_EXPIRED"}:
            self.assertEqual(
                controller.scale_result_for_capacity(status),
                "CAPACITY_LOCAL_KEEP_PROCESS_ALIVE",
            )
        for status in {"INVALID_REQUEST", "UNAUTHORIZED_PEER"}:
            self.assertEqual(
                controller.scale_result_for_capacity(status),
                "FATAL_PROTOCOL",
            )

    def test_authorized_reserve_launch_finish_happy_path(self):
        class_id = "workspace-control-control-small-v1"
        root = self.root()
        peer = self.peer(class_id)
        name = self.runner_name(class_id, "happy")
        reserve = root.reserve(peer_user=peer, request_id="req-happy", runner_name=name)
        self.assertEqual(reserve["status"], "RESERVED")
        self.assertEqual(root.status(peer_user=peer, request_id="req-happy")["status"], "RESERVED")

        launch = root.launch(
            peer_user=peer,
            request_id="req-happy",
            runner_name=name,
            jit_config="opaque-jit",
        )
        self.assertEqual(launch["status"], "ACCEPTED")
        self.assertEqual(root.status(peer_user=peer, request_id="req-happy")["status"], "ACCEPTED")

        root.finish(request_id="req-happy", success=True, cleanup_ok=True)
        self.assertEqual(root.status(peer_user=peer, request_id="req-happy")["status"], "COMPLETED")

    def test_unknown_peer_and_runner_prefix_violation_are_fatal(self):
        root = self.root()
        with self.assertRaisesRegex(model.ProtocolFatal, "UNAUTHORIZED_PEER"):
            root.reserve(
                peer_user="ci-controller",
                request_id="req-unknown-peer",
                runner_name="lambda-anything",
            )

        class_id = "workspace-control-control-small-v1"
        with self.assertRaisesRegex(model.ProtocolFatal, "runner-name prefix mismatch"):
            root.reserve(
                peer_user=self.peer(class_id),
                request_id="req-wrong-prefix",
                runner_name="lambda-research-engine-evil",
            )

    def test_duplicate_reserve_is_idempotent_but_conflicting_replay_is_fatal(self):
        class_id = "workspace-control-control-small-v1"
        root = self.root()
        peer = self.peer(class_id)
        name = self.runner_name(class_id, "dup")
        first = root.reserve(peer_user=peer, request_id="req-dup", runner_name=name)
        second = root.reserve(peer_user=peer, request_id="req-dup", runner_name=name)
        self.assertEqual(first["status"], "RESERVED")
        self.assertEqual(second["status"], "DUPLICATE")
        self.assertEqual(second["receipt_status"], "RESERVED")

        with self.assertRaisesRegex(model.ProtocolFatal, "replay conflict"):
            root.reserve(
                peer_user=peer,
                request_id="req-dup",
                runner_name=self.runner_name(class_id, "different"),
            )

    def test_cross_class_request_id_collision_is_fatal(self):
        root = self.root(host_max=4, project_max=4)
        a = "workspace-control-control-small-v1"
        b = "padataset-cpu-public-v1"
        root.reserve(
            peer_user=self.peer(a),
            request_id="same-request",
            runner_name=self.runner_name(a, "one"),
        )
        with self.assertRaises(model.ProtocolFatal):
            root.reserve(
                peer_user=self.peer(b),
                request_id="same-request",
                runner_name=self.runner_name(b, "two"),
            )

    def test_busy_does_not_generate_jit(self):
        root = self.root()  # migration host max = 1
        wc = "workspace-control-control-small-v1"
        pad = "padataset-cpu-public-v1"
        first = model.ClassCapacityControllerModel(self.controller_policy(wc), root)
        second = model.ClassCapacityControllerModel(self.controller_policy(pad), root)

        self.assertEqual(
            first.provision_one(
                request_id="req-wc",
                runner_name=self.runner_name(wc, "one"),
            ),
            "ACCEPTED",
        )
        self.assertEqual(first.jit_generation_count, 1)
        self.assertEqual(
            second.provision_one(
                request_id="req-pad",
                runner_name=self.runner_name(pad, "two"),
            ),
            "BUSY",
        )
        self.assertEqual(second.jit_generation_count, 0)

    def test_jit_is_generated_only_after_reservation(self):
        root = self.root()
        class_id = "padataset-cpu-public-v1"
        calls = []
        controller = model.ClassCapacityControllerModel(
            self.controller_policy(class_id),
            root,
            jit_factory=lambda runner_name: calls.append(runner_name) or f"jit:{runner_name}",
        )
        status = controller.provision_one(
            request_id="req-order",
            runner_name=self.runner_name(class_id, "order"),
        )
        self.assertEqual(status, "ACCEPTED")
        self.assertEqual(len(calls), 1)
        self.assertIn("req-order", root.records)
        self.assertEqual(root.records["req-order"].state, "LAUNCHED")

    def test_reservation_expiry_releases_capacity_and_launch_is_rejected(self):
        class_id = "padataset-gpu-single-public-v1"
        root = self.root(host_max=4, project_max=4)
        peer = self.peer(class_id)
        name = self.runner_name(class_id, "expire")
        result = root.reserve(peer_user=peer, request_id="req-expire", runner_name=name)
        self.assertEqual(result["status"], "RESERVED")
        root.advance(60)
        self.assertEqual(root.status(peer_user=peer, request_id="req-expire")["status"], "CANCELED")
        launch = root.launch(
            peer_user=peer,
            request_id="req-expire",
            runner_name=name,
            jit_config="orphan-jit",
        )
        self.assertEqual(launch["status"], "RESERVATION_EXPIRED")

    def test_cancel_reserved_request_is_idempotent_and_releases_resources(self):
        class_id = "padataset-gpu-single-public-v1"
        root = self.root(host_max=4, project_max=4)
        peer = self.peer(class_id)
        gpu = self.root_class(class_id)["exclusive_resource_claims"][0]
        root.reserve(
            peer_user=peer,
            request_id="req-cancel",
            runner_name=self.runner_name(class_id, "cancel"),
        )
        self.assertEqual(root.resource_owner(gpu), "req-cancel")
        self.assertEqual(
            root.cancel(peer_user=peer, request_id="req-cancel")["status"],
            "CANCELED",
        )
        self.assertIsNone(root.resource_owner(gpu))
        self.assertEqual(
            root.cancel(peer_user=peer, request_id="req-cancel")["status"],
            "ALREADY_TERMINAL",
        )

    def test_root_crash_before_unit_recovers_failed_and_releases_resources(self):
        class_id = "padataset-gpu-single-public-v1"
        root = self.root(host_max=4, project_max=4)
        peer = self.peer(class_id)
        name = self.runner_name(class_id, "crash-before")
        gpu = self.root_class(class_id)["exclusive_resource_claims"][0]
        root.reserve(peer_user=peer, request_id="req-crash-before", runner_name=name)
        with self.assertRaisesRegex(model.ModelError, "CRASH_BEFORE_UNIT"):
            root.launch(
                peer_user=peer,
                request_id="req-crash-before",
                runner_name=name,
                jit_config="jit-secret",
                fault="crash_before_unit",
            )
        self.assertEqual(root.records["req-crash-before"].state, "PREPARING")
        root.reconcile_startup()
        self.assertEqual(root.status(peer_user=peer, request_id="req-crash-before")["status"], "FAILED")
        self.assertIsNone(root.resource_owner(gpu))

    def test_root_crash_after_unit_recovers_accepted_without_relaunch(self):
        class_id = "padataset-gpu-single-public-v1"
        root = self.root(host_max=4, project_max=4)
        peer = self.peer(class_id)
        name = self.runner_name(class_id, "crash-after")
        root.reserve(peer_user=peer, request_id="req-crash-after", runner_name=name)
        with self.assertRaisesRegex(model.ModelError, "CRASH_AFTER_UNIT"):
            root.launch(
                peer_user=peer,
                request_id="req-crash-after",
                runner_name=name,
                jit_config="jit-secret",
                fault="crash_after_unit",
            )
        self.assertEqual(root.records["req-crash-after"].state, "PREPARING")
        root.reconcile_startup()
        self.assertEqual(root.status(peer_user=peer, request_id="req-crash-after")["status"], "ACCEPTED")
        duplicate = root.launch(
            peer_user=peer,
            request_id="req-crash-after",
            runner_name=name,
            jit_config="different-jit-must-not-relaunch",
        )
        self.assertEqual(duplicate["status"], "DUPLICATE")
        self.assertEqual(duplicate["receipt_status"], "ACCEPTED")

    def test_dual_gpu_reservation_is_atomic_when_gpu0_is_busy(self):
        root = self.root(host_max=4, project_max=4)
        single = "padataset-gpu-single-public-v1"
        dual = "research-model-dual-public-v1"

        single_result = root.reserve(
            peer_user=self.peer(single),
            request_id="req-single",
            runner_name=self.runner_name(single, "one"),
        )
        self.assertEqual(single_result["status"], "RESERVED")
        gpu0, gpu1 = self.root_class(dual)["exclusive_resource_claims"]
        self.assertEqual(root.resource_owner(gpu0), "req-single")
        self.assertIsNone(root.resource_owner(gpu1))

        dual_result = root.reserve(
            peer_user=self.peer(dual),
            request_id="req-dual",
            runner_name=self.runner_name(dual, "two"),
        )
        self.assertEqual(dual_result["status"], "BUSY")
        self.assertEqual(root.resource_owner(gpu0), "req-single")
        self.assertIsNone(root.resource_owner(gpu1))
        self.assertNotIn("req-dual", root.records)

    def test_dual_gpu_reservation_claims_and_releases_both_resources(self):
        root = self.root(host_max=4, project_max=4)
        class_id = "research-model-dual-public-v1"
        peer = self.peer(class_id)
        resources = self.root_class(class_id)["exclusive_resource_claims"]
        self.assertEqual(len(resources), 2)
        root.reserve(
            peer_user=peer,
            request_id="req-dual-clean",
            runner_name=self.runner_name(class_id, "clean"),
        )
        self.assertEqual([root.resource_owner(x) for x in resources], ["req-dual-clean"] * 2)
        root.cancel(peer_user=peer, request_id="req-dual-clean")
        self.assertEqual([root.resource_owner(x) for x in resources], [None, None])

    def test_cpu_class_claims_no_gpu(self):
        class_id = "research-cpu-public-v1"
        root = self.root(host_max=4, project_max=4)
        result = root.reserve(
            peer_user=self.peer(class_id),
            request_id="req-cpu",
            runner_name=self.runner_name(class_id, "cpu"),
        )
        self.assertEqual(result["status"], "RESERVED")
        self.assertEqual(root.records["req-cpu"].reserved_resources, ())

    def test_cleanup_failure_quarantines_only_exact_class_and_retains_resources(self):
        root = self.root(host_max=4, project_max=4)
        class_id = "padataset-gpu-single-public-v1"
        peer = self.peer(class_id)
        name = self.runner_name(class_id, "dirty")
        gpu = self.root_class(class_id)["exclusive_resource_claims"][0]
        root.reserve(peer_user=peer, request_id="req-dirty", runner_name=name)
        root.launch(
            peer_user=peer,
            request_id="req-dirty",
            runner_name=name,
            jit_config="jit",
        )
        root.finish(request_id="req-dirty", success=False, cleanup_ok=False)

        self.assertIn(class_id, root.quarantined_classes)
        self.assertEqual(root.resource_owner(gpu), "req-dirty")
        quarantined = root.reserve(
            peer_user=peer,
            request_id="req-dirty-next",
            runner_name=self.runner_name(class_id, "next"),
        )
        self.assertEqual(quarantined["status"], "CLASS_QUARANTINED")

        # A different class that needs the same GPU is BUSY, not quarantined.
        other = "research-gpu-single-public-v1"
        blocked = root.reserve(
            peer_user=self.peer(other),
            request_id="req-other",
            runner_name=self.runner_name(other, "other"),
        )
        self.assertEqual(blocked["status"], "BUSY")

        root.clear_quarantine_after_containment(
            runner_class_id=class_id,
            request_id="req-dirty",
        )
        self.assertNotIn(class_id, root.quarantined_classes)
        self.assertIsNone(root.resource_owner(gpu))
        self.assertEqual(
            root.status(peer_user=peer, request_id="req-dirty")["status"],
            "FAILED",
        )

    def test_migration_host_max_one_serializes_even_disjoint_cpu_classes(self):
        root = self.root()  # host max one is deliberate migration policy.
        a = "workspace-control-control-small-v1"
        b = "research-cpu-public-v1"
        self.assertEqual(
            root.reserve(
                peer_user=self.peer(a),
                request_id="req-host-a",
                runner_name=self.runner_name(a, "a"),
            )["status"],
            "RESERVED",
        )
        self.assertEqual(
            root.reserve(
                peer_user=self.peer(b),
                request_id="req-host-b",
                runner_name=self.runner_name(b, "b"),
            )["status"],
            "BUSY",
        )

    def test_project_and_class_limits_are_independent_when_host_limit_raised(self):
        root = self.root(host_max=9, project_max=1)
        a = "research-cpu-public-v1"
        b = "research-gpu-single-public-v1"
        root.reserve(
            peer_user=self.peer(a),
            request_id="req-project-a",
            runner_name=self.runner_name(a, "a"),
        )
        self.assertEqual(
            root.reserve(
                peer_user=self.peer(b),
                request_id="req-project-b",
                runner_name=self.runner_name(b, "b"),
            )["status"],
            "BUSY",
        )

    def test_status_missing_is_safe_and_class_scoped(self):
        root = self.root()
        class_id = "workspace-control-control-small-v1"
        self.assertEqual(
            root.status(peer_user=self.peer(class_id), request_id="does-not-exist")["status"],
            "MISSING",
        )

    def test_scale_plan_uses_total_assigned_jobs_not_lifecycle_event_count(self):
        class_id = "research-model-dual-public-v1"
        root = self.root(host_max=4, project_max=4)
        controller = model.RunnerClassControllerModel(self.controller_policy(class_id))
        cycle = model.ScaleSetCycleModel(controller, root)

        empty_events = cycle.plan_capacity(
            total_assigned_jobs=1,
            lifecycle_events=[],
        )
        many_events = cycle.plan_capacity(
            total_assigned_jobs=1,
            lifecycle_events=[
                {"type": "JobAssigned"},
                {"type": "JobStarted"},
                {"type": "JobCompleted"},
                {"type": "JobCompleted"},
            ],
        )
        self.assertEqual(empty_events.desired_capacity, 1)
        self.assertEqual(many_events.desired_capacity, 1)
        self.assertEqual(empty_events.deficit, many_events.deficit)
        self.assertEqual(empty_events.observed_lifecycle_events, 0)
        self.assertEqual(many_events.observed_lifecycle_events, 4)

    def test_controller_restart_with_assigned_jobs_needs_no_job_command_reconstruction(self):
        class_id = "workspace-control-control-small-v1"
        root = self.root()
        controller = model.RunnerClassControllerModel(self.controller_policy(class_id))
        cycle = model.ScaleSetCycleModel(controller, root)

        plan = cycle.plan_capacity(
            total_assigned_jobs=1,
            lifecycle_events=[{"type": "JobAssigned", "job_display_name": "unparseable"}],
        )
        self.assertEqual(plan.desired_capacity, 1)
        self.assertEqual(plan.live_or_reserved_capacity, 0)
        self.assertEqual(plan.deficit, 1)

    def test_live_reserved_capacity_satisfies_desired_count(self):
        class_id = "workspace-control-control-small-v1"
        root = self.root()
        controller = model.RunnerClassControllerModel(self.controller_policy(class_id))
        cycle = model.ScaleSetCycleModel(controller, root)
        root.reserve(
            peer_user=self.peer(class_id),
            request_id="req-reserved-capacity",
            runner_name=self.runner_name(class_id, "reserved"),
        )
        plan = cycle.plan_capacity(total_assigned_jobs=1)
        self.assertEqual(plan.live_or_reserved_capacity, 1)
        self.assertEqual(plan.deficit, 0)

    def test_trusted_and_untrusted_available_jobs_can_coexist_without_parser_failure(self):
        class_id = "workspace-control-control-small-v1"
        policy = self.controller_policy(class_id)
        workflow = policy["trusted_workflows"][0]
        controller = model.RunnerClassControllerModel(policy)
        cycle = model.ScaleSetCycleModel(controller, self.root())

        trusted = self.trusted_job(class_id, workflow, request_id=501)
        untrusted = self.trusted_job(class_id, workflow, request_id=502)
        untrusted["workflow_blob_sha"] = "0" * 40
        result = cycle.evaluate_available_jobs([untrusted, trusted])
        self.assertEqual(result["acquire_runner_request_ids"], [501])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0].runner_request_id, 502)

    def test_job_available_redelivery_is_idempotent(self):
        class_id = "workspace-control-control-small-v1"
        policy = self.controller_policy(class_id)
        workflow = policy["trusted_workflows"][0]
        controller = model.RunnerClassControllerModel(policy)
        cycle = model.ScaleSetCycleModel(controller, self.root())
        job = self.trusted_job(class_id, workflow, request_id=601)

        first = cycle.evaluate_available_jobs([job])
        redelivery_before_acquire = cycle.evaluate_available_jobs([job])
        self.assertEqual(first["acquire_runner_request_ids"], [601])
        self.assertEqual(redelivery_before_acquire["acquire_runner_request_ids"], [])

        cycle.mark_acquired([601])
        redelivery_after_acquire = cycle.evaluate_available_jobs([job])
        self.assertEqual(redelivery_after_acquire["acquire_runner_request_ids"], [])

    def test_canceled_assignment_releases_request_dedupe_for_requeue(self):
        class_id = "workspace-control-control-small-v1"
        policy = self.controller_policy(class_id)
        workflow = policy["trusted_workflows"][0]
        controller = model.RunnerClassControllerModel(policy)
        cycle = model.ScaleSetCycleModel(controller, self.root())
        job = self.trusted_job(class_id, workflow, request_id=603)

        first = cycle.evaluate_available_jobs([job])
        self.assertEqual(first["acquire_runner_request_ids"], [603])
        cycle.mark_acquired([603])
        self.assertIn(603, cycle.acquired_ids)

        cycle.complete_scheduler_attempt(
            runner_request_id=603,
            result="canceled",
        )
        self.assertNotIn(603, cycle.acquired_ids)

        # If GitHub reuses the request id, we are still safe; if it issues a
        # new id, this behavior is equivalent.
        requeued = cycle.evaluate_available_jobs([job])
        self.assertEqual(requeued["acquire_runner_request_ids"], [603])

    def test_anomalous_job_redelivery_is_bounded_and_deduplicated_in_state(self):
        class_id = "workspace-control-control-small-v1"
        policy = self.controller_policy(class_id)
        workflow = policy["trusted_workflows"][0]
        controller = model.RunnerClassControllerModel(policy)
        cycle = model.ScaleSetCycleModel(controller, self.root())
        job = self.trusted_job(class_id, workflow, request_id=602)
        job["actor_login"] = "attacker"

        for _ in range(10):
            result = cycle.evaluate_available_jobs([job])
            self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(len(cycle.anomalies), 1)
        self.assertIn(602, cycle.anomalies)

    def test_request_local_and_capacity_local_outcomes_never_request_process_exit(self):
        supervisor = model.ControllerSupervisorModel()
        outcomes = [
            "ANOMALOUS_UNTRUSTED_JOB",
            "DUPLICATE_TERMINAL_LOCAL_STATE",
            "BUSY",
            "CLASS_QUARANTINED",
            "RESERVATION_EXPIRED",
        ] * 20
        for outcome in outcomes:
            result = supervisor.handle(outcome)
            self.assertTrue(result.acknowledge_message)
            self.assertFalse(result.process_exit)
            self.assertEqual(supervisor.state, "SESSION_ACTIVE")
        self.assertEqual(supervisor.systemd_restart_count, 0)

    def test_transient_failures_use_in_process_exponential_backoff(self):
        supervisor = model.ControllerSupervisorModel(max_backoff_seconds=8)
        expected = [1, 2, 4, 8, 8]
        for seconds in expected:
            result = supervisor.handle("ROOT_SOCKET_TRANSIENT")
            self.assertEqual(result.state, "RETRY_BACKOFF")
            self.assertFalse(result.acknowledge_message)
            self.assertFalse(result.process_exit)
            self.assertEqual(result.backoff_seconds, seconds)
            self.assertEqual(supervisor.systemd_restart_count, 0)
            supervisor.resume_after_backoff()
        self.assertEqual(supervisor.state, "SESSION_ACTIVE")

    def test_successful_session_work_resets_retry_backoff_sequence(self):
        supervisor = model.ControllerSupervisorModel(max_backoff_seconds=8)
        first = supervisor.handle("GITHUB_REST_TRANSIENT")
        self.assertEqual(first.backoff_seconds, 1)
        supervisor.resume_after_backoff()
        second = supervisor.handle("GITHUB_REST_TRANSIENT")
        self.assertEqual(second.backoff_seconds, 2)
        supervisor.resume_after_backoff()
        supervisor.note_successful_session_work()
        reset = supervisor.handle("GITHUB_REST_TRANSIENT")
        self.assertEqual(reset.backoff_seconds, 1)

    def test_only_fatal_configuration_or_corruption_requests_process_exit(self):
        for fatal in model.ControllerSupervisorModel.FATAL:
            supervisor = model.ControllerSupervisorModel()
            result = supervisor.handle(fatal)
            self.assertEqual(result.state, "FATAL")
            self.assertTrue(result.process_exit)
            self.assertFalse(result.acknowledge_message)
            self.assertEqual(supervisor.systemd_restart_count, 1)

    def test_unknown_supervisor_outcome_is_protocol_fatal(self):
        supervisor = model.ControllerSupervisorModel()
        with self.assertRaises(model.ProtocolFatal):
            supervisor.handle("SOMETHING_IMPLICIT_AND_UNMODELED")

    def test_same_request_status_from_wrong_class_is_fatal(self):
        root = self.root(host_max=4, project_max=4)
        a = "workspace-control-control-small-v1"
        b = "padataset-cpu-public-v1"
        root.reserve(
            peer_user=self.peer(a),
            request_id="req-private",
            runner_name=self.runner_name(a, "private"),
        )
        with self.assertRaisesRegex(model.ProtocolFatal, "another runner class"):
            root.status(peer_user=self.peer(b), request_id="req-private")


if __name__ == "__main__":
    unittest.main()
