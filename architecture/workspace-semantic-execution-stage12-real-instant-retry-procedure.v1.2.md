# Stage-12 Real-Instant Retry Procedure v1.2

Status: REVIEW CANDIDATE — NOT AUTHORITY

## Purpose

Run one fresh bounded D4 calibration against the **final accepted Windows Operator front end** after repairing the pre-consumption v1.1 Windows preparation regression. The v1.1 authority aborted unconsumed before launcher startup because its frozen command required PATH-only .NET discovery; review also found that its shallow moving-branch fetch could no longer equal the older frozen source SHA after the branch advanced.

D4 is intentionally smaller than the later Research Engine proving run. It answers one question: can a real ChatGPT Instant conversation act as a production semantic worker through the final Windows Operator, private Tailscale route, immutable GitHub candidate path, independent ingestion/validation, persistent-session reuse, stale-generation fencing, and replacement-session recovery?

This procedure grants **zero live authority**. The v1.1 one-shot authority is non-reusable but unconsumed. A future live attempt requires a separate fresh one-shot authority artifact created only after this v1.2 review candidate is exact-head validated and Adam explicitly approves that exact validated repair.

## Exact executable bindings

- Windows/source head: `2f32513f97834da76287d2f948891b758d5194f5`
- Source validation: Workspace #3085 / Semantic #385 / Operator #658 = SUCCESS
- Windows launcher: `operator-bridge/tools/run-stage12-real-instant.ps1`
- Windows launcher blob: `a4619bcc8f4177878ddf0f40bec402e1b211aeb6`
- Windows tray/hotkey source blob: `b86e04065b354b8aa54ee2a9ca3e71ab555cde7c`
- Human Enter confirmation gate blob: `8a4f8ac4ad5cbce10d71e4b59f24aaabaee382e3`
- Firefox adapter blob: `ba67137e92844a9205a36241d6299ce1cfad80a7`
- Linux private-route transaction: `benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v3.sh`
- Linux transaction blob: `3eb352f456d84de565514e2a7046e847ea0d25ea`
- Real-Instant harness: `benchmarks/workspace-semantic-execution/live_real_instant_calibration_v1.py`
- Harness blob: `7b1feb8fa13cf0ea46883b07831e829fd9e7e75d`
- Frozen semantic execution SHA: `7c20097c5f177f23c16a765b95ce94d7161f0d29`
- Candidate repository/branch: `adamtrott78/workspace-control` / `worker-result-candidates-v1`
- Required candidate baseline before live consumption: `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`
- Candidate namespace: `worker-results/stage12/<run-token>/`

## Accepted Windows prerequisite

The local Windows fast loop and required convenience shims are already accepted. Do **not** repeat frontend repair work during D4.

Accepted behavior:

1. Dedicated persistent non-default Firefox profile.
2. Sessionstore-only cleanup preserves authentication while preventing stale tab resurrection.
3. Runtime opens on one clean blank tab.
4. First `Ctrl+Space` creates/focuses a fresh Personalized Temporary Chat and closes only that startup blank.
5. Clipboard staging is automatic; paste and Enter remain human actions.
6. A repeat `Ctrl+Space` before human Enter is blocked/refocused and cannot advance/minimize.
7. Plain Enter while the captured worker Firefox window is foreground unlocks the next scheduler press.
8. Raw literal `@github` invocation works without UI autocomplete selection.
9. No-work scheduler press minimizes only the dedicated Firefox window.
10. Persistent commands `wop-up/down/reset/status/self-test` are installed; D4 itself uses the pinned Stage-12 launcher, not the dev smoke lifecycle.

A7 closeout head `a9532ca8b86b7839822939a970e16af1d4a41864` passed Workspace #3084 / Semantic #384 / Operator #657. The D4 auth-instruction alignment head `2f32513f97834da76287d2f948891b758d5194f5` passed #3085 / #385 / #658.

## Retained safety and authority boundaries

