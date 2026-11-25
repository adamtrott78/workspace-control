# E3-A10 binding-closure successor orchestrator. Historical launchers remain untouched.
[CmdletBinding()]
param(
  [string]$RepositoryRoot = "",
  [string]$OperatorBridgeUrl = "https://gokhan-lambda-vector.tailca6171.ts.net/",
  [string]$SshTarget = "atrott@gokhan-lambda-vector.tailca6171.ts.net",
  [string]$SchedulerHotkey = "Ctrl+Space"
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
  $RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$bindingManifestRel = "architecture/workspace-semantic-execution-e3-live-binding-manifest.v0.1.json"
$bindingManifestPath = Join-Path $repo ($bindingManifestRel -replace "/", "\")
if (-not (Test-Path -LiteralPath $bindingManifestPath -PathType Leaf)) { throw "E3_A10_BINDING_MANIFEST_MISSING:$bindingManifestPath" }
$bindingManifest = Get-Content -LiteralPath $bindingManifestPath -Raw | ConvertFrom-Json
if ([string]$bindingManifest.artifact_id -ne "workspace-semantic-execution-e3-live-binding-manifest-v1") { throw "E3_A10_BINDING_MANIFEST_ID_MISMATCH" }
$acceptedFrontendHead = [string]$bindingManifest.provenance.a8_frontend_review_head
$acceptedFrontendSourceHead = [string]$bindingManifest.provenance.a8_frontend_source_head
$expectedFrontendTree = [string]$bindingManifest.provenance.a8_frontend_src_tree
$expectedDevBlob = [string]$bindingManifest.provenance.accepted_a7_dev_harness_blob
foreach ($binding in @($acceptedFrontendHead,$acceptedFrontendSourceHead,$expectedFrontendTree,$expectedDevBlob)) {
  if ($binding -notmatch "^[0-9a-f]{40}$") { throw "E3_A10_FRONTEND_MANIFEST_SHA_INVALID:$binding" }
}
$linuxRel = "benchmarks/workspace-semantic-execution/private_route_research_iterate_e3_a10_v1.sh"
$remoteBootstrapRel = "operator-bridge/tools/run-research-iterate-e3-a10-remote-bootstrap.sh"
$remoteBootstrapPath = Join-Path $repo ($remoteBootstrapRel -replace "/", "\")
$engine = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$ssh = (Get-Command ssh.exe -ErrorAction Stop).Source
$tempRoot = Join-Path $env:TEMP ("workspace-control-e3-a10-" + [guid]::NewGuid().ToString("N"))
$frontendRepo = Join-Path $tempRoot "accepted-a8-frontend"
$dev = Join-Path $frontendRepo "operator-bridge\tools\workspace-operator-dev.ps1"
$frontendReady = Join-Path $tempRoot "frontend-ready.txt"
$frontendLog = Join-Path $tempRoot "frontend.log"
$sshBatch = Join-Path $tempRoot "run-ssh.cmd"
$sshExitFile = Join-Path $tempRoot "ssh-exit-code.txt"
$sshProcess = $null

function Get-E3RecordedSshExitCode {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Path,
    [int]$TimeoutMilliseconds = 2000
  )

  $deadline = (Get-Date).AddMilliseconds($TimeoutMilliseconds)
  do {
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
      $raw = (Get-Content -LiteralPath $Path -Raw).Trim()
      $parsed = 0
      if ([int]::TryParse($raw, [ref]$parsed)) {
        return $parsed
      }
      throw "E3_A10_SSH_EXIT_CODE_INVALID:$raw"
    }
    Start-Sleep -Milliseconds 50
  } while ((Get-Date) -lt $deadline)

  throw "E3_A10_SSH_EXIT_CODE_UNAVAILABLE"
}

function Get-E3BackendStatus {
  param(
    [Parameter(Mandatory=$true)]
    [string]$StatusUrl,
    [int]$TimeoutSec = 2
  )

  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $StatusUrl -TimeoutSec $TimeoutSec
  } catch {
    throw ("E3_A10_BACKEND_STATUS_REQUEST_FAILED:" + $_.Exception.GetType().Name)
  }

  if ($response.StatusCode -ne 200) {
    throw ("E3_A10_BACKEND_STATUS_HTTP_" + [int]$response.StatusCode)
  }

  try {
    $payload = $response.Content | ConvertFrom-Json
  } catch {
    throw "E3_A10_BACKEND_STATUS_NOT_JSON"
  }

  if ($null -eq $payload.readyManualCycles -or $null -eq $payload.sentUnconfirmed) {
    throw "E3_A10_BACKEND_STATUS_SHAPE_INVALID"
  }

  try {
    $readyManualCycles = [int]$payload.readyManualCycles
    $sentUnconfirmed = [int]$payload.sentUnconfirmed
  } catch {
    throw "E3_A10_BACKEND_STATUS_VALUES_INVALID"
  }

  if ($readyManualCycles -lt 0 -or $sentUnconfirmed -lt 0) {
    throw "E3_A10_BACKEND_STATUS_VALUES_INVALID"
  }

  [pscustomobject]@{
    ReadyManualCycles = $readyManualCycles
    SentUnconfirmed = $sentUnconfirmed
  }
}

