[CmdletBinding()]
param(
    [string]$RedraftRoot,
    [string]$ProfileId,
    [switch]$AllProfiles,
    [string]$BackupRoot
)

# ---------------------------------------------------------------------------
# Root discovery -- must resolve the SAME canonical runtime root the real
# Tauri Redraft app uses, not the git-tracked repo-relative seed data.
#
# Real app resolution (desktop/crates/nwr-desktop-runtime/src/lib.rs:196-241):
#   state_dir = app.path().app_local_data_dir() / "state"
#   env NWR_REDRAFT_HOME = state_dir / "redraft"
# Python side (src/services/redraft_engine_v1_service.py:243) trusts
# NWR_REDRAFT_HOME when set, else falls back to <repo>/local_exports/redraft_v1
# -- a stale, pre-draft seed copy, NOT live app state. That fallback silently
# missing the real KHA board on 2026-09-02 is the incident this fixes.
#
# Priority, mirroring the app exactly, most-trustworthy first:
#   1. -RedraftRoot explicit param
#   2. $env:NWR_REDRAFT_HOME (what the Python backend itself would use)
#   3. Computed OS app-local-data dir for the Tauri app identifier
#      (com.ninerswarroom.redraft, from desktop/apps/redraft/src-tauri/tauri.conf.json)
#      -> Windows: %LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft
#   4. Repo-relative local_exports\redraft_v1 -- LAST RESORT ONLY, loudly
#      flagged, because this is exactly the wrong root for anything written
#      by the real launcher-started desktop app.
# ---------------------------------------------------------------------------

$TauriAppIdentifier = "com.ninerswarroom.redraft"
$desktopRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $desktopRoot

$rootSource = $null

if ($RedraftRoot) {
    $rootSource = "explicit_param"
} elseif ($env:NWR_REDRAFT_HOME -and $env:NWR_REDRAFT_HOME.Trim()) {
    $RedraftRoot = $env:NWR_REDRAFT_HOME.Trim()
    $rootSource = "env_NWR_REDRAFT_HOME"
} else {
    $appDataCandidate = $null
    if ($env:LOCALAPPDATA) {
        $appDataCandidate = Join-Path $env:LOCALAPPDATA (Join-Path $TauriAppIdentifier "state\redraft")
    }
    if ($appDataCandidate -and (Test-Path -LiteralPath $appDataCandidate -PathType Container)) {
        $RedraftRoot = $appDataCandidate
        $rootSource = "app_local_data_dir"
    } else {
        $RedraftRoot = Join-Path $repoRoot "local_exports\redraft_v1"
        $rootSource = "repo_fallback"
        Write-Warning "NWR_REDRAFT_HOME is not set and no app-local-data directory was found for '$TauriAppIdentifier'."
        Write-Warning "Falling back to the repo-relative seed path: $RedraftRoot"
        Write-Warning "This is almost certainly NOT the real live app's state root. Pass -RedraftRoot explicitly, or run this from an environment where the Redraft desktop app has launched at least once."
    }
}

if (-not (Test-Path -LiteralPath $RedraftRoot -PathType Container)) {
    throw "Resolved RedraftRoot does not exist: $RedraftRoot (source: $rootSource). Nothing to checkpoint."
}
$RedraftRoot = (Resolve-Path -LiteralPath $RedraftRoot).Path

if (-not $BackupRoot) {
    $BackupRoot = Join-Path $repoRoot "local_exports\redraft_v1_checkpoints"
}
$BackupRoot = [System.IO.Path]::GetFullPath($BackupRoot)

# ---------------------------------------------------------------------------
# Profile selection. Default is EVERY profile found under the resolved root
# (not KHA-only) -- this is a safety net, not a UI concept, so it should not
# depend on guessing which profile the owner currently has "active".
# ---------------------------------------------------------------------------

$profilesDir = Join-Path $RedraftRoot "profiles"
$resolvedProfileIds = @()
if ($ProfileId) {
    $resolvedProfileIds = @($ProfileId)
} elseif (Test-Path -LiteralPath $profilesDir -PathType Container) {
    $resolvedProfileIds = Get-ChildItem -LiteralPath $profilesDir -Filter "*.json" -File |
        Where-Object { $_.Name -notmatch '\.backup\.json$' } |
        ForEach-Object { [System.IO.Path]::GetFileNameWithoutExtension($_.Name) }
} else {
    Write-Warning "No profiles directory found at $profilesDir -- nothing to enumerate. Pass -ProfileId explicitly if you know it."
}

