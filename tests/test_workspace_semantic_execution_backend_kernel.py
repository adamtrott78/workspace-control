"""Production-domain tests for Workspace Semantic Execution backend v1."""
from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.domain import (  # noqa: E402
    AuthorityDecision,
    AuthorityOutcome,
    CandidateAction,
    DomainKernel,
    EffectReceipt,
    KernelError,
    ProcessState,
    ValidationResult,
)


CONTRACT = json.loads(
    (ROOT / "architecture/workspace-semantic-execution-kernel.v0.1.json").read_text()
)


def receipt(
    *,
    action_id: str = "A1",
    idempotency_key: str = "I1",
    effect_hash: str = "hash:1",
    generation: int = 0,
) -> EffectReceipt:
    return EffectReceipt(
        action_id=action_id,
        idempotency_key=idempotency_key,
        target_ref="target:1",
        effect_hash=effect_hash,
        executor_id="executor:test",
        generation=generation,
        observed_at="T1",
    )


def complete(
    graph,
    process_id: str,
    *,
    worker_id: str,
    lease_id: str,
    action_id: str,
):
    generation = graph.processes[process_id].generation
    graph = DomainKernel.claim(
        graph,
        process_id,
        worker_id=worker_id,
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = DomainKernel.start(
        graph,
        process_id,
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = DomainKernel.record_effect(
        graph,
        process_id,
        receipt=receipt(
            action_id=action_id,
            idempotency_key=f"idem:{action_id}",
            effect_hash=f"hash:{action_id}",
            generation=generation,
        ),
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = DomainKernel.propose_terminal(
        graph,
        process_id,
        lease_id=lease_id,
        expected_generation=generation,
    )
    graph = DomainKernel.begin_validation(graph, process_id)
    return DomainKernel.record_validation(
        graph,
        process_id,
        result=ValidationResult(
            validator_id="validator:test",
            passed=True,
            evidence_ref=f"evidence:{action_id}",
            observed_at="T2",
        ),
    )


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_production_states_match_validated_reference_contract(self):
        self.assertEqual(
            {state.value for state in ProcessState},
            set(CONTRACT["process_states"]),
        )

    def test_domain_has_no_infrastructure_imports(self):
        domain_root = SRC / "workspace_semantic_execution" / "domain"
        allowed_absolute = {
            "__future__",
            "ast",
            "copy",
            "dataclasses",
            "enum",
            "typing",
        }
        failures = []
        for path in domain_root.glob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".", 1)[0]
                        if root not in sys.stdlib_module_names:
                            failures.append(f"{path.name}:import:{alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        continue
                    root = (node.module or "").split(".", 1)[0]
                    if root and root not in sys.stdlib_module_names and root not in allowed_absolute:
                        failures.append(f"{path.name}:from:{node.module}")
        self.assertEqual(failures, [])

    def test_domain_source_has_no_gpu_runtime_dependency(self):
        domain_root = SRC / "workspace_semantic_execution" / "domain"
        text = "\n".join(path.read_text().lower() for path in domain_root.glob("*.py"))
        for forbidden in ("torch", "cupy", "cuda_visible_devices", "nvidia"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)


class GenerationLeaseAndCopyTests(unittest.TestCase):
    def test_stale_generation_is_fenced_and_failed_transition_is_non_mutating(self):
        graph = DomainKernel.create_graph([DomainKernel.create_process("R")])
        graph = DomainKernel.claim(
            graph,
            "R",
            worker_id="W0",
            lease_id="L0",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "R",
            lease_id="L0",
            expected_generation=0,
        )
        graph = DomainKernel.recover(
            graph,
            "R",
            expected_generation=0,
            reason="worker lost",
        )
        before = deepcopy(graph)

        with self.assertRaises(KernelError):
            DomainKernel.record_effect(
                graph,
                "R",
                receipt=receipt(generation=0),
                lease_id="L0",
                expected_generation=0,
            )

        self.assertEqual(graph, before)
        self.assertEqual(graph.processes["R"].generation, 1)
        self.assertEqual(graph.processes["R"].state, ProcessState.READY_TO_RESUME)

    def test_single_current_lease(self):
        graph = DomainKernel.create_graph([DomainKernel.create_process("R")])
        graph = DomainKernel.claim(
            graph,
            "R",
            worker_id="W1",
            lease_id="L1",
            expected_generation=0,
        )
        with self.assertRaises(KernelError):
            DomainKernel.claim(
                graph,
                "R",
                worker_id="W2",
                lease_id="L2",
                expected_generation=0,
            )


class DependencyTests(unittest.TestCase):
    def test_dependency_readiness_and_fanin(self):
        graph = DomainKernel.create_graph(
            [
                DomainKernel.create_process("A"),
                DomainKernel.create_process("B"),
                DomainKernel.create_process("C", dependencies=("A", "B")),
            ]
        )
        with self.assertRaises(KernelError):
            DomainKernel.claim(
                graph,
                "C",
                worker_id="WC",
                lease_id="LC",
                expected_generation=0,
            )

        graph = complete(
            graph,
            "A",
            worker_id="WA",
            lease_id="LA",
            action_id="AA",
        )
        with self.assertRaises(KernelError):
            DomainKernel.claim(
                graph,
                "C",
                worker_id="WC",
                lease_id="LC",
                expected_generation=0,
            )

        graph = complete(
            graph,
            "B",
            worker_id="WB",
            lease_id="LB",
            action_id="AB",
        )
        graph = DomainKernel.claim(
            graph,
            "C",
            worker_id="WC",
            lease_id="LC",
            expected_generation=0,
        )
        self.assertEqual(graph.processes["C"].state, ProcessState.CLAIMED)

    def test_decomposed_parent_resumes_only_after_all_children_complete(self):
        graph = DomainKernel.create_graph([DomainKernel.create_process("P")])
        graph = DomainKernel.claim(
            graph,
            "P",
            worker_id="WP",
            lease_id="LP",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "P",
            lease_id="LP",
            expected_generation=0,
        )
        graph = DomainKernel.decompose(
            graph,
            "P",
            children=(
                DomainKernel.create_process("P.1"),
                DomainKernel.create_process("P.2"),
            ),
            lease_id="LP",
            expected_generation=0,
        )
        self.assertEqual(
            graph.processes["P"].state,
            ProcessState.WAITING_DEPENDENCIES,
        )
        self.assertIsNone(graph.processes["P"].lease_id)

        graph = complete(
            graph,
            "P.1",
            worker_id="W1",
            lease_id="L1",
            action_id="A1",
        )
        graph = DomainKernel.refresh_dependency_waits(
            graph,
            event_id="child-1",
        )
        self.assertEqual(
            graph.processes["P"].state,
            ProcessState.WAITING_DEPENDENCIES,
        )

        graph = complete(
            graph,
            "P.2",
            worker_id="W2",
            lease_id="L2",
            action_id="A2",
        )
        graph = DomainKernel.refresh_dependency_waits(
            graph,
            event_id="child-2",
        )
        self.assertEqual(
            graph.processes["P"].state,
            ProcessState.READY_TO_RESUME,
        )

    def test_recovery_preserves_dependency_wait(self):
        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("P-recover")]
        )
        graph = DomainKernel.claim(
            graph,
            "P-recover",
            worker_id="WP",
            lease_id="LP",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "P-recover",
            lease_id="LP",
            expected_generation=0,
        )
        graph = DomainKernel.decompose(
            graph,
            "P-recover",
            children=(
                DomainKernel.create_process("P-recover.1"),
                DomainKernel.create_process("P-recover.2"),
            ),
            lease_id="LP",
            expected_generation=0,
        )
        graph = DomainKernel.recover(
            graph,
            "P-recover",
            expected_generation=0,
            reason="scheduler restart",
        )
        parent = graph.processes["P-recover"]
        self.assertEqual(parent.generation, 1)
        self.assertEqual(
            parent.state,
            ProcessState.WAITING_DEPENDENCIES,
        )
        with self.assertRaises(KernelError):
            DomainKernel.claim(
                graph,
                "P-recover",
                worker_id="WP2",
                lease_id="LP2",
                expected_generation=1,
            )


class WaitTests(unittest.TestCase):
    def test_external_wait_owns_no_lease_and_cannot_poll_model(self):
        graph = DomainKernel.create_graph([DomainKernel.create_process("R")])
        graph = DomainKernel.claim(
            graph,
            "R",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.record_reasoning_quantum(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )
        before_quanta = graph.processes["R"].reasoning_quanta
        graph = DomainKernel.wait_external(
            graph,
            "R",
            wait_key="ci:run:123",
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(
            graph.processes["R"].state,
            ProcessState.WAITING_EXTERNAL,
        )
        self.assertIsNone(graph.processes["R"].worker_id)
        self.assertIsNone(graph.processes["R"].lease_id)

        with self.assertRaises(KernelError):
            DomainKernel.record_reasoning_quantum(
                graph,
                "R",
                lease_id="L",
                expected_generation=0,
            )

        graph = DomainKernel.wake_external(
            graph,
            "R",
            wait_key="ci:run:123",
            event_id="ci:run:123:completed",
        )
        self.assertEqual(
            graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertEqual(
            graph.processes["R"].reasoning_quanta,
            before_quanta,
        )

    def test_recovery_preserves_external_wait_until_actual_wake(self):
        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("R-wait-recover")]
        )
        graph = DomainKernel.claim(
            graph,
            "R-wait-recover",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "R-wait-recover",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.wait_external(
            graph,
            "R-wait-recover",
            wait_key="ci:run:999",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.recover(
            graph,
            "R-wait-recover",
            expected_generation=0,
            reason="backend restart",
        )
        process = graph.processes["R-wait-recover"]
        self.assertEqual(process.generation, 1)
        self.assertEqual(process.state, ProcessState.WAITING_EXTERNAL)
        self.assertEqual(process.wait_key, "ci:run:999")
        with self.assertRaises(KernelError):
            DomainKernel.claim(
                graph,
                "R-wait-recover",
                worker_id="W2",
                lease_id="L2",
                expected_generation=1,
            )
        graph = DomainKernel.wake_external(
            graph,
            "R-wait-recover",
            wait_key="ci:run:999",
            event_id="ci:run:999:completed",
        )
        self.assertEqual(
            graph.processes["R-wait-recover"].state,
            ProcessState.READY_TO_RESUME,
        )


class EffectValidationAndRecoveryTests(unittest.TestCase):
    def running_graph(self):
        graph = DomainKernel.create_graph([DomainKernel.create_process("R")])
        graph = DomainKernel.claim(
            graph,
            "R",
            worker_id="W",
            lease_id="L",
            expected_generation=0,
        )
        return DomainKernel.start(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )

    def test_identical_duplicate_receipt_is_noop_conflict_fails_closed(self):
        graph = self.running_graph()
        effect = receipt()
        graph = DomainKernel.record_effect(
            graph,
            "R",
            receipt=effect,
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.record_effect(
            graph,
            "R",
            receipt=effect,
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(len(graph.processes["R"].effect_receipts), 1)

        with self.assertRaises(KernelError):
            DomainKernel.record_effect(
                graph,
                "R",
                receipt=receipt(effect_hash="different"),
                lease_id="L",
                expected_generation=0,
            )

    def test_tool_receipt_alone_cannot_complete(self):
        graph = self.running_graph()
        graph = DomainKernel.record_effect(
            graph,
            "R",
            receipt=receipt(),
            lease_id="L",
            expected_generation=0,
        )
        self.assertEqual(graph.processes["R"].state, ProcessState.RUNNING)

    def test_completion_requires_passing_postcondition_validation(self):
        graph = self.running_graph()
        with self.assertRaises(KernelError):
            DomainKernel.propose_terminal(
                graph,
                "R",
                lease_id="L",
                expected_generation=0,
            )

        graph = DomainKernel.record_effect(
            graph,
            "R",
            receipt=receipt(),
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.propose_terminal(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.begin_validation(graph, "R")
        graph = DomainKernel.record_validation(
            graph,
            "R",
            result=ValidationResult(
                validator_id="V",
                passed=True,
                evidence_ref="evidence:postcondition",
                observed_at="T2",
            ),
        )
        self.assertEqual(graph.processes["R"].state, ProcessState.COMPLETED)

    def test_failed_validation_returns_to_repair(self):
        graph = self.running_graph()
        graph = DomainKernel.record_effect(
            graph,
            "R",
            receipt=receipt(),
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.propose_terminal(
            graph,
            "R",
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.begin_validation(graph, "R")
        graph = DomainKernel.record_validation(
            graph,
            "R",
            result=ValidationResult(
                validator_id="V",
                passed=False,
                evidence_ref="evidence:failed",
                observed_at="T2",
            ),
        )
        self.assertEqual(
            graph.processes["R"].state,
            ProcessState.READY_TO_RESUME,
        )
        self.assertTrue(graph.processes["R"].repair_required)

    def test_crash_after_effect_preserves_receipt_and_fences_old_lease(self):
        graph = self.running_graph()
        graph = DomainKernel.record_effect(
            graph,
            "R",
            receipt=receipt(),
            lease_id="L",
            expected_generation=0,
        )
        graph = DomainKernel.recover(
            graph,
            "R",
            expected_generation=0,
            reason="crash after external effect",
        )
        self.assertIn("I1", graph.processes["R"].effect_receipts)

        with self.assertRaises(KernelError):
            DomainKernel.propose_terminal(
                graph,
                "R",
                lease_id="L",
                expected_generation=0,
            )

        graph = DomainKernel.claim(
            graph,
            "R",
            worker_id="W2",
            lease_id="L2",
            expected_generation=1,
        )
        graph = DomainKernel.start(
            graph,
            "R",
            lease_id="L2",
            expected_generation=1,
        )
        graph = DomainKernel.propose_terminal(
            graph,
            "R",
            lease_id="L2",
            expected_generation=1,
        )
        graph = DomainKernel.begin_validation(graph, "R")
        graph = DomainKernel.record_validation(
            graph,
            "R",
            result=ValidationResult(
                validator_id="V",
                passed=True,
                evidence_ref="evidence:effect-observed",
                observed_at="T2",
            ),
        )
        self.assertEqual(graph.processes["R"].state, ProcessState.COMPLETED)
        self.assertEqual(len(graph.processes["R"].effect_receipts), 1)


class AuthorityTests(unittest.TestCase):
    def candidate(self) -> CandidateAction:
        return CandidateAction(
            action_id="A1",
            process_id="R1",
            target_ref="github:repo@sha",
            executor_type="GITHUB_READ_ONLY",
            idempotency_key="idem:A1",
            preconditions=("source_sha_matches",),
            expected_effect="read exact repository state",
            postcondition_validator="validator:exact_sha_read",
        )

    def test_candidate_cannot_self_authorize(self):
        candidate = self.candidate()
        self.assertEqual(candidate.authorization_state, "UNDECIDED")

        claimed = CandidateAction(
            **{
                **candidate.__dict__,
                "authorization_state": "ALLOW",
            }
        )
        with self.assertRaises(KernelError):
            DomainKernel.compile_action_spec(
                claimed,
                AuthorityDecision(
                    decision_id="D",
                    outcome=AuthorityOutcome.ALLOW,
                    action_id="A1",
                    target_ref="github:repo@sha",
                    authority_scope_ref="policy:scope",
                ),
            )

    def test_only_exact_allow_compiles_action_spec(self):
        candidate = self.candidate()
        for outcome in (
            AuthorityOutcome.DENY,
            AuthorityOutcome.ABSTAIN,
            AuthorityOutcome.UNKNOWN,
        ):
            with self.subTest(outcome=outcome):
                with self.assertRaises(KernelError):
                    DomainKernel.compile_action_spec(
                        candidate,
                        AuthorityDecision(
                            decision_id=f"D:{outcome}",
                            outcome=outcome,
                            action_id="A1",
                            target_ref="github:repo@sha",
                            authority_scope_ref="policy:scope",
                        ),
                    )

        with self.assertRaises(KernelError):
            DomainKernel.compile_action_spec(
                candidate,
                AuthorityDecision(
                    decision_id="D:mismatch",
                    outcome=AuthorityOutcome.ALLOW,
                    action_id="OTHER",
                    target_ref="github:repo@sha",
                    authority_scope_ref="policy:scope",
                ),
            )

        action = DomainKernel.compile_action_spec(
            candidate,
            AuthorityDecision(
                decision_id="D:allow",
                outcome=AuthorityOutcome.ALLOW,
                action_id="A1",
                target_ref="github:repo@sha",
                authority_scope_ref="policy:scope",
            ),
        )
        self.assertEqual(action.authority_decision_id, "D:allow")
        self.assertEqual(action.target_ref, "github:repo@sha")


class FailClosedTests(unittest.TestCase):
    def test_unknown_state_fails_closed(self):
        graph = DomainKernel.create_graph([DomainKernel.create_process("R")])
        graph.processes["R"].state = "MAGIC"  # type: ignore[assignment]
        with self.assertRaises(KernelError):
            DomainKernel.validate(graph)


if __name__ == "__main__":
    unittest.main()