if (-not (Test-Path -LiteralPath $remoteBootstrapPath -PathType Leaf)) { throw "E3_A10_WOP_REMOTE_BOOTSTRAP_MISSING:$remoteBootstrapPath" }

$sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") { throw "E3_A10_WOP_SOURCE_SHA_UNAVAILABLE" }
$linuxBlob = (git -C $repo rev-parse ("{0}:{1}" -f $sourceSha,$linuxRel)).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $linuxBlob -notmatch "^[0-9a-f]{40}$") { throw "E3_A10_WOP_LINUX_BLOB_UNAVAILABLE" }

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
git -C $repo fetch --no-tags origin $acceptedFrontendHead
if ($LASTEXITCODE -ne 0) { throw "E3_A10_FRONTEND_FETCH_FAILED:$LASTEXITCODE" }
git -C $repo worktree add --detach $frontendRepo $acceptedFrontendHead | Out-Null
if ($LASTEXITCODE -ne 0) { throw "E3_A10_FRONTEND_WORKTREE_FAILED:$LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $dev -PathType Leaf)) { throw "E3_A10_WOP_DEV_SCRIPT_MISSING:$dev" }
$frontendTree = (git -C $frontendRepo rev-parse "HEAD:operator-bridge/src").Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $frontendTree -ne $expectedFrontendTree) { throw "E3_A10_FRONTEND_TREE_MISMATCH:$frontendTree" }
$devBlob = (git -C $frontendRepo rev-parse "HEAD:operator-bridge/tools/workspace-operator-dev.ps1").Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $devBlob -ne $expectedDevBlob) { throw "E3_FRONTEND_DEV_HARNESS_NOT_ACCEPTED_A7:$devBlob" }
Write-Host "=== E3-A10 INTEGRATED RESEARCH-ITERATE - VALIDATED A8 FRONTEND ==="
Write-Host ("E3_A10_WOP_SOURCE_SHA=" + $sourceSha)
Write-Host ("E3_A10_FRONTEND_REVIEW_HEAD=" + $acceptedFrontendHead)
Write-Host ("E3_A10_FRONTEND_SOURCE_HEAD=" + $acceptedFrontendSourceHead)
Write-Host ("E3_FRONTEND_SRC_TREE=" + $frontendTree)
Write-Host ("E3_FRONTEND_DEV_BLOB=" + $devBlob)
Write-Host ("E3_A10_WOP_LINUX_BLOB=" + $linuxBlob)

& $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev self-test -RepositoryRoot $frontendRepo
if ($LASTEXITCODE -ne 0) { throw "E3_A10_FRONTEND_SELF_TEST_FAILED:$LASTEXITCODE" }
Write-Host "E3_A10_FRONTEND_DETERMINISTIC_PREFLIGHT=PASS"
& $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev stop -RepositoryRoot $frontendRepo
if ($LASTEXITCODE -ne 0) { throw "E3_A10_WOP_PRESTOP_FAILED:$LASTEXITCODE" }

