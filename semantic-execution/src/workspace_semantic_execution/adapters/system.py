"""Minimal production clock/telemetry adapters."""
from __future__ import annotations

from datetime import datetime, timezone

from ..ports import TelemetryRecord


class SystemClock:
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


class NoopTelemetry:
    """Content-free sink for surfaces that do not yet own telemetry export."""

    def record(self, record: TelemetryRecord) -> None:
        return