- Manual ChatGPT login only.
- Manual Instant selection only.
- Manual worker service only: `Ctrl+Space -> Ctrl+V -> Enter`.
- Do not press the next `Ctrl+Space` until Linux prints the next `STAGE12_*_READY` marker.
- No automatic typing, paste, Enter, Send, or mouse input.
- No DOM/page-content/output scraping.
- No credential automation.
- No API-key or paid-API fallback.
- Firefox permissions remain exactly `nativeMessaging,tabs,sessions`; no content scripts or host permissions.
- No Tailscale Funnel or public listener.
- Backend remains loopback and privately exposed only through the reviewed tailnet route.
- No production PostgreSQL mutation.
- No GPU or PADataset mutation.
- No Workspace Shell network/helper/generic-shell authority widening.
- Worker results are never copied back manually. The worker must publish exactly one immutable candidate to the isolated candidate branch/path.
- Source/authority branches are never result targets.
- Stale-generation candidates must remain rejected.
- The one live attempt is not consumed until Linux prints `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`.
- After that marker, success or failure consumes the one attempt. Any retry requires a fresh diagnosis/review/validation/approval cycle.

## Windows-first pre-live preparation

Before Linux consumes live authority:

1. `wop-status` must be OFFLINE.
2. Close all Firefox windows. The Stage-12 launcher intentionally refuses pre-existing Firefox.
3. Run the exact Windows preparation command below **only after a future v1.2 authority explicitly authorizes it**.
4. The launcher starts the isolated Stage-12 profile on one blank tab.
5. If authentication/model verification is needed, manually navigate that same tab to `https://chatgpt.com/?temporary-chat=true`, sign in normally, select Instant, then navigate the **same tab** back to `about:blank`.
6. Require exactly one blank tab before confirming the launcher prompt.
7. Require `STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`.
8. Leave the Windows launcher running at its final cleanup prompt while Linux executes.

Exact Windows command:

