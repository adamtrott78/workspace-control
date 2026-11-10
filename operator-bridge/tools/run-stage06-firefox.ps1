param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,
  [Parameter(Mandatory = $true)]
  [string]$ResultPath
)

$ErrorActionPreference = "Stop"

$bridgeRoot = Join-Path $RepositoryRoot "operator-bridge"
$runnerDll = Join-Path $bridgeRoot "integration/bin/Release/net10.0-windows/WorkspaceOperator.IntegrationHarness.dll"
$helperExe = Join-Path $bridgeRoot "src/WorkspaceOperator/bin/Release/net10.0-windows/WorkspaceOperator.exe"

if (-not (Test-Path $runnerDll)) {
  throw "Stage 06 integration runner is missing: $runnerDll"
}
if (-not (Test-Path $helperExe)) {
  throw "WorkspaceOperator helper is missing: $helperExe"
}

$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"
if (-not (Test-Path $firefox)) {
  $installer = Join-Path $env:RUNNER_TEMP "firefox-esr-installer.exe"
  Write-Host "Downloading current Firefox ESR from Mozilla."
  & curl.exe -L --fail --silent --show-error "https://download.mozilla.org/?product=firefox-esr-latest&os=win64&lang=en-US" -o $installer
  if ($LASTEXITCODE -ne 0) {
    throw "Firefox ESR download failed."
  }
  $install = Start-Process -FilePath $installer -ArgumentList "/S" -PassThru -Wait
  if ($install.ExitCode -ne 0) {
    throw "Firefox ESR silent install failed with exit code $($install.ExitCode)."
  }
}

$version = (& $firefox --version 2>&1 | Out-String).Trim()
Write-Host "STAGE06_FIREFOX_VERSION=$version"

$work = Join-Path $env:RUNNER_TEMP "workspace-operator-stage06"
if (Test-Path $work) {
  Remove-Item $work -Recurse -Force
}
New-Item $work -ItemType Directory | Out-Null

$extensionSource = Join-Path $bridgeRoot "simulator/FirefoxProfile/extension"
$extensionStage = Join-Path $work "extension"
Copy-Item $extensionSource $extensionStage -Recurse
Copy-Item (Join-Path $bridgeRoot "src/FirefoxAdapter/adapter_core.js") (Join-Path $extensionStage "adapter_core.js")

$webExtRoot = Join-Path $work "web-ext-tool"
New-Item $webExtRoot -ItemType Directory | Out-Null
Push-Location $webExtRoot
try {
  & npm.cmd init -y | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "npm init failed for the Stage 06 test-only web-ext tool."
  }
  & npm.cmd install --no-audit --no-fund --save-exact web-ext@10.8.0
  if ($LASTEXITCODE -ne 0) {
    throw "Pinned web-ext@10.8.0 installation failed."
  }
}
finally {
  Pop-Location
}
$webExt = Join-Path $webExtRoot "node_modules\.bin\web-ext.cmd"
if (-not (Test-Path $webExt)) {
  throw "Pinned web-ext executable was not installed."
}
Write-Host "STAGE06_WEB_EXT_VERSION=10.8.0"

$nativeManifest = Join-Path $work "native-host.json"
$manifestObject = [ordered]@{
  name = "com.workspacecontrol.operator_bridge"
  description = "Workspace Control Operator Stage 06 Native Host"
  path = $helperExe
  type = "stdio"
  allowed_extensions = @("workspace-control-operator@adamtrott78.local")
}
$manifestObject | ConvertTo-Json -Depth 5 | Set-Content $nativeManifest -Encoding UTF8

$regPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
New-Item -Path $regPath -Force | Out-Null
Set-Item -Path $regPath -Value $nativeManifest

$runnerOut = Join-Path $work "runner.out.log"
$runnerErr = Join-Path $work "runner.err.log"
$webExtOut = Join-Path $work "web-ext.out.log"
$webExtErr = Join-Path $work "web-ext.err.log"
$runner = $null
$webExtProcess = $null

try {
  $runnerArgs = @(
    $runnerDll,
    "--result=$ResultPath",
    "--timeout-seconds=75"
  )
  $runner = Start-Process -FilePath "dotnet" -ArgumentList $runnerArgs -RedirectStandardOutput $runnerOut -RedirectStandardError $runnerErr -PassThru

  Start-Sleep -Seconds 2

  $webExtArgs = @(
    "run",
    "--source-dir=$extensionStage",
    "--firefox=\`"$firefox\`"",
    "--no-reload",
    "--no-input",
    "--arg=-headless",
    "--arg=-no-remote"
  )
  Write-Host ("STAGE06_WEB_EXT_ARGS=" + ($webExtArgs -join " "))
  $webExtProcess = Start-Process -FilePath $webExt -ArgumentList $webExtArgs -RedirectStandardOutput $webExtOut -RedirectStandardError $webExtErr -PassThru

  if (-not $runner.WaitForExit(90000)) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
    throw "Stage 06 Firefox integration runner timed out."
  }

  if ($runner.ExitCode -ne 0) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    if (Test-Path $webExtOut) { Get-Content $webExtOut }
    if (Test-Path $webExtErr) { Get-Content $webExtErr }
    if (Test-Path $ResultPath) { Get-Content $ResultPath }
    throw "Stage 06 Firefox integration runner failed with exit code $($runner.ExitCode)."
  }

  $result = Get-Content $ResultPath -Raw | ConvertFrom-Json
  if ($result.result -ne "PASS") {
    Get-Content $ResultPath
    throw "Stage 06 Firefox integration result was not PASS."
  }

  Write-Host "STAGE06_FIREFOX_INTEGRATION=PASS"
  Get-Content $ResultPath
}
finally {
  if ($webExtProcess -and -not $webExtProcess.HasExited) {
    Stop-Process -Id $webExtProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($runner -and -not $runner.HasExited) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
  }
  Remove-Item $regPath -Recurse -Force -ErrorAction SilentlyContinue
}
