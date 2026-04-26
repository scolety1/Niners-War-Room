param(
    [string]$Task,
    [string]$Stage = "diff",
    [int]$MaxChangedFiles = 12
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($Task)) {
    $Task = $env:CODEX_SELECTED_TASK
}

function Stop-Guardrail {
    param([string]$Message)
    Write-Host "Guardrail failed during ${Stage}: $Message" -ForegroundColor Red
    exit 1
}

$changedFiles = @(git diff --name-only)
if ($LASTEXITCODE -ne 0) {
    Stop-Guardrail "Could not inspect git diff."
}

if ($changedFiles.Count -eq 0) {
    Stop-Guardrail "No changed files found."
}

if ($changedFiles.Count -gt $MaxChangedFiles) {
    Stop-Guardrail "Too many files changed ($($changedFiles.Count)); max is $MaxChangedFiles."
}

$normalizedFiles = $changedFiles | ForEach-Object { $_ -replace "\\", "/" }
$profilePath = "docs/codex/PROFILE.json"

if (Test-Path $profilePath) {
    $profile = Get-Content $profilePath -Raw | ConvertFrom-Json

    $blocked = @()
    foreach ($file in $normalizedFiles) {
        foreach ($blockedPath in @($profile.blockedPaths)) {
            $pattern = "^" + [regex]::Escape(($blockedPath -replace "\\", "/"))
            if ($file -match $pattern) {
                $blocked += $file
                break
            }
        }
    }

    if ($blocked.Count -gt 0) {
        Stop-Guardrail "Blocked file changes detected: $($blocked -join ', ')"
    }
}

$addedDiffLines = @(git diff --unified=0 | Where-Object {
    $_ -match "^\+" -and $_ -notmatch "^\+\+\+"
})

$debugLines = @($addedDiffLines | Where-Object {
    $_ -match "\bconsole\.(log|debug|trace)\b" -or $_ -match "\bdebugger\b"
})

if ($debugLines.Count -gt 0) {
    Stop-Guardrail "Debug statements were added."
}

if (Test-Path $profilePath) {
    $profile = Get-Content $profilePath -Raw | ConvertFrom-Json
    $blockedTerms = @($profile.blockedTerms)
    $termHits = @()

    foreach ($line in $addedDiffLines) {
        foreach ($term in $blockedTerms) {
            if ($line -match [regex]::Escape($term)) {
                $termHits += $term
            }
        }
    }

    if ($termHits.Count -gt 0) {
        Stop-Guardrail "Blocked term(s) added: $(($termHits | Sort-Object -Unique) -join ', ')"
    }
}

Write-Host "Guardrails passed during ${Stage}: $($normalizedFiles.Count) changed file(s)." -ForegroundColor Green
