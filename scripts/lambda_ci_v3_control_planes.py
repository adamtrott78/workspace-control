#!/usr/bin/env python3
"""Pure models for Lambda CI v3 maintenance and reconciliation planes."""

from __future__ import annotations

import copy
import dataclasses
from typing import Any


class PlaneError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class MaintenanceResult:
    status: str
    operation: str
    runner_class_id: str
    authority: str
    mutated: bool
    detail: dict[str, Any]


class MaintenancePlaneModel:
    """Typed maintenance operations over deployment state.

    Raw slash commands are intentionally absent. The unprivileged ingress
    controller is assumed to have parsed one generated executor action into
    these typed operations before this model is invoked.
    """

    READ_ONLY = {
        "DIAGNOSE_RUNNER_CLASS",
        "HOST_ATTEST_RUNNER_CLASS",
    }

    def __init__(
        self,
        *,
        root_projection: dict[str, Any],
        overlay: dict[str, Any],
        class_quarantine_receipts: dict[str, str] | None = None,
    ) -> None:
        self.root_projection = copy.deepcopy(root_projection)
        self.overlay = copy.deepcopy(overlay)
        self.class_quarantine_receipts = dict(class_quarantine_receipts or {})

    def _class(self, runner_class_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self.root_projection["runner_classes"].get(runner_class_id)
        state = self.overlay["classes"].get(runner_class_id)
        if policy is None or state is None:
            raise PlaneError("UNKNOWN_RUNNER_CLASS")
        return policy, state

    def execute(
        self,
        *,
        operation: str,
        runner_class_id: str,
        quarantine_receipt_id: str | None = None,
    ) -> MaintenanceResult:
        policy, state = self._class(runner_class_id)

        if operation == "DIAGNOSE_RUNNER_CLASS":
            return MaintenanceResult(
                "OK",
                operation,
                runner_class_id,
                "READ_ONLY",
                False,
                {
                    "install_state": state["install_state"],
                    "controller_state": state["controller_state"],
                    "containment_state": state["containment"]["state"],
                    "root_envelope_sha256": policy["root_envelope_sha256"],
                },
            )

        if operation == "HOST_ATTEST_RUNNER_CLASS":
            return MaintenanceResult(
                "OK",
                operation,
                runner_class_id,
                "READ_ONLY",
                False,
                {
                    "controller_peer": copy.deepcopy(policy["controller_peer"]),
                    "runner_prefix": policy["runner_prefix"],
                    "execution_contract_id": policy["execution_contract_id"],
                    "exclusive_resource_claims": copy.deepcopy(
                        policy["exclusive_resource_claims"]
                    ),
                },
            )

        if operation == "RESTART_RUNNER_CLASS_CONTROLLER":
            if state["install_state"] != "INSTALLED":
                return MaintenanceResult(
                    "NOT_INSTALLED",
                    operation,
                    runner_class_id,
                    "CONTROLLER_LIFECYCLE_ONLY",
                    False,
                    {},
                )
            if state["controller_state"] != "ACTIVE":
                return MaintenanceResult(
                    "NOT_ACTIVE",
                    operation,
                    runner_class_id,
                    "CONTROLLER_LIFECYCLE_ONLY",
                    False,
                    {},
                )
            if state["containment"]["state"] != "CLEAR":
                return MaintenanceResult(
                    "CONTAINED",
                    operation,
                    runner_class_id,
                    "CONTROLLER_LIFECYCLE_ONLY",
                    False,
                    {},
                )
            # Restart is lifecycle-preserving: ACTIVE -> ACTIVE. It cannot
            # activate an inactive controller or enable a route.
            return MaintenanceResult(
                "RESTART_AUTHORIZED",
                operation,
                runner_class_id,
                "CONTROLLER_LIFECYCLE_ONLY",
                False,
                {"controller_state": "ACTIVE"},
            )

        if operation == "RESET_STALE_RUNNER_CLASS":
            expected = self.class_quarantine_receipts.get(runner_class_id)
            if expected is None:
                return MaintenanceResult(
                    "NO_CLASS_QUARANTINE_RECEIPT",
                    operation,
                    runner_class_id,
                    "RECOVERY_RECEIPT_REQUIRED",
                    False,
                    {},
                )
            if quarantine_receipt_id != expected:
                return MaintenanceResult(
                    "QUARANTINE_RECEIPT_MISMATCH",
                    operation,
                    runner_class_id,
                    "RECOVERY_RECEIPT_REQUIRED",
                    False,
                    {},
                )
            if state["containment"]["state"] != "CLASS_QUARANTINED":
                return MaintenanceResult(
                    "CLASS_NOT_QUARANTINED",
                    operation,
                    runner_class_id,
                    "RECOVERY_RECEIPT_REQUIRED",
                    False,
                    {},
                )
            # This model intentionally does not reactivate controller/routes.
            state["containment"] = {
                "state": "CLEAR",
                "source": f"cleared by exact quarantine receipt {expected}",
            }
            return MaintenanceResult(
                "CONTAINMENT_CLEARED",
                operation,
                runner_class_id,
                "RECOVERY_RECEIPT_REQUIRED",
                True,
                {
                    "controller_state": state["controller_state"],
                    "routes_unchanged": True,
                },
            )

        raise PlaneError(f"UNKNOWN_MAINTENANCE_OPERATION:{operation}")


class ReconciliationPlaneModel:
    """Atomic policy-install model with no activation authority."""

    def __init__(
        self,
        *,
        compiled: dict[str, Any],
        overlay: dict[str, Any],
    ) -> None:
        self.compiled = copy.deepcopy(compiled)
        self.overlay = copy.deepcopy(overlay)

    def install_generation(
        self,
        *,
        runner_class_ids: list[str] | None = None,
        fault_after: int | None = None,
    ) -> dict[str, Any]:
        target = copy.deepcopy(self.overlay)
        classes = sorted(
            runner_class_ids
            if runner_class_ids is not None
            else self.compiled["root_projection"]["runner_classes"].keys()
        )
        known = set(self.compiled["root_projection"]["runner_classes"])
        unknown = sorted(set(classes) - known)
        if unknown:
            raise PlaneError(f"UNKNOWN_RUNNER_CLASSES:{unknown}")

        # Generation binding is policy deployment only.
        target["catalog_generation_sha256"] = self.compiled[
            "catalog_generation_sha256"
        ]

        completed = 0
        for class_id in classes:
            state = target["classes"][class_id]
            state["install_state"] = "INSTALLED"
            # Never activate, drain, clear containment, or alter routes.
            completed += 1
            if fault_after is not None and completed >= fault_after:
                raise PlaneError("SIMULATED_RECONCILIATION_FAILURE")

        return target

    @staticmethod
    def assert_no_activation_delta(
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> None:
        for class_id, prior in before["classes"].items():
            current = after["classes"][class_id]
            if current["controller_state"] != prior["controller_state"]:
                raise PlaneError(f"{class_id}: reconciliation changed controller state")
            if current["containment"] != prior["containment"]:
                raise PlaneError(f"{class_id}: reconciliation changed containment")
        if after["routes"] != before["routes"]:
            raise PlaneError("reconciliation changed route admission state")
        if after["legacy"] != before["legacy"]:
            raise PlaneError("reconciliation changed legacy containment/retirement state")
