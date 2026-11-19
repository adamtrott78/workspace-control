"""Immutable GitHub candidate-source observation and intake."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Protocol

from ..application.production_scheduler import candidate_target_ref
from ..application.runtime import RuntimeCoordinator
from ..application.worker_results import (
    WorkerResultIntakeOutcome,
    WorkerResultIntakeService,
)
from .worker_result_candidate import (
    ImmutableWorkerResultCandidate,
    WorkerResultCandidateAdapter,
)


_IMMUTABLE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class GitHubCandidateError(RuntimeError):
    """Fail-closed immutable candidate-source error."""


@dataclass(frozen=True)
class GitHubCandidateObservation:
    repository: str
    ref: str
    path: str
    commit_sha: str
    content: bytes

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


class GitHubCandidateReaderPort(Protocol):
    """Read one candidate file at an exact immutable Git commit."""

    def read_exact(
        self,
        *,
        repository: str,
        ref: str,
        path: str,
        commit_sha: str,
    ) -> GitHubCandidateObservation: ...


class GitHubCandidateEventService:
    """Event-driven immutable candidate ingestion; never polls consumer UI."""

    def __init__(
        self,
        *,
        runtime: RuntimeCoordinator,
        intake: WorkerResultIntakeService,
        reader: GitHubCandidateReaderPort,
    ) -> None:
        self._runtime = runtime
        self._intake = intake
        self._reader = reader

    def ingest(
        self,
        *,
        dispatch_id: str,
        commit_sha: str,
    ) -> WorkerResultIntakeOutcome:
        if not _IMMUTABLE_COMMIT_RE.fullmatch(commit_sha):
            raise GitHubCandidateError(
                "candidate_commit_sha_invalid"
            )

        graph = self._runtime.snapshot().graph
        spec = graph.scheduler_dispatches.get(dispatch_id)
        if spec is None:
            raise GitHubCandidateError(
                "candidate_dispatch_unknown"
            )
        operator = spec.operator
        if operator is None:
            raise GitHubCandidateError(
                "candidate_dispatch_not_operator"
            )

        observation = self._reader.read_exact(
            repository=operator.candidate_repository,
            ref=operator.candidate_ref,
            path=operator.candidate_path,
            commit_sha=commit_sha,
        )
        expected = (
            operator.candidate_repository,
            operator.candidate_ref,
            operator.candidate_path,
            commit_sha,
        )
        observed = (
            observation.repository,
            observation.ref,
            observation.path,
            observation.commit_sha,
        )
        if observed != expected:
            raise GitHubCandidateError(
                "candidate_observation_binding_mismatch"
            )

        outcome = WorkerResultCandidateAdapter(
            intake=self._intake,
        ).ingest(
            ImmutableWorkerResultCandidate(
                target_ref=candidate_target_ref(operator),
                immutable_revision=commit_sha,
                raw_bytes=observation.content,
            )
        )
        self._runtime.refresh_dependency_waits(
            event_id=(
                "github-candidate:"
                f"{dispatch_id}:{commit_sha}:"
                f"{observation.content_sha256}"
            )
        )
        return outcome
