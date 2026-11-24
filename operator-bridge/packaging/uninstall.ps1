[CmdletBinding()]
param([string]$InstallRoot = (Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge"))

$ErrorActionPreference = "Stop"
$ExpectedProductId = "workspace-control-operator-bridge"
$RegistryPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"

function Test-UnderRoot([string]$Path, [string]$Root) {
    $full = [System.IO.Path]::GetFullPath($Path)
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd("\")
    return $full.Equals($rootFull, [System.StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($rootFull + "\", [System.StringComparison]::OrdinalIgnoreCase)
}

$installRootPath = [System.IO.Path]::GetFullPath($InstallRoot)
$markerPath = Join-Path $installRootPath ".workspace-control-operator-owned.json"
if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) { throw "Refusing uninstall: operator ownership marker is missing." }

$marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
if ($marker.product_id -ne $ExpectedProductId -or $marker.scope -ne "current-user") { throw "Refusing uninstall: operator ownership marker is invalid." }

$registryExists = Test-Path -LiteralPath $RegistryPath
if ($registryExists) {
    $registryValue = (Get-Item -LiteralPath $RegistryPath).GetValue("")
    if (-not [string]::IsNullOrWhiteSpace([string]$registryValue) -and -not (Test-UnderRoot ([string]$registryValue) $installRootPath)) { throw "Refusing uninstall: native-host registry value is not owned by this install root." }
}

if ($registryExists) { Remove-Item -LiteralPath $RegistryPath -Recurse -Force }
Remove-Item -LiteralPath $installRootPath -Recurse -Force
Write-Output ([pscustomobject]@{ removed_install_root = $installRootPath; removed_registry_path = $RegistryPath })
