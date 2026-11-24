# D4 orchestrator. The accepted A7 frontend remains byte-pinned and is launched only after the semantic backend reports a ready manual cycle.
[CmdletBinding()]
param(
  [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
  [string]$OperatorBridgeUrl = "https://gokhan-lambda-vector.tailca6171.ts.net/",
  [string]$SshTarget = "atrott@gokhan-lambda-vector.tailca6171.ts.net",
  [string]$SchedulerHotkey = "Ctrl+Space"
)

$ErrorActionPreference = "Stop"
$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$dev = Join-Path $repo "operator-bridge\tools\workspace-operator-dev.ps1"
$linuxRel = "benchmarks/workspace-semantic-execution/private_route_stage12_real_instant_v4.sh"
$remoteBootstrapRel = "operator-bridge/tools/run-stage12-remote-bootstrap.sh"
$remoteBootstrapPath = Join-Path $repo ($remoteBootstrapRel -replace "/", "\")
$engine = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$ssh = (Get-Command ssh.exe -ErrorAction Stop).Source
$tempRoot = Join-Path $env:TEMP ("workspace-control-d4-" + [guid]::NewGuid().ToString("N"))
$frontendReady = Join-Path $tempRoot "frontend-ready.txt"
$frontendLog = Join-Path $tempRoot "frontend.log"
$sshBatch = Join-Path $tempRoot "run-ssh.cmd"
$sshProcess = $null

function Get-D4BackendStatus {
  param(
    [Parameter(Mandatory=$true)]
    [string]$StatusUrl,
    [int]$TimeoutSec = 2
  )

  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $StatusUrl -TimeoutSec $TimeoutSec
  } catch {
    throw ("D4_BACKEND_STATUS_REQUEST_FAILED:" + $_.Exception.GetType().Name)
  }

  if ($response.StatusCode -ne 200) {
    throw ("D4_BACKEND_STATUS_HTTP_" + [int]$response.StatusCode)
  }

  try {
    $payload = $response.Content | ConvertFrom-Json
  } catch {
    throw "D4_BACKEND_STATUS_NOT_JSON"
  }

  if ($null -eq $payload.readyManualCycles -or $null -eq $payload.sentUnconfirmed) {
    throw "D4_BACKEND_STATUS_SHAPE_INVALID"
  }

  try {
    $readyManualCycles = [int]$payload.readyManualCycles
    $sentUnconfirmed = [int]$payload.sentUnconfirmed
  } catch {
    throw "D4_BACKEND_STATUS_VALUES_INVALID"
  }

  if ($readyManualCycles -lt 0 -or $sentUnconfirmed -lt 0) {
    throw "D4_BACKEND_STATUS_VALUES_INVALID"
  }

  [pscustomobject]@{
    ReadyManualCycles = $readyManualCycles
    SentUnconfirmed = $sentUnconfirmed
  }
}

if (-not (Test-Path -LiteralPath $dev -PathType Leaf)) { throw "D4_WOP_DEV_SCRIPT_MISSING:$dev" }
if (-not (Test-Path -LiteralPath $remoteBootstrapPath -PathType Leaf)) { throw "D4_WOP_REMOTE_BOOTSTRAP_MISSING:$remoteBootstrapPath" }

$sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") { throw "D4_WOP_SOURCE_SHA_UNAVAILABLE" }
$frontendTree = (git -C $repo rev-parse ($sourceSha + ":operator-bridge/src")).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $frontendTree -ne "51480cc44f62d661421e975e67af127ecd0b0417") { throw "D4_FRONTEND_TREE_NOT_ACCEPTED_A7:$frontendTree" }
$devBlob = (git -C $repo rev-parse ($sourceSha + ":operator-bridge/tools/workspace-operator-dev.ps1")).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $devBlob -ne "ac035d2fc898274c32cad43954ce44c15b198207") { throw "D4_FRONTEND_DEV_HARNESS_NOT_ACCEPTED_A7:$devBlob" }
$linuxBlob = (git -C $repo rev-parse ("{0}:{1}" -f $sourceSha,$linuxRel)).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $linuxBlob -notmatch "^[0-9a-f]{40}$") { throw "D4_WOP_LINUX_BLOB_UNAVAILABLE" }

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
Write-Host "=== D4 REAL INSTANT - ACCEPTED A7 FRONTEND ==="
Write-Host ("D4_WOP_SOURCE_SHA=" + $sourceSha)
Write-Host "D4_FRONTEND_BASELINE_SHA=a9532ca8b86b7839822939a970e16af1d4a41864"
Write-Host ("D4_FRONTEND_SRC_TREE=" + $frontendTree)
Write-Host ("D4_FRONTEND_DEV_BLOB=" + $devBlob)
Write-Host ("D4_WOP_LINUX_BLOB=" + $linuxBlob)

& $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev stop -RepositoryRoot $repo
if ($LASTEXITCODE -ne 0) { throw "D4_WOP_PRESTOP_FAILED:$LASTEXITCODE" }

