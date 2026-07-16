[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$bootstrap = Join-Path $repo "scripts\bootstrap-hermetic-test-pack.ps1"
$verify = Join-Path $repo "scripts\verify-repository.ps1"
$ownedRoot = [IO.Path]::GetFullPath((Join-Path $repo "local_exports"))
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$runId = [guid]::NewGuid().ToString("N")
$outputA = Join-Path $ownedRoot ("hermetic_test_pack_v1-contract-a-" + $runId)
$outputB = Join-Path $ownedRoot ("hermetic_test_pack_v1-contract-b-" + $runId)
$freshCheckout = Join-Path $tempRoot ("nwr-hermetic-checkout-" + $runId)
$patchFile = Join-Path $tempRoot ("nwr-hermetic-candidate-" + $runId + ".patch")
$localManifest = Join-Path $ownedRoot "LOCAL_TEST_PACK_MANIFEST.json"
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

function Assert-Fails {
    param([scriptblock]$Action, [string]$Pattern = ".*")
    $result = & $Action
    if ($result.ExitCode -eq 0 -or $result.Output -notmatch $Pattern) {
        throw "Expected failure matching '$Pattern'; code=$($result.ExitCode), output=$($result.Output)"
    }
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

function Invoke-PowerShellScript {
    param([string]$Path, [string[]]$Arguments)
    $prior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $lines = @(& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $Path @Arguments 2>&1 |
            ForEach-Object { $_.ToString() })
        $code = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $prior }
    return [pscustomobject]@{ ExitCode = $code; Output = ($lines -join "`n") }
}

function Invoke-Bootstrap {
    param([string]$Root, [switch]$Clean, [switch]$VerifyOnly)
    $args = @("-RepoRoot", $repo, "-OutputRoot", $Root)
    if ($Clean) { $args += "-Clean" }
    if ($VerifyOnly) { $args += "-VerifyOnly" }
    return Invoke-PowerShellScript $bootstrap $args
}

function Assert-SafeOwnedOutput {
    param([string]$Path)
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = $ownedRoot.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not [IO.Path]::GetFileName($full).StartsWith("hermetic_test_pack_v1-contract-", [StringComparison]::Ordinal)) {
        throw "Refusing cleanup outside the contract-test output root: $full"
    }
}

