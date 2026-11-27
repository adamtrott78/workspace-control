"""Provider-neutral read-only repository executor and validator."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re

from ..domain import (
    ActionSpec,
    EffectReceipt,
    ExecutorAvailability,
    ExecutorProfile,
    ValidationResult,
)
from ..ports import (
    ClockPort,
    RepositoryFileObservation,
    RepositoryReadPort,
    RepositoryReadRequest,
)


_TARGET_RE = re.compile(
    r"^repo://(?P<repository>[^@]+)@(?P<revision>[0-9a-f]{40})/"
    r"(?P<path>.+)$"
)


class RepositoryReadContractError(RuntimeError):
    """Fail-closed read-only repository contract error."""


@dataclass(frozen=True)
class ParsedRepositoryTarget:
    repository: str
    revision: str
    path: str


def parse_repository_target(target_ref: str) -> ParsedRepositoryTarget:
    match = _TARGET_RE.fullmatch(target_ref)
    if match is None:
        raise RepositoryReadContractError("invalid_repository_target_ref")
    path = match.group("path")
    if path.startswith("/") or ".." in path.split("/"):
        raise RepositoryReadContractError("unsafe_repository_path")
    return ParsedRepositoryTarget(
        repository=match.group("repository"),
        revision=match.group("revision"),
        path=path,
    )


def observation_effect_hash(
    observation: RepositoryFileObservation,
) -> str:
    content_sha256 = hashlib.sha256(observation.content).hexdigest()
    payload = {
        "repository": observation.repository,
        "revision": observation.revision,
        "path": observation.path,
        "blob_id": observation.blob_id,
        "byte_size": observation.byte_size,
        "content_sha256": content_sha256,
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


class ReadOnlyRepositoryExecutor:
    """ExecutorPort implementation for exact immutable repository reads."""

    EXECUTOR_TYPE = "REPOSITORY_READ_ONLY"

    def __init__(
        self,
        *,
        reader: RepositoryReadPort,
        clock: ClockPort,
    ) -> None:
        self._reader = reader
        self._clock = clock
        self.observations: list[RepositoryFileObservation] = []

    def execute(
        self,
        action: ActionSpec,
        *,
        executor: ExecutorProfile,
    ) -> EffectReceipt:
        if action.executor_type != self.EXECUTOR_TYPE:
            raise RepositoryReadContractError("executor_type_mismatch")
        if executor.availability not in {
            ExecutorAvailability.AVAILABLE,
            ExecutorAvailability.DEGRADED,
        }:
            raise RepositoryReadContractError("executor_not_available")

        target = parse_repository_target(action.target_ref)
        observation = self._reader.read_exact(
            RepositoryReadRequest(
                repository=target.repository,
                revision=target.revision,
                path=target.path,
            )
        )
        self._validate_observation(target, observation)
        self.observations.append(deepcopy(observation))

        return EffectReceipt(
            action_id=action.action_id,
            idempotency_key=action.idempotency_key,
            target_ref=action.target_ref,
            effect_hash=observation_effect_hash(observation),
            executor_id=executor.executor_id,
            generation=action.process_generation,
            observed_at=self._clock.now(),
        )

    @staticmethod
    def _validate_observation(
        target: ParsedRepositoryTarget,
        observation: RepositoryFileObservation,
    ) -> None:
        if (
            observation.repository != target.repository
            or observation.revision != target.revision
            or observation.path != target.path
        ):
            raise RepositoryReadContractError(
                "reader_returned_wrong_source_identity"
            )
        if not observation.blob_id:
            raise RepositoryReadContractError("blob_identity_required")


class RepositoryReadPostconditionValidator:
    """Independent reread validator for a repository read effect."""

    VALIDATOR_ID = "repository-read-exact-source-v1"

    def __init__(
        self,
        *,
        reader: RepositoryReadPort,
        clock: ClockPort,
    ) -> None:
        self._reader = reader
        self._clock = clock

    def validate(
        self,
        action: ActionSpec,
        receipt: EffectReceipt,
    ) -> ValidationResult:
        target = parse_repository_target(action.target_ref)
        reread = self._reader.read_exact(
            RepositoryReadRequest(
                repository=target.repository,
                revision=target.revision,
                path=target.path,
            )
        )

        passed = (
            receipt.action_id == action.action_id
            and receipt.idempotency_key == action.idempotency_key
            and receipt.target_ref == action.target_ref
            and receipt.generation == action.process_generation
            and reread.repository == target.repository
            and reread.revision == target.revision
            and reread.path == target.path
            and bool(reread.blob_id)
            and receipt.effect_hash == observation_effect_hash(reread)
        )
        evidence_ref = (
            f"repo:{reread.repository}@{reread.revision}:"
            f"{reread.path}:blob={reread.blob_id}:"
            f"effect_sha256={observation_effect_hash(reread)}"
        )
        return ValidationResult(
            validator_id=self.VALIDATOR_ID,
            passed=passed,
            evidence_ref=evidence_ref,
            observed_at=self._clock.now(),
        )
