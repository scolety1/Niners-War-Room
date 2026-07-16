function ConvertTo-NormalizedRepositoryPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $normalized = ($Path -replace "\\", "/")
    while ($normalized.StartsWith("./", [StringComparison]::Ordinal)) {
        $normalized = $normalized.Substring(2)
    }
    return $normalized.TrimStart("/")
}

function Test-RepositoryPathRule {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Rule
    )

    $normalizedPath = ConvertTo-NormalizedRepositoryPath -Path $Path
    $normalizedRule = ConvertTo-NormalizedRepositoryPath -Path $Rule
    if ([string]::IsNullOrWhiteSpace($normalizedRule)) {
        return $false
    }
    if ($normalizedRule.EndsWith("/", [StringComparison]::Ordinal)) {
        return $normalizedPath.StartsWith($normalizedRule, [StringComparison]::OrdinalIgnoreCase)
    }
    return $normalizedPath.Equals($normalizedRule, [StringComparison]::OrdinalIgnoreCase) -or
        $normalizedPath.StartsWith($normalizedRule + "/", [StringComparison]::OrdinalIgnoreCase)
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Trusted artifact is missing: $Path"
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-StringSha256 {
    param([Parameter(Mandatory = $true)][string]$Value)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Assert-FileSha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256
    )

    $actual = Get-FileSha256 -Path $Path
    if (-not $actual.Equals($ExpectedSha256, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Trusted artifact digest changed: $Path"
    }
}

function Assert-TrustedArtifactSet {
    param([Parameter(Mandatory = $true)][object[]]$Artifacts)

    foreach ($artifact in $Artifacts) {
        Assert-FileSha256 -Path ([string]$artifact.Path) -ExpectedSha256 ([string]$artifact.Sha256)
    }
}

function Lock-TrustedArtifactSet {
    param([Parameter(Mandatory = $true)][object[]]$Artifacts)

    $handles = @()
    try {
        foreach ($artifact in $Artifacts) {
            $handles += [IO.File]::Open(
                [string]$artifact.Path,
                [IO.FileMode]::Open,
                [IO.FileAccess]::Read,
                [IO.FileShare]::Read
            )
        }
        return $handles
    }
    catch {
        foreach ($handle in $handles) {
            $handle.Dispose()
        }
        throw
    }
}

function Close-TrustedArtifactSet {
    param([object[]]$Handles)

    foreach ($handle in @($Handles)) {
        if ($null -ne $handle) {
            $handle.Dispose()
        }
    }
}

function Get-TrustedEnvelopeDigest {
    param([Parameter(Mandatory = $true)][object[]]$Artifacts)

    $records = @($Artifacts | ForEach-Object {
        "{0}:{1}" -f ([string]$_.Name), ([string]$_.Sha256).ToLowerInvariant()
    } | Sort-Object)
    return Get-StringSha256 -Value ($records -join "`n")
}

function Assert-NoReparsePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Candidate
    )

    $rootItem = Get-Item -LiteralPath $Root -Force
    if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Approved root may not be a symlink or junction: $Root"
    }

    if ($Candidate.Equals($Root, [StringComparison]::OrdinalIgnoreCase)) {
        return
    }
    $rootPrefix = $Root + [IO.Path]::DirectorySeparatorChar
    $relative = $Candidate.Substring($rootPrefix.Length)
    $current = $Root
    foreach ($segment in @($relative -split "[\\/]" | Where-Object { $_.Length -gt 0 })) {
        $current = Join-Path $current $segment
        $item = Get-Item -LiteralPath $current -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Working directory crosses a symlink or junction: $current"
        }
    }
}

