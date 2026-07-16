[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$sourceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$securityHelper = Join-Path $sourceRoot "scripts\codex-night-loop-security.ps1"
$guardrailSource = Join-Path $sourceRoot "scripts\codex-guardrails.ps1"
$nightLoopSource = Join-Path $sourceRoot "scripts\codex-night-loop.ps1"
$bootstrapSource = Join-Path $sourceRoot "scripts\bootstrap-hermetic-test-pack.ps1"
. $securityHelper

$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$scratch = Join-Path $tempRoot ("nwr-codex-night-loop-tests-" + [guid]::NewGuid().ToString("N"))
$scratchFull = [IO.Path]::GetFullPath($scratch)
$script:Passed = 0
$script:Failed = 0

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Equal {
    param([AllowNull()]$Expected, [AllowNull()]$Actual, [string]$Message)
    if ($Expected -ne $Actual) { throw "$Message Expected '$Expected', found '$Actual'." }
}

function Assert-Throws {
    param([scriptblock]$Action, [string]$Pattern = ".*")
    try { & $Action }
    catch {
        if ($_.Exception.Message -notmatch $Pattern) {
            throw "Expected failure matching '$Pattern', found '$($_.Exception.Message)'."
        }
        return
    }
    throw "Expected action to fail matching '$Pattern'."
}

function Invoke-Test {
    param([string]$Name, [scriptblock]$Action)
    try {
        & $Action
        $script:Passed++
        Write-Output "PASS $Name"
    }
    catch {
        $script:Failed++
        Write-Output "FAIL $Name :: $($_.Exception.Message)"
    }
}

function New-TestRepository {
    param([string]$Name)

    $repo = Join-Path $scratchFull $Name
    $remote = Join-Path $scratchFull ($Name + "-origin.git")
    New-Item -ItemType Directory -Path (Join-Path $repo "scripts") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $repo "docs\codex") -Force | Out-Null
    Copy-Item -LiteralPath $guardrailSource -Destination (Join-Path $repo "scripts\codex-guardrails.ps1")
    Copy-Item -LiteralPath $securityHelper -Destination (Join-Path $repo "scripts\codex-night-loop-security.ps1")
    Set-Content -LiteralPath (Join-Path $repo "allowed.txt") -Value "baseline"
    Set-Content -LiteralPath (Join-Path $repo "other.txt") -Value "baseline"
    [ordered]@{
        blockedPaths = @("package.json")
        blockedTerms = @("BLOCKED_TERM")
        buildDirectory = "."
        buildCommand = "fixed baseline"
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $repo "docs\codex\PROFILE.json") -Encoding UTF8

    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("init", "--quiet"))
    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("config", "core.autocrlf", "false"))
    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("config", "user.email", "security-test@example.invalid"))
    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("config", "user.name", "Security Test"))
    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("add", "--all", "--", "."))
    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("commit", "--quiet", "-m", "baseline"))
    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("branch", "-M", "codex/security-test"))
    [void](Invoke-GitChecked -RepoRoot $scratchFull -Arguments @("init", "--bare", "--quiet", $remote))
    [void](Invoke-GitChecked -RepoRoot $repo -Arguments @("remote", "add", "origin", $remote))
    return [pscustomobject]@{ Repo = $repo; Remote = $remote }
}

