[CmdletBinding()]
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputRoot,
    [switch]$Clean,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Write-Utf8NoBomLf {
    param([string]$Path, [string]$Text)
    $normalized = ($Text -replace "`r`n", "`n") -replace "`r", "`n"
    [IO.File]::WriteAllText($Path, $normalized, [Text.UTF8Encoding]::new($false))
}

function Get-ContainedRelativePath {
    param([string]$Root, [string]$Candidate)
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $candidateFull = [IO.Path]::GetFullPath($Candidate)
    $prefix = $rootFull + [IO.Path]::DirectorySeparatorChar
    if ($candidateFull.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase)) { return "." }
    if (-not $candidateFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is not contained by its approved root: $candidateFull"
    }
    return $candidateFull.Substring($prefix.Length)
}

function Assert-NoExistingReparsePoint {
    param([string]$Root, [string]$Candidate)
    $rootItem = Get-Item -LiteralPath $Root -Force
    if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Owned output root may not begin at a reparse point: $Root"
    }
    $relative = Get-ContainedRelativePath -Root $Root -Candidate $Candidate
    $current = $Root
    foreach ($segment in @($relative -split "[\\/]" | Where-Object { $_ -and $_ -ne "." })) {
        $current = Join-Path $current $segment
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Owned output path crosses a reparse point: $current"
            }
        }
    }
}

function Remove-EmptyDirectory {
    param([string]$Path)
    if ((Test-Path -LiteralPath $Path -PathType Container) -and
        @(Get-ChildItem -LiteralPath $Path -Force).Count -eq 0) {
        Remove-Item -LiteralPath $Path -Force
    }
}

$repo = [IO.Path]::GetFullPath($RepoRoot).TrimEnd(
    [IO.Path]::DirectorySeparatorChar,
    [IO.Path]::AltDirectorySeparatorChar
)
if (-not (Test-Path -LiteralPath $repo -PathType Container)) {
    throw "Repository root does not exist: $repo"
}
$gitTop = @(& git -c core.fsmonitor=false -C $repo rev-parse --show-toplevel 2>&1)
if ($LASTEXITCODE -ne 0 -or $gitTop.Count -ne 1) {
    throw "Repository root is not a Git worktree: $repo"
}
$actualTop = [IO.Path]::GetFullPath(([string]$gitTop[0]).Trim()).TrimEnd(
    [IO.Path]::DirectorySeparatorChar,
    [IO.Path]::AltDirectorySeparatorChar
)
if (-not $actualTop.Equals($repo, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Repository root binding mismatch."
}

$allowedRoot = [IO.Path]::GetFullPath((Join-Path $repo "local_exports")).TrimEnd(
    [IO.Path]::DirectorySeparatorChar,
    [IO.Path]::AltDirectorySeparatorChar
)
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $allowedRoot "hermetic_test_pack_v1"
}
$output = [IO.Path]::GetFullPath($OutputRoot).TrimEnd(
    [IO.Path]::DirectorySeparatorChar,
    [IO.Path]::AltDirectorySeparatorChar
)
$allowedPrefix = $allowedRoot + [IO.Path]::DirectorySeparatorChar
$ownedName = [IO.Path]::GetFileName($output)
if (-not $output.StartsWith($allowedPrefix, [StringComparison]::OrdinalIgnoreCase) -or
    -not $ownedName.StartsWith("hermetic_test_pack_v1", [StringComparison]::Ordinal)) {
    throw "Output path escapes the owned ignored Hermetic root: $output"
}

$relativeOutput = (Get-ContainedRelativePath -Root $repo -Candidate $output) -replace "\\", "/"
& git -c core.fsmonitor=false -C $repo check-ignore --quiet -- $relativeOutput
if ($LASTEXITCODE -ne 0) {
    throw "Hermetic output is not ignored by Git: $relativeOutput"
}

