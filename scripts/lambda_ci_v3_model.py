#!/usr/bin/env python3
"""Pure state-machine model for the proposed Lambda CI v3 control plane.

This module is intentionally side-effect free.  It models class-controller
admission and root capacity/resource behavior without GitHub, systemd, sockets,
or Lambda access.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import re
from collections.abc import Callable
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ModelError(RuntimeError):
    pass


class ProtocolFatal(ModelError):
    """Static/protocol corruption that is allowed to terminate a controller."""


@dataclasses.dataclass(frozen=True)
class AdmissionDecision:
    state: str
    runner_request_id: int
    workflow_run_id: int
    reason: str | None = None


@dataclasses.dataclass
class CapacityRecord:
    request_id: str
    peer_user: str
    runner_class_id: str
    project_id: str
    runner_name: str
    state: str
    reserved_resources: tuple[str, ...]
    reservation_expires_at: int | None
    root_policy_sha256: str
    root_envelope_sha256: str
    jit_sha256: str | None = None
    unit_name: str | None = None
    unit_created: bool = False
    cleanup_verified: bool = False
    failure_reason: str | None = None


class RunnerClassControllerModel:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = copy.deepcopy(policy)
        self.runner_class_id = policy["runner_class_id"]
        self.repository = policy["repository"]
        self.scale_set_name = policy["scale_set_name"]
        self.max_runners = int(policy["max_runners"])
        self.workflows = {
            item["path"]: copy.deepcopy(item)
            for item in policy["trusted_workflows"]
        }
        if len(self.workflows) != len(policy["trusted_workflows"]):
            raise ProtocolFatal("duplicate trusted workflow path")

    @staticmethod
    def _workflow_path_from_ref(value: str) -> tuple[str, str]:
        if "@" not in value:
            raise ValueError("workflow ref missing @")
        base, ref = value.rsplit("@", 1)
        marker = "/.github/workflows/"
        if marker not in base:
            raise ValueError("workflow ref path invalid")
        path = ".github/workflows/" + base.split(marker, 1)[1]
        return path, ref

    def attest_job(self, job: dict[str, Any]) -> AdmissionDecision:
        runner_request_id = int(job.get("runner_request_id", 0))
        workflow_run_id = int(job.get("workflow_run_id", 0))
        if runner_request_id <= 0 or workflow_run_id <= 0:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "missing scheduler identity",
            )

        if job.get("repository") != self.repository:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "repository mismatch",
            )

        labels = job.get("request_labels")
        if not isinstance(labels, list) or self.scale_set_name not in labels:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "runner class label mismatch",
            )

        try:
            path, ref = self._workflow_path_from_ref(str(job.get("job_workflow_ref", "")))
        except ValueError as exc:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                str(exc),
            )
        workflow = self.workflows.get(path)
        if workflow is None:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "workflow path is not allowlisted for runner class",
            )
        if ref != f"refs/heads/{workflow['default_branch']}":
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "workflow ref is not trusted default branch",
            )

        if job.get("event_name") not in workflow["allowed_events"]:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "event is not allowed",
            )
        if job.get("actor_login") not in workflow["allowed_actor_logins"]:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "actor is not allowed",
            )
        if job.get("triggering_actor_login") not in workflow["allowed_actor_logins"]:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "triggering actor is not allowed",
            )
        if job.get("workflow_blob_sha") != workflow["blob_sha"]:
            return AdmissionDecision(
                "ANOMALOUS_UNTRUSTED",
                runner_request_id,
                workflow_run_id,
                "trusted workflow blob mismatch",
            )

        # Deliberately ignore JobDisplayName, candidate SHA, PR number, and
        # workflow-local parameters.  They are not infrastructure authority.
        return AdmissionDecision(
            "TRUSTED",
            runner_request_id,
            workflow_run_id,
        )

    def desired_capacity(self, total_assigned_jobs: int) -> int:
        if not isinstance(total_assigned_jobs, int) or total_assigned_jobs < 0:
            raise ProtocolFatal("TotalAssignedJobs must be nonnegative integer")
        return min(self.max_runners, total_assigned_jobs)

    @staticmethod
    def scale_result_for_admission(decision: AdmissionDecision) -> str:
        if decision.state == "TRUSTED":
            return "ACQUIRE"
        if decision.state == "ANOMALOUS_UNTRUSTED":
            return "ACK_ANOMALY_KEEP_PROCESS_ALIVE"
        raise ProtocolFatal(f"unknown admission state {decision.state!r}")

    @staticmethod
    def scale_result_for_capacity(status: str) -> str:
        if status in {"RESERVED", "PREPARING", "ACCEPTED", "FAILED", "DUPLICATE"}:
            return "HANDLED_KEEP_PROCESS_ALIVE"
        if status in {"BUSY", "CLASS_QUARANTINED", "RESERVATION_EXPIRED"}:
            return "CAPACITY_LOCAL_KEEP_PROCESS_ALIVE"
        if status in {"INVALID_REQUEST", "UNAUTHORIZED_PEER"}:
            return "FATAL_PROTOCOL"
        raise ProtocolFatal(f"unknown capacity result {status!r}")


class RootCapacityModel:
    def __init__(
        self,
        root_projection: dict[str, Any],
        *,
        now: int = 0,
    ) -> None:
        self.policy = copy.deepcopy(root_projection)
        self.now = now
        self.records: dict[str, CapacityRecord] = {}
        self.quarantined_classes: set[str] = set()
        self._peer_to_class: dict[str, str] = {}
        self._resources_in_use: dict[str, str] = {}

        root_sha = self.policy["root_policy_sha256"]
        if HEX64.fullmatch(root_sha) is None:
            raise ProtocolFatal("root_policy_sha256 invalid")
        for class_id, cls in self.policy["runner_classes"].items():
            peer = cls["controller_peer"]["unix_user"]
            if peer in self._peer_to_class:
                raise ProtocolFatal("controller peer maps to multiple classes")
            self._peer_to_class[peer] = class_id

    def advance(self, seconds: int) -> None:
        if seconds < 0:
            raise ProtocolFatal("clock cannot go backward")
        self.now += seconds
        self.expire_reservations()

    def _class_for_peer(self, peer_user: str) -> tuple[str, dict[str, Any]]:
        class_id = self._peer_to_class.get(peer_user)
        if class_id is None:
            raise ProtocolFatal("UNAUTHORIZED_PEER")
        return class_id, self.policy["runner_classes"][class_id]

    def _record_for_authorized_peer(
        self,
        peer_user: str,
        request_id: str,
    ) -> CapacityRecord | None:
        class_id, _ = self._class_for_peer(peer_user)
        record = self.records.get(request_id)
        if record is not None and record.runner_class_id != class_id:
            raise ProtocolFatal("request identity belongs to another runner class")
        return record

    def _validate_runner_name(self, cls: dict[str, Any], runner_name: str) -> None:
        prefix = cls["runner_prefix"]
        if not isinstance(runner_name, str) or not runner_name.startswith(prefix):
            raise ProtocolFatal("INVALID_REQUEST: runner-name prefix mismatch")
        suffix = runner_name[len(prefix):]
        if not suffix or len(runner_name) > 128:
            raise ProtocolFatal("INVALID_REQUEST: runner name malformed")
        if re.fullmatch(r"[A-Za-z0-9._-]+", suffix) is None:
            raise ProtocolFatal("INVALID_REQUEST: runner name malformed")

    def _active_records(self) -> list[CapacityRecord]:
        return [
            record
            for record in self.records.values()
            if record.state in {"RESERVED", "PREPARING", "LAUNCHED"}
        ]

    def _can_allocate(self, class_id: str, cls: dict[str, Any]) -> bool:
        active = self._active_records()
        host_max = int(
            self.policy["host_resource_policy"]["migration_mode"]["host_max_active_runners"]
        )
        if len(active) >= host_max:
            return False

        project_id = cls["project_id"]
        project_max = int(cls["project_max_active_runners"])
        if sum(item.project_id == project_id for item in active) >= project_max:
            return False

        class_max = int(cls["max_runners"])
        if sum(item.runner_class_id == class_id for item in active) >= class_max:
            return False

        for resource in cls["exclusive_resource_claims"]:
            if resource in self._resources_in_use:
                return False
        return True

    def _reserve_resources(self, request_id: str, cls: dict[str, Any]) -> tuple[str, ...]:
        resources = tuple(cls["exclusive_resource_claims"])
        if any(resource in self._resources_in_use for resource in resources):
            raise ProtocolFatal("allocator violated atomic preflight")
        for resource in resources:
            self._resources_in_use[resource] = request_id
        return resources

    def _release_resources(self, record: CapacityRecord) -> None:
        for resource in record.reserved_resources:
            owner = self._resources_in_use.get(resource)
            if owner == record.request_id:
                del self._resources_in_use[resource]

    def reserve(
        self,
        *,
        peer_user: str,
        request_id: str,
        runner_name: str,
    ) -> dict[str, Any]:
        class_id, cls = self._class_for_peer(peer_user)
        self._validate_runner_name(cls, runner_name)
        existing = self.records.get(request_id)
        if existing is not None:
            if (
                existing.peer_user != peer_user
                or existing.runner_name != runner_name
                or existing.runner_class_id != class_id
            ):
                raise ProtocolFatal("INVALID_REQUEST: replay conflict")
            return {
                "status": "DUPLICATE",
                "request_id": request_id,
                "receipt_status": self.external_status(existing),
                "reservation_expires_at": existing.reservation_expires_at,
            }

        if class_id in self.quarantined_classes:
            return {"status": "CLASS_QUARANTINED", "request_id": request_id}

        self.expire_reservations()
        if not self._can_allocate(class_id, cls):
            return {"status": "BUSY", "request_id": request_id}

        resources = self._reserve_resources(request_id, cls)
        ttl = int(
            self.policy["host_resource_policy"]["reservation_policy"]["ttl_seconds"]
        )
        record = CapacityRecord(
            request_id=request_id,
            peer_user=peer_user,
            runner_class_id=class_id,
            project_id=cls["project_id"],
            runner_name=runner_name,
            state="RESERVED",
            reserved_resources=resources,
            reservation_expires_at=self.now + ttl,
            root_policy_sha256=self.policy["root_policy_sha256"],
            root_envelope_sha256=cls["root_envelope_sha256"],
        )
        self.records[request_id] = record
        return {
            "status": "RESERVED",
            "request_id": request_id,
            "reservation_expires_at": record.reservation_expires_at,
        }

    @staticmethod
    def _unit_name(record: CapacityRecord) -> str:
        digest = hashlib.sha256(record.request_id.encode("ascii")).hexdigest()[:16]
        return f"workspace-ci-v3-{digest}.service"

    def launch(
        self,
        *,
        peer_user: str,
        request_id: str,
        runner_name: str,
        jit_config: str,
        fault: str | None = None,
    ) -> dict[str, Any]:
        record = self._record_for_authorized_peer(peer_user, request_id)
        if record is None:
            raise ProtocolFatal("INVALID_REQUEST: LAUNCH without reservation")
        if runner_name != record.runner_name:
            raise ProtocolFatal("INVALID_REQUEST: runner name differs from reservation")
        if record.state == "LAUNCHED":
            return {
                "status": "DUPLICATE",
                "request_id": request_id,
                "receipt_status": "ACCEPTED",
            }
        if record.state == "EXPIRED":
            return {
                "status": "RESERVATION_EXPIRED",
                "request_id": request_id,
            }
        if record.state in {"COMPLETED", "FAILED", "CANCELED"}:
            return {
                "status": "DUPLICATE",
                "request_id": request_id,
                "receipt_status": self.external_status(record),
            }
        if record.state != "RESERVED":
            raise ProtocolFatal(f"INVALID_REQUEST: cannot LAUNCH from {record.state}")

        if record.reservation_expires_at is None or self.now >= record.reservation_expires_at:
            self._release_resources(record)
            record.state = "CANCELED"
            record.reservation_expires_at = None
            return {"status": "RESERVATION_EXPIRED", "request_id": request_id}

        if not isinstance(jit_config, str) or not jit_config:
            raise ProtocolFatal("INVALID_REQUEST: JIT config required")
        record.jit_sha256 = hashlib.sha256(jit_config.encode("utf-8")).hexdigest()
        record.state = "PREPARING"
        record.unit_name = self._unit_name(record)

        if fault == "crash_before_unit":
            raise ModelError("SIMULATED_ROOT_CRASH_BEFORE_UNIT")

        record.unit_created = True
        if fault == "crash_after_unit":
            raise ModelError("SIMULATED_ROOT_CRASH_AFTER_UNIT")

        record.state = "LAUNCHED"
        record.reservation_expires_at = None
        return {"status": "ACCEPTED", "request_id": request_id}

    def external_status(self, record: CapacityRecord) -> str:
        if record.state == "LAUNCHED":
            return "ACCEPTED"
        if record.state == "EXPIRED":
            return "CANCELED"
        if record.state in {"RESERVED", "COMPLETED", "FAILED", "CANCELED"}:
            return record.state
        if record.state == "PREPARING":
            # PREPARING is reconciled before being externally exposed.
            self.reconcile_startup()
            return self.external_status(record)
        raise ProtocolFatal(f"unsupported root record state {record.state!r}")

    def status(self, *, peer_user: str, request_id: str) -> dict[str, Any]:
        self.expire_reservations()
        record = self._record_for_authorized_peer(peer_user, request_id)
        if record is None:
            return {"status": "MISSING", "request_id": request_id}
        return {
            "status": self.external_status(record),
            "request_id": request_id,
            "runner_name": record.runner_name,
            "reservation_expires_at": record.reservation_expires_at,
        }

    def cancel(self, *, peer_user: str, request_id: str) -> dict[str, Any]:
        record = self._record_for_authorized_peer(peer_user, request_id)
        if record is None:
            return {"status": "MISSING", "request_id": request_id}
        if record.state == "RESERVED":
            self._release_resources(record)
            record.state = "CANCELED"
            record.reservation_expires_at = None
            return {"status": "CANCELED", "request_id": request_id}
        if record.state in {"COMPLETED", "FAILED", "CANCELED", "EXPIRED"}:
            return {"status": "ALREADY_TERMINAL", "request_id": request_id}
        return {"status": "NOT_CANCELABLE", "request_id": request_id}

    def expire_reservations(self) -> None:
        for record in self.records.values():
            if (
                record.state == "RESERVED"
                and record.reservation_expires_at is not None
                and self.now >= record.reservation_expires_at
            ):
                self._release_resources(record)
                record.state = "EXPIRED"
                record.reservation_expires_at = None

    def reconcile_startup(self) -> None:
        self.expire_reservations()
        for record in self.records.values():
            if record.state != "PREPARING":
                continue
            if record.unit_created:
                record.state = "LAUNCHED"
                record.reservation_expires_at = None
            else:
                record.state = "FAILED"
                record.failure_reason = "PREPARING_WITHOUT_SYSTEMD_UNIT"
                record.reservation_expires_at = None
                self._release_resources(record)

    def finish(
        self,
        *,
        request_id: str,
        success: bool,
        cleanup_ok: bool,
    ) -> None:
        record = self.records.get(request_id)
        if record is None or record.state != "LAUNCHED":
            raise ProtocolFatal("finish requires LAUNCHED request")
        if cleanup_ok:
            record.cleanup_verified = True
            record.state = "COMPLETED" if success else "FAILED"
            self._release_resources(record)
            return

        record.failure_reason = "CLEANUP_FAILED"
        self.quarantined_classes.add(record.runner_class_id)
        # Conservatively retain exclusive resources and active record until
        # typed maintenance proves containment and clears the class.

    def clear_quarantine_after_containment(
        self,
        *,
        runner_class_id: str,
        request_id: str,
    ) -> None:
        record = self.records.get(request_id)
        if (
            record is None
            or record.runner_class_id != runner_class_id
            or record.failure_reason != "CLEANUP_FAILED"
        ):
            raise ProtocolFatal("quarantine clearance evidence mismatch")
        record.cleanup_verified = True
        record.state = "FAILED"
        self._release_resources(record)
        self.quarantined_classes.discard(runner_class_id)

    def resource_owner(self, resource: str) -> str | None:
        return self._resources_in_use.get(resource)


class ClassCapacityControllerModel:
    """Controller-side ordering model: RESERVE before JIT, then LAUNCH."""

    def __init__(
        self,
        controller_policy: dict[str, Any],
        root: RootCapacityModel,
        *,
        jit_factory: Callable[[str], str] | None = None,
    ) -> None:
        self.policy = controller_policy
        self.root = root
        self.peer_user = root.policy["runner_classes"][
            controller_policy["runner_class_id"]
        ]["controller_peer"]["unix_user"]
        self.jit_factory = jit_factory or (lambda runner_name: f"jit:{runner_name}")
        self.jit_generation_count = 0

    def provision_one(self, *, request_id: str, runner_name: str) -> str:
        reserve = self.root.reserve(
            peer_user=self.peer_user,
            request_id=request_id,
            runner_name=runner_name,
        )
        status = reserve["status"]
        if status != "RESERVED":
            return status

        self.jit_generation_count += 1
        jit = self.jit_factory(runner_name)
        launch = self.root.launch(
            peer_user=self.peer_user,
            request_id=request_id,
            runner_name=runner_name,
            jit_config=jit,
        )
        return launch["status"]



@dataclasses.dataclass(frozen=True)
class ScalePlan:
    total_assigned_jobs: int
    desired_capacity: int
    live_or_reserved_capacity: int
    deficit: int
    surplus: int
    observed_lifecycle_events: int


class ScaleSetCycleModel:
    """Pure scheduler-facing model that uses statistics for capacity, not event counts."""

    def __init__(
        self,
        controller: RunnerClassControllerModel,
        root: RootCapacityModel,
    ) -> None:
        self.controller = controller
        self.root = root
        self.runner_class_id = controller.runner_class_id
        self.pending_acquire_ids: set[int] = set()
        self.acquired_ids: set[int] = set()
        self.anomalies: dict[int, str] = {}

    def evaluate_available_jobs(
        self,
        jobs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        acquire: list[int] = []
        anomalies: list[AdmissionDecision] = []
        for job in jobs:
            decision = self.controller.attest_job(job)
            if decision.state == "TRUSTED":
                request_id = decision.runner_request_id
                if (
                    request_id not in self.pending_acquire_ids
                    and request_id not in self.acquired_ids
                ):
                    self.pending_acquire_ids.add(request_id)
                    acquire.append(request_id)
                continue

            if decision.state == "ANOMALOUS_UNTRUSTED":
                self.anomalies.setdefault(
                    decision.runner_request_id,
                    decision.reason or "untrusted",
                )
                anomalies.append(decision)
                continue
            raise ProtocolFatal(f"unknown admission decision {decision.state!r}")

        return {
            "acquire_runner_request_ids": acquire,
            "anomalies": anomalies,
        }

    def mark_acquired(self, runner_request_ids: list[int]) -> None:
        for request_id in runner_request_ids:
            if request_id in self.pending_acquire_ids:
                self.pending_acquire_ids.remove(request_id)
            self.acquired_ids.add(request_id)

    def complete_scheduler_attempt(
        self,
        *,
        runner_request_id: int,
        result: str,
    ) -> None:
        if runner_request_id <= 0:
            raise ProtocolFatal("completed scheduler attempt requires positive RunnerRequestID")
        self.pending_acquire_ids.discard(runner_request_id)
        self.acquired_ids.discard(runner_request_id)
        # A canceled assignment may later be requeued by GitHub, potentially
        # with new messages for the same workflow job. Local dedupe is scoped
        # only to the current scheduler attempt.
        if result == "canceled":
            self.anomalies.pop(runner_request_id, None)

    def live_or_reserved_capacity(self) -> int:
        return sum(
            record.runner_class_id == self.runner_class_id
            and record.state in {"RESERVED", "PREPARING", "LAUNCHED"}
            for record in self.root.records.values()
        )

    def plan_capacity(
        self,
        *,
        total_assigned_jobs: int,
        lifecycle_events: list[dict[str, Any]] | None = None,
    ) -> ScalePlan:
        # lifecycle_events are evidence only; they are deliberately excluded
        # from desired-capacity arithmetic.
        events = lifecycle_events or []
        desired = self.controller.desired_capacity(total_assigned_jobs)
        live = self.live_or_reserved_capacity()
        return ScalePlan(
            total_assigned_jobs=total_assigned_jobs,
            desired_capacity=desired,
            live_or_reserved_capacity=live,
            deficit=max(0, desired - live),
            surplus=max(0, live - desired),
            observed_lifecycle_events=len(events),
        )


@dataclasses.dataclass(frozen=True)
class SupervisorOutcome:
    state: str
    acknowledge_message: bool
    process_exit: bool
    backoff_seconds: int
    category: str


class ControllerSupervisorModel:
    """Models in-process retry/backoff versus process-fatal failures."""

    REQUEST_LOCAL = {
        "ANOMALOUS_UNTRUSTED_JOB",
        "DUPLICATE_TERMINAL_LOCAL_STATE",
    }
    CAPACITY_LOCAL = {
        "BUSY",
        "CLASS_QUARANTINED",
        "RESERVATION_EXPIRED",
    }
    RETRYABLE = {
        "GITHUB_REST_TRANSIENT",
        "SCALESET_API_TRANSIENT",
        "ROOT_SOCKET_TRANSIENT",
        "JIT_API_TRANSIENT",
    }
    FATAL = {
        "UNKNOWN_CONTROLLER_PEER",
        "RUNNER_CLASS_CATALOG_INVALID",
        "RUNNER_PREFIX_GENERATOR_VIOLATION",
        "DURABLE_LEDGER_CORRUPT",
        "ROOT_RESPONSE_SCHEMA_CORRUPT",
    }

    def __init__(self, *, max_backoff_seconds: int = 60) -> None:
        self.state = "SESSION_ACTIVE"
        self.retry_attempt = 0
        self.max_backoff_seconds = max_backoff_seconds
        self.systemd_restart_count = 0
        self.process_exit_requested = False

    def handle(self, outcome: str) -> SupervisorOutcome:
        if self.state == "FATAL":
            raise ProtocolFatal("supervisor is already fatal")

        if outcome in self.REQUEST_LOCAL:
            self.state = "SESSION_ACTIVE"
            return SupervisorOutcome(
                self.state, True, False, 0, "REQUEST_LOCAL"
            )

        if outcome in self.CAPACITY_LOCAL:
            self.state = "SESSION_ACTIVE"
            return SupervisorOutcome(
                self.state, True, False, 0, "CAPACITY_LOCAL"
            )

        if outcome in self.RETRYABLE:
            self.retry_attempt += 1
            self.state = "RETRY_BACKOFF"
            backoff = min(
                self.max_backoff_seconds,
                2 ** min(self.retry_attempt - 1, 16),
            )
            return SupervisorOutcome(
                self.state, False, False, backoff, "RETRYABLE"
            )

        if outcome in self.FATAL:
            self.state = "FATAL"
            self.process_exit_requested = True
            # A true fatal process exit is where systemd would observe one
            # process failure; request-local outcomes never increment this.
            self.systemd_restart_count += 1
            return SupervisorOutcome(
                self.state, False, True, 0, "FATAL"
            )

        raise ProtocolFatal(f"unknown supervisor outcome {outcome!r}")

    def resume_after_backoff(self) -> None:
        if self.state != "RETRY_BACKOFF":
            raise ProtocolFatal("resume_after_backoff requires RETRY_BACKOFF")
        self.state = "SESSION_ACTIVE"

    def note_successful_session_work(self) -> None:
        if self.state != "SESSION_ACTIVE":
            raise ProtocolFatal("successful work requires SESSION_ACTIVE")
        self.retry_attempt = 0



@dataclasses.dataclass
class ControllerRunnerLedgerRecord:
    request_id: str
    runner_name: str
    runner_class_id: str
    state: str
    reservation_expires_at: int | None = None
    root_status: str | None = None
    jit_runner_id: int | None = None
    jit_sha256: str | None = None


class GitHubJitRegistryModel:
    """Pure model of ephemeral GitHub JIT runner registrations."""

    def __init__(self) -> None:
        self.next_runner_id = 1
        self.registrations: dict[int, dict[str, Any]] = {}

    def generate(self, runner_name: str) -> tuple[int, str]:
        if not isinstance(runner_name, str) or not runner_name:
            raise ProtocolFatal("JIT runner name required")
        runner_id = self.next_runner_id
        self.next_runner_id += 1
        raw = f"jit:{runner_id}:{runner_name}"
        self.registrations[runner_id] = {
            "runner_name": runner_name,
            "state": "REGISTERED",
        }
        return runner_id, raw

    def remove(self, runner_id: int) -> bool:
        record = self.registrations.get(runner_id)
        if record is None:
            return False
        record["state"] = "REMOVED"
        return True

    def mark_consumed(self, runner_id: int) -> None:
        record = self.registrations.get(runner_id)
        if record is None:
            raise ProtocolFatal("unknown JIT runner registration")
        record["state"] = "CONSUMED"

    def state(self, runner_id: int) -> str | None:
        record = self.registrations.get(runner_id)
        return None if record is None else str(record["state"])


class RecoveringClassCapacityControllerModel:
    """Controller ledger model for all crash boundaries around RESERVE/JIT/LAUNCH."""

    def __init__(
        self,
        controller_policy: dict[str, Any],
        root: RootCapacityModel,
        jit_registry: GitHubJitRegistryModel,
    ) -> None:
        self.policy = copy.deepcopy(controller_policy)
        self.runner_class_id = controller_policy["runner_class_id"]
        self.root = root
        self.jit_registry = jit_registry
        self.peer_user = root.policy["runner_classes"][self.runner_class_id][
            "controller_peer"
        ]["unix_user"]
        self.ledger: dict[str, ControllerRunnerLedgerRecord] = {}

    def begin(self, *, request_id: str, runner_name: str) -> ControllerRunnerLedgerRecord:
        if request_id in self.ledger:
            raise ProtocolFatal("runner-instance request already exists in controller ledger")
        record = ControllerRunnerLedgerRecord(
            request_id=request_id,
            runner_name=runner_name,
            runner_class_id=self.runner_class_id,
            state="RESERVING",
        )
        self.ledger[request_id] = record
        return record

    def reserve(self, *, request_id: str) -> str:
        record = self.ledger.get(request_id)
        if record is None:
            raise ProtocolFatal("reserve requires controller ledger entry")
        response = self.root.reserve(
            peer_user=self.peer_user,
            request_id=record.request_id,
            runner_name=record.runner_name,
        )
        status = str(response["status"])
        record.root_status = status
        if status == "RESERVED":
            record.state = "RESERVED"
            record.reservation_expires_at = response["reservation_expires_at"]
        elif status in {"BUSY", "CLASS_QUARANTINED"}:
            record.state = "WAITING_CAPACITY"
        elif status == "DUPLICATE":
            receipt = str(response.get("receipt_status"))
            record.root_status = receipt
            if receipt == "RESERVED":
                record.state = "RESERVED"
                record.reservation_expires_at = response.get("reservation_expires_at")
            elif receipt == "ACCEPTED":
                record.state = "ACCEPTED"
            elif receipt in {"COMPLETED", "FAILED", "CANCELED"}:
                record.state = "TERMINAL"
            else:
                raise ProtocolFatal(f"unknown duplicate reserve receipt {receipt!r}")
        else:
            raise ProtocolFatal(f"unexpected RESERVE status {status!r}")
        return status

    def generate_jit(self, *, request_id: str) -> str:
        record = self.ledger.get(request_id)
        if record is None or record.state != "RESERVED":
            raise ProtocolFatal("JIT generation requires RESERVED controller state")
        root_status = self.root.status(
            peer_user=self.peer_user,
            request_id=request_id,
        )["status"]
        if root_status != "RESERVED":
            raise ProtocolFatal("root reservation is not valid for JIT generation")

        runner_id, raw = self.jit_registry.generate(record.runner_name)
        record.jit_runner_id = runner_id
        record.jit_sha256 = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        record.state = "JIT_REGISTERED"
        # Raw bytes are returned to the caller only and are never stored in the
        # durable ledger model.
        return raw

    def launch(self, *, request_id: str, jit_config: str) -> str:
        record = self.ledger.get(request_id)
        if record is None or record.state != "JIT_REGISTERED":
            raise ProtocolFatal("LAUNCH requires JIT_REGISTERED controller state")
        if hashlib.sha256(jit_config.encode("utf-8")).hexdigest() != record.jit_sha256:
            raise ProtocolFatal("memory-only JIT does not match durable digest")
        response = self.root.launch(
            peer_user=self.peer_user,
            request_id=request_id,
            runner_name=record.runner_name,
            jit_config=jit_config,
        )
        status = str(response["status"])
        record.root_status = status
        if status == "ACCEPTED":
            record.state = "ACCEPTED"
            if record.jit_runner_id is not None:
                self.jit_registry.mark_consumed(record.jit_runner_id)
        elif status == "RESERVATION_EXPIRED":
            self._remove_orphan_jit(record)
            record.state = "NEEDS_NEW_REQUEST"
        elif status == "DUPLICATE":
            receipt = str(response.get("receipt_status"))
            record.root_status = receipt
            if receipt == "ACCEPTED":
                record.state = "ACCEPTED"
            elif receipt in {"COMPLETED", "FAILED", "CANCELED"}:
                self._remove_orphan_jit(record)
                record.state = "TERMINAL"
            else:
                raise ProtocolFatal(f"unknown duplicate launch receipt {receipt!r}")
        else:
            raise ProtocolFatal(f"unexpected LAUNCH status {status!r}")
        return status

    def _remove_orphan_jit(self, record: ControllerRunnerLedgerRecord) -> None:
        if record.jit_runner_id is not None:
            self.jit_registry.remove(record.jit_runner_id)
        record.jit_runner_id = None
        record.jit_sha256 = None

    def recover(self, *, request_id: str) -> str:
        record = self.ledger.get(request_id)
        if record is None:
            raise ProtocolFatal("recover requires controller ledger entry")
        status = str(
            self.root.status(
                peer_user=self.peer_user,
                request_id=request_id,
            )["status"]
        )
        record.root_status = status

        if status == "MISSING":
            self._remove_orphan_jit(record)
            record.state = "RESERVING"
            record.reservation_expires_at = None
            return "RETRY_RESERVE"

        if status == "RESERVED":
            if record.jit_runner_id is not None:
                # Raw JIT bytes are intentionally unrecoverable after a
                # controller crash. Remove the exact orphan registration and
                # generate a new one under the still-valid reservation.
                self._remove_orphan_jit(record)
                record.state = "RESERVED"
                return "REMOVE_ORPHAN_AND_REGENERATE_JIT"
            record.state = "RESERVED"
            return "GENERATE_JIT"

        if status == "ACCEPTED":
            record.state = "ACCEPTED"
            # Do not remove a registration here: the launched runner may still
            # be consuming it after a response-loss crash.
            return "AWAIT_ROOT_OR_GITHUB_TERMINAL"

        if status in {"COMPLETED", "FAILED"}:
            self._remove_orphan_jit(record)
            record.state = "TERMINAL"
            return "TERMINAL"

        if status == "CANCELED":
            self._remove_orphan_jit(record)
            record.state = "NEEDS_NEW_REQUEST"
            return "NEW_REQUEST_REQUIRED"

        raise ProtocolFatal(f"unknown root STATUS result {status!r}")

    def durable_record(self, request_id: str) -> dict[str, Any]:
        record = self.ledger.get(request_id)
        if record is None:
            raise ProtocolFatal("unknown controller ledger request")
        return dataclasses.asdict(record)
