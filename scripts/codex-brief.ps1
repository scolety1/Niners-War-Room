param(
    [int]$CommitCount = 5,
    [int]$ReportLines = 80
)

$ErrorActionPreference = "Continue"

$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) {
    Write-Host "Not inside a git repo." -ForegroundColor Red
    exit 1
}

Set-Location $repoRoot

$branch = git branch --show-current
$status = @(git status --short)
$hasCommits = $true
$lastCommit = git rev-parse --short HEAD 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($lastCommit)) {
    $hasCommits = $false
    $lastCommit = "none"
}

if ($hasCommits) {
    $commits = @(git log --oneline -n $CommitCount)
    $changedInLastCommit = @(git show --name-only --format="" HEAD | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
} else {
    $commits = @()
    $changedInLastCommit = @()
}

$uncheckedTasks = @(Select-String -Path "docs/codex/TASK_QUEUE.md" -Pattern "^\s*-\s+\[ \]" -ErrorAction SilentlyContinue | ForEach-Object { $_.Line.Trim() })
$completedTasks = @(Select-String -Path "docs/codex/TASK_QUEUE.md" -Pattern "^\s*-\s+\[x\]" -ErrorAction SilentlyContinue | ForEach-Object { $_.Line.Trim() })

Write-Host "# Codex Run Brief"
Write-Host ""
Write-Host "## Repo"
Write-Host "- Path: $repoRoot"
Write-Host "- Branch: $branch"
Write-Host "- HEAD: $lastCommit"
Write-Host ""

Write-Host "## Working Tree"
if ($status.Count -eq 0) { Write-Host "- Clean" } else { $status | ForEach-Object { Write-Host "- $_" } }
Write-Host ""

Write-Host "## Recent Commits"
if ($commits.Count -eq 0) { Write-Host "- None" } else { $commits | ForEach-Object { Write-Host "- $_" } }
Write-Host ""

Write-Host "## Files In Latest Commit"
if ($changedInLastCommit.Count -eq 0) { Write-Host "- None" } else { $changedInLastCommit | ForEach-Object { Write-Host "- $_" } }
Write-Host ""

Write-Host "## Completed Tasks"
if ($completedTasks.Count -eq 0) { Write-Host "- None" } else { $completedTasks | ForEach-Object { Write-Host "- $_" } }
Write-Host ""

Write-Host "## Remaining Unchecked Tasks"
if ($uncheckedTasks.Count -eq 0) { Write-Host "- None" } else { $uncheckedTasks | ForEach-Object { Write-Host "- $_" } }
Write-Host ""

Write-Host "## Nightly Report Tail"
if (Test-Path "docs/codex/NIGHTLY_REPORT.md") {
    Get-Content "docs/codex/NIGHTLY_REPORT.md" -Tail $ReportLines
} else {
    Write-Host "- No nightly report found."
}
