# Windows-only fast-loop harness: content-free smoke actions remain operator-triggered.
[CmdletBinding()]
param(
  [ValidateSet("smoke","reset","restart","start","online","stop","offline","status","self-test")]
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
$cleanupResiduePath = Join-Path $runtimeRoot "cleanup-residue.jsonl"
$registryPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"
$firefoxProfile = Join-Path $runtimeRoot "firefox-profile"

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

function Test-Pid([int]$ProcessId) {
  return $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
}

function Try-RemoveTreeWithRetry([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $true }

  $lastError = ""
  for ($i = 0; $i -lt 20; $i++) {
    try {
      Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
      return $true
    } catch {
      $lastError = $_.Exception.Message
      Start-Sleep -Milliseconds 250
    }
  }

  [ordered]@{
    schema_version = 1
    observed_at = [DateTimeOffset]::UtcNow.ToString("O")
    path = $Path
    error = $lastError
  } | ConvertTo-Json -Compress | Add-Content -LiteralPath $cleanupResiduePath -Encoding UTF8

  Write-Host ("WORKSPACE_OPERATOR_RUNTIME_RESIDUE=DEFERRED:" + $Path)
  return $false
}

function Get-RuntimeOwnedProcesses([object]$State) {
  $snapshot = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
  if ($snapshot.Count -eq 0) { return @() }

  $owned = [System.Collections.Generic.HashSet[int]]::new()
  $workDir = [string]$State.work_dir
  $helperPath = [string]$State.helper_path

  foreach ($process in $snapshot) {
    $pidValue = [int]$process.ProcessId
    $name = [string]$process.Name
    $commandLine = [string]$process.CommandLine
    $executablePath = [string]$process.ExecutablePath

    if (
      $State.web_ext_pid -and
      $pidValue -eq [int]$State.web_ext_pid -and
      $name -ieq "cmd.exe"
    ) {
      [void]$owned.Add($pidValue)
    }

    if (
      $State.helper_pid -and
      $pidValue -eq [int]$State.helper_pid -and
      $name -ieq "WorkspaceOperator.exe"
    ) {
      [void]$owned.Add($pidValue)
    }

    if (
      @($State.firefox_pids) -contains $pidValue -and
      $name -ieq "firefox.exe"
    ) {
      [void]$owned.Add($pidValue)
    }

    if (
      @($State.workspace_operator_pids) -contains $pidValue -and
      $name -ieq "WorkspaceOperator.exe"
    ) {
      [void]$owned.Add($pidValue)
    }

    if (
      -not [string]::IsNullOrWhiteSpace($workDir) -and
      -not [string]::IsNullOrWhiteSpace($commandLine) -and
      $commandLine.IndexOf(
        $workDir,
        [System.StringComparison]::OrdinalIgnoreCase) -ge 0
    ) {
      [void]$owned.Add($pidValue)
    }

    if (
      $name -ieq "WorkspaceOperator.exe" -and
      -not [string]::IsNullOrWhiteSpace($helperPath) -and
      [string]::Equals(
        $executablePath,
        $helperPath,
        [System.StringComparison]::OrdinalIgnoreCase)
    ) {
      [void]$owned.Add($pidValue)
    }
  }

  $changed = $true
  while ($changed) {
    $changed = $false
    foreach ($process in $snapshot) {
      $pidValue = [int]$process.ProcessId
      $parentPid = [int]$process.ParentProcessId
      if ($owned.Contains($parentPid) -and $owned.Add($pidValue)) {
        $changed = $true
      }
    }
  }

  return @($snapshot | Where-Object {
    $owned.Contains([int]$_.ProcessId)
  })
}

function Stop-RuntimeOwnedProcesses([object]$State) {
  $owned = @(Get-RuntimeOwnedProcesses $State)
  $firefoxIds = @(
    $owned |
      Where-Object { [string]$_.Name -ieq "firefox.exe" } |
      ForEach-Object { [int]$_.ProcessId }
  )
  Stop-ManagedFirefox $firefoxIds

  $owned = @(Get-RuntimeOwnedProcesses $State)
  foreach ($process in $owned) {
    if ([string]$process.Name -ieq "firefox.exe") { continue }
    Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
  }

  $deadline = (Get-Date).AddSeconds(5)
  do {
    $remaining = @(Get-RuntimeOwnedProcesses $State)
    if ($remaining.Count -eq 0) {
      Write-Host "WORKSPACE_OPERATOR_RUNTIME_PROCESS_CLEANUP=PASS"
      return
    }
    Start-Sleep -Milliseconds 100
  } while ((Get-Date) -lt $deadline)

  foreach ($process in $remaining) {
    Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Milliseconds 500

  $remaining = @(Get-RuntimeOwnedProcesses $State)
  if ($remaining.Count -gt 0) {
    $ids = @($remaining | ForEach-Object { [string]$_.ProcessId }) -join ","
    throw "DEV_RUNTIME_PROCESS_CLEANUP_FAILED:$ids"
  }

  Write-Host "WORKSPACE_OPERATOR_RUNTIME_PROCESS_CLEANUP=PASS"
}

function Stop-ManagedFirefox([object[]]$ProcessIds) {
  $ids = @($ProcessIds | Where-Object { $_ } | ForEach-Object { [int]$_ } | Select-Object -Unique)
  if ($ids.Count -eq 0) { return }

  $closeRequested = $false
  foreach ($pidValue in $ids) {
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process -and $process.MainWindowHandle -ne 0) {
      try {
        if ($process.CloseMainWindow()) { $closeRequested = $true }
      } catch {}
    }
  }

  if ($closeRequested) {
    $deadline = (Get-Date).AddSeconds(5)
    while ((Get-Date) -lt $deadline) {
      $alive = @($ids | Where-Object { Test-Pid $_ })
      if ($alive.Count -eq 0) {
        Write-Host "WORKSPACE_OPERATOR_FIREFOX_SHUTDOWN=GRACEFUL"
        return
      }
      Start-Sleep -Milliseconds 100
    }
  }

  $remaining = @($ids | Where-Object { Test-Pid $_ })
  foreach ($pidValue in $remaining) {
    Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
  }
  if ($remaining.Count -gt 0) {
    Write-Host "WORKSPACE_OPERATOR_FIREFOX_SHUTDOWN=FORCED_FALLBACK"
  }
}

function Stop-DevRuntime {
  $state = Read-State
  if ($null -eq $state) {
    Write-Host "WORKSPACE_OPERATOR_DEV_OFFLINE=PASS"
    return
  }

  Stop-RuntimeOwnedProcesses $state

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

  $workdirRemoved = Try-RemoveTreeWithRetry ([string]$state.work_dir)
  Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue

  if ($workdirRemoved) {
    Write-Host "WORKSPACE_OPERATOR_RUNTIME_WORKDIR_CLEANUP=PASS"
  } else {
    Write-Host "WORKSPACE_OPERATOR_RUNTIME_WORKDIR_CLEANUP=DEFERRED"
  }

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

function Reset-DedicatedFirefoxSessionState([string]$ProfilePath) {
  if (-not (Test-Path -LiteralPath $ProfilePath -PathType Container)) {
    Write-Host "WORKSPACE_OPERATOR_FIREFOX_SESSION_STATE_RESET=PASS"
    return
  }

  foreach ($relative in @(
    "sessionstore.jsonlz4",
    "sessionCheckpoints.json",
    "sessionstore-backups"
  )) {
    $target = Join-Path $ProfilePath $relative
    if (Test-Path -LiteralPath $target) {
      Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
    }
  }

  Write-Host "WORKSPACE_OPERATOR_FIREFOX_SESSION_STATE_RESET=PASS"
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

  $work = $null
  $helperProcess = $null
  $webExtProcess = $null
  $registryExisted = $false
  $registryOldValue = $null
  $nativeManifest = $null

  try {
    $helper = Join-Path $bridgeRoot "src\WorkspaceOperator\bin\Release\net10.0-windows\WorkspaceOperator.exe"
    $buildStamp = Join-Path $runtimeRoot "build-source-tree.txt"
    $buildTree = (git -C $repo rev-parse "HEAD:operator-bridge/src").Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $buildTree -notmatch "^[0-9a-f]{40}$") {
      throw "DEV_BUILD_TREE_UNAVAILABLE"
    }

    $cachedTree = if (Test-Path -LiteralPath $buildStamp -PathType Leaf) {
      (Get-Content -LiteralPath $buildStamp -Raw).Trim().ToLowerInvariant()
    } else {
      ""
    }

    if ($cachedTree -ne $buildTree -or -not (Test-Path -LiteralPath $helper -PathType Leaf)) {
      & $dotnet build (Join-Path $bridgeRoot "WorkspaceOperatorBridge.slnx") --configuration Release
      if ($LASTEXITCODE -ne 0) { throw "DEV_BUILD_FAILED" }
      Set-Content -LiteralPath $buildStamp -Value $buildTree -Encoding ASCII
      Write-Host "WORKSPACE_OPERATOR_BUILD_CACHE=MISS"
    } else {
      Write-Host "WORKSPACE_OPERATOR_BUILD_CACHE=HIT"
    }

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
call "$webExt" run --source-dir "$extension" --firefox "$firefox" --firefox-profile "$firefoxProfile" --profile-create-if-missing --keep-profile-changes --no-reload --no-input --pref=browser.startup.page=0 --pref=browser.sessionstore.resume_from_crash=false --arg=-no-remote
"@ | Set-Content -LiteralPath $launcher -Encoding ASCII

    Reset-DedicatedFirefoxSessionState $firefoxProfile
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
      helper_path = $helper
      helper_pid = $helperProcess.Id
      web_ext_pid = $webExtProcess.Id
      firefox_pids = $newFirefox
      firefox_profile = $firefoxProfile
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
    if ($webExtProcess -and -not $webExtProcess.HasExited) {
      Stop-Process -Id $webExtProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($helperProcess -and -not $helperProcess.HasExited) {
      Stop-Process -Id $helperProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($nativeManifest -and (Test-Path -LiteralPath $registryPath)) {
      $current = (Get-Item -LiteralPath $registryPath).GetValue("")
      if ([string]$current -eq [string]$nativeManifest) {
        if ($registryExisted) {
          Set-Item -LiteralPath $registryPath -Value $registryOldValue
        } else {
          Remove-Item -LiteralPath $registryPath -Recurse -Force
        }
      }
    }
    if ($work) {
      [void](Try-RemoveTreeWithRetry $work)
    }
    throw
  } finally {
    $env:PATH = $oldPath
    $env:DOTNET_ROOT = $oldDotnetRoot
  }
}

function Invoke-SelfTest {
  if (-not (Test-Path -LiteralPath $repo -PathType Container)) {
    throw "WOP_REPOSITORY_ROOT_MISSING:$repo"
  }
  if (-not (Test-Path -LiteralPath $firefox -PathType Leaf)) {
    throw "FIREFOX_NOT_FOUND:$firefox"
  }

  $sourceSha = (git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") {
    throw "SOURCE_SHA_UNAVAILABLE"
  }

  $dotnet = Get-Dotnet10
  $nodeDir = Get-Node24Directory

  $runtimeState = "OFFLINE"
  $state = Read-State
  if ($null -ne $state) {
    if ([string]$state.source_sha -notmatch "^[0-9a-f]{40}$") {
      throw "DEV_RUNTIME_STATE_SOURCE_SHA_INVALID"
    }

    $helperAlive = Test-Pid ([int]$state.helper_pid)
    $webAlive = Test-Pid ([int]$state.web_ext_pid)
    if (-not ($helperAlive -and $webAlive)) {
      throw "DEV_RUNTIME_DEGRADED"
    }
    $runtimeState = "ONLINE"
  }

  Write-Host "WORKSPACE_OPERATOR_SELF_TEST=PASS"
  Write-Host ("SOURCE_SHA=" + $sourceSha)
  Write-Host ("DOTNET10=" + (& $dotnet --version).Trim())
  Write-Host ("NODE24=" + (& (Join-Path $nodeDir "node.exe") --version).Trim())
  Write-Host ("FIREFOX_PATH=" + $firefox)
  Write-Host ("RUNTIME_STATE=" + $runtimeState)
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
  Write-Host ("FIREFOX_PROFILE=" + $state.firefox_profile)
  Write-Host ("HOTKEY=" + $state.scheduler_hotkey)
}

switch ($Action) {
  "stop" { Stop-DevRuntime }
  "offline" { Stop-DevRuntime }
  "status" { Show-Status }
  "self-test" { Invoke-SelfTest }
  "smoke" { Stop-DevRuntime; Start-DevRuntime $true }
  "reset" { Stop-DevRuntime; Start-DevRuntime $true }
  "restart" { Stop-DevRuntime; Start-DevRuntime $true }
  "start" { Stop-DevRuntime; Start-DevRuntime ([string]::IsNullOrWhiteSpace($OperatorBridgeUrl)) }
  "online" { Stop-DevRuntime; Start-DevRuntime ([string]::IsNullOrWhiteSpace($OperatorBridgeUrl)) }
}
