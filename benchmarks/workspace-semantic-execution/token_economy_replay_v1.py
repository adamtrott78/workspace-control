"""Offline E4-0 packet-economy replay over accepted Research-Iterate shapes.

This benchmark performs no model calls and no external effects. It reconstructs
representative packets through the accepted E2 packet builders, then compares
legacy FULL_RECOVERY rendering against the compact REF_ONLY projection while
requiring identical canonical packet identity.
"""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.application import (  # noqa: E402
    SemanticPacketCompiler,
    TokenEconomyPlanner,
    TokenEconomyRequest,
    openai_chat_instant_current_profile,
)
from workspace_semantic_execution.domain import (  # noqa: E402
    WorkerResultPublicationContract,
)

E2_PATH = (
    ROOT
    / "benchmarks"
    / "workspace-semantic-execution"
    / "live_research_iterate_e2.py"
)


class TokenEconomyReplayError(RuntimeError):
    pass


def _load_e2():
    spec = importlib.util.spec_from_file_location(
        "token_economy_replay_e2",
        E2_PATH,
    )
    if spec is None or spec.loader is None:
        raise TokenEconomyReplayError("e2_module_load_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _publication(source, *, action_id: str, path: str):
    return replace(
        source,
        result_publication=WorkerResultPublicationContract(
            publication_id=f"worker-result:{action_id}:0",
            action_id=action_id,
            action_generation=0,
            process_generation=0,
            worker_slot_id="replay-slot",
            session_generation=0,
            schema_ref=(
                "architecture/"
                "workspace-semantic-execution-worker-result.v0.1.json"
            ),
            target_ref=(
                "github-candidate://adamtrott78/workspace-control/"
                f"ref/refs%2Fheads%2Fworker-result-candidates-v1/path/{path}"
            ),
            candidate_only=True,
        ),
    )


def packet_cases():
    e2 = _load_e2()
    token = "token-economy-replay"
    root_id = f"research-iterate-e2:{token}"
    source_id = f"{root_id}.source"
    analysis_id = f"{root_id}.analysis"
    shell_id = f"{root_id}.workspace-shell"

    root_path = "worker-results/e2/replay/root.json"
    analysis_path = "worker-results/e2/replay/analysis.json"
    shell_path = "worker-results/e2/replay/shell.json"
    synthesis_path = "worker-results/e2/replay/synthesis.json"

    root = e2._root_packet(
        root_id=root_id,
        source_id=source_id,
        analysis_id=analysis_id,
        shell_id=shell_id,
        path=root_path,
        marker="e2:root:replay",
    )
    analysis = e2._result_packet(
        process_id=analysis_id,
        checkpoint="research-iterate-e2@analysis-g1",
        objective=(
            "Resume the analysis leaf from durable mission state after the "
            "previous worker/session generation was fenced. Use exact-source "
            "provenance and publish only the declared candidate."
        ),
        path=analysis_path,
        payload_ref="e2://replay/analysis/result",
        payload_sha256="a" * 64,
        evidence_instruction=(
            "evidence_refs must contain the analysis marker and exact-source "
            "validator evidence."
        ),
        extra_constraints=(
            "The previous worker/session generation is stale.",
            "Recover from durable packet state only.",
        ),
    )
    shell = e2._result_packet(
        process_id=shell_id,
        checkpoint="research-iterate-e2@workspace-shell",
        objective=(
            "Perform the bounded Workspace Shell read-only capability probe, "
            "then publish its exact evidence."
        ),
        path=shell_path,
        payload_ref="e2://replay/shell/result",
        payload_sha256="b" * 64,
        evidence_instruction=(
            "evidence_refs must contain only the declared shell-probe marker."
        ),
        plugin_mentions=(
            e2.WORKSPACE_SHELL_PLUGIN_MENTION,
            e2.GITHUB_PLUGIN_MENTION,
        ),
        extra_constraints=(
            "Workspace Shell capability is strictly read-only for this leaf.",
            "workspace_shell_exec and workspace_shell_run_reviewed_helper are prohibited.",
        ),
        allowed_actions=(
            "inspect-workspace-shell-runtime-inventory",
            "publish-exact-worker-result-candidate",
        ),
    )
    synthesis = e2._result_packet(
        process_id=root_id,
        checkpoint="research-iterate-e2@synthesis",
        objective=(
            "Synthesize the validated exact-source, analysis, and Workspace "
            "Shell capability evidence into the final mission result. Do not "
            "add unsupported claims."
        ),
        path=synthesis_path,
        payload_ref="e2://replay/synthesis/result",
        payload_sha256="c" * 64,
        evidence_instruction=(
            "evidence_refs must contain the exact validated source, analysis, "
            "and Workspace Shell evidence refs."
        ),
    )

    return {
        "root_decomposition": _publication(
            root,
            action_id="action:replay:root",
            path=root_path,
        ),
        "analysis": _publication(
            analysis,
            action_id="action:replay:analysis",
            path=analysis_path,
        ),
        "workspace_shell": _publication(
            shell,
            action_id="action:replay:shell",
            path=shell_path,
        ),
        "synthesis": _publication(
            synthesis,
            action_id="action:replay:synthesis",
            path=synthesis_path,
        ),
    }


def run_replay() -> dict[str, object]:
    executor = openai_chat_instant_current_profile()
    compiler = SemanticPacketCompiler()
    planner = TokenEconomyPlanner()

    rows = []
    full_bytes_total = 0
    compact_bytes_total = 0

    for name, source in packet_cases().items():
        full = compiler.compile(source, executor=executor)
        decision = planner.plan(
            TokenEconomyRequest(
                required_refs=tuple(
                    dict.fromkeys(
                        source.evidence_refs + source.authority_refs
                    )
                ),
                base_checkpoint=source.source_checkpoint,
                invocation_mode=executor.invocation_mode,
                session_mode=executor.session_mode,
            )
        )
        compact = compiler.compile(
            source,
            executor=executor,
            token_economy=decision,
        )
        if full.packet_sha256 != compact.packet_sha256:
            raise TokenEconomyReplayError(
                f"canonical_packet_hash_changed:{name}"
            )
        if full.canonical_payload_json != compact.canonical_payload_json:
            raise TokenEconomyReplayError(
                f"canonical_payload_changed:{name}"
            )

        full_bytes = len(full.text.encode("utf-8"))
        compact_bytes = len(compact.text.encode("utf-8"))
        full_bytes_total += full_bytes
        compact_bytes_total += compact_bytes
        rows.append(
            {
                "case": name,
                "packet_sha256": full.packet_sha256,
                "context_mode": decision.context.context_mode.value,
                "full_worker_text_bytes": full_bytes,
                "compact_worker_text_bytes": compact_bytes,
                "byte_reduction": full_bytes - compact_bytes,
                "byte_reduction_fraction": (
                    0.0
                    if full_bytes == 0
                    else (full_bytes - compact_bytes) / full_bytes
                ),
                "canonical_identity_preserved": True,
            }
        )

    return {
        "schema_version": 1,
        "benchmark": "workspace-token-economy-replay-v1",
        "model_calls": 0,
        "token_claim": (
            "Byte/character reduction is an offline input-size proxy only; "
            "actual provider token/allowance consumption remains live telemetry."
        ),
        "cases": rows,
        "aggregate": {
            "full_worker_text_bytes": full_bytes_total,
            "compact_worker_text_bytes": compact_bytes_total,
            "byte_reduction": full_bytes_total - compact_bytes_total,
            "byte_reduction_fraction": (
                0.0
                if full_bytes_total == 0
                else (
                    full_bytes_total - compact_bytes_total
                ) / full_bytes_total
            ),
        },
    }


def main() -> int:
    print(
        json.dumps(
            run_replay(),
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
