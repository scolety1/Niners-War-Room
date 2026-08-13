[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$desktopRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $desktopRoot
$entryPoint = Join-Path $repoRoot "scripts\run_nwr_desktop_api.py"
$iconPath = Join-Path $repoRoot "assets\branding\nwr_desktop_icon.ico"
$outputRoot = Join-Path $desktopRoot "binaries"
$sidecarBaseName = "nwr-desktop-api-x86_64-pc-windows-msvc"
$outputPath = Join-Path $outputRoot "$sidecarBaseName.exe"
$receiptPath = Join-Path $outputRoot "$sidecarBaseName.exe.sha256"
$tempRoot = Join-Path $repoRoot ".codex-tmp"
$workRoot = Join-Path $tempRoot "pyinstaller-build"
$stagingRoot = Join-Path $tempRoot "pyinstaller-dist"
$stagedOutputPath = Join-Path $stagingRoot "$sidecarBaseName.exe"

function Assert-BuildHost {
    $runtimeInformation = [System.Runtime.InteropServices.RuntimeInformation]
    if (-not $runtimeInformation::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)) {
        throw "The desktop sidecar can only be built on Windows."
    }
    if ($runtimeInformation::OSArchitecture -ne [System.Runtime.InteropServices.Architecture]::X64) {
        throw "The desktop sidecar filename targets x86_64-pc-windows-msvc; an x64 build host is required."
    }
}

function Write-IntegrityReceipt {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BinaryPath
    )

    $hash = (Get-FileHash -LiteralPath $BinaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath $receiptPath -Encoding Ascii -Value "$hash *$sidecarBaseName.exe"
    Write-Host "SHA-256: $hash"
    Write-Host "Receipt: $receiptPath"
}

function Assert-SidecarSmokeTest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BinaryPath
    )

    & $BinaryPath --help *> $null
    $helpExitCode = $LASTEXITCODE
    if ($helpExitCode -ne 0) {
        throw "The sidecar failed its --help smoke test with exit code ${helpExitCode}: $BinaryPath"
    }
}

Assert-BuildHost

foreach ($requiredPath in @($entryPoint, $iconPath, (Join-Path $repoRoot "pyproject.toml"))) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required sidecar build input is missing: $requiredPath"
    }
}

$sourceRoot = Join-Path $repoRoot "src"
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "Required sidecar source directory is missing: $sourceRoot"
}

$inputPaths = @(
    $PSCommandPath
    $entryPoint
    $iconPath
    (Join-Path $repoRoot "pyproject.toml")
)
$inputPaths += @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Filter "*.py" | Select-Object -ExpandProperty FullName)
$latestInput = $inputPaths |
    ForEach-Object { Get-Item -LiteralPath $_ } |
    Sort-Object -Property LastWriteTimeUtc -Descending |
    Select-Object -First 1

if (-not $Force -and (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
    $existingOutput = Get-Item -LiteralPath $outputPath
    if ($existingOutput.Length -gt 1MB -and $existingOutput.LastWriteTimeUtc -ge $latestInput.LastWriteTimeUtc) {
        Assert-SidecarSmokeTest -BinaryPath $outputPath
        Write-Host "Sidecar is current: $outputPath"
        Write-IntegrityReceipt -BinaryPath $outputPath
        exit 0
    }
}

$uvCommand = Get-Command "uv" -CommandType Application -ErrorAction SilentlyContinue
if ($null -eq $uvCommand) {
    throw "uv is required to build the frozen Python sidecar. Install uv and retry."
}

New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
New-Item -ItemType Directory -Path $workRoot -Force | Out-Null
New-Item -ItemType Directory -Path $stagingRoot -Force | Out-Null

$pyInstallerArguments = @(
    "run"
    "--isolated"
    "--no-project"
    "--python"
    "3.14"
    "--with"
    "pyinstaller==6.21.0"
    "--with"
    "pandas==3.0.5"
    "--with"
    "nflreadpy==0.1.5"
    "--with"
    "numpy==2.5.2"
    "--with"
    "pydantic==2.13.4"
    "--with"
    "streamlit==1.61.1"
    "pyinstaller"
    "--noconfirm"
    "--clean"
    "--onefile"
    "--console"
    "--name"
    $sidecarBaseName
    "--distpath"
    $stagingRoot
    "--workpath"
    $workRoot
    "--specpath"
    $tempRoot
    "--paths"
    $repoRoot
    "--icon"
    $iconPath
    $entryPoint
)

Write-Host "Building $sidecarBaseName in an isolated pinned Python 3.14 environment..."
$buildExitCode = $null
Push-Location $repoRoot
try {
    & $uvCommand.Source @pyInstallerArguments
    $buildExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($buildExitCode -ne 0) {
    throw "PyInstaller failed with exit code $buildExitCode."
}
if (-not (Test-Path -LiteralPath $stagedOutputPath -PathType Leaf)) {
    throw "PyInstaller reported success but did not emit: $stagedOutputPath"
}

$stagedOutput = Get-Item -LiteralPath $stagedOutputPath
if ($stagedOutput.Length -le 1MB) {
    throw "The staged sidecar is unexpectedly small ($($stagedOutput.Length) bytes): $stagedOutputPath"
}

Assert-SidecarSmokeTest -BinaryPath $stagedOutputPath

Copy-Item -LiteralPath $stagedOutputPath -Destination $outputPath -Force
Write-IntegrityReceipt -BinaryPath $outputPath
Write-Host "Sidecar ready: $outputPath"
