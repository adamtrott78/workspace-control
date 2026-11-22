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
      $response = Invoke-WebRequest -UseBasicParsing -Uri $statusUrl -TimeoutSec 2
      if ($response.StatusCode -eq 200) {
        $payload = $response.Content | ConvertFrom-Json
        if ([int]$payload.readyManualCycles -ge 1) { $ready = $true; break }
      }
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
  Write-Host "D4_ACCEPTED_FRONTEND_READY=PASS"
  Write-Host "D4_OPERATOR_LOOP=Ctrl+Space -> Ctrl+V -> Enter"

  while (-not $sshProcess.HasExited) {
    Start-Sleep -Milliseconds 250
    $sshProcess.Refresh()
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
