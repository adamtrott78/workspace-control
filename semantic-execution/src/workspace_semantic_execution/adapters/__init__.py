"""Infrastructure adapters for Workspace Semantic Execution."""

from .dbos_runtime import DBOSDurableRuntime
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
from .read_only_repository import (
    ReadOnlyRepositoryExecutor,
    RepositoryReadContractError,
    RepositoryReadPostconditionValidator,
    observation_effect_hash,
    parse_repository_target,
)
from .serialization import (
    GraphCodecError,
    decode_work_graph,
    dumps_work_graph,
    encode_work_graph,
    loads_work_graph,
)
from .static_repository_reader import StaticRepositoryReader

__all__ = [
    "DBOSDurableRuntime",
    "DeterministicFakeExecutor",
    "DeterministicSemanticProjection",
    "FakeClock",
    "GraphCodecError",
    "InMemoryDurableRuntime",
    "InMemoryEventLedger",
    "InMemoryStateStore",
    "PostgresEventLedger",
    "PostgresStateStore",
    "ReadOnlyRepositoryExecutor",
    "RecordingTelemetry",
    "RepositoryReadContractError",
    "RepositoryReadPostconditionValidator",
    "StaticAuthorityEvaluator",
    "StaticRepositoryReader",
    "decode_work_graph",
    "dumps_work_graph",
    "encode_work_graph",
    "loads_work_graph",
    "observation_effect_hash",
    "parse_repository_target",
]
