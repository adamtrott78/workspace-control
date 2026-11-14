[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PackageRoot,
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge"),
    [switch]$AllowCiUnsignedFixture
)

$ErrorActionPreference = "Stop"
$ExpectedProductId = "workspace-control-operator-bridge"
$ExpectedExtensionId = "workspace-control-operator@adamtrott78.local"
$ExpectedNativeHost = "com.workspacecontrol.operator_bridge"
$ExpectedPermissions = @("nativeMessaging", "tabs", "sessions")
$RegistryPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"

function Get-Sha256Lower([string]$Path) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
function Test-UnderRoot([string]$Path, [string]$Root) {
    $full = [System.IO.Path]::GetFullPath($Path)
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd("\")
    return $full.Equals($rootFull, [System.StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($rootFull + "\", [System.StringComparison]::OrdinalIgnoreCase)
}
function Get-RelativePackagePath([string]$FullPath, [string]$Root) {
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd("\") + "\"
    return ([System.IO.Path]::GetFullPath($FullPath).Substring($rootFull.Length)).Replace("\", "/")
}

$packageRootPath = [System.IO.Path]::GetFullPath($PackageRoot)
$installRootPath = [System.IO.Path]::GetFullPath($InstallRoot)
$manifestPath = Join-Path $packageRootPath "package.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "package.json is required." }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

if ($manifest.schema_version -ne 1 -or $manifest.product_id -ne $ExpectedProductId) { throw "Unsupported package contract." }
if ($manifest.runtime -ne "win-x64" -or -not $manifest.self_contained) { throw "Package must be a self-contained win-x64 release." }
if ($manifest.native_host_name -ne $ExpectedNativeHost -or $manifest.extension_id -ne $ExpectedExtensionId) { throw "Package identity does not match the frozen baseline." }
if ((@($manifest.firefox_permissions) -join ",") -ne ($ExpectedPermissions -join ",")) { throw "Package Firefox permissions do not match the frozen baseline." }
if ($manifest.version -notmatch "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$") { throw "Package version is not path-safe." }
if ($manifest.source_sha -notmatch "^[0-9a-f]{40}$") { throw "Package source SHA is invalid." }
if ($manifest.xpi_mode -ne "MOZILLA_SIGNED" -and -not ($AllowCiUnsignedFixture -and $manifest.xpi_mode -eq "CI_UNSIGNED_FIXTURE")) { throw "Production install requires a package marked MOZILLA_SIGNED." }

$declaredPaths = @($manifest.files | ForEach-Object { [string]$_.path } | Sort-Object)
$actualPaths = @(
    Get-ChildItem -LiteralPath $packageRootPath -Recurse -File |
        Where-Object { $_.Name -ne "package.json" } |
        ForEach-Object { Get-RelativePackagePath $_.FullName $packageRootPath } |
        Sort-Object
)
if (($declaredPaths -join "|") -ne ($actualPaths -join "|")) { throw "Package file inventory does not match package.json." }

foreach ($entry in @($manifest.files)) {
    $relative = [string]$entry.path
    if ([System.IO.Path]::IsPathRooted($relative) -or $relative -match "(^|[\\/])\.\.([\\/]|$)") { throw "Package contains an unsafe relative path." }
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $packageRootPath ($relative.Replace("/", "\"))))
    if (-not (Test-UnderRoot $candidate $packageRootPath) -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Package file is missing or out of bounds: $relative" }
    if ((Get-Sha256Lower $candidate) -ne ([string]$entry.sha256).ToLowerInvariant()) { throw "Package hash mismatch: $relative" }
}

$xpiPathInPackage = Join-Path $packageRootPath "payload\extension\workspace-control-operator.xpi"
if ((Get-Sha256Lower $xpiPathInPackage) -ne ([string]$manifest.xpi_sha256).ToLowerInvariant()) { throw "XPI hash does not match package.json." }

$markerPath = Join-Path $installRootPath ".workspace-control-operator-owned.json"
$statePath = Join-Path $installRootPath "install-state.json"
$releasesRoot = Join-Path $installRootPath "releases"

if (Test-Path -LiteralPath $installRootPath) {
    if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) { throw "Install root exists without the operator ownership marker." }
    $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
    if ($marker.product_id -ne $ExpectedProductId -or $marker.scope -ne "current-user") { throw "Install root ownership marker is invalid." }
}
else {
    New-Item -ItemType Directory -Path $installRootPath -Force | Out-Null
    [ordered]@{ schema_version = 1; product_id = $ExpectedProductId; scope = "current-user" } | ConvertTo-Json | Set-Content -LiteralPath $markerPath -Encoding UTF8
}

New-Item -ItemType Directory -Path $releasesRoot -Force | Out-Null
$releasePath = Join-Path $releasesRoot ([string]$manifest.version)
if (Test-Path -LiteralPath $releasePath) { throw "Release already exists; existing releases are immutable." }

$previousVersion = $null
$previousSourceSha = $null
$oldStateRaw = $null
if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $oldStateRaw = Get-Content -LiteralPath $statePath -Raw
    $oldState = $oldStateRaw | ConvertFrom-Json
    $previousVersion = [string]$oldState.active_version
    $previousSourceSha = [string]$oldState.active_source_sha
}

$staging = Join-Path $releasesRoot (".staging-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $staging -Force | Out-Null
try {
    Copy-Item -LiteralPath (Join-Path $packageRootPath "payload") -Destination $staging -Recurse
    Copy-Item -LiteralPath (Join-Path $packageRootPath "management") -Destination $staging -Recurse
    Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $staging "package.json")

    $helperPath = Join-Path $staging "payload\helper\WorkspaceOperator.exe"
    $xpiPath = Join-Path $staging "payload\extension\workspace-control-operator.xpi"
    if (-not (Test-Path -LiteralPath $helperPath -PathType Leaf) -or -not (Test-Path -LiteralPath $xpiPath -PathType Leaf)) { throw "Package payload is incomplete." }

    $nativeManifestPath = Join-Path $staging "native-host.json"
    [ordered]@{
        name = $ExpectedNativeHost
        description = "Workspace Control Operator Browser Adapter"
        path = $helperPath
        type = "stdio"
        allowed_extensions = @($ExpectedExtensionId)
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $nativeManifestPath -Encoding UTF8

    Move-Item -LiteralPath $staging -Destination $releasePath
}
catch {
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
    throw
}

$nativeManifestPath = Join-Path $releasePath "native-host.json"
$helperPath = Join-Path $releasePath "payload\helper\WorkspaceOperator.exe"
$xpiPath = Join-Path $releasePath "payload\extension\workspace-control-operator.xpi"

[ordered]@{
    name = $ExpectedNativeHost
    description = "Workspace Control Operator Browser Adapter"
    path = $helperPath
    type = "stdio"
    allowed_extensions = @($ExpectedExtensionId)
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $nativeManifestPath -Encoding UTF8

$hadRegistryKey = Test-Path -LiteralPath $RegistryPath
$oldRegistryValue = $null
if ($hadRegistryKey) { $oldRegistryValue = (Get-Item -LiteralPath $RegistryPath).GetValue("") }

$newState = [ordered]@{
    schema_version = 1
    product_id = $ExpectedProductId
    active_version = [string]$manifest.version
    active_source_sha = [string]$manifest.source_sha
    previous_version = $previousVersion
    previous_source_sha = $previousSourceSha
}
$stateTemp = Join-Path $installRootPath ("install-state." + [Guid]::NewGuid().ToString("N") + ".tmp")
$newState | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $stateTemp -Encoding UTF8

try {
    New-Item -ItemType Directory -Path $RegistryPath -Force | Out-Null
    Set-Item -LiteralPath $RegistryPath -Value $nativeManifestPath
    Move-Item -LiteralPath $stateTemp -Destination $statePath -Force
}
catch {
    if ($hadRegistryKey) {
        New-Item -ItemType Directory -Path $RegistryPath -Force | Out-Null
        Set-Item -LiteralPath $RegistryPath -Value $oldRegistryValue
    }
    elseif (Test-Path -LiteralPath $RegistryPath) { Remove-Item -LiteralPath $RegistryPath -Recurse -Force }

    if ($null -ne $oldStateRaw) { $oldStateRaw | Set-Content -LiteralPath $statePath -Encoding UTF8 }
    elseif (Test-Path -LiteralPath $statePath) { Remove-Item -LiteralPath $statePath -Force }

    if (Test-Path -LiteralPath $releasePath) { Remove-Item -LiteralPath $releasePath -Recurse -Force }
    throw
}

$rootManagement = Join-Path $installRootPath "management"
New-Item -ItemType Directory -Path $rootManagement -Force | Out-Null
Copy-Item -Path (Join-Path $releasePath "management\*") -Destination $rootManagement -Recurse -Force

Write-Output ([pscustomobject]@{ active_version = [string]$manifest.version; source_sha = [string]$manifest.source_sha; helper_path = $helperPath; xpi_path = $xpiPath; native_host_manifest = $nativeManifestPath; registry_path = $RegistryPath })
