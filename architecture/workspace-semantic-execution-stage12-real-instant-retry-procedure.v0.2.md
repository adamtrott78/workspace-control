# Stage-12 Real-Instant Retry Procedure v0.2

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Purpose

Replace the failed Attempt-01 launch sequencing with a bounded retry procedure that cannot consume a live-attempt authority merely because the Linux transaction was started before the Windows managed runtime was actually prepared.

This procedure does **not** authorize a second live Stage-12 attempt.

## Exact executable bindings

- Executable source commit: `b0466c03acb9d6b863df421e2c116c84bff312f6`
- Linux v2 transaction:
  - `benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v2.sh`
  - blob `962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca`
- Real-Instant harness:
  - `benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py`
  - blob `7b1feb8fa13cf0ea46883b07831e829fd9e7e75d`
- Windows launcher:
  - `operator-bridge/tools/run-stage12-real-instant.ps1`
  - blob `d9d474ca6870585c9e4767f551086e17b4525fbc`
- Candidate branch baseline:
  - `worker-result-candidates-v1@0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`

## What changes from Attempt 01

1. Windows preparation is completed **first**.
2. The Windows launcher is invoked from a single complete PowerShell command line; no multiline `try/finally` paste is used.
3. The operator must observe:
   `STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`
4. The Linux v2 transaction performs read-only/exact-state preflight and then stops at a mandatory readiness prompt.
5. The operator must type the exact Windows marker into that prompt.
6. Only after that exact marker is accepted does Linux print:
   `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`
7. A future retry authority, if granted, must define that marker as the live-attempt consumption point.
8. On abort/failure after route activation, cleanup rechecks the exact preexisting Serve/Funnel snapshot. Cleanup failure is surfaced and the runtime evidence directory is preserved instead of silently deleting evidence.

The manual Windows readiness marker is a setup/readiness gate only. It is not a model result relay and carries no ChatGPT output.

## Windows preparation

Run in Windows PowerShell. The command below is intentionally a single executable line to avoid PowerShell continuation-prompt ambiguity:

```powershell
$ErrorActionPreference='Stop'; $RepoUrl='https://github.com/adamtrott78/workspace-control.git'; $SourceSha='b0466c03acb9d6b863df421e2c116c84bff312f6'; $Launcher='operator-bridge/tools/run-stage12-real-instant.ps1'; $LauncherBlob='d9d474ca6870585c9e4767f551086e17b4525fbc'; $Stage=Join-Path $env:TEMP 'workspace-control-stage12-retry-v2'; if(Test-Path -LiteralPath $Stage){throw "STAGE12_STAGE_DIRECTORY_ALREADY_EXISTS: $Stage"}; git init -q $Stage; if($LASTEXITCODE -ne 0){throw 'git init failed'}; git -C $Stage remote add origin $RepoUrl; git -C $Stage fetch --no-tags origin workspace-semantic-execution-migration-v1; if($LASTEXITCODE -ne 0){throw 'fetch failed'}; git -C $Stage checkout --detach $SourceSha; if($LASTEXITCODE -ne 0){throw 'checkout failed'}; $Head=(git -C $Stage rev-parse HEAD).Trim().ToLowerInvariant(); if($Head -ne $SourceSha){throw "SOURCE_HEAD_MISMATCH: $Head"}; $Spec="{0}:{1}" -f $SourceSha,$Launcher; $Blob=(git -C $Stage rev-parse $Spec).Trim().ToLowerInvariant(); if($Blob -ne $LauncherBlob){throw "LAUNCHER_BLOB_MISMATCH: $Blob"}; & (Join-Path $Stage 'operator-bridge\tools\run-stage12-real-instant.ps1') -RepositoryRoot $Stage
```

The isolated Firefox profile must open. Authenticate to normal ChatGPT manually, select normal Instant manually, then press Enter only in the launcher prompt.

Do not start the live Linux phase until the same PowerShell window prints:

`STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

Leave that PowerShell window running.

## Linux materialization and pre-live gate

Materialize executable source `b0466c03…` from the authoritative repository and verify the v2 transaction/harness blobs before invocation.

When the v2 transaction prints:

`STAGE12_PRELIVE_WINDOWS_CONFIRMATION_REQUIRED=STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

type exactly:

`STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

and press Enter.

If the marker is absent, mistyped, or the Windows launcher is not actually prepared, stop. Do not improvise a substitute.

A future retry authority is consumed only when the transaction then prints:

`STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`

## Real worker interactions

Only after the live-authority consumption marker:

- at `STAGE12_Q1_READY`: Ctrl+Space -> Ctrl+V -> Enter
- at `STAGE12_Q2_REUSE_READY`: Ctrl+Space -> Ctrl+V -> Enter
- at `STAGE12_Q3_REPLACEMENT_READY`: Ctrl+Space -> Ctrl+V -> Enter

Do not manually search for worker tabs. Do not copy worker results to Linux. The worker must publish its immutable GitHub candidate.

## Required success

Require all previous Stage-12 acceptance evidence plus:

- `STAGE12_WINDOWS_READY_GATE=PASS`
- `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`
- `PRIVATE_ROUTE_STAGE12_REAL_INSTANT_V2=PASS`
- exact Serve/Funnel restoration on normal completion
- `STAGE12_CLEANUP_ROUTE_RESTORED=PASS` on abnormal exit after route activation
- Windows launcher final `STAGE12_WINDOWS_CLEANUP=PASS`

## Failure policy

Any failure after the future live-authority consumption marker consumes that future attempt authority. Fail closed, preserve exact evidence, restore reviewed temporary state, and obtain another fresh reviewed authority before retry.

No browser permission widening, credential automation, DOM/page-content scraping, automatic typing/submission, paid/API-key fallback, public/Funnel exposure, production PostgreSQL mutation, GPU use, PADataset mutation, or generic Workspace Shell authority is introduced by this candidate.
