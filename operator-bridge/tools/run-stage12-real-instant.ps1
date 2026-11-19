[CmdletBinding()]
param(
  [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
  [string]$OperatorBridgeUrl = "https://gokhan-lambda-vector.tailca6171.ts.net/",
  [string]$SchedulerHotkey = "Ctrl+Space"
)

$ErrorActionPreference = "Stop"

$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch '^[0-9a-f]{40}$') {
  throw "Stage 12 requires an exact Git source SHA."
}

if (Get-Process WorkspaceOperator -ErrorAction SilentlyContinue) {
  throw "Stage 12 requires no pre-existing WorkspaceOperator process."
}
if (Get-Process firefox -ErrorAction SilentlyContinue) {
  throw "Stage 12 requires Firefox to be closed before starting the isolated calibration profile."
}

$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"
$temporaryChatUrl = "https://chatgpt.com/?temporary-chat=true"
$firefoxProfile = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Stage12\firefox-profile"
if (-not (Test-Path -LiteralPath $firefox -PathType Leaf)) {
  throw "Firefox is required at $firefox"
}

$manifestPath = Join-Path $repo "operator-bridge\src\FirefoxAdapter\manifest.json"
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$expectedPermissions = @("nativeMessaging", "tabs", "sessions")
$actualPermissions = @($manifest.permissions)
if (($actualPermissions -join ",") -ne ($expectedPermissions -join ",")) {
  throw "Stage 12 refuses Firefox permission drift."
}
if ($manifest.PSObject.Properties.Name -contains "content_scripts") {
  throw "Stage 12 refuses content-script/page-content access."
}
if ($manifest.PSObject.Properties.Name -contains "host_permissions") {
  throw "Stage 12 refuses host-permission widening."
}

$bridgeRoot = Join-Path $repo "operator-bridge"
Write-Host "=== STAGE 12 WINDOWS BUILD ==="
Write-Host ("STAGE12_SOURCE_SHA=" + $sourceSha)

dotnet build (Join-Path $bridgeRoot "WorkspaceOperatorBridge.slnx") --configuration Release
if ($LASTEXITCODE -ne 0) {
  throw "Stage 12 Operator Bridge build failed."
}

$helper = Join-Path $bridgeRoot "src\WorkspaceOperator\bin\Release\net10.0-windows\WorkspaceOperator.exe"
if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
  throw "Stage 12 helper binary is missing after build."
}

$cacheRoot = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Stage12"
$webExtRoot = Join-Path $cacheRoot "web-ext-10.8.0"
$webExt = Join-Path $webExtRoot "node_modules\.bin\web-ext.cmd"
$webExtPackage = Join-Path $webExtRoot "node_modules\web-ext\package.json"
New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null

$webExtReady = $false
if ((Test-Path -LiteralPath $webExt) -and (Test-Path -LiteralPath $webExtPackage)) {
  try {
    $meta = Get-Content -LiteralPath $webExtPackage -Raw | ConvertFrom-Json
    $webExtReady = $meta.version -eq "10.8.0"
  }
  catch {
    $webExtReady = $false
  }
}

