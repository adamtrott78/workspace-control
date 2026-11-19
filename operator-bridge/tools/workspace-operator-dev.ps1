[CmdletBinding()]
param(
  [ValidateSet("smoke","reset","restart","start","online","stop","offline","status")]
  [string]$Action = "status",
  [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
  [string]$SchedulerHotkey = "Ctrl+Space",
  [string]$OperatorBridgeUrl = ""
)

$ErrorActionPreference = "Stop"

$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$bridgeRoot = Join-Path $repo "operator-bridge"
$runtimeRoot = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\DevRuntime"
$statePath = Join-Path $runtimeRoot "runtime.json"
$registryPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"

function Get-Dotnet10 {
  $candidates = @()
  $cmd = Get-Command dotnet -ErrorAction SilentlyContinue
  if ($cmd) { $candidates += $cmd.Source }
  if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles "dotnet\dotnet.exe") }
  if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} "dotnet\dotnet.exe") }
  if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA "Microsoft\dotnet\dotnet.exe") }
  if ($env:USERPROFILE) { $candidates += (Join-Path $env:USERPROFILE ".dotnet\dotnet.exe") }

  foreach ($candidate in ($candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)) {
    $version = (& $candidate --version).Trim()
    if ($LASTEXITCODE -eq 0 -and $version -match "^10\.") { return $candidate }
  }
  throw "DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS"
}

function Get-Node24Directory {
  $node = Get-Command node.exe -ErrorAction SilentlyContinue
  if ($node) {
    $dir = Split-Path -Parent $node.Source
    $nodeExe = Join-Path $dir "node.exe"
    $npmCmd = Join-Path $dir "npm.cmd"
    if ((Test-Path $nodeExe) -and (Test-Path $npmCmd)) {
      $version = (& $nodeExe --version).Trim()
      if ($LASTEXITCODE -eq 0 -and $version -match "^v24\.") { return $dir }
    }
  }

  $toolCache = if ($env:RUNNER_TOOL_CACHE) { $env:RUNNER_TOOL_CACHE } else { Join-Path $env:USERPROFILE "actions-runner\_work\_tool" }
  $nodeRoot = Join-Path $toolCache "node"
  $dirs = @(Get-ChildItem $nodeRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "^24\.\d+\.\d+$" } |
    Sort-Object { [version]$_.Name } -Descending)
  foreach ($entry in $dirs) {
    $dir = Join-Path $entry.FullName "x64"
    if ((Test-Path (Join-Path $dir "node.exe")) -and (Test-Path (Join-Path $dir "npm.cmd"))) { return $dir }
  }
  throw "NODE24_NOT_FOUND_IN_REVIEWED_LOCATIONS"
}

function Read-State {
  if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { return $null }
  return Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
}

function Test-Pid([int]$Pid) {
  return $null -ne (Get-Process -Id $Pid -ErrorAction SilentlyContinue)
}

