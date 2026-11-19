# Stage-12 Real-Instant Retry Procedure v1.0

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Purpose

Repair the consumed v0.9 Q1 Windows foreground-activation failure without changing the Linux private-route transaction, Real-Instant harness, candidate-result branch, manual typing boundary, or live-consumption semantics.

The v0.9 attempt reached `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS` and `STAGE12_Q1_READY`. The Firefox adapter successfully implements `ACTIVATE_WORKER_BINDING` by activating the managed tab and requesting `browser.windows.update(..., { focused: true })`, but Windows did not bring the isolated Firefox window to the foreground. The pinned native helper already contains a verified Win32 fallback, `ForegroundPreparedWorkerWindow()`, which calls `SetForegroundWindow` and verifies the result with `GetForegroundWindow`; the hotkey LocalPrepared path did not invoke it.

v1.0 adds exactly that existing native foreground fallback call immediately before `RecordPreparedWorkerWindow()` in the LocalPrepared hotkey path. No automatic typing or submission is added.

This procedure does **not** authorize a live Stage-12 attempt.

## Exact executable bindings

- Windows executable source commit: `1ecc094a62e2ed96b278ab954d46246e26dc33fd`
- Windows foreground repair file: `operator-bridge/src/WorkspaceOperator/Windows/TrayApplicationContext.cs`
- Windows foreground repair blob: `2e0d2248927aaff4afbbe9e036bc810d729cdb3d`
- Windows launcher path: `operator-bridge/tools/run-stage12-real-instant.ps1`
- Windows launcher blob: `d9d474ca6870585c9e4767f551086e17b4525fbc`
- Linux transaction path: `benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v3.sh`
- Linux transaction blob: `3eb352f456d84de565514e2a7046e847ea0d25ea`
- Real-Instant harness blob: `7b1feb8fa13cf0ea46883b07831e829fd9e7e75d`
- Candidate-result baseline: `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`
- Validated foreground-repair candidate: `1ecc094a62e2ed96b278ab954d46246e26dc33fd`
- Candidate validation: Workspace #3030 / Semantic #330 / Operator #603 = SUCCESS

## Exact v1.0 Windows delta

The production behavior change is confined to the `DispatchOutcome.LocalPrepared` branch in `TrayApplicationContext.cs`:

```csharp
_workerWindowSafety.ForegroundPreparedWorkerWindow();
_workerWindowSafety.RecordPreparedWorkerWindow();
```

The first call invokes the already-existing Win32 foreground fallback; the second captures the now-foreground prepared Firefox window for later queue-empty minimization.

The regression guard requires the foreground call to exist in this branch and occur before the capture call.

## Retained boundaries

- Manual login only.
- Manual Instant selection only.
- Manual worker service sequence remains exactly `Ctrl+Space -> Ctrl+V -> Enter`.
- No automatic typing or submission.
- No DOM/page-content scraping.
- No credential automation.
- No API-key or paid-API fallback.
- No Funnel.
- No public listener.
- No non-loopback backend.
- No production PostgreSQL mutation.
- No GPU.
- No PADataset mutation.
- No Workspace Shell authority widening.
- Candidate results remain on `worker-result-candidates-v1` under `worker-results/stage12/<run-token>/`.
- Source/authority branch result writes remain forbidden.
- Live authority remains unconsumed until Linux prints `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`.
- After that marker, success or failure consumes the attempt.

## Mandatory predecessor cleanup gate

The consumed v0.9 runtime must be fully cleaned up before any v1.0 live retry:

1. Linux v0.9 process must exit or be interrupted through its existing cleanup trap.
2. Exact Tailscale pre-run configuration must be restored.
3. The Windows v0.9 helper/isolated Firefox runtime must be cleaned up.
4. Any stale `%TEMP%\workspace-control-stage12-retry-v7` checkout must be removed using the already-bounded cleanup path.
5. Candidate-result branch must still equal the required baseline before a new live attempt.

