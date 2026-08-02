[CmdletBinding()]
param(
    [ValidateSet("Hermetic", "LocalData", "Developer")]
    [string]$Tier = "Developer",
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$LocalPackRoot
)

$ErrorActionPreference = "Stop"
$ExitTestFailure = 1
$ExitContractFailure = 2
$ExitDifferentialFailure = 3
$ExitMissingLocalPack = 4
$ExitBindingFailure = 5

function Write-CommandOutput {
    param([object[]]$Lines)
    foreach ($line in @($Lines)) { Write-Host ([string]$line) }
}

function Invoke-NativeChecked {
    param([string]$Executable, [string[]]$Arguments, [string]$Label)
    $prior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = @(& $Executable @Arguments 2>&1 | ForEach-Object { $_.ToString() })
        $code = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $prior }
    Write-CommandOutput $output
    if ($code -ne 0) {
        Write-Host "$Label failed with exit code $code." -ForegroundColor Red
    }
    return [int]$code
}

function Get-RepositoryRoot {
    param([string]$RequestedRoot)
    $requested = [IO.Path]::GetFullPath($RequestedRoot).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $output = @(& git -c core.fsmonitor=false -C $requested rev-parse --show-toplevel 2>&1)
    if ($LASTEXITCODE -ne 0 -or $output.Count -ne 1) { throw "Repository binding could not be resolved." }
    $actual = [IO.Path]::GetFullPath(([string]$output[0]).Trim()).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    if (-not $actual.Equals($requested, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Repository binding mismatch."
    }
    return $actual
}

function Get-TierContract {
    param([string]$Repo)
    $path = Join-Path $Repo "tests\hermetic_localdata_manifest.json"
    try { $contract = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }
    catch { throw "Tier contract is malformed: $($_.Exception.Message)" }
    if ($contract.schemaVersion -ne 1 -or $contract.tier -ne "LocalData" -or
        $contract.pack.packId -ne "nwr-local-data-receipt-pack" -or
        $contract.pack.version -ne "1.0.0" -or
        $contract.pack.allowedRoot -ne "local_exports" -or
        $contract.pack.manifestFile -ne "LOCAL_TEST_PACK_MANIFEST.json" -or
        -not [bool]$contract.pack.noCopy -or -not [bool]$contract.pack.noCheckIn -or
        [bool]$contract.pack.arbitraryDiskFallback) {
        throw "Tier contract fields are invalid."
    }
    $seen = @{}
    foreach ($file in @($contract.testFiles)) {
        $relative = ([string]$file) -replace "\\", "/"
        if (-not $relative.StartsWith("tests/test_", [StringComparison]::Ordinal) -or
            -not $relative.EndsWith(".py", [StringComparison]::Ordinal) -or
            $relative -match "(^|/)\.\.(/|$)" -or $seen.ContainsKey($relative)) {
            throw "Tier contract contains an invalid or duplicate test path: $relative"
        }
        $seen[$relative] = $true
        if (-not (Test-Path -LiteralPath (Join-Path $Repo $relative) -PathType Leaf)) {
            throw "Tier contract test file is missing: $relative"
        }
    }
    return $contract
}

function Resolve-Uv {
    $command = Get-Command uv.exe -CommandType Application -ErrorAction Stop
    return [IO.Path]::GetFullPath($command.Source)
}

function Get-OfflinePythonPrefix {
    return @(
        "run", "--offline", "--no-project",
        "--with", "pytest",
        "--with", "ruff",
        "--with", "nflreadpy",
        "--with", "numpy",
        "--with", "pandas",
        "--with", "pydantic",
        "--with", "streamlit"
    )
}

function Invoke-HermeticTier {
    param([string]$Repo, [Parameter(Mandatory = $true)]$Contract)
    Write-Host "HERMETIC_TIER_BEGIN" -ForegroundColor Cyan
    $bootstrap = Join-Path $Repo "scripts\bootstrap-hermetic-test-pack.ps1"
    $packRoot = Join-Path $Repo "local_exports\hermetic_test_pack_v1"
    $bootstrapCode = Invoke-NativeChecked powershell.exe @(
        "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $bootstrap,
        "-RepoRoot", $Repo, "-OutputRoot", $packRoot, "-Clean"
    ) "Hermetic bootstrap"
    if ($bootstrapCode -ne 0) { return $ExitContractFailure }

    $priorPack = $env:NWR_HERMETIC_PACK_ROOT
    $priorActive = $env:NWR_HERMETIC_GATE_ACTIVE
    $env:NWR_HERMETIC_PACK_ROOT = $packRoot
    $env:NWR_HERMETIC_GATE_ACTIVE = "1"
    try {
        $bootstrapTests = Join-Path $Repo "scripts\tests\test-hermetic-bootstrap.ps1"
        $bootstrapTestCode = Invoke-NativeChecked powershell.exe @(
            "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $bootstrapTests
        ) "Hermetic bootstrap controls"
        if ($bootstrapTestCode -ne 0) { return $ExitTestFailure }

        $securityTests = Join-Path $Repo "scripts\tests\test-codex-night-loop-security.ps1"
        $securityCode = Invoke-NativeChecked powershell.exe @(
            "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", $securityTests
        ) "Focused security controls"
        if ($securityCode -ne 0) { return $ExitTestFailure }

        $localSet = @{}
        foreach ($file in @($Contract.testFiles)) { $localSet[([string]$file).Replace("\", "/")] = $true }
        $hermeticFiles = @(
            Get-ChildItem -LiteralPath (Join-Path $Repo "tests") -Filter "test_*.py" -File -Recurse |
                ForEach-Object {
                    ($_.FullName.Substring($Repo.Length).TrimStart([char[]]"\/") -replace "\\", "/")
                } |
                Where-Object { -not $localSet.ContainsKey($_) } |
                Sort-Object
        )
        if ($hermeticFiles.Count -eq 0 -or
            $hermeticFiles -notcontains "tests/test_hermetic_fixture_families.py") {
            Write-Host "Hermetic collection contract is empty or missing its fixture-family tests." -ForegroundColor Red
            return $ExitContractFailure
        }
        $uv = Resolve-Uv
        $pytestArgs = @(Get-OfflinePythonPrefix) + @(
            "python", "-m", "pytest", "-q", "-ra", "--strict-markers",
            "-p", "scripts.pytest_no_skips_plugin"
        ) + $hermeticFiles
        $pytestCode = Invoke-NativeChecked $uv $pytestArgs "Hermetic pytest collection"
        if ($pytestCode -ne 0) { return $ExitTestFailure }

        $ruffCode = Invoke-NativeChecked $uv @(
            "run", "--offline", "--no-project", "--with", "ruff", "ruff", "check",
            "tests/test_hermetic_fixture_families.py"
        ) "Owned Python Ruff check"
        if ($ruffCode -ne 0) { return $ExitTestFailure }
    }
    finally {
        $env:NWR_HERMETIC_PACK_ROOT = $priorPack
        $env:NWR_HERMETIC_GATE_ACTIVE = $priorActive
    }
    Write-Host "HERMETIC_TIER_PASS" -ForegroundColor Green
    return 0
}

function Invoke-LocalDataTier {
    param([string]$Repo, [Parameter(Mandatory = $true)]$Contract, [string]$RequestedPackRoot)
    Write-Host "LOCALDATA_TIER_BEGIN" -ForegroundColor Cyan
    $allowed = [IO.Path]::GetFullPath((Join-Path $Repo "local_exports")).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $requested = if ([string]::IsNullOrWhiteSpace($RequestedPackRoot)) {
        $allowed
    }
    else {
        [IO.Path]::GetFullPath($RequestedPackRoot).TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        )
    }
    if (-not $requested.Equals($allowed, [StringComparison]::OrdinalIgnoreCase)) {
        Write-Host "LocalData root is not the single approved repository-local root." -ForegroundColor Red
        return $ExitContractFailure
    }
    $manifestPath = Join-Path $requested ([string]$Contract.pack.manifestFile)
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        Write-Host "BLOCKED_MISSING_LOCAL_TEST_PACK"
        Write-Host "Required governed manifest: local_exports/$([string]$Contract.pack.manifestFile)"
        Write-Host "Required pack: $([string]$Contract.pack.packId) version $([string]$Contract.pack.version)"
        Write-Host "Owner action: install the authorized pack at the governed local path; no search, copy, or reconstruction was attempted."
        return $ExitMissingLocalPack
    }
    try { $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json }
    catch {
        Write-Host "LocalData manifest is malformed: $($_.Exception.Message)" -ForegroundColor Red
        return $ExitContractFailure
    }
    if ($manifest.schemaVersion -ne 1 -or
        $manifest.packId -ne [string]$Contract.pack.packId -or
        $manifest.version -ne [string]$Contract.pack.version -or
        -not [bool]$manifest.rights.ownerAuthorized -or
        -not [bool]$manifest.rights.noRedistribution -or
        -not [bool]$manifest.rights.noCheckIn) {
        Write-Host "LocalData manifest contract or rights attestation is invalid." -ForegroundColor Red
        return $ExitContractFailure
    }

    $uv = Resolve-Uv
    $pytestArgs = @(Get-OfflinePythonPrefix) + @(
        "python", "-m", "pytest", "-q", "-ra", "--strict-markers",
        "-p", "scripts.pytest_no_skips_plugin"
    ) + @($Contract.testFiles)
    $code = Invoke-NativeChecked $uv $pytestArgs "LocalData pytest collection"
    if ($code -ne 0) { return $ExitTestFailure }
    Write-Host "LOCALDATA_TIER_PASS" -ForegroundColor Green
    return 0
}

try {
    $repo = Get-RepositoryRoot $RepoRoot
    $contract = Get-TierContract $repo
}
catch {
    Write-Host "Repository verification binding failure: $($_.Exception.Message)" -ForegroundColor Red
    exit $ExitBindingFailure
}

if ($Tier -eq "Hermetic") {
    exit (Invoke-HermeticTier $repo $contract)
}
if ($Tier -eq "LocalData") {
    exit (Invoke-LocalDataTier $repo $contract $LocalPackRoot)
}

$hermeticCode = Invoke-HermeticTier $repo $contract
Write-Host "DEVELOPER_HERMETIC_RESULT exit=$hermeticCode"
$localCode = Invoke-LocalDataTier $repo $contract $LocalPackRoot
Write-Host "DEVELOPER_LOCALDATA_RESULT exit=$localCode"
if ($hermeticCode -ne 0) { exit $hermeticCode }
exit $localCode
