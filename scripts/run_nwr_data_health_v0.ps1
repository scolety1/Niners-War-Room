param(
    [string]$Python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    [string]$SharedRoot = "C:\NWR_SHARED_DATA"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogRoot = Join-Path $SharedRoot "scheduled_ingest\logs"
$LogPath = Join-Path $LogRoot "nwr_data_health_v0_$Timestamp.log"

New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
Start-Transcript -Path $LogPath -Force | Out-Null
try {
    Write-Host "NWR Data Health V0"
    Write-Host "Repo: $RepoRoot"
    Write-Host "Guardrail: read-only operator status only."

    Set-Location $RepoRoot
    & $Python scripts/nwr_operator_status_v0.py `
        --shared-root $SharedRoot `
        --write-report

    if ($LASTEXITCODE -ne 0) {
        throw "NWR operator status failed with exit code $LASTEXITCODE"
    }
}
finally {
    Stop-Transcript | Out-Null
}