```powershell
$ErrorActionPreference='Stop'; $RepoUrl='https://github.com/adamtrott78/workspace-control.git'; $SourceSha='2f32513f97834da76287d2f948891b758d5194f5'; $Launcher='operator-bridge/tools/run-stage12-real-instant.ps1'; $LauncherBlob='a4619bcc8f4177878ddf0f40bec402e1b211aeb6'; $Stage=Join-Path $env:TEMP 'workspace-control-stage12-d4-v12'; if(Test-Path -LiteralPath $Stage){throw "STAGE12_STAGE_DIRECTORY_ALREADY_EXISTS:$Stage"}; $Engine=(Get-Process -Id $PID).Path; $EngineName=[IO.Path]::GetFileName($Engine).ToLowerInvariant(); if($EngineName -notin @('powershell.exe','pwsh.exe')){throw "UNEXPECTED_POWERSHELL_ENGINE:$Engine"}; $Policy=@{}; Get-ExecutionPolicy -List | ForEach-Object { $Policy[$_.Scope.ToString()]=$_.ExecutionPolicy.ToString() }; if($Policy['MachinePolicy'] -ne 'Undefined' -or $Policy['UserPolicy'] -ne 'Undefined'){throw "GROUP_POLICY_EXECUTION_POLICY_PRESENT:MachinePolicy=$($Policy['MachinePolicy']):UserPolicy=$($Policy['UserPolicy'])"}; $DotnetCandidates=@(); $DotnetCmd=Get-Command dotnet -ErrorAction SilentlyContinue; if($DotnetCmd){$DotnetCandidates+=$DotnetCmd.Source}; if($env:ProgramFiles){$DotnetCandidates+=(Join-Path $env:ProgramFiles 'dotnet\dotnet.exe')}; if(${env:ProgramFiles(x86)}){$DotnetCandidates+=(Join-Path ${env:ProgramFiles(x86)} 'dotnet\dotnet.exe')}; if($env:LOCALAPPDATA){$DotnetCandidates+=(Join-Path $env:LOCALAPPDATA 'Microsoft\dotnet\dotnet.exe')}; if($env:USERPROFILE){$DotnetCandidates+=(Join-Path $env:USERPROFILE '.dotnet\dotnet.exe')}; $DotnetPath=$null; foreach($Candidate in ($DotnetCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique)){ $CandidateVersion=(& $Candidate --version).Trim(); if($LASTEXITCODE -eq 0 -and $CandidateVersion -match '^10\.'){ $DotnetPath=$Candidate; break } }; if(-not $DotnetPath){throw 'DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $DotnetVersion=(& $DotnetPath --version).Trim(); if($LASTEXITCODE -ne 0 -or $DotnetVersion -notmatch '^10\.'){throw "DOTNET10_VERSION_MISMATCH:$DotnetVersion"}; $DotnetDir=Split-Path -Parent $DotnetPath; $NodeDir=$null; $NodeCommand=Get-Command node.exe -ErrorAction SilentlyContinue; if($NodeCommand){$CurrentNodeDir=Split-Path -Parent $NodeCommand.Source; $CurrentNodeExe=Join-Path $CurrentNodeDir 'node.exe'; $CurrentNpmCmd=Join-Path $CurrentNodeDir 'npm.cmd'; if((Test-Path -LiteralPath $CurrentNodeExe -PathType Leaf) -and (Test-Path -LiteralPath $CurrentNpmCmd -PathType Leaf)){ $CurrentNodeVersion=(& $CurrentNodeExe --version).Trim(); if($LASTEXITCODE -eq 0 -and $CurrentNodeVersion -match '^v24\.'){ $CurrentNpmVersion=(& $CurrentNpmCmd --version).Trim(); if($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($CurrentNpmVersion)){ $NodeDir=$CurrentNodeDir } } } }; if(-not $NodeDir){$ToolCache=if($env:RUNNER_TOOL_CACHE){$env:RUNNER_TOOL_CACHE}else{Join-Path $env:USERPROFILE 'actions-runner\_work\_tool'}; $NodeRoot=Join-Path $ToolCache 'node'; $NodeCandidates=@(Get-ChildItem $NodeRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^24\.\d+\.\d+$' } | Sort-Object { [version]$_.Name } -Descending); foreach($Candidate in $NodeCandidates){$CandidateDir=Join-Path $Candidate.FullName 'x64'; $CandidateNode=Join-Path $CandidateDir 'node.exe'; $CandidateNpm=Join-Path $CandidateDir 'npm.cmd'; if((Test-Path -LiteralPath $CandidateNode -PathType Leaf) -and (Test-Path -LiteralPath $CandidateNpm -PathType Leaf)){ $CandidateNodeVersion=(& $CandidateNode --version).Trim(); if($LASTEXITCODE -eq 0 -and $CandidateNodeVersion -match '^v24\.'){ $CandidateNpmVersion=(& $CandidateNpm --version).Trim(); if($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($CandidateNpmVersion)){ $NodeDir=$CandidateDir; break } } } } }; if(-not $NodeDir){throw 'NODE24_NOT_FOUND_IN_REVIEWED_LOCATIONS'}; $NodeExe=Join-Path $NodeDir 'node.exe'; $NpmCmd=Join-Path $NodeDir 'npm.cmd'; $NodeVersion=(& $NodeExe --version).Trim(); if($LASTEXITCODE -ne 0 -or $NodeVersion -notmatch '^v24\.'){throw "NODE24_VERSION_MISMATCH:$NodeVersion"}; $NpmVersion=(& $NpmCmd --version).Trim(); if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($NpmVersion)){throw 'NPM_NOT_AVAILABLE_IN_REVIEWED_NODE24'}; $OldPath=$env:PATH; $OldDotnetRoot=$env:DOTNET_ROOT; $env:PATH="$DotnetDir;$NodeDir;$OldPath"; $env:DOTNET_ROOT=$DotnetDir; try { git init -q $Stage; if($LASTEXITCODE -ne 0){throw 'GIT_INIT_FAILED'}; git -C $Stage remote add origin $RepoUrl; if($LASTEXITCODE -ne 0){throw 'GIT_REMOTE_ADD_FAILED'}; git -C $Stage fetch --no-tags origin workspace-semantic-execution-migration-v1; if($LASTEXITCODE -ne 0){throw 'GIT_BRANCH_FETCH_FAILED'}; git -C $Stage cat-file -e ($SourceSha + '^{commit}'); if($LASTEXITCODE -ne 0){throw 'SOURCE_COMMIT_UNAVAILABLE'}; git -C $Stage checkout --detach $SourceSha; if($LASTEXITCODE -ne 0){throw 'GIT_CHECKOUT_FAILED'}; $Head=(git -C $Stage rev-parse HEAD).Trim().ToLowerInvariant(); if($Head -ne $SourceSha){throw "SOURCE_HEAD_MISMATCH:$Head"}; git -C $Stage cat-file -e ($SourceSha + '^{tree}'); if($LASTEXITCODE -ne 0){throw 'SOURCE_TREE_UNAVAILABLE'}; $Spec="{0}:{1}" -f $SourceSha,$Launcher; $Blob=(git -C $Stage rev-parse $Spec).Trim().ToLowerInvariant(); if($Blob -ne $LauncherBlob){throw "LAUNCHER_BLOB_MISMATCH:$Blob"}; $LauncherPath=Join-Path $Stage 'operator-bridge\tools\run-stage12-real-instant.ps1'; & $Engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $LauncherPath -RepositoryRoot $Stage; if($LASTEXITCODE -ne 0){throw "STAGE12_WINDOWS_LAUNCHER_EXIT:$LASTEXITCODE"} } finally { $env:PATH=$OldPath; $env:DOTNET_ROOT=$OldDotnetRoot; if(Test-Path -LiteralPath $Stage){Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue} }
```

