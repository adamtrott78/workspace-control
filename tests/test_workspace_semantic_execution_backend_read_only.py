"""Read-only repository effect executor and postcondition tests."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    FakeClock,
    ReadOnlyRepositoryExecutor,
    RepositoryReadContractError,
    RepositoryReadPostconditionValidator,
    StaticRepositoryReader,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    ActionSpec,
    DomainKernel,
    ExecutorAvailability,
    ExecutorLifecycle,
    ExecutorLocality,
    ExecutorProfile,
    InvocationMode,
    MemoryResetPolicy,
    PrivacyClass,
    ProcessState,
    SessionMode,
)
from workspace_semantic_execution.ports import (  # noqa: E402
    RepositoryFileObservation,
    RepositoryReadRequest,
)


SHA = "1" * 40
TARGET = f"repo://adamtrott78/research-engine@{SHA}/src/research_engine/orchestration.py"


def profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="repo-read-only",
        provider_id="repository-port",
        model_id="none",
        surface_id="machine",
        harness_id="exact-repository-read-v1",
        toolset_id="repository-read-only",
        capabilities=frozenset({"repository.read_exact"}),
        invocation_mode=InvocationMode.DETERMINISTIC,
        session_mode=SessionMode.NONE,
        lifecycle=ExecutorLifecycle.DETERMINISTIC_PROCESS,
        memory_reset_policy=MemoryResetPolicy.NONE,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.PROVIDER_REMOTE,
        privacy_classes=frozenset({PrivacyClass.PUBLIC, PrivacyClass.INTERNAL}),
        resource_classes=frozenset({"CPU"}),
        scarcity_rank=0,
    )


def action(*, generation: int = 0) -> ActionSpec:
    return ActionSpec(
        action_id="read:research-engine-orchestration",
        process_id="shadow:research-engine",
        process_generation=generation,
        target_ref=TARGET,
        executor_type="REPOSITORY_READ_ONLY",
        authority_decision_id="authority:read-only",
        authority_scope_ref="scope:research-engine-read",
        idempotency_key="read:research-engine-orchestration:v1",
        preconditions=("immutable_revision_required",),
        expected_effect="observe exact repository file bytes",
        postcondition_validator="repository-read-exact-source-v1",
    )


def observation(*, content: bytes = b"real workflow bytes") -> RepositoryFileObservation:
    return RepositoryFileObservation(
        repository="adamtrott78/research-engine",
        revision=SHA,
        path="src/research_engine/orchestration.py",
        blob_id="blob:exact",
        content=content,
    )


class MutableReader:
    def __init__(self, first, second):
        self._items = [first, second]
        self._index = 0

    def read_exact(self, request: RepositoryReadRequest):
        item = self._items[min(self._index, len(self._items) - 1)]
        self._index += 1
        return item


class ReadOnlyRepositoryExecutorTests(unittest.TestCase):
    def test_exact_read_produces_receipt_bound_to_action_generation(self):
        reader = StaticRepositoryReader((observation(),))
        clock = FakeClock(seconds=7)
        executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)

        receipt = executor.execute(action(generation=3), executor=profile())

        self.assertEqual(receipt.action_id, action().action_id)
        self.assertEqual(receipt.target_ref, TARGET)
        self.assertEqual(receipt.generation, 3)
        self.assertEqual(receipt.executor_id, "repo-read-only")
        self.assertEqual(reader.read_count, 1)
        self.assertEqual(len(executor.observations), 1)

    def test_validator_performs_independent_reread(self):
        reader = StaticRepositoryReader((observation(),))
        clock = FakeClock()
        executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)
        validator = RepositoryReadPostconditionValidator(
            reader=reader,
            clock=clock,
        )

        receipt = executor.execute(action(), executor=profile())
        self.assertEqual(reader.read_count, 1)
        verdict = validator.validate(action(), receipt)

        self.assertTrue(verdict.passed)
        self.assertEqual(
            verdict.validator_id,
            "repository-read-exact-source-v1",
        )
        self.assertEqual(reader.read_count, 2)
        self.assertIn(SHA, verdict.evidence_ref)
        self.assertIn("blob=blob:exact", verdict.evidence_ref)

    def test_changed_bytes_between_effect_and_validation_fail(self):
        reader = MutableReader(
            observation(content=b"first"),
            observation(content=b"second"),
        )
        clock = FakeClock()
        executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)
        validator = RepositoryReadPostconditionValidator(
            reader=reader,
            clock=clock,
        )

        receipt = executor.execute(action(), executor=profile())
        verdict = validator.validate(action(), receipt)

        self.assertFalse(verdict.passed)

    def test_wrong_source_identity_from_reader_fails_closed(self):
        wrong = replace(observation(), revision="2" * 40)
        reader = StaticRepositoryReader((wrong,))

        class WrongReader:
            def read_exact(self, request):
                return wrong

        executor = ReadOnlyRepositoryExecutor(
            reader=WrongReader(),
            clock=FakeClock(),
        )
        with self.assertRaises(RepositoryReadContractError):
            executor.execute(action(), executor=profile())

    def test_nonimmutable_target_is_rejected(self):
        bad = replace(
            action(),
            target_ref=(
                "repo://adamtrott78/research-engine@main/"
                "src/research_engine/orchestration.py"
            ),
        )
        executor = ReadOnlyRepositoryExecutor(
            reader=StaticRepositoryReader((observation(),)),
            clock=FakeClock(),
        )
        with self.assertRaises(RepositoryReadContractError):
            executor.execute(bad, executor=profile())

    def test_path_traversal_is_rejected(self):
        bad = replace(
            action(),
            target_ref=(
                f"repo://adamtrott78/research-engine@{SHA}/"
                "../secrets"
            ),
        )
        executor = ReadOnlyRepositoryExecutor(
            reader=StaticRepositoryReader((observation(),)),
            clock=FakeClock(),
        )
        with self.assertRaises(RepositoryReadContractError):
            executor.execute(bad, executor=profile())

    def test_receipt_plus_independent_validation_is_required_for_completion(self):
        reader = StaticRepositoryReader((observation(),))
        clock = FakeClock()
        executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)
        validator = RepositoryReadPostconditionValidator(
            reader=reader,
            clock=clock,
        )

        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("shadow:research-engine")]
        )
        graph = DomainKernel.claim(
            graph,
            "shadow:research-engine",
            worker_id="read-worker",
            lease_id="read-lease",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "shadow:research-engine",
            lease_id="read-lease",
            expected_generation=0,
        )

        receipt = executor.execute(action(), executor=profile())
        graph = DomainKernel.record_effect(
            graph,
            "shadow:research-engine",
            receipt=receipt,
            lease_id="read-lease",
            expected_generation=0,
        )
        self.assertEqual(
            graph.processes["shadow:research-engine"].state,
            ProcessState.RUNNING,
        )

        graph = DomainKernel.propose_terminal(
            graph,
            "shadow:research-engine",
            lease_id="read-lease",
            expected_generation=0,
        )
        graph = DomainKernel.begin_validation(
            graph,
            "shadow:research-engine",
        )
        verdict = validator.validate(action(), receipt)
        graph = DomainKernel.record_validation(
            graph,
            "shadow:research-engine",
            result=verdict,
        )

        self.assertTrue(verdict.passed)
        self.assertEqual(
            graph.processes["shadow:research-engine"].state,
            ProcessState.COMPLETED,
        )


if __name__ == "__main__":
    unittest.main()
