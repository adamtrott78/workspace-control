#!/usr/bin/env python3
"""Trusted dual-GPU timeout acceptance probe.

Root installs this immutable probe and may bind it only in a synthetic
gpu-heavy/model-eval-dual-gpu host-acceptance spec. It consumes the opaque JIT
line, proves both visible GPUs participate in NCCL, then deliberately remains
alive until systemd RuntimeMaxSec terminates the entire cgroup.
"""

from __future__ import annotations

import datetime
import os
import socket
import sys
import time

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

EXPECTED_UUIDS = (
    "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea",
    "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6",
)


def free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def worker(rank: int, port: int) -> None:
    os.environ["MASTER_ADDR"] = "127.0.0.1"
    os.environ["MASTER_PORT"] = str(port)

    torch.cuda.set_device(rank)
    dist.init_process_group(
        backend="nccl",
        rank=rank,
        world_size=2,
        timeout=datetime.timedelta(seconds=30),
    )

    try:
        tensor = torch.full(
            (8 * 1024 * 1024,),
            float(rank + 1),
            dtype=torch.float32,
            device=f"cuda:{rank}",
        )
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
        torch.cuda.synchronize(rank)
        if float(tensor[0].item()) != 3.0:
            raise RuntimeError("dual timeout probe NCCL all-reduce mismatch")
        # Deliberately exceed the root-authored RuntimeMaxSec acceptance bound.
        time.sleep(600)
    finally:
        if dist.is_initialized():
            dist.destroy_process_group()


def main() -> int:
    _ = sys.stdin.readline()

    visible = tuple(os.environ.get("CUDA_VISIBLE_DEVICES", "").split(","))
    if visible != EXPECTED_UUIDS:
        return 91
    if torch.cuda.device_count() != 2:
        return 92

    mp.spawn(
        worker,
        args=(free_port(),),
        nprocs=2,
        join=True,
    )
    # Reaching this line before systemd timeout is a failure.
    return 93


if __name__ == "__main__":
    raise SystemExit(main())
