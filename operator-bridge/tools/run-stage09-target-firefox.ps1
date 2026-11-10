param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,

  [Parameter(Mandatory = $true)]
  [string]$ResultPath,

  [string]$FirefoxPath = "C:\Program Files\Mozilla Firefox\firefox.exe",

  [string]$FirefoxProfile = "WorkspaceWorkers",

  [switch]$SkipLatency,

  [switch]$SkipColdStart,

  [switch]$PreflightOnly,

  [string]$DiagnosticsDirectory = ""
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
$collectorSucceeded = $false
$ownedFirefoxIds = [System.Collections.Generic.HashSet[int]]::new()

function Update-OwnedFirefoxIds {
  if ($ownedFirefoxIds.Count -eq 0) { return }
  $rows = @(Get-CimInstance Win32_Process -Filter "Name='firefox.exe'" -ErrorAction SilentlyContinue)
  $changed = $true
  while ($changed) {
    $changed = $false
    foreach ($row in $rows) {
      $pidValue = [int]$row.ProcessId
      $parentValue = [int]$row.ParentProcessId
      if ($ownedFirefoxIds.Contains($parentValue) -and -not $ownedFirefoxIds.Contains($pidValue)) {
        [void]$ownedFirefoxIds.Add($pidValue)
        $changed = $true
      }
    }
  }
}

function Stop-TrackedFirefoxProcesses {
  Update-OwnedFirefoxIds
  foreach ($ownedId in @($ownedFirefoxIds | Sort-Object -Descending)) {
    try {
      $ownedProcess = Get-Process -Id $ownedId -ErrorAction Stop
      if ($ownedProcess.ProcessName -eq "firefox") {
        Stop-Process -Id $ownedId -Force -ErrorAction SilentlyContinue
      }
    } catch {
    }
  }

  $deadline = (Get-Date).AddSeconds(10)
  while ((Get-Date) -lt $deadline) {
    Update-OwnedFirefoxIds
    $ownedRemaining = @($ownedFirefoxIds | Where-Object {
      Get-Process -Id $_ -ErrorAction SilentlyContinue
    })
    if ($ownedRemaining.Count -eq 0) { break }
    Start-Sleep -Milliseconds 100
  }
}

function Write-BoundedTextDiagnostic {
  param([string]$Source, [string]$Destination)
  if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { return }
  $lines = @(Get-Content -LiteralPath $Source -Tail 200 -ErrorAction SilentlyContinue)
  [System.IO.File]::WriteAllLines($Destination, [string[]]$lines)
}

