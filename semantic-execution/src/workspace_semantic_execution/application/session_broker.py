"""Persistent/session-scoped executor session broker.

A session is a replaceable cache. Correctness comes from durable typed work
state and deterministic packets, never transcript continuity.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..domain import (
    ExecutorProfile,
    ExecutorSession,
    ExecutorSessionState,
    SessionMode,
)
from .runtime import RuntimeCoordinator


class SessionBrokerError(RuntimeError):
    """Fail-closed session-broker contract error."""


@dataclass(frozen=True)
class SessionBinding:
    slot_id: str
    session_generation: int
    session_id: str
    executor_id: str
    process_id: str
    process_generation: int
    packet_sha256: str


class PersistentExecutorSessionBroker:
    def __init__(self, runtime: RuntimeCoordinator) -> None:
        self._runtime = runtime

    @staticmethod
    def _uses_session(profile: ExecutorProfile) -> bool:
        return profile.session_mode in {
            SessionMode.PERSISTENT_CHAT,
            SessionMode.SESSION_SCOPED,
        }

    def get(self, slot_id: str) -> ExecutorSession:
        try:
            return self._runtime.snapshot().graph.executor_sessions[slot_id]
        except KeyError as exc:
            raise SessionBrokerError(f"unknown_session_slot:{slot_id}") from exc

    def ensure_session(
        self,
        *,
        profile: ExecutorProfile,
        slot_id: str,
        session_id: str,
    ) -> ExecutorSession | None:
        if profile.session_mode in {SessionMode.NONE, SessionMode.STATELESS}:
            return None
        if not self._uses_session(profile):
            raise SessionBrokerError(
                f"unsupported_session_mode:{profile.session_mode}"
            )
        existing = self._runtime.snapshot().graph.executor_sessions.get(slot_id)
        if existing is None:
            snapshot = self._runtime.register_executor_session(
                slot_id=slot_id,
                executor_id=profile.executor_id,
                session_id=session_id,
            )
            return snapshot.graph.executor_sessions[slot_id]
        if existing.executor_id != profile.executor_id:
            raise SessionBrokerError("session_executor_mismatch")
        if existing.state == ExecutorSessionState.NEEDS_REPLACEMENT:
            raise SessionBrokerError("session_requires_explicit_replacement")
        if existing.state == ExecutorSessionState.RETIRED:
            raise SessionBrokerError("session_retired")
        return existing

    def bind(
        self,
        *,
        profile: ExecutorProfile,
        slot_id: str,
        expected_session_generation: int,
        process_id: str,
        process_generation: int,
        packet_sha256: str,
    ) -> SessionBinding:
        if not self._uses_session(profile):
            raise SessionBrokerError("executor_does_not_use_session")
        session = self.get(slot_id)
        if session.executor_id != profile.executor_id:
            raise SessionBrokerError("session_executor_mismatch")
        snapshot = self._runtime.bind_executor_session(
            slot_id=slot_id,
            expected_session_generation=expected_session_generation,
            process_id=process_id,
            process_generation=process_generation,
            packet_sha256=packet_sha256,
        )
        bound = snapshot.graph.executor_sessions[slot_id]
        if bound.session_id is None:
            raise SessionBrokerError("bound_session_missing_id")
        return SessionBinding(
            slot_id=slot_id,
            session_generation=bound.session_generation,
            session_id=bound.session_id,
            executor_id=bound.executor_id,
            process_id=process_id,
            process_generation=process_generation,
            packet_sha256=packet_sha256,
        )

    def acknowledge(
        self,
        *,
        slot_id: str,
        expected_session_generation: int,
        process_id: str,
        process_generation: int,
        ack_id: str,
    ) -> ExecutorSession:
        snapshot = self._runtime.acknowledge_executor_session(
            slot_id=slot_id,
            expected_session_generation=expected_session_generation,
            process_id=process_id,
            process_generation=process_generation,
            ack_id=ack_id,
        )
        return snapshot.graph.executor_sessions[slot_id]

    def invalidate(
        self,
        *,
        slot_id: str,
        expected_session_generation: int,
        reason: str,
    ) -> ExecutorSession:
        snapshot = self._runtime.invalidate_executor_session(
            slot_id=slot_id,
            expected_session_generation=expected_session_generation,
            reason=reason,
        )
        return snapshot.graph.executor_sessions[slot_id]

    def replace(
        self,
        *,
        slot_id: str,
        expected_session_generation: int,
        session_id: str,
    ) -> ExecutorSession:
        snapshot = self._runtime.replace_executor_session(
            slot_id=slot_id,
            expected_session_generation=expected_session_generation,
            session_id=session_id,
        )
        return snapshot.graph.executor_sessions[slot_id]
