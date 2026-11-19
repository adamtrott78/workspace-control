"""Ephemeral hidden-oracle fixture generation for resumable-reasoning benchmarks.

The worker-visible fixture and public seal may be persisted in Git. The oracle,
seed, and seal nonce are evaluator-only and MUST remain outside worker-readable
state until an optional post-run audit reveal.

This module is authority-free and uses only deterministic synthetic data.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import random
from typing import Any, Mapping


GENERATOR_ID = "workspace-resumable-reasoning-ephemeral-v1"

HYPOTHESES = {
    "H_queue": "The regression is primarily queue-capacity saturation.",
    "H_retry_state": "Retry state is incorrectly retained across request boundaries.",
    "H_clock_bucket": "Timeout timestamp quantization bunches retries into the same bucket.",
}

EXPERIMENTS = {
    "E_queue_4x": "Increase queue capacity by 4x while holding load and retry policy fixed.",
    "E_force_retry_reset": "Reset retry state at every request boundary while preserving pooling.",
    "E_clock_quantization": "Replace quantized timeout timestamps with monotonic high-resolution timestamps.",
    "E_half_concurrency": "Halve concurrency without changing the suspected mechanisms.",
}

TARGET_EXPERIMENT = {
    "H_queue": "E_queue_4x",
    "H_retry_state": "E_force_retry_reset",
    "H_clock_bucket": "E_clock_quantization",
}


class EphemeralFixtureError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_hex(value: bytes) -> str:
    return sha256(value).hexdigest()


def _require_secret_hex(value: str, *, field: str, min_bytes: int = 16) -> bytes:
    if not isinstance(value, str):
        raise EphemeralFixtureError(f"{field} must be hex text")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise EphemeralFixtureError(f"{field} must be valid hex") from exc
    if len(raw) < min_bytes:
        raise EphemeralFixtureError(f"{field} must contain at least {min_bytes} secret bytes")
    return raw


def generate_bundle(*, seed_hex: str, seal_nonce_hex: str) -> dict[str, dict[str, Any]]:
    """Return public fixture, evaluator oracle, and public commitment record.

    seed_hex and seal_nonce_hex are evaluator secrets. Neither is copied into
    the public fixture or public seal.
    """
    seed = _require_secret_hex(seed_hex, field="seed_hex")
    nonce = _require_secret_hex(seal_nonce_hex, field="seal_nonce_hex")
    rng = random.Random(int.from_bytes(seed, "big"))

    expected = rng.choice(sorted(HYPOTHESES))
    target_experiment = TARGET_EXPERIMENT[expected]
    non_targets = [x for x in sorted(HYPOTHESES) if x != expected]

    baseline_p95 = rng.randint(395, 455)
    baseline_retries = round(rng.uniform(2.7, 3.4), 2)
    target_p95 = rng.randint(205, 238)
    target_retries = round(rng.uniform(0.9, 1.2), 2)

    fixture_token = _sha256_hex(
        GENERATOR_ID.encode("utf-8") + b":" + seed
    )[:20]
    fixture_id = f"research-iterate-ephemeral-{fixture_token}"

    public_fixture = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "family": "research_iterate",
        "visibility": "worker_visible",
        "generator_id": GENERATOR_ID,
        "objective": (
            "Determine the primary mechanism causing a fresh synthetic request-latency "
            "regression. Use at least two experiment/result cycles, reject the competing "
            "mechanisms supported poorly by evidence, and explain why load relief alone "
            "is not causal identification."
        ),
        "starting_observations": [
            {
                "id": "O1",
                "observation": (
                    f"At the reference load, p95 latency is {baseline_p95} ms and mean "
                    f"retries per request are {baseline_retries}."
                ),
            },
            {
                "id": "O2",
                "observation": (
                    f"Halving concurrency lowers p95 latency by {rng.randint(80, 125)} ms "
                    "but retry amplification remains abnormal."
                ),
                "warning": "This observation is real but intentionally non-discriminating.",
            },
            {
                "id": "O3",
                "observation": (
                    f"CPU stays below {rng.randint(42, 57)}% and observed queue occupancy "
                    f"below {rng.randint(55, 69)}% in the baseline trace."
                ),
            },
        ],
        "candidate_hypotheses": [
            {"id": key, "statement": HYPOTHESES[key]}
            for key in sorted(HYPOTHESES)
        ],
        "experiment_catalog": [
            {"id": key, "intervention": EXPERIMENTS[key], "cost": 1}
            for key in sorted(EXPERIMENTS)
        ],
        "worker_contract": {
            "minimum_experiment_cycles_before_terminal_claim": 2,
            "must_reject_at_least_one_competing_hypothesis": True,
            "must_address_observation": "O2",
            "terminal_output_fields": [
                "final_hypothesis",
                "rejected_hypotheses",
                "observed_results",
                "addressed_observations",
                "rationale",
            ],
            "oracle_is_evaluator_only": True,
        },
        "authority": {
            "execution_authority": False,
            "production_mutation": False,
            "external_submission": False,
            "fixture_only": True,
        },
    }

    result_map: dict[str, dict[str, Any]] = {}
    for experiment_id in sorted(EXPERIMENTS):
        if experiment_id == target_experiment:
            result_map[experiment_id] = {
                "p95_latency_ms": target_p95,
                "mean_retries": target_retries,
                "effect": "causal_mechanism_removed",
            }
        elif experiment_id == "E_half_concurrency":
            result_map[experiment_id] = {
                "p95_latency_ms": baseline_p95 - rng.randint(75, 120),
                "mean_retries": round(max(2.4, baseline_retries - rng.uniform(0.0, 0.25)), 2),
                "effect": "load_relief_without_mechanism_removal",
            }
        else:
            result_map[experiment_id] = {
                "p95_latency_ms": baseline_p95 - rng.randint(0, 18),
                "mean_retries": round(max(2.5, baseline_retries - rng.uniform(0.0, 0.18)), 2),
                "effect": "no_material_mechanism_change",
            }

    oracle = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "visibility": "evaluator_only_do_not_supply_to_reasoning_worker",
        "generator_id": GENERATOR_ID,
        "experiment_results": result_map,
        "terminal_criteria": {
            "expected_hypothesis": expected,
            "minimum_unique_experiments": 2,
            "required_experiment_groups": [
                [target_experiment],
                [
                    experiment_id
                    for experiment_id in sorted(TARGET_EXPERIMENT.values())
                    if experiment_id != target_experiment
                ],
            ],
            "required_rejected_hypotheses": non_targets,
            "required_addressed_observations": ["O2"],
        },
        "generation_metadata": {
            "seed_commitment": _sha256_hex(seed),
            "secret_material_in_worker_state": False,
        },
    }

    public_hash = _sha256_hex(_canonical_bytes(public_fixture))
    oracle_bytes = _canonical_bytes(oracle)
    oracle_commitment = _sha256_hex(
        nonce + b":" + bytes.fromhex(public_hash) + b":" + oracle_bytes
    )

    public_seal = {
        "schema_version": 1,
        "seal_type": "sha256_hidden_nonce_commitment",
        "generator_id": GENERATOR_ID,
        "fixture_id": fixture_id,
        "public_fixture_sha256": public_hash,
        "oracle_commitment_sha256": oracle_commitment,
        "nonce_visibility": "evaluator_only_until_optional_audit_reveal",
        "oracle_visibility": "evaluator_only",
    }

    return {
        "public_fixture": public_fixture,
        "evaluator_oracle": oracle,
        "public_seal": public_seal,
    }


def verify_bundle(
    *,
    public_fixture: Mapping[str, Any],
    evaluator_oracle: Mapping[str, Any],
    public_seal: Mapping[str, Any],
    seal_nonce_hex: str,
) -> bool:
    nonce = _require_secret_hex(seal_nonce_hex, field="seal_nonce_hex")
    if public_fixture.get("fixture_id") != evaluator_oracle.get("fixture_id"):
        return False
    if public_fixture.get("fixture_id") != public_seal.get("fixture_id"):
        return False
    public_hash = _sha256_hex(_canonical_bytes(public_fixture))
    if public_hash != public_seal.get("public_fixture_sha256"):
        return False
    commitment = _sha256_hex(
        nonce
        + b":"
        + bytes.fromhex(public_hash)
        + b":"
        + _canonical_bytes(evaluator_oracle)
    )
    return commitment == public_seal.get("oracle_commitment_sha256")


def worker_packet_material(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Return the only bundle material eligible for a scored worker packet."""
    return {
        "public_fixture": deepcopy(bundle["public_fixture"]),
        "public_seal": deepcopy(bundle["public_seal"]),
    }