try {
  $token = [guid]::NewGuid().ToString("N")
  $remoteText = [System.IO.File]::ReadAllText($remoteBootstrapPath)
  $remoteText = $remoteText.Replace("`r`n","`n").Replace("`r","`n")
  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  $remoteBytes = $utf8NoBom.GetBytes($remoteText)
  if ([Array]::IndexOf($remoteBytes, [byte]13) -ge 0) { throw "E3_A10_REMOTE_BOOTSTRAP_CR_BYTE_REMAINS" }
  $remoteB64 = [Convert]::ToBase64String($remoteBytes)
  $remoteCommand = "echo '$remoteB64' | base64 -d | bash -s -- '$sourceSha' '$linuxRel' '$linuxBlob' '$token'"
  $sshBatchText = @"
@echo off
"$ssh" -tt "$SshTarget" "$remoteCommand"
set "WORKSPACE_E3_A10_SSH_RC=%ERRORLEVEL%"
> "$sshExitFile" echo %WORKSPACE_E3_A10_SSH_RC%
exit /b %WORKSPACE_E3_A10_SSH_RC%
"@
  Set-Content -LiteralPath $sshBatch -Value $sshBatchText -Encoding ASCII

  Write-Host "E3_A10_BACKEND_STARTING=PASS"
  Write-Host "The accepted Workspace Operator Bridge frontend will open automatically only after the first E2 Instant action is ready."
  Write-Host "When Firefox opens: authenticate normally if needed, select ChatGPT Instant, then service each E2 action with Ctrl+Space -> Ctrl+V -> Enter."

  $sshProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d","/c",$sshBatch) -NoNewWindow -PassThru

  $statusUrl = $OperatorBridgeUrl.TrimEnd("/") + "/operator-bridge/v1/status"
  $deadline = (Get-Date).AddMinutes(10)
  $ready = $false
  do {
    if ($sshProcess.HasExited) {
      $sshProcess.WaitForExit()
      $sshProcess.Refresh()
      throw "E3_A10_REMOTE_EXIT_BEFORE_BACKEND_READY:$($sshProcess.ExitCode)"
    }
    try {
      $status = Get-E3BackendStatus -StatusUrl $statusUrl -TimeoutSec 2
      if ($status.ReadyManualCycles -ge 1) { $ready = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 250
    $sshProcess.Refresh()
  } while ((Get-Date) -lt $deadline)

  if (-not $ready) {
    Stop-Process -Id $sshProcess.Id -Force -ErrorAction SilentlyContinue
    throw "E3_A10_BACKEND_READY_ACTION_TIMEOUT"
  }

  # Critical A7 invariant: launch the accepted frontend from this interactive
  # PowerShell session, exactly as the validated operator UX was exercised.
  & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev online -RepositoryRoot $frontendRepo -SchedulerHotkey $SchedulerHotkey -OperatorBridgeUrl $OperatorBridgeUrl
  if ($LASTEXITCODE -ne 0) {
    Stop-Process -Id $sshProcess.Id -Force -ErrorAction SilentlyContinue
    throw "E3_A10_ACCEPTED_FRONTEND_START_FAILED:$LASTEXITCODE"
  }

  # A7 startup takes several seconds. Re-prove that the remote E2 process and
  # private Operator Bridge route survived that startup window before telling
  # the human that Ctrl+Space can be serviced.
  $sshProcess.Refresh()
  if ($sshProcess.HasExited) {
    $sshProcess.WaitForExit()
    $sshProcess.Refresh()
    throw "E3_A10_BACKEND_EXITED_DURING_FRONTEND_START:$($sshProcess.ExitCode)"
  }

  try {
    $postFrontendStatus = Get-E3BackendStatus -StatusUrl $statusUrl -TimeoutSec 2
  } catch {
    throw ("E3_A10_BACKEND_LOST_AFTER_FRONTEND_START:" + $_.Exception.Message)
  }

  if ($postFrontendStatus.ReadyManualCycles -lt 1) {
    throw "E3_A10_ROOT_NOT_CLAIMABLE_AFTER_FRONTEND_START"
  }

  Write-Host "E3_A10_BACKEND_REVALIDATED_AFTER_FRONTEND_START=PASS"
  Write-Host "E3_A10_ACCEPTED_FRONTEND_READY=PASS"
  Write-Host "E3_A10_OPERATOR_LOOP=Ctrl+Space -> Ctrl+V -> Enter"

  $nextBackendHealthCheck = (Get-Date).AddSeconds(2)
  while (-not $sshProcess.HasExited) {
    Start-Sleep -Milliseconds 250
    $sshProcess.Refresh()

    if ((Get-Date) -ge $nextBackendHealthCheck -and -not $sshProcess.HasExited) {
      try {
        $null = Get-E3BackendStatus -StatusUrl $statusUrl -TimeoutSec 2
      } catch {
        $routeLossMessage = $_.Exception.Message
        $teardownDeadline = (Get-Date).AddSeconds(10)
        do {
          Start-Sleep -Milliseconds 100
          $sshProcess.Refresh()
        } while (-not $sshProcess.HasExited -and (Get-Date) -lt $teardownDeadline)

        if ($sshProcess.HasExited) {
          $sshProcess.WaitForExit()
          $sshProcess.Refresh()
          $recordedExitCode = Get-E3RecordedSshExitCode -Path $sshExitFile
          if ($recordedExitCode -eq 0) {
            Write-Host "E3_A10_EXPECTED_POSTSUCCESS_ROUTE_TEARDOWN=PASS"
            break
          }
          throw "E3_A10_WOP_REMOTE_EXIT_AFTER_ROUTE_LOSS:$recordedExitCode"
        }

        throw ("E3_A10_OPERATOR_BACKEND_ROUTE_LOST:" + $routeLossMessage)
      }
      $nextBackendHealthCheck = (Get-Date).AddSeconds(2)
    }
  }
  $sshProcess.WaitForExit()
  $sshProcess.Refresh()
  $sshExitCode = Get-E3RecordedSshExitCode -Path $sshExitFile
  if ($sshExitCode -ne 0) { throw "E3_A10_WOP_REMOTE_EXIT:$sshExitCode" }
  Write-Host "E3_A10_WOP_REMOTE_WORKFLOW=PASS"
}
finally {
  if ($sshProcess -and -not $sshProcess.HasExited) { Stop-Process -Id $sshProcess.Id -Force -ErrorAction SilentlyContinue }
  & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev stop -RepositoryRoot $frontendRepo
  if ($LASTEXITCODE -eq 0) { Write-Host "E3_A10_WOP_WINDOWS_CLEANUP=PASS" } else { Write-Warning ("E3_A10_WOP_WINDOWS_CLEANUP=FAIL:" + $LASTEXITCODE) }
  git -C $repo worktree remove --force $frontendRepo 2>$null | Out-Null
  Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
