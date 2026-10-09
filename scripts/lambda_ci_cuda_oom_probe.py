#!/usr/bin/env python3
"""Trusted CUDA OOM acceptance probe.

This script is installed root-owned and is not reachable from candidate-controlled
workflow inputs. It consumes one opaque stdin line so the launcher can clear the
ephemeral JIT config, then requests a single CUDA allocation larger than current
free VRAM. Only an actual torch CUDA OOM maps to the dedicated probe exit code.
"""

from __future__ import annotations

import sys

CUDA_OOM_EXIT = 86
UNEXPECTED_SUCCESS_EXIT = 87
UNEXPECTED_ERROR_EXIT = 88


def main() -> int:
    _ = sys.stdin.readline()

    try:
        import torch

        if not torch.cuda.is_available():
            return UNEXPECTED_ERROR_EXIT

        torch.cuda.set_device(0)
        free_bytes, _total_bytes = torch.cuda.mem_get_info()

        request_bytes = int(free_bytes) + (256 * 1024 * 1024)

        try:
            _allocation = torch.empty(
                (request_bytes,),
                dtype=torch.uint8,
                device="cuda",
            )
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            return CUDA_OOM_EXIT
        except RuntimeError as exc:
            # Some torch/CUDA builds expose allocation OOM as RuntimeError.
            # The trusted probe itself inspects the runtime exception; the root
            # classifier never trusts candidate stdout/stderr text.
            if "out of memory" in str(exc).lower():
                torch.cuda.empty_cache()
                return CUDA_OOM_EXIT
            raise

        del _allocation
        torch.cuda.empty_cache()
        return UNEXPECTED_SUCCESS_EXIT

    except Exception:
        return UNEXPECTED_ERROR_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
