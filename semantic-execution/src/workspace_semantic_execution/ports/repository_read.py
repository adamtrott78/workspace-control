"""Read-only immutable repository observation port."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RepositoryReadRequest:
    repository: str
    revision: str
    path: str


@dataclass(frozen=True)
class RepositoryFileObservation:
    repository: str
    revision: str
    path: str
    blob_id: str
    content: bytes

    @property
    def byte_size(self) -> int:
        return len(self.content)


class RepositoryReadPort(Protocol):
    """Read exact bytes from an immutable repository revision."""

    def read_exact(
        self,
        request: RepositoryReadRequest,
    ) -> RepositoryFileObservation: ...
