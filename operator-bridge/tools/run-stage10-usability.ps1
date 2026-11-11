param(
  [Parameter(Mandatory = $true)]
  [string]$RepositoryRoot,
  [Parameter(Mandatory = $true)]
  [ValidateSet("UT-11", "UT-01", "UT-10")]
  [string]$TrialId,
  [string]$ResultPath,
  [int]$DurationSeconds = 900
)

$ErrorActionPreference = "Stop"

$repo = [System.IO.Path]::GetFullPath($RepositoryRoot)
$bridgeRoot = Join-Path $repo "operator-bridge"
$runnerDll = Join-Path $bridgeRoot "integration/bin/Release/net10.0-windows/WorkspaceOperator.IntegrationHarness.dll"
$helperExe = Join-Path $bridgeRoot "src/WorkspaceOperator/bin/Release/net10.0-windows/WorkspaceOperator.exe"
$firefox = "C:\Program Files\Mozilla Firefox\firefox.exe"

if (-not $ResultPath) {
  $ResultPath = Join-Path $repo ("benchmarks\workspace-semantic-execution\operator_bridge\stage10-" + $TrialId.ToLowerInvariant() + "-result.json")
}
$ResultPath = [System.IO.Path]::GetFullPath($ResultPath)
$readyPath = $ResultPath + ".ready.json"

if (Get-Process firefox -ErrorAction SilentlyContinue) {
  throw "Stage 10 usability trial requires no pre-existing Firefox process."
}
if (Get-Process WorkspaceOperator -ErrorAction SilentlyContinue) {
  throw "Stage 10 usability trial requires no pre-existing WorkspaceOperator process."
}
if (-not (Test-Path $firefox)) {
  throw "Stage 10 usability trial requires Firefox to be installed at $firefox."
}

dotnet build (Join-Path $bridgeRoot "WorkspaceOperatorBridge.Integration.slnx") --configuration Release
if ($LASTEXITCODE -ne 0) {
  throw "Stage 10 integration build failed."
}

$work = Join-Path $env:TEMP ("workspace-operator-stage10-" + [guid]::NewGuid().ToString("N"))
New-Item $work -ItemType Directory -Force | Out-Null
$extensionStage = Join-Path $work "extension"
Copy-Item (Join-Path $bridgeRoot "usability\FirefoxProfile\extension") $extensionStage -Recurse
Copy-Item (Join-Path $bridgeRoot "src\FirefoxAdapter\adapter_core.js") (Join-Path $extensionStage "adapter_core.js")

$webExtRoot = Join-Path $work "web-ext-tool"
New-Item $webExtRoot -ItemType Directory -Force | Out-Null
Push-Location $webExtRoot
try {
  npm.cmd init -y | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "npm init failed." }
  npm.cmd install --no-audit --no-fund --save-exact web-ext@10.8.0 | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Pinned web-ext@10.8.0 install failed." }
}
finally {
  Pop-Location
}
$webExt = Join-Path $webExtRoot "node_modules\.bin\web-ext.cmd"

$nativeManifest = Join-Path $work "native-host.json"
[ordered]@{
  name = "com.workspacecontrol.operator_bridge"
  description = "Workspace Control Stage 10 usability native host"
  path = $helperExe
  type = "stdio"
  allowed_extensions = @("workspace-control-operator@adamtrott78.local")
} | ConvertTo-Json -Depth 5 | Set-Content $nativeManifest -Encoding UTF8

$regPath = "HKCU:\Software\Mozilla\NativeMessagingHosts\com.workspacecontrol.operator_bridge"
$regExisted = Test-Path $regPath
$oldValue = if ($regExisted) { (Get-Item -LiteralPath $regPath).GetValue("") } else { $null }

New-Item $regPath -Force | Out-Null
Set-Item -LiteralPath $regPath -Value $nativeManifest

$runnerOut = Join-Path $work "runner.out.log"
$runnerErr = Join-Path $work "runner.err.log"
$webExtOut = Join-Path $work "web-ext.out.log"
$webExtErr = Join-Path $work "web-ext.err.log"
$runner = $null
$webExtProcess = $null

try {
  Remove-Item $ResultPath -Force -ErrorAction SilentlyContinue
  Remove-Item $readyPath -Force -ErrorAction SilentlyContinue

  $runner = Start-Process -FilePath "dotnet" -ArgumentList @(
    $runnerDll,
    "--usability-trial=$TrialId",
    "--result=$ResultPath",
    "--ready=$readyPath",
    "--duration-seconds=$DurationSeconds"
  ) -RedirectStandardOutput $runnerOut -RedirectStandardError $runnerErr -PassThru

  Start-Sleep -Seconds 1
  if ($runner.HasExited) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    throw "Stage 10 usability harness exited during startup."
  }

  $launcher = Join-Path $work "run-web-ext.cmd"
  @"
@echo off
call "$webExt" run --source-dir "$extensionStage" --firefox "$firefox" --no-reload --no-input --arg=-no-remote
"@ | Set-Content $launcher -Encoding ASCII

  $webExtProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/d", "/c", $launcher
  ) -RedirectStandardOutput $webExtOut -RedirectStandardError $webExtErr -PassThru

  $deadline = (Get-Date).AddSeconds(100)
  while (-not (Test-Path $readyPath) -and (Get-Date) -lt $deadline) {
    if ($runner.HasExited) { break }
    Start-Sleep -Milliseconds 250
  }

  if (-not (Test-Path $readyPath)) {
    if (Test-Path $runnerOut) { Get-Content $runnerOut }
    if (Test-Path $runnerErr) { Get-Content $runnerErr }
    if (Test-Path $webExtOut) { Get-Content $webExtOut }
    if (Test-Path $webExtErr) { Get-Content $webExtErr }
    throw "Stage 10 usability harness never reached ready state."
  }

  Write-Host "STAGE10_USABILITY_READY=$TrialId"
  if ($TrialId -eq "UT-11") {
    Write-Host "Bridge is OFF. Use Ctrl+B normally in representative foreground applications for the configured duration. The bridge must not react."
  } else {
    Write-Host "For each cycle: press Ctrl+B, then Ctrl+V, then Enter. Do not manually choose or search browser tabs."
  }

  if (-not $runner.WaitForExit(1800000)) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
    throw "Stage 10 usability trial exceeded the 30-minute bounded execution window."
  }

  if (-not (Test-Path $ResultPath)) {
    throw "Stage 10 usability trial produced no structured result."
  }

  $resultObject = Get-Content $ResultPath -Raw | ConvertFrom-Json
  Get-Content $ResultPath
  if ($resultObject.result -ne "OBJECTIVE_PASS") {
    throw "Stage 10 usability harness reported objective failure."
  }
  if ($runner.ExitCode -ne 0) {
    Write-Warning ("Stage 10 harness process exit code was " + $runner.ExitCode +
      " despite structured OBJECTIVE_PASS; structured result is authoritative.")
  }
}
finally {
  if ($webExtProcess -and -not $webExtProcess.HasExited) {
    Stop-Process -Id $webExtProcess.Id -Force -ErrorAction SilentlyContinue
  }
  if ($runner -and -not $runner.HasExited) {
    Stop-Process -Id $runner.Id -Force -ErrorAction SilentlyContinue
  }

  if ($regExisted) {
    Set-Item -LiteralPath $regPath -Value $oldValue
  } else {
    Remove-Item -LiteralPath $regPath -Recurse -Force -ErrorAction SilentlyContinue
  }

  Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
}
