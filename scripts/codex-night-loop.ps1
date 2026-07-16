param(
    [int]$Rounds = 1,
    [int]$MaxChangedFiles = 12,
    [int]$MaxCodexAttempts = 4,
    [switch]$Push
)

$ErrorActionPreference = "Stop"

$Repo = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
Set-Location $Repo
. (Join-Path $PSScriptRoot "codex-night-loop-security.ps1")

$script:TrustedRoot = $null
$script:TrustedArtifacts = @()
$script:FrozenPolicy = $null
$script:PolicyPath = $null
$script:PolicySha256 = $null
$script:TrustedGuardrailPath = $null
$script:TrustedHandles = @()
$scriptExitCode = 0

function Get-FirstUncheckedTask {
    foreach ($line in Get-Content -LiteralPath (Join-Path $Repo "docs\codex\TASK_QUEUE.md")) {
        if ($line -match "^\s*-\s+\[ \]\s+(.+)$") {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Assert-TrustedEnvelope {
    Assert-TrustedArtifactSet -Artifacts $script:TrustedArtifacts
    Assert-FileSha256 -Path $script:PolicyPath -ExpectedSha256 $script:PolicySha256
}

function Invoke-Guardrails {
    param([string]$Task, [string]$Stage)

    Assert-TrustedEnvelope
    $previousTask = $env:CODEX_SELECTED_TASK
    $previousErrorActionPreference = $ErrorActionPreference
    $env:CODEX_SELECTED_TASK = $Task
    try {
        $ErrorActionPreference = "Continue"
        & ([string]$script:FrozenPolicy.build.executable) `
            -NoProfile `
            -NonInteractive `
            -ExecutionPolicy Bypass `
            -File $script:TrustedGuardrailPath `
            -RepoRoot $Repo `
            -PolicySnapshotPath $script:PolicyPath `
            -ExpectedPolicySha256 $script:PolicySha256 `
            -Stage $Stage `
            -MaxChangedFiles ([int]$script:FrozenPolicy.maxChangedFiles)
        $exitCode = $LASTEXITCODE
        return $exitCode -eq 0
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        $env:CODEX_SELECTED_TASK = $previousTask
    }
}

function Invoke-CodexExec {
    param([string]$Prompt, [string]$LogPath)

    for ($attempt = 1; $attempt -le $MaxCodexAttempts; $attempt++) {
        Write-Host "Codex attempt $attempt of $MaxCodexAttempts" -ForegroundColor DarkCyan
        $attemptLog = if ($attempt -eq 1) {
            $LogPath
        }
        else {
            $LogPath -replace "\.log$", "-attempt-$attempt.log"
        }
        $previousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $Prompt | & codex exec --full-auto - 2>&1 | Tee-Object -FilePath $attemptLog
            $exitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
        Assert-TrustedEnvelope
        if ($exitCode -eq 0) {
            return 0
        }
        if (Test-RepositoryHasChanges -RepoRoot $Repo) {
            Write-Host "Codex exited nonzero after making changes; continuing to candidate checks." -ForegroundColor Yellow
            return $exitCode
        }

        $sleepSeconds = [Math]::Min(300, 30 * $attempt)
        Write-Host "Codex failed with no repository changes. Waiting $sleepSeconds seconds before retry." -ForegroundColor Yellow
        Start-Sleep -Seconds $sleepSeconds
    }
    return 1
}

function Invoke-ExternalBuild {
    if (-not [bool]$script:FrozenPolicy.build.enabled) {
        return $true
    }

    Assert-TrustedEnvelope
    $exitCode = Invoke-ApprovedExecutable `
        -Executable ([string]$script:FrozenPolicy.build.executable) `
        -Arguments @($script:FrozenPolicy.build.arguments | ForEach-Object { [string]$_ }) `
        -WorkingDirectory ([string]$script:FrozenPolicy.build.workingDirectory) `
        -ApprovedRoot $Repo
    return $exitCode -eq 0
}

function Initialize-TrustedEnvelope {
    param(
        [Parameter(Mandatory = $true)]$Profile,
        [Parameter(Mandatory = $true)][string]$ExpectedParent,
        [Parameter(Mandatory = $true)][string]$ExpectedBranch,
        [Parameter(Mandatory = $true)][string]$ExpectedRemote,
        [Parameter(Mandatory = $true)][string]$ExpectedRemoteUrl
    )

    $approvedLegacyBuildCommand = "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1"
    $buildEnabled = -not [string]::IsNullOrWhiteSpace([string]$Profile.buildCommand)
    if ($buildEnabled -and
        -not ([string]$Profile.buildCommand).Equals($approvedLegacyBuildCommand, [StringComparison]::OrdinalIgnoreCase)) {
        throw "PROFILE.json buildCommand is not the fixed approved static-check command. Repository command text will not be interpreted."
    }

    $buildWorkingDirectory = Resolve-ApprovedWorkingDirectory `
        -ApprovedRoot $Repo `
        -RequestedPath ([string]$Profile.buildDirectory)
    $powershellCommand = Get-Command powershell.exe -CommandType Application -ErrorAction Stop
    $powershellExecutable = [IO.Path]::GetFullPath($powershellCommand.Source)

    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $script:TrustedRoot = [IO.Path]::GetFullPath((Join-Path $tempRoot (
        "nwr-codex-night-loop-trusted-" + [guid]::NewGuid().ToString("N")
    )))
    New-Item -ItemType Directory -Path $script:TrustedRoot -Force | Out-Null

    $trustedHelper = Join-Path $script:TrustedRoot "codex-night-loop-security.ps1"
    $script:TrustedGuardrailPath = Join-Path $script:TrustedRoot "codex-guardrails.ps1"
    $trustedBuild = Join-Path $script:TrustedRoot "codex-static-check.ps1"
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "codex-night-loop-security.ps1") -Destination $trustedHelper
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "codex-guardrails.ps1") -Destination $script:TrustedGuardrailPath
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "codex-static-check.ps1") -Destination $trustedBuild

    $protectedPaths = @(
        "docs/codex/PROFILE.json",
        "scripts/codex-night-loop.ps1",
        "scripts/codex-guardrails.ps1",
        "scripts/codex-night-loop-security.ps1",
        "scripts/codex-static-check.ps1",
        "scripts/bootstrap-hermetic-test-pack.ps1",
        "scripts/verify-repository.ps1",
        "scripts/tests/test-codex-night-loop-security.ps1",
        "scripts/tests/test-hermetic-bootstrap.ps1",
        "scripts/pytest_no_skips_plugin.py",
        "tests/hermetic_localdata_manifest.json"
    )
    $buildArguments = @(
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", $trustedBuild,
        "-RepoRoot", $Repo
    )

    $policy = [ordered]@{
        schemaVersion = 1
        maxChangedFiles = $MaxChangedFiles
        allowedPaths = @($Profile.allowedPaths)
        blockedPaths = @($Profile.blockedPaths)
        blockedTerms = @($Profile.blockedTerms)
        protectedPaths = $protectedPaths
        build = [ordered]@{
            enabled = $buildEnabled
            executable = $powershellExecutable
            arguments = $buildArguments
            workingDirectory = $buildWorkingDirectory
        }
        git = [ordered]@{
            expectedRepoRoot = $Repo
            expectedParent = $ExpectedParent
            expectedBranch = $ExpectedBranch
            expectedRemote = $ExpectedRemote
            expectedRemoteUrl = $ExpectedRemoteUrl
            commitAllowed = $false
            pushAllowed = $false
        }
    }

    if ($policy.allowedPaths.Count -eq 0) {
        throw "Frozen policy requires at least one allowed path."
    }

    $script:PolicyPath = Join-Path $script:TrustedRoot "frozen-policy.json"
    $policy | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $script:PolicyPath -Encoding UTF8
    $script:PolicySha256 = Get-FileSha256 -Path $script:PolicyPath
    $script:FrozenPolicy = Get-Content -LiteralPath $script:PolicyPath -Raw | ConvertFrom-Json

    $trustedArtifacts = @(
        [pscustomobject]@{ Name = "policy"; Path = $script:PolicyPath; Sha256 = $script:PolicySha256 },
        [pscustomobject]@{ Name = "guardrail"; Path = $script:TrustedGuardrailPath; Sha256 = Get-FileSha256 -Path $script:TrustedGuardrailPath },
        [pscustomobject]@{ Name = "security-helper"; Path = $trustedHelper; Sha256 = Get-FileSha256 -Path $trustedHelper },
        [pscustomobject]@{ Name = "build-script"; Path = $trustedBuild; Sha256 = Get-FileSha256 -Path $trustedBuild }
    )
    foreach ($configName in @("config", "config.worktree")) {
        $configOutput = @(Invoke-GitChecked -RepoRoot $Repo -Arguments @("rev-parse", "--git-path", $configName))
        if ($configOutput.Count -eq 1 -and -not [string]::IsNullOrWhiteSpace([string]$configOutput[0])) {
            $configPath = [string]$configOutput[0]
            if (-not [IO.Path]::IsPathRooted($configPath)) {
                $configPath = [IO.Path]::GetFullPath((Join-Path $Repo $configPath))
            }
            if (Test-Path -LiteralPath $configPath -PathType Leaf) {
                $trustedArtifacts += [pscustomobject]@{
                    Name = "git-$configName"
                    Path = $configPath
                    Sha256 = Get-FileSha256 -Path $configPath
                }
            }
        }
    }

    $script:TrustedArtifacts = $trustedArtifacts
    Assert-TrustedEnvelope
    $script:TrustedHandles = @(Lock-TrustedArtifactSet -Artifacts $script:TrustedArtifacts)
    Assert-TrustedEnvelope
}

function Remove-TrustedEnvelope {
    Close-TrustedArtifactSet -Handles $script:TrustedHandles
    $script:TrustedHandles = @()
    if ([string]::IsNullOrWhiteSpace($script:TrustedRoot) -or
        -not (Test-Path -LiteralPath $script:TrustedRoot)) {
        return
    }

    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $trustedFull = [IO.Path]::GetFullPath($script:TrustedRoot)
    $safePrefix = "nwr-codex-night-loop-trusted-"
    $underTemp = $trustedFull.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)
    $safeName = [IO.Path]::GetFileName($trustedFull).StartsWith($safePrefix, [StringComparison]::Ordinal)
    if (-not $underTemp -or -not $safeName) {
        throw "Refusing to clean up an unverified trusted-envelope path: $trustedFull"
    }
    Remove-Item -LiteralPath $trustedFull -Recurse -Force
}

try {
    if ($Push) {
        throw "Unattended push is disabled. Use the human re-enable checklist after independent review."
    }
    if ($Rounds -ne 1) {
        throw "Approval-only dry-run mode supports exactly one round per invocation."
    }
    if ($MaxChangedFiles -le 0 -or $MaxCodexAttempts -le 0) {
        throw "MaxChangedFiles and MaxCodexAttempts must be positive."
    }
    if (Test-RepositoryHasChanges -RepoRoot $Repo) {
        throw "Repo is not clean. Commit, restore, or stash changes before running the loop."
    }

    $profilePath = Join-Path $Repo "docs\codex\PROFILE.json"
    if (-not (Test-Path -LiteralPath $profilePath -PathType Leaf)) {
        throw "Required Codex profile is missing: $profilePath"
    }
    $profile = Get-Content -LiteralPath $profilePath -Raw | ConvertFrom-Json
    if ($profile.maxChangedFiles) {
        $MaxChangedFiles = [int]$profile.maxChangedFiles
    }

    $branch = Get-CurrentBranchName -RepoRoot $Repo
    $parent = Get-CurrentCommit -RepoRoot $Repo
    $remoteName = "origin"
    $remoteUrl = @((Invoke-GitChecked -RepoRoot $Repo -Arguments @("remote", "get-url", $remoteName)))[0].ToString().Trim()

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logDir = ".codex-logs\$timestamp"
    $excludePath = @((Invoke-GitChecked -RepoRoot $Repo -Arguments @(
        "rev-parse", "--git-path", "info/exclude"
    )))[0].ToString().Trim()
    $excludeParent = Split-Path -Parent $excludePath
    if (-not (Test-Path -LiteralPath $excludeParent -PathType Container)) {
        New-Item -ItemType Directory -Path $excludeParent -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $excludePath -PathType Leaf)) {
        New-Item -ItemType File -Path $excludePath -Force | Out-Null
    }
    $excludeText = Get-Content -LiteralPath $excludePath -Raw
    if ($excludeText -notmatch "(?m)^\.codex-logs/$") {
        Add-Content -LiteralPath $excludePath -Value ".codex-logs/"
    }

    Initialize-TrustedEnvelope `
        -Profile $profile `
        -ExpectedParent $parent `
        -ExpectedBranch $branch `
        -ExpectedRemote $remoteName `
        -ExpectedRemoteUrl $remoteUrl
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null

    Write-Host "Starting Codex approval-only dry run on branch $branch" -ForegroundColor Cyan
    $task = Get-FirstUncheckedTask
    if ([string]::IsNullOrWhiteSpace($task)) {
        throw "No unchecked task was found."
    }

    $prompt = @"
Read docs/codex/RUN_POLICY.md and docs/codex/TASK_QUEUE.md.

Implement only this selected task:
$task

Rules:
1. Inspect relevant files before editing.
2. Make a small reviewable change.
3. Do not run build commands.
4. Do not stage, commit, push, or mark tasks complete.
5. Do not edit NIGHTLY_REPORT.md.
6. Obey the project guardrails.
"@
    $log1 = "$logDir\round-1-implement.log"
    $exit = Invoke-CodexExec -Prompt $prompt -LogPath $log1
    if ($exit -ne 0 -and -not (Test-RepositoryHasChanges -RepoRoot $Repo)) {
        throw "Codex command failed and made no changes."
    }
    if (-not (Test-RepositoryHasChanges -RepoRoot $Repo)) {
        throw "Codex made no changes."
    }

    Stage-CandidateIndex -RepoRoot $Repo
    if (-not (Invoke-Guardrails -Task $task -Stage "implementation-candidate")) {
        throw "Implementation candidate guardrail failed."
    }
    if (-not (Invoke-ExternalBuild)) {
        throw "External build failed."
    }

    $reviewPrompt = @"
Review the final candidate in git diff --cached for only this selected task:
$task

Rules:
1. Inspect the staged diff and relevant changed files.
2. Fix only clear issues caused by this task.
3. Do not broaden scope.
4. Do not run build commands.
5. Do not stage, commit, push, or mark tasks complete.
6. Do not edit NIGHTLY_REPORT.md.
"@
    $log2 = "$logDir\round-1-review.log"
    [void](Invoke-CodexExec -Prompt $reviewPrompt -LogPath $log2)
    if (-not (Test-RepositoryHasChanges -RepoRoot $Repo)) {
        throw "Codex review removed the complete candidate."
    }

    Stage-CandidateIndex -RepoRoot $Repo
    if (-not (Invoke-Guardrails -Task $task -Stage "review-candidate")) {
        throw "Review candidate guardrail failed."
    }
    if (-not (Invoke-ExternalBuild)) {
        throw "Final external build failed."
    }

    Stage-CandidateIndex -RepoRoot $Repo
    if (-not (Invoke-Guardrails -Task $task -Stage "final-index-approval")) {
        throw "Final-index guardrail failed."
    }
    $approval = New-FinalIndexApproval `
        -RepoRoot $Repo `
        -ExpectedRepoRoot ([string]$script:FrozenPolicy.git.expectedRepoRoot) `
        -ExpectedParent ([string]$script:FrozenPolicy.git.expectedParent) `
        -ExpectedBranch ([string]$script:FrozenPolicy.git.expectedBranch) `
        -ExpectedRemote ([string]$script:FrozenPolicy.git.expectedRemote) `
        -ExpectedRemoteUrl ([string]$script:FrozenPolicy.git.expectedRemoteUrl) `
        -CommitAllowed ([bool]$script:FrozenPolicy.git.commitAllowed) `
        -PushAllowed ([bool]$script:FrozenPolicy.git.pushAllowed) `
        -TrustedArtifacts $script:TrustedArtifacts

    Write-Host "APPROVED_DRY_RUN tree=$($approval.ApprovedTree) parent=$($approval.ExpectedParent) branch=$($approval.ExpectedBranch) remote=$($approval.ExpectedRemote)" -ForegroundColor Green
    Write-Host "Unattended commit and push remain disabled; the final index is left staged for human review." -ForegroundColor Yellow
}
catch {
    Write-Host "Codex loop failed closed: $($_.Exception.Message)" -ForegroundColor Red
    $scriptExitCode = 1
}
finally {
    try {
        Remove-TrustedEnvelope
    }
    catch {
        Write-Host "Trusted-envelope cleanup failed: $($_.Exception.Message)" -ForegroundColor Red
        $scriptExitCode = 1
    }
}

exit $scriptExitCode