function New-TestPolicy {
    param(
        [string]$Name,
        [Parameter(Mandatory = $true)]$TestRepository,
        [bool]$CommitAllowed = $true,
        [bool]$PushAllowed = $false
    )

    $trusted = Join-Path $scratchFull ("trusted-" + $Name)
    New-Item -ItemType Directory -Path $trusted -Force | Out-Null
    $policyPath = Join-Path $trusted "frozen-policy.json"
    $sentinelPath = Join-Path $trusted "trusted-sentinel.txt"
    Set-Content -LiteralPath $sentinelPath -Value "trusted"
    $repo = [string]$TestRepository.Repo
    $parent = Get-CurrentCommit -RepoRoot $repo
    $policy = [ordered]@{
        schemaVersion = 1
        maxChangedFiles = 12
        allowedPaths = @("allowed.txt", "other.txt", "new-allowed.txt", "docs/", "scripts/")
        blockedPaths = @("package.json")
        blockedTerms = @("BLOCKED_TERM")
        protectedPaths = @(
            "docs/codex/PROFILE.json",
            "scripts/codex-night-loop.ps1",
            "scripts/codex-guardrails.ps1",
            "scripts/codex-night-loop-security.ps1",
            "scripts/codex-static-check.ps1"
        )
        git = [ordered]@{
            expectedRepoRoot = $repo
            expectedParent = $parent
            expectedBranch = "codex/security-test"
            expectedRemote = "origin"
            expectedRemoteUrl = [string]$TestRepository.Remote
            commitAllowed = $CommitAllowed
            pushAllowed = $PushAllowed
        }
    }
    $policy | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $policyPath -Encoding UTF8
    $policySha = Get-FileSha256 -Path $policyPath
    $artifacts = @(
        [pscustomobject]@{ Name = "policy"; Path = $policyPath; Sha256 = $policySha },
        [pscustomobject]@{ Name = "sentinel"; Path = $sentinelPath; Sha256 = Get-FileSha256 -Path $sentinelPath }
    )
    return [pscustomobject]@{ Path = $policyPath; Sha256 = $policySha; Artifacts = $artifacts; Data = $policy }
}

