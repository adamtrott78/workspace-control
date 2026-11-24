"""Exact-source candidate adapter for worker result publications."""
from __future__ import annotations

from dataclasses import dataclass
import re

from ..application.worker_results import (
    WorkerResultIntakeOutcome,
    WorkerResultIntakeService,
)
from .worker_result_json import parse_worker_result_json


_IMMUTABLE_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class ImmutableWorkerResultCandidate:
    target_ref: str
    immutable_revision: str
    raw_bytes: bytes

    @property
    def source_ref(self) -> str:
        return f"{self.target_ref}@{self.immutable_revision}"


class WorkerResultCandidateAdapter:
    """Bind immutable candidate bytes to a source ref, then ingest them."""

    def __init__(
        self,
        *,
        intake: WorkerResultIntakeService,
    ) -> None:
        self._intake = intake

    def ingest(
        self,
        candidate: ImmutableWorkerResultCandidate,
    ) -> WorkerResultIntakeOutcome:
        if (
            not candidate.target_ref.startswith(
                "github-candidate://"
            )
            or ".." in candidate.target_ref
            or "?" in candidate.target_ref
            or "#" in candidate.target_ref
        ):
            raise ValueError("worker_result_candidate_target_invalid")
        if not _IMMUTABLE_GIT_SHA_RE.fullmatch(
            candidate.immutable_revision
        ):
            raise ValueError(
                "worker_result_candidate_revision_not_immutable"
            )
        publication = parse_worker_result_json(
            candidate.raw_bytes,
            source_ref=candidate.source_ref,
        )
        return self._intake.ingest(publication)
