# E2 Live Durable-Recovery Procedure v0.2

Status: **VALIDATED EXECUTABLE REVIEW / NOT AUTHORITY**

Executable implementation head: `d04d06cee576a21e77286f7f6efe66485ec34375`  
Candidate baseline: `fdb801d895068c78b2e2e11e6984173812884deb`

## Service sequence

Use only **Ctrl+Space -> Ctrl+V -> Enter** at each manual service point:

1. root decomposition
2. analysis generation 0 — this worker is deliberately fenced immediately after local submission
3. analysis generation 1 replacement — must be serviced from a replacement managed session generation
4. Workspace Shell read-only probe
5. final synthesis

The backend must observe and reject the late generation-0 analysis candidate without durable mutation, rehydrate orchestration state from PostgreSQL, replace the persistent session at generation 1, and continue without manual state reconstruction.

## Failure boundary

Once `E2_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS` is emitted, success or failure consumes the one-shot authority. No silent retry.

This document grants no execution authority.
