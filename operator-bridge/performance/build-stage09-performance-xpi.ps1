[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepositoryRoot,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = "Stop"
$ExpectedExtensionId = "workspace-control-operator@adamtrott78.local"
$ExpectedExtensionVersion = "0.1.9"
$ExpectedAdapterVersion = "0.1.9-perf"
$FakeWorkerUrl = "http://127.0.0.1:8765/fake-worker.html"

function Get-Sha256Lower([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$output = [System.IO.Path]::GetFullPath($OutputPath)
New-Item -ItemType Directory -Path (Split-Path -Parent $output) -Force | Out-Null

$sourceSha = (& git -C $repo rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $sourceSha -notmatch "^[0-9a-f]{40}$") {
    throw "Stage 09 performance XPI requires an exact Git source SHA."
}

$perf = Join-Path $repo "operator-bridge\performance\FirefoxProfile\extension"
$coreSource = Join-Path $repo "operator-bridge\src\FirefoxAdapter\adapter_core.js"
$work = Join-Path $env:TEMP ("workspace-operator-stage09-xpi-" + [Guid]::NewGuid().ToString("N"))
$stage = Join-Path $work "extension"
New-Item -ItemType Directory -Path $stage -Force | Out-Null

try {
    Copy-Item -LiteralPath (Join-Path $perf "manifest.json") -Destination $stage
    Copy-Item -LiteralPath (Join-Path $perf "background.js") -Destination $stage

    $core = Get-Content -LiteralPath $coreSource -Raw
    $production = 'const WORKER_START_URL = "https://chatgpt.com/";'
    $benchmark = 'const WORKER_START_URL = "' + $FakeWorkerUrl + '";'
    if (-not $core.Contains($production)) {
        throw "Reviewed production worker URL constant was not found."
    }
    $core.Replace($production, $benchmark) |
        Set-Content -LiteralPath (Join-Path $stage "adapter_core.js") -Encoding UTF8

    $manifest = Get-Content -LiteralPath (Join-Path $stage "manifest.json") -Raw | ConvertFrom-Json
    if ($manifest.browser_specific_settings.gecko.id -ne $ExpectedExtensionId) {
        throw "Performance extension ID drifted."
    }
    if ($manifest.version -ne $ExpectedExtensionVersion) {
        throw "Performance extension version drifted."
    }
    if ((@($manifest.permissions) -join ",") -ne "nativeMessaging,tabs,sessions") {
        throw "Performance extension permissions drifted."
    }

    $background = Get-Content -LiteralPath (Join-Path $stage "background.js") -Raw
    if (-not $background.Contains('const ADAPTER_VERSION = "' + $ExpectedAdapterVersion + '";')) {
        throw "Performance adapter handshake version drifted."
    }
    $stagedCore = Get-Content -LiteralPath (Join-Path $stage "adapter_core.js") -Raw
    if ($background.Contains("https://chatgpt.com") -or $stagedCore.Contains("https://chatgpt.com/")) {
        throw "Stage 09 signing input must not retain the production ChatGPT worker URL."
    }

    if (Test-Path -LiteralPath $output) { Remove-Item -LiteralPath $output -Force }
    $zip = $output + ".zip"
    if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
    Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -CompressionLevel Optimal
    Move-Item -LiteralPath $zip -Destination $output

    [ordered]@{
        schema_version = 1
        stage = "impl_09_performance_benchmark_execution"
        artifact_kind = "UNSIGNED_MOZILLA_SIGNING_INPUT"
        source_sha = $sourceSha
        extension_id = $ExpectedExtensionId
        extension_version = $ExpectedExtensionVersion
        adapter_version = $ExpectedAdapterVersion
        fake_worker_url = $FakeWorkerUrl
        xpi_sha256 = Get-Sha256Lower $output
        payload = @("manifest.json", "adapter_core.js", "background.js")
    } | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath ($output + ".json") -Encoding UTF8

    Write-Host "STAGE09_PERFORMANCE_SIGNING_INPUT=PASS"
}
finally {
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
