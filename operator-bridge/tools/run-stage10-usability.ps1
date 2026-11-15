param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,
  [Parameter(Mandatory = $true)]
  [ValidateSet("UT-11", "UT-01", "UT-02", "UT-03", "UT-04", "UT-05", "UT-06", "UT-07", "UT-08", "UT-10", "UT-12")]
  [string]$TrialId,
  [string]$ResultPath,
  [int]$DurationSeconds = 900,
  [string]$SchedulerHotkey = "Ctrl+Space"
)

$ErrorActionPreference = "Stop"

$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$bridgeRoot = Join-Path $repo "operator-bridge"
$sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch '^[0-9a-f]{40}$') {
  throw "Stage 10 usability trial requires an exact Git source SHA."
}
$cacheRoot = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Stage10"
$buildTree = @(git -C $repo ls-tree -r HEAD -- `
  "operator-bridge/integration" `
  "operator-bridge/src" `
  "operator-bridge/simulator" `
  "operator-bridge/WorkspaceOperatorBridge.Integration.slnx") -join "`n"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($buildTree)) {
  throw "Stage 10 usability trial could not derive the build fingerprint."
}
$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
  $buildFingerprintBytes = [System.Text.Encoding]::UTF8.GetBytes($buildTree)
  $buildFingerprintHash = $sha256.ComputeHash($buildFingerprintBytes)
  $buildFingerprint = ([System.BitConverter]::ToString($buildFingerprintHash)).Replace("-", "").ToLowerInvariant()
}
finally {
  $sha256.Dispose()
}
$buildCache = Join-Path $cacheRoot ("build\" + $buildFingerprint)
$runnerDll = Join-Path $buildCache "integration\WorkspaceOperator.IntegrationHarness.dll"
$helperExe = Join-Path $buildCache "helper\WorkspaceOperator.exe"
$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"
New-Item $cacheRoot -ItemType Directory -Force | Out-Null

if (-not $ResultPath) {
  $ResultPath = Join-Path $repo ("benchmarks\workspace-semantic-execution\operator_bridge\stage10-" + $TrialId.ToLowerInvariant() + "-result.json")
}
$ResultPath = [System.IO.Path]::GetFullPath($ResultPath)
$readyPath = $ResultPath + ".ready.json"

if (Get-Process firefox -ErrorAction SilentlyContinue) {
  throw "Stage 10 usability trial requires no pre-existing Firefox process."
}
if (Get-Process WorkspaceOperator -ErrorAction SilentlyContinue) {
  throw "Stage 10 usability trial requires no pre-existing WorkspaceOperator process."
}
if (-not (Test-Path $firefox)) {
  throw "Stage 10 usability trial requires Firefox to be installed at $firefox."
}

$buildCacheHit = (Test-Path $runnerDll) -and (Test-Path $helperExe)
if (-not $buildCacheHit) {
  $buildStage = Join-Path $cacheRoot ("build-staging-" + [guid]::NewGuid().ToString("N"))
  try {
    dotnet build (Join-Path $bridgeRoot "WorkspaceOperatorBridge.Integration.slnx") --configuration Release
    if ($LASTEXITCODE -ne 0) {
      throw "Stage 10 integration build failed."
    }

    New-Item $buildStage -ItemType Directory -Force | Out-Null
    Copy-Item `
      (Join-Path $bridgeRoot "integration\bin\Release\net10.0-windows") `
      (Join-Path $buildStage "integration") `
      -Recurse
    Copy-Item `
      (Join-Path $bridgeRoot "src\WorkspaceOperator\bin\Release\net10.0-windows") `
      (Join-Path $buildStage "helper") `
      -Recurse

    if (-not (Test-Path (Join-Path $buildStage "integration\WorkspaceOperator.IntegrationHarness.dll"))) {
      throw "Stage 10 build cache staging is missing the integration harness."
    }
    if (-not (Test-Path (Join-Path $buildStage "helper\WorkspaceOperator.exe"))) {
      throw "Stage 10 build cache staging is missing the native helper."
    }

    New-Item (Split-Path -Parent $buildCache) -ItemType Directory -Force | Out-Null
    Remove-Item $buildCache -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item $buildStage $buildCache
  }
  finally {
    if ($buildStage -and (Test-Path $buildStage)) {
      Remove-Item $buildStage -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}
Write-Host ("STAGE10_BUILD_CACHE=" + $(if ($buildCacheHit) { "HIT" } else { "MISS" }) + " source_sha=" + $sourceSha + " build_fingerprint=" + $buildFingerprint)

$work = Join-Path $env:TEMP ("workspace-operator-stage10-" + [guid]::NewGuid().ToString("N"))
New-Item $work -ItemType Directory -Force | Out-Null
$extensionStage = Join-Path $work "extension"
Copy-Item (Join-Path $bridgeRoot "usability\FirefoxProfile\extension") $extensionStage -Recurse
Copy-Item (Join-Path $bridgeRoot "src\FirefoxAdapter\adapter_core.js") (Join-Path $extensionStage "adapter_core.js")

$webExtRoot = Join-Path $cacheRoot "web-ext-10.8.0"
$webExt = Join-Path $webExtRoot "node_modules\.bin\web-ext.cmd"
$webExtPackage = Join-Path $webExtRoot "node_modules\web-ext\package.json"
$webExtCacheHit = $false
if ((Test-Path $webExt) -and (Test-Path $webExtPackage)) {
  try {
    $webExtMetadata = Get-Content $webExtPackage -Raw | ConvertFrom-Json
    $webExtCacheHit = $webExtMetadata.version -eq "10.8.0"
  }
  catch {
    $webExtCacheHit = $false
  }
}

if (-not $webExtCacheHit) {
  $webExtStage = Join-Path $cacheRoot ("web-ext-staging-" + [guid]::NewGuid().ToString("N"))
  try {
    New-Item $webExtStage -ItemType Directory -Force | Out-Null
    '{"private":true}' | Set-Content (Join-Path $webExtStage "package.json") -Encoding ASCII

    $npmProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @(
      "/d",
      "/c",
      "npm.cmd install --no-audit --no-fund --prefer-offline --save-exact web-ext@10.8.0"
    ) -WorkingDirectory $webExtStage -NoNewWindow -PassThru
    if (-not $npmProcess.WaitForExit(120000)) {
      Stop-Process -Id $npmProcess.Id -Force -ErrorAction SilentlyContinue
      throw "Pinned web-ext@10.8.0 install exceeded the 120-second bootstrap bound."
    }
    # Process.ExitCode is unreliable for this cmd.exe child on the Windows
    # self-hosted runner. The bounded process completion above establishes
    # termination; the pinned artifact/version checks below establish success.
    $stagedPackage = Join-Path $webExtStage "node_modules\web-ext\package.json"
    $stagedBinary = Join-Path $webExtStage "node_modules\.bin\web-ext.cmd"
    if (-not (Test-Path $stagedPackage) -or -not (Test-Path $stagedBinary)) {
      throw "Pinned web-ext cache staging is incomplete."
    }
    $stagedMetadata = Get-Content $stagedPackage -Raw | ConvertFrom-Json
    if ($stagedMetadata.version -ne "10.8.0") {
      throw "Pinned web-ext cache staging resolved an unexpected version."
    }

    Remove-Item $webExtRoot -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item $webExtStage $webExtRoot
  }
  finally {
    if ($webExtStage -and (Test-Path $webExtStage)) {
      Remove-Item $webExtStage -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}
Write-Host ("STAGE10_WEB_EXT_CACHE=" + $(if ($webExtCacheHit) { "HIT" } else { "MISS" }) + " version=10.8.0")

$nativeManifest = Join-Path $work "native-host.json"
[ordered]@{
  name = "com.workspacecontrol.operator_bridge"
  description = "Workspace Control Stage 10 usability native host"
  path = $helperExe
  type = "stdio"
  allowed_extensions = @("workspace-control-operator@adamtrott78.local")
} | ConvertTo-Json -Depth 5 | Set-Content $nativeManifest -Encoding UTF8

$regPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
$regExisted = Test-Path $regPath
$oldValue = if ($regExisted) { (Get-Item -LiteralPath $regPath).GetValue("") } else { $null }

New-Item $regPath -Force | Out-Null
Set-Item -LiteralPath $regPath -Value $nativeManifest

$runnerOut = Join-Path $work "runner.out.log"
$runnerErr = Join-Path $work "runner.err.log"
$webExtOut = Join-Path $work "web-ext.out.log"
$webExtErr = Join-Path $work "web-ext.err.log"
$runner = $null
$webExtProcess = $null

try {
  Remove-Item $ResultPath -Force -ErrorAction SilentlyContinue
  Remove-Item $readyPath -Force -ErrorAction SilentlyContinue

  $runner = Start-Process -FilePath "dotnet" -ArgumentList @(
    $runnerDll,
    "--usability-trial=$TrialId",
    "--result=$ResultPath",
    "--ready=$readyPath",
    "--duration-seconds=$DurationSeconds",
    "--scheduler-hotkey=$SchedulerHotkey"
  ) -RedirectStandardOutput $runnerOut -RedirectStandardError $runnerErr -PassThru

  Start-Sleep -Seconds 1
  if ($runner.HasExited) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    throw "Stage 10 usability harness exited during startup."
  }

  $launcher = Join-Path $work "run-web-ext.cmd"
  @"
@echo off
call "$webExt" run --source-dir "$extensionStage" --firefox "$firefox" --no-reload --no-input --arg=-no-remote
"@ | Set-Content $launcher -Encoding ASCII

  $webExtProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/d", "/c", $launcher
  ) -RedirectStandardOutput $webExtOut -RedirectStandardError $webExtErr -PassThru

  $deadline = (Get-Date).AddSeconds(100)
  while (-not (Test-Path $readyPath) -and (Get-Date) -lt $deadline) {
    if ($runner.HasExited) { break }
    Start-Sleep -Milliseconds 250
  }

  if (-not (Test-Path $readyPath)) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    if (Test-Path $webExtOut) { Get-Content $webExtOut }
    if (Test-Path $webExtErr) { Get-Content $webExtErr }
    throw "Stage 10 usability harness never reached ready state."
  }

  Write-Host "STAGE10_USABILITY_READY=$TrialId"
  if ($TrialId -eq "UT-11") {
    Write-Host "Bridge is OFF. Use $SchedulerHotkey normally in representative foreground applications for the configured duration. The bridge must not react."
  } elseif ($TrialId -eq "UT-02") {
    Write-Host "UT-02 mixed batch is ready. Repeat: press $SchedulerHotkey, then Ctrl+V, then Enter whenever a worker is focused. Local-only retire/discard actions are drained transparently by the same scheduler press. Do not manually choose or search browser tabs."
  } elseif ($TrialId -eq "UT-03") {
    Write-Host "UT-03 interruption trial is ready. Complete six normal service cycles. After each of the first five durable acknowledgments, follow the tray interruption prompt: switch to another normal app for 30-60 seconds or take a short idle, then return and resume only with $SchedulerHotkey. Do not search worker tabs or reconstruct scheduler state."
  } elseif ($TrialId -eq "UT-04") {
    Write-Host "UT-04 multiple SENT/UNCONFIRMED trial is ready. The tray starts with two independent sent/unconfirmed workers while four new service actions are ready. Complete four normal $SchedulerHotkey -> Ctrl+V -> Enter cycles. Do not choose, revisit, or resolve the prior unconfirmed workers; the simulator will deliver their late durable acknowledgments after the ready work is complete."
  } elseif ($TrialId -eq "UT-05") {
    Write-Host "UT-05 judgment-gate trial is ready. Press $SchedulerHotkey once. A distinct bounded judgment surface must open for exact gate ut05-judgment-01 without preparing a worker or changing the clipboard. Choose Yes to record the simulator-authority judgment, then complete one normal $SchedulerHotkey -> Ctrl+V -> Enter worker cycle."
  } elseif ($TrialId -eq "UT-06") {
    Write-Host "UT-06 managed-tab-loss recovery is ready. Press $SchedulerHotkey once; use only the explicit recovery surface and click OK. Do not search Firefox tabs or reconstruct state. After the tray shows one ready cycle, complete exactly one normal $SchedulerHotkey -> Ctrl+V -> Enter cycle."
  } elseif ($TrialId -eq "UT-07") {
    Write-Host "UT-07 profile-wide auth-refresh recovery is ready. Press $SchedulerHotkey once; click OK on the recovery surface, then click OK on the simulated manual-auth-return boundary. The fake-worker trial performs no credential automation. Do not inspect worker tabs. Then complete exactly one normal $SchedulerHotkey -> Ctrl+V -> Enter cycle."
  } elseif ($TrialId -eq "UT-08") {
    Write-Host "UT-08 cold-restart recovery is ready. The recovery incident has been rehydrated from durable simulator state. Press $SchedulerHotkey once and click OK on the explicit recovery surface; do not inspect tabs or replay the old packet. Then complete exactly one normal $SchedulerHotkey -> Ctrl+V -> Enter cycle."
  } elseif ($TrialId -eq "UT-12") {
    Write-Host "UT-12 no-work/background-ack trial is ready. One fake worker is already SENT/UNCONFIRMED and there is no READY action. Press $SchedulerHotkey once; the accepted READY=0 behavior may minimize only WorkspaceWorkers Firefox. Then switch to another normal app and leave it foreground. After about 3 seconds the simulator will apply the durable ack in the background. Do not paste or press Enter; verify no focus steal or clipboard disruption."
  } else {
    Write-Host "For each cycle: press $SchedulerHotkey, then Ctrl+V, then Enter. Do not manually choose or search browser tabs."
  }

  if (-not $runner.WaitForExit(1800000)) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
    throw "Stage 10 usability trial exceeded the 30-minute bounded execution window."
  }

  if (-not (Test-Path $ResultPath)) {
    throw "Stage 10 usability trial produced no structured result."
  }

  $resultObject = Get-Content $ResultPath -Raw | ConvertFrom-Json
  Get-Content $ResultPath
  if ($resultObject.result -ne "OBJECTIVE_PASS") {
    throw "Stage 10 usability harness reported objective failure."
  }
  if ($runner.ExitCode -ne 0) {
    Write-Warning ("Stage 10 harness process exit code was " + $runner.ExitCode +
      " despite structured OBJECTIVE_PASS; structured result is authoritative.")
  }
}
finally {
  if ($webExtProcess -and -not $webExtProcess.HasExited) {
    Stop-Process -Id $webExtProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($runner -and -not $runner.HasExited) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
  }

  if ($regExisted) {
    Set-Item -LiteralPath $regPath -Value $oldValue
  } else {
    Remove-Item -LiteralPath $regPath -Recurse -Force -ErrorAction SilentlyContinue
  }

  Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
}
