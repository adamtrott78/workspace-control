# Installs current-user executable shims for the Workspace Operator dev lifecycle.
[CmdletBinding()]
param(
  [switch]$Remove
)

$ErrorActionPreference = "Stop"

$legacyBegin = "# BEGIN WORKSPACE OPERATOR COMMANDS V1"
$legacyEnd = "# END WORKSPACE OPERATOR COMMANDS V1"
$shimMarker = "@rem workspace-control-owned:wop-command-v2"
$driverMarker = "# workspace-control-owned:wop-driver-v2"
$commandRoot = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Commands"
$commandDirectory = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
$driverPath = Join-Path $commandRoot "wop-driver.ps1"
$legacyProfilePath = $PROFILE.CurrentUserAllHosts
$commandNames = @(
  "wop",
  "wop-d4",
  "wop-e1",
  "wop-e2",
  "wop-e3",
  "wop-up",
  "wop-down",
  "wop-reset",
  "wop-status",
  "wop-self-test"
)

function Remove-LegacyProfileBlock {
  if (-not (Test-Path -LiteralPath $legacyProfilePath -PathType Leaf)) {
    Write-Host "WORKSPACE_OPERATOR_LEGACY_PROFILE_BLOCK=ABSENT"
    return
  }

  $content = Get-Content -LiteralPath $legacyProfilePath -Raw
  $pattern = "(?ms)^" +
    [regex]::Escape($legacyBegin) +
    "\r?\n.*?^" +
    [regex]::Escape($legacyEnd) +
    "\r?\n?"
  $updated = [regex]::Replace($content, $pattern, "")

  if ($updated -ne $content) {
    Set-Content -LiteralPath $legacyProfilePath -Value $updated.TrimEnd() -Encoding UTF8
    Write-Host "WORKSPACE_OPERATOR_LEGACY_PROFILE_BLOCK=REMOVED"
  } else {
    Write-Host "WORKSPACE_OPERATOR_LEGACY_PROFILE_BLOCK=ABSENT"
  }
}

