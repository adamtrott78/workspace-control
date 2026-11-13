"""Infrastructure adapters for Workspace Semantic Execution."""

from .in_memory import (
    DeterministicFakeExecutor,
    DeterministicSemanticProjection,
    FakeClock,
    InMemoryDurableRuntime,
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
    StaticAuthorityEvaluator,
)
from .postgres import PostgresEventLedger, PostgresStateStore
from .serialization import (
    GraphCodecError,
    decode_work_graph,
    dumps_work_graph,
    encode_work_graph,
    loads_work_graph,
)

__all__ = [
    "DeterministicFakeExecutor",
    "DeterministicSemanticProjection",
    "FakeClock",
    "GraphCodecError",
    "InMemoryDurableRuntime",
    "InMemoryEventLedger",
    "InMemoryStateStore",
    "PostgresEventLedger",
    "PostgresStateStore",
    "RecordingTelemetry",
    "StaticAuthorityEvaluator",
    "decode_work_graph",
    "dumps_work_graph",
    "encode_work_graph",
    "loads_work_graph",
]
