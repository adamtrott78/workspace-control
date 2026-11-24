[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepositoryRoot,
    [Parameter(Mandatory = $true)][string]$ResultPath
)

$ErrorActionPreference = "Stop"
$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$result = [System.IO.Path]::GetFullPath($ResultPath)
$resultDirectory = Split-Path -Parent $result
New-Item -ItemType Directory -Path $resultDirectory -Force | Out-Null

$sourceSha = $env:OPERATOR_BRIDGE_SOURCE_SHA
if ([string]::IsNullOrWhiteSpace($sourceSha)) { $sourceSha = (& git -C $repo rev-parse HEAD).Trim() }
if ($sourceSha -notmatch "^[0-9a-f]{40}$") { throw "Stage 08 smoke requires an exact source SHA." }
$gitHead = (& git -C $repo rev-parse HEAD).Trim()
if ($gitHead -ne $sourceSha) { throw "Stage 08 smoke source SHA does not equal checked-out Git HEAD." }

$buildRoot = Join-Path $env:RUNNER_TEMP ("workspace-operator-stage08-build-" + [Guid]::NewGuid().ToString("N"))
$installRoot = Join-Path $env:RUNNER_TEMP ("workspace-operator-stage08-install-" + [Guid]::NewGuid().ToString("N"))
$outsideSentinelRoot = Join-Path $env:RUNNER_TEMP ("workspace-operator-stage08-outside-" + [Guid]::NewGuid().ToString("N"))
$outsideSentinel = Join-Path $outsideSentinelRoot "sentinel.txt"
$profileSentinelRoot = Join-Path (Join-Path $env:APPDATA "Mozilla\Firefox\Profiles") ("stage08-unrelated-" + [Guid]::NewGuid().ToString("N"))
$profileSentinel = Join-Path $profileSentinelRoot "sentinel.txt"
$hostRegistry = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
$siblingRegistry = "HKCU:\Software\Mozilla\NativeMessagingHosts\stage08-unrelated-sentinel"

if (Test-Path -LiteralPath $hostRegistry) { throw "Stage 08 smoke refuses to overwrite a pre-existing native-host registration." }

New-Item -ItemType Directory -Path $outsideSentinelRoot -Force | Out-Null
"outside-do-not-touch" | Set-Content -LiteralPath $outsideSentinel -Encoding UTF8
New-Item -ItemType Directory -Path $profileSentinelRoot -Force | Out-Null
"profile-do-not-touch" | Set-Content -LiteralPath $profileSentinel -Encoding UTF8
New-Item -ItemType Directory -Path $siblingRegistry -Force | Out-Null
Set-Item -LiteralPath $siblingRegistry -Value "registry-do-not-touch"

$versionA = "0.8.0-ci-a"
$versionB = "0.8.0-ci-b"