function Test-CommandDirectoryOnPath {
  $expected = [System.IO.Path]::GetFullPath($commandDirectory).TrimEnd("\")
  foreach ($entry in ($env:PATH -split ";")) {
    if ([string]::IsNullOrWhiteSpace($entry)) { continue }
    try {
      $expanded = [Environment]::ExpandEnvironmentVariables($entry)
      $actual = [System.IO.Path]::GetFullPath($expanded).TrimEnd("\")
      if ($actual.Equals(
        $expected,
        [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
      }
    } catch {}
  }
  return $false
}

function Assert-OwnedOrAbsent([string]$Path, [string]$ExpectedMarker) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
  $firstLine = Get-Content -LiteralPath $Path -TotalCount 1
  if ($firstLine -ne $ExpectedMarker) {
    throw "WOP_COMMAND_PATH_COLLISION:$Path"
  }
}

function Remove-OwnedFile([string]$Path, [string]$ExpectedMarker) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
  Assert-OwnedOrAbsent $Path $ExpectedMarker
  Remove-Item -LiteralPath $Path -Force
}

Remove-LegacyProfileBlock

if (-not (Test-Path -LiteralPath $commandDirectory -PathType Container)) {
  throw "WOP_WINDOWS_APPS_DIRECTORY_MISSING:$commandDirectory"
}
if (-not (Test-CommandDirectoryOnPath)) {
  throw "WOP_WINDOWS_APPS_NOT_ON_PATH:$commandDirectory"
}

if ($Remove) {
  foreach ($name in $commandNames) {
    Remove-OwnedFile (Join-Path $commandDirectory ($name + ".cmd")) $shimMarker
  }
  Remove-OwnedFile $driverPath $driverMarker
  if (Test-Path -LiteralPath $commandRoot -PathType Container) {
    $remaining = @(Get-ChildItem -LiteralPath $commandRoot -Force -ErrorAction SilentlyContinue)
    if ($remaining.Count -eq 0) {
      Remove-Item -LiteralPath $commandRoot -Force
    }
  }
  Write-Host "WORKSPACE_OPERATOR_COMMANDS_REMOVED=PASS"
  Write-Host ("COMMAND_DIRECTORY=" + $commandDirectory)
  return
}

$probe = Join-Path $commandDirectory ("wop-write-probe-" + [guid]::NewGuid().ToString("N") + ".tmp")
try {
  Set-Content -LiteralPath $probe -Value "probe" -Encoding ASCII
} finally {
  Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
}
Write-Host "WORKSPACE_OPERATOR_COMMAND_PATH=PASS"

New-Item -ItemType Directory -Path $commandRoot -Force | Out-Null

$driver = @'
# workspace-control-owned:wop-driver-v2
[CmdletBinding()]
param(
  [ValidateSet("smoke","reset","restart","start","online","d4","e1","e2","e3","stop","offline","status","self-test")]
  [string]$Action = "status",
  [string]$Sha = ""
)

$ErrorActionPreference = "Stop"

try {
  $W = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\DevCheckout"
  if (-not (Test-Path -LiteralPath (Join-Path $W ".git") -PathType Container)) {
    throw "WOP_DEV_CHECKOUT_MISSING:$W"
  }

  if ([string]::Equals($Action, "d4", [System.StringComparison]::OrdinalIgnoreCase) -and
      [string]::IsNullOrWhiteSpace($Sha)) {
    git -C $W fetch --force --depth=1 origin workspace-semantic-execution-migration-v1
    if ($LASTEXITCODE -ne 0) { throw "WOP_D4_BRANCH_FETCH_FAILED" }
    $Sha = (git -C $W rev-parse FETCH_HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $Sha -notmatch "^[0-9a-f]{40}$") {
      throw "WOP_D4_BRANCH_HEAD_UNAVAILABLE"
    }
  }

  if ([string]::Equals($Action, "e1", [System.StringComparison]::OrdinalIgnoreCase) -and
      [string]::IsNullOrWhiteSpace($Sha)) {
    git -C $W fetch --force --depth=1 origin workspace-semantic-execution-migration-v1
    if ($LASTEXITCODE -ne 0) { throw "WOP_E1_BRANCH_FETCH_FAILED" }
    $Sha = (git -C $W rev-parse FETCH_HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $Sha -notmatch "^[0-9a-f]{40}$") {
      throw "WOP_E1_BRANCH_HEAD_UNAVAILABLE"
    }
  }

  if ([string]::Equals($Action, "e2", [System.StringComparison]::OrdinalIgnoreCase) -and
      [string]::IsNullOrWhiteSpace($Sha)) {
    git -C $W fetch --force --depth=1 origin workspace-semantic-execution-migration-v1
    if ($LASTEXITCODE -ne 0) { throw "WOP_E2_BRANCH_FETCH_FAILED" }
    $Sha = (git -C $W rev-parse FETCH_HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $Sha -notmatch "^[0-9a-f]{40}$") {
      throw "WOP_E2_BRANCH_HEAD_UNAVAILABLE"
    }
  }

  if ([string]::Equals($Action, "e3", [System.StringComparison]::OrdinalIgnoreCase) -and
      [string]::IsNullOrWhiteSpace($Sha)) {
    git -C $W fetch --force --depth=1 origin workspace-semantic-execution-migration-v1
    if ($LASTEXITCODE -ne 0) { throw "WOP_E3_BRANCH_FETCH_FAILED" }
    $Sha = (git -C $W rev-parse FETCH_HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $Sha -notmatch "^[0-9a-f]{40}$") {
      throw "WOP_E3_BRANCH_HEAD_UNAVAILABLE"
    }
  }

  if (-not [string]::IsNullOrWhiteSpace($Sha)) {
    if ($Sha -notmatch "^[0-9a-fA-F]{40}$") {
      throw "WOP_SHA_INVALID:$Sha"
    }

    git -C $W fetch --force --depth=1 origin workspace-semantic-execution-migration-v1
    if ($LASTEXITCODE -ne 0) { throw "WOP_BRANCH_FETCH_FAILED" }

    $branchHead = (git -C $W rev-parse FETCH_HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $branchHead -notmatch "^[0-9a-f]{40}$") {
      throw "WOP_BRANCH_HEAD_UNAVAILABLE"
    }

    if ($branchHead -eq $Sha.ToLowerInvariant()) {
      git -C $W checkout --detach FETCH_HEAD
    } else {
      git -C $W fetch --force --depth=1 origin $Sha
      if ($LASTEXITCODE -ne 0) { throw "WOP_EXACT_FETCH_FAILED:$Sha" }
      git -C $W checkout --detach FETCH_HEAD
    }
    if ($LASTEXITCODE -ne 0) { throw "WOP_CHECKOUT_FAILED:$Sha" }

    $actual = (git -C $W rev-parse HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $actual -ne $Sha.ToLowerInvariant()) {
      throw "WOP_CHECKOUT_MISMATCH:$actual"
    }

    git -C $W cat-file -e ($actual + "^{tree}")
    if ($LASTEXITCODE -ne 0) {
      throw "WOP_CHECKOUT_TREE_UNAVAILABLE:$actual"
    }
  }

  $engine = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
  if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {
    throw "WOP_POWERSHELL_ENGINE_MISSING:$engine"
  }

  if ([string]::Equals($Action, "d4", [System.StringComparison]::OrdinalIgnoreCase)) {
    $script = Join-Path $W "operator-bridge\tools\run-stage12-wop.ps1"
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
      throw "WOP_D4_SCRIPT_MISSING:$script"
    }
    & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $script -RepositoryRoot $W
  } elseif ([string]::Equals($Action, "e1", [System.StringComparison]::OrdinalIgnoreCase)) {
    $script = Join-Path $W "operator-bridge\tools\run-research-iterate-e1-wop.ps1"
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
      throw "WOP_E1_SCRIPT_MISSING:$script"
    }
    & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $script -RepositoryRoot $W
  } elseif ([string]::Equals($Action, "e2", [System.StringComparison]::OrdinalIgnoreCase)) {
    $script = Join-Path $W "operator-bridge\tools\run-research-iterate-e2-wop.ps1"
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
      throw "WOP_E2_SCRIPT_MISSING:$script"
    }
    & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $script -RepositoryRoot $W
  } elseif ([string]::Equals($Action, "e3", [System.StringComparison]::OrdinalIgnoreCase)) {
    $script = Join-Path $W "operator-bridge\tools\run-research-iterate-e3-wop.ps1"
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
      throw "WOP_E3_SCRIPT_MISSING:$script"
    }
    & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $script -RepositoryRoot $W
  } else {
    $script = Join-Path $W "operator-bridge\tools\workspace-operator-dev.ps1"
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
      throw "WOP_SCRIPT_MISSING:$script"
    }
    & $engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $script $Action -RepositoryRoot $W
  }
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    throw "WOP_ACTION_FAILED:${Action}:${exitCode}"
  }
  exit 0
} catch {
  Write-Error $_
  exit 1
}
'@

