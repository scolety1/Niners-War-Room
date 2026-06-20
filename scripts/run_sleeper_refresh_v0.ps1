param(
    [string]$Python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    [string]$SharedRoot = "C:\NWR_SHARED_DATA",
    [string]$LeagueId = "1344772855908290560",
    [string]$DraftId = "1353280212753723392",
    [string]$Season = "2026",
    [string]$LeagueName = "Las Vegas Enginerds",
    [string]$TransactionRounds = "1",
    [string]$SnapshotLabel = "",
    [switch]$WriteCandidates
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if ([string]::IsNullOrWhiteSpace($SnapshotLabel)) {
    $SnapshotLabel = $Timestamp
}

$SleeperRoot = Join-Path $SharedRoot "scheduled_ingest\sleeper"
$LogRoot = Join-Path $SharedRoot "scheduled_ingest\logs"
$LogPath = Join-Path $LogRoot "sleeper_refresh_v0_$SnapshotLabel.log"
$SnapshotDir = Join-Path $SleeperRoot $SnapshotLabel

New-Item -ItemType Directory -Force -Path $SleeperRoot, $LogRoot | Out-Null
Start-Transcript -Path $LogPath -Force | Out-Null
try {
    Write-Host "NWR Sleeper Refresh V0"
    Write-Host "Repo: $RepoRoot"
    Write-Host "Snapshot: $SnapshotDir"
    Write-Host "WriteCandidates: $WriteCandidates"
    Write-Host "Guardrail: latest_approved is never created or updated by this runner."

    Set-Location $RepoRoot
    & $Python scripts/sleeper_scheduled_pull_v0.py `
        --league-id $LeagueId `
        --draft-id $DraftId `
        --season $Season `
        --league-name $LeagueName `
        --transaction-rounds $TransactionRounds `
        --output-root $SleeperRoot `
        --snapshot-label $SnapshotLabel

    if ($LASTEXITCODE -ne 0) {
        throw "Sleeper scheduled pull failed with exit code $LASTEXITCODE"
    }

    if ($WriteCandidates) {
        Write-Host "Running Sleeper normalizer in latest_candidate mode only."
        & $Python scripts/sleeper_normalize_snapshot_v0.py `
            --snapshot-dir $SnapshotDir `
            --output-root (Join-Path $SharedRoot "lane_exchange") `
            --write-candidates
        if ($LASTEXITCODE -ne 0) {
            throw "Sleeper normalizer failed with exit code $LASTEXITCODE"
        }
    }
    else {
        Write-Host "Skipping Sleeper candidate generation; pass -WriteCandidates to opt in."
    }
}
finally {
    Stop-Transcript | Out-Null
}
