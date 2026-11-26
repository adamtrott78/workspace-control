"""Offline E4-0 token-economy replay over accepted research-iterate packet shapes.

No model, browser, network model API, subscription meter, runtime mutation, or
authority is required. The harness compares legacy full worker rendering with
the compact projection while asserting identical canonical packet identity.
"""
from __future__ import annotations

import argparse
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
    ROOT / "benchmarks" / "workspace-semantic-execution"
    / "live_research_iterate_e2.py"
)


def _load_e2():
    spec = importlib.util.spec_from_file_location(
        "token_economy_replay_e2",
        E2_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("e2_module_load_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _with_publication(packet, *, action: str, target: str, generation: int = 0):
    return replace(
        packet,
        result_publication=WorkerResultPublicationContract(
            publication_id=f"worker-result:{action}:0",
            action_id=action,
            action_generation=0,
            process_generation=generation,
            worker_slot_id="e4-0-replay-slot",
            session_generation=generation,
            schema_ref=(
                "architecture/"
                "workspace-semantic-execution-worker-result.v0.1.json"
            ),
            target_ref=target,
            candidate_only=True,
        ),
    )


def _cases():
    e2 = _load_e2()
    root_id = "research-iterate-e4-0:replay"
    source_id = f"{root_id}.source"
    analysis_id = f"{root_id}.analysis"
    shell_id = f"{root_id}.workspace-shell"

    root = e2._root_packet(
        root_id=root_id,
        source_id=source_id,
        analysis_id=analysis_id,
        shell_id=shell_id,
        path="worker-results/e4-0/replay/root.json",
        marker="e4-0:root",
    )
    analysis = e2._result_packet(
        process_id=analysis_id,
        checkpoint="research-iterate-e2@analysis-g1",
        objective=(
            "Resume the analysis leaf from durable mission state after the "
            "previous worker/session generation was fenced. Use this packet "
            "and exact-source provenance; do not rely on the retired chat "
            "generation."
        ),
        path="worker-results/e4-0/replay/analysis.json",
        payload_ref="e4-0://analysis/result",
        payload_sha256="a" * 64,
        evidence_instruction=(
            "evidence_refs must contain exactly e4-0:analysis and "
            "validation:e4-0:source."
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
        path="worker-results/e4-0/replay/shell.json",
        payload_ref="e4-0://workspace-shell/result",
        payload_sha256="b" * 64,
        evidence_instruction=(
            "Publish only the exact content-free runtime inventory evidence."
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
            "Shell capability evidence into the final E2 mission result. "
            "Do not add unsupported claims."
        ),
        path="worker-results/e4-0/replay/synthesis.json",
        payload_ref="e4-0://synthesis/result",
        payload_sha256="c" * 64,
        evidence_instruction=(
            "evidence_refs must contain exactly the supplied validated inputs."
        ),
    )

    return (
        (
            "root-decomposition",
            _with_publication(
                root,
                action="action:e4-0:root",
                target="github://candidate/root",
            ),
        ),
        (
            "analysis-recovery",
            _with_publication(
                analysis,
                action="action:e4-0:analysis",
                target="github://candidate/analysis",
                generation=1,
            ),
        ),
        (
            "workspace-shell",
            _with_publication(
                shell,
                action="action:e4-0:shell",
                target="github://candidate/shell",
            ),
        ),
        (
            "synthesis",
            _with_publication(
                synthesis,
                action="action:e4-0:synthesis",
                target="github://candidate/synthesis",
            ),
        ),
    )


def build_report() -> dict[str, object]:
    compiler = SemanticPacketCompiler()
    planner = TokenEconomyPlanner()
    executor = openai_chat_instant_current_profile()
    rows: list[dict[str, object]] = []

    for name, source in _cases():
        full = compiler.compile(source, executor=executor)
        decision = planner.plan(
            TokenEconomyRequest(
                required_refs=source.evidence_refs + source.authority_refs,
                base_checkpoint=source.source_checkpoint,
                session_has_base_checkpoint=False,
                recovery_required=False,
                broad_context_required=False,
                waiting_external=False,
                invocation_mode=executor.invocation_mode,
                session_mode=executor.session_mode,
                user_facing=False,
                deep_reasoning_required=False,
            )
        )
        compact = compiler.compile(
            source,
            executor=executor,
            token_economy=decision,
        )
        if full.packet_sha256 != compact.packet_sha256:
            raise RuntimeError("packet_hash_changed")
        if full.canonical_payload_json != compact.canonical_payload_json:
            raise RuntimeError("canonical_payload_changed")

        full_bytes = len(full.text.encode("utf-8"))
        compact_bytes = len(compact.text.encode("utf-8"))
        saved = full_bytes - compact_bytes
        reduction = 0.0 if full_bytes == 0 else saved / full_bytes

        rows.append(
            {
                "case": name,
                "packet_sha256": compact.packet_sha256,
                "context_mode": decision.context.context_mode.value,
                "reasoning_profile": decision.budget.reasoning_profile.value,
                "communication_mode": decision.budget.communication_mode.value,
                "max_output_tokens": decision.budget.max_output_tokens,
                "legacy_full_bytes": full_bytes,
                "compact_bytes": compact_bytes,
                "bytes_saved": saved,
                "reduction_fraction": round(reduction, 6),
                "canonical_identity_preserved": True,
            }
        )

    full_total = sum(int(row["legacy_full_bytes"]) for row in rows)
    compact_total = sum(int(row["compact_bytes"]) for row in rows)
    total_saved = full_total - compact_total
    total_reduction = (
        0.0 if full_total == 0 else total_saved / full_total
    )
    return {
        "schema_version": 1,
        "artifact_id": "workspace-token-economy-e4-0-replay-v1",
        "model_calls": 0,
        "codex_calls": 0,
        "paid_api_calls": 0,
        "source_fixture": "accepted research-iterate E2/A10 packet shapes",
        "measurement_unit": "utf8_worker_packet_bytes",
        "notes": [
            "Byte reduction is an offline deterministic proxy for input-token reduction; exact provider token accounting remains a live telemetry concern.",
            "Canonical payload JSON and packet SHA are identical between full and compact renderings.",
            "This replay does not assume a persistent-session checkpoint; compact cases therefore begin REF_ONLY.",
        ],
        "cases": rows,
        "totals": {
            "legacy_full_bytes": full_total,
            "compact_bytes": compact_total,
            "bytes_saved": total_saved,
            "reduction_fraction": round(total_reduction, 6),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
