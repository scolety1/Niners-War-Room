$ErrorActionPreference = "Stop"

$RepoRoot = "C:\NWR\Niners-War-Room"
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$RefreshScript = Join-Path $RepoRoot "scripts\refresh_dynastyprocess_market_baseline_v1.py"
$FreshnessReport = Join-Path $RepoRoot "docs\hq\parallel_lanes\dynastyprocess_market_baseline_20260622\dp_freshness_report.csv"
$LogRoot = "C:\NWR_SHARED_DATA\market_sources\dynastyprocess\logs"

New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $LogRoot "dynastyprocess_refresh_$Timestamp.stdout.log"
$StderrLog = Join-Path $LogRoot "dynastyprocess_refresh_$Timestamp.stderr.log"

function Write-CompactStatus {
    param(
        [string] $ExitCode
    )

    if (Test-Path -LiteralPath $FreshnessReport) {
        $Freshness = Import-Csv -LiteralPath $FreshnessReport | Select-Object -First 1
        $Status = $Freshness.freshness_status
        $ScrapeDate = $Freshness.upstream_scrape_date
        $Commit = $Freshness.upstream_latest_commit_sha
        $CachePath = $Freshness.local_cache_path
        Write-Host "exit_code=$ExitCode freshness_status=$Status scrape_date=$ScrapeDate commit=$Commit cache_path=$CachePath"
    }
    else {
        Write-Host "exit_code=$ExitCode freshness_status=UNKNOWN scrape_date=UNKNOWN commit=UNKNOWN cache_path=UNKNOWN"
    }
    Write-Host "stdout_log=$StdoutLog"
    Write-Host "stderr_log=$StderrLog"
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

    Push-Location $RepoRoot
    try {
        & $PythonExe $RefreshScript 1> $StdoutLog 2> $StderrLog
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
