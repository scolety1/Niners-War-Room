param(
    [string]$Task,
    [string]$Stage = "diff",
    [int]$MaxChangedFiles = 12,
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PolicySnapshotPath,
    [string]$ExpectedPolicySha256
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex-night-loop-security.ps1")

function Stop-Guardrail {
    param([string]$Message)
    Write-Host "Guardrail failed during ${Stage}: $Message" -ForegroundColor Red
    exit 1
}

try {
    if ([string]::IsNullOrWhiteSpace($Task)) {
        $Task = $env:CODEX_SELECTED_TASK
    }
    if ([string]::IsNullOrWhiteSpace($PolicySnapshotPath) -or
        [string]::IsNullOrWhiteSpace($ExpectedPolicySha256)) {
        Stop-Guardrail "A frozen policy snapshot and expected digest are required."
    }

    Assert-FileSha256 -Path $PolicySnapshotPath -ExpectedSha256 $ExpectedPolicySha256
    $policy = Get-Content -LiteralPath $PolicySnapshotPath -Raw | ConvertFrom-Json
    if ($policy.schemaVersion -ne 1) {
        Stop-Guardrail "Unsupported frozen policy schema."
    }

    $resolvedRepo = [IO.Path]::GetFullPath($RepoRoot)
    Assert-RepositoryBinding `
        -RepoRoot $resolvedRepo `
        -ExpectedRepoRoot ([string]$policy.git.expectedRepoRoot)
    Assert-ExpectedBranch `
        -RepoRoot $resolvedRepo `
        -ExpectedBranch ([string]$policy.git.expectedBranch)
    Assert-ExpectedRemote `
        -RepoRoot $resolvedRepo `
        -ExpectedRemote ([string]$policy.git.expectedRemote) `
        -ExpectedRemoteUrl ([string]$policy.git.expectedRemoteUrl)
    $parent = Get-CurrentCommit -RepoRoot $resolvedRepo
    if (-not $parent.Equals([string]$policy.git.expectedParent, [StringComparison]::OrdinalIgnoreCase)) {
        Stop-Guardrail "Parent binding changed before final-index review."
    }

    Assert-NoTrackedWorkingTreeDrift -RepoRoot $resolvedRepo
    Assert-NoNonIgnoredUntrackedDrift -RepoRoot $resolvedRepo
    $changedFiles = @(Get-StagedChangedPaths -RepoRoot $resolvedRepo)
    if ($changedFiles.Count -eq 0) {
        Stop-Guardrail "No final staged files found."
    }

    $policyMaxChangedFiles = [int]$policy.maxChangedFiles
    if ($policyMaxChangedFiles -le 0 -or $MaxChangedFiles -ne $policyMaxChangedFiles) {
        Stop-Guardrail "Runtime file-count limit differs from the frozen policy."
    }
    if ($changedFiles.Count -gt $policyMaxChangedFiles) {
        Stop-Guardrail "Too many final staged files ($($changedFiles.Count)); max is $policyMaxChangedFiles."
    }

    $outsideAllowed = @()
    foreach ($file in $changedFiles) {
        $allowed = $false
        foreach ($allowedPath in @($policy.allowedPaths)) {
            if (Test-RepositoryPathRule -Path $file -Rule ([string]$allowedPath)) {
                $allowed = $true
                break
            }
        }
        if (-not $allowed) {
            $outsideAllowed += $file
        }
    }
    if ($outsideAllowed.Count -gt 0) {
        Stop-Guardrail "Final staged files are outside frozen allowed paths: $(($outsideAllowed | Sort-Object -Unique) -join ', ')"
    }

    $protected = @()
    foreach ($file in $changedFiles) {
        foreach ($protectedPath in @($policy.protectedPaths)) {
            if (Test-RepositoryPathRule -Path $file -Rule ([string]$protectedPath)) {
                $protected += $file
                break
            }
        }
    }
    if ($protected.Count -gt 0) {
        Stop-Guardrail "Privileged automation changes are not allowed: $(($protected | Sort-Object -Unique) -join ', ')"
    }

    $blocked = @()
    foreach ($file in $changedFiles) {
        foreach ($blockedPath in @($policy.blockedPaths)) {
            if (Test-RepositoryPathRule -Path $file -Rule ([string]$blockedPath)) {
                $blocked += $file
                break
            }
        }
    }
    if ($blocked.Count -gt 0) {
        Stop-Guardrail "Blocked final staged file changes detected: $(($blocked | Sort-Object -Unique) -join ', ')"
    }

    $addedDiffLines = @(
        Invoke-GitChecked -RepoRoot $resolvedRepo -Arguments @(
            "diff", "--cached", "--unified=0", "--no-ext-diff", "--no-textconv",
            "--no-renames", "HEAD", "--"
        ) | Where-Object {
            $_ -match "^\+" -and $_ -notmatch "^\+\+\+"
        }
    )

    $debugLines = @($addedDiffLines | Where-Object {
        $_ -match "\bconsole\.(log|debug|trace)\b" -or $_ -match "\bdebugger\b"
    })
    if ($debugLines.Count -gt 0) {
        Stop-Guardrail "Debug statements were added to the final staged index."
    }

    $termHits = @()
    foreach ($line in $addedDiffLines) {
        foreach ($term in @($policy.blockedTerms)) {
            if (-not [string]::IsNullOrWhiteSpace([string]$term) -and
                $line -match [regex]::Escape([string]$term)) {
                $termHits += [string]$term
            }
        }
    }
    if ($termHits.Count -gt 0) {
        Stop-Guardrail "Blocked term(s) added to the final staged index: $(($termHits | Sort-Object -Unique) -join ', ')"
    }

    $approvedTree = Get-IndexTreeHash -RepoRoot $resolvedRepo
    Write-Host "Guardrails passed during ${Stage}: $($changedFiles.Count) final staged file(s), tree $approvedTree." -ForegroundColor Green
}
catch {
    Stop-Guardrail $_.Exception.Message
}
