# Stage-12 Real-Instant Retry Procedure v0.9

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Purpose

Repair the pre-live Linux v2 declaration defect observed on 2026-11-18 under v0.8 authority. The exact reviewed Linux v2 blob `962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca` contains three literal two-byte `\n` sequences on one physical assignment line, joining the `HARNESS_REL`, `REPO_URL`, `CANDIDATE_BASELINE`, and `WINDOWS_READY_MARKER` declarations. Bash syntax validation accepts that text, but `set -u` later fails at line 102 because `REPO_URL` was never assigned.

v0.9 creates Linux v3 by replacing exactly those three literal `\n` byte pairs with three real LF line breaks and changing no other Linux transaction byte. Windows preparation, launcher, harness, candidate-result namespace, private-route constraints, manual-auth boundary, and live-consumption semantics are unchanged.

This procedure does **not** authorize a live Stage-12 attempt.

## Exact executable bindings

- Windows executable source commit: `b0466c03acb9d6b863df421e2c116c84bff312f6`
- Linux v2 predecessor blob: `962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca`
- Linux v3 candidate path: `benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v3.sh`
- Linux v3 candidate blob: `3eb352f456d84de565514e2a7046e847ea0d25ea`
- Real-Instant harness blob: `7b1feb8fa13cf0ea46883b07831e829fd9e7e75d`
- Windows launcher blob: `d9d474ca6870585c9e4767f551086e17b4525fbc`
- Candidate baseline: `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`
- Reviewed Node-binding source workflow blob: `1ea4135e0ff80454b5a8e5feac139d0177d3b764`

## v0.9 Linux declaration repair

The Linux v3 transaction is byte-for-byte identical to v2 except:

- v2 contains exactly three literal two-byte `\n` sequences.
- v3 contains zero literal `\n` sequences.
- Each of those three sequences is replaced by one real LF newline.
- The four declarations `HARNESS_REL`, `REPO_URL`, `CANDIDATE_BASELINE`, and `WINDOWS_READY_MARKER` are separate physical shell lines.
- No other Linux transaction byte changes.

## Windows preparation

The Windows command is exactly unchanged from v0.8. Run it as one complete line only after fresh v0.9 authority exists:

