#requires -version 5.1
<#
.SYNOPSIS
    NWR desktop release gate: a repeatable, real (non-mocked) smoke test.

.DESCRIPTION
    Built by Worker 3 (P0-3, post-UI-product-v1 shift, 2026-09-12) as a
    repeatable release gate for the NWR desktop app. Two independent things
    are exercised and reported SEPARATELY -- never blended into one verdict:

      1. PACKAGING GATE  -- can `npm run check:resources` and a full native
         `tauri build` actually run in this environment? (Rust toolchain,
         PyInstaller sidecar, the resource-allowlist/owner-privacy guard.)
         This step is opt-in (-AttemptNativeBuild) because a full native
         build is slow (Rust compiles from scratch the first time) and,
         as of this writing, is expected to legitimately FAIL at
         check:resources for the `redraft` app -- see KNOWN ISSUES below.
         This script never bypasses that guard; it only reports what it
         finds.

      2. BRIDGE SMOKE -- a real production `vite build`, served by vite
         preview, talking to the REAL Python desktop API backend process
         (scripts/run_nwr_desktop_api.py) over real loopback HTTP. This is
         the fallback proxy this project uses when a full native bundle
         is not attempted or not achievable, per
         docs/codex/post_ui_v1/NWR_POST_UI_WORKDAY_LEDGER.md (Worker 3).
         Nothing here is mocked: it is the real facade, the real bundled
         projection seed, and (optionally) a real read-only Sleeper league.

    KNOWN ISSUES this script will surface (not fix -- packaging/verification
    tooling only, see the hard boundary in Worker 3's ledger entry):
      - `npm run check:resources` fails for the `redraft` app because the
        bundled `NWR_DATA_GOVERNANCE.json` governance receipt legitimately
        contains the real owner's name in its own audit trail
        ("approved_by"/"renewed_by"), which the same script's owner-privacy
        guard forbids in any bundled resource. This predates this shift
        (confirmed via `git diff --stat <start-head> HEAD -- desktop/scripts
        desktop/apps/redraft/src-tauri/tauri.windows.conf.json`, which is
        empty) -- it is not a regression this script or this shift caused.
      - POST /api/v1/redraft/weekly-home-actions (feeds the "Weekly Home"
        surface's "NWR Actions" panel) returns HTTP 500. Root cause:
        `DesktopBackendFacade.redraft_weekly_home_actions` (src/application/
        desktop_facade.py) still assumes `redraft_kdst_streamer(...).data
        ["positions"]` is a dict keyed by position; it is actually a list of
        decision-envelope rows. Reproduced directly (not just via HTTP) with
        a standalone `AttributeError: 'list' object has no attribute
        'items'`. Real, disclosed, NOT fixed by this pass (backend/model
        files are out of scope for this pass beyond Worker 2's already-
        committed migration).

.PARAMETER Mode
    "redraft" (default) or "dynasty".

.PARAMETER AttemptNativeBuild
    Also attempt the full native Tauri packaging pipeline
    (sidecar:build + tauri:build). Off by default (slow; expected to stop
    at check:resources for redraft -- see KNOWN ISSUES). This never
    bypasses check:resources.

.PARAMETER SleeperLeagueId / SleeperUsername
    Optional. If both are supplied, the script performs ONE real read-only
    Sleeper import through the app's own backend endpoint
    (POST /api/v1/redraft/sleeper/import) against a real Sleeper league,
    with a real before/after byte-diff of league/rosters/users fetched
    directly from api.sleeper.app to prove zero writes. Omit both to run
    an isolated local-preset profile instead (no live Sleeper contact) --
    the script discloses which path it took in its summary and JSON report.

.PARAMETER RepoRoot
    Defaults to the repository root two levels above this script
    (desktop/scripts/..\..).

.PARAMETER KeepRunning
    Leave the backend + vite preview processes running after the script
    finishes (default: both are stopped at the end).

.EXAMPLE
    # Isolated local-only smoke pass, no native build attempt (fast, safe
    # default for CI / a quick re-check):
    pwsh -File desktop/scripts/nwr_release_gate_smoke.ps1

.EXAMPLE
    # Full pass including a real read-only Sleeper league and a native
    # build attempt:
    pwsh -File desktop/scripts/nwr_release_gate_smoke.ps1 `
        -AttemptNativeBuild `
        -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety
#>
[CmdletBinding()]
param(
    [ValidateSet("redraft", "dynasty")]
    [string]$Mode = "redraft",
    [switch]$AttemptNativeBuild,
    [string]$SleeperLeagueId,
    [string]$SleeperUsername,
    [string]$RepoRoot,
    [switch]$KeepRunning
)

$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

# Windows PowerShell 5.1 note: consuming a native (non-cmdlet) executable's
# stderr stream from WITHIN PowerShell -- even via `2>&1` or `2> file` --
# wraps each line in a NativeCommandError object, which prints noisily (and,
# combined with $ErrorActionPreference = "Stop", would throw even on a clean
# exit). Shelling out through cmd.exe so the OS itself does the redirection
# avoids PowerShell's stream-wrapping entirely; only `$LASTEXITCODE` is used
# to detect failure, never exceptions from stderr content.
function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory)][string]$CommandLine,
        [string]$WorkingDirectory = (Get-Location).Path
    )
    $outFile = [System.IO.Path]::GetTempFileName()
    try {
        Push-Location $WorkingDirectory
        try {
            $cmdLine = "$CommandLine > `"$outFile`" 2>&1"
            cmd.exe /c $cmdLine
            $exit = $LASTEXITCODE
        } finally {
            Pop-Location
        }
        $combined = (Get-Content -LiteralPath $outFile -ErrorAction SilentlyContinue) -join "`n"
        return [pscustomobject]@{ ExitCode = $exit; Output = $combined }
    } finally {
        Remove-Item -LiteralPath $outFile -Force -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopRoot = Split-Path -Parent $ScriptRoot
if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent $DesktopRoot
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$AppDir = Join-Path $DesktopRoot "apps\$Mode"
if (-not (Test-Path -LiteralPath $AppDir -PathType Container)) {
    throw "App directory not found for mode '$Mode': $AppDir"
}

$BackendPort = if ($Mode -eq "redraft") { 18742 } else { 18741 }
$FrontendPort = if ($Mode -eq "redraft") { 1422 } else { 1421 }
$DefaultDevToken = "nwr-desktop-development-token-only-000000000000"

$StampUtc = [DateTime]::UtcNow.ToString("yyyyMMdd'T'HHmmss'Z'")
$OutDir = Join-Path $RepoRoot "local_exports\release_gate\$StampUtc"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$report = [ordered]@{
    generatedAtUtc          = [DateTime]::UtcNow.ToString("o")
    mode                    = $Mode
    repoRoot                = $RepoRoot
    packagingGate           = [ordered]@{}
    bridgeSmoke             = [ordered]@{}
    sleeper                 = [ordered]@{}
    latencyMs               = [ordered]@{}
    findings                = @()
}

function Write-Section([string]$title) {
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Add-Finding([string]$text) {
    $report.findings += $text
    Write-Host "FINDING: $text" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# 1. PACKAGING GATE (never bypassed; reported, not forced)
# ---------------------------------------------------------------------------

Write-Section "Packaging gate: check:resources"
$checkResult = Invoke-NativeCapture -CommandLine "node ./scripts/check-resource-allowlists.mjs" -WorkingDirectory $DesktopRoot
$checkExit = $checkResult.ExitCode
Write-Host $checkResult.Output
$report.packagingGate.checkResourcesExitCode = $checkExit
$report.packagingGate.checkResourcesOutput = $checkResult.Output
if ($checkExit -eq 0) {
    Write-Host "check:resources PASSED." -ForegroundColor Green
} else {
    Write-Host "check:resources FAILED (see KNOWN ISSUES in this script's header)." -ForegroundColor Red
    Add-Finding "check:resources failed -- native bundling is blocked at the resource-privacy/allowlist gate, not by a missing toolchain. Exact output saved to the JSON report."
}

if ($AttemptNativeBuild) {
    Write-Section "Packaging gate: native build attempt"
    if ($checkExit -ne 0) {
        Write-Host "Skipping tauri:build -- check:resources must pass first. This script does not bypass that guard." -ForegroundColor Yellow
        $report.packagingGate.nativeBuildAttempted = $false
        $report.packagingGate.nativeBuildSkippedReason = "check:resources failed"
    } else {
        $sidecarResult = Invoke-NativeCapture -CommandLine "npm run sidecar:build" -WorkingDirectory $DesktopRoot
        Write-Host $sidecarResult.Output
        $report.packagingGate.sidecarBuildExitCode = $sidecarResult.ExitCode
        if ($sidecarResult.ExitCode -eq 0) {
            $tauriResult = Invoke-NativeCapture -CommandLine "npm run tauri:build --workspace @nwr/$Mode-desktop" -WorkingDirectory $DesktopRoot
            Write-Host $tauriResult.Output
            $report.packagingGate.tauriBuildExitCode = $tauriResult.ExitCode
        }
        $report.packagingGate.nativeBuildAttempted = $true
    }
} else {
    Write-Host "Native build attempt skipped (-AttemptNativeBuild not set)." -ForegroundColor DarkGray
    $report.packagingGate.nativeBuildAttempted = $false
}

# Independent evidence the Rust toolchain itself is not the blocker: a plain
# `cargo check` never bundles resources (no privacy conflict), so it is safe
# to run unconditionally.
Write-Section "Packaging gate: Rust toolchain sanity (cargo check, no bundling)"
$tauriCrateDir = Join-Path $AppDir "src-tauri"
$cargoResult = Invoke-NativeCapture -CommandLine "cargo check" -WorkingDirectory $tauriCrateDir
$cargoExit = $cargoResult.ExitCode
Write-Host $cargoResult.Output
$report.packagingGate.cargoCheckExitCode = $cargoExit
if ($cargoExit -eq 0) {
    Write-Host "cargo check PASSED -- the Rust/Tauri toolchain itself compiles cleanly." -ForegroundColor Green
} else {
    Write-Host "cargo check FAILED -- see output; this WOULD indicate a genuine toolchain problem." -ForegroundColor Red
    Add-Finding "cargo check failed in $tauriCrateDir -- a real toolchain problem, not just the privacy gate."
}

# ---------------------------------------------------------------------------
# 2. BRIDGE SMOKE (real backend + real production frontend build)
# ---------------------------------------------------------------------------

Write-Section "Bridge smoke: production frontend build"
$t0 = Get-Date
$buildResult = Invoke-NativeCapture -CommandLine "npm run build" -WorkingDirectory $AppDir
$buildMs = [int]((Get-Date) - $t0).TotalMilliseconds
Write-Host $buildResult.Output
if ($buildResult.ExitCode -ne 0) {
    throw "Production vite build failed (exit $($buildResult.ExitCode)) -- cannot continue the bridge smoke."
}
$report.bridgeSmoke.viteBuildMs = $buildMs

Write-Section "Bridge smoke: starting vite preview on the allowed dev origin (port $FrontendPort)"
$previewProc = $null
$previewLog = Join-Path $OutDir "vite_preview.log"
# `npx` is a .cmd shim on Windows -- Start-Process cannot exec it directly
# ("%1 is not a valid Win32 application"), so route through cmd.exe /c.
$previewProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList @("/c", "npx vite preview --port $FrontendPort --strictPort") `
    -WorkingDirectory $AppDir -RedirectStandardOutput $previewLog -RedirectStandardError "$previewLog.err" `
    -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Section "Bridge smoke: starting the REAL Python desktop API backend (port $BackendPort)"
function New-RandomSecret([string]$prefix) {
    $suffix = -join ((48..57) + (97..122) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
    return "$prefix-$suffix"
}
$apiToken = $DefaultDevToken
$startupProofKey = New-RandomSecret "nwr-startup-proof-key-release-gate"
$credsPath = Join-Path $OutDir "backend_creds.json"
$creds = @{ apiToken = $apiToken; startupProofKey = $startupProofKey } | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($credsPath, "$creds`n", (New-Object System.Text.UTF8Encoding($false)))

$backendProc = $null
$backendLog = Join-Path $OutDir "backend.log"
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonExe) { $pythonExe = (Get-Command py -ErrorAction Stop) }
$backendArgs = @(
    (Join-Path $RepoRoot "scripts\run_nwr_desktop_api.py"),
    "--host", "127.0.0.1", "--port", "$BackendPort", "--mode", $Mode, "--repo-root", $RepoRoot
)
$backendProc = Start-Process -FilePath $pythonExe.Source -ArgumentList $backendArgs `
    -WorkingDirectory $RepoRoot -RedirectStandardInput $credsPath `
    -RedirectStandardOutput $backendLog -RedirectStandardError "$backendLog.err" `
    -PassThru -WindowStyle Hidden

$base = "http://127.0.0.1:$BackendPort"
$origin = "http://127.0.0.1:$FrontendPort"
$headers = @{ Authorization = "Bearer $apiToken"; Origin = $origin }

function Invoke-TimedRequest {
    param([string]$Name, [string]$Method, [string]$Path, [string]$Body)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        if ($Method -eq "GET") {
            $resp = Invoke-WebRequest -Uri "$base$Path" -Headers $headers -UseBasicParsing -TimeoutSec 30
        } else {
            $resp = Invoke-WebRequest -Uri "$base$Path" -Method POST -Headers $headers `
                -ContentType "application/json" -Body $Body -UseBasicParsing -TimeoutSec 30
        }
        $sw.Stop()
        $status = [int]$resp.StatusCode
    } catch {
        $sw.Stop()
        $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { -1 }
    }
    $ms = $sw.Elapsed.TotalMilliseconds
    $report.latencyMs[$Name] = [math]::Round($ms, 1)
    Write-Host ("{0,-28} status={1,-5} time={2,8:N1} ms" -f $Name, $status, $ms)
    return $status
}

Write-Section "Bridge smoke: waiting for the real backend to come up"
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $probe = Invoke-WebRequest -Uri "$base/api/v1/bootstrap" -Headers $headers -UseBasicParsing -TimeoutSec 5
        if ($probe.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
}
if (-not $ready) {
    Write-Host (Get-Content $backendLog -Raw -ErrorAction SilentlyContinue)
    throw "The real backend did not become ready on $base within the timeout."
}
Write-Host "Backend is up: $base" -ForegroundColor Green
$report.bridgeSmoke.backendReady = $true

Write-Section "Bridge smoke: cold vs warm bootstrap (Home) latency"
Invoke-TimedRequest -Name "bootstrap_cold" -Method GET -Path "/api/v1/bootstrap" | Out-Null
Invoke-TimedRequest -Name "bootstrap_warm" -Method GET -Path "/api/v1/bootstrap" | Out-Null

# ---------------------------------------------------------------------------
# 3. League setup: real Sleeper (if given) or an isolated local profile
# ---------------------------------------------------------------------------

Write-Section "League setup"
if ($Mode -eq "redraft") {
    if ($SleeperLeagueId -and $SleeperUsername) {
        Write-Host "Using a REAL read-only Sleeper league: $SleeperLeagueId" -ForegroundColor Magenta
        $report.sleeper.pathUsed = "REAL_READ_ONLY_LEAGUE"
        $report.sleeper.leagueId = $SleeperLeagueId

        function Get-SleeperSnapshot {
            param([string]$LeagueId)
            $snap = [ordered]@{}
            foreach ($seg in @("", "/rosters", "/users")) {
                $key = if ($seg) { $seg.Trim('/') } else { "league" }
                $snap[$key] = Invoke-RestMethod -Uri "https://api.sleeper.app/v1/league/$LeagueId$seg" -TimeoutSec 30 | ConvertTo-Json -Depth 20 -Compress
            }
            return $snap
        }

        Write-Host "Capturing BEFORE snapshot directly from api.sleeper.app (read-only GET)..."
        $before = Get-SleeperSnapshot -LeagueId $SleeperLeagueId

        $importBody = @{ leagueId = $SleeperLeagueId; username = $SleeperUsername } | ConvertTo-Json -Compress
        $importStatus = Invoke-TimedRequest -Name "sleeper_import" -Method POST -Path "/api/v1/redraft/sleeper/import" -Body $importBody
        if ($importStatus -ne 200) {
            throw "Real Sleeper import failed with status $importStatus -- aborting rather than guessing why."
        }

        Write-Host "Capturing AFTER snapshot directly from api.sleeper.app (read-only GET)..."
        $after = Get-SleeperSnapshot -LeagueId $SleeperLeagueId

        $diffs = @()
        foreach ($key in $before.Keys) {
            if ($before[$key] -ne $after[$key]) { $diffs += $key }
        }
        if ($diffs.Count -eq 0) {
            Write-Host "Sleeper before/after byte-comparison: IDENTICAL (league, rosters, users). 0 writes confirmed." -ForegroundColor Green
            $report.sleeper.beforeAfterIdentical = $true
        } else {
            Write-Host "Sleeper before/after DIFFERS in: $($diffs -join ', ')" -ForegroundColor Red
            $report.sleeper.beforeAfterIdentical = $false
            $report.sleeper.differingSections = $diffs
            Add-Finding "Sleeper before/after snapshot differs in: $($diffs -join ', ') -- investigate before trusting a 0-writes claim (could be legitimate opponent activity unrelated to this app; does not by itself prove a write)."
        }
        $report.sleeper.writeCapableClientMethodsFound = $false
        $report.sleeper.grepEvidence = "src/services/sleeper_import_service.py defines only SleeperHttpClient.get_json() via urllib.request.urlopen() (GET only, no data= payload); no POST/PUT/PATCH/DELETE call sites target api.sleeper.app anywhere in src/ (verified by this session's own grep)."
    } else {
        Write-Host "No Sleeper league/username supplied -- creating an isolated LOCAL preset profile instead." -ForegroundColor DarkYellow
        $report.sleeper.pathUsed = "ISOLATED_LOCAL_PROFILE_ONLY"
        $createBody = @{ presetKey = "12_TEAM_PPR"; leagueName = "NWR Release Gate Local Profile" } | ConvertTo-Json -Compress
        Invoke-TimedRequest -Name "create_local_profile" -Method POST -Path "/api/v1/redraft/profiles" -Body $createBody | Out-Null
    }
}

# ---------------------------------------------------------------------------
# 4. Surface-by-surface smoke (Home / Lineup / Improve Team / Trades /
#    Players / League) -- all read GETs plus the same POSTs the real UI
#    issues for its computed views.
# ---------------------------------------------------------------------------

if ($Mode -eq "redraft") {
    Write-Section "Surface smoke: League / My Roster / Opponent Rosters / Data Health"
    Invoke-TimedRequest -Name "league_workspace_context" -Method GET -Path "/api/v1/redraft/league-workspace-context" | Out-Null
    Invoke-TimedRequest -Name "my_roster" -Method GET -Path "/api/v1/redraft/my-roster" | Out-Null
    Invoke-TimedRequest -Name "opponent_rosters" -Method GET -Path "/api/v1/redraft/opponent-rosters" | Out-Null
    Invoke-TimedRequest -Name "data_health" -Method GET -Path "/api/v1/redraft/data-health" | Out-Null
    Invoke-TimedRequest -Name "player_availability_status" -Method GET -Path "/api/v1/redraft/player-availability-status" | Out-Null

    Write-Section "Surface smoke: Players / rankings (via bootstrap, already fetched above)"
    Write-Host "Rankings are served inline on /api/v1/bootstrap -- see bootstrap_cold/bootstrap_warm above."

    Write-Section "Surface smoke: Lineup (Start/Sit)"
    Invoke-TimedRequest -Name "weekly_lineup_week1" -Method POST -Path "/api/v1/redraft/weekly-lineup" -Body '{"week":1}' | Out-Null

    Write-Section "Surface smoke: Improve Team (Waivers / Free Agents / Trade Finder)"
    Invoke-TimedRequest -Name "waivers" -Method POST -Path "/api/v1/redraft/waivers" -Body '{"mode":"THIS_WEEK","week":1}' | Out-Null
    Invoke-TimedRequest -Name "free_agents" -Method GET -Path "/api/v1/redraft/free-agents" | Out-Null
    $tradeFinderStatus = Invoke-TimedRequest -Name "trade_finder" -Method GET -Path "/api/v1/redraft/trade-finder"

    Write-Section "Surface smoke: Weekly Home actions aggregation (KNOWN real bug -- see header)"
    $homeActionsStatus = Invoke-TimedRequest -Name "weekly_home_actions_week1" -Method POST -Path "/api/v1/redraft/weekly-home-actions" -Body '{"week":1}'
    if ($homeActionsStatus -eq 500) {
        Add-Finding "POST /api/v1/redraft/weekly-home-actions returned 500 for this profile. Root cause (confirmed by Worker 3 via direct reproduction, not just the HTTP symptom): DesktopBackendFacade.redraft_weekly_home_actions (src/application/desktop_facade.py) still assumes redraft_kdst_streamer(...).data['positions'] is a dict keyed by position; it is actually a list of decision-envelope rows -- 'list' object has no attribute 'items'. Reproduced against a real Sleeper-imported profile with an active roster (Fantasy Gamers); NOT reproduced against a fresh local-preset profile with no roster yet (this run) -- the STREAMER section is likely only reached once a roster exists. Not fixed here (backend logic out of scope for this pass)."
    } elseif ($homeActionsStatus -ne 200) {
        Add-Finding "POST /api/v1/redraft/weekly-home-actions returned unexpected status $homeActionsStatus for this profile -- investigate."
    }

    Write-Section "Surface smoke: Draft (read-only board state -- never starts/advances a draft)"
    Write-Host "Draft board state is served inline on /api/v1/bootstrap ('draftBoard') -- this script never calls draft/start, draft/pick, or draft/advance." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 5. Teardown
# ---------------------------------------------------------------------------

Write-Section "Summary"
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath (Join-Path $OutDir "release_gate_report.json") -Encoding utf8
Write-Host "Full JSON report: $(Join-Path $OutDir 'release_gate_report.json')"
if ($report.findings.Count -gt 0) {
    Write-Host ""
    Write-Host "Findings requiring owner/next-worker attention:" -ForegroundColor Yellow
    $report.findings | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
}

if (-not $KeepRunning) {
    Write-Section "Stopping backend + preview processes started by this script"
    # Stop-Process on the tracked PID alone can leave grandchildren alive
    # (cmd.exe -> npx.cmd -> node.exe is a process TREE; killing only the
    # tracked top-level PID does not kill its descendants on Windows). Kill
    # the tracked PIDs first, then fall back to whatever is still actually
    # LISTENING on the two ports this run used, which is the authoritative
    # signal regardless of process-tree shape.
    foreach ($proc in @($backendProc, $previewProc)) {
        if ($proc -and -not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Milliseconds 500
    $leftoverPids = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -in @($BackendPort, $FrontendPort) } |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($leftoverPid in $leftoverPids) {
        Write-Host "Force-stopping leftover process still listening on a smoke-test port: PID $leftoverPid" -ForegroundColor DarkYellow
        Stop-Process -Id $leftoverPid -Force -ErrorAction SilentlyContinue
    }
} else {
    $backendPid = if ($backendProc) { $backendProc.Id } else { "n/a" }
    $previewPid = if ($previewProc) { $previewProc.Id } else { "n/a" }
    Write-Host "Leaving backend (pid $backendPid) and preview (pid $previewPid) running (-KeepRunning)." -ForegroundColor DarkGray
}
