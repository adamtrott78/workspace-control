# Stage-12 Real-Instant Retry Procedure v0.4

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Purpose

Repair the second non-consuming Windows pre-live blocker: the exact pinned Stage-12 launcher executed under the v0.3 process-scoped execution-policy repair, but its child PowerShell could not resolve `dotnet` from `PATH`.

This candidate preserves all v0.3 safety boundaries and executable bytes. It does not install .NET and does not persistently modify machine/user PATH or execution policy.

This procedure does **not** authorize a live Stage-12 attempt.

## Exact executable bindings

- Executable source commit: `b0466c03acb9d6b863df421e2c116c84bff312f6`
- Linux v2 transaction blob: `962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca`
- Real-Instant harness blob: `7b1feb8fa13cf0ea46883b07831e829fd9e7e75d`
- Windows launcher blob: `d9d474ca6870585c9e4767f551086e17b4525fbc`
- Candidate baseline: `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`

## v0.4 .NET discovery repair

The operator command resolves an existing `dotnet.exe` only from the current command resolution and standard Program Files / LocalAppData locations, requires SDK major 10, temporarily prepends only that directory to the current process environment, and restores `PATH`/`DOTNET_ROOT` afterward. It installs nothing and makes no persistent PATH, registry, execution-policy, browser, or network change.

## Windows preparation

Run this as **one complete line** in Windows PowerShell:

```powershell
$ErrorActionPreference='Stop'; $RepoUrl='https://github.com/adamtrott78/workspace-control.git'; $SourceSha='b0466c03acb9d6b863df421e2c116c84bff312f6'; $Launcher='operator-bridge/tools/run-stage12-real-instant.ps1'; $LauncherBlob='d9d474ca6870585c9e4767f551086e17b4525fbc'; $Stage=Join-Path $env:TEMP 'workspace-control-stage12-retry-v4'; if(Test-Path -LiteralPath $Stage){throw "STAGE12_STAGE_DIRECTORY_ALREADY_EXISTS: $Stage"}; $Engine=(Get-Process -Id $PID).Path; $EngineName=[IO.Path]::GetFileName($Engine).ToLowerInvariant(); if($EngineName -notin @('powershell.exe','pwsh.exe')){throw "UNEXPECTED_POWERSHELL_ENGINE: $Engine"}; $Policy=@{}; Get-ExecutionPolicy -List | ForEach-Object { $Policy[$_.Scope.ToString()]=$_.ExecutionPolicy.ToString() }; if($Policy['MachinePolicy'] -ne 'Undefined' -or $Policy['UserPolicy'] -ne 'Undefined'){throw "GROUP_POLICY_EXECUTION_POLICY_PRESENT: MachinePolicy=$($Policy['MachinePolicy']) UserPolicy=$($Policy['UserPolicy'])"}; $DotnetCandidates=@(); $DotnetCmd=Get-Command dotnet -ErrorAction SilentlyContinue; if($DotnetCmd){$DotnetCandidates+=$DotnetCmd.Source}; if($env:ProgramFiles){$DotnetCandidates+=(Join-Path $env:ProgramFiles 'dotnet\dotnet.exe')}; if(${env:ProgramFiles(x86)}){$DotnetCandidates+=(Join-Path ${env:ProgramFiles(x86)} 'dotnet\dotnet.exe')}; if($env:LOCALAPPDATA){$DotnetCandidates+=(Join-Path $env:LOCALAPPDATA 'Microsoft\dotnet\dotnet.exe')}; $DotnetPath=$DotnetCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique | Select-Object -First 1; if(-not $DotnetPath){throw 'DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $DotnetVersion=(& $DotnetPath --version).Trim(); if($LASTEXITCODE -ne 0 -or $DotnetVersion -notmatch '^10\.'){throw "DOTNET10_VERSION_MISMATCH: $DotnetVersion"}; $OldPath=$env:PATH; $OldDotnetRoot=$env:DOTNET_ROOT; $DotnetDir=Split-Path -Parent $DotnetPath; $env:PATH="$DotnetDir;$OldPath"; $env:DOTNET_ROOT=$DotnetDir; try { git init -q $Stage; if($LASTEXITCODE -ne 0){throw 'git init failed'}; git -C $Stage remote add origin $RepoUrl; git -C $Stage fetch --no-tags origin workspace-semantic-execution-migration-v1; if($LASTEXITCODE -ne 0){throw 'fetch failed'}; git -C $Stage checkout --detach $SourceSha; if($LASTEXITCODE -ne 0){throw 'checkout failed'}; $Head=(git -C $Stage rev-parse HEAD).Trim().ToLowerInvariant(); if($Head -ne $SourceSha){throw "SOURCE_HEAD_MISMATCH: $Head"}; $Spec="{0}:{1}" -f $SourceSha,$Launcher; $Blob=(git -C $Stage rev-parse $Spec).Trim().ToLowerInvariant(); if($Blob -ne $LauncherBlob){throw "LAUNCHER_BLOB_MISMATCH: $Blob"}; $LauncherPath=Join-Path $Stage 'operator-bridge\tools\run-stage12-real-instant.ps1'; & $Engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $LauncherPath -RepositoryRoot $Stage; if($LASTEXITCODE -ne 0){throw "STAGE12_WINDOWS_LAUNCHER_EXIT=$LASTEXITCODE"}; Remove-Item -LiteralPath $Stage -Recurse -Force } finally { $env:PATH=$OldPath; $env:DOTNET_ROOT=$OldDotnetRoot }
```

The isolated Firefox profile must open. Authenticate manually to normal ChatGPT, select Instant manually, and follow only the launcher's reviewed prompts.

Do not start Linux until the launcher prints:

`STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

## Linux/live boundary

Linux remains the exact v2 transaction. The one live attempt remains unconsumed until Linux prints:

`STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`

Only then service Q1/Q2/Q3 via Ctrl+Space -> Ctrl+V -> Enter at their exact markers.

## Failure policy

Any Windows failure before the live Linux consumption marker is non-consuming. Fail closed. Do not install software, edit persistent PATH, use registry mutation, widen execution policy, widen browser/network permissions, or silently retry under a changed procedure without fresh review/authority.
