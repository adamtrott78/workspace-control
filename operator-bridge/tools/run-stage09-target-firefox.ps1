param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,

  [Parameter(Mandatory = $true)]
  [string]$ResultPath,

  [string]$FirefoxPath = "C:\Program Files\Mozilla Firefox\firefox.exe",

  [string]$FirefoxProfile = "WorkspaceWorkers",

  [switch]$SkipLatency,

  [switch]$SkipColdStart,

  [switch]$PreflightOnly
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
if ($FirefoxProfile -ne "WorkspaceWorkers") {
  throw "Target measurement requires the frozen WorkspaceWorkers Firefox profile."
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
$coldRunnerOut = Join-Path $work "cold-runner.out.log"
$coldRunnerErr = Join-Path $work "cold-runner.err.log"
$steadyResultPath = Join-Path $work "firefox-steady.json"
$coldResultPath = Join-Path $work "firefox-cold.json"
$readyFile = Join-Path $work "server.ready"

$fakeWorker = $null
$runner = $null
$coldRunner = $null
$firefox = $null

try {
  $fakeWorker = Start-Process -FilePath "python" -ArgumentList @(
    "-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", $fakeWorkerRoot
  ) -RedirectStandardOutput $fakeWorkerOut -RedirectStandardError $fakeWorkerErr -PassThru

  $runnerArgs = if ($PreflightOnly) {
    @(
      $runnerDll,
      "--result=$steadyResultPath",
      "--helper=$helperExe",
      "--ready-file=$readyFile",
      "--mode=adapter-preflight",
      "--timeout-seconds=30"
    )
  } else {
    @(
      $runnerDll,
      "--result=$steadyResultPath",
      "--helper=$helperExe",
      "--ready-file=$readyFile",
      "--mode=target",
      "--warmup-ms=60000",
      "--sample-ms=120000",
      "--sample-interval-ms=1000",
      "--latency-scale=1",
      "--timeout-seconds=120"
    )
  }
  if ($SkipLatency -and -not $PreflightOnly) {
    $runnerArgs += "--skip-latency"
  }
  $runner = Start-Process -FilePath "dotnet" -ArgumentList $runnerArgs -RedirectStandardOutput $runnerOut -RedirectStandardError $runnerErr -PassThru

  # Full target mode performs helper-idle measurement before readiness;
  # adapter-preflight publishes readiness immediately and sends no browser command.
  $readyDeadline = (Get-Date).AddMinutes($(if ($PreflightOnly) { 1 } else { 4 }))
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

  $runnerTimeoutMs = $(if ($PreflightOnly) { 60000 } else { 1800000 })
  if (-not $runner.WaitForExit($runnerTimeoutMs)) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
    throw $(if ($PreflightOnly) { "Target Firefox adapter preflight timed out." } else { "Target Firefox collector exceeded the bounded 30-minute execution window." })
  }

  if ($runner.ExitCode -ne 0) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    if (Test-Path $steadyResultPath) { Get-Content $steadyResultPath }
    throw $(if ($PreflightOnly) { "Target Firefox adapter identity preflight failed." } else { "Target Firefox steady-state collector failed." })
  }

  $steadyResult = Get-Content $steadyResultPath -Raw | ConvertFrom-Json
  if ($PreflightOnly) {
    if ($steadyResult.evidence_class -ne "TARGET_ADAPTER_PREFLIGHT" -or
        $steadyResult.status -ne "PASS" -or
        $steadyResult.adapter_version -ne "0.1.9-perf") {
      throw "Target Firefox adapter preflight emitted invalid evidence."
    }
    $steadyResult | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ResultPath -Encoding UTF8
    Write-Host "STAGE09_TARGET_ADAPTER_PREFLIGHT=PASS"
    return
  }
  if ($steadyResult.evidence_class -ne "TARGET_MODE_PARTIAL") {
    throw "Target Firefox steady-state collector emitted an unexpected evidence class."
  }
  if ($steadyResult.target_contract_complete -ne $false) {
    throw "Firefox-only target evidence must not claim complete UX-09 acceptance."
  }
  if ($steadyResult.content_policy -ne "CONTENT_FREE") {
    throw "Target Firefox evidence must remain content-free."
  }

  $coldResult = $null
  if (-not $SkipColdStart) {
    if ($firefox -and -not $firefox.HasExited) {
      Stop-Process -Id $firefox.Id -Force -ErrorAction SilentlyContinue
      $firefox.WaitForExit(10000) | Out-Null
    }
    $firefox = $null

    $closeDeadline = (Get-Date).AddSeconds(10)
    while ((Get-Process firefox -ErrorAction SilentlyContinue) -and (Get-Date) -lt $closeDeadline) {
      Start-Sleep -Milliseconds 100
    }
    if (Get-Process firefox -ErrorAction SilentlyContinue) {
      throw "Target measurement rejected: Firefox did not reach the required cold-start baseline."
    }

    $coldRunner = Start-Process -FilePath "dotnet" -ArgumentList @(
      $runnerDll,
      "--result=$coldResultPath",
      "--helper=$helperExe",
      "--mode=cold-target",
      "--cold-count=10",
      "--timeout-seconds=120"
    ) -RedirectStandardOutput $coldRunnerOut -RedirectStandardError $coldRunnerErr -PassThru

    if (-not $coldRunner.WaitForExit(300000)) {
      Stop-Process -Id $coldRunner.Id -Force -ErrorAction SilentlyContinue
      throw "Target cold-start collector exceeded the bounded 5-minute execution window."
    }
    if ($coldRunner.ExitCode -ne 0) {
      if (Test-Path $coldRunnerOut) { Get-Content $coldRunnerOut }
      if (Test-Path $coldRunnerErr) { Get-Content $coldRunnerErr }
      if (Test-Path $coldResultPath) { Get-Content $coldResultPath }
      throw "Target cold-start collector failed."
    }

    $coldResult = Get-Content $coldResultPath -Raw | ConvertFrom-Json
    if ($coldResult.evidence_class -ne "TARGET_COLD_FIREFOX_PARTIAL") {
      throw "Target cold-start collector emitted an unexpected evidence class."
    }
    if ($coldResult.target_contract_complete -ne $false) {
      throw "Cold-start partial evidence must not claim complete UX-09 acceptance."
    }
    if ($coldResult.cold_firefox_start.count -ne 10) {
      throw "Target cold-start collector did not execute the frozen 10 trials."
    }

  }
  [ordered]@{
    schema_version = 1
    stage = "impl_09_performance_benchmark_execution"
    evidence_class = "TARGET_FIREFOX_PARTIAL"
    target_contract_complete = $false
    content_policy = "CONTENT_FREE"
    steady_state = $steadyResult
    cold_start = $coldResult
    remaining_requirements = @(
      "three complete Firefox/Chrome resource replicates with order alternation",
      "Chrome Memory Saver disabled and recorded",
      "five discard/restore resource replicates",
      $(if ($SkipLatency) { "exact 50/30/30/100 steady-state latency counts" } else { $null }),
      $(if ($SkipColdStart) { "exact 10-trial cold-start latency count" } else { $null }),
      "complete aggregate budget evaluation"
    ) | Where-Object { $_ }
  } | ConvertTo-Json -Depth 20 | Set-Content $ResultPath -Encoding UTF8

  Write-Host "STAGE09_TARGET_FIREFOX_PARTIAL=PASS"
  Get-Content $ResultPath
}
finally {
  if ($runner -and -not $runner.HasExited) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
  }
  if ($coldRunner -and -not $coldRunner.HasExited) {
    Stop-Process -Id $coldRunner.Id -Force -ErrorAction SilentlyContinue
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
