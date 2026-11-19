"""Recursive task-tree, obligation inheritance, and fan-in tests."""
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
    InMemoryEventLedger,
    InMemoryStateStore,
    RecordingTelemetry,
)
from workspace_semantic_execution.application import (  # noqa: E402
    ChildWorkSpec,
    RuntimeCoordinator,
    TaskTreeCoordinator,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    DomainKernel,
    EffectReceipt,
    KernelError,
    ProcessState,
    ValidationResult,
    WorkContract,
    WorkDisposition,
)


ROOT_ID = "research-iterate"
ROOT_CONTRACT = WorkContract(
    objective="Research the objective and synthesize a validated answer.",
    mandatory_constraints=(
        "no write-capable external effects",
        "preserve exact evidence provenance",
    ),
    provenance_refs=("research-engine@1031861",),
    authority_refs=("scope:research-read-only",),
    validator_contracts=("validator:evidence-grounding-v1",),
    output_schema_refs=("schema:research-synthesis-v1",),
)


def runtime_with_root():
    store = InMemoryStateStore()
    runtime = RuntimeCoordinator(
        state_store=store,
        event_ledger=InMemoryEventLedger(),
        telemetry=RecordingTelemetry(),
        clock=FakeClock(),
    )
    runtime.initialize(
        DomainKernel.create_graph(
            [
                DomainKernel.create_process(
                    ROOT_ID,
                    work_contract=ROOT_CONTRACT,
                )
            ]
        )
    )
    return runtime


def start_process(
    runtime: RuntimeCoordinator,
    process_id: str,
    *,
    worker: str,
    lease: str,
):
    process = runtime.snapshot().graph.processes[process_id]
    runtime.claim(
        process_id,
        worker_id=worker,
        lease_id=lease,
        expected_generation=process.generation,
    )
    runtime.start(
        process_id,
        lease_id=lease,
        expected_generation=process.generation,
    )
    return process.generation


def complete_process(
    runtime: RuntimeCoordinator,
    process_id: str,
    *,
    worker: str,
    lease: str,
    action_id: str,
):
    generation = start_process(
        runtime,
        process_id,
        worker=worker,
        lease=lease,
    )
    runtime.classify_work(
        process_id,
        disposition=WorkDisposition.EXECUTABLE,
        reason="bounded leaf or synthesis step",
        lease_id=lease,
        expected_generation=generation,
    )
    runtime.record_effect(
        process_id,
        receipt=EffectReceipt(
            action_id=action_id,
            idempotency_key=f"idem:{action_id}",
            target_ref=f"task:{process_id}",
            effect_hash=f"hash:{action_id}",
            executor_id="executor:test",
            generation=generation,
            observed_at="T1",
        ),
        lease_id=lease,
        expected_generation=generation,
    )
    runtime.propose_terminal(
        process_id,
        lease_id=lease,
        expected_generation=generation,
    )
    runtime.begin_validation(process_id)
    runtime.record_validation(
        process_id,
        result=ValidationResult(
            validator_id="validator:evidence-grounding-v1",
            passed=True,
            evidence_ref=f"evidence:{action_id}",
            observed_at="T2",
        ),
    )


