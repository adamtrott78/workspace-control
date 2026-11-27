"""Deterministic exact-source repository reader for tests/canaries."""
from __future__ import annotations

from copy import deepcopy

from ..ports import (
    RepositoryFileObservation,
    RepositoryReadRequest,
)


class StaticRepositoryReader:
    """Maps exact (repository, revision, path) identities to frozen observations."""

    def __init__(
        self,
        observations: tuple[RepositoryFileObservation, ...],
    ) -> None:
        self._observations = {
            (item.repository, item.revision, item.path): deepcopy(item)
            for item in observations
        }
        if len(self._observations) != len(observations):
            raise ValueError("duplicate_repository_observation_identity")
        self.read_count = 0

    def read_exact(
        self,
        request: RepositoryReadRequest,
    ) -> RepositoryFileObservation:
        self.read_count += 1
        key = (request.repository, request.revision, request.path)
        try:
            return deepcopy(self._observations[key])
        except KeyError as exc:
            raise KeyError(
                "exact_repository_source_not_available:"
                f"{request.repository}@{request.revision}:{request.path}"
            ) from exc
