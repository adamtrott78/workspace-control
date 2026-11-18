# Stage-12 Real-Instant Retry Procedure v0.8

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Purpose

Repair the pre-execution v0.7 PowerShell escape defect discovered by exact-byte audit after v0.7 authority validation but before any Windows or Linux execution.

The v0.7 fenced one-line command contains a literal backslash before each `${env:ProgramFiles(x86)}` reference. PowerShell accepts the text syntactically, so parser-only validation did not detect the semantic defect. v0.8 removes exactly those two stray backslashes from the executable command and changes no other command byte.

All pinned launcher/Linux/harness executable bytes, browser/network/result boundaries, Node/.NET discovery policy, manual-auth boundary, and authority-consumption semantics remain unchanged. This procedure does **not** authorize a live Stage-12 attempt.

## Exact executable bindings

- Executable source commit: `b0466c03acb9d6b863df421e2c116c84bff312f6`
- Linux v2 transaction blob: `962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca`
- Real-Instant harness blob: `7b1feb8fa13cf0ea46883b07831e829fd9e7e75d`
- Windows launcher blob: `d9d474ca6870585c9e4767f551086e17b4525fbc`
- Candidate baseline: `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`
- Reviewed Node-binding source workflow blob: `1ea4135e0ff80454b5a8e5feac139d0177d3b764`

## v0.8 escape repair

