[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,

  [Parameter(Mandatory = $true)]
  [string]$ResultPath,

  [string]$FirefoxPath = "C:\Program Files\Mozilla Firefox\firefox.exe",

  [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",

  [string]$FirefoxProfile = "WorkspaceWorkers",

  [string]$PerformanceSignedXpiPath = (Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Stage09\workspace-control-operator-performance-signed.xpi"),

  [switch]$ConfirmAcPower,

  [switch]$ConfirmChromeMemorySaverDisabled,

  [switch]$PlanOnly,

  [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"

$WarmupSeconds = 60
$SteadySeconds = 120
$SampleRateHz = 1
$BrowserResourceRepetitions = 3
$DiscardRestoreRepetitions = 5
$ReuseRepetitions = 50
$RestoreRepetitions = 30
$CreateRepetitions = 30
$ColdStartRepetitions = 10
$PrimitiveRepetitions = 100
$BackgroundCpuRejectPercent = 20
$BrowserOrder = @(
  @("firefox", "chrome"),
  @("chrome", "firefox"),
  @("firefox", "chrome")
)

$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$resultPathFull = [System.IO.Path]::GetFullPath($ResultPath)
$resultDir = Split-Path -Parent $resultPathFull
New-Item -ItemType Directory -Path $resultDir -Force | Out-Null

$sourceSha = (& git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") {
  throw "Stage 09 target matrix requires an exact Git source SHA."
}

$plan = [ordered]@{
  schema_version = 1
  stage = "impl_09_performance_benchmark_execution"
  evidence_class = "TARGET_MATRIX_PLAN_ONLY"
  source_sha = $sourceSha
  target_contract_complete = $false
  measurement = [ordered]@{
    warmup_seconds = $WarmupSeconds
    steady_state_seconds = $SteadySeconds
    sample_rate_hz = $SampleRateHz
    browser_order = $BrowserOrder
  }
  repetitions = [ordered]@{
    browser_resource = $BrowserResourceRepetitions
    discard_restore = $DiscardRestoreRepetitions
    reuse = $ReuseRepetitions
    restore = $RestoreRepetitions
    create = $CreateRepetitions
    cold_start = $ColdStartRepetitions
    local_primitives = $PrimitiveRepetitions
  }
  target_requirements = @(
    "AC power explicitly confirmed",
    "Chrome Memory Saver explicitly confirmed disabled",
    "no pre-existing Firefox/Chrome/WorkspaceOperator process",
    "unrelated CPU mean <= 20 percent of total CPU during measured windows",
    "content-free OS process telemetry only"
  )
}

if ($PlanOnly) {
  $plan | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPathFull -Encoding UTF8
  Write-Host "STAGE09_TARGET_MATRIX_PLAN=PASS"
  Get-Content -LiteralPath $resultPathFull
  return
}

if (-not $PreflightOnly) {
  if (-not $ConfirmAcPower) {
    throw "Target matrix requires explicit -ConfirmAcPower."
  }
  if (-not $ConfirmChromeMemorySaverDisabled) {
    throw "Target matrix requires explicit -ConfirmChromeMemorySaverDisabled."
  }
}
if ($FirefoxProfile -ne "WorkspaceWorkers") {
  throw "Target matrix requires the frozen WorkspaceWorkers Firefox profile."
}

if (-not (Test-Path -LiteralPath $FirefoxPath -PathType Leaf)) {
  throw "Firefox executable not found at the reviewed path."
}
if (-not $PreflightOnly -and -not (Test-Path -LiteralPath $ChromePath -PathType Leaf)) {
  $alternateChrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
  if (Test-Path -LiteralPath $alternateChrome -PathType Leaf) {
    $ChromePath = $alternateChrome
  } else {
    throw "Chrome executable not found at a reviewed path."
  }
}

$preflightProcessNames = @("firefox", "WorkspaceOperator")
$fullProcessNames = @("firefox", "chrome", "WorkspaceOperator")
foreach ($name in $(if ($PreflightOnly) { $preflightProcessNames } else { $fullProcessNames })) {
  if (Get-Process -Name $name -ErrorAction SilentlyContinue) {
    throw "Target measurement rejected: pre-existing $name process is present."
  }
}

$bridgeRoot = Join-Path $repo "operator-bridge"
$helperExe = Join-Path $bridgeRoot "src\WorkspaceOperator\bin\Release\net10.0-windows\WorkspaceOperator.exe"
$targetFirefoxScript = Join-Path $bridgeRoot "tools\run-stage09-target-firefox.ps1"
$profilePrepScript = Join-Path $bridgeRoot "performance\prepare-stage09-target-profile.ps1"
$validator = Join-Path $bridgeRoot "performance\validate-stage09-target.py"
$fakeWorkerRoot = Join-Path $bridgeRoot "simulator\FirefoxProfile\extension"
if (-not (Test-Path -LiteralPath $targetFirefoxScript -PathType Leaf)) {
  throw "Target Firefox collector is missing."
}
if (-not (Test-Path -LiteralPath $validator -PathType Leaf)) {
  throw "Target evidence validator is missing."
}
if (-not (Test-Path -LiteralPath $profilePrepScript -PathType Leaf)) {
  throw "Stage 09 target-profile preparation script is missing."
}
if (-not (Test-Path -LiteralPath $PerformanceSignedXpiPath -PathType Leaf)) {
  throw "Stage 09 requires the Mozilla-signed fake-worker performance XPI at: $PerformanceSignedXpiPath"
}

# The target measurement must not inherit persistent compiler/MSBuild servers
# from its own exact-head build. They are GitHub-job-owned work, but detached
# build servers are not reliably discoverable through the live parent/child
# process tree used by the frozen unrelated-CPU calculation.
& dotnet build (Join-Path $bridgeRoot "WorkspaceOperatorBridge.Integration.slnx") `
  --configuration Release `
  --disable-build-servers `
  -p:UseSharedCompilation=false `
  -nodeReuse:false
if ($LASTEXITCODE -ne 0) {
  throw "Stage 09 target matrix build failed."
}

& $profilePrepScript -RepositoryRoot $repo -SignedXpiPath $PerformanceSignedXpiPath -FirefoxPath $FirefoxPath -ProfileName $FirefoxProfile -VerifyOnly
if ($LASTEXITCODE -ne 0) {
  throw "Stage 09 target Firefox profile preparation failed."
}

$work = Join-Path $env:TEMP ("workspace-operator-stage09-matrix-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work -Force | Out-Null
$chromeFakeWorker = $null
$nativeRegPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
$nativeRegExisted = Test-Path -LiteralPath $nativeRegPath
$nativeHostOverridden = $false
$originalNativeHostPath = $null
if ($nativeRegExisted) {
  $originalNativeHostPath = (Get-Item -LiteralPath $nativeRegPath).GetValue("")
  if ([string]::IsNullOrWhiteSpace([string]$originalNativeHostPath)) {
    throw "Existing native-host registration is empty; refusing to overwrite ambiguous state."
  }
}
if (-not (Test-Path -LiteralPath $helperExe -PathType Leaf)) {
  throw "Exact-head helper build is missing after target matrix build."
}

$targetNativeManifest = Join-Path $work "native-host-exact-head.json"
[ordered]@{
  name = "com.workspacecontrol.operator_bridge"
  description = "Workspace Control Operator Stage 09 Exact-Head Native Host"
  path = $helperExe
  type = "stdio"
  allowed_extensions = @("workspace-control-operator@adamtrott78.local")
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $targetNativeManifest -Encoding UTF8

function Get-Percentile {
  param([double[]]$Values, [double]$P)
  if ($Values.Count -eq 0) { return 0.0 }
  $sorted = @($Values | Sort-Object)
  $index = [Math]::Max(0, [Math]::Min($sorted.Count - 1, [Math]::Ceiling($P * $sorted.Count) - 1))
  return [double]$sorted[$index]
}

function Get-Summary {
  param([double[]]$Values)
  if ($Values.Count -eq 0) {
    return [ordered]@{ p50 = 0.0; p95 = 0.0; max = 0.0; mean = 0.0 }
  }
  return [ordered]@{
    p50 = Get-Percentile $Values 0.50
    p95 = Get-Percentile $Values 0.95
    max = [double](($Values | Measure-Object -Maximum).Maximum)
    mean = [double](($Values | Measure-Object -Average).Average)
  }
}

function Get-DescendantProcessIds {
  param([int]$RootPid)
  $rows = @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId)
  $seen = [System.Collections.Generic.HashSet[int]]::new()
  [void]$seen.Add($RootPid)
  $changed = $true
  while ($changed) {
    $changed = $false
    foreach ($row in $rows) {
      $pidValue = [int]$row.ProcessId
      $parent = [int]$row.ParentProcessId
      if ($seen.Contains($parent) -and -not $seen.Contains($pidValue)) {
        [void]$seen.Add($pidValue)
        $changed = $true
      }
    }
  }
  return @($seen)
}

function New-ProcessOwnershipTracker {
  param(
    [string]$Name,
    [int]$RootPid
  )
  $known = [System.Collections.Generic.HashSet[int]]::new()
  [void]$known.Add($RootPid)
  return [pscustomobject]@{
    Name = $Name
    SessionId = (Get-Process -Id $PID).SessionId
    KnownPids = $known
    LastNamedPidSignature = ""
  }
}

function Add-ProcessOwnershipRoot {
  param(
    $Tracker,
    [int]$RootPid
  )
  [void]$Tracker.KnownPids.Add($RootPid)
}

function Update-ProcessOwnershipTracker {
  param($Tracker)

  $rows = @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId)
  $changed = $true
  while ($changed) {
    $changed = $false
    foreach ($row in $rows) {
      $pidValue = [int]$row.ProcessId
      $parent = [int]$row.ParentProcessId
      if ($Tracker.KnownPids.Contains($parent) -and -not $Tracker.KnownPids.Contains($pidValue)) {
        [void]$Tracker.KnownPids.Add($pidValue)
        $changed = $true
      }
    }
  }

  $namedRows = @(
    $rows |
      Where-Object {
        try {
          $proc = Get-Process -Id ([int]$_.ProcessId) -ErrorAction Stop
          $proc.ProcessName -eq $Tracker.Name -and $proc.SessionId -eq $Tracker.SessionId
        } catch {
          $false
        }
      } |
      Sort-Object ProcessId
  )
  $signature = (($namedRows | ForEach-Object { "$($_.ProcessId):$($_.ParentProcessId)" }) -join ",")
  if ($signature -ne $Tracker.LastNamedPidSignature) {
    $event = [ordered]@{
      process_name = $Tracker.Name
      named_processes = @($namedRows | ForEach-Object {
        [ordered]@{
          pid = [int]$_.ProcessId
          parent_pid = [int]$_.ParentProcessId
          historically_owned = $Tracker.KnownPids.Contains([int]$_.ProcessId)
        }
      })
      historically_owned_pids = @($Tracker.KnownPids | Sort-Object)
    }
    Write-Host ("STAGE09_PROCESS_TRACKER_EVENT=" + ($event | ConvertTo-Json -Depth 5 -Compress))
    $Tracker.LastNamedPidSignature = $signature
  }

  foreach ($row in $namedRows) {
    $pidValue = [int]$row.ProcessId
    if (-not $Tracker.KnownPids.Contains($pidValue)) {
      throw "Target measurement rejected: unowned $($Tracker.Name) process appeared during measurement."
    }
  }
}

function Get-TrackedOwnedProcessIds {
  param($Tracker)
  $ids = [System.Collections.Generic.HashSet[int]]::new()
  foreach ($id in @(Get-DescendantProcessIds -RootPid $PID)) {
    [void]$ids.Add([int]$id)
  }
  if ($null -ne $Tracker) {
    foreach ($id in $Tracker.KnownPids) {
      if (Get-Process -Id $id -ErrorAction SilentlyContinue) {
        [void]$ids.Add([int]$id)
      }
    }
  }
  return @($ids)
}

function Stop-TrackedProcessName {
  param($Tracker)

  Update-ProcessOwnershipTracker -Tracker $Tracker
  $deadline = (Get-Date).AddSeconds(15)
  while ((Get-Date) -lt $deadline) {
    $current = @(Get-Process -Name $Tracker.Name -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $Tracker.SessionId })
    if ($current.Count -eq 0) {
      return
    }

    Update-ProcessOwnershipTracker -Tracker $Tracker
    foreach ($p in $current) {
      if (-not $Tracker.KnownPids.Contains($p.Id)) {
        throw "Target measurement rejected: $($Tracker.Name) process attribution/cleanup was lost."
      }
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 200
  }

  if (Get-Process -Name $Tracker.Name -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $Tracker.SessionId }) {
    throw "Target measurement rejected: $($Tracker.Name) process attribution/cleanup was lost."
  }
}

function Get-CpuSnapshot {
  param([int[]]$ProcessIds)
  $map = @{}
  foreach ($pidValue in $ProcessIds) {
    try {
      $p = Get-Process -Id $pidValue -ErrorAction Stop
      $map[$pidValue] = [double]$p.TotalProcessorTime.TotalSeconds
    } catch {
    }
  }
  return $map
}

function Get-ProcessNameCpuSnapshot {
  param([string]$Name)
  $map = @{}
  $session = (Get-Process -Id $PID).SessionId
  foreach ($p in @(Get-Process -Name $Name -ErrorAction SilentlyContinue)) {
    try {
      if ($p.SessionId -eq $session) {
        $map[$p.Id] = [double]$p.TotalProcessorTime.TotalSeconds
      }
    } catch {
    }
  }
  return $map
}

function Get-CpuDeltaSeconds {
  param($Before, $After)
  $sum = 0.0
  foreach ($entry in $After.GetEnumerator()) {
    if ($Before.ContainsKey($entry.Key)) {
      $sum += [Math]::Max(0.0, [double]$entry.Value - [double]$Before[$entry.Key])
    }
  }
  return $sum
}

function Get-TotalCpuPercent {
  try {
    return [double](Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'").PercentProcessorTime
  } catch {
    return 0.0
  }
}

function Assert-BackgroundCpuQuiet {
  param(
    [int]$Seconds = 10,
    [double]$LimitPercent = $BackgroundCpuRejectPercent,
    [int]$MaxAttempts = 6,
    [int]$RetryDelaySeconds = 5
  )

  # Apply the same frozen "unrelated CPU" definition used by the measured
  # scenarios. The benchmark's own build/compiler descendants must not make
  # the quiet-machine preflight reject itself. A bounded settle loop permits
  # transient post-build/antimalware spikes to drain without weakening the
  # frozen <=20% mean requirement for any accepted window.
  $bestMean = [double]::PositiveInfinity

  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $samples = [System.Collections.Generic.List[double]]::new()
    $ownedBefore = Get-CpuSnapshot -ProcessIds @(Get-DescendantProcessIds -RootPid $PID)
    $wallBefore = Get-Date

    for ($i = 0; $i -lt $Seconds; $i++) {
      Start-Sleep -Seconds 1
      $ownedAfter = Get-CpuSnapshot -ProcessIds @(Get-DescendantProcessIds -RootPid $PID)
      $wallAfter = Get-Date
      $wallSeconds = [Math]::Max(0.001, ($wallAfter - $wallBefore).TotalSeconds)
      $ownedCpuTotal = (Get-CpuDeltaSeconds $ownedBefore $ownedAfter) / $wallSeconds / [Environment]::ProcessorCount * 100.0
      $unrelatedCpu = [Math]::Max(0.0, (Get-TotalCpuPercent) - $ownedCpuTotal)
      $samples.Add($unrelatedCpu)
      $ownedBefore = $ownedAfter
      $wallBefore = $wallAfter
    }

    $summary = Get-Summary ([double[]]$samples.ToArray())
    $bestMean = [Math]::Min($bestMean, [double]$summary.mean)
    $accepted = ([double]$summary.mean -le $LimitPercent)
    Write-Host ("STAGE09_BACKGROUND_CPU_PREFLIGHT=" + ([ordered]@{
      attempt = $attempt
      max_attempts = $MaxAttempts
      sample_seconds = $Seconds
      mean_unrelated_cpu_percent = [double]$summary.mean
      p95_unrelated_cpu_percent = [double]$summary.p95
      limit_percent = $LimitPercent
      accepted = $accepted
    } | ConvertTo-Json -Depth 4 -Compress))

    if ($accepted) {
      return
    }
    if ($attempt -lt $MaxAttempts) {
      Start-Sleep -Seconds $RetryDelaySeconds
    }
  }

  throw ("Target measurement rejected before benchmark: unrelated background CPU did not settle below {0:N2}% across {1} bounded windows; best mean was {2:N2}%." -f $LimitPercent, $MaxAttempts, $bestMean)
}

function Assert-NamedProcessesOwned {
  param([string]$Name)
  $owned = [System.Collections.Generic.HashSet[int]]::new()
  foreach ($id in @(Get-DescendantProcessIds -RootPid $PID)) {
    [void]$owned.Add([int]$id)
  }
  $session = (Get-Process -Id $PID).SessionId
  foreach ($p in @(Get-Process -Name $Name -ErrorAction SilentlyContinue)) {
    try {
      if ($p.SessionId -eq $session -and -not $owned.Contains($p.Id)) {
        throw "Target measurement rejected: unowned $Name process appeared during measurement."
      }
    } catch [System.Management.Automation.RuntimeException] {
      throw
    } catch {
    }
  }
}

function Measure-ProcessGroup {
  param(
    [string]$ProcessName,
    [string]$ScenarioId,
    [int]$Repetition,
    [Nullable[int]]$LiveTabs,
    $OwnershipTracker = $null
  )

  $warmupDeadline = (Get-Date).AddSeconds($WarmupSeconds)
  while ((Get-Date) -lt $warmupDeadline) {
    Start-Sleep -Milliseconds 250
    if ($null -ne $OwnershipTracker) {
      Update-ProcessOwnershipTracker -Tracker $OwnershipTracker
    } else {
      Assert-NamedProcessesOwned -Name $ProcessName
    }
  }

  $working = [System.Collections.Generic.List[double]]::new()
  $private = [System.Collections.Generic.List[double]]::new()
  $cpu = [System.Collections.Generic.List[double]]::new()
  $unrelated = [System.Collections.Generic.List[double]]::new()

  $targetBefore = Get-ProcessNameCpuSnapshot -Name $ProcessName
  $ownedBefore = Get-CpuSnapshot -ProcessIds @(Get-TrackedOwnedProcessIds -Tracker $OwnershipTracker)
  $wallBefore = Get-Date

  for ($i = 0; $i -lt $SteadySeconds; $i++) {
    Start-Sleep -Seconds 1
    if ($null -ne $OwnershipTracker) {
      Update-ProcessOwnershipTracker -Tracker $OwnershipTracker
    } else {
      Assert-NamedProcessesOwned -Name $ProcessName
    }

    $session = (Get-Process -Id $PID).SessionId
    $processes = @(Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $session })
    if ($processes.Count -eq 0) {
      if ($null -ne $OwnershipTracker) {
        $ownedAlive = @(
          $OwnershipTracker.KnownPids |
            Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue } |
            Sort-Object
        )
        Write-Host ("STAGE09_PROCESS_TRACKER_ZERO=" + ([ordered]@{
          process_name = $ProcessName
          scenario_id = $ScenarioId
          historically_owned_pids = @($OwnershipTracker.KnownPids | Sort-Object)
          historically_owned_alive_pids = @($ownedAlive)
        } | ConvertTo-Json -Depth 4 -Compress))
      }
      throw "No $ProcessName process available for $ScenarioId."
    }

    $workingMiB = [double](($processes | Measure-Object -Property WorkingSet64 -Sum).Sum) / 1MB
    $privateMiB = [double](($processes | Measure-Object -Property PrivateMemorySize64 -Sum).Sum) / 1MB
    $targetAfter = Get-ProcessNameCpuSnapshot -Name $ProcessName
    $ownedAfter = Get-CpuSnapshot -ProcessIds @(Get-TrackedOwnedProcessIds -Tracker $OwnershipTracker)
    $wallAfter = Get-Date
    $wallSeconds = [Math]::Max(0.001, ($wallAfter - $wallBefore).TotalSeconds)

    $targetCpuOneLogical = (Get-CpuDeltaSeconds $targetBefore $targetAfter) / $wallSeconds * 100.0
    $ownedCpuTotal = (Get-CpuDeltaSeconds $ownedBefore $ownedAfter) / $wallSeconds / [Environment]::ProcessorCount * 100.0
    $unrelatedCpu = [Math]::Max(0.0, (Get-TotalCpuPercent) - $ownedCpuTotal)

    $working.Add($workingMiB)
    $private.Add($privateMiB)
    $cpu.Add($targetCpuOneLogical)
    $unrelated.Add($unrelatedCpu)

    $targetBefore = $targetAfter
    $ownedBefore = $ownedAfter
    $wallBefore = $wallAfter
  }

  $unrelatedSummary = Get-Summary ([double[]]$unrelated.ToArray())
  if ([double]$unrelatedSummary.mean -gt $BackgroundCpuRejectPercent) {
    throw ("Target measurement rejected for {0} repetition {1}: sustained unrelated CPU mean {2:N2}% exceeded {3:N2}%." -f $ScenarioId, $Repetition, [double]$unrelatedSummary.mean, $BackgroundCpuRejectPercent)
  }

  return [ordered]@{
    scenario_id = $ScenarioId
    repetition = $Repetition
    live_tabs = $LiveTabs
    working_set_mib_samples = @($working)
    private_memory_mib_samples = @($private)
    cpu_one_logical_cpu_percent_samples = @($cpu)
    unrelated_cpu_total_percent_samples = @($unrelated)
    working_set = Get-Summary ([double[]]$working.ToArray())
    private_memory = Get-Summary ([double[]]$private.ToArray())
    cpu_one_logical_cpu_percent = Get-Summary ([double[]]$cpu.ToArray())
    unrelated_cpu_total_percent = $unrelatedSummary
  }
}

function Stop-OwnedProcessName {
  param([string]$Name)
  $owned = [System.Collections.Generic.HashSet[int]]::new()
  foreach ($id in @(Get-DescendantProcessIds -RootPid $PID)) {
    [void]$owned.Add([int]$id)
  }
  foreach ($p in @(Get-Process -Name $Name -ErrorAction SilentlyContinue)) {
    if ($owned.Contains($p.Id)) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
  }
  $deadline = (Get-Date).AddSeconds(15)
  while ((Get-Process -Name $Name -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 200
  }
  if (Get-Process -Name $Name -ErrorAction SilentlyContinue) {
    throw "Target measurement rejected: $Name process attribution/cleanup was lost."
  }
}

function Initialize-FirefoxBaselineProfile {
  param([string]$ProfilePath)

  New-Item -ItemType Directory -Path $ProfilePath -Force | Out-Null
  $prefs = @(
    'user_pref("browser.aboutwelcome.enabled", false);'
    'user_pref("browser.preonboarding.enabled", false);'
    'user_pref("browser.shell.checkDefaultBrowser", false);'
    'user_pref("browser.sessionstore.resume_from_crash", false);'
    'user_pref("browser.startup.homepage_override.mstone", "ignore");'
    'user_pref("browser.startup.page", 0);'
    'user_pref("startup.homepage_welcome_url", "about:blank");'
    'user_pref("startup.homepage_welcome_url.additional", "");'
    'user_pref("datareporting.policy.dataSubmissionPolicyBypassNotification", true);'
    'user_pref("termsofuse.bypassNotification", true);'
  )
  $userJs = Join-Path $ProfilePath "user.js"
  [System.IO.File]::WriteAllLines(
    $userJs,
    [string[]]$prefs,
    [System.Text.UTF8Encoding]::new($false)
  )

  $verified = Get-Content -LiteralPath $userJs -Raw
  foreach ($required in @(
    'browser.aboutwelcome.enabled'
    'browser.shell.checkDefaultBrowser'
    'browser.sessionstore.resume_from_crash'
    'termsofuse.bypassNotification'
  )) {
    if (-not $verified.Contains($required)) {
      throw "Firefox benchmark profile initialization is incomplete: $required"
    }
  }
}

function Invoke-FirefoxNoExtensionBaseline {
  param([int]$Repetition)
  if (Get-Process firefox -ErrorAction SilentlyContinue) {
    throw "Firefox no-extension baseline requires zero pre-existing Firefox processes."
  }
  $profile = Join-Path $work ("firefox-no-extension-" + $Repetition)
  Initialize-FirefoxBaselineProfile -ProfilePath $profile
  $root = Start-Process -FilePath $FirefoxPath -ArgumentList @("-profile", ('"' + $profile + '"'), "-no-remote", "about:blank") -PassThru
  $tracker = New-ProcessOwnershipTracker -Name "firefox" -RootPid $root.Id
  Update-ProcessOwnershipTracker -Tracker $tracker
  try {
    return Measure-ProcessGroup -ProcessName "firefox" -ScenarioId "FIREFOX_0_WORKERS_NO_EXTENSION" -Repetition $Repetition -LiveTabs 0 -OwnershipTracker $tracker
  } finally {
    Stop-TrackedProcessName -Tracker $tracker
  }
}

function Initialize-ChromeBenchmarkProfile {
  param([string]$ProfilePath)

  New-Item -ItemType Directory -Path $ProfilePath -Force | Out-Null
  $localStatePath = Join-Path $ProfilePath "Local State"
  $localState = [ordered]@{
    performance_tuning = [ordered]@{
      high_efficiency_mode = [ordered]@{
        state = 0
        enabled = $false
      }
    }
  }
  $json = $localState | ConvertTo-Json -Depth 10 -Compress
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($localStatePath, $json, $utf8NoBom)

  $verified = Get-Content -LiteralPath $localStatePath -Raw | ConvertFrom-Json
  if ([int]$verified.performance_tuning.high_efficiency_mode.state -ne 0) {
    throw "Chrome benchmark profile Memory Saver Local State is not disabled."
  }
}

function Invoke-ChromeReplicate {
  param([int]$Repetition)
  if (Get-Process chrome -ErrorAction SilentlyContinue) {
    throw "Chrome replicate requires zero pre-existing Chrome processes."
  }

  $profile = Join-Path $work ("chrome-profile-" + $Repetition)
  Initialize-ChromeBenchmarkProfile -ProfilePath $profile
  $profileArg = '--user-data-dir="' + $profile + '"'
  $baseArgs = @(
    $profileArg,
    "--no-first-run",
    "--disable-extensions",
    "--disable-default-apps",
    "--disable-background-networking"
  )

  $root = Start-Process -FilePath $ChromePath -ArgumentList @($baseArgs + @("about:blank")) -PassThru
  $tracker = New-ProcessOwnershipTracker -Name "chrome" -RootPid $root.Id
  Update-ProcessOwnershipTracker -Tracker $tracker
  try {
    $runs = [System.Collections.Generic.List[object]]::new()
    $runs.Add((Measure-ProcessGroup -ProcessName "chrome" -ScenarioId "CHROME_0_WORKERS" -Repetition $Repetition -LiveTabs 0 -OwnershipTracker $tracker))

    $opened = 0
    foreach ($targetCount in @(1, 2, 4)) {
      while ($opened -lt $targetCount) {
        $opened++
        $url = "http://127.0.0.1:8766/fake-worker.html?slot=$opened"
        $newRoot = Start-Process -FilePath $ChromePath -ArgumentList @($baseArgs + @($url)) -PassThru
        Add-ProcessOwnershipRoot -Tracker $tracker -RootPid $newRoot.Id
        Start-Sleep -Milliseconds 750
        Update-ProcessOwnershipTracker -Tracker $tracker
      }
      $runs.Add((Measure-ProcessGroup -ProcessName "chrome" -ScenarioId ("CHROME_" + $targetCount + "_WORKERS") -Repetition $Repetition -LiveTabs $targetCount -OwnershipTracker $tracker))
    }

    return [ordered]@{
      repetition = $Repetition
      resource_runs = @($runs)
    }
  } finally {
    Stop-TrackedProcessName -Tracker $tracker
  }
}

function Invoke-FirefoxReplicate {
  param(
    [int]$Repetition,
    [switch]$SkipLatency,
    [switch]$SkipColdStart
  )

  if (Get-Process firefox -ErrorAction SilentlyContinue) {
    throw "Firefox replicate requires zero pre-existing Firefox processes."
  }

  $repResult = Join-Path $work ("firefox-rep-" + $Repetition + ".json")
  $stdout = Join-Path $work ("firefox-rep-" + $Repetition + ".out.log")
  $stderr = Join-Path $work ("firefox-rep-" + $Repetition + ".err.log")
  $shellPath = (Get-Process -Id $PID).Path
  $args = @(
    "-NoProfile",
    "-File", ('"' + $targetFirefoxScript + '"'),
    "-RepositoryRoot", ('"' + $repo + '"'),
    "-ResultPath", ('"' + $repResult + '"'),
    "-FirefoxPath", ('"' + $FirefoxPath + '"'),
    "-FirefoxProfile", $FirefoxProfile
  )
  if ($SkipLatency) { $args += "-SkipLatency" }
  if ($SkipColdStart) { $args += "-SkipColdStart" }

  $child = Start-Process -FilePath $shellPath -ArgumentList $args -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  $noise = [System.Collections.Generic.List[double]]::new()
  $ownedBefore = Get-CpuSnapshot -ProcessIds @(Get-DescendantProcessIds -RootPid $PID)
  $wallBefore = Get-Date

  while (-not $child.HasExited) {
    Start-Sleep -Seconds 1
    Assert-NamedProcessesOwned -Name "firefox"
    $ownedAfter = Get-CpuSnapshot -ProcessIds @(Get-DescendantProcessIds -RootPid $PID)
    $wallAfter = Get-Date
    $wallSeconds = [Math]::Max(0.001, ($wallAfter - $wallBefore).TotalSeconds)
    $ownedCpuTotal = (Get-CpuDeltaSeconds $ownedBefore $ownedAfter) / $wallSeconds / [Environment]::ProcessorCount * 100.0
    $noise.Add([Math]::Max(0.0, (Get-TotalCpuPercent) - $ownedCpuTotal))
    $ownedBefore = $ownedAfter
    $wallBefore = $wallAfter
    $child.Refresh()
  }

  # Start-Process -PassThru can report HasExited before Windows has
  # finalized the live ExitCode property. Finalize the Process object before
  # evaluating success, otherwise a transient $null ExitCode compares as
  # non-zero and falsely rejects a successful Firefox replicate.
  $child.WaitForExit()
  $child.Refresh()

  $childExitCode = $null
  $exitCodeDeadline = (Get-Date).AddSeconds(5)
  while ($null -eq $childExitCode -and (Get-Date) -lt $exitCodeDeadline) {
    try {
      $child.Refresh()
      $childExitCode = $child.ExitCode
    } catch {
      $childExitCode = $null
    }
    if ($null -eq $childExitCode) {
      Start-Sleep -Milliseconds 100
    }
  }
  if ($null -eq $childExitCode) {
    throw "Firefox target replicate $Repetition exit code did not finalize."
  }

  if ([int]$childExitCode -ne 0) {
    $repEvidenceClass = $null
    $repStatus = $null
    if (Test-Path -LiteralPath $repResult -PathType Leaf) {
      try {
        $repDiagnostic = Get-Content -LiteralPath $repResult -Raw | ConvertFrom-Json
        $repEvidenceClass = [string]$repDiagnostic.evidence_class
        if ($repDiagnostic.PSObject.Properties.Name -contains "status") {
          $repStatus = [string]$repDiagnostic.status
        }
      } catch {
      }
    }
    $stdoutBytes = if (Test-Path -LiteralPath $stdout -PathType Leaf) { [long](Get-Item -LiteralPath $stdout).Length } else { 0 }
    $stderrBytes = if (Test-Path -LiteralPath $stderr -PathType Leaf) { [long](Get-Item -LiteralPath $stderr).Length } else { 0 }
    Write-Host ("STAGE09_FIREFOX_REPLICATE_FAILURE=" + ([ordered]@{
      repetition = $Repetition
      child_exit_code = [int]$childExitCode
      result_exists = (Test-Path -LiteralPath $repResult -PathType Leaf)
      result_evidence_class = $repEvidenceClass
      result_status = $repStatus
      stdout_bytes = $stdoutBytes
      stderr_bytes = $stderrBytes
    } | ConvertTo-Json -Depth 4 -Compress))
    if (Test-Path $stdout) { Get-Content $stdout }
    if (Test-Path $stderr) { Get-Content $stderr }
    if (Test-Path $repResult) { Get-Content $repResult }
    throw "Firefox target replicate $Repetition failed."
  }

  if (Get-Process firefox -ErrorAction SilentlyContinue) {
    throw "Firefox target replicate $Repetition left an unattributed process."
  }

  $noiseSummary = Get-Summary ([double[]]$noise.ToArray())
  if ([double]$noiseSummary.mean -gt $BackgroundCpuRejectPercent) {
    throw "Target measurement rejected: sustained unrelated CPU exceeded 20 percent during Firefox replicate $Repetition."
  }

  return [ordered]@{
    repetition = $Repetition
    unrelated_cpu_total_percent = $noiseSummary
    result = Get-Content -LiteralPath $repResult -Raw | ConvertFrom-Json
  }
}

function Get-FirefoxRun {
  param($Replicate, [string]$ScenarioId)
  return @($Replicate.result.steady_state.firefox_resource_runs | Where-Object { $_.ScenarioId -eq $ScenarioId })[0]
}

function Max-Value {
  param([object[]]$Values)
  return [double](($Values | Measure-Object -Maximum).Maximum)
}

function Min-Value {
  param([object[]]$Values)
  return [double](($Values | Measure-Object -Minimum).Minimum)
}

function New-BudgetCheck {
  param(
    [string]$Id,
    [double]$Actual,
    [string]$Operator,
    [double]$Limit
  )
  $pass = if ($Operator -eq "<=") { $Actual -le $Limit } else { $Actual -ge $Limit }
  return [ordered]@{
    id = $Id
    actual = $Actual
    operator = $Operator
    limit = $Limit
    pass_fail = $(if ($pass) { "PASS" } else { "FAIL" })
  }
}

try {
  New-Item -Path "HKCU:\Software\Mozilla\NativeMessagingHosts" -Force | Out-Null
  New-Item -Path $nativeRegPath -Force | Out-Null
  Set-Item -LiteralPath $nativeRegPath -Value $targetNativeManifest
  $nativeHostOverridden = $true

  $preflightPath = Join-Path $work "stage09-adapter-preflight.json"
  $preflightDiagnosticsDir = Join-Path $resultDir "stage09-preflight-diagnostics"
  if (Test-Path -LiteralPath $preflightDiagnosticsDir) {
    Remove-Item -LiteralPath $preflightDiagnosticsDir -Recurse -Force
  }
  & $targetFirefoxScript `
    -RepositoryRoot $repo `
    -ResultPath $preflightPath `
    -FirefoxPath $FirefoxPath `
    -FirefoxProfile $FirefoxProfile `
    -PreflightOnly `
    -DiagnosticsDirectory $preflightDiagnosticsDir
  if ($LASTEXITCODE -ne 0) {
    throw "Stage 09 performance-adapter identity preflight failed."
  }
  $preflight = Get-Content -LiteralPath $preflightPath -Raw | ConvertFrom-Json
  if ($preflight.evidence_class -ne "TARGET_ADAPTER_PREFLIGHT" -or
      $preflight.status -ne "PASS" -or
      $preflight.adapter_version -ne "0.1.9-perf") {
    throw "Stage 09 target refused a non-performance Firefox adapter."
  }

  if ($PreflightOnly) {
    $preflight | ConvertTo-Json -Depth 10 |
      Set-Content -LiteralPath $resultPathFull -Encoding UTF8
    Write-Host "STAGE09_TARGET_PREFLIGHT_ONLY=PASS"
    Get-Content -LiteralPath $resultPathFull
    return
  }

  Assert-BackgroundCpuQuiet -Seconds 10 -LimitPercent $BackgroundCpuRejectPercent

  $chromeFakeWorker = Start-Process -FilePath "python" -ArgumentList @(
    "-m", "http.server", "8766", "--bind", "127.0.0.1", "--directory", ('"' + $fakeWorkerRoot + '"')
  ) -PassThru -WindowStyle Hidden
  Start-Sleep -Seconds 1

  $firefoxReplicates = @{}
  $chromeReplicates = @{}
  $firefoxNoExtension = @{}

  for ($rep = 1; $rep -le $BrowserResourceRepetitions; $rep++) {
    foreach ($browser in $BrowserOrder[$rep - 1]) {
      if ($browser -eq "firefox") {
        $firefoxNoExtension[$rep] = Invoke-FirefoxNoExtensionBaseline -Repetition $rep
        $firefoxReplicates[$rep] = Invoke-FirefoxReplicate -Repetition $rep -SkipLatency:($rep -ne 1) -SkipColdStart:($rep -ne 1)
      } else {
        $chromeReplicates[$rep] = Invoke-ChromeReplicate -Repetition $rep
      }
    }
  }

  for ($rep = 4; $rep -le $DiscardRestoreRepetitions; $rep++) {
    $firefoxReplicates[$rep] = Invoke-FirefoxReplicate -Repetition $rep -SkipLatency -SkipColdStart
  }

  $full = $firefoxReplicates[1].result
  if ($null -eq $full.steady_state.latency -or $null -eq $full.steady_state.hotkey_queue_to_callback_proxy) {
    throw "Full Firefox replicate is missing exact latency evidence."
  }
  if ($null -eq $full.cold_start -or $full.cold_start.cold_firefox_start.count -ne $ColdStartRepetitions) {
    throw "Full Firefox replicate is missing the exact 10 cold-start trials."
  }

  $ffFirstThree = @(1..3 | ForEach-Object { $firefoxReplicates[$_] })
  $ffAllFive = @(1..5 | ForEach-Object { $firefoxReplicates[$_] })

  $helperWs = Max-Value @($ffFirstThree | ForEach-Object { [double]$_.result.steady_state.helper_idle.WorkingSet.P95 })
  $helperCpu = Max-Value @($ffFirstThree | ForEach-Object { [double]$_.result.steady_state.helper_idle.CpuOneLogicalCpuPercent.Mean })
  $ffTwoWs = Max-Value @($ffFirstThree | ForEach-Object { [double]((Get-FirefoxRun $_ "FIREFOX_2_WORKERS").WorkingSet.P95) })
  $ffFourWs = Max-Value @($ffFirstThree | ForEach-Object { [double]((Get-FirefoxRun $_ "FIREFOX_4_WORKERS").WorkingSet.P95) })
  $ffTwoCpu = Max-Value @($ffFirstThree | ForEach-Object { [double]((Get-FirefoxRun $_ "FIREFOX_2_WORKERS").CpuOneLogicalCpuPercent.Mean) })
  $discardMin = Min-Value @($ffAllFive | ForEach-Object { [double]$_.result.steady_state.discard_three_of_four_p95_reduction_percent })

  $extensionIncrementals = @()
  for ($rep = 1; $rep -le 3; $rep++) {
    $withExtension = [double](Get-FirefoxRun $firefoxReplicates[$rep] "FIREFOX_0_WORKERS").WorkingSet.P95
    $withoutExtension = [double]$firefoxNoExtension[$rep].working_set.p95
    $helper = [double]$firefoxReplicates[$rep].result.steady_state.helper_idle.WorkingSet.P95
    $extensionIncrementals += $helper + [Math]::Max(0.0, $withExtension - $withoutExtension)
  }
  $helperPlusExtension = Max-Value $extensionIncrementals

  $hotkey = $full.steady_state.hotkey_queue_to_callback_proxy
  if ($hotkey.Status -ne "PASS" -or $null -eq $hotkey.Latency) {
    throw "Target hotkey recognition metric is invalid."
  }
  $hotkeyMax = [double]$hotkey.Latency.Max
  $latency = $full.steady_state.latency
  $cold = $full.cold_start.cold_firefox_start.latency_ms

  $reuseP50Bound = [double]$latency.ReuseReady.P50 + $hotkeyMax
  $reuseP95Bound = [double]$latency.ReuseReady.P95 + $hotkeyMax
  $reuseHardBound = [double]$latency.ReuseReady.Max + $hotkeyMax
  $restoreP95Bound = [double]$latency.RestoreReady.P95 + $hotkeyMax
  $createP95Bound = [double]$latency.CreateReady.P95 + $hotkeyMax
  $coldP95Bound = [double]$cold.P95 + $hotkeyMax
  $noWorkP95Bound = [double]$latency.NoWork.P95 + $hotkeyMax

  $checks = @(
    (New-BudgetCheck "hotkey_recognition_p95_ms" ([double]$hotkey.Latency.P95) "<=" 50)
    (New-BudgetCheck "clipboard_write_p95_ms" ([double]$latency.ClipboardWrite.P95) "<=" 50)
    (New-BudgetCheck "existing_tab_activate_p95_ms" ([double]$latency.ExistingTabActivate.P95) "<=" 300)
    (New-BudgetCheck "reuse_ready_p50_composed_upper_bound_ms" $reuseP50Bound "<=" 250)
    (New-BudgetCheck "reuse_ready_p95_composed_upper_bound_ms" $reuseP95Bound "<=" 750)
    (New-BudgetCheck "reuse_ready_observed_max_composed_upper_bound_ms" $reuseHardBound "<=" 1500)
    (New-BudgetCheck "restore_ready_p95_composed_upper_bound_ms" $restoreP95Bound "<=" 2500)
    (New-BudgetCheck "create_ready_p95_composed_upper_bound_ms" $createP95Bound "<=" 2000)
    (New-BudgetCheck "cold_start_p95_composed_upper_bound_ms" $coldP95Bound "<=" 8000)
    (New-BudgetCheck "no_work_p95_composed_upper_bound_ms" $noWorkP95Bound "<=" 250)
    (New-BudgetCheck "native_helper_working_set_mib_p95" $helperWs "<=" 100)
    (New-BudgetCheck "native_helper_plus_extension_incremental_mib_p95" $helperPlusExtension "<=" 150)
    (New-BudgetCheck "helper_idle_cpu_percent_one_logical_cpu_mean" $helperCpu "<=" 1)
    (New-BudgetCheck "firefox_two_live_worker_tabs_working_set_mib_p95" $ffTwoWs "<=" 1536)
    (New-BudgetCheck "firefox_four_live_worker_tabs_working_set_mib_p95" $ffFourWs "<=" 2560)
    (New-BudgetCheck "firefox_two_live_idle_tabs_cpu_percent_one_logical_cpu_mean" $ffTwoCpu "<=" 5)
    (New-BudgetCheck "discard_three_of_four_tabs_working_set_reduction_percent" $discardMin ">=" 25)
  )

  $allPass = (@($checks | Where-Object { $_.pass_fail -ne "PASS" }).Count -eq 0)

  $chromeTwo = Max-Value @(1..3 | ForEach-Object {
    [double](@($chromeReplicates[$_].resource_runs | Where-Object { $_.scenario_id -eq "CHROME_2_WORKERS" })[0].working_set.p95)
  })
  $firefoxToChromeTwoRatio = if ($chromeTwo -gt 0) { $ffTwoWs / $chromeTwo } else { $null }

  $os = Get-CimInstance Win32_OperatingSystem
  $cpuInfo = Get-CimInstance Win32_Processor | Select-Object -First 1
  $computer = Get-CimInstance Win32_ComputerSystem
  $descriptor = "$($os.Version)|$($os.BuildNumber)|$($cpuInfo.Name)|$($computer.TotalPhysicalMemory)"
  $hashBytes = [System.Security.Cryptography.SHA256]::HashData([System.Text.Encoding]::UTF8.GetBytes($descriptor))
  $machineFingerprint = [Convert]::ToHexString($hashBytes).ToLowerInvariant()
  $powerMode = ((& powercfg /GETACTIVESCHEME 2>$null) -join " ").Trim()
  $firefoxVersion = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($FirefoxPath).FileVersion
  $chromeVersion = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($ChromePath).FileVersion

  $evidence = [ordered]@{
    schema_version = 1
    stage = "impl_09_performance_benchmark_execution"
    evidence_class = "TARGET_WINDOWS_OPERATOR_WORKSTATION"
    source_sha = $sourceSha
    target_contract_complete = $true
    environment = [ordered]@{
      machine_fingerprint = $machineFingerprint
      os_build = "$($os.Version).$($os.BuildNumber)"
      power_mode = $powerMode
      firefox_version = $firefoxVersion
      chrome_version = $chromeVersion
      chrome_memory_saver_disabled = $true
      same_name_process_isolation_valid = $true
      background_noise_valid = $true
    }
    measurement = [ordered]@{
      warmup_seconds = $WarmupSeconds
      steady_state_seconds = $SteadySeconds
      sample_rate_hz = $SampleRateHz
      browser_order_alternated = $true
    }
    repetitions = [ordered]@{
      browser_resource = $BrowserResourceRepetitions
      discard_restore = $DiscardRestoreRepetitions
      reuse = $ReuseRepetitions
      restore = $RestoreRepetitions
      create = $CreateRepetitions
      cold_start = $ColdStartRepetitions
      local_primitives = $PrimitiveRepetitions
    }
    results = [ordered]@{
      firefox = [ordered]@{
        resource_replicates = @(1..3 | ForEach-Object { $firefoxReplicates[$_] })
        no_extension_baselines = @(1..3 | ForEach-Object { $firefoxNoExtension[$_] })
        discard_restore_replicates = @(1..5 | ForEach-Object {
          [ordered]@{
            repetition = $_
            reduction_percent = [double]$firefoxReplicates[$_].result.steady_state.discard_three_of_four_p95_reduction_percent
          }
        })
      }
      chrome = [ordered]@{
        memory_saver_control = [ordered]@{
          method = "fresh-user-data-local-state"
          pref = "performance_tuning.high_efficiency_mode.state"
          disabled_value = 0
        }
        resource_replicates = @(1..3 | ForEach-Object { $chromeReplicates[$_] })
        comparison_to_firefox = [ordered]@{
          firefox_two_worker_p95_mib = $ffTwoWs
          chrome_two_worker_p95_mib = $chromeTwo
          firefox_to_chrome_two_worker_p95_ratio = $firefoxToChromeTwoRatio
        }
      }
      latency = [ordered]@{
        hotkey_queue_to_callback = $hotkey
        dispatch = $latency
        cold_start = $full.cold_start
        composed_upper_bounds = [ordered]@{
          reuse_p50_ms = $reuseP50Bound
          reuse_p95_ms = $reuseP95Bound
          reuse_observed_max_ms = $reuseHardBound
          restore_p95_ms = $restoreP95Bound
          create_p95_ms = $createP95Bound
          cold_start_p95_ms = $coldP95Bound
          no_work_p95_ms = $noWorkP95Bound
          method = "dispatch statistic plus observed maximum WM_HOTKEY queue-to-callback latency; conservative upper bound"
        }
      }
      budget_evaluation = [ordered]@{
        all_pass = $allPass
        checks = $checks
      }
    }
    security = [ordered]@{
      dom_or_page_content_collected = $false
      raw_urls_collected = $false
      screenshots_collected = $false
      credentials_or_tokens_collected = $false
      synthetic_paste_enter_send_or_mouse = $false
    }
    blockers = @()
  }

  $evidence | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $resultPathFull -Encoding UTF8
  & python $validator $resultPathFull
  if ($LASTEXITCODE -ne 0) {
    throw "Stage 09 target evidence failed local schema/contract validation."
  }

  if ($allPass) {
    Write-Host "STAGE09_TARGET_MATRIX=PASS"
  } else {
    Write-Host "STAGE09_TARGET_MATRIX=BUDGET_FAILURE"
  }
  Get-Content -LiteralPath $resultPathFull

  if (-not $allPass) {
    throw "Stage 09 target matrix completed but one or more frozen budgets failed."
  }
}
finally {
  if ($chromeFakeWorker -and -not $chromeFakeWorker.HasExited) {
    Stop-Process -Id $chromeFakeWorker.Id -Force -ErrorAction SilentlyContinue
  }
  try { Stop-OwnedProcessName -Name "chrome" } catch {}
  try { Stop-OwnedProcessName -Name "firefox" } catch {}
  if ($nativeHostOverridden) {
    if ($nativeRegExisted) {
      Set-Item -LiteralPath $nativeRegPath -Value $originalNativeHostPath
    } else {
      Remove-Item -LiteralPath $nativeRegPath -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
  Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