$driverTemp = $driverPath + "." + [guid]::NewGuid().ToString("N") + ".tmp"
Set-Content -LiteralPath $driverTemp -Value $driver -Encoding UTF8
if (Test-Path -LiteralPath $driverPath -PathType Leaf) {
  Assert-OwnedOrAbsent $driverPath $driverMarker
}
Move-Item -LiteralPath $driverTemp -Destination $driverPath -Force

$shimActions = [ordered]@{
  "wop" = ""
  "wop-d4" = "d4"
  "wop-e1" = "e1"
  "wop-e2" = "e2"
  "wop-e3" = "e3"
  "wop-up" = "start"
  "wop-down" = "stop"
  "wop-reset" = "reset"
  "wop-status" = "status"
  "wop-self-test" = "self-test"
}

foreach ($entry in $shimActions.GetEnumerator()) {
  $path = Join-Path $commandDirectory ($entry.Key + ".cmd")
  Assert-OwnedOrAbsent $path $shimMarker

  $actionPrefix = if ([string]::IsNullOrWhiteSpace([string]$entry.Value)) {
    ""
  } else {
    ([string]$entry.Value) + " "
  }

  $shim = @"
$shimMarker
@echo off
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$driverPath" $actionPrefix%*
exit /b %ERRORLEVEL%
"@
  Set-Content -LiteralPath $path -Value $shim -Encoding ASCII
}

Write-Host "WORKSPACE_OPERATOR_COMMANDS_INSTALLED=PASS"
Write-Host ("COMMAND_DIRECTORY=" + $commandDirectory)
Write-Host ("DRIVER_PATH=" + $driverPath)
Write-Host "COMMANDS=wop,wop-d4,wop-e1,wop-e2,wop-e3,wop-up,wop-down,wop-reset,wop-status,wop-self-test"
