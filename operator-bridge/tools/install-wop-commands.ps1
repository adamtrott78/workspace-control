# Installs current-user PowerShell commands for the Workspace Operator dev lifecycle.
[CmdletBinding()]
param(
  [string]$ProfilePath = $PROFILE.CurrentUserAllHosts,
  [switch]$Remove
)

$ErrorActionPreference = "Stop"

$beginMarker = "# BEGIN WORKSPACE OPERATOR COMMANDS V1"
$endMarker = "# END WORKSPACE OPERATOR COMMANDS V1"

function Remove-ManagedBlock([string]$Content) {
  if ([string]::IsNullOrEmpty($Content)) { return "" }

  $pattern = "(?ms)^" +
    [regex]::Escape($beginMarker) +
    "\r?\n.*?^" +
    [regex]::Escape($endMarker) +
    "\r?\n?"
  return [regex]::Replace($Content, $pattern, "")
}

$existing = if (Test-Path -LiteralPath $ProfilePath -PathType Leaf) {
  Get-Content -LiteralPath $ProfilePath -Raw
} else {
  ""
}
$withoutManagedBlock = Remove-ManagedBlock $existing

if ($Remove) {
  $directory = Split-Path -Parent $ProfilePath
  if (-not [string]::IsNullOrWhiteSpace($directory)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
  }
  Set-Content -LiteralPath $ProfilePath -Value $withoutManagedBlock.TrimEnd() -Encoding UTF8
  Write-Host "WORKSPACE_OPERATOR_COMMANDS_REMOVED=PASS"
  Write-Host ("PROFILE_PATH=" + $ProfilePath)
  return
}

$managedBlock = @'
# BEGIN WORKSPACE OPERATOR COMMANDS V1
function global:wop {
  [CmdletBinding()]
  param(
    [ValidateSet("smoke","reset","restart","start","online","stop","offline","status","self-test")]
    [string]$Action = "status",
    [string]$Sha = ""
  )

  $W = Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\DevCheckout"
  if (-not (Test-Path -LiteralPath (Join-Path $W ".git") -PathType Container)) {
    throw "WOP_DEV_CHECKOUT_MISSING:$W"
  }

  if (-not [string]::IsNullOrWhiteSpace($Sha)) {
    git -C $W fetch origin workspace-semantic-execution-migration-v1
    if ($LASTEXITCODE -ne 0) { throw "WOP_FETCH_FAILED" }

    git -C $W cat-file -e ($Sha + "^{commit}")
    if ($LASTEXITCODE -ne 0) { throw "WOP_SHA_NOT_FOUND:$Sha" }

    git -C $W checkout --detach $Sha
    if ($LASTEXITCODE -ne 0) { throw "WOP_CHECKOUT_FAILED:$Sha" }

    $actual = (git -C $W rev-parse HEAD).Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $actual -ne $Sha.ToLowerInvariant()) {
      throw "WOP_CHECKOUT_MISMATCH:$actual"
    }
  }

  $Script = Join-Path $W "operator-bridge\tools\workspace-operator-dev.ps1"
  if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) {
    throw "WOP_SCRIPT_MISSING:$Script"
  }

  $Engine = (Get-Process -Id $PID).Path
  & $Engine -NoLogo -NoProfile -ExecutionPolicy Bypass -File $Script $Action -RepositoryRoot $W
  if ($LASTEXITCODE -ne 0) {
    throw "WOP_ACTION_FAILED:$Action:$LASTEXITCODE"
  }
}

function global:wop-up {
  [CmdletBinding()]
  param([string]$Sha = "")
  wop -Action start -Sha $Sha
}

function global:wop-down {
  [CmdletBinding()]
  param()
  wop -Action stop
}

function global:wop-reset {
  [CmdletBinding()]
  param([string]$Sha = "")
  wop -Action reset -Sha $Sha
}

function global:wop-status {
  [CmdletBinding()]
  param()
  wop -Action status
}

function global:wop-self-test {
  [CmdletBinding()]
  param([string]$Sha = "")
  wop -Action self-test -Sha $Sha
}
# END WORKSPACE OPERATOR COMMANDS V1
'@

$directory = Split-Path -Parent $ProfilePath
if (-not [string]::IsNullOrWhiteSpace($directory)) {
  New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

$prefix = $withoutManagedBlock.TrimEnd()
$newContent = if ([string]::IsNullOrWhiteSpace($prefix)) {
  $managedBlock + [Environment]::NewLine
} else {
  $prefix + [Environment]::NewLine + [Environment]::NewLine +
    $managedBlock + [Environment]::NewLine
}
Set-Content -LiteralPath $ProfilePath -Value $newContent -Encoding UTF8

# Make the commands available in the current PowerShell process as well as future sessions.
Invoke-Expression $managedBlock

Write-Host "WORKSPACE_OPERATOR_COMMANDS_INSTALLED=PASS"
Write-Host ("PROFILE_PATH=" + $ProfilePath)
Write-Host "COMMANDS=wop,wop-up,wop-down,wop-reset,wop-status,wop-self-test"
