param(
    [string]$Python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    [string]$SharedRoot = "C:\NWR_SHARED_DATA",
    [string]$NflreadpyPath = "C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps",
    [string[]]$Seasons = @("2024", "2025"),
    [string[]]$Datasets = @(
        "weekly_stats",
        "season_stats",
        "rosters",
        "weekly_rosters",
        "snap_counts",
        "participation",
        "opportunity"
    ),
    [string]$SnapshotLabel = "",
    [switch]$CheckDependencies,
    [switch]$WriteCandidates
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if ([string]::IsNullOrWhiteSpace($SnapshotLabel)) {
    $SnapshotLabel = $Timestamp
}

$NflverseRoot = Join-Path $SharedRoot "scheduled_ingest\nflverse"
$LogRoot = Join-Path $SharedRoot "scheduled_ingest\logs"
$LogPath = Join-Path $LogRoot "nflverse_refresh_v0_$SnapshotLabel.log"
$SnapshotDir = Join-Path $NflverseRoot $SnapshotLabel

if ($CheckDependencies) {
    $DepsExist = Test-Path -LiteralPath $NflreadpyPath
    Write-Host "NWR nflverse dependency check"
    Write-Host "Runner: $PSCommandPath"
    Write-Host "NflreadpyPath: $NflreadpyPath"
    Write-Host "DependenciesFound: $DepsExist"
    if (-not $DepsExist) {
        exit 2
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path $NflverseRoot, $LogRoot | Out-Null
Start-Transcript -Path $LogPath -Force | Out-Null
$OriginalPythonPath = $env:PYTHONPATH
try {
    Write-Host "NWR nflverse Refresh V0"
    Write-Host "Repo: $RepoRoot"
    Write-Host "Snapshot: $SnapshotDir"
    Write-Host "Datasets: $($Datasets -join ', ')"
    Write-Host "WriteCandidates: $WriteCandidates"
    Write-Host "Guardrail: latest_approved is never created or updated by this runner."

    $env:PYTHONPATH = $NflreadpyPath
    Set-Location $RepoRoot
    & $Python scripts/nflverse_scheduled_pull_v0.py `
        --seasons $Seasons `
        --datasets $Datasets `
        --output-root $NflverseRoot `
        --snapshot-label $SnapshotLabel

    if ($LASTEXITCODE -ne 0) {
        throw "nflverse scheduled pull failed with exit code $LASTEXITCODE"
    }

    if ($WriteCandidates) {
        Write-Host "Running nflverse normalizer in latest_candidate mode only."
        & $Python scripts/nflverse_normalize_snapshot_v0.py `
            --snapshot-dir $SnapshotDir `
            --output-root (Join-Path $SharedRoot "lane_exchange") `
            --write-candidates
        if ($LASTEXITCODE -ne 0) {
            throw "nflverse normalizer failed with exit code $LASTEXITCODE"
        }
    }
    else {
        Write-Host "Skipping nflverse candidate generation; pass -WriteCandidates to opt in."
    }
}
finally {
    $env:PYTHONPATH = $OriginalPythonPath
    Stop-Transcript | Out-Null
}
