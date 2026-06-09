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

if ($python -eq "py") {
    & $python -3 scripts/merge_lve_roster_ranks.py @args
} else {
    & $python scripts/merge_lve_roster_ranks.py @args
}
