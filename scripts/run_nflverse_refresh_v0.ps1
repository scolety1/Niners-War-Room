param(
    [string]$Python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    [string]$SharedRoot = "C:\NWR_SHARED_DATA",
    [string]$NflreadpyPath = "C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps",
    [string[]]$Seasons = @("2024", "2025"),
    [string[]]$Datasets = @(
        "schedules",
        "teams",
        "players",
        "rosters",
        "weekly_rosters",
        "ff_playerids",
        "depth_charts",
        "injuries",
        "player_stats_weekly",
        "snap_counts",
        "trades",
        "player_stats_seasonal",
        "play_by_play",
        "team_stats",
        "participation",
        "ftn_charting",
        "pfr_advstats",
        "nextgen_stats",
        "draft_picks",
        "combine",
        "contracts",
        "officials",
        "espn_qbr",
        "ff_opportunity"
    ),
    [string]$SnapshotLabel = "",
    [switch]$CheckDependencies
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
    Write-Host "Guardrail: this safe runner never writes candidates, latest_candidate, or latest_approved."

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

    Write-Host "Skipping candidate generation by design; use a separate approved lane for normalization."
}
finally {
    $env:PYTHONPATH = $OriginalPythonPath
    Stop-Transcript | Out-Null
}