```powershell
$ErrorActionPreference='Stop'; $RepoUrl='https://github.com/adamtrott78/workspace-control.git'; $SourceSha='b0466c03acb9d6b863df421e2c116c84bff312f6'; $Launcher='operator-bridge/tools/run-stage12-real-instant.ps1'; $LauncherBlob='d9d474ca6870585c9e4767f551086e17b4525fbc'; $Stage=Join-Path $env:TEMP 'workspace-control-stage12-retry-v7'; if(Test-Path -LiteralPath $Stage){throw "STAGE12_STAGE_DIRECTORY_ALREADY_EXISTS: $Stage"}; $Engine=(Get-Process -Id $PID).Path; $EngineName=[IO.Path]::GetFileName($Engine).ToLowerInvariant(); if($EngineName -notin @('powershell.exe','pwsh.exe')){throw "UNEXPECTED_POWERSHELL_ENGINE: $Engine"}; $Policy=@{}; Get-ExecutionPolicy -List | ForEach-Object { $Policy[$_.Scope.ToString()]=$_.ExecutionPolicy.ToString() }; if($Policy['MachinePolicy'] -ne 'Undefined' -or $Policy['UserPolicy'] -ne 'Undefined'){throw "GROUP_POLICY_EXECUTION_POLICY_PRESENT: MachinePolicy=$($Policy['MachinePolicy']) UserPolicy=$($Policy['UserPolicy'])"}; $DotnetCandidates=@(); $DotnetCmd=Get-Command dotnet -ErrorAction SilentlyContinue; if($DotnetCmd){$DotnetCandidates+=$DotnetCmd.Source}; if($env:ProgramFiles){$DotnetCandidates+=(Join-Path $env:ProgramFiles 'dotnet\dotnet.exe')}; if(${env:ProgramFiles(x86)}){$DotnetCandidates+=(Join-Path ${env:ProgramFiles(x86)} 'dotnet\dotnet.exe')}; if($env:LOCALAPPDATA){$DotnetCandidates+=(Join-Path $env:LOCALAPPDATA 'Microsoft\dotnet\dotnet.exe')}; if($env:USERPROFILE){$DotnetCandidates+=(Join-Path $env:USERPROFILE '.dotnet\dotnet.exe')}; $DotnetPath=$DotnetCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique | Select-Object -First 1; if(-not $DotnetPath){throw 'DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $DotnetVersion=(& $DotnetPath --version).Trim(); if($LASTEXITCODE -ne 0 -or $DotnetVersion -notmatch '^10\.'){throw "DOTNET10_VERSION_MISMATCH: $DotnetVersion"}; $DotnetDir=Split-Path -Parent $DotnetPath; $OldPath=$env:PATH; $OldDotnetRoot=$env:DOTNET_ROOT; $NodeDir=$null; $NodeCommand=Get-Command node.exe -ErrorAction SilentlyContinue; if($NodeCommand){$CurrentNodeDir=Split-Path -Parent $NodeCommand.Source; $CurrentNodeExe=Join-Path $CurrentNodeDir 'node.exe'; $CurrentNpmCmd=Join-Path $CurrentNodeDir 'npm.cmd'; if((Test-Path -LiteralPath $CurrentNodeExe) -and (Test-Path -LiteralPath $CurrentNpmCmd)){$CurrentNodeVersion=(& $CurrentNodeExe --version).Trim(); if($LASTEXITCODE -eq 0 -and $CurrentNodeVersion -match '^v24\.'){$CurrentNpmVersion=(& $CurrentNpmCmd --version).Trim(); if($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($CurrentNpmVersion)){$NodeDir=$CurrentNodeDir}}}}; if(-not $NodeDir){$ToolCache=if($env:RUNNER_TOOL_CACHE){$env:RUNNER_TOOL_CACHE}else{Join-Path $env:USERPROFILE 'actions-runner\_work\_tool'}; $NodeRoot=Join-Path $ToolCache 'node'; $NodeCandidates=@(Get-ChildItem $NodeRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^24\.\d+\.\d+$' } | Sort-Object { [version]$_.Name } -Descending); foreach($Candidate in $NodeCandidates){$CandidateDir=Join-Path $Candidate.FullName 'x64'; if((Test-Path -LiteralPath (Join-Path $CandidateDir 'node.exe')) -and (Test-Path -LiteralPath (Join-Path $CandidateDir 'npm.cmd'))){$NodeDir=$CandidateDir; break}}}; if(-not $NodeDir){throw 'NODE24_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $NodeExe=Join-Path $NodeDir 'node.exe'; $NpmCmd=Join-Path $NodeDir 'npm.cmd'; $NodeVersion=(& $NodeExe --version).Trim(); if($LASTEXITCODE -ne 0 -or $NodeVersion -notmatch '^v24\.'){throw "NODE24_VERSION_MISMATCH: $NodeVersion"}; $NpmVersion=(& $NpmCmd --version).Trim(); if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($NpmVersion)){throw 'NPM_NOT_AVAILABLE_IN_REVIEWED_NODE24'}; $env:PATH="$DotnetDir;$NodeDir;$OldPath"; $env:DOTNET_ROOT=$DotnetDir; try { git init -q $Stage; if($LASTEXITCODE -ne 0){throw 'git init failed'}; git -C $Stage remote add origin $RepoUrl; git -C $Stage fetch --no-tags origin workspace-semantic-execution-migration-v1; if($LASTEXITCODE -ne 0){throw 'fetch failed'}; git -C $Stage checkout --detach $SourceSha; if($LASTEXITCODE -ne 0){throw 'checkout failed'}; $Head=(git -C $Stage rev-parse HEAD).Trim().ToLowerInvariant(); if($Head -ne $SourceSha){throw "SOURCE_HEAD_MISMATCH: $Head"}; $Spec="{0}:{1}" -f $SourceSha,$Launcher; $Blob=(git -C $Stage rev-parse $Spec).Trim().ToLowerInvariant(); if($Blob -ne $LauncherBlob){throw "LAUNCHER_BLOB_MISMATCH: $Blob"}; $LauncherPath=Join-Path $Stage 'operator-bridge\tools\run-stage12-real-instant.ps1'; & $Engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $LauncherPath -RepositoryRoot $Stage; if($LASTEXITCODE -ne 0){throw "STAGE12_WINDOWS_LAUNCHER_EXIT=$LASTEXITCODE"}; Remove-Item -LiteralPath $Stage -Recurse -Force } finally { $env:PATH=$OldPath; $env:DOTNET_ROOT=$OldDotnetRoot }
```

Authenticate manually to normal ChatGPT, select Instant manually, and stop at the launcher's final cleanup prompt after:

`STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

## Linux/live boundary

After fresh v0.9 authority, execute the exact Linux v3 transaction. The attempt remains unconsumed until Linux prints:

`STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`

Only then service Q1/Q2/Q3 via Ctrl+Space -> Ctrl+V -> Enter at their exact markers.

## Failure policy

v0.8 failed before the live-consumption marker and is therefore unconsumed, but its authority is invalidated because its exact Linux transaction bytes are defective. Do not reuse v0.8 authority for v3. Any v0.9 live execution requires exact-head validation and fresh explicit operator approval. Do not install Node/npm or .NET, persistently edit PATH, mutate registry, widen browser/network/API/DB/GPU/Workspace Shell authority, or silently retry under changed bytes.