try {
    $packageAResult = & (Join-Path $repo "operator-bridge\packaging\build-package.ps1") -RepositoryRoot $repo -Version $versionA -SourceSha $sourceSha -OutputDirectory $buildRoot -CiUnsignedFixture
    $packageBResult = & (Join-Path $repo "operator-bridge\packaging\build-package.ps1") -RepositoryRoot $repo -Version $versionB -SourceSha $sourceSha -OutputDirectory $buildRoot -CiUnsignedFixture

    $packageA = [string]$packageAResult.package_root
    $packageB = [string]$packageBResult.package_root
    $manifestAPath = Join-Path $packageA "package.json"
    $manifestBPath = Join-Path $packageB "package.json"
    $manifestA = Get-Content -LiteralPath $manifestAPath -Raw | ConvertFrom-Json
    $manifestB = Get-Content -LiteralPath $manifestBPath -Raw | ConvertFrom-Json

    Copy-Item -LiteralPath $manifestAPath -Destination (Join-Path $resultDirectory "stage08-package-a.json") -Force
    Copy-Item -LiteralPath $manifestBPath -Destination (Join-Path $resultDirectory "stage08-package-b.json") -Force

    $installA = & (Join-Path $packageA "management\install.ps1") -PackageRoot $packageA -InstallRoot $installRoot -AllowCiUnsignedFixture
    $stateA = Get-Content -LiteralPath (Join-Path $installRoot "install-state.json") -Raw | ConvertFrom-Json
    if ($stateA.active_version -ne $versionA -or $stateA.previous_version) { throw "Clean install state is incorrect." }
    $registryA = (Get-Item -LiteralPath $hostRegistry).GetValue("")
    if ($registryA -ne $installA.native_host_manifest) { throw "Clean install native-host registration failed." }

    $installB = & (Join-Path $packageB "management\install.ps1") -PackageRoot $packageB -InstallRoot $installRoot -AllowCiUnsignedFixture
    $stateB = Get-Content -LiteralPath (Join-Path $installRoot "install-state.json") -Raw | ConvertFrom-Json
    $registryB = (Get-Item -LiteralPath $hostRegistry).GetValue("")
    if ($stateB.active_version -ne $versionB -or $stateB.previous_version -ne $versionA -or $registryB -eq $registryA) { throw "Upgrade smoke failed." }

    $rollback = & (Join-Path $installRoot "management\rollback.ps1") -InstallRoot $installRoot -AllowCiUnsignedFixture
    $stateRollback = Get-Content -LiteralPath (Join-Path $installRoot "install-state.json") -Raw | ConvertFrom-Json
    $registryRollback = (Get-Item -LiteralPath $hostRegistry).GetValue("")
    if ($stateRollback.active_version -ne $versionA -or $stateRollback.previous_version -ne $versionB -or $registryRollback -ne $registryA -or $rollback.xpi_path -ne $installA.xpi_path) { throw "Rollback did not restore the previous helper/XPI release." }

    & (Join-Path $installRoot "management\uninstall.ps1") -InstallRoot $installRoot | Out-Null

    if (Test-Path -LiteralPath $installRoot) { throw "Uninstall did not remove the owned install root." }
    if (Test-Path -LiteralPath $hostRegistry) { throw "Uninstall did not remove the dedicated native-host key." }
    if ((Get-Content -LiteralPath $outsideSentinel -Raw).Trim() -ne "outside-do-not-touch") { throw "Uninstall mutated unrelated filesystem state." }
    if ((Get-Content -LiteralPath $profileSentinel -Raw).Trim() -ne "profile-do-not-touch") { throw "Firefox profile sentinel changed." }
    if ((Get-Item -LiteralPath $siblingRegistry).GetValue("") -ne "registry-do-not-touch") { throw "Sibling registry sentinel changed." }

    $evidence = [ordered]@{
        schema_version = 1
        stage = "impl_08_packaging_install_update_rollback"
        source_sha = $sourceSha
        package_a_version = $versionA
        package_b_version = $versionB
        package_a_manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestAPath).Hash.ToLowerInvariant()
        package_b_manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestBPath).Hash.ToLowerInvariant()
        package_a_xpi_sha256 = [string]$manifestA.xpi_sha256
        package_b_xpi_sha256 = [string]$manifestB.xpi_sha256
        extension_id = "workspace-control-operator@adamtrott78.local"
        firefox_permissions = @("nativeMessaging", "tabs", "sessions")
        native_host_name = "com.workspacecontrol.operator_bridge"
        self_contained_win_x64 = "PASS"
        clean_install_smoke = "PASS"
        native_host_registration = "PASS"
        upgrade_smoke = "PASS"
        rollback_previous_helper_xpi = "PASS"
        uninstall_owned_scope_only = "PASS"
        unrelated_filesystem_unchanged = "PASS"
        unrelated_registry_unchanged = "PASS"
        unrelated_firefox_profile_unchanged = "PASS"
        admin_required_by_install_surface = $false
        automatic_self_updater = $false
        direct_firefox_profile_mutation = $false
        ci_xpi_mode = "CI_UNSIGNED_FIXTURE"
        signed_xpi_ci_claim = "NOT_CLAIMED"
        signed_xpi_production_flow = "MANUAL_FIREFOX_SIGNATURE_VERIFICATION_REQUIRED"
    }
    $evidence | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $result -Encoding UTF8
    Write-Host ("STAGE08_PACKAGING_RESULT=" + ($evidence | ConvertTo-Json -Compress -Depth 6))
}
finally {
    if (Test-Path -LiteralPath $hostRegistry) { Remove-Item -LiteralPath $hostRegistry -Recurse -Force }
    if (Test-Path -LiteralPath $siblingRegistry) { Remove-Item -LiteralPath $siblingRegistry -Recurse -Force }
    if (Test-Path -LiteralPath $installRoot) { Remove-Item -LiteralPath $installRoot -Recurse -Force }
    if (Test-Path -LiteralPath $outsideSentinelRoot) { Remove-Item -LiteralPath $outsideSentinelRoot -Recurse -Force }
    if (Test-Path -LiteralPath $profileSentinelRoot) { Remove-Item -LiteralPath $profileSentinelRoot -Recurse -Force }
    if (Test-Path -LiteralPath $buildRoot) { Remove-Item -LiteralPath $buildRoot -Recurse -Force }
}