if (-not $webExtReady) {
  $stage = Join-Path $cacheRoot ("web-ext-stage-" + [guid]::NewGuid().ToString("N"))
  try {
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    '{"private":true}' | Set-Content -LiteralPath (Join-Path $stage "package.json") -Encoding ASCII
    Push-Location $stage
    try {
      npm.cmd install --no-audit --no-fund --save-exact web-ext@10.8.0
      if ($LASTEXITCODE -ne 0) {
        throw "Pinned web-ext installation failed."
      }
    }
    finally {
      Pop-Location
    }
    $meta = Get-Content -LiteralPath (Join-Path $stage "node_modules\web-ext\package.json") -Raw | ConvertFrom-Json
    if ($meta.version -ne "10.8.0") {
      throw "Pinned web-ext resolved an unexpected version."
    }
    Remove-Item -LiteralPath $webExtRoot -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item -LiteralPath $stage -Destination $webExtRoot
  }
  finally {
    if ($stage -and (Test-Path -LiteralPath $stage)) {
      Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}

$work = Join-Path $env:TEMP ("workspace-stage12-real-instant-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work -Force | Out-Null

$extensionStage = Join-Path $work "extension"
Copy-Item -LiteralPath (Join-Path $bridgeRoot "src\FirefoxAdapter") -Destination $extensionStage -Recurse

$nativeManifest = Join-Path $work "native-host.json"
[ordered]@{
  name = "com.workspacecontrol.operator_bridge"
  description = "Workspace Control Stage 12 real-Instant calibration"
  path = $helper
  type = "stdio"
  allowed_extensions = @("workspace-control-operator@adamtrott78.local")
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $nativeManifest -Encoding UTF8

$regPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
$regExisted = Test-Path -LiteralPath $regPath
$oldValue = if ($regExisted) { (Get-Item -LiteralPath $regPath).GetValue("") } else { $null }

$helperOut = Join-Path $work "helper.out.log"
$helperErr = Join-Path $work "helper.err.log"
$webExtOut = Join-Path $work "web-ext.out.log"
$webExtErr = Join-Path $work "web-ext.err.log"
$helperProcess = $null
$webExtProcess = $null

try {
  New-Item -ItemType Directory -Path $regPath -Force | Out-Null
  Set-Item -LiteralPath $regPath -Value $nativeManifest

  $helperProcess = Start-Process -FilePath $helper -ArgumentList @(
    "--operator-bridge-url=$OperatorBridgeUrl",
    "--operator-helper-id=stage12-desktop-ub9p70p",
    "--operator-bridge-timeout-ms=5000",
    "--operator-status-refresh-ms=500",
    "--operator-claim-lease-ms=30000",
    "--scheduler-hotkey=$SchedulerHotkey",
    "--bridge-start-enabled"
  ) -RedirectStandardOutput $helperOut -RedirectStandardError $helperErr -PassThru

  Start-Sleep -Milliseconds 750
  if ($helperProcess.HasExited) {
    if (Test-Path $helperOut) { Get-Content $helperOut }
    if (Test-Path $helperErr) { Get-Content $helperErr }
    throw "Stage 12 helper exited during startup."
  }

  $launcher = Join-Path $work "run-web-ext.cmd"
  @"
@echo off
call "$webExt" run --source-dir "$extensionStage" --firefox "$firefox" --firefox-profile "$firefoxProfile" --profile-create-if-missing --keep-profile-changes --start-url "$temporaryChatUrl" --no-reload --no-input --arg=-no-remote
"@ | Set-Content -LiteralPath $launcher -Encoding ASCII

  $webExtProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/d", "/c", $launcher
  ) -RedirectStandardOutput $webExtOut -RedirectStandardError $webExtErr -PassThru

  Start-Sleep -Seconds 4
  if ($webExtProcess.HasExited) {
    if (Test-Path $webExtOut) { Get-Content $webExtOut }
    if (Test-Path $webExtErr) { Get-Content $webExtErr }
    throw "Stage 12 isolated Firefox profile exited during startup."
  }

  Write-Host ""
  Write-Host "STAGE12_WINDOWS_RUNTIME_READY=PASS"
  Write-Host "The dedicated persistent Workspace Operator Firefox profile is open."
  Write-Host "The worker is launched at https://chatgpt.com/?temporary-chat=true. Sign in normally if the dedicated profile is not already authenticated."
  Write-Host "Do not paste credentials into this terminal and do not use credential automation."
  Write-Host "Select the normal ChatGPT Instant mode for the calibration."
  [void](Read-Host "After normal manual login is complete and Instant is selected, press Enter here")

  Write-Host "STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS"
  Write-Host ""
  Write-Host "Keep this PowerShell window running."
  Write-Host "When the Linux calibration terminal prints a STAGE12_*_READY line:"
  Write-Host "  1. press $SchedulerHotkey"
  Write-Host "  2. press Ctrl+V"
  Write-Host "  3. press Enter"
  Write-Host "Do not manually search for worker tabs and do not copy worker results back to the Linux terminal."
  Write-Host "The worker must publish its own immutable GitHub candidate."
  Write-Host ""

  [void](Read-Host "After Linux reports STAGE12_REAL_INSTANT_CALIBRATION result PASS (or a failure), press Enter to clean up")
}
finally {
  if ($webExtProcess -and -not $webExtProcess.HasExited) {
    Stop-Process -Id $webExtProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($helperProcess -and -not $helperProcess.HasExited) {
    Stop-Process -Id $helperProcess.Id -Force -ErrorAction SilentlyContinue
  }

  if ($regExisted) {
    New-Item -ItemType Directory -Path $regPath -Force | Out-Null
    Set-Item -LiteralPath $regPath -Value $oldValue
  }
  elseif (Test-Path -LiteralPath $regPath) {
    Remove-Item -LiteralPath $regPath -Recurse -Force
  }

  Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "STAGE12_WINDOWS_CLEANUP=PASS"