## Exact Windows preparation command

Run only after predecessor cleanup is verified and only after fresh v1.0 authority exists:

```powershell
$ErrorActionPreference='Stop'; $RepoUrl='https://github.com/adamtrott78/workspace-control.git'; $SourceSha='1ecc094a62e2ed96b278ab954d46246e26dc33fd'; $Launcher='operator-bridge/tools/run-stage12-real-instant.ps1'; $LauncherBlob='d9d474ca6870585c9e4767f551086e17b4525fbc'; $Stage=Join-Path $env:TEMP 'workspace-control-stage12-retry-v7'; if(Test-Path -LiteralPath $Stage){throw "STAGE12_STAGE_DIRECTORY_ALREADY_EXISTS: $Stage"}; $Engine=(Get-Process -Id $PID).Path; $EngineName=[IO.Path]::GetFileName($Engine).ToLowerInvariant(); if($EngineName -notin @('powershell.exe','pwsh.exe')){throw "UNEXPECTED_POWERSHELL_ENGINE: $Engine"}; $Policy=@{}; Get-ExecutionPolicy -List | ForEach-Object { $Policy[$_.Scope.ToString()]=$_.ExecutionPolicy.ToString() }; if($Policy['MachinePolicy'] -ne 'Undefined' -or $Policy['UserPolicy'] -ne 'Undefined'){throw "GROUP_POLICY_EXECUTION_POLICY_PRESENT: MachinePolicy=$($Policy['MachinePolicy']) UserPolicy=$($Policy['UserPolicy'])"}; $DotnetCandidates=@(); $DotnetCmd=Get-Command dotnet -ErrorAction SilentlyContinue; if($DotnetCmd){$DotnetCandidates+=$DotnetCmd.Source}; if($env:ProgramFiles){$DotnetCandidates+=(Join-Path $env:ProgramFiles 'dotnet\dotnet.exe')}; if(${env:ProgramFiles(x86)}){$DotnetCandidates+=(Join-Path ${env:ProgramFiles(x86)} 'dotnet\dotnet.exe')}; if($env:LOCALAPPDATA){$DotnetCandidates+=(Join-Path $env:LOCALAPPDATA 'Microsoft\dotnet\dotnet.exe')}; if($env:USERPROFILE){$DotnetCandidates+=(Join-Path $env:USERPROFILE '.dotnet\dotnet.exe')}; $DotnetPath=$DotnetCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique | Select-Object -First 1; if(-not $DotnetPath){throw 'DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $DotnetVersion=(& $DotnetPath --version).Trim(); if($LASTEXITCODE -ne 0 -or $DotnetVersion -notmatch '^10\.'){throw "DOTNET10_VERSION_MISMATCH: $DotnetVersion"}; $DotnetDir=Split-Path -Parent $DotnetPath; $OldPath=$env:PATH; $OldDotnetRoot=$env:DOTNET_ROOT; $NodeDir=$null; $NodeCommand=Get-Command node.exe -ErrorAction SilentlyContinue; if($NodeCommand){$CurrentNodeDir=Split-Path -Parent $NodeCommand.Source; $CurrentNodeExe=Join-Path $CurrentNodeDir 'node.exe'; $CurrentNpmCmd=Join-Path $CurrentNodeDir 'npm.cmd'; if((Test-Path -LiteralPath $CurrentNodeExe) -and (Test-Path -LiteralPath $CurrentNpmCmd)){$CurrentNodeVersion=(& $CurrentNodeExe --version).Trim(); if($LASTEXITCODE -eq 0 -and $CurrentNodeVersion -match '^v24\.'){$CurrentNpmVersion=(& $CurrentNpmCmd --version).Trim(); if($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($CurrentNpmVersion)){$NodeDir=$CurrentNodeDir}}}}; if(-not $NodeDir){$ToolCache=if($env:RUNNER_TOOL_CACHE){$env:RUNNER_TOOL_CACHE}else{Join-Path $env:USERPROFILE 'actions-runner\_work\_tool'}; $NodeRoot=Join-Path $ToolCache 'node'; $NodeCandidates=@(Get-ChildItem $NodeRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^24\.\d+\.\d+$' } | Sort-Object { [version]$_.Name } -Descending); foreach($Candidate in $NodeCandidates){$CandidateDir=Join-Path $Candidate.FullName 'x64'; if((Test-Path -LiteralPath (Join-Path $CandidateDir 'node.exe')) -and (Test-Path -LiteralPath (Join-Path $CandidateDir 'npm.cmd'))){$NodeDir=$CandidateDir; break}}}; if(-not $NodeDir){throw 'NODE24_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $NodeExe=Join-Path $NodeDir 'node.exe'; $NpmCmd=Join-Path $NodeDir 'npm.cmd'; $NodeVersion=(& $NodeExe --version).Trim(); if($LASTEXITCODE -ne 0 -or $NodeVersion -notmatch '^v24\.'){throw "NODE24_VERSION_MISMATCH: $NodeVersion"}; $NpmVersion=(& $NpmCmd --version).Trim(); if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($NpmVersion)){throw 'NPM_NOT_AVAILABLE_IN_REVIEWED_NODE24'}; $env:PATH="$DotnetDir;$NodeDir;$OldPath"; $env:DOTNET_ROOT=$DotnetDir; try { git init -q $Stage; if($LASTEXITCODE -ne 0){throw 'git init failed'}; git -C $Stage remote add origin $RepoUrl; git -C $Stage fetch --no-tags origin workspace-semantic-execution-migration-v1; if($LASTEXITCODE -ne 0){throw 'fetch failed'}; git -C $Stage checkout --detach $SourceSha; if($LASTEXITCODE -ne 0){throw 'checkout failed'}; $Head=(git -C $Stage rev-parse HEAD).Trim().ToLowerInvariant(); if($Head -ne $SourceSha){throw "SOURCE_HEAD_MISMATCH: $Head"}; $Spec="{0}:{1}" -f $SourceSha,$Launcher; $Blob=(git -C $Stage rev-parse $Spec).Trim().ToLowerInvariant(); if($Blob -ne $LauncherBlob){throw "LAUNCHER_BLOB_MISMATCH: $Blob"}; $LauncherPath=Join-Path $Stage 'operator-bridge\tools\run-stage12-real-instant.ps1'; & $Engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $LauncherPath -RepositoryRoot $Stage; if($LASTEXITCODE -ne 0){throw "STAGE12_WINDOWS_LAUNCHER_EXIT=$LASTEXITCODE"}; Remove-Item -LiteralPath $Stage -Recurse -Force } finally { $env:PATH=$OldPath; $env:DOTNET_ROOT=$OldDotnetRoot }
```

After the isolated Firefox window opens:

1. Sign in manually.
2. Select Instant manually.
3. At the manual-auth confirmation prompt, press Enter exactly once.
4. Verify `STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`.
5. Leave the final Windows cleanup prompt untouched while Linux runs.

## Linux transaction

The Linux v3 transaction is unchanged from v0.9. A future v1.0 authority, if explicitly approved after validation, must bind the exact Linux v3 blob `3eb352f456d84de565514e2a7046e847ea0d25ea` and exact candidate baseline.

At each `STAGE12_*_READY` marker, the only worker-service interaction remains:

`Ctrl+Space -> Ctrl+V -> Enter`

No manual worker-tab search or manual result relay is allowed.

## Authority gate

This artifact is review-only. It grants zero live authority.

A new live retry requires:
1. v1.0 review/procedure exact-head validation,
2. verified predecessor cleanup,
3. fresh explicit operator approval binding these exact bytes,
4. authority-persistence validation before Windows/Linux execution.
