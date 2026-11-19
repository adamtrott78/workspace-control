[CmdletBinding()]
param(
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

$installRootPath = [System.IO.Path]::GetFullPath($InstallRoot)
$markerPath = Join-Path $installRootPath ".workspace-control-operator-owned.json"
$statePath = Join-Path $installRootPath "install-state.json"
if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf) -or -not (Test-Path -LiteralPath $statePath -PathType Leaf)) { throw "Rollback requires an owned installed baseline." }

$marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
if ($marker.product_id -ne $ExpectedProductId -or $marker.scope -ne "current-user") { throw "Install root ownership marker is invalid." }

$oldStateRaw = Get-Content -LiteralPath $statePath -Raw
$state = $oldStateRaw | ConvertFrom-Json
$previousVersion = [string]$state.previous_version
if ([string]::IsNullOrWhiteSpace($previousVersion) -or $previousVersion -notmatch "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$") { throw "No valid previous release is available for rollback." }

$previousRelease = Join-Path (Join-Path $installRootPath "releases") $previousVersion
$manifestPath = Join-Path $previousRelease "package.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Previous release package.json is missing." }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

if ($manifest.product_id -ne $ExpectedProductId -or $manifest.native_host_name -ne $ExpectedNativeHost -or $manifest.extension_id -ne $ExpectedExtensionId -or (@($manifest.firefox_permissions) -join ",") -ne ($ExpectedPermissions -join ",")) { throw "Previous release identity does not match the frozen baseline." }
if ($manifest.xpi_mode -ne "MOZILLA_SIGNED" -and -not ($AllowCiUnsignedFixture -and $manifest.xpi_mode -eq "CI_UNSIGNED_FIXTURE")) { throw "Rollback target is not an accepted signed production package." }

foreach ($entry in @($manifest.files)) {
    $relative = [string]$entry.path
    if ([System.IO.Path]::IsPathRooted($relative) -or $relative -match "(^|[\\/])\.\.([\\/]|$)") { throw "Previous release contains an unsafe relative path." }
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $previousRelease ($relative.Replace("/", "\"))))
    if (-not (Test-UnderRoot $candidate $previousRelease) -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Previous release file is missing or out of bounds: $relative" }
    if ((Get-Sha256Lower $candidate) -ne ([string]$entry.sha256).ToLowerInvariant()) { throw "Previous release hash mismatch: $relative" }
}

$previousNativeManifest = Join-Path $previousRelease "native-host.json"
$previousHelper = Join-Path $previousRelease "payload\helper\WorkspaceOperator.exe"
$previousXpi = Join-Path $previousRelease "payload\extension\workspace-control-operator.xpi"
$nativeManifest = Get-Content -LiteralPath $previousNativeManifest -Raw | ConvertFrom-Json
if ($nativeManifest.name -ne $ExpectedNativeHost -or $nativeManifest.path -ne $previousHelper -or (@($nativeManifest.allowed_extensions) -join ",") -ne $ExpectedExtensionId) { throw "Previous native-host manifest is invalid." }

$hadRegistryKey = Test-Path -LiteralPath $RegistryPath
$oldRegistryValue = $null
if ($hadRegistryKey) { $oldRegistryValue = (Get-Item -LiteralPath $RegistryPath).GetValue("") }

$newState = [ordered]@{
    schema_version = 1
    product_id = $ExpectedProductId
    active_version = $previousVersion
    active_source_sha = [string]$manifest.source_sha
    previous_version = [string]$state.active_version
    previous_source_sha = [string]$state.active_source_sha
}
$stateTemp = Join-Path $installRootPath ("install-state." + [Guid]::NewGuid().ToString("N") + ".tmp")
$newState | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $stateTemp -Encoding UTF8

try {
    New-Item -ItemType Directory -Path $RegistryPath -Force | Out-Null
    Set-Item -LiteralPath $RegistryPath -Value $previousNativeManifest
    Move-Item -LiteralPath $stateTemp -Destination $statePath -Force
}
catch {
    if ($hadRegistryKey) {
        New-Item -ItemType Directory -Path $RegistryPath -Force | Out-Null
        Set-Item -LiteralPath $RegistryPath -Value $oldRegistryValue
    }
    elseif (Test-Path -LiteralPath $RegistryPath) { Remove-Item -LiteralPath $RegistryPath -Recurse -Force }
    $oldStateRaw | Set-Content -LiteralPath $statePath -Encoding UTF8
    throw
}

$rootManagement = Join-Path $installRootPath "management"
New-Item -ItemType Directory -Path $rootManagement -Force | Out-Null
Copy-Item -Path (Join-Path $previousRelease "management\*") -Destination $rootManagement -Recurse -Force

Write-Output ([pscustomobject]@{ active_version = $previousVersion; source_sha = [string]$manifest.source_sha; helper_path = $previousHelper; xpi_path = $previousXpi; native_host_manifest = $previousNativeManifest; registry_path = $RegistryPath })