function Resolve-ApprovedWorkingDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$ApprovedRoot,
        [string]$RequestedPath = "."
    )

    $root = [IO.Path]::GetFullPath($ApprovedRoot).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        throw "Approved working-directory root does not exist: $root"
    }
    if ([string]::IsNullOrWhiteSpace($RequestedPath)) {
        $RequestedPath = "."
    }
    if ($RequestedPath.StartsWith("\\", [StringComparison]::Ordinal) -or
        $RequestedPath.StartsWith("//", [StringComparison]::Ordinal)) {
        throw "UNC working directories are not allowed: $RequestedPath"
    }

    $pathParts = @($RequestedPath -split "[\\/]" | Where-Object { $_.Length -gt 0 })
    if ($pathParts -contains "..") {
        throw "Working-directory traversal is not allowed: $RequestedPath"
    }

    if ([IO.Path]::IsPathRooted($RequestedPath)) {
        $candidate = [IO.Path]::GetFullPath($RequestedPath)
    }
    else {
        $candidate = [IO.Path]::GetFullPath((Join-Path $root $RequestedPath))
    }
    $candidate = $candidate.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )

    $rootDrive = [IO.Path]::GetPathRoot($root)
    $candidateDrive = [IO.Path]::GetPathRoot($candidate)
    if (-not $rootDrive.Equals($candidateDrive, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Working directory must remain on the approved drive: $RequestedPath"
    }

    $rootPrefix = $root + [IO.Path]::DirectorySeparatorChar
    $insideRoot = $candidate.Equals($root, [StringComparison]::OrdinalIgnoreCase) -or
        $candidate.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)
    if (-not $insideRoot) {
        throw "Working directory escapes the approved root: $RequestedPath"
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Container)) {
        throw "Approved working directory does not exist: $candidate"
    }

    Assert-NoReparsePath -Root $root -Candidate $candidate
    return $candidate
}

function Invoke-ApprovedExecutable {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$ApprovedRoot
    )

    $resolvedExecutable = [IO.Path]::GetFullPath($Executable)
    if (-not (Test-Path -LiteralPath $resolvedExecutable -PathType Leaf)) {
        throw "Approved executable is missing: $resolvedExecutable"
    }
    $resolvedWorkingDirectory = Resolve-ApprovedWorkingDirectory `
        -ApprovedRoot $ApprovedRoot `
        -RequestedPath $WorkingDirectory

    Push-Location $resolvedWorkingDirectory
    try {
        & $resolvedExecutable @Arguments
        return $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

function Invoke-GitChecked {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $priorErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = @(& git -c core.fsmonitor=false -C $RepoRoot @Arguments 2>&1 |
            ForEach-Object { $_.ToString() })
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $priorErrorActionPreference
    }
    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join ' ')"
    }
    return $output
}

function Get-GitNullPathList {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $output = Invoke-GitChecked -RepoRoot $RepoRoot -Arguments $Arguments
    if ($output.Count -eq 0) {
        return @()
    }
    $raw = $output -join "`n"
    return @($raw -split "`0" | Where-Object { $_.Length -gt 0 })
}

function Get-RepositoryTopLevel {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    $top = @(Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @("rev-parse", "--show-toplevel"))
    if ($top.Count -ne 1) {
        throw "Could not resolve a unique repository root."
    }
    return [IO.Path]::GetFullPath(([string]$top[0]).Trim()).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
}

function Assert-RepositoryBinding {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedRepoRoot
    )

    $requested = [IO.Path]::GetFullPath($RepoRoot).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $expected = [IO.Path]::GetFullPath($ExpectedRepoRoot).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $actual = Get-RepositoryTopLevel -RepoRoot $requested
    if (-not $requested.Equals($actual, [StringComparison]::OrdinalIgnoreCase) -or
        -not $actual.Equals($expected, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Repository root binding changed. Expected '$expected', found '$actual'."
    }
}

function Get-NonIgnoredUntrackedPaths {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    return @(Get-GitNullPathList -RepoRoot $RepoRoot -Arguments @(
        "ls-files", "--others", "--exclude-standard", "-z", "--"
    ))
}

function Get-StagedChangedPaths {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    return @(Get-GitNullPathList -RepoRoot $RepoRoot -Arguments @(
        "diff", "--cached", "--name-only", "-z", "--no-renames",
        "--diff-filter=ACDMRTUXB", "HEAD", "--"
    ) | ForEach-Object { ConvertTo-NormalizedRepositoryPath -Path $_ })
}

function Test-RepositoryHasChanges {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    $status = Get-GitNullPathList -RepoRoot $RepoRoot -Arguments @(
        "status", "--porcelain=v1", "-z", "--untracked-files=normal"
    )
    return $status.Count -gt 0
}

function Assert-NoTrackedWorkingTreeDrift {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    & git -c core.fsmonitor=false -C $RepoRoot diff --quiet --no-ext-diff --ignore-submodules=none --
    $code = $LASTEXITCODE
    if ($code -eq 1) {
        throw "Tracked working-tree drift exists after candidate staging."
    }
    if ($code -ne 0) {
        throw "Could not inspect tracked working-tree drift."
    }
}