if ($resolvedProfileIds.Count -eq 0) {
    throw "No profile IDs resolved (root: $RedraftRoot). Nothing to checkpoint."
}

# ---------------------------------------------------------------------------
# Small, dumb, synchronous backup -- no watcher, no locking, no background
# writer. Just copies the files needed to recover each profile's
# configuration and draft state to a fresh timestamped folder, then verifies
# every copy by hash. Safe to run any number of times; never deletes,
# overwrites, or otherwise mutates anything under $RedraftRoot.
# ---------------------------------------------------------------------------

function Get-CheckpointRelativeFiles([string]$pid_) {
    @(
        "profiles\$pid_.json"
        "draft_boards\$pid_.json"
        "draft_boards\$pid_.backup.json"
        "manual_assets\$pid_.json"
        "adp_snapshots\$pid_.json"
        "adp_provider_cache\owner_platform_snapshot\snapshot.json"
        "adp_provider_cache\owner_platform_snapshot\leagues\$pid_.json"
        "adp_provider_cache\owner_platform_snapshot\selections\$pid_.json"
        "adp_provider_cache\ffc\$pid_.json"
        "adp_provider_cache\owner_paste\$pid_.json"
        "sleeper_imports\$pid_.json"
        "projections\2026\current.csv"
        "projections\2026\current.manifest.json"
        "projections\2026\current.approval.json"
        "projections\2026\DRAFT_DAY_AUTHORIZATION.json"
    )
}

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dest = Join-Path $BackupRoot $stamp
New-Item -ItemType Directory -Path $dest -Force | Out-Null

$sha256 = [System.Security.Cryptography.SHA256]::Create()
function Get-FileHashHex([string]$path) {
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $hashBytes = $sha256.ComputeHash($bytes)
    -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
}

$profileResults = @()
foreach ($pid_ in $resolvedProfileIds) {
    $copied = @()
    $skipped = @()
    $verifyFailed = @()
    foreach ($relative in (Get-CheckpointRelativeFiles $pid_)) {
        $source = Join-Path $RedraftRoot $relative
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            $targetPath = Join-Path $dest $relative
            New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
            Copy-Item -LiteralPath $source -Destination $targetPath -Force

            $sourceHash = Get-FileHashHex $source
            $destHash = Get-FileHashHex $targetPath
            if ($sourceHash -eq $destHash) {
                $copied += [ordered]@{ path = $relative; sha256 = $destHash; verified = $true }
            } else {
                $verifyFailed += [ordered]@{ path = $relative; source_sha256 = $sourceHash; dest_sha256 = $destHash }
                Write-Warning "Hash mismatch after copy for $relative -- source and destination differ. Copy left in place for inspection, NOT treated as a verified checkpoint."
            }
        } else {
            $skipped += $relative
        }
    }
    $profileResults += [ordered]@{
        profile_id     = $pid_
        copied         = $copied
        not_found      = $skipped
        verify_failed  = $verifyFailed
    }
}
$sha256.Dispose()

$manifest = [ordered]@{
    checkpoint_utc  = (Get-Date).ToUniversalTime().ToString("o")
    redraft_root    = $RedraftRoot
    root_source     = $rootSource
    profile_ids     = $resolvedProfileIds
    profiles        = $profileResults
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $dest "CHECKPOINT_MANIFEST.json") -Encoding utf8

$totalCopied = ($profileResults | ForEach-Object { $_.copied.Count } | Measure-Object -Sum).Sum
$totalFailed = ($profileResults | ForEach-Object { $_.verify_failed.Count } | Measure-Object -Sum).Sum

Write-Host "KHA/NWR draft checkpoint saved: $dest"
Write-Host "Root: $RedraftRoot (source: $rootSource)"
Write-Host "Profiles: $($resolvedProfileIds.Count)   Files copied+verified: $totalCopied   Hash-verify failures: $totalFailed"
if ($totalFailed -gt 0) {
    Write-Warning "One or more files failed hash verification after copy -- see CHECKPOINT_MANIFEST.json."
}
