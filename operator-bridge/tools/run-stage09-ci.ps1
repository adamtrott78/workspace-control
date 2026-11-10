param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,
  [Parameter(Mandatory = $true)]
  [string]$ResultPath
)

$ErrorActionPreference = "Stop"

$bridgeRoot = Join-Path $RepositoryRoot "operator-bridge"
$runnerDll = Join-Path $bridgeRoot "performance/bin/Release/net10.0-windows/WorkspaceOperator.PerformanceHarness.dll"
$helperExe = Join-Path $bridgeRoot "src/WorkspaceOperator/bin/Release/net10.0-windows/WorkspaceOperator.exe"

if (-not (Test-Path $runnerDll)) {
  throw "Stage 09 performance harness is missing: $runnerDll"
}
if (-not (Test-Path $helperExe)) {
  throw "WorkspaceOperator helper is missing: $helperExe"
}

$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"
if (-not (Test-Path $firefox)) {
  $installer = Join-Path $env:RUNNER_TEMP "firefox-esr-installer.exe"
  & curl.exe -L --fail --silent --show-error "https://download.mozilla.org/?product=firefox-esr-latest&os=win64&lang=en-US" -o $installer
  if ($LASTEXITCODE -ne 0) {
    throw "Firefox ESR download failed."
  }
  $install = Start-Process -FilePath $installer -ArgumentList "/S" -PassThru -Wait
  if ($install.ExitCode -ne 0) {
    throw "Firefox ESR install failed."
  }
}

if (Get-Process firefox -ErrorAction SilentlyContinue) {
  throw "Stage 09 CI smoke requires no pre-existing Firefox process."
}

$work = Join-Path $env:RUNNER_TEMP ("workspace-operator-stage09-" + [Guid]::NewGuid().ToString("N"))
New-Item $work -ItemType Directory -Force | Out-Null

$extensionSource = Join-Path $bridgeRoot "performance/FirefoxProfile/extension"
$extensionStage = Join-Path $work "extension"
Copy-Item $extensionSource $extensionStage -Recurse
Copy-Item (Join-Path $bridgeRoot "src/FirefoxAdapter/adapter_core.js") (Join-Path $extensionStage "adapter_core.js")
Copy-Item (Join-Path $bridgeRoot "simulator/FirefoxProfile/extension/fake-worker.html") (Join-Path $extensionStage "fake-worker.html")

$webExtRoot = Join-Path $work "web-ext-tool"
New-Item $webExtRoot -ItemType Directory | Out-Null
Push-Location $webExtRoot
try {
  & npm.cmd init -y | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "npm init failed." }
  & npm.cmd install --no-audit --no-fund --save-exact web-ext@10.8.0
  if ($LASTEXITCODE -ne 0) { throw "Pinned web-ext install failed." }
}
finally {
  Pop-Location
}
$webExt = Join-Path $webExtRoot "node_modules\.bin\web-ext.cmd"

$nativeManifest = Join-Path $work "native-host.json"
[ordered]@{
  name = "com.workspacecontrol.operator_bridge"
  description = "Workspace Control Operator Stage 09 Native Host"
  path = $helperExe
  type = "stdio"
  allowed_extensions = @("workspace-control-operator@adamtrott78.local")
} | ConvertTo-Json -Depth 5 | Set-Content $nativeManifest -Encoding UTF8

$regPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
if (Test-Path $regPath) {
  throw "Stage 09 CI smoke refuses to overwrite a pre-existing native-host key."
}
New-Item -Path $regPath -Force | Out-Null
Set-Item -Path $regPath -Value $nativeManifest

$readyFile = Join-Path $work "server.ready"
$runnerOut = Join-Path $work "runner.out.log"
$runnerErr = Join-Path $work "runner.err.log"
$webExtOut = Join-Path $work "web-ext.out.log"
$webExtErr = Join-Path $work "web-ext.err.log"
$fakeWorkerOut = Join-Path $work "fake-worker.out.log"
$fakeWorkerErr = Join-Path $work "fake-worker.err.log"

$runner = $null
$webExtProcess = $null
$fakeWorkerProcess = $null

try {
  $fakeWorkerProcess = Start-Process -FilePath "python" -ArgumentList @(
    "-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", $extensionStage
  ) -RedirectStandardOutput $fakeWorkerOut -RedirectStandardError $fakeWorkerErr -PassThru

  $runner = Start-Process -FilePath "dotnet" -ArgumentList @(
    $runnerDll,
    "--result=$ResultPath",
    "--helper=$helperExe",
    "--ready-file=$readyFile",
    "--mode=ci",
    "--warmup-ms=250",
    "--sample-ms=1200",
    "--sample-interval-ms=200",
    "--latency-scale=10",
    "--timeout-seconds=90"
  ) -RedirectStandardOutput $runnerOut -RedirectStandardError $runnerErr -PassThru

  $readyDeadline = (Get-Date).AddSeconds(20)
  while (-not (Test-Path $readyFile) -and (Get-Date) -lt $readyDeadline) {
    if ($runner.HasExited) { break }
    Start-Sleep -Milliseconds 100
  }
  if (-not (Test-Path $readyFile)) {
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    throw "Stage 09 harness did not become ready."
  }

  $webExtLauncher = Join-Path $work "run-web-ext.cmd"
  @"
@echo off
call "$webExt" run --source-dir "$extensionStage" --firefox "$firefox" --no-reload --no-input --arg=-headless --arg=-no-remote
"@ | Set-Content -Path $webExtLauncher -Encoding ASCII

  $webExtProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/d", "/c", $webExtLauncher
  ) -RedirectStandardOutput $webExtOut -RedirectStandardError $webExtErr -PassThru

  if (-not $runner.WaitForExit(180000)) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
    throw "Stage 09 CI performance harness timed out."
  }

  if ($runner.ExitCode -ne 0) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    if (Test-Path $webExtOut) { Get-Content $webExtOut }
    if (Test-Path $webExtErr) { Get-Content $webExtErr }
    if (Test-Path $ResultPath) { Get-Content $ResultPath }
    throw "Stage 09 CI performance harness failed."
  }

  $result = Get-Content $ResultPath -Raw | ConvertFrom-Json
  if ($result.evidence_class -ne "GITHUB_HOSTED_WINDOWS_CI") {
    throw "Stage 09 CI result evidence class is invalid."
  }
  if ($result.target_contract_complete -ne $false) {
    throw "CI evidence must never claim target-contract completion."
  }
  if ($result.content_policy -ne "CONTENT_FREE") {
    throw "Stage 09 CI result must remain content-free."
  }

  Write-Host "STAGE09_CI_PERFORMANCE_SMOKE=PASS"
  Get-Content $ResultPath
}
finally {
  if ($fakeWorkerProcess -and -not $fakeWorkerProcess.HasExited) {
    Stop-Process -Id $fakeWorkerProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($webExtProcess -and -not $webExtProcess.HasExited) {
    Stop-Process -Id $webExtProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($runner -and -not $runner.HasExited) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
  }
  Get-Process firefox -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Remove-Item $regPath -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
}
