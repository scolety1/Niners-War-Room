param(
    [string]$KnownFolderTestRoot = '',
    [switch]$AllowUncommittedTest
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stableCheckout = 'C:\NWR\Niners-War-Room-V1'
$hqRef = 'refs/remotes/origin/work/hq-parallel-control'
$testMode = -not [string]::IsNullOrWhiteSpace($KnownFolderTestRoot)

function Assert-NoReparsePath([string]$Path, [string]$Boundary) {
    $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $base = [System.IO.Path]::GetFullPath($Boundary).TrimEnd('\')
    $relative = $full.Substring($base.Length).TrimStart('\')
    $current = $base
    foreach ($part in @('') + @($relative.Split('\',[System.StringSplitOptions]::RemoveEmptyEntries))) {
        if ($part) { $current = Join-Path $current $part }
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -Force -LiteralPath $current
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Disposable Known Folder path contains a reparse point: $current"
            }
        }
    }
}

if ($testMode) {
    if (-not $AllowUncommittedTest) { throw 'Disposable uninstall testing requires -AllowUncommittedTest.' }
    $testRoot = [System.IO.Path]::GetFullPath($KnownFolderTestRoot).TrimEnd('\')
    $allowedTestBase = [System.IO.Path]::GetFullPath(
        (Join-Path (Split-Path $repoRoot -Parent) '.codex-known-folder-tests')
    ).TrimEnd('\')
    if (-not $testRoot.StartsWith($allowedTestBase + '\',[System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Disposable Known Folder root must be a child of $allowedTestBase"
    }
    Assert-NoReparsePath -Path $testRoot -Boundary $allowedTestBase
    $marker = Join-Path $testRoot '.nwr-disposable-known-folders'
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf) -or
        (Get-Content -Raw -LiteralPath $marker).Trim() -cne 'NWR_DISPOSABLE_KNOWN_FOLDER_TEST_V1') {
        throw 'Disposable Known Folder marker is missing or invalid.'
    }
    $desktop = Join-Path $testRoot 'Desktop'
    $programs = Join-Path $testRoot 'Programs'
    $runtimeCheckout = $repoRoot
} else {
    if ($AllowUncommittedTest) { throw 'Test-only switches cannot be used for a real uninstall.' }
    if ([System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\') -ine $stableCheckout.TrimEnd('\')) {
        throw "Uninstall from the stable canonical checkout only: $stableCheckout"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git') -PathType Container)) {
        throw 'The stable runtime must be a standalone clone with its own .git directory.'
    }
    $current = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $sessionId = (Get-Process -Id $PID).SessionId
    $explorers = @(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Where-Object {
        $_.SessionId -eq $sessionId
    })
    $owners = @($explorers | ForEach-Object {
        $owner = Invoke-CimMethod -InputObject $_ -MethodName GetOwner
        if ($owner.ReturnValue -eq 0) { "$($owner.Domain)\$($owner.User)" }
    } | Select-Object -Unique)
    if ($owners.Count -ne 1 -or $owners[0] -ne $current) {
        throw 'Interactive Explorer identity is unresolved or differs from the uninstaller identity.'
    }
    $desktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
    $programs = [Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)
    $runtimeCheckout = $stableCheckout
    foreach ($knownFolder in @($desktop,$programs)) {
        if (-not $knownFolder -or -not (Test-Path -LiteralPath $knownFolder -PathType Container)) {
            throw 'A required per-user Windows Known Folder could not be resolved.'
        }
    }
}

$headCommit = (& git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $headCommit) { throw 'The runtime checkout commit is unavailable.' }
if ($testMode) {
    & git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot merge-base --is-ancestor dc399a8c2ed5d77d9802d98c215a12cbe594d7d7 HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Disposable uninstaller test is not based on accepted NWR V1.' }
} else {
    $expectedCommit = (& git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot rev-parse $hqRef).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $expectedCommit) {
        throw 'The canonical HQ remote-tracking commit is unavailable.'
    }
    if ($headCommit -ne $expectedCommit) {
        throw 'The runtime checkout is not at the exact canonical HQ commit.'
    }
    $dirty = & git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot status --porcelain
    if ($dirty) { throw 'Shortcut removal requires a clean canonical runtime checkout.' }
}

$legacyPythonwCandidates = @(
    (Join-Path $runtimeCheckout '.venv\Scripts\pythonw.exe'),
    'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\pythonw.exe'
)
$powershell = Join-Path $PSHOME 'powershell.exe'
$desktopCommand = Join-Path $PSScriptRoot 'nwr_desktop.py'
$commandsScript = Join-Path $PSScriptRoot 'NWR Desktop Commands.ps1'
$installerScript = Join-Path $PSScriptRoot 'Install Niners War Room Shortcut.ps1'
$uninstallerScript = Join-Path $PSScriptRoot 'Uninstall Niners War Room Shortcut.ps1'
$startMenuRoot = Join-Path $programs 'Niners War Room'
$appIcon = "$(Join-Path $runtimeCheckout 'assets\branding\nwr_desktop_icon.ico'),0"
$commandIcon = "$env:SystemRoot\System32\shell32.dll,13"
$shell = New-Object -ComObject WScript.Shell

$startArguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command start'
$legacyStartArguments = '"' + $desktopCommand + '" start'
$specs = @(
    @{ Path=(Join-Path $desktop 'Niners War Room.lnk'); Targets=@($powershell); Arguments=$startArguments; LegacyTargets=$legacyPythonwCandidates; LegacyArguments=$legacyStartArguments; LegacyIcons=@($commandIcon,$appIcon); Description='Niners War Room V1' },
    @{ Path=(Join-Path $startMenuRoot 'Niners War Room.lnk'); Targets=@($powershell); Arguments=$startArguments; LegacyTargets=$legacyPythonwCandidates; LegacyArguments=$legacyStartArguments; LegacyIcons=@($commandIcon,$appIcon); Description='Niners War Room V1' },
    @{ Path=(Join-Path $startMenuRoot 'Stop Niners War Room.lnk'); Targets=@($powershell); Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command stop'); Description='Stop Niners War Room V1' },
    @{ Path=(Join-Path $startMenuRoot 'Niners War Room Status.lnk'); Targets=@($powershell); Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command status'); Description='Niners War Room V1 status' },
    @{ Path=(Join-Path $startMenuRoot 'Back Up Niners War Room.lnk'); Targets=@($powershell); Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command backup'); Description='Back up Niners War Room V1' },
    @{ Path=(Join-Path $startMenuRoot 'Restore Niners War Room - Dry Run.lnk'); Targets=@($powershell); Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command restore-dry-run'); Description='Preview Niners War Room V1 restore' },
    @{ Path=(Join-Path $startMenuRoot 'Recover Niners War Room Data Health Receipt.lnk'); Targets=@($powershell); Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command recover-data-health'); Description='Recover the Niners War Room V1 Data Health receipt' },
    @{ Path=(Join-Path $startMenuRoot 'Install Niners War Room.lnk'); Targets=@($powershell); Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $installerScript + '"'); Description='Install or repair Niners War Room V1 shortcuts' },
    @{ Path=(Join-Path $startMenuRoot 'Uninstall Niners War Room.lnk'); Targets=@($powershell); Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $uninstallerScript + '"'); Description='Remove Niners War Room V1 shortcuts and preserve data' }
)

$ownedExisting = @()
foreach ($spec in $specs) {
    if (-not (Test-Path -LiteralPath $spec.Path)) { continue }
    $existing = $shell.CreateShortcut($spec.Path)
    $currentOwned = (
        $existing.TargetPath -in $spec.Targets -and
        $existing.Arguments -eq $spec.Arguments -and
        $existing.WorkingDirectory -eq $runtimeCheckout -and
        $existing.Description -eq $spec.Description
    )
    $legacyOwned = @($spec.LegacyTargets).Count -gt 0 -and
        $existing.TargetPath -in @($spec.LegacyTargets) -and
        $existing.Arguments -eq $spec.LegacyArguments -and
        $existing.WorkingDirectory -eq $runtimeCheckout -and
        $existing.Description -eq $spec.Description -and
        $existing.IconLocation -in @($spec.LegacyIcons)
    if (-not $currentOwned -and -not $legacyOwned) {
        throw "Refusing to remove a same-named shortcut not owned by this installer: $($spec.Path)"
    }
    $ownedExisting += @{
        Path=$spec.Path
        Target=$existing.TargetPath
        Arguments=$existing.Arguments
        WorkingDirectory=$existing.WorkingDirectory
        Description=$existing.Description
        IconLocation=$existing.IconLocation
    }
}

$removed = @()
try {
    foreach ($owned in $ownedExisting) {
        Remove-Item -LiteralPath $owned.Path -Force
        $removed += $owned.Path
    }
} catch {
    foreach ($owned in $ownedExisting) {
        if ($owned.Path -notin $removed) { continue }
        $restored = $shell.CreateShortcut($owned.Path)
        $restored.TargetPath = $owned.Target
        $restored.Arguments = $owned.Arguments
        $restored.WorkingDirectory = $owned.WorkingDirectory
        $restored.Description = $owned.Description
        $restored.IconLocation = $owned.IconLocation
        $restored.Save()
    }
    throw
}
if (Test-Path -LiteralPath $startMenuRoot -PathType Container) {
    if (-not (Get-ChildItem -LiteralPath $startMenuRoot -Force)) {
        Remove-Item -LiteralPath $startMenuRoot -Force
    }
}
[ordered]@{
    status = 'SHORTCUTS_REMOVED_DATA_PRESERVED'
    removed = $removed
    persistent_data_preserved = $true
    backup_data_preserved = $true
} | ConvertTo-Json -Depth 3
