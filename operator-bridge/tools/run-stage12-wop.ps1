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
$engine = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$ssh = Get-Command ssh.exe -ErrorAction Stop
$statePath = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\DevRuntime\runtime.json"

if (-not (Test-Path -LiteralPath $dev -PathType Leaf)) { throw "D4_WOP_DEV_SCRIPT_MISSING:$dev" }
if (-not (Test-Path -LiteralPath $linuxPath -PathType Leaf)) { throw "D4_WOP_LINUX_SCRIPT_MISSING:$linuxPath" }

$sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") { throw "D4_WOP_SOURCE_SHA_UNAVAILABLE" }
$linuxBlob = (git -C $repo rev-parse ("{0}:{1}" -f $sourceSha,$linuxRel)).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $linuxBlob -notmatch "^[0-9a-f]{40}$") { throw "D4_WOP_LINUX_BLOB_UNAVAILABLE" }

Write-Host "=== D4 REAL INSTANT — WOP ONE-LINE LAUNCH ==="
Write-Host ("D4_WOP_SOURCE_SHA=" + $sourceSha)
Write-Host ("D4_WOP_LINUX_BLOB=" + $linuxBlob)

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
  $remoteTemplate = @'
set -Eeuo pipefail
REPO_URL='https://github.com/adamtrott78/workspace-control.git'
SOURCE_SHA='__SOURCE_SHA__'
LINUX_REL='__LINUX_REL__'
LINUX_BLOB='__LINUX_BLOB__'
D='/tmp/workspace-stage12-wop-__TOKEN__'
cleanup_outer() { rm -rf -- "$D" >/dev/null 2>&1 || true; }
trap cleanup_outer EXIT
[[ ! -e "$D" ]] || { echo "D4_WOP_REMOTE_STAGE_EXISTS=$D" >&2; exit 70; }
git init -q "$D"
git -C "$D" remote add origin "$REPO_URL"
git -C "$D" fetch --no-tags origin workspace-semantic-execution-migration-v1
if ! git -C "$D" cat-file -e "$SOURCE_SHA^{commit}" 2>/dev/null; then
  git -C "$D" fetch --no-tags origin "$SOURCE_SHA"
fi
git -C "$D" cat-file -e "$SOURCE_SHA^{commit}"
git -C "$D" checkout --detach "$SOURCE_SHA" >/dev/null
ACTUAL="$(git -C "$D" rev-parse HEAD)"
[[ "$ACTUAL" == "$SOURCE_SHA" ]] || { echo "D4_WOP_REMOTE_SOURCE_MISMATCH=$ACTUAL" >&2; exit 70; }
ACTUAL_BLOB="$(git -C "$D" rev-parse "${SOURCE_SHA}:$LINUX_REL")"
[[ "$ACTUAL_BLOB" == "$LINUX_BLOB" ]] || { echo "D4_WOP_REMOTE_LINUX_BLOB_MISMATCH=$ACTUAL_BLOB" >&2; exit 70; }
echo "D4_WOP_REMOTE_EXACT_BINDINGS=PASS"
export STAGE12_WINDOWS_READY_CONFIRMATION='STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS'
cd "$D"
set +e
bash "$LINUX_REL"
RC=$?
set -e
exit "$RC"
'@
  $remoteScript = $remoteTemplate.Replace("__SOURCE_SHA__",$sourceSha).Replace("__LINUX_REL__",$linuxRel).Replace("__LINUX_BLOB__",$linuxBlob).Replace("__TOKEN__",$token)
  $remoteB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($remoteScript))
  $remoteCommand = "printf '%s' '$remoteB64' | base64 -d | bash"

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
