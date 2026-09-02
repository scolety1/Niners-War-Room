[CmdletBinding()]
param(
    [string]$RedraftRoot,
    [string]$ProfileId = "fb1c49402c7644a99120197d41344bbb",  # REAL: 2026 KHA High Stakes League
    [string]$BackupRoot
)

$desktopRoot = Split-Path -Parent $PSScriptRoot
if (-not $RedraftRoot) { $RedraftRoot = Join-Path $desktopRoot "..\local_exports\redraft_v1" }
if (-not $BackupRoot) { $BackupRoot = Join-Path $desktopRoot "..\local_exports\redraft_v1_checkpoints" }
$RedraftRoot = (Resolve-Path $RedraftRoot).Path
$BackupRoot = [System.IO.Path]::GetFullPath((Join-Path $desktopRoot "..\local_exports\redraft_v1_checkpoints"))

# Small, dumb, synchronous backup -- no watcher, no locking, no background
# writer. Just copies the files needed to recover the REAL profile's
# configuration and draft state to a fresh timestamped folder. Safe to run
# any number of times; never deletes or overwrites anything.

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dest = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Path $dest -Force | Out-Null

$relativeFiles = @(
    "profiles\$ProfileId.json"
    "draft_boards\$ProfileId.json"
    "manual_assets\$ProfileId.json"
    "adp_snapshots\$ProfileId.json"
    "adp_provider_cache\owner_platform_snapshot\snapshot.json"
    "adp_provider_cache\owner_platform_snapshot\leagues\$ProfileId.json"
    "adp_provider_cache\owner_platform_snapshot\selections\$ProfileId.json"
    "adp_provider_cache\ffc\$ProfileId.json"
    "projections\2026\current.csv"
    "projections\2026\current.manifest.json"
    "projections\2026\current.approval.json"
    "projections\2026\DRAFT_DAY_AUTHORIZATION.json"
)

$copied = @()
$skipped = @()
foreach ($relative in $relativeFiles) {
    $source = Join-Path $RedraftRoot $relative
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        $targetPath = Join-Path $dest $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $targetPath -Force
        $copied += $relative
    } else {
        $skipped += $relative
    }
}

$manifest = [ordered]@{
    checkpoint_utc = (Get-Date).ToUniversalTime().ToString("o")
    profile_id     = $ProfileId
    redraft_root   = $RedraftRoot
    copied         = $copied
    not_found      = $skipped
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dest "CHECKPOINT_MANIFEST.json") -Encoding utf8

Write-Host "KHA draft checkpoint saved: $dest"
Write-Host "Files copied: $($copied.Count)  Not found (ok if not yet created): $($skipped.Count)"