function Remove-TreeWithRetry([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  for ($i = 0; $i -lt 20; $i++) {
    try {
      Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
      return
    } catch {
      Start-Sleep -Milliseconds 250
    }
  }
  throw "DEV_RUNTIME_CLEANUP_FAILED:$Path"
}

function Stop-DevRuntime {
  $state = Read-State
  if ($null -eq $state) {
    Write-Host "WORKSPACE_OPERATOR_DEV_OFFLINE=PASS"
    return
  }

  $pids = @()
  if ($state.web_ext_pid) { $pids += [int]$state.web_ext_pid }
  foreach ($pidValue in @($state.firefox_pids)) { if ($pidValue) { $pids += [int]$pidValue } }
  foreach ($pidValue in @($state.workspace_operator_pids)) { if ($pidValue) { $pids += [int]$pidValue } }

  foreach ($pidValue in ($pids | Select-Object -Unique)) {
    Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Milliseconds 500

  if (Test-Path -LiteralPath $registryPath) {
    $current = (Get-Item -LiteralPath $registryPath).GetValue("")
    if ([string]$current -eq [string]$state.native_manifest) {
      if ($state.registry_existed) {
        Set-Item -LiteralPath $registryPath -Value ([string]$state.registry_old_value)
      } else {
        Remove-Item -LiteralPath $registryPath -Recurse -Force
      }
    }
  }

  Remove-TreeWithRetry ([string]$state.work_dir)
  Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
  Write-Host "WORKSPACE_OPERATOR_DEV_OFFLINE=PASS"
}

function Ensure-WebExt([string]$NodeDir) {
  $cacheRoot = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Stage12"
  $webExtRoot = Join-Path $cacheRoot "web-ext-10.8.0"
  $webExt = Join-Path $webExtRoot "node_modules\.bin\web-ext.cmd"
  $package = Join-Path $webExtRoot "node_modules\web-ext\package.json"
  New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null

  if ((Test-Path $webExt) -and (Test-Path $package)) {
    $meta = Get-Content $package -Raw | ConvertFrom-Json
    if ($meta.version -eq "10.8.0") { return $webExt }
  }

  $stage = Join-Path $cacheRoot ("web-ext-stage-" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $stage -Force | Out-Null
  try {
    '{"private":true}' | Set-Content (Join-Path $stage "package.json") -Encoding ASCII
    Push-Location $stage
    try {
      & (Join-Path $NodeDir "npm.cmd") install --no-audit --no-fund --save-exact web-ext@10.8.0
      if ($LASTEXITCODE -ne 0) { throw "PINNED_WEB_EXT_INSTALL_FAILED" }
    } finally { Pop-Location }
    Remove-Item -LiteralPath $webExtRoot -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item -LiteralPath $stage -Destination $webExtRoot
  } finally {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
  }
  return $webExt
}

function Start-DevRuntime([bool]$LocalSmoke) {
  if (Read-State) { throw "DEV_RUNTIME_ALREADY_EXISTS: use reset or stop" }
  if (-not (Test-Path -LiteralPath $firefox -PathType Leaf)) { throw "FIREFOX_NOT_FOUND:$firefox" }

  New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
  $sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") { throw "SOURCE_SHA_UNAVAILABLE" }

  $dotnet = Get-Dotnet10
  $nodeDir = Get-Node24Directory
  $oldPath = $env:PATH
  $oldDotnetRoot = $env:DOTNET_ROOT
  $env:PATH = "$(Split-Path -Parent $dotnet);$nodeDir;$oldPath"
  $env:DOTNET_ROOT = Split-Path -Parent $dotnet

  try {
    & $dotnet build (Join-Path $bridgeRoot "WorkspaceOperatorBridge.slnx") --configuration Release
    if ($LASTEXITCODE -ne 0) { throw "DEV_BUILD_FAILED" }

    $helper = Join-Path $bridgeRoot "src\WorkspaceOperator\bin\Release\net10.0-windows\WorkspaceOperator.exe"
    $webExt = Ensure-WebExt $nodeDir
    $work = Join-Path $runtimeRoot ("run-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    $extension = Join-Path $work "extension"
    Copy-Item -LiteralPath (Join-Path $bridgeRoot "src\FirefoxAdapter") -Destination $extension -Recurse

    $nativeManifest = Join-Path $work "native-host.json"
    [ordered]@{
      name = "com.workspacecontrol.operator_bridge"
      description = "Workspace Control development runtime"
      path = $helper
      type = "stdio"
      allowed_extensions = @("workspace-control-operator@adamtrott78.local")
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $nativeManifest -Encoding UTF8

    $registryExisted = Test-Path -LiteralPath $registryPath
    $registryOldValue = if ($registryExisted) { (Get-Item -LiteralPath $registryPath).GetValue("") } else { $null }
    $beforeFirefox = @(Get-Process firefox -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    $beforeOperator = @(Get-Process WorkspaceOperator -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)

    New-Item -ItemType Directory -Path $registryPath -Force | Out-Null
    Set-Item -LiteralPath $registryPath -Value $nativeManifest

    $helperOut = Join-Path $work "helper.out.log"
    $helperErr = Join-Path $work "helper.err.log"
    $webOut = Join-Path $work "web-ext.out.log"
    $webErr = Join-Path $work "web-ext.err.log"

    $helperArgs = @("--bridge-start-enabled", "--scheduler-hotkey=$SchedulerHotkey")
    if ($LocalSmoke) {
      $helperArgs += "--local-smoke"
    } elseif (-not [string]::IsNullOrWhiteSpace($OperatorBridgeUrl)) {
      $helperArgs += "--operator-bridge-url=$OperatorBridgeUrl"
      $helperArgs += "--operator-helper-id=workspace-operator-dev"
    }

    $helperProcess = Start-Process -FilePath $helper -ArgumentList $helperArgs -RedirectStandardOutput $helperOut -RedirectStandardError $helperErr -PassThru
    Start-Sleep -Milliseconds 750
    if ($helperProcess.HasExited) {
      if (Test-Path $helperOut) { Get-Content $helperOut }
      if (Test-Path $helperErr) { Get-Content $helperErr }
      throw "DEV_HELPER_START_FAILED"
    }

    $launcher = Join-Path $work "run-web-ext.cmd"
    @"
@echo off
call "$webExt" run --source-dir "$extension" --firefox "$firefox" --no-reload --no-input --arg=-no-remote
"@ | Set-Content -LiteralPath $launcher -Encoding ASCII

    $webExtProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d","/c",$launcher) -RedirectStandardOutput $webOut -RedirectStandardError $webErr -PassThru
    Start-Sleep -Seconds 4
    if ($webExtProcess.HasExited) {
      if (Test-Path $webOut) { Get-Content $webOut }
      if (Test-Path $webErr) { Get-Content $webErr }
      throw "DEV_FIREFOX_START_FAILED"
    }

    $afterFirefox = @(Get-Process firefox -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    $afterOperator = @(Get-Process WorkspaceOperator -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    $newFirefox = @($afterFirefox | Where-Object { $_ -notin $beforeFirefox })
    $newOperator = @($afterOperator | Where-Object { $_ -notin $beforeOperator })

    [ordered]@{
      schema_version = 1
      source_sha = $sourceSha
      mode = if ($LocalSmoke) { "smoke" } else { "online" }
      work_dir = $work
      native_manifest = $nativeManifest
      registry_existed = $registryExisted
      registry_old_value = $registryOldValue
      helper_pid = $helperProcess.Id
      web_ext_pid = $webExtProcess.Id
      firefox_pids = $newFirefox
      workspace_operator_pids = $newOperator
      scheduler_hotkey = $SchedulerHotkey
      started_at = [DateTimeOffset]::UtcNow.ToString("O")
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding UTF8

    Write-Host "WORKSPACE_OPERATOR_DEV_ONLINE=PASS"
    Write-Host "WORKSPACE_OPERATOR_HOTKEY_REGISTERED=PASS"
    Write-Host ("WORKSPACE_OPERATOR_SOURCE_SHA=" + $sourceSha)
    if ($LocalSmoke) {
      Write-Host "WORKSPACE_OPERATOR_SMOKE_READY=Press Ctrl+Space once. Expected clipboard: WORKSPACE_OPERATOR_SMOKE_PACKET_V1; expected foreground: the dedicated Firefox window."
    }
  } catch {
    try { Stop-DevRuntime } catch {}
    throw
  } finally {
    $env:PATH = $oldPath
    $env:DOTNET_ROOT = $oldDotnetRoot
  }
}

function Show-Status {
  $state = Read-State
  if ($null -eq $state) {
    Write-Host "WORKSPACE_OPERATOR_DEV_STATUS=OFFLINE"
    return
  }
  $helperAlive = Test-Pid ([int]$state.helper_pid)
  $webAlive = Test-Pid ([int]$state.web_ext_pid)
  $firefoxAlive = @($state.firefox_pids | Where-Object { Test-Pid ([int]$_) }).Count
  Write-Host ("WORKSPACE_OPERATOR_DEV_STATUS=" + ($(if ($helperAlive -and $webAlive) { "ONLINE" } else { "DEGRADED" })))
  Write-Host ("SOURCE_SHA=" + $state.source_sha)
  Write-Host ("MODE=" + $state.mode)
  Write-Host ("HELPER_ALIVE=" + $helperAlive)
  Write-Host ("WEB_EXT_ALIVE=" + $webAlive)
  Write-Host ("FIREFOX_ALIVE_COUNT=" + $firefoxAlive)
  Write-Host ("HOTKEY=" + $state.scheduler_hotkey)
}

switch ($Action) {
  "stop" { Stop-DevRuntime }
  "offline" { Stop-DevRuntime }
  "status" { Show-Status }
  "smoke" { Stop-DevRuntime; Start-DevRuntime $true }
  "reset" { Stop-DevRuntime; Start-DevRuntime $true }
  "restart" { Stop-DevRuntime; Start-DevRuntime $true }
  "start" { Stop-DevRuntime; Start-DevRuntime ([string]::IsNullOrWhiteSpace($OperatorBridgeUrl)) }
  "online" { Stop-DevRuntime; Start-DevRuntime ([string]::IsNullOrWhiteSpace($OperatorBridgeUrl)) }
}
