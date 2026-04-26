param(
    [int]$Rounds = 1,
    [int]$MaxChangedFiles = 12,
    [int]$MaxCodexAttempts = 4,
    [switch]$Push
)

$ErrorActionPreference = "Continue"

$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

$profilePath = "docs/codex/PROFILE.json"
$profile = $null
if (Test-Path $profilePath) {
    $profile = Get-Content $profilePath -Raw | ConvertFrom-Json
    if ($profile.maxChangedFiles) {
        $MaxChangedFiles = [int]$profile.maxChangedFiles
    }
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$branchPrefix = if ($profile -and $profile.branchPrefix) { $profile.branchPrefix } else { "codex/run" }
$branch = "$branchPrefix-$timestamp"
$logDir = ".codex-logs\$timestamp"

Write-Host "Starting Codex loop on branch $branch" -ForegroundColor Cyan

if (!(Test-Path ".git\info\exclude")) {
    New-Item -ItemType File -Path ".git\info\exclude" -Force | Out-Null
}

$excludeText = Get-Content ".git\info\exclude" -Raw
if ($excludeText -notmatch "\.codex-logs/") {
    Add-Content ".git\info\exclude" "`n.codex-logs/"
}

function Get-FirstUncheckedTask {
    foreach ($line in Get-Content "docs/codex/TASK_QUEUE.md") {
        if ($line -match "^\s*-\s+\[ \]\s+(.+)$") {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Mark-FirstUncheckedTaskComplete {
    $path = "docs/codex/TASK_QUEUE.md"
    $updated = $false
    $newLines = foreach ($line in Get-Content $path) {
        if (-not $updated -and $line -match "^(\s*-\s+)\[ \](\s+.+)$") {
            $updated = $true
            "$($Matches[1])[x]$($Matches[2])"
        } else {
            $line
        }
    }
    Set-Content $path $newLines
}

function Append-Report {
    param([string]$Task, [string[]]$FilesChanged, [string]$BuildResult, [string]$Risk)

    if (!(Test-Path "docs/codex/NIGHTLY_REPORT.md")) {
        "# Codex Nightly Report`n" | Set-Content "docs/codex/NIGHTLY_REPORT.md"
    }

    $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $files = if ($FilesChanged.Count -gt 0) { ($FilesChanged | ForEach-Object { "- $_" }) -join "`n" } else { "- None" }

    Add-Content "docs/codex/NIGHTLY_REPORT.md" @"

## $date

- Task attempted: $Task
- Build result: $BuildResult
- Files changed:
$files
- Risks or follow-up needed: $Risk
"@
}

function Invoke-Guardrails {
    param([string]$Task, [string]$Stage)
    $previousTask = $env:CODEX_SELECTED_TASK
    $env:CODEX_SELECTED_TASK = $Task
    powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\codex-guardrails.ps1" -Stage $Stage -MaxChangedFiles $MaxChangedFiles
    $passed = $LASTEXITCODE -eq 0
    $env:CODEX_SELECTED_TASK = $previousTask
    return $passed
}

function Invoke-CodexExec {
    param([string]$Prompt, [string]$LogPath)

    for ($attempt = 1; $attempt -le $MaxCodexAttempts; $attempt++) {
        Write-Host "Codex attempt $attempt of $MaxCodexAttempts" -ForegroundColor DarkCyan
        $attemptLog = if ($attempt -eq 1) { $LogPath } else { $LogPath -replace "\.log$", "-attempt-$attempt.log" }
        $Prompt | & codex exec --full-auto - 2>&1 | Tee-Object -FilePath $attemptLog
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            return 0
        }

        $diffText = (git diff) -join "`n"
        if (![string]::IsNullOrWhiteSpace($diffText)) {
            Write-Host "Codex exited nonzero after making changes; continuing to build/guardrail checks." -ForegroundColor Yellow
            return $exitCode
        }

        $sleepSeconds = [Math]::Min(300, 30 * $attempt)
        Write-Host "Codex failed with no repo changes. Waiting $sleepSeconds seconds before retry." -ForegroundColor Yellow
        Start-Sleep -Seconds $sleepSeconds
    }

    return 1
}

function Invoke-ExternalBuild {
    if (!(Test-Path $profilePath)) {
        return $true
    }

    $profile = Get-Content $profilePath -Raw | ConvertFrom-Json
    if ([string]::IsNullOrWhiteSpace($profile.buildCommand)) {
        return $true
    }

    Push-Location $profile.buildDirectory
    Invoke-Expression $profile.buildCommand
    $ok = $LASTEXITCODE -eq 0
    Pop-Location
    return $ok
}

$status = (git status --porcelain) -join "`n"
if (![string]::IsNullOrWhiteSpace($status)) {
    Write-Host "Repo is not clean. Commit, restore, or stash changes before running the loop." -ForegroundColor Red
    git status
    exit 1
}

git checkout main
if ($LASTEXITCODE -ne 0) { exit 1 }

$upstream = git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($upstream)) {
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

git checkout -b $branch
if ($LASTEXITCODE -ne 0) { exit 1 }

mkdir $logDir -Force | Out-Null

for ($i = 1; $i -le $Rounds; $i++) {
    Write-Host "`n===== ROUND $i of $Rounds =====" -ForegroundColor Cyan
    $task = Get-FirstUncheckedTask
    if ([string]::IsNullOrWhiteSpace($task)) {
        Append-Report -Task "No unchecked tasks" -FilesChanged @() -BuildResult "Skipped" -Risk "No unchecked tasks were found."
        break
    }

    Write-Host "Selected task: $task" -ForegroundColor Cyan
    $prompt = @"
Read docs/codex/RUN_POLICY.md and docs/codex/TASK_QUEUE.md.

Implement only this selected task:
$task

Rules:
1. Inspect relevant files before editing.
2. Make a small reviewable change.
3. Do not run build commands.
4. Do not mark tasks complete.
5. Do not edit NIGHTLY_REPORT.md.
6. Obey the project guardrails.
"@

    $log1 = "$logDir\round-$i-implement.log"
    $exit = Invoke-CodexExec -Prompt $prompt -LogPath $log1
    if ($exit -ne 0 -and [string]::IsNullOrWhiteSpace(((git diff) -join "`n"))) {
        Append-Report -Task $task -FilesChanged @() -BuildResult "Failed" -Risk "Codex command failed and made no changes."
        break
    }

    if ([string]::IsNullOrWhiteSpace(((git diff) -join "`n"))) {
        Append-Report -Task $task -FilesChanged @() -BuildResult "Skipped" -Risk "Codex made no changes."
        break
    }

    if (-not (Invoke-Guardrails -Task $task -Stage "implementation")) { break }
    if (-not (Invoke-ExternalBuild)) {
        $filesChanged = git diff --name-only
        Append-Report -Task $task -FilesChanged $filesChanged -BuildResult "Failed" -Risk "External build failed."
        break
    }

    $reviewPrompt = @"
Review the current git diff for only this selected task:
$task

Rules:
1. Inspect the diff and relevant changed files.
2. Fix only clear issues caused by this task.
3. Do not broaden scope.
4. Do not run build commands.
5. Do not mark tasks complete.
6. Do not edit NIGHTLY_REPORT.md.
"@
    $log2 = "$logDir\round-$i-review.log"
    $reviewExit = Invoke-CodexExec -Prompt $reviewPrompt -LogPath $log2
    if ($reviewExit -ne 0 -and [string]::IsNullOrWhiteSpace(((git diff) -join "`n"))) {
        Append-Report -Task $task -FilesChanged @() -BuildResult "Failed" -Risk "Codex review command failed and left no changes."
        break
    }

    if (-not (Invoke-Guardrails -Task $task -Stage "review")) { break }
    if (-not (Invoke-ExternalBuild)) {
        $filesChanged = git diff --name-only
        Append-Report -Task $task -FilesChanged $filesChanged -BuildResult "Failed" -Risk "Final external build failed."
        break
    }

    $filesChangedBeforeDocs = git diff --name-only
    Mark-FirstUncheckedTaskComplete
    Append-Report -Task $task -FilesChanged $filesChangedBeforeDocs -BuildResult "Passed" -Risk "Low. External build passed."
    git add .
    git commit -m "Codex round $i"
    if ($Push) { git push -u origin $branch }
}

Write-Host "`nCodex loop finished." -ForegroundColor Cyan
Write-Host "Branch: $branch"
Write-Host "Raw logs: $logDir"
