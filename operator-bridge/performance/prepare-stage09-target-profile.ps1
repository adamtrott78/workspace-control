[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepositoryRoot,
    [Parameter(Mandatory = $true)][string]$SignedXpiPath,
    [string]$FirefoxPath = "C:\Program Files\Mozilla Firefox\firefox.exe",
    [string]$ProfileName = "WorkspaceWorkers",
    [string]$ProfileRoot = (Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Stage09\FirefoxProfiles\WorkspaceWorkers"),
    [switch]$InteractiveInstall,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
$ExpectedExtensionId = "workspace-control-operator@adamtrott78.local"
$ExpectedExtensionVersion = "0.1.9"
$ExpectedAdapterVersion = "0.1.9-perf"
$FakeWorkerUrl = "http://127.0.0.1:8765/fake-worker.html"
$OwnerFile = ".workspace-control-stage09-profile.json"

function Remove-StaleOwnedProfileRegistration {
    param(
        [string]$ProfileName,
        [string]$ExpectedProfilePath
    )

    $profilesIni = Join-Path $env:APPDATA "Mozilla\Firefox\profiles.ini"
    if (-not (Test-Path -LiteralPath $profilesIni -PathType Leaf)) {
        return
    }

    $lines = @(Get-Content -LiteralPath $profilesIni)
    $sectionStart = -1
    $sectionName = $null
    $sectionRelative = $null
    $sectionPath = $null
    $matches = [System.Collections.Generic.List[object]]::new()

    for ($i = 0; $i -le $lines.Count; $i++) {
        $atEnd = $i -eq $lines.Count
        $isHeader = $false
        if (-not $atEnd) {
            $line = [string]$lines[$i]
            $isHeader = $line.StartsWith("[") -and $line.EndsWith("]")
        }

        if ($atEnd -or $isHeader) {
            if ($sectionStart -ge 0 -and $sectionName -eq $ProfileName) {
                $matches.Add([pscustomobject]@{
                    Start = $sectionStart
                    End = $i
                    IsRelative = $sectionRelative
                    Path = $sectionPath
                })
            }

            if ($atEnd) { break }
            $sectionStart = $i
            $sectionName = $null
            $sectionRelative = $null
            $sectionPath = $null
            continue
        }

        if ($sectionStart -lt 0) { continue }
        if ($line.StartsWith("Name=")) {
            $sectionName = $line.Substring(5)
        } elseif ($line.StartsWith("IsRelative=")) {
            $sectionRelative = $line.Substring(11)
        } elseif ($line.StartsWith("Path=")) {
            $sectionPath = $line.Substring(5)
        }
    }

    if ($matches.Count -eq 0) {
        return
    }
    if ($matches.Count -ne 1) {
        throw "Stage 09 found ambiguous WorkspaceWorkers Firefox profile registrations."
    }

    $match = $matches[0]
    if ([string]::IsNullOrWhiteSpace([string]$match.Path)) {
        throw "Stage 09 WorkspaceWorkers Firefox profile registration is missing its path."
    }

    $expectedPath = [System.IO.Path]::GetFullPath($ExpectedProfilePath)
    if ($match.IsRelative -eq "0") {
        $registeredPath = [System.IO.Path]::GetFullPath([string]$match.Path)
        if ($registeredPath -ne $expectedPath) {
            throw "Refusing to remove an absolute WorkspaceWorkers Firefox profile registration outside the owned Stage 09 path."
        }
    } elseif ($match.IsRelative -eq "1") {
        # Firefox Refresh may replace the dedicated custom-path profile with a
        # same-name relative profile under Firefox's normal Profiles root.
        # Reconcile only the registration; never delete the refreshed profile
        # files. The frozen WorkspaceWorkers name remains reserved for Stage 09.
        $firefoxRoot = [System.IO.Path]::GetFullPath(
            (Join-Path $env:APPDATA "Mozilla\Firefox")
        )
        $profilesRoot = [System.IO.Path]::GetFullPath(
            (Join-Path $firefoxRoot "Profiles")
        )
        $registeredPath = [System.IO.Path]::GetFullPath(
            (Join-Path $firefoxRoot ([string]$match.Path))
        )
        $profilesPrefix = $profilesRoot.TrimEnd([char]92) + [char]92
        if (-not $registeredPath.StartsWith(
            $profilesPrefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw "Refusing to remove a relative WorkspaceWorkers registration outside Firefox Profiles."
        }
        Write-Host "STAGE09_TARGET_PROFILE_REFRESH_REGISTRATION_RECONCILED=PASS"
    } else {
        throw "Stage 09 WorkspaceWorkers profile registration has an invalid IsRelative value."
    }

    $remaining = [System.Collections.Generic.List[string]]::new()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($i -lt $match.Start -or $i -ge $match.End) {
            $remaining.Add([string]$lines[$i])
        }
    }

    [System.IO.File]::WriteAllLines(
        $profilesIni,
        [string[]]$remaining,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host "STAGE09_TARGET_PROFILE_STALE_REGISTRATION_RECONCILED=PASS"
}

function Get-ZipText($Archive, [string]$Name) {
    $entry = $Archive.GetEntry($Name)
    if ($null -eq $entry) { throw "Signed Stage 09 XPI is missing $Name." }
    $reader = New-Object System.IO.StreamReader($entry.Open())
    try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}

if ($ProfileName -ne "WorkspaceWorkers") {
    throw "Stage 09 profile name is frozen as WorkspaceWorkers."
}
if (-not (Test-Path -LiteralPath $FirefoxPath -PathType Leaf)) {
    throw "Firefox executable was not found at the reviewed path."
}
if (-not (Test-Path -LiteralPath $SignedXpiPath -PathType Leaf)) {
    throw "Signed Stage 09 performance XPI is missing."
}
if (Get-Process firefox -ErrorAction SilentlyContinue) {
    throw "Stage 09 profile preparation requires Firefox to be closed."
}

$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$profile = [System.IO.Path]::GetFullPath($ProfileRoot)
$xpi = [System.IO.Path]::GetFullPath($SignedXpiPath)
$canonicalXpi = [System.IO.Path]::GetFullPath(
    (Join-Path $env:LOCALAPPDATA "WorkspaceControl\OperatorBridge\Stage09\workspace-control-operator-performance-signed.xpi")
)
$sourceSha = (& git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") {
    throw "Stage 09 profile preparation requires an exact Git source SHA."
}

$expectedManifest = Get-Content -LiteralPath (Join-Path $repo "operator-bridge\performance\FirefoxProfile\extension\manifest.json") -Raw
$expectedBackground = Get-Content -LiteralPath (Join-Path $repo "operator-bridge\performance\FirefoxProfile\extension\background.js") -Raw
$core = Get-Content -LiteralPath (Join-Path $repo "operator-bridge\src\FirefoxAdapter\adapter_core.js") -Raw
$production = 'const WORKER_START_URL = "https://chatgpt.com/";'
$benchmark = 'const WORKER_START_URL = "' + $FakeWorkerUrl + '";'
if (-not $core.Contains($production)) { throw "Reviewed production worker URL constant was not found." }
$expectedCore = $core.Replace($production, $benchmark)

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($xpi)
try {
    $manifestText = Get-ZipText $archive "manifest.json"
    $backgroundText = Get-ZipText $archive "background.js"
    $coreText = Get-ZipText $archive "adapter_core.js"

    $manifest = $manifestText | ConvertFrom-Json
    if ($manifest.browser_specific_settings.gecko.id -ne $ExpectedExtensionId) {
        throw "Signed Stage 09 XPI has the wrong extension ID."
    }
    if ($manifest.version -ne $ExpectedExtensionVersion) {
        throw "Signed Stage 09 XPI has the wrong extension version."
    }
    if ((@($manifest.permissions) -join ",") -ne "nativeMessaging,tabs,sessions") {
        throw "Signed Stage 09 XPI permissions drifted."
    }
    if (-not $backgroundText.Contains('const ADAPTER_VERSION = "' + $ExpectedAdapterVersion + '";')) {
        throw "Signed Stage 09 XPI has the wrong adapter handshake version."
    }

    $normalize = {
        param([string]$Value)
        return $Value.Replace("`r`n", "`n").Trim().TrimStart([char]0xFEFF)
    }
    if ((& $normalize $manifestText) -ne (& $normalize $expectedManifest)) {
        throw "Signed Stage 09 XPI manifest does not match exact repo source."
    }
    if ((& $normalize $backgroundText) -ne (& $normalize $expectedBackground)) {
        throw "Signed Stage 09 XPI background does not match exact repo source."
    }
    if ((& $normalize $coreText) -ne (& $normalize $expectedCore)) {
        throw "Signed Stage 09 XPI adapter core does not match the reviewed fake-worker transform."
    }
    if ($coreText.Contains("https://chatgpt.com/")) {
        throw "Signed Stage 09 XPI retains the production ChatGPT worker URL."
    }
}
finally {
    $archive.Dispose()
}

$ownerPath = Join-Path $profile $OwnerFile
if (Test-Path -LiteralPath $profile) {
    if (-not (Test-Path -LiteralPath $ownerPath -PathType Leaf)) {
        throw "Refusing to mutate an existing Firefox profile not owned by Stage 09."
    }
    $owner = Get-Content -LiteralPath $ownerPath -Raw | ConvertFrom-Json
    if ($owner.owner -ne "workspace-control-stage09" -or $owner.profile_name -ne $ProfileName) {
        throw "Stage 09 Firefox profile ownership marker is invalid."
    }

    if ($VerifyOnly) {
        $extensionsStatePath = Join-Path $profile "extensions.json"
        if (-not (Test-Path -LiteralPath $extensionsStatePath -PathType Leaf)) {
            throw "Stage 09 WorkspaceWorkers profile is missing Firefox extensions.json runtime state."
        }

        $extensionsState = Get-Content -LiteralPath $extensionsStatePath -Raw | ConvertFrom-Json
        $addonMatches = @($extensionsState.addons | Where-Object { $_.id -eq $ExpectedExtensionId })
        if ($addonMatches.Count -ne 1) {
            throw "Stage 09 performance adapter is not uniquely present in Firefox runtime add-on state."
        }

        $addon = $addonMatches[0]
        $addonState = [ordered]@{
            extension_id = [string]$addon.id
            version = [string]$addon.version
            active = [bool]$addon.active
            user_disabled = [bool]$addon.userDisabled
            app_disabled = [bool]$addon.appDisabled
            signed_state = $addon.signedState
        }
        Write-Host ("STAGE09_TARGET_PROFILE_ADDON_STATE=" + ($addonState | ConvertTo-Json -Compress))

        if ([string]$addon.version -ne $ExpectedExtensionVersion -or
            -not [bool]$addon.active -or
            [bool]$addon.userDisabled -or
            [bool]$addon.appDisabled) {
            throw "Stage 09 performance adapter is not active/enabled in the WorkspaceWorkers Firefox profile."
        }
    }
}
else {
    if ($VerifyOnly) {
        throw "Stage 09 owned WorkspaceWorkers profile has not been prepared yet."
    }
    Remove-StaleOwnedProfileRegistration -ProfileName $ProfileName -ExpectedProfilePath $profile
    New-Item -ItemType Directory -Path (Split-Path -Parent $profile) -Force | Out-Null
    $createArgs = @("-CreateProfile", ('"' + $ProfileName + ' ' + $profile + '"'))
    $create = Start-Process -FilePath $FirefoxPath -ArgumentList $createArgs -PassThru -Wait
    if ($create.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $profile)) {
        throw "Firefox failed to create the dedicated Stage 09 WorkspaceWorkers profile."
    }
    [ordered]@{
        schema_version = 1
        owner = "workspace-control-stage09"
        profile_name = $ProfileName
    } | ConvertTo-Json | Set-Content -LiteralPath $ownerPath -Encoding UTF8
}

[ordered]@{
    schema_version = 1
    stage = "impl_09_performance_benchmark_execution"
    source_sha = $sourceSha
    profile_name = $ProfileName
    profile_root = $profile
    extension_id = $ExpectedExtensionId
    extension_version = $ExpectedExtensionVersion
    adapter_version = $ExpectedAdapterVersion
    signed_xpi_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $xpi).Hash.ToLowerInvariant()
} | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $profile "stage09-profile-state.json") -Encoding UTF8

if ($InteractiveInstall) {
    if ($VerifyOnly) {
        throw "-InteractiveInstall and -VerifyOnly are mutually exclusive."
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $canonicalXpi) -Force | Out-Null
    if ($xpi -ne $canonicalXpi) {
        Copy-Item -LiteralPath $xpi -Destination $canonicalXpi -Force
        $xpi = $canonicalXpi
    }
    Start-Process -FilePath $FirefoxPath -ArgumentList @(
        "-P", $ProfileName, "-no-remote", ('"' + $xpi + '"')
    ) | Out-Null
    Write-Host "STAGE09_TARGET_PROFILE_INSTALL_UI_OPENED=PASS"
    Write-Host "Complete the normal Firefox signed-add-on confirmation, then close Firefox before target execution."
    return
}

Write-Host "STAGE09_TARGET_PROFILE_VERIFIED=PASS"
