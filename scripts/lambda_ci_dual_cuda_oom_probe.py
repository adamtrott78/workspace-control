#!/usr/bin/env python3
"""Trusted dual-GPU CUDA OOM acceptance probe.

Root installs this immutable probe and may bind it only in a synthetic
gpu-heavy/model-eval-dual-gpu host-acceptance spec. It consumes the opaque JIT
line and requires a real CUDA allocation OOM independently on both exact
visible GPUs before returning the dedicated trusted exit code.
"""

from __future__ import annotations

import os
import sys

DUAL_CUDA_OOM_EXIT = 86
UNEXPECTED_SUCCESS_EXIT = 87
UNEXPECTED_ERROR_EXIT = 88

EXPECTED_UUIDS = (
    "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
    "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
)


def allocation_oom_on_device(torch, device: int) -> bool:
    torch.cuda.set_device(device)
    free_bytes, _total_bytes = torch.cuda.mem_get_info(device)
    request_bytes = int(free_bytes) + (256 * 1024 * 1024)

    try:
        allocation = torch.empty(
            (request_bytes,),
            dtype=torch.uint8,
            device=f"cuda:{device}",
        )
    except torch.OutOfMemoryError:
        torch.cuda.empty_cache()
        return True
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            torch.cuda.empty_cache()
            return True
        raise

    del allocation
    torch.cuda.empty_cache()
    return False


def main() -> int:
    _ = sys.stdin.readline()

    try:
        import torch

        visible = tuple(os.environ.get("CUDA_VISIBLE_DEVICES", "").split(","))
        if visible != EXPECTED_UUIDS:
            return UNEXPECTED_ERROR_EXIT
        if not torch.cuda.is_available() or torch.cuda.device_count() != 2:
            return UNEXPECTED_ERROR_EXIT

        results = [
            allocation_oom_on_device(torch, 0),
            allocation_oom_on_device(torch, 1),
        ]

        if results == [True, True]:
            return DUAL_CUDA_OOM_EXIT
        return UNEXPECTED_SUCCESS_EXIT

    except Exception:
        return UNEXPECTED_ERROR_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