No PowerShell profile sourcing, package installation, persistent PATH edit, or persistent execution-policy change is permitted. The command reuses the same bounded .NET 10 and Node 24 discovery locations already accepted by `workspace-operator-dev.ps1`, scopes PATH/DOTNET_ROOT changes to the current process, restores them in `finally`, and checks out the frozen source SHA after fetching branch history instead of requiring the moving branch tip to equal the frozen source.

## Linux transaction and authority consumption

The exact Linux v3 transaction remains byte-identical at blob `3eb352f456d84de565514e2a7046e847ea0d25ea`.

It must, in order:

1. verify the candidate branch still equals `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`;
2. verify the exact source/harness and preexisting Tailscale Serve/Funnel state;
3. require the exact Windows-ready marker;
4. print `STAGE12_WINDOWS_READY_GATE=PASS`;
5. only then print `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`;
6. create the bounded private `/operator-bridge/v1` route to the loopback backend;
7. execute the Real-Instant harness;
8. restore the preexisting Serve/Funnel state through its cleanup trap whether the calibration passes or fails.

If any pre-consumption invariant fails, stop without consuming the live attempt.

## Human D4 service sequence

Only act when the Linux terminal prints the corresponding READY marker.

### Q1 — real Instant candidate

At `STAGE12_Q1_READY`:

1. Press `Ctrl+Space` once.
2. Confirm the fresh Temporary Chat worker is foreground.
3. Press `Ctrl+V`.
4. Press plain `Enter`.
5. Do nothing else until Linux accepts the candidate and prints the next READY marker.

Expected backend evidence includes `STAGE12_Q1_REAL_INSTANT=PASS`.

### Q2 — persistent conversation reuse

At `STAGE12_Q2_REUSE_READY`:

1. Press `Ctrl+Space` once. This consumes the prior human-Enter confirmation and dispatches the next action.
2. The same managed conversation/session must be reused.
3. Press `Ctrl+V`, then plain `Enter`.
4. Wait for Linux.

Expected evidence includes `STAGE12_PERSISTENT_SESSION_REUSE=PASS`.

### Stale-generation fence and Q3 replacement

The harness fences the old generation and proves a late old-generation candidate cannot be accepted. No human result relay is permitted.

At `STAGE12_Q3_REPLACEMENT_READY`:

1. Press `Ctrl+Space` once.
2. A replacement managed worker/session must be prepared.
3. Press `Ctrl+V`, then plain `Enter`.
4. Wait for Linux.

Expected evidence includes `STAGE12_STALE_SESSION_FENCE=PASS` and final `STAGE12_REAL_INSTANT_CALIBRATION=PASS`.

## Cleanup and success

After Linux reports PASS or a bounded failure:

1. Let the Linux transaction cleanup trap finish.
2. Require exact restoration of the preexisting tailnet-only Serve/Funnel configuration and removal of the Stage-12 route.
3. Return to the still-running Windows launcher and press Enter at its cleanup prompt.
4. Require `STAGE12_WINDOWS_CLEANUP=PASS`.
5. Do not treat any candidate/result as accepted unless the harness independently ingested and validated its exact immutable revision.

D4 passes only if Q1 real Instant, Q2 session reuse, stale-generation rejection, Q3 replacement, final operator-work-empty state, and cleanup invariants all pass.

## Authority gate

This v1.2 procedure is a review artifact only.

- Live attempts authorized now: **0**
- Existing v1.1 authority reusable: **NO — aborted pre-consumption on the defective Windows preparation command**
- Fresh explicit operator approval required after exact-head review validation: **YES**
- Model reasoning can create live execution authority: **NO**