try {
    if (Test-Path -LiteralPath $localManifest) {
        throw "LocalData contract tests require the explicit pack manifest to be genuinely absent."
    }

    Invoke-Test "01 fresh disposable checkout succeeds" {
        & git -c core.fsmonitor=false -C $repo diff --cached --binary --output=$patchFile HEAD --
        if ($LASTEXITCODE -ne 0) { throw "Could not snapshot the staged candidate." }
        & git -c core.fsmonitor=false -C $repo worktree add --quiet --detach $freshCheckout HEAD
        if ($LASTEXITCODE -ne 0) { throw "Could not create disposable checkout." }
        if ((Get-Item -LiteralPath $patchFile).Length -gt 0) {
            & git -c core.fsmonitor=false -C $freshCheckout apply --index $patchFile
            if ($LASTEXITCODE -ne 0) { throw "Could not apply candidate overlay to disposable checkout." }
            # git apply materializes a newly introduced -text attribute and its payload in one
            # operation. Windows Git may convert that payload before observing the new attribute.
            # Restore the candidate's exact fixture bytes; a committed fresh checkout needs no fixup.
            $candidateFixture = Join-Path $repo "tests\fixtures\hermetic\local_export_pack_v1"
            $freshFixture = Join-Path $freshCheckout "tests\fixtures\hermetic\local_export_pack_v1"
            Copy-Item -LiteralPath (Join-Path $candidateFixture "fixture-manifest.json") `
                -Destination (Join-Path $freshFixture "fixture-manifest.json") -Force
            Copy-Item -LiteralPath (Join-Path $candidateFixture "payload\families.csv") `
                -Destination (Join-Path $freshFixture "payload\families.csv") -Force
        }
        $freshBootstrap = Join-Path $freshCheckout "scripts\bootstrap-hermetic-test-pack.ps1"
        $freshOutput = Join-Path $freshCheckout "local_exports\hermetic_test_pack_v1"
        $r = Invoke-PowerShellScript $freshBootstrap @("-RepoRoot", $freshCheckout, "-OutputRoot", $freshOutput, "-Clean")
        Assert-True ($r.ExitCode -eq 0 -and $r.Output -match "HERMETIC_BOOTSTRAP_READY") "Fresh checkout bootstrap failed: $($r.Output)"
    }

    Invoke-Test "02 independent runs have identical manifests and hashes" {
        $a = Invoke-Bootstrap $outputA -Clean
        $b = Invoke-Bootstrap $outputB -Clean
        Assert-Equal 0 $a.ExitCode "First materialization failed."
        Assert-Equal 0 $b.ExitCode "Second materialization failed."
        foreach ($relative in @("PACK_MANIFEST.json", "SHA256SUMS", ".nwr-hermetic-owned", "payload\families.csv")) {
            $hashA = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $outputA $relative)).Hash
            $hashB = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $outputB $relative)).Hash
            Assert-Equal $hashA $hashB "Independent bytes differ for $relative."
        }
    }

    Invoke-Test "03 rerun is idempotent" {
        $before = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $outputA "SHA256SUMS")).Hash
        $r = Invoke-Bootstrap $outputA
        $after = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $outputA "SHA256SUMS")).Hash
        Assert-Equal 0 $r.ExitCode "Idempotent rerun failed."
        Assert-Equal $before $after "Idempotent rerun changed its receipt."
    }

    Invoke-Test "04 corrupt output is detected" {
        Add-Content -LiteralPath (Join-Path $outputA "payload\families.csv") -Value "corrupt"
        $r = Invoke-Bootstrap $outputA -VerifyOnly
        Assert-True ($r.ExitCode -ne 0 -and $r.Output -match "corruption") "Corrupt payload was accepted."
        $repair = Invoke-Bootstrap $outputA -Clean
        Assert-Equal 0 $repair.ExitCode "Pack repair failed."
    }

    Invoke-Test "05 path escape rejects" {
        $outside = Join-Path $tempRoot ("hermetic_test_pack_v1-outside-" + $runId)
        Assert-Fails { Invoke-Bootstrap $outside } "escapes"
    }

    Invoke-Test "06 unowned files survive owned cleanup" {
        $unowned = Join-Path $outputA "user-owned-sentinel.txt"
        Set-Content -LiteralPath $unowned -Value "must survive"
        $r = Invoke-Bootstrap $outputA -Clean
        Assert-Equal 0 $r.ExitCode "Owned cleanup bootstrap failed."
        Assert-True (Test-Path -LiteralPath $unowned -PathType Leaf) "Owned cleanup deleted an unowned file."
    }

    Invoke-Test "07 generated rows are visibly fictional and bounded" {
        $rows = Import-Csv -LiteralPath (Join-Path $outputB "payload\families.csv")
        Assert-Equal 11 $rows.Count "Fixture family count changed."
        foreach ($row in $rows) {
            Assert-Equal "FICTIONAL_TEST_FIXTURE_NOT_REAL" $row.fixture_label "Fixture label is not explicit."
            Assert-True $row.entity_id.StartsWith("fictional_", [StringComparison]::Ordinal) "Fixture identifier is not fictional."
        }
        Assert-True ((Get-Item -LiteralPath (Join-Path $outputB "payload\families.csv")).Length -lt 65536) "Fixture output is unbounded."
    }

    Invoke-Test "08 bootstrap contains zero network execution paths" {
        $text = Get-Content -LiteralPath $bootstrap -Raw
        Assert-True ($text -notmatch "(?i)Invoke-WebRequest|Invoke-RestMethod|Start-BitsTransfer|\bcurl(\.exe)?\b|\bwget(\.exe)?\b|https?://") "Bootstrap contains a network path."
    }

    Invoke-Test "09 no arbitrary local evidence is consumed" {
        $manifest = Get-Content -LiteralPath (Join-Path $outputB "PACK_MANIFEST.json") -Raw | ConvertFrom-Json
        $tracked = Join-Path $repo "tests\fixtures\hermetic\local_export_pack_v1\payload\families.csv"
        Assert-Equal ((Get-FileHash -Algorithm SHA256 -LiteralPath $tracked).Hash.ToLowerInvariant()) ([string]$manifest.files[0].sha256) "Output did not bind to tracked fixture bytes."
        Assert-True (-not [bool]$manifest.networkRequired) "Output claims an external dependency."
    }

    Invoke-Test "10 missing LocalData returns exact exit four" {
        $r = Invoke-PowerShellScript $verify @("-Tier", "LocalData", "-RepoRoot", $repo)
        Assert-Equal 4 $r.ExitCode "Missing LocalData exit code changed."
        Assert-True ($r.Output -match "(?m)^BLOCKED_MISSING_LOCAL_TEST_PACK$") "Exact missing-pack marker is absent."
        Assert-True ($r.Output -notmatch "passed|skipped|xfailed") "Missing LocalData was falsely classified as a test result."
    }

    Invoke-Test "11 malformed LocalData manifest rejects" {
        [IO.File]::WriteAllText($localManifest, "{ malformed", [Text.UTF8Encoding]::new($false))
        try {
            $r = Invoke-PowerShellScript $verify @("-Tier", "LocalData", "-RepoRoot", $repo)
            Assert-Equal 2 $r.ExitCode "Malformed LocalData manifest exit code changed."
        }
        finally { Remove-Item -LiteralPath $localManifest -Force }
    }

    Invoke-Test "12 wrong LocalData version rejects" {
        $bad = [ordered]@{
            schemaVersion = 1
            packId = "nwr-local-data-receipt-pack"
            version = "0.0.0"
            rights = [ordered]@{ ownerAuthorized = $true; noRedistribution = $true; noCheckIn = $true }
        }
        $bad | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $localManifest -Encoding UTF8
        try {
            $r = Invoke-PowerShellScript $verify @("-Tier", "LocalData", "-RepoRoot", $repo)
            Assert-Equal 2 $r.ExitCode "Wrong LocalData version exit code changed."
        }
        finally { Remove-Item -LiteralPath $localManifest -Force }
    }

    Invoke-Test "13 unapproved LocalData root rejects" {
        $outside = Join-Path $tempRoot ("nwr-unapproved-local-pack-" + $runId)
        $r = Invoke-PowerShellScript $verify @("-Tier", "LocalData", "-RepoRoot", $repo, "-LocalPackRoot", $outside)
        Assert-Equal 2 $r.ExitCode "Unapproved LocalData root exit code changed."
    }

    if ($env:NWR_HERMETIC_GATE_ACTIVE -ne "1") {
        Invoke-Test "14 Developer aggregate preserves Hermetic result when LocalData blocks" {
            $r = Invoke-PowerShellScript $verify @("-Tier", "Developer", "-RepoRoot", $repo)
            Assert-Equal 4 $r.ExitCode "Developer aggregate did not preserve the LocalData block."
            Assert-True ($r.Output -match "DEVELOPER_HERMETIC_RESULT exit=0") "Hermetic result is not independently visible."
            Assert-True ($r.Output -match "DEVELOPER_LOCALDATA_RESULT exit=4") "LocalData result is not independently visible."
        }
    }
}
finally {
    if (Test-Path -LiteralPath $localManifest -PathType Leaf) {
        Remove-Item -LiteralPath $localManifest -Force
    }
    foreach ($path in @($outputA, $outputB)) {
        Assert-SafeOwnedOutput $path
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force }
    }
    $freshFull = [IO.Path]::GetFullPath($freshCheckout)
    $safeFresh = $freshFull.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and
        [IO.Path]::GetFileName($freshFull).StartsWith("nwr-hermetic-checkout-", [StringComparison]::Ordinal)
    if ((Test-Path -LiteralPath $freshFull) -and $safeFresh) {
        & git -c core.fsmonitor=false -C $repo worktree remove --force $freshFull *> $null
    }
    if ((Test-Path -LiteralPath $patchFile -PathType Leaf) -and
        [IO.Path]::GetFileName($patchFile).StartsWith("nwr-hermetic-candidate-", [StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $patchFile -Force
    }
}

Write-Output "RESULT passed=$script:Passed failed=$script:Failed"
if ($script:Failed -gt 0) { exit 1 }