function Invoke-TestGuardrail {
    param([string]$Repo, [Parameter(Mandatory = $true)]$Policy)
    $output = @(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
        -File (Join-Path $Repo "scripts\codex-guardrails.ps1") `
        -RepoRoot $Repo `
        -PolicySnapshotPath $Policy.Path `
        -ExpectedPolicySha256 $Policy.Sha256 `
        -Stage "security-regression" `
        -MaxChangedFiles 12 2>&1)
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = ($output -join "`n") }
}

function New-TestApproval {
    param(
        [Parameter(Mandatory = $true)]$TestRepository,
        [Parameter(Mandatory = $true)]$Policy,
        [bool]$CommitAllowed = $true,
        [bool]$PushAllowed = $false
    )
    $repo = [string]$TestRepository.Repo
    $guardrail = Invoke-TestGuardrail -Repo $repo -Policy $Policy
    Assert-Equal 0 $guardrail.ExitCode "Candidate guardrail should pass."
    return New-FinalIndexApproval `
        -RepoRoot $repo `
        -ExpectedRepoRoot $repo `
        -ExpectedParent ([string]$Policy.Data.git.expectedParent) `
        -ExpectedBranch "codex/security-test" `
        -ExpectedRemote "origin" `
        -ExpectedRemoteUrl ([string]$TestRepository.Remote) `
        -CommitAllowed $CommitAllowed `
        -PushAllowed $PushAllowed `
        -TrustedArtifacts $Policy.Artifacts
}

function Copy-Approval {
    param([Parameter(Mandatory = $true)]$Approval)
    return [pscustomobject]@{
        ApprovedTree = [string]$Approval.ApprovedTree
        ExpectedRepoRoot = [string]$Approval.ExpectedRepoRoot
        ExpectedParent = [string]$Approval.ExpectedParent
        ExpectedBranch = [string]$Approval.ExpectedBranch
        ExpectedRemote = [string]$Approval.ExpectedRemote
        ExpectedRemoteUrl = [string]$Approval.ExpectedRemoteUrl
        CommitAllowed = [bool]$Approval.CommitAllowed
        PushAllowed = [bool]$Approval.PushAllowed
        TrustedEnvelopeDigest = [string]$Approval.TrustedEnvelopeDigest
        ApprovedAtUtc = [string]$Approval.ApprovedAtUtc
        ExpectedCommit = [string]$Approval.ExpectedCommit
    }
}

try {
    New-Item -ItemType Directory -Path $scratchFull -Force | Out-Null

    Invoke-Test "01 pre-staged prohibited content rejects" {
        $t = New-TestRepository "prestaged"
        $p = New-TestPolicy "prestaged" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "BLOCKED_TERM in index"
        [void](Invoke-GitChecked $t.Repo @("add", "--", "allowed.txt"))
        $r = Invoke-TestGuardrail $t.Repo $p
        Assert-True ($r.ExitCode -ne 0 -and $r.Output -match "Blocked term") "Pre-staged content bypassed policy."
    }

    Invoke-Test "02 untracked prohibited content rejects" {
        $t = New-TestRepository "untracked-prohibited"
        $p = New-TestPolicy "untracked-prohibited" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "new-allowed.txt") -Value "BLOCKED_TERM from untracked"
        Stage-CandidateIndex $t.Repo
        $r = Invoke-TestGuardrail $t.Repo $p
        Assert-True ($r.ExitCode -ne 0 -and $r.Output -match "Blocked term") "Untracked content bypassed policy."
    }

    Invoke-Test "03 benign final index passes" {
        $t = New-TestRepository "benign"
        $p = New-TestPolicy "benign" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "new-allowed.txt") -Value "benign"
        Stage-CandidateIndex $t.Repo
        $r = Invoke-TestGuardrail $t.Repo $p
        Assert-Equal 0 $r.ExitCode "Benign final index failed."
    }

    Invoke-Test "04 cached diff is the reviewed diff" {
        $t = New-TestRepository "cached-diff"
        $p = New-TestPolicy "cached-diff" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "pre-staged"
        [void](Invoke-GitChecked $t.Repo @("add", "--", "allowed.txt"))
        Set-Content -LiteralPath (Join-Path $t.Repo "new-allowed.txt") -Value "formerly untracked"
        Stage-CandidateIndex $t.Repo
        $paths = @(Get-StagedChangedPaths $t.Repo | Sort-Object)
        Assert-Equal "allowed.txt,new-allowed.txt" ($paths -join ",") "Final cached path set differed."
        $tree = Get-IndexTreeHash $t.Repo
        $r = Invoke-TestGuardrail $t.Repo $p
        Assert-True ($r.ExitCode -eq 0 -and $r.Output -match [regex]::Escape($tree)) "Guardrail did not review the write-tree identity."
    }

    Invoke-Test "05 index drift rejects" {
        $t = New-TestRepository "index-drift"
        $p = New-TestPolicy "index-drift" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p
        Set-Content -LiteralPath (Join-Path $t.Repo "other.txt") -Value "late staged"
        [void](Invoke-GitChecked $t.Repo @("add", "--", "other.txt"))
        Assert-Throws { Assert-ApprovalState $t.Repo $a $p.Artifacts } "Index tree changed"
    }

    Invoke-Test "06 unstaged tracked drift rejects" {
        $t = New-TestRepository "tracked-drift"
        $p = New-TestPolicy "tracked-drift" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "late unstaged"
        Assert-Throws { Assert-ApprovalState $t.Repo $a $p.Artifacts } "working-tree drift"
    }

    Invoke-Test "07 untracked drift rejects" {
        $t = New-TestRepository "untracked-drift"
        $p = New-TestPolicy "untracked-drift" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p
        Set-Content -LiteralPath (Join-Path $t.Repo "late.txt") -Value "late untracked"
        Assert-Throws { Assert-ApprovalState $t.Repo $a $p.Artifacts } "untracked drift"
    }

    Invoke-Test "08 policy and profile tampering has no effect" {
        $t = New-TestRepository "profile-tamper"
        $p = New-TestPolicy "profile-tamper" $t
        $profilePath = Join-Path $t.Repo "docs\codex\PROFILE.json"
        $profile = Get-Content -LiteralPath $profilePath -Raw | ConvertFrom-Json
        $profile.blockedTerms = @()
        $profile.buildCommand = "Set-Content SHOULD_NOT_RUN"
        $profile | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $profilePath -Encoding UTF8
        Stage-CandidateIndex $t.Repo
        $r = Invoke-TestGuardrail $t.Repo $p
        Assert-True ($r.ExitCode -ne 0 -and $r.Output -match "Privileged automation") "Profile redefined frozen policy."

        $t2 = New-TestRepository "policy-tamper"
        $p2 = New-TestPolicy "policy-tamper" $t2
        Set-Content -LiteralPath (Join-Path $t2.Repo "allowed.txt") -Value "approved"
        Stage-CandidateIndex $t2.Repo
        $a2 = New-TestApproval $t2 $p2
        Add-Content -LiteralPath $p2.Path -Value " "
        Assert-Throws { Assert-ApprovalState $t2.Repo $a2 $p2.Artifacts } "digest changed"
    }

    Invoke-Test "09 repository command text is never executed" {
        $badMarker = Join-Path $scratchFull "bad-command-marker.txt"
        $nightText = Get-Content -LiteralPath $nightLoopSource -Raw
        Assert-True ($nightText -notmatch "(?i)Invoke-Expression|\biex\b") "Expression-evaluation sink remains."
        Assert-True ($nightText -notmatch [regex]::Escape($badMarker)) "Unexpected marker reference."
        Assert-True ($nightText -match "fixed approved static-check command") "Fixed-command admission is absent."
    }

    Invoke-Test "10 structured approved command runs" {
        $t = New-TestRepository "structured-command"
        $output = Join-Path $scratchFull "structured.txt"
        $script = Join-Path $scratchFull "structured.ps1"
        @'
param([string]$OutputPath, [string]$Value)
[IO.File]::WriteAllText($OutputPath, $Value, [Text.Encoding]::UTF8)
exit 0
'@ | Set-Content -LiteralPath $script -Encoding UTF8
        $literal = 'literal; Write-Output INERT $(not-run)'
        $powershell = [IO.Path]::GetFullPath((Get-Command powershell.exe -CommandType Application).Source)
        $code = Invoke-ApprovedExecutable $powershell @("-NoProfile", "-File", $script, "-OutputPath", $output, "-Value", $literal) "." $t.Repo
        Assert-Equal 0 $code "Approved structured command failed."
        Assert-Equal $literal ([IO.File]::ReadAllText($output, [Text.Encoding]::UTF8)) "Argument was reinterpreted."
    }

    Invoke-Test "11 working-directory traversal rejects" {
        $t = New-TestRepository "traversal"
        New-Item -ItemType Directory -Path (Join-Path $t.Repo "inside") | Out-Null
        [void](Resolve-ApprovedWorkingDirectory $t.Repo "inside")
        Assert-Throws { [void](Resolve-ApprovedWorkingDirectory $t.Repo "..\outside") } "traversal"
    }

    Invoke-Test "12 out-of-root UNC and alternate-drive paths reject" {
        $t = New-TestRepository "path-escape"
        Assert-Throws { [void](Resolve-ApprovedWorkingDirectory $t.Repo $scratchFull) } "escapes"
        Assert-Throws { [void](Resolve-ApprovedWorkingDirectory $t.Repo "\\server\share") } "UNC"
        Assert-Throws { [void](Resolve-ApprovedWorkingDirectory $t.Repo "D:\outside") } "drive"
    }

    Invoke-Test "13 exact commit tree is enforced" {
        $t = New-TestRepository "exact-commit"
        $p = New-TestPolicy "exact-commit" $t $true $false
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved commit"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p $true $false
        $commit = Commit-ApprovedTree $t.Repo $a $p.Artifacts "approved"
        Assert-Equal $commit (Assert-CommittedTree $t.Repo $a $p.Artifacts) "Commit identity differed."
        $tree = @((Invoke-GitChecked $t.Repo @("rev-parse", "HEAD^{tree}")))[0].ToString().Trim()
        Assert-Equal $a.ApprovedTree $tree "Committed tree differed from approval."
    }

    Invoke-Test "14 wrong parent rejects" {
        $t = New-TestRepository "wrong-parent"
        $p = New-TestPolicy "wrong-parent" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p
        $bad = Copy-Approval $a
        $bad.ExpectedParent = "0000000000000000000000000000000000000000"
        Assert-Throws { Assert-ApprovalState $t.Repo $bad $p.Artifacts } "Parent or commit binding"
    }

    Invoke-Test "15 wrong branch rejects" {
        $t = New-TestRepository "wrong-branch"
        $p = New-TestPolicy "wrong-branch" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p
        $bad = Copy-Approval $a
        $bad.ExpectedBranch = "codex/unapproved"
        Assert-Throws { Assert-ApprovalState $t.Repo $bad $p.Artifacts } "Branch binding"
    }

    Invoke-Test "16 wrong remote and repository root reject" {
        $t = New-TestRepository "wrong-remote"
        $p = New-TestPolicy "wrong-remote" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p
        $badRoot = Copy-Approval $a
        $badRoot.ExpectedRepoRoot = $scratchFull
        Assert-Throws { Assert-ApprovalState $t.Repo $badRoot $p.Artifacts } "Repository root binding"
        [void](Invoke-GitChecked $t.Repo @("remote", "set-url", "origin", (Join-Path $scratchFull "other.git")))
        Assert-Throws { Assert-ApprovalState $t.Repo $a $p.Artifacts } "Remote binding"
    }

    Invoke-Test "17 push binding accepts only exact authorized tuple" {
        $t = New-TestRepository "push-tuple"
        $p = New-TestPolicy "push-tuple" $t $true $true
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "approved push"
        Stage-CandidateIndex $t.Repo
        $a = New-TestApproval $t $p $true $true
        [void](Commit-ApprovedTree $t.Repo $a $p.Artifacts "approved")
        Assert-PushBinding $t.Repo $a $p.Artifacts
        $bad = Copy-Approval $a
        $bad.ApprovedTree = "0000000000000000000000000000000000000000"
        Assert-Throws { Assert-PushBinding $t.Repo $bad $p.Artifacts } "Index tree changed|Committed tree"
    }

    Invoke-Test "18 no force-push path exists" {
        $nightText = Get-Content -LiteralPath $nightLoopSource -Raw
        Assert-True ($nightText -notmatch "(?i)git\s+push|--force|-f\s+origin") "Supervisor contains a push or force-push execution path."
        Assert-True ($nightText -match "Unattended push is disabled") "Push fail-closed control is absent."
    }

    Invoke-Test "19 legitimate approval-only dry-run remains available" {
        $nightText = Get-Content -LiteralPath $nightLoopSource -Raw
        Assert-True ($nightText -match "APPROVED_DRY_RUN") "Dry-run approval receipt is absent."
        Assert-True ($nightText -match 'commitAllowed\s*=\s*\$false') "Auto-commit is not frozen off."
        Assert-True ($nightText -match 'pushAllowed\s*=\s*\$false') "Auto-push is not frozen off."
        Assert-True ($nightText -notmatch "Commit-ApprovedTree") "Production supervisor invokes a commit primitive."
    }

    Invoke-Test "20 controls work after Hermetic bootstrap" {
        Assert-True (Test-Path -LiteralPath $bootstrapSource -PathType Leaf) "Hermetic bootstrap is missing."
        $outputRoot = Join-Path $sourceRoot "local_exports\hermetic_test_pack_v1"
        & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $bootstrapSource -RepoRoot $sourceRoot -OutputRoot $outputRoot -Clean *> $null
        Assert-Equal 0 $LASTEXITCODE "Hermetic bootstrap failed before security control."
        $t = New-TestRepository "post-bootstrap-control"
        $p = New-TestPolicy "post-bootstrap-control" $t
        Set-Content -LiteralPath (Join-Path $t.Repo "allowed.txt") -Value "BLOCKED_TERM remains blocked"
        Stage-CandidateIndex $t.Repo
        $r = Invoke-TestGuardrail $t.Repo $p
        Assert-True ($r.ExitCode -ne 0 -and $r.Output -match "Blocked term") "Bootstrap weakened security controls."
    }
}
finally {
    $safePrefix = "nwr-codex-night-loop-tests-"
    $isUnderTemp = $scratchFull.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)
    $hasSafeName = [IO.Path]::GetFileName($scratchFull).StartsWith($safePrefix, [StringComparison]::Ordinal)
    if ((Test-Path -LiteralPath $scratchFull) -and $isUnderTemp -and $hasSafeName) {
        Remove-Item -LiteralPath $scratchFull -Recurse -Force
    }
}

Write-Output "RESULT passed=$script:Passed failed=$script:Failed"
if ($script:Failed -gt 0) { exit 1 }
