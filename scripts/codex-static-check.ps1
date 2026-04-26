$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$pythonCandidates = @()
if ($env:PYTHON) {
    $pythonCandidates += $env:PYTHON
}
$pythonCandidates += @(
    "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    "python",
    "py"
)

$python = $null
foreach ($candidate in $pythonCandidates) {
    try {
        if ($candidate -eq "py") {
            & $candidate -3 --version *> $null
        } else {
            & $candidate --version *> $null
        }
        $python = $candidate
        break
    } catch {
        continue
    }
}

if (-not $python) {
    throw "No Python runtime found. Set PYTHON or install Python 3.12+."
}

$tempDb = Join-Path $env:TEMP ("niners-war-room-check-" + [guid]::NewGuid().ToString() + ".sqlite3")
try {
    if ($python -eq "py") {
        & $python -3 scripts/init_db.py --database $tempDb
        & $python -3 -m pytest
        & $python -3 -m ruff check .
    } else {
        & $python scripts/init_db.py --database $tempDb
        & $python -m pytest
        & $python -m ruff check .
    }
} finally {
    if (Test-Path $tempDb) {
        Remove-Item -LiteralPath $tempDb -Force
    }
}

Write-Host "Niners War Room static check passed."
