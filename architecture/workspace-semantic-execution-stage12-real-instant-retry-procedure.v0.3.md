# Stage-12 Real-Instant Retry Procedure v0.3

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Purpose

Repair the pre-live Windows setup blocker discovered under the still-unconsumed v0.2 authority: the host's PowerShell execution policy rejected the pinned `.ps1` launcher before it executed.

This candidate preserves the validated v0.2 Windows-first sequencing, Linux readiness gate, browser/manual-auth boundary, launcher bytes, Linux transaction bytes, harness bytes, and candidate baseline. The only operational delta is the Windows invocation mechanism.

This procedure does **not** authorize a live Stage-12 attempt.

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

## v0.3 Windows execution-policy repair

The reviewed launcher itself is unchanged.

The operator command:

1. Detects the current PowerShell executable.
2. Fails closed if Windows Group Policy defines `MachinePolicy` or `UserPolicy`; this candidate does not override centrally managed policy.
3. Does **not** call `Set-ExecutionPolicy`, edit the registry, call `Unblock-File`, or persist any execution-policy change.
4. Starts one child PowerShell process with `-ExecutionPolicy Bypass`; this applies only to that child process.
5. The child executes the exact pinned launcher blob and remains interactive for the existing manual-auth / manual-Instant / cleanup prompts.
6. If the child launcher exits nonzero, the staged checkout is preserved for diagnosis. On success, the staged checkout is removed.

## Windows preparation

Run the following as **one complete line** in Windows PowerShell:

```powershell
$ErrorActionPreference='Stop'; $RepoUrl='https://github.com/adamtrott78/workspace-control.git'; $SourceSha='b0466c03acb9d6b863df421e2c116c84bff312f6'; $Launcher='operator-bridge/tools/run-stage12-real-instant.ps1'; $LauncherBlob='d9d474ca6870585c9e4767f551086e17b4525fbc'; $Stage=Join-Path $env:TEMP 'workspace-control-stage12-retry-v3'; if(Test-Path -LiteralPath $Stage){throw "STAGE12_STAGE_DIRECTORY_ALREADY_EXISTS: $Stage"}; $Engine=(Get-Process -Id $PID).Path; $EngineName=[IO.Path]::GetFileName($Engine).ToLowerInvariant(); if($EngineName -notin @('powershell.exe','pwsh.exe')){throw "UNEXPECTED_POWERSHELL_ENGINE: $Engine"}; $Policy=@{}; Get-ExecutionPolicy -List | ForEach-Object { $Policy[$_.Scope.ToString()]=$_.ExecutionPolicy.ToString() }; if($Policy['MachinePolicy'] -ne 'Undefined' -or $Policy['UserPolicy'] -ne 'Undefined'){throw "GROUP_POLICY_EXECUTION_POLICY_PRESENT: MachinePolicy=$($Policy['MachinePolicy']) UserPolicy=$($Policy['UserPolicy'])"}; git init -q $Stage; if($LASTEXITCODE -ne 0){throw 'git init failed'}; git -C $Stage remote add origin $RepoUrl; git -C $Stage fetch --no-tags origin workspace-semantic-execution-migration-v1; if($LASTEXITCODE -ne 0){throw 'fetch failed'}; git -C $Stage checkout --detach $SourceSha; if($LASTEXITCODE -ne 0){throw 'checkout failed'}; $Head=(git -C $Stage rev-parse HEAD).Trim().ToLowerInvariant(); if($Head -ne $SourceSha){throw "SOURCE_HEAD_MISMATCH: $Head"}; $Spec="{0}:{1}" -f $SourceSha,$Launcher; $Blob=(git -C $Stage rev-parse $Spec).Trim().ToLowerInvariant(); if($Blob -ne $LauncherBlob){throw "LAUNCHER_BLOB_MISMATCH: $Blob"}; $LauncherPath=Join-Path $Stage 'operator-bridge\tools\run-stage12-real-instant.ps1'; & $Engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $LauncherPath -RepositoryRoot $Stage; if($LASTEXITCODE -ne 0){throw "STAGE12_WINDOWS_LAUNCHER_EXIT=$LASTEXITCODE"}; Remove-Item -LiteralPath $Stage -Recurse -Force
```

The isolated Firefox profile must open. Authenticate to normal ChatGPT manually, select normal Instant manually, then press Enter only at the launcher's reviewed manual setup prompt.

Do not start Linux until the Windows launcher prints:

`STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

Leave the launcher/isolated Firefox running.

## Linux pre-live gate

The Linux transaction remains the exact v2 blob above.

At:

`STAGE12_PRELIVE_WINDOWS_CONFIRMATION_REQUIRED=STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

type exactly:

`STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

Only after Linux prints:

`STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`

has a future one-shot live authority been consumed.

## Real worker interactions

Only after the live-consumption marker:

- `STAGE12_Q1_READY`: Ctrl+Space -> Ctrl+V -> Enter
- `STAGE12_Q2_REUSE_READY`: Ctrl+Space -> Ctrl+V -> Enter
- `STAGE12_Q3_REPLACEMENT_READY`: Ctrl+Space -> Ctrl+V -> Enter

No manual worker-result relay is permitted.

## Failure / cleanup

Before the live-consumption marker, aborting remains non-consuming.

After the marker, any success or failure consumes that future one-shot authority. Fail closed, preserve evidence, restore exact reviewed temporary state, and do not silently retry.

This candidate introduces no permanent execution-policy change, no credential automation, no DOM/page-content scraping, no automatic typing/submission, no browser-permission widening, no API-key/paid fallback, no public/Funnel exposure, no production PostgreSQL mutation, no GPU use, no PADataset mutation, and no generic Workspace Shell authority.
