param(
    [int]$Port = 8512
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$pythonCandidates = @(
    (Join-Path $repoRoot ".venv\Scripts\python.exe"),
    "C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe",
    "python",
    "py"
)
$python = $null
foreach ($candidate in $pythonCandidates) {
    try {
        if ($candidate -like "*.exe" -and -not (Test-Path $candidate)) { continue }
        & $candidate --version *> $null
        $python = $candidate
        break
    } catch { continue }
}
if (-not $python) { Write-Error "No Python runtime found." }

Write-Host "Starting Niners War Room — Redraft at http://127.0.0.1:$Port"
& $python -m streamlit run app/main_redraft.py `
    --server.address 127.0.0.1 `
    --server.port $Port `
    --server.headless true `
    --browser.gatherUsageStats false
