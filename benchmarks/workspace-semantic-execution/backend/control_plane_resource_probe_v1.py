"""Bounded resource probe for the semantic-execution control plane."""
from __future__ import annotations

import json
import os
from pathlib import Path
import resource
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "semantic-execution" / "src"
sys.path.insert(0, str(SRC))

from workspace_semantic_execution.domain import DomainKernel  # noqa: E402


ITERATIONS = 1000
RSS_LIMIT_MIB = 1024.0
BURST_CPU_CORE_LIMIT = 2.0


def main() -> int:
    gpu_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if gpu_visible != "":
        raise RuntimeError(
            "control_plane_gpu_visibility_must_be_empty:"
            f"{gpu_visible!r}"
        )

    graph = DomainKernel.create_graph([DomainKernel.create_process("probe")])
    generation = 0
    wall_start = time.perf_counter()
    cpu_start = time.process_time()

    for index in range(ITERATIONS):
        lease = f"L{generation}"
        graph = DomainKernel.claim(
            graph,
            "probe",
            worker_id=f"W{generation}",
            lease_id=lease,
            expected_generation=generation,
        )
        graph = DomainKernel.start(
            graph,
            "probe",
            lease_id=lease,
            expected_generation=generation,
        )
        graph = DomainKernel.recover(
            graph,
            "probe",
            expected_generation=generation,
            reason=f"probe:{index}",
        )
        generation += 1

    cpu_seconds = time.process_time() - cpu_start
    wall_seconds = time.perf_counter() - wall_start
    cpu_cores = cpu_seconds / max(wall_seconds, 1e-9)

    # Linux reports ru_maxrss in KiB.
    rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

    result = {
        "probe": "semantic-execution-control-plane-resource-v1",
        "iterations": ITERATIONS,
        "cuda_visible_devices": gpu_visible,
        "cpu_seconds": cpu_seconds,
        "wall_seconds": wall_seconds,
        "observed_cpu_cores": cpu_cores,
        "max_rss_mib": rss_mib,
        "targets": {
            "gpu_visible_devices": 0,
            "gpu_vram_bytes": 0,
            "burst_cpu_cores_lte": BURST_CPU_CORE_LIMIT,
            "application_rss_mib_lte": RSS_LIMIT_MIB,
        },
    }
    print(json.dumps(result, sort_keys=True))

    if cpu_cores > BURST_CPU_CORE_LIMIT:
        raise RuntimeError(
            f"control_plane_cpu_budget_exceeded:{cpu_cores:.3f}"
        )
    if rss_mib > RSS_LIMIT_MIB:
        raise RuntimeError(
            f"control_plane_rss_budget_exceeded:{rss_mib:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
