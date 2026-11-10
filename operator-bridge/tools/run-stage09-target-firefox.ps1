param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,

  [Parameter(Mandatory = $true)]
  [string]$ResultPath,

  [string]$FirefoxPath = "C:\Program Files\Mozilla Firefox\firefox.exe",

  [string]$FirefoxProfile = "WorkspaceWorkers"
)

$ErrorActionPreference = "Stop"

$bridgeRoot = Join-Path $RepositoryRoot "operator-bridge"
$runnerDll = Join-Path $bridgeRoot "performance/bin/Release/net10.0-windows/WorkspaceOperator.PerformanceHarness.dll"
$helperExe = Join-Path $bridgeRoot "src/WorkspaceOperator/bin/Release/net10.0-windows/WorkspaceOperator.exe"
$regPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"

if (-not (Test-Path $runnerDll -PathType Leaf)) {
  throw "Stage 09 performance harness is missing. Build the integration solution in Release first."
}
if (-not (Test-Path $helperExe -PathType Leaf)) {
  throw "WorkspaceOperator helper is missing. Build the production solution in Release first."
}
if (-not (Test-Path $FirefoxPath -PathType Leaf)) {
  throw "Firefox executable was not found at the reviewed path."
}
if (-not (Test-Path $regPath)) {
  throw "Stage-08 per-user native-host registration is required before target measurement."
}
if (Get-Process firefox -ErrorAction SilentlyContinue) {
  throw "Target measurement rejected: unrelated same-name Firefox process is present."
}

$work = Join-Path $env:TEMP ("workspace-operator-stage09-target-" + [Guid]::NewGuid().ToString("N"))
New-Item $work -ItemType Directory -Force | Out-Null

$fakeWorkerRoot = Join-Path $bridgeRoot "simulator/FirefoxProfile/extension"
$fakeWorkerOut = Join-Path $work "fake-worker.out.log"
$fakeWorkerErr = Join-Path $work "fake-worker.err.log"
$runnerOut = Join-Path $work "runner.out.log"
$runnerErr = Join-Path $work "runner.err.log"
$readyFile = Join-Path $work "server.ready"

$fakeWorker = $null
$runner = $null
$firefox = $null

try {
  $fakeWorker = Start-Process -FilePath "python" -ArgumentList @(
    "-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", $fakeWorkerRoot
  ) -RedirectStandardOutput $fakeWorkerOut -RedirectStandardError $fakeWorkerErr -PassThru

  $runner = Start-Process -FilePath "dotnet" -ArgumentList @(
    $runnerDll,
    "--result=$ResultPath",
    "--helper=$helperExe",
    "--ready-file=$readyFile",
    "--mode=target",
    "--warmup-ms=60000",
    "--sample-ms=120000",
    "--sample-interval-ms=1000",
    "--latency-scale=1",
    "--timeout-seconds=120"
  ) -RedirectStandardOutput $runnerOut -RedirectStandardError $runnerErr -PassThru

  # The harness performs the full helper-idle 60s/120s window before exposing
  # the browser-server ready marker.
  $readyDeadline = (Get-Date).AddMinutes(4)
  while (-not (Test-Path $readyFile) -and (Get-Date) -lt $readyDeadline) {
    if ($runner.HasExited) { break }
    Start-Sleep -Milliseconds 250
  }
  if (-not (Test-Path $readyFile)) {
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    throw "Target Firefox collector did not reach browser-server readiness."
  }

  $firefox = Start-Process -FilePath $FirefoxPath -ArgumentList @(
    "-P", $FirefoxProfile, "-no-remote"
  ) -PassThru

  if (-not $runner.WaitForExit(1800000)) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
    throw "Target Firefox collector exceeded the bounded 30-minute execution window."
  }

  if ($runner.ExitCode -ne 0) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    if (Test-Path $ResultPath) { Get-Content $ResultPath }
    throw "Target Firefox collector failed."
  }

  $result = Get-Content $ResultPath -Raw | ConvertFrom-Json
  if ($result.evidence_class -ne "TARGET_MODE_PARTIAL") {
    throw "Target Firefox collector emitted an unexpected evidence class."
  }
  if ($result.target_contract_complete -ne $false) {
    throw "Firefox-only target evidence must not claim complete UX-09 acceptance."
  }
  if ($result.content_policy -ne "CONTENT_FREE") {
    throw "Target Firefox evidence must remain content-free."
  }

  Write-Host "STAGE09_TARGET_FIREFOX_PARTIAL=PASS"
  Get-Content $ResultPath
}
finally {
  if ($runner -and -not $runner.HasExited) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
  }
  if ($firefox -and -not $firefox.HasExited) {
    Stop-Process -Id $firefox.Id -Force -ErrorAction SilentlyContinue
  }
  if ($fakeWorker -and -not $fakeWorker.HasExited) {
    Stop-Process -Id $fakeWorker.Id -Force -ErrorAction SilentlyContinue
  }

  # Only the process started by this collector is explicitly stopped above.
  # Any remaining Firefox process makes the target run invalid rather than
  # being killed or adopted.
  if (Get-Process firefox -ErrorAction SilentlyContinue) {
    Write-Warning "Firefox remains running after collector cleanup; reject this target run."
  }

  Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
}
