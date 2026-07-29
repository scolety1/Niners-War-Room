param(
    [string] $SafeRoot = "C:\NWR\Niners-War-Room\local_exports\refresh_data\dynastyprocess_market_baseline"
)

$ErrorActionPreference = "Stop"

$RepoRoot = "C:\NWR\Niners-War-Room"
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$RefreshScript = Join-Path $RepoRoot "scripts\refresh_dynastyprocess_market_baseline_v1.py"
$ExpectedSafeRoot = Join-Path $RepoRoot "local_exports\refresh_data\dynastyprocess_market_baseline"
$CurrentPointer = Join-Path $ExpectedSafeRoot "current_generation.json"
$LogRoot = "C:\NWR_SHARED_DATA\market_sources\dynastyprocess\logs"

New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $LogRoot "dynastyprocess_refresh_$Timestamp.stdout.log"
$StderrLog = Join-Path $LogRoot "dynastyprocess_refresh_$Timestamp.stderr.log"

function Write-CompactStatus {
    param(
        [string] $ExitCode
    )

    $PointerStatus = if (Test-Path -LiteralPath $CurrentPointer -PathType Leaf) {
        "PRESENT"
    } else {
        "MISSING"
    }
    Write-Host "exit_code=$ExitCode current_pointer=$PointerStatus safe_root=$ExpectedSafeRoot"
    Write-Host "stdout_log=$StdoutLog"
    Write-Host "stderr_log=$StderrLog"
}

function Assert-SafeRoot {
    $CanonicalExpected = [System.IO.Path]::GetFullPath($ExpectedSafeRoot)
    $CanonicalRequested = [System.IO.Path]::GetFullPath($SafeRoot)
    if ($SafeRoot.StartsWith("\\?\", [System.StringComparison]::Ordinal) -or
        $SafeRoot.StartsWith("\\.\", [System.StringComparison]::Ordinal)) {
        throw "Device-path aliases are prohibited for SafeRoot."
    }
    if (-not [System.String]::Equals(
        $CanonicalRequested,
        $CanonicalExpected,
        [System.StringComparison]::Ordinal
    )) {
        throw "SafeRoot must exactly match $CanonicalExpected"
    }
    $Current = Get-Item -LiteralPath $RepoRoot -Force
    while ($null -ne $Current) {
        if (($Current.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "SafeRoot ancestor is a reparse point: $($Current.FullName)"
        }
        if ($Current.FullName -eq [System.IO.Path]::GetPathRoot($Current.FullName)) {
            break
        }
        $Current = $Current.Parent
    }
}

try {
    if (-not (Test-Path -LiteralPath $RepoRoot)) {
        throw "Repo root not found: $RepoRoot"
    }
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        throw "Python executable not found: $PythonExe"
    }
    if (-not (Test-Path -LiteralPath $RefreshScript)) {
        throw "Refresh script not found: $RefreshScript"
    }
    Assert-SafeRoot

    Push-Location $RepoRoot
    try {
        & $PythonExe $RefreshScript --safe-root $SafeRoot 1> $StdoutLog 2> $StderrLog
        $ExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    Write-CompactStatus -ExitCode $ExitCode

    if ($ExitCode -ne 0) {
        Write-Error "DynastyProcess refresh failed with exit code $ExitCode. See $StdoutLog and $StderrLog."
        exit $ExitCode
    }

    exit 0
}
catch {
    $Message = $_.Exception.Message
    Add-Content -LiteralPath $StderrLog -Value $Message
    Write-CompactStatus -ExitCode "1"
    Write-Error $Message
    exit 1
}
