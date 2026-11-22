# One-line D4 launcher: reuse the validated persistent WOP runtime and run the Linux calibration over the user's existing Tailscale SSH path.
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
$linuxPath = Join-Path $repo ($linuxRel -replace "/", "\")
$remoteBootstrapRel = "operator-bridge/tools/run-stage12-remote-bootstrap.sh"
$remoteBootstrapPath = Join-Path $repo ($remoteBootstrapRel -replace "/", "\")
$engine = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$ssh = Get-Command ssh.exe -ErrorAction Stop
$statePath = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\DevRuntime\runtime.json"

if (-not (Test-Path -LiteralPath $dev -PathType Leaf)) { throw "D4_WOP_DEV_SCRIPT_MISSING:$dev" }
if (-not (Test-Path -LiteralPath $linuxPath -PathType Leaf)) { throw "D4_WOP_LINUX_SCRIPT_MISSING:$linuxPath" }
if (-not (Test-Path -LiteralPath $remoteBootstrapPath -PathType Leaf)) { throw "D4_WOP_REMOTE_BOOTSTRAP_MISSING:$remoteBootstrapPath" }

$sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") { throw "D4_WOP_SOURCE_SHA_UNAVAILABLE" }

$linuxBlob = (git -C $repo rev-parse ("{0}:{1}" -f $sourceSha,$linuxRel)).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $linuxBlob -notmatch "^[0-9a-f]{40}$") { throw "D4_WOP_LINUX_BLOB_UNAVAILABLE" }

$remoteBootstrapBlob = (git -C $repo rev-parse ("{0}:{1}" -f $sourceSha,$remoteBootstrapRel)).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $remoteBootstrapBlob -notmatch "^[0-9a-f]{40}$") { throw "D4_WOP_REMOTE_BOOTSTRAP_BLOB_UNAVAILABLE" }

Write-Host "=== D4 REAL INSTANT - WOP ONE-LINE LAUNCH ==="
Write-Host ("D4_WOP_SOURCE_SHA=" + $sourceSha)
Write-Host ("D4_WOP_LINUX_BLOB=" + $linuxBlob)
Write-Host ("D4_WOP_REMOTE_BOOTSTRAP_BLOB=" + $remoteBootstrapBlob)

& $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev stop -RepositoryRoot $repo
if ($LASTEXITCODE -ne 0) { throw "D4_WOP_PRESTOP_FAILED:$LASTEXITCODE" }

try {
  & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev online -RepositoryRoot $repo -SchedulerHotkey $SchedulerHotkey -OperatorBridgeUrl $OperatorBridgeUrl
  if ($LASTEXITCODE -ne 0) { throw "D4_WOP_WINDOWS_START_FAILED:$LASTEXITCODE" }

  if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { throw "D4_WOP_RUNTIME_STATE_MISSING" }
  $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
  if ([string]$state.mode -ne "online") { throw "D4_WOP_RUNTIME_NOT_ONLINE" }
  if (-not (Get-Process -Id ([int]$state.helper_pid) -ErrorAction SilentlyContinue)) { throw "D4_WOP_HELPER_NOT_ALIVE" }
  if (-not (Get-Process -Id ([int]$state.web_ext_pid) -ErrorAction SilentlyContinue)) { throw "D4_WOP_WEB_EXT_NOT_ALIVE" }

  Write-Host "STAGE12_WOP_WINDOWS_RUNTIME_READY=PASS"
  Write-Host "The persistent WorkspaceWorkers Firefox profile is open."
  Write-Host "If authentication is needed, use that profile normally and ensure ChatGPT Instant is selected."
  [void](Read-Host "When that profile is ready for the live worker loop, press Enter here")
  Write-Host "STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"

  $token = [guid]::NewGuid().ToString("N")
  $remoteBytes = [System.IO.File]::ReadAllBytes($remoteBootstrapPath)
  $remoteB64 = [Convert]::ToBase64String($remoteBytes)
  $remoteCommand = "printf '%s' '$remoteB64' | base64 -d | bash -s -- '$sourceSha' '$linuxRel' '$linuxBlob' '$token'"

  Write-Host ("STAGE12_WOP_REMOTE_START=" + $SshTarget)
  & $ssh.Source -tt $SshTarget $remoteCommand
  $sshExit = $LASTEXITCODE
  if ($sshExit -ne 0) { throw "D4_WOP_REMOTE_EXIT:$sshExit" }

  Write-Host "STAGE12_WOP_REMOTE_CALIBRATION=PASS"
}
finally {
  & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $dev stop -RepositoryRoot $repo
  if ($LASTEXITCODE -eq 0) {
    Write-Host "STAGE12_WOP_WINDOWS_CLEANUP=PASS"
  } else {
    Write-Warning ("STAGE12_WOP_WINDOWS_CLEANUP=FAIL:" + $LASTEXITCODE)
  }
}
