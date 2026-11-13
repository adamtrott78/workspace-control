"""Production shadow canary over exact frozen Research Engine source bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.adapters import (  # noqa: E402
    DeterministicSemanticProjection,
    FakeClock,
    ReadOnlyRepositoryExecutor,
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
)


RESEARCH_ENGINE_SHA = "1031861c03b2af8cff5cf72939bbbc83a95e65a4"
SOURCE_BLOB_SHA = "0d051fa50960708e0e773f6871c7e924c5796394"
SOURCE_PATH = "src/research_engine/orchestration.py"
FROZEN_SOURCE = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "backend"
    / "research-engine-1031861"
    / "orchestration.py"
)
WORKFLOW_FIXTURE = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "research_engine_kernel_canary_v1.json"
)


def git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()  # noqa: S324 - Git identity


def read_profile() -> ExecutorProfile:
    return ExecutorProfile(
        executor_id="research-engine-shadow-read",
        provider_id="frozen-exact-source",
        model_id="none",
        surface_id="machine",
        harness_id="research-engine-shadow-v1",
        toolset_id="repository-read-only",
        capabilities=frozenset({"repository.read_exact"}),
        invocation_mode=InvocationMode.DETERMINISTIC,
        session_mode=SessionMode.NONE,
        lifecycle=ExecutorLifecycle.DETERMINISTIC_PROCESS,
        memory_reset_policy=MemoryResetPolicy.NONE,
        availability=ExecutorAvailability.AVAILABLE,
        locality=ExecutorLocality.LOCAL_HOST,
        privacy_classes=frozenset({PrivacyClass.PUBLIC}),
        resource_classes=frozenset({"CPU"}),
        scarcity_rank=0,
    )


def source_action() -> ActionSpec:
    return ActionSpec(
        action_id="shadow:read-research-engine-orchestration",
        process_id="shadow:source-observation",
        process_generation=0,
        target_ref=(
            "repo://adamtrott78/research-engine@"
            f"{RESEARCH_ENGINE_SHA}/{SOURCE_PATH}"
        ),
        executor_type="REPOSITORY_READ_ONLY",
        authority_decision_id="authority:shadow-read-only",
        authority_scope_ref="scope:research-engine-exact-source-read",
        idempotency_key="shadow:source-observation:v1",
        preconditions=(
            "research-engine source is immutable exact SHA",
            "read-only observation only",
        ),
        expected_effect="observe exact Research Engine orchestration bytes",
        postcondition_validator="repository-read-exact-source-v1",
    )


class ResearchEngineProductionShadowCanary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = FROZEN_SOURCE.read_bytes()
        cls.fixture = json.loads(WORKFLOW_FIXTURE.read_text())

    def test_frozen_source_is_byte_identical_git_blob(self):
        self.assertEqual(
            git_blob_sha(self.source_bytes),
            SOURCE_BLOB_SHA,
        )
        source = self.fixture["source"]
        self.assertEqual(source["repository"], "adamtrott78/research-engine")
        self.assertEqual(source["commit_sha"], RESEARCH_ENGINE_SHA)
        self.assertEqual(source["path"], SOURCE_PATH)

    def test_workflow_shape_is_supported_by_real_source_bytes(self):
        text = self.source_bytes.decode("utf-8")
        required_markers = (
            "class ResearchPlanner:",
            "def lease_next(",
            "class AgentWorker:",
            "JobType.DISCOVERY",
            "JobType.SCREEN",
            "JobType.ACQUIRE",
            "JobType.EXTRACT",
            "JobType.VERIFY",
            "JobType.CHECKPOINT",
            "JobType.SYNTHESIZE",
            "JobType.GAP_GENERATE",
            "JobType.NOVELTY_SEARCH",
            "JobType.NOVELTY_ARBITRATE",
            "JobType.HUMAN_REVIEW",
            "depends_on=[discovery[0].id]",
            "depends_on=[j.id for j in verifies]",
            "status='WAITING_HUMAN'",
        )
        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_exact_source_read_effect_and_independent_validator_pass(self):
        observation = RepositoryFileObservation(
            repository="adamtrott78/research-engine",
            revision=RESEARCH_ENGINE_SHA,
            path=SOURCE_PATH,
            blob_id=SOURCE_BLOB_SHA,
            content=self.source_bytes,
        )
        reader = StaticRepositoryReader((observation,))
        clock = FakeClock()
        executor = ReadOnlyRepositoryExecutor(reader=reader, clock=clock)
        validator = RepositoryReadPostconditionValidator(
            reader=reader,
            clock=clock,
        )

        graph = DomainKernel.create_graph(
            [DomainKernel.create_process("shadow:source-observation")]
        )
        graph = DomainKernel.claim(
            graph,
            "shadow:source-observation",
            worker_id="shadow-reader",
            lease_id="shadow-read-lease",
            expected_generation=0,
        )
        graph = DomainKernel.start(
            graph,
            "shadow:source-observation",
            lease_id="shadow-read-lease",
            expected_generation=0,
        )

        action = source_action()
        receipt = executor.execute(action, executor=read_profile())
        graph = DomainKernel.record_effect(
            graph,
            "shadow:source-observation",
            receipt=receipt,
            lease_id="shadow-read-lease",
            expected_generation=0,
        )
        graph = DomainKernel.propose_terminal(
            graph,
            "shadow:source-observation",
            lease_id="shadow-read-lease",
            expected_generation=0,
        )
        graph = DomainKernel.begin_validation(
            graph,
            "shadow:source-observation",
        )
        verdict = validator.validate(action, receipt)
        graph = DomainKernel.record_validation(
            graph,
            "shadow:source-observation",
            result=verdict,
        )

        self.assertTrue(verdict.passed)
        self.assertEqual(reader.read_count, 2)
        self.assertEqual(
            graph.processes["shadow:source-observation"].state,
            ProcessState.COMPLETED,
        )
        self.assertIn(SOURCE_BLOB_SHA, verdict.evidence_ref)

    def test_real_workflow_projects_into_production_kernel_without_schema_special_case(self):
        graph = DomainKernel.create_graph(
            [
                DomainKernel.create_process(
                    node["process_id"],
                    dependencies=tuple(node["dependencies"]),
                )
                for node in self.fixture["nodes"]
            ]
        )
        projection = DeterministicSemanticProjection().project(graph)
        projected = {
            item["process_id"]: item
            for item in projection["processes"]
        }

        self.assertEqual(len(projected), len(self.fixture["nodes"]))
        self.assertEqual(
            projected["re:checkpoint"]["dependencies"],
            ["re:verify:paper1", "re:verify:paper2"],
        )
        self.assertEqual(
            projected["re:arbitrate:g1"]["dependencies"],
            ["re:novelty:g1:0", "re:novelty:g1:1"],
        )
        self.assertEqual(
            projected["re:human-review"]["dependencies"],
            ["re:arbitrate:g1"],
        )

        with self.assertRaises(Exception):
            DomainKernel.claim(
                graph,
                "re:checkpoint",
                worker_id="early",
                lease_id="early",
                expected_generation=0,
            )

    def test_shadow_canary_has_no_research_engine_write_surface(self):
        source = Path(__file__).read_text()
        forbidden = (
            "research-engine.git",
            "git push",
            "update_file(",
            "create_file(",
            "delete_file(",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