if (-not (Test-Path -LiteralPath $allowedRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $allowedRoot | Out-Null
}
Assert-NoExistingReparsePoint -Root $allowedRoot -Candidate $output

$fixtureRoot = Join-Path $repo "tests\fixtures\hermetic\local_export_pack_v1"
$sourceManifestPath = Join-Path $fixtureRoot "fixture-manifest.json"
$sourceManifest = Get-Content -LiteralPath $sourceManifestPath -Raw | ConvertFrom-Json
if ($sourceManifest.schemaVersion -ne 1 -or
    $sourceManifest.packId -ne "nwr-hermetic-local-export-behavior-fixtures" -or
    $sourceManifest.version -ne "1.0.0" -or
    $sourceManifest.fixtureClass -ne "FICTIONAL_TEST_FIXTURE_NOT_REAL" -or
    $sourceManifest.rights -ne "FICTIONAL_RIGHTS_CLEAR_TEST_DATA_ONLY" -or
    [bool]$sourceManifest.networkRequired) {
    throw "Tracked fixture manifest contract is invalid."
}

$manifestRelative = (Get-ContainedRelativePath -Root $repo -Candidate $sourceManifestPath) -replace "\\", "/"
& git -c core.fsmonitor=false -C $repo ls-files --error-unmatch -- $manifestRelative *> $null
if ($LASTEXITCODE -ne 0) { throw "Fixture manifest is not tracked: $manifestRelative" }

foreach ($entry in @($sourceManifest.files)) {
    $relative = ([string]$entry.path) -replace "\\", "/"
    if ($relative -match "(^|/)\.\.(/|$)" -or [IO.Path]::IsPathRooted($relative)) {
        throw "Fixture manifest path escapes its tracked root: $relative"
    }
    $sourcePath = [IO.Path]::GetFullPath((Join-Path $fixtureRoot $relative))
    $fixturePrefix = [IO.Path]::GetFullPath($fixtureRoot).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (-not $sourcePath.StartsWith($fixturePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Fixture manifest path escapes its tracked root: $relative"
    }
    $trackedRelative = (Get-ContainedRelativePath -Root $repo -Candidate $sourcePath) -replace "\\", "/"
    & git -c core.fsmonitor=false -C $repo ls-files --error-unmatch -- $trackedRelative *> $null
    if ($LASTEXITCODE -ne 0) { throw "Fixture payload is not tracked: $trackedRelative" }
    if ((Get-Sha256 $sourcePath) -ne ([string]$entry.sha256).ToLowerInvariant() -or
        (Get-Item -LiteralPath $sourcePath).Length -ne [int64]$entry.bytes) {
        throw "Tracked fixture payload hash or size mismatch: $relative"
    }
    if ([int64]$entry.bytes -gt 65536) { throw "Fixture payload exceeds the bounded size contract." }
}

$payloadOutput = Join-Path $output "payload\families.csv"
$packManifestOutput = Join-Path $output "PACK_MANIFEST.json"
$receiptOutput = Join-Path $output "SHA256SUMS"
$markerOutput = Join-Path $output ".nwr-hermetic-owned"
$knownFiles = @($payloadOutput, $packManifestOutput, $receiptOutput, $markerOutput)

if ($Clean) {
    foreach ($knownFile in $knownFiles) {
        if (Test-Path -LiteralPath $knownFile -PathType Leaf) {
            Remove-Item -LiteralPath $knownFile -Force
        }
    }
    Remove-EmptyDirectory -Path (Join-Path $output "payload")
    Remove-EmptyDirectory -Path $output
}

function Assert-GeneratedPack {
    foreach ($required in $knownFiles) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Generated Hermetic pack is incomplete: $required"
        }
    }
    $pack = Get-Content -LiteralPath $packManifestOutput -Raw | ConvertFrom-Json
    if ($pack.schemaVersion -ne 1 -or
        $pack.packId -ne "nwr-hermetic-local-export-behavior-fixtures" -or
        $pack.version -ne "1.0.0" -or
        $pack.rights -ne "FICTIONAL_RIGHTS_CLEAR_TEST_DATA_ONLY" -or
        [bool]$pack.networkRequired) {
        throw "Generated Hermetic pack manifest is invalid."
    }
    $payloadHash = Get-Sha256 $payloadOutput
    if ($payloadHash -ne ([string]$pack.files[0].sha256).ToLowerInvariant() -or
        (Get-Item -LiteralPath $payloadOutput).Length -ne [int64]$pack.files[0].bytes) {
        throw "Generated Hermetic payload corruption detected."
    }
    $expectedReceipt = @(
        "$payloadHash  payload/families.csv",
        "$(Get-Sha256 $packManifestOutput)  PACK_MANIFEST.json",
        ""
    ) -join "`n"
    $actualReceipt = [IO.File]::ReadAllText($receiptOutput, [Text.Encoding]::UTF8)
    if ($actualReceipt -ne $expectedReceipt) { throw "Generated SHA-256 receipt mismatch." }
    if ([IO.File]::ReadAllText($markerOutput, [Text.Encoding]::UTF8) -ne "NWR_HERMETIC_PACK_OWNED_V1`n") {
        throw "Generated ownership marker mismatch."
    }
}

if ($VerifyOnly) {
    Assert-GeneratedPack
    Write-Output "HERMETIC_BOOTSTRAP_VERIFIED root=$output sha256=$(Get-Sha256 $receiptOutput)"
    exit 0
}

New-Item -ItemType Directory -Path (Join-Path $output "payload") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $fixtureRoot "payload\families.csv") -Destination $payloadOutput -Force
$sourceManifestSha = Get-Sha256 $sourceManifestPath
$payloadSha = Get-Sha256 $payloadOutput
$payloadBytes = (Get-Item -LiteralPath $payloadOutput).Length
$packText = @"
{
  "schemaVersion": 1,
  "packId": "nwr-hermetic-local-export-behavior-fixtures",
  "version": "1.0.0",
  "fixtureClass": "FICTIONAL_TEST_FIXTURE_NOT_REAL",
  "rights": "FICTIONAL_RIGHTS_CLEAR_TEST_DATA_ONLY",
  "networkRequired": false,
  "sourceManifestSha256": "$sourceManifestSha",
  "files": [
    {
      "path": "payload/families.csv",
      "sha256": "$payloadSha",
      "bytes": $payloadBytes
    }
  ]
}

"@
Write-Utf8NoBomLf -Path $packManifestOutput -Text $packText
$receiptText = @(
    "$payloadSha  payload/families.csv",
    "$(Get-Sha256 $packManifestOutput)  PACK_MANIFEST.json",
    ""
) -join "`n"
Write-Utf8NoBomLf -Path $receiptOutput -Text $receiptText
Write-Utf8NoBomLf -Path $markerOutput -Text "NWR_HERMETIC_PACK_OWNED_V1`n"
Assert-GeneratedPack
Write-Output "HERMETIC_BOOTSTRAP_READY root=$output sha256=$(Get-Sha256 $receiptOutput)"