The executable command is byte-for-byte identical to v0.7 except that the two literal `\` characters immediately preceding `${env:ProgramFiles(x86)}` are removed. The repaired references are `${env:ProgramFiles(x86)}`.

## Windows preparation

Run this as **one complete line** in Windows PowerShell:

```powershell
$ErrorActionPreference='Stop'; $RepoUrl='https://github.com/adamtrott78/workspace-control.git'; $SourceSha='b0466c03acb9d6b863df421e2c116c84bff312f6'; $Launcher='operator-bridge/tools/run-stage12-real-instant.ps1'; $LauncherBlob='d9d474ca6870585c9e4767f551086e17b4525fbc'; $Stage=Join-Path $env:TEMP 'workspace-control-stage12-retry-v7'; if(Test-Path -LiteralPath $Stage){throw "STAGE12_STAGE_DIRECTORY_ALREADY_EXISTS: $Stage"}; $Engine=(Get-Process -Id $PID).Path; $EngineName=[IO.Path]::GetFileName($Engine).ToLowerInvariant(); if($EngineName -notin @('powershell.exe','pwsh.exe')){throw "UNEXPECTED_POWERSHELL_ENGINE: $Engine"}; $Policy=@{}; Get-ExecutionPolicy -List | ForEach-Object { $Policy[$_.Scope.ToString()]=$_.ExecutionPolicy.ToString() }; if($Policy['MachinePolicy'] -ne 'Undefined' -or $Policy['UserPolicy'] -ne 'Undefined'){throw "GROUP_POLICY_EXECUTION_POLICY_PRESENT: MachinePolicy=$($Policy['MachinePolicy']) UserPolicy=$($Policy['UserPolicy'])"}; $DotnetCandidates=@(); $DotnetCmd=Get-Command dotnet -ErrorAction SilentlyContinue; if($DotnetCmd){$DotnetCandidates+=$DotnetCmd.Source}; if($env:ProgramFiles){$DotnetCandidates+=(Join-Path $env:ProgramFiles 'dotnet\dotnet.exe')}; if(${env:ProgramFiles(x86)}){$DotnetCandidates+=(Join-Path ${env:ProgramFiles(x86)} 'dotnet\dotnet.exe')}; if($env:LOCALAPPDATA){$DotnetCandidates+=(Join-Path $env:LOCALAPPDATA 'Microsoft\dotnet\dotnet.exe')}; if($env:USERPROFILE){$DotnetCandidates+=(Join-Path $env:USERPROFILE '.dotnet\dotnet.exe')}; $DotnetPath=$DotnetCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique | Select-Object -First 1; if(-not $DotnetPath){throw 'DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $DotnetVersion=(& $DotnetPath --version).Trim(); if($LASTEXITCODE -ne 0 -or $DotnetVersion -notmatch '^10\.'){throw "DOTNET10_VERSION_MISMATCH: $DotnetVersion"}; $DotnetDir=Split-Path -Parent $DotnetPath; $OldPath=$env:PATH; $OldDotnetRoot=$env:DOTNET_ROOT; $NodeDir=$null; $NodeCommand=Get-Command node.exe -ErrorAction SilentlyContinue; if($NodeCommand){$CurrentNodeDir=Split-Path -Parent $NodeCommand.Source; $CurrentNodeExe=Join-Path $CurrentNodeDir 'node.exe'; $CurrentNpmCmd=Join-Path $CurrentNodeDir 'npm.cmd'; if((Test-Path -LiteralPath $CurrentNodeExe) -and (Test-Path -LiteralPath $CurrentNpmCmd)){$CurrentNodeVersion=(& $CurrentNodeExe --version).Trim(); if($LASTEXITCODE -eq 0 -and $CurrentNodeVersion -match '^v24\.'){$CurrentNpmVersion=(& $CurrentNpmCmd --version).Trim(); if($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($CurrentNpmVersion)){$NodeDir=$CurrentNodeDir}}}}; if(-not $NodeDir){$ToolCache=if($env:RUNNER_TOOL_CACHE){$env:RUNNER_TOOL_CACHE}else{Join-Path $env:USERPROFILE 'actions-runner\_work\_tool'}; $NodeRoot=Join-Path $ToolCache 'node'; $NodeCandidates=@(Get-ChildItem $NodeRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^24\.\d+\.\d+$' } | Sort-Object { [version]$_.Name } -Descending); foreach($Candidate in $NodeCandidates){$CandidateDir=Join-Path $Candidate.FullName 'x64'; if((Test-Path -LiteralPath (Join-Path $CandidateDir 'node.exe')) -and (Test-Path -LiteralPath (Join-Path $CandidateDir 'npm.cmd'))){$NodeDir=$CandidateDir; break}}}; if(-not $NodeDir){throw 'NODE24_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $NodeExe=Join-Path $NodeDir 'node.exe'; $NpmCmd=Join-Path $NodeDir 'npm.cmd'; $NodeVersion=(& $NodeExe --version).Trim(); if($LASTEXITCODE -ne 0 -or $NodeVersion -notmatch '^v24\.'){throw "NODE24_VERSION_MISMATCH: $NodeVersion"}; $NpmVersion=(& $NpmCmd --version).Trim(); if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($NpmVersion)){throw 'NPM_NOT_AVAILABLE_IN_REVIEWED_NODE24'}; $env:PATH="$DotnetDir;$NodeDir;$OldPath"; $env:DOTNET_ROOT=$DotnetDir; try { git init -q $Stage; if($LASTEXITCODE -ne 0){throw 'git init failed'}; git -C $Stage remote add origin $RepoUrl; git -C $Stage fetch --no-tags origin workspace-semantic-execution-migration-v1; if($LASTEXITCODE -ne 0){throw 'fetch failed'}; git -C $Stage checkout --detach $SourceSha; if($LASTEXITCODE -ne 0){throw 'checkout failed'}; $Head=(git -C $Stage rev-parse HEAD).Trim().ToLowerInvariant(); if($Head -ne $SourceSha){throw "SOURCE_HEAD_MISMATCH: $Head"}; $Spec="{0}:{1}" -f $SourceSha,$Launcher; $Blob=(git -C $Stage rev-parse $Spec).Trim().ToLowerInvariant(); if($Blob -ne $LauncherBlob){throw "LAUNCHER_BLOB_MISMATCH: $Blob"}; $LauncherPath=Join-Path $Stage 'operator-bridge\tools\run-stage12-real-instant.ps1'; & $Engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $LauncherPath -RepositoryRoot $Stage; if($LASTEXITCODE -ne 0){throw "STAGE12_WINDOWS_LAUNCHER_EXIT=$LASTEXITCODE"}; Remove-Item -LiteralPath $Stage -Recurse -Force } finally { $env:PATH=$OldPath; $env:DOTNET_ROOT=$OldDotnetRoot }
```

The isolated Firefox profile must open. Authenticate manually to normal ChatGPT, select Instant manually, and follow only the launcher's reviewed prompts.

Do not start Linux until the launcher prints:

`STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`

## Linux/live boundary

Linux remains the exact v2 transaction. The one live attempt remains unconsumed until Linux prints:

`STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`

Only then service Q1/Q2/Q3 via Ctrl+Space -> Ctrl+V -> Enter at their exact markers.

## Failure policy

Any Windows failure before the live Linux consumption marker is non-consuming. Fail closed. Do not install Node/npm, install .NET, edit persistent PATH, mutate the registry, widen execution policy/browser/network permissions, or silently retry under a changed procedure without fresh review/authority.