try {
  $token = [guid]::NewGuid().ToString("N")
  $remoteText = [System.IO.File]::ReadAllText($remoteBootstrapPath)
  $remoteText = $remoteText.Replace("`r`n","`n").Replace("`r","`n")
  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  $remoteBytes = $utf8NoBom.GetBytes($remoteText)
  if ([Array]::IndexOf($remoteBytes, [byte]13) -ge 0) { throw "D4_REMOTE_BOOTSTRAP_CR_BYTE_REMAINS" }
  $remoteB64 = [Convert]::ToBase64String($remoteBytes)
  $remoteCommand = "echo '$remoteB64' | base64 -d | bash -s -- '$sourceSha' '$linuxRel' '$linuxBlob' '$token'"
  $sshBatchText = @"
@echo off
"$ssh" -tt "$SshTarget" "$remoteCommand"
exit /b %ERRORLEVEL%
"@
  Set-Content -LiteralPath $sshBatch -Value $sshBatchText -Encoding ASCII

  Write-Host "D4_BACKEND_STARTING=PASS"
  Write-Host "The accepted Workspace Operator Bridge frontend will open automatically only after Q1 is actually ready."
  Write-Host "When Firefox opens: authenticate normally if needed, select ChatGPT Instant, then use Ctrl+Space -> Ctrl+V -> Enter."

  $sshProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d","/c",$sshBatch) -NoNewWindow -PassThru

  $statusUrl = $OperatorBridgeUrl.TrimEnd("/") + "/operator-bridge/v1/status"
  $deadline = (Get-Date).AddMinutes(10)
  $ready = $false
  do {
    if ($sshProcess.HasExited) {
      $sshProcess.WaitForExit()
      $sshProcess.Refresh()
      throw "D4_REMOTE_EXIT_BEFORE_BACKEND_READY:$($sshProcess.ExitCode)"
    }
    try {
      $status = Get-D4BackendStatus -StatusUrl $statusUrl -TimeoutSec 2
      if ($status.ReadyManualCycles -ge 1) { $ready = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 250
    $sshProcess.Refresh()
  } while ((Get-Date) -lt $deadline)

  if (-not $ready) {
    Stop-Process -Id $sshProcess.Id -Force -ErrorAction SilentlyContinue
    throw "D4_BACKEND_READY_ACTION_TIMEOUT"
  }

  # Critical A7 invariant: launch the accepted frontend from this interactive
  # PowerShell session, exactly as the validated operator UX was exercised.
  & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev online -RepositoryRoot $repo -SchedulerHotkey $SchedulerHotkey -OperatorBridgeUrl $OperatorBridgeUrl
  if ($LASTEXITCODE -ne 0) {
    Stop-Process -Id $sshProcess.Id -Force -ErrorAction SilentlyContinue
    throw "D4_ACCEPTED_FRONTEND_START_FAILED:$LASTEXITCODE"
  }

  # A7 startup takes several seconds. Re-prove that the remote D4 process and
  # private Operator Bridge route survived that startup window before telling
  # the human that Ctrl+Space can be serviced.
  $sshProcess.Refresh()
  if ($sshProcess.HasExited) {
    $sshProcess.WaitForExit()
    $sshProcess.Refresh()
    throw "D4_BACKEND_EXITED_DURING_FRONTEND_START:$($sshProcess.ExitCode)"
  }

  try {
    $postFrontendStatus = Get-D4BackendStatus -StatusUrl $statusUrl -TimeoutSec 2
  } catch {
    throw ("D4_BACKEND_LOST_AFTER_FRONTEND_START:" + $_.Exception.Message)
  }

  if ($postFrontendStatus.ReadyManualCycles -lt 1) {
    throw "D4_Q1_NOT_CLAIMABLE_AFTER_FRONTEND_START"
  }

  Write-Host "D4_BACKEND_REVALIDATED_AFTER_FRONTEND_START=PASS"
  Write-Host "D4_ACCEPTED_FRONTEND_READY=PASS"
  Write-Host "D4_OPERATOR_LOOP=Ctrl+Space -> Ctrl+V -> Enter"

  $nextBackendHealthCheck = (Get-Date).AddSeconds(2)
  while (-not $sshProcess.HasExited) {
    Start-Sleep -Milliseconds 250
    $sshProcess.Refresh()

    if ((Get-Date) -ge $nextBackendHealthCheck -and -not $sshProcess.HasExited) {
      try {
        $null = Get-D4BackendStatus -StatusUrl $statusUrl -TimeoutSec 2
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
          if ($sshProcess.ExitCode -eq 0) {
            Write-Host "D4_EXPECTED_POSTSUCCESS_ROUTE_TEARDOWN=PASS"
            break
          }
          throw "D4_WOP_REMOTE_EXIT_AFTER_ROUTE_LOSS:$($sshProcess.ExitCode)"
        }

        throw ("D4_OPERATOR_BACKEND_ROUTE_LOST:" + $routeLossMessage)
      }
      $nextBackendHealthCheck = (Get-Date).AddSeconds(2)
    }
  }
  $sshProcess.WaitForExit()
  $sshProcess.Refresh()
  $sshExitCode = $sshProcess.ExitCode
  if ($sshExitCode -ne 0) { throw "D4_WOP_REMOTE_EXIT:$sshExitCode" }
  Write-Host "STAGE12_WOP_REMOTE_CALIBRATION=PASS"
}
finally {
  if ($sshProcess -and -not $sshProcess.HasExited) { Stop-Process -Id $sshProcess.Id -Force -ErrorAction SilentlyContinue }
  & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev stop -RepositoryRoot $repo
  if ($LASTEXITCODE -eq 0) { Write-Host "STAGE12_WOP_WINDOWS_CLEANUP=PASS" } else { Write-Warning ("STAGE12_WOP_WINDOWS_CLEANUP=FAIL:" + $LASTEXITCODE) }
  Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