function Assert-NoNonIgnoredUntrackedDrift {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    $untracked = @(Get-NonIgnoredUntrackedPaths -RepoRoot $RepoRoot)
    if ($untracked.Count -gt 0) {
        throw "Non-ignored untracked drift exists: $($untracked -join ', ')"
    }
}

function Stage-CandidateIndex {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    [void](Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @("add", "--all", "--", "."))
    Assert-NoTrackedWorkingTreeDrift -RepoRoot $RepoRoot
    Assert-NoNonIgnoredUntrackedDrift -RepoRoot $RepoRoot
}

function Get-IndexTreeHash {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    $tree = @(Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @("write-tree"))
    if ($tree.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$tree[0])) {
        throw "Could not record the candidate index tree."
    }
    return ([string]$tree[0]).Trim()
}

function Get-CurrentCommit {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    return (@(Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @("rev-parse", "HEAD"))[0]).ToString().Trim()
}

function Get-CurrentBranchName {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)

    $branch = @(Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @("branch", "--show-current"))
    if ($branch.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$branch[0])) {
        throw "Repository is not on an expected named branch."
    }
    return ([string]$branch[0]).Trim()
}

function Assert-ExpectedBranch {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedBranch
    )

    $actual = Get-CurrentBranchName -RepoRoot $RepoRoot
    if (-not $actual.Equals($ExpectedBranch, [StringComparison]::Ordinal)) {
        throw "Branch binding changed. Expected '$ExpectedBranch', found '$actual'."
    }
}

function Assert-ExpectedRemote {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedRemote,
        [Parameter(Mandatory = $true)][string]$ExpectedRemoteUrl
    )

    $remoteUrl = @(Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @(
        "remote", "get-url", $ExpectedRemote
    ))
    if ($remoteUrl.Count -ne 1 -or
        -not ([string]$remoteUrl[0]).Trim().Equals($ExpectedRemoteUrl, [StringComparison]::Ordinal)) {
        throw "Remote binding changed for '$ExpectedRemote'."
    }
}

function New-FinalIndexApproval {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedRepoRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedParent,
        [Parameter(Mandatory = $true)][string]$ExpectedBranch,
        [Parameter(Mandatory = $true)][string]$ExpectedRemote,
        [Parameter(Mandatory = $true)][string]$ExpectedRemoteUrl,
        [Parameter(Mandatory = $true)][bool]$CommitAllowed,
        [Parameter(Mandatory = $true)][bool]$PushAllowed,
        [Parameter(Mandatory = $true)][object[]]$TrustedArtifacts
    )

    Assert-TrustedArtifactSet -Artifacts $TrustedArtifacts
    Assert-RepositoryBinding -RepoRoot $RepoRoot -ExpectedRepoRoot $ExpectedRepoRoot
    Assert-ExpectedBranch -RepoRoot $RepoRoot -ExpectedBranch $ExpectedBranch
    Assert-ExpectedRemote -RepoRoot $RepoRoot -ExpectedRemote $ExpectedRemote -ExpectedRemoteUrl $ExpectedRemoteUrl
    $parent = Get-CurrentCommit -RepoRoot $RepoRoot
    if (-not $parent.Equals($ExpectedParent, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Parent binding changed. Expected '$ExpectedParent', found '$parent'."
    }
    Assert-NoTrackedWorkingTreeDrift -RepoRoot $RepoRoot
    Assert-NoNonIgnoredUntrackedDrift -RepoRoot $RepoRoot

    return [pscustomobject]@{
        ApprovedTree = Get-IndexTreeHash -RepoRoot $RepoRoot
        ExpectedRepoRoot = [IO.Path]::GetFullPath($ExpectedRepoRoot)
        ExpectedParent = $ExpectedParent
        ExpectedBranch = $ExpectedBranch
        ExpectedRemote = $ExpectedRemote
        ExpectedRemoteUrl = $ExpectedRemoteUrl
        CommitAllowed = $CommitAllowed
        PushAllowed = $PushAllowed
        TrustedEnvelopeDigest = Get-TrustedEnvelopeDigest -Artifacts $TrustedArtifacts
        ApprovedAtUtc = [DateTime]::UtcNow.ToString("o")
        ExpectedCommit = $null
    }
}

