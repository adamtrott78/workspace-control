"""Provisional PostgreSQL adapters for current state and external events.

These adapters implement validated ports only. They do not contain scheduling,
reasoning, authority, or executor policy.
"""
from __future__ import annotations

import json
from typing import Any

from ..domain import DomainKernel, WorkGraph
from ..ports import (
    RuntimeEvent,
    StateConflict,
    StateNotInitialized,
    StateSnapshot,
)
from .serialization import decode_work_graph, encode_work_graph


_SCHEMA = "workspace_semantic_execution"
_STATE_TABLE = f"{_SCHEMA}.current_state"
_EVENT_TABLE = f"{_SCHEMA}.external_events"


def _load_psycopg():
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL adapters require psycopg; install the spike dependency "
            "in the dedicated semantic-execution environment."
        ) from exc
    return psycopg


def _decode_jsonb(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        if isinstance(decoded, dict):
            return decoded
    raise RuntimeError("unexpected_graph_jsonb_value")


class _PostgresBase:
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("postgres_dsn_required")
        self._dsn = dsn
        self._ensure_schema()

    def _connect(self):
        return _load_psycopg().connect(self._dsn)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_STATE_TABLE} (
                        state_key TEXT PRIMARY KEY,
                        version BIGINT NOT NULL CHECK (version >= 0),
                        graph_json JSONB NOT NULL
                    )
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_EVENT_TABLE} (
                        event_seq BIGSERIAL PRIMARY KEY,
                        event_id TEXT NOT NULL UNIQUE,
                        wait_key TEXT NOT NULL,
                        observed_at TEXT NOT NULL,
                        payload_ref TEXT NULL
                    )
                    """
                )
                cur.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS
                    workspace_semantic_execution_events_wait_key_idx
                    ON {_EVENT_TABLE} (wait_key, event_seq)
                    """
                )


class PostgresStateStore(_PostgresBase):
    """Versioned CAS state store backed by one authoritative JSONB snapshot."""

    def __init__(self, dsn: str, *, state_key: str = "control") -> None:
        if not state_key:
            raise ValueError("state_key_required")
        self._state_key = state_key
        super().__init__(dsn)

    def initialize(self, graph: WorkGraph) -> StateSnapshot:
        DomainKernel.validate(graph)
        payload = json.dumps(
            encode_work_graph(graph),
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_STATE_TABLE}
                        (state_key, version, graph_json)
                    VALUES (%s, 0, %s::jsonb)
                    ON CONFLICT (state_key) DO NOTHING
                    RETURNING version, graph_json
                    """,
                    (self._state_key, payload),
                )
                row = cur.fetchone()
                if row is None:
                    raise StateConflict("state_already_initialized")
        return StateSnapshot(
            version=int(row[0]),
            graph=decode_work_graph(_decode_jsonb(row[1])),
        )

    def load(self) -> StateSnapshot:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT version, graph_json
                    FROM {_STATE_TABLE}
                    WHERE state_key = %s
                    """,
                    (self._state_key,),
                )
                row = cur.fetchone()
        if row is None:
            raise StateNotInitialized("state_not_initialized")
        return StateSnapshot(
            version=int(row[0]),
            graph=decode_work_graph(_decode_jsonb(row[1])),
        )

    def compare_and_swap(
        self,
        *,
        expected_version: int,
        graph: WorkGraph,
    ) -> StateSnapshot:
        if expected_version < 0:
            raise ValueError("expected_version_must_be_nonnegative")
        DomainKernel.validate(graph)
        payload = json.dumps(
            encode_work_graph(graph),
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_STATE_TABLE}
                    SET version = version + 1,
                        graph_json = %s::jsonb
                    WHERE state_key = %s
                      AND version = %s
                    RETURNING version, graph_json
                    """,
                    (payload, self._state_key, expected_version),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        f"""
                        SELECT version
                        FROM {_STATE_TABLE}
                        WHERE state_key = %s
                        """,
                        (self._state_key,),
                    )
                    current = cur.fetchone()
                    if current is None:
                        raise StateNotInitialized("state_not_initialized")
                    raise StateConflict(
                        "stale_state_version:"
                        f"expected={expected_version}:current={int(current[0])}"
                    )
        return StateSnapshot(
            version=int(row[0]),
            graph=decode_work_graph(_decode_jsonb(row[1])),
        )


class PostgresEventLedger(_PostgresBase):
    """Immutable external wake-event evidence in PostgreSQL."""

    def publish_event(self, event: RuntimeEvent) -> bool:
        if not event.event_id or not event.wait_key or not event.observed_at:
            raise ValueError("runtime_event_required_fields")

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_EVENT_TABLE}
                        (event_id, wait_key, observed_at, payload_ref)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    RETURNING event_id
                    """,
                    (
                        event.event_id,
                        event.wait_key,
                        event.observed_at,
                        event.payload_ref,
                    ),
                )
                inserted = cur.fetchone()
                if inserted is not None:
                    return True

                cur.execute(
                    f"""
                    SELECT wait_key, observed_at, payload_ref
                    FROM {_EVENT_TABLE}
                    WHERE event_id = %s
                    """,
                    (event.event_id,),
                )
                row = cur.fetchone()

        if row is None:
            raise RuntimeError("event_conflict_without_existing_row")
        existing = RuntimeEvent(
            event_id=event.event_id,
            wait_key=str(row[0]),
            observed_at=str(row[1]),
            payload_ref=row[2],
        )
        if existing != event:
            raise ValueError("conflicting_duplicate_runtime_event")
        return False

    def find_event(self, *, wait_key: str) -> RuntimeEvent | None:
        if not wait_key:
            raise ValueError("wait_key_required")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT event_id, wait_key, observed_at, payload_ref
                    FROM {_EVENT_TABLE}
                    WHERE wait_key = %s
                    ORDER BY event_seq ASC
                    LIMIT 1
                    """,
                    (wait_key,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return RuntimeEvent(
            event_id=str(row[0]),
            wait_key=str(row[1]),
            observed_at=str(row[2]),
            payload_ref=row[3],
        )
