[CmdletBinding(DefaultParameterSetName = "Signed")]
param(
    [Parameter(Mandatory = $true)][string]$RepositoryRoot,
    [Parameter(Mandatory = $true)][ValidatePattern("^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")][string]$Version,
    [Parameter(Mandatory = $true)][ValidatePattern("^[0-9a-f]{40}$")][string]$SourceSha,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true, ParameterSetName = "Signed")][string]$SignedXpiPath,
    [Parameter(Mandatory = $true, ParameterSetName = "CiFixture")][switch]$CiUnsignedFixture
)

$ErrorActionPreference = "Stop"
$ExpectedExtensionId = "workspace-control-operator@adamtrott78.local"
$ExpectedNativeHost = "com.workspacecontrol.operator_bridge"
$ExpectedPermissions = @("nativeMessaging", "tabs", "sessions")
$ExpectedFirefoxMinVersion = "153.0"
$ExpectedExtensionVersion = "0.1.0"

function Get-Sha256Lower([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-ArchiveEntrySha256Lower($Archive, [string]$EntryName) {
    $entry = $Archive.GetEntry($EntryName)
    if ($null -eq $entry) { throw "XPI is missing required entry: $EntryName" }
    $stream = $entry.Open()
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($sha.ComputeHash($stream) | ForEach-Object { $_.ToString("x2") }) -join "")
    }
    finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

$repositoryRootPath = [System.IO.Path]::GetFullPath($RepositoryRoot)
$outputRootPath = [System.IO.Path]::GetFullPath($OutputDirectory)
$projectPath = Join-Path $repositoryRootPath "operator-bridge\src\WorkspaceOperator\WorkspaceOperator.csproj"
$firefoxSource = Join-Path $repositoryRootPath "operator-bridge\src\FirefoxAdapter"

$gitHead = (& git -C $repositoryRootPath rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $gitHead -ne $SourceSha.ToLowerInvariant()) {
    throw "SourceSha must equal the exact Git HEAD being packaged."
}

New-Item -ItemType Directory -Path $outputRootPath -Force | Out-Null
$packageRoot = Join-Path $outputRootPath ("workspace-control-operator-" + $Version)
if (Test-Path -LiteralPath $packageRoot) { throw "Package destination already exists: $packageRoot" }

$payloadHelper = Join-Path $packageRoot "payload\helper"
$payloadExtension = Join-Path $packageRoot "payload\extension"
$management = Join-Path $packageRoot "management"
New-Item -ItemType Directory -Path $payloadHelper -Force | Out-Null
New-Item -ItemType Directory -Path $payloadExtension -Force | Out-Null
New-Item -ItemType Directory -Path $management -Force | Out-Null

& dotnet publish $projectPath --configuration Release --runtime win-x64 --self-contained true -p:PublishSingleFile=false --output $payloadHelper
if ($LASTEXITCODE -ne 0) { throw "Self-contained win-x64 publish failed." }

$xpiPath = Join-Path $payloadExtension "workspace-control-operator.xpi"
if ($PSCmdlet.ParameterSetName -eq "Signed") {
    $signedPath = [System.IO.Path]::GetFullPath($SignedXpiPath)
    if (-not (Test-Path -LiteralPath $signedPath -PathType Leaf)) { throw "Signed XPI was not found." }
    Copy-Item -LiteralPath $signedPath -Destination $xpiPath
    $xpiMode = "MOZILLA_SIGNED"
}
else {
    $tempZip = $xpiPath + ".zip"
    Compress-Archive -Path (Join-Path $firefoxSource "*") -DestinationPath $tempZip -CompressionLevel Optimal
    Move-Item -LiteralPath $tempZip -Destination $xpiPath
    $xpiMode = "CI_UNSIGNED_FIXTURE"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($xpiPath)
try {
    $manifestEntry = $archive.GetEntry("manifest.json")
    if ($null -eq $manifestEntry) { throw "XPI is missing manifest.json." }
    $reader = New-Object System.IO.StreamReader($manifestEntry.Open())
    try { $xpiManifest = ($reader.ReadToEnd() | ConvertFrom-Json) }
    finally { $reader.Dispose() }

    if ($xpiManifest.manifest_version -ne 3) { throw "XPI manifest_version must remain 3." }
    if ($xpiManifest.version -ne $ExpectedExtensionVersion) { throw "XPI extension version does not match the frozen baseline." }
    if ($xpiManifest.browser_specific_settings.gecko.id -ne $ExpectedExtensionId) { throw "XPI extension identity does not match the frozen identity." }
    if ($xpiManifest.browser_specific_settings.gecko.strict_min_version -ne $ExpectedFirefoxMinVersion) { throw "XPI minimum Firefox version does not match the frozen baseline." }
    if ((@($xpiManifest.permissions) -join ",") -ne ($ExpectedPermissions -join ",")) { throw "XPI Firefox permissions do not match the frozen allowlist." }
    if ((@($xpiManifest.browser_specific_settings.gecko.data_collection_permissions.required) -join ",") -ne "none") { throw "XPI data collection declaration must remain none." }

    foreach ($forbiddenKey in @("host_permissions", "optional_host_permissions", "content_scripts", "externally_connectable")) {
        if ($xpiManifest.PSObject.Properties.Name -contains $forbiddenKey) { throw "XPI contains forbidden manifest key: $forbiddenKey" }
    }

    foreach ($fileName in @("manifest.json", "adapter_core.js", "background.js")) {
        $sourceHash = Get-Sha256Lower (Join-Path $firefoxSource $fileName)
        $archiveHash = Get-ArchiveEntrySha256Lower $archive $fileName
        if ($sourceHash -ne $archiveHash) { throw "XPI production source mismatch: $fileName" }
    }
}
finally { $archive.Dispose() }

foreach ($name in @("install.ps1", "uninstall.ps1", "rollback.ps1", "SIGNED-XPI-INSTALL.md")) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $management $name)
}

$packagePrefix = $packageRoot.TrimEnd("\") + "\"
$files = @(
    Get-ChildItem -LiteralPath $packageRoot -Recurse -File |
        Where-Object { $_.Name -ne "package.json" } |
        ForEach-Object {
            [ordered]@{
                path = $_.FullName.Substring($packagePrefix.Length).Replace("\", "/")
                sha256 = Get-Sha256Lower $_.FullName
                bytes = $_.Length
            }
        } |
        Sort-Object path
)

$manifest = [ordered]@{
    schema_version = 1
    product_id = "workspace-control-operator-bridge"
    version = $Version
    source_sha = $SourceSha.ToLowerInvariant()
    runtime = "win-x64"
    self_contained = $true
    native_host_name = $ExpectedNativeHost
    extension_id = $ExpectedExtensionId
    extension_version = $ExpectedExtensionVersion
    firefox_min_version = $ExpectedFirefoxMinVersion
    firefox_permissions = $ExpectedPermissions
    xpi_mode = $xpiMode
    xpi_sha256 = Get-Sha256Lower $xpiPath
    files = $files
}

$manifestPath = Join-Path $packageRoot "package.json"
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Output ([pscustomobject]@{ package_root = $packageRoot; package_manifest = $manifestPath; source_sha = $SourceSha.ToLowerInvariant(); version = $Version; xpi_mode = $xpiMode })