function Assert-ApprovalState {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)]$Approval,
        [Parameter(Mandatory = $true)][object[]]$TrustedArtifacts
    )

    Assert-TrustedArtifactSet -Artifacts $TrustedArtifacts
    $envelopeDigest = Get-TrustedEnvelopeDigest -Artifacts $TrustedArtifacts
    if (-not $envelopeDigest.Equals([string]$Approval.TrustedEnvelopeDigest, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Privileged policy envelope digest changed after approval."
    }
    Assert-RepositoryBinding -RepoRoot $RepoRoot -ExpectedRepoRoot ([string]$Approval.ExpectedRepoRoot)
    Assert-ExpectedBranch -RepoRoot $RepoRoot -ExpectedBranch ([string]$Approval.ExpectedBranch)
    Assert-ExpectedRemote `
        -RepoRoot $RepoRoot `
        -ExpectedRemote ([string]$Approval.ExpectedRemote) `
        -ExpectedRemoteUrl ([string]$Approval.ExpectedRemoteUrl)
    Assert-NoTrackedWorkingTreeDrift -RepoRoot $RepoRoot
    Assert-NoNonIgnoredUntrackedDrift -RepoRoot $RepoRoot

    $expectedHead = if ([string]::IsNullOrWhiteSpace([string]$Approval.ExpectedCommit)) {
        [string]$Approval.ExpectedParent
    }
    else {
        [string]$Approval.ExpectedCommit
    }
    $head = Get-CurrentCommit -RepoRoot $RepoRoot
    if (-not $head.Equals($expectedHead, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Parent or commit binding changed. Expected '$expectedHead', found '$head'."
    }

    $tree = Get-IndexTreeHash -RepoRoot $RepoRoot
    if (-not $tree.Equals([string]$Approval.ApprovedTree, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Index tree changed after approval."
    }
}

function Assert-ApprovalBeforeCommit {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)]$Approval,
        [Parameter(Mandatory = $true)][object[]]$TrustedArtifacts
    )

    if (-not [bool]$Approval.CommitAllowed) {
        throw "Frozen policy does not permit commit."
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$Approval.ExpectedCommit)) {
        throw "Approval already has a committed identity."
    }
    Assert-ApprovalState -RepoRoot $RepoRoot -Approval $Approval -TrustedArtifacts $TrustedArtifacts
}

function Commit-ApprovedTree {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)]$Approval,
        [Parameter(Mandatory = $true)][object[]]$TrustedArtifacts,
        [Parameter(Mandatory = $true)][string]$Message
    )

    Assert-ApprovalBeforeCommit -RepoRoot $RepoRoot -Approval $Approval -TrustedArtifacts $TrustedArtifacts
    $commit = @((Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @(
        "commit-tree", ([string]$Approval.ApprovedTree),
        "-p", ([string]$Approval.ExpectedParent), "-m", $Message
    )))[0].ToString().Trim()
    $branchRef = "refs/heads/$([string]$Approval.ExpectedBranch)"
    [void](Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @(
        "update-ref", "-m", "codex approved-tree commit", $branchRef,
        $commit, ([string]$Approval.ExpectedParent)
    ))
    $Approval.ExpectedCommit = $commit
    return $commit
}

function Assert-CommittedTree {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)]$Approval,
        [Parameter(Mandatory = $true)][object[]]$TrustedArtifacts
    )

    if ([string]::IsNullOrWhiteSpace([string]$Approval.ExpectedCommit)) {
        throw "Committed identity is missing from approval."
    }
    Assert-ApprovalState -RepoRoot $RepoRoot -Approval $Approval -TrustedArtifacts $TrustedArtifacts
    $tree = @((Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @("rev-parse", "HEAD^{tree}")))[0].ToString().Trim()
    if (-not $tree.Equals([string]$Approval.ApprovedTree, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Committed tree does not equal the approved tree."
    }
    $parent = @((Invoke-GitChecked -RepoRoot $RepoRoot -Arguments @("rev-parse", "HEAD^")))[0].ToString().Trim()
    if (-not $parent.Equals([string]$Approval.ExpectedParent, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Committed parent does not equal the approved parent."
    }
    return [string]$Approval.ExpectedCommit
}

function Assert-PushBinding {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)]$Approval,
        [Parameter(Mandatory = $true)][object[]]$TrustedArtifacts
    )

    if (-not [bool]$Approval.PushAllowed) {
        throw "Frozen policy does not permit push."
    }
    [void](Assert-CommittedTree -RepoRoot $RepoRoot -Approval $Approval -TrustedArtifacts $TrustedArtifacts)
}
