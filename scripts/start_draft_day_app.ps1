param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$url = "http://127.0.0.1:$Port/rankings"
$fallback = Join-Path $repoRoot "docs\draft_day_exports\final_board_v1_20260622\OPEN_THIS_FIRST.html"

Write-Host "Niners War Room Draft-Day App V1"
Write-Host "Repo: $repoRoot"
Write-Host "Local URL: $url"
Write-Host "Static fallback: $fallback"
Write-Host ""

$pythonCandidates = @(
    (Join-Path $repoRoot ".venv\Scripts\python.exe"),
    "C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe",
    "python",
    "py"
)

$python = $null
foreach ($candidate in $pythonCandidates) {
    try {
        if ($candidate -like "*.exe" -and -not (Test-Path $candidate)) {
            continue
        }
        & $candidate --version *> $null
        $python = $candidate
        break
    } catch {
        continue
    }
}

if (-not $python) {
    Write-Error "No Python runtime found. Open the static fallback HTML instead."
}

try {
    & $python -m streamlit --version *> $null
} catch {
    Write-Host "Streamlit is not installed in this Python environment."
    Write-Host "Install once from repo root with:"
    Write-Host "  $python -m pip install -r requirements.txt"
    Write-Host "Then rerun this script. Static fallback remains available at:"
    Write-Host "  $fallback"
    exit 1
}

Write-Host "Starting Streamlit. Leave this window open during the draft."
Write-Host "Open: $url"
& $python -m streamlit run app/main.py `
    --server.address 127.0.0.1 `
    --server.port $Port `
    --server.headless true `
    --browser.gatherUsageStats false