class RecursiveTaskTreeTests(unittest.TestCase):
    def test_two_level_decomposition_inherits_obligations_and_fanin(self):
        runtime = runtime_with_root()
        tree = TaskTreeCoordinator(runtime)

        root_generation = start_process(
            runtime,
            ROOT_ID,
            worker="W-root",
            lease="L-root",
        )
        tree.classify(
            ROOT_ID,
            disposition=WorkDisposition.TOO_LARGE,
            reason="two independent evidence workstreams",
            lease_id="L-root",
            expected_generation=root_generation,
        )
        tree.decompose(
            ROOT_ID,
            lease_id="L-root",
            expected_generation=root_generation,
            children=(
                ChildWorkSpec(
                    process_id="research-iterate.A",
                    objective="Acquire and screen evidence stream A.",
                    mandatory_constraints=("screen before extraction",),
                    provenance_refs=("stream:A",),
                    validator_contracts=("validator:screen-v1",),
                    output_schema_refs=("schema:evidence-stream-v1",),
                ),
                ChildWorkSpec(
                    process_id="research-iterate.B",
                    objective="Acquire and screen evidence stream B.",
                    provenance_refs=("stream:B",),
                ),
            ),
        )

        snapshot = runtime.snapshot()
        root = snapshot.graph.processes[ROOT_ID]
        child_a = snapshot.graph.processes["research-iterate.A"]
        child_b = snapshot.graph.processes["research-iterate.B"]
        self.assertEqual(root.state, ProcessState.WAITING_DEPENDENCIES)
        self.assertEqual(
            root.disposition,
            WorkDisposition.TOO_LARGE,
        )

        for child in (child_a, child_b):
            self.assertIsNotNone(child.work_contract)
            contract = child.work_contract
            assert contract is not None
            self.assertTrue(
                set(ROOT_CONTRACT.mandatory_constraints).issubset(
                    set(contract.mandatory_constraints)
                )
            )
            self.assertTrue(
                set(ROOT_CONTRACT.provenance_refs).issubset(
                    set(contract.provenance_refs)
                )
            )
            self.assertTrue(
                set(ROOT_CONTRACT.authority_refs).issubset(
                    set(contract.authority_refs)
                )
            )
            self.assertTrue(
                set(ROOT_CONTRACT.validator_contracts).issubset(
                    set(contract.validator_contracts)
                )
            )
            self.assertTrue(
                set(ROOT_CONTRACT.output_schema_refs).issubset(
                    set(contract.output_schema_refs)
                )
            )

        self.assertIn(
            "screen before extraction",
            child_a.work_contract.mandatory_constraints,
        )
        self.assertIn(
            "stream:A",
            child_a.work_contract.provenance_refs,
        )

        a_generation = start_process(
            runtime,
            "research-iterate.A",
            worker="W-A",
            lease="L-A",
        )
        tree.classify(
            "research-iterate.A",
            disposition=WorkDisposition.TOO_LARGE,
            reason="stream A still contains two independent bounded leaves",
            lease_id="L-A",
            expected_generation=a_generation,
        )
        tree.decompose(
            "research-iterate.A",
            lease_id="L-A",
            expected_generation=a_generation,
            children=(
                ChildWorkSpec(
                    process_id="research-iterate.A.1",
                    objective="Extract evidence item A1.",
                    provenance_refs=("source:A1",),
                ),
                ChildWorkSpec(
                    process_id="research-iterate.A.2",
                    objective="Extract evidence item A2.",
                    provenance_refs=("source:A2",),
                ),
            ),
        )

        grandchild = runtime.snapshot().graph.processes[
            "research-iterate.A.1"
        ]
        contract = grandchild.work_contract
        assert contract is not None
        self.assertIn(
            "no write-capable external effects",
            contract.mandatory_constraints,
        )
        self.assertIn(
            "screen before extraction",
            contract.mandatory_constraints,
        )
        self.assertIn("research-engine@1031861", contract.provenance_refs)
        self.assertIn("stream:A", contract.provenance_refs)
        self.assertIn("source:A1", contract.provenance_refs)
        self.assertIn(
            "scope:research-read-only",
            contract.authority_refs,
        )
        self.assertIn(
            "validator:evidence-grounding-v1",
            contract.validator_contracts,
        )
        self.assertIn(
            "validator:screen-v1",
            contract.validator_contracts,
        )
        self.assertIn(
            "schema:research-synthesis-v1",
            contract.output_schema_refs,
        )
        self.assertIn(
            "schema:evidence-stream-v1",
            contract.output_schema_refs,
        )

        # Independent branch B may finish while nested A work remains.
        complete_process(
            runtime,
            "research-iterate.B",
            worker="W-B",
            lease="L-B",
            action_id="B",
        )
        tree.refresh_fan_in(event_id="B-complete")
        self.assertEqual(
            runtime.snapshot().graph.processes[ROOT_ID].state,
            ProcessState.WAITING_DEPENDENCIES,
        )

        complete_process(
            runtime,
            "research-iterate.A.1",
            worker="W-A1",
            lease="L-A1",
            action_id="A1",
        )
        tree.refresh_fan_in(event_id="A1-complete")
        self.assertEqual(
            runtime.snapshot().graph.processes["research-iterate.A"].state,
            ProcessState.WAITING_DEPENDENCIES,
        )

        complete_process(
            runtime,
            "research-iterate.A.2",
            worker="W-A2",
            lease="L-A2",
            action_id="A2",
        )
        tree.refresh_fan_in(event_id="A2-complete")
        resumed_a = runtime.snapshot().graph.processes[
            "research-iterate.A"
        ]
        self.assertEqual(resumed_a.state, ProcessState.READY_TO_RESUME)
        self.assertEqual(
            resumed_a.disposition,
            WorkDisposition.UNCLASSIFIED,
        )

        # A performs its bounded synthesis, then root fan-in can wake.
        complete_process(
            runtime,
            "research-iterate.A",
            worker="W-A-synth",
            lease="L-A-synth",
            action_id="A-synth",
        )
        tree.refresh_fan_in(event_id="A-synth-complete")
        resumed_root = runtime.snapshot().graph.processes[ROOT_ID]
        self.assertEqual(
            resumed_root.state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(
            resumed_root.disposition,
            WorkDisposition.UNCLASSIFIED,
        )

        complete_process(
            runtime,
            ROOT_ID,
            worker="W-root-synth",
            lease="L-root-synth",
            action_id="root-synth",
        )
        self.assertEqual(
            runtime.snapshot().graph.processes[ROOT_ID].state,
            ProcessState.COMPLETED,
        )

    def test_intrinsically_difficult_releases_lease_for_escalation(self):
        runtime = runtime_with_root()
        tree = TaskTreeCoordinator(runtime)
        generation = start_process(
            runtime,
            ROOT_ID,
            worker="W-cheap",
            lease="L-cheap",
        )

        tree.classify(
            ROOT_ID,
            disposition=WorkDisposition.INTRINSICALLY_DIFFICULT,
            reason="coupled reasoning exceeds current executor capability",
            lease_id="L-cheap",
            expected_generation=generation,
        )
        process = runtime.snapshot().graph.processes[ROOT_ID]

        self.assertEqual(process.state, ProcessState.READY_TO_RESUME)
        self.assertEqual(
            process.disposition,
            WorkDisposition.INTRINSICALLY_DIFFICULT,
        )
        self.assertIsNone(process.worker_id)
        self.assertIsNone(process.lease_id)
        self.assertTrue(tree.status(ROOT_ID).escalation_required)
        self.assertEqual(process.children, ())

        with self.assertRaises(KernelError):
            tree.decompose(
                ROOT_ID,
                lease_id="L-cheap",
                expected_generation=generation,
                children=(
                    ChildWorkSpec(
                        process_id="fake-child",
                        objective="Do not manufacture this child.",
                    ),
                ),
            )

        # A stronger executor can take the same durable generation, then
        # explicitly reclassify the bounded attempt as executable.
        runtime.claim(
            ROOT_ID,
            worker_id="W-strong",
            lease_id="L-strong",
            expected_generation=generation,
        )
        runtime.start(
            ROOT_ID,
            lease_id="L-strong",
            expected_generation=generation,
        )
        tree.classify(
            ROOT_ID,
            disposition=WorkDisposition.EXECUTABLE,
            reason="stronger executor satisfies coupled reasoning requirement",
            lease_id="L-strong",
            expected_generation=generation,
        )
        self.assertEqual(
            runtime.snapshot().graph.processes[ROOT_ID].disposition,
            WorkDisposition.EXECUTABLE,
        )

    def test_contracted_decomposition_cannot_drop_parent_obligations(self):
        runtime = runtime_with_root()
        generation = start_process(
            runtime,
            ROOT_ID,
            worker="W",
            lease="L",
        )

        # A contracted process cannot decompose without a TOO_LARGE
        # classification.
        with self.assertRaisesRegex(
            KernelError,
            "contracted_decomposition_requires_too_large",
        ):
            runtime.decompose(
                ROOT_ID,
                children=(
                    DomainKernel.create_process(
                        "child-premature",
                        work_contract=WorkContract(
                            objective="premature child"
                        ),
                    ),
                ),
                lease_id="L",
                expected_generation=generation,
            )

        runtime.classify_work(
            ROOT_ID,
            disposition=WorkDisposition.TOO_LARGE,
            reason="bounded decomposition required",
            lease_id="L",
            expected_generation=generation,
        )

        # Omitting a child contract is fail-closed because there is nowhere
        # to bind the child's local objective.
        with self.assertRaisesRegex(
            KernelError,
            "contracted_child_requires_work_contract",
        ):
            runtime.decompose(
                ROOT_ID,
                children=(DomainKernel.create_process("child-no-contract"),),
                lease_id="L",
                expected_generation=generation,
            )

        runtime.decompose(
            ROOT_ID,
            children=(
                DomainKernel.create_process(
                    "child",
                    work_contract=WorkContract(
                        objective="bounded child objective"
                    ),
                ),
            ),
            lease_id="L",
            expected_generation=generation,
        )
        graph = runtime.snapshot().graph
        child = graph.processes["child"]
        contract = child.work_contract
        assert contract is not None
        self.assertEqual(
            set(ROOT_CONTRACT.mandatory_constraints),
            set(contract.mandatory_constraints),
        )

        # Direct state corruption that drops an inherited mandatory
        # constraint is rejected by global graph validation.
        child.work_contract = replace(
            contract,
            mandatory_constraints=(),
        )
        with self.assertRaisesRegex(
            KernelError,
            "inherited_work_contract_dropped",
        ):
            DomainKernel.validate(graph)

    def test_recovery_preserves_contract_and_dependency_wait(self):
        runtime = runtime_with_root()
        tree = TaskTreeCoordinator(runtime)
        generation = start_process(
            runtime,
            ROOT_ID,
            worker="W-root",
            lease="L-root",
        )
        tree.classify(
            ROOT_ID,
            disposition=WorkDisposition.TOO_LARGE,
            reason="two leaves",
            lease_id="L-root",
            expected_generation=generation,
        )
        tree.decompose(
            ROOT_ID,
            lease_id="L-root",
            expected_generation=generation,
            children=(
                ChildWorkSpec(
                    process_id="leaf-1",
                    objective="Leaf one.",
                ),
                ChildWorkSpec(
                    process_id="leaf-2",
                    objective="Leaf two.",
                ),
            ),
        )

        runtime.recover(
            ROOT_ID,
            expected_generation=0,
            reason="scheduler restart during fan-out",
        )
        recovered = runtime.snapshot().graph.processes[ROOT_ID]
        self.assertEqual(recovered.generation, 1)
        self.assertEqual(
            recovered.state,
            ProcessState.WAITING_DEPENDENCIES,
        )
        self.assertEqual(recovered.work_contract, ROOT_CONTRACT)

        complete_process(
            runtime,
            "leaf-1",
            worker="W1",
            lease="L1",
            action_id="leaf-1",
        )
        tree.refresh_fan_in(event_id="leaf-1")
        self.assertEqual(
            runtime.snapshot().graph.processes[ROOT_ID].state,
            ProcessState.WAITING_DEPENDENCIES,
        )

        complete_process(
            runtime,
            "leaf-2",
            worker="W2",
            lease="L2",
            action_id="leaf-2",
        )
        tree.refresh_fan_in(event_id="leaf-2")
        resumed = runtime.snapshot().graph.processes[ROOT_ID]
        self.assertEqual(resumed.generation, 1)
        self.assertEqual(resumed.state, ProcessState.READY_TO_RESUME)
        self.assertEqual(resumed.work_contract, ROOT_CONTRACT)

    def test_contracted_effect_requires_executable_classification(self):
        runtime = runtime_with_root()
        generation = start_process(
            runtime,
            ROOT_ID,
            worker="W",
            lease="L",
        )
        with self.assertRaisesRegex(
            KernelError,
            "contracted_effect_requires_executable",
        ):
            runtime.record_effect(
                ROOT_ID,
                receipt=EffectReceipt(
                    action_id="A",
                    idempotency_key="I",
                    target_ref="target",
                    effect_hash="hash",
                    executor_id="executor",
                    generation=generation,
                    observed_at="T",
                ),
                lease_id="L",
                expected_generation=generation,
            )


if __name__ == "__main__":
    unittest.main()