function Get-BoundedFirefoxProcessMetadata {
  $rows = @(Get-CimInstance Win32_Process -Filter "Name='firefox.exe'" -ErrorAction SilentlyContinue | Select-Object -First 16)
  $items = @()
  foreach ($row in $rows) {
    $sessionId = $null
    try {
      $sessionId = (Get-Process -Id ([int]$row.ProcessId) -ErrorAction Stop).SessionId
    } catch {
    }
    $items += [ordered]@{
      process_id = [int]$row.ProcessId
      parent_process_id = [int]$row.ParentProcessId
      session_id = $sessionId
      owned_by_collector = $ownedFirefoxIds.Contains([int]$row.ProcessId)
    }
  }
  return @($items)
}

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
  [void]$ownedFirefoxIds.Add([int]$firefox.Id)
  Update-OwnedFirefoxIds

  $runnerTimeoutMs = $(if ($PreflightOnly) { 60000 } else { 1800000 })
  $runnerDeadline = (Get-Date).AddMilliseconds($runnerTimeoutMs)
  while (-not $runner.HasExited -and (Get-Date) -lt $runnerDeadline) {
    Update-OwnedFirefoxIds
    Start-Sleep -Milliseconds 100
    $runner.Refresh()
  }
  Update-OwnedFirefoxIds
  if (-not $runner.HasExited) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
    throw $(if ($PreflightOnly) { "Target Firefox adapter preflight timed out." } else { "Target Firefox collector exceeded the bounded 30-minute execution window." })
  }

  # Polling above is required to retain Firefox process ancestry while the
  # harness runs. Finalize the Process object before reading ExitCode;
  # Start-Process -PassThru may otherwise expose a null exit code even after
  # HasExited becomes true, which PowerShell compares as non-zero.
  $runner.WaitForExit()
  $runner.Refresh()

  if (-not $PreflightOnly -and $runner.ExitCode -ne 0) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    if (Test-Path $steadyResultPath) { Get-Content $steadyResultPath }
    throw "Target Firefox steady-state collector failed."
  }

  if (-not (Test-Path -LiteralPath $steadyResultPath -PathType Leaf)) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    throw $(if ($PreflightOnly) { "Target Firefox adapter preflight produced no result evidence." } else { "Target Firefox steady-state collector produced no result evidence." })
  }

  $steadyResult = Get-Content $steadyResultPath -Raw | ConvertFrom-Json
  if ($PreflightOnly) {
    # PowerShell's live Process.ExitCode property can remain null briefly even
    # after HasExited/WaitForExit on this Windows runner. The harness-written
    # bounded result is authoritative for adapter preflight success/failure.
    if ($steadyResult.evidence_class -ne "TARGET_ADAPTER_PREFLIGHT" -or
        $steadyResult.status -ne "PASS" -or
        $steadyResult.adapter_version -ne "0.1.9-perf") {
      if (Test-Path $runnerOut) { Get-Content $runnerOut }
      if (Test-Path $runnerErr) { Get-Content $runnerErr }
      throw "Target Firefox adapter preflight emitted failing or invalid evidence."
    }
    $steadyResult | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ResultPath -Encoding UTF8
    $collectorSucceeded = $true
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
    Stop-TrackedFirefoxProcesses
    $firefox = $null

    if (Get-Process firefox -ErrorAction SilentlyContinue) {
      throw "Target measurement rejected: Firefox did not reach the required cold-start baseline without adopting or killing unowned processes."
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

  $collectorSucceeded = $true
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
  Stop-TrackedFirefoxProcesses

  if ($fakeWorker -and -not $fakeWorker.HasExited) {
    Stop-Process -Id $fakeWorker.Id -Force -ErrorAction SilentlyContinue
  }

  $remainingFirefox = @(Get-BoundedFirefoxProcessMetadata)
  $cleanupFailed = $remainingFirefox.Count -gt 0

  if ($PreflightOnly -and (-not $collectorSucceeded -or $cleanupFailed)) {
    $diagnosticRoot = if ([string]::IsNullOrWhiteSpace($DiagnosticsDirectory)) {
      [System.IO.Path]::GetFullPath($ResultPath + ".diagnostics")
    } else {
      [System.IO.Path]::GetFullPath($DiagnosticsDirectory)
    }
    New-Item -ItemType Directory -Path $diagnosticRoot -Force | Out-Null
    Write-BoundedTextDiagnostic -Source $runnerOut -Destination (Join-Path $diagnosticRoot "runner.out.log")
    Write-BoundedTextDiagnostic -Source $runnerErr -Destination (Join-Path $diagnosticRoot "runner.err.log")
    Write-BoundedTextDiagnostic -Source $fakeWorkerOut -Destination (Join-Path $diagnosticRoot "fake-worker.out.log")
    Write-BoundedTextDiagnostic -Source $fakeWorkerErr -Destination (Join-Path $diagnosticRoot "fake-worker.err.log")
    if (Test-Path -LiteralPath $steadyResultPath -PathType Leaf) {
      Copy-Item -LiteralPath $steadyResultPath -Destination (Join-Path $diagnosticRoot "adapter-preflight-result.json") -Force
    }

    $launcherHasExited = $null
    if ($firefox) {
      try {
        $firefox.Refresh()
        $launcherHasExited = [bool]$firefox.HasExited
      } catch {
      }
    }
    [ordered]@{
      schema_version = 1
      evidence_class = "TARGET_ADAPTER_PREFLIGHT_DIAGNOSTICS"
      content_policy = "CONTENT_FREE"
      launcher_pid = $(if ($firefox) { [int]$firefox.Id } else { $null })
      launcher_has_exited = $launcherHasExited
      runner_exit_code = $(if ($runner -and $runner.HasExited) { [int]$runner.ExitCode } else { $null })
      tracked_owned_firefox_ids = @($ownedFirefoxIds | Sort-Object)
      remaining_firefox_process_count = $remainingFirefox.Count
      remaining_firefox_processes = $remainingFirefox
      captured_files = @(
        "runner.out.log",
        "runner.err.log",
        "fake-worker.out.log",
        "fake-worker.err.log",
        $(if (Test-Path -LiteralPath $steadyResultPath -PathType Leaf) { "adapter-preflight-result.json" } else { $null })
      ) | Where-Object { $_ }
    } | ConvertTo-Json -Depth 8 |
      Set-Content -LiteralPath (Join-Path $diagnosticRoot "process-summary.json") -Encoding UTF8
  }

  if ($cleanupFailed) {
    Write-Warning "Firefox remains running after collector-owned cleanup; reject this target run without adopting or killing unowned processes."
  }

  Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue

  if ($collectorSucceeded -and $cleanupFailed) {
    throw "Target Firefox cleanup did not reach a clean owned-process baseline."
  }
}
