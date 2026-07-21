param(
    [string]$KnownFolderTestRoot = '',
    [switch]$AllowUncommittedTest,
    [switch]$ConfirmInstall
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stableCheckout = 'C:\NWR\Niners-War-Room-V1'
$hqRef = 'refs/remotes/origin/work/hq-parallel-control'
$testMode = -not [string]::IsNullOrWhiteSpace($KnownFolderTestRoot)

function Get-FullPath([string]$Path) {
    return [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Assert-NoReparsePath([string]$Path, [string]$Boundary) {
    $full = Get-FullPath $Path
    $base = Get-FullPath $Boundary
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
    if (-not $AllowUncommittedTest -or -not $ConfirmInstall) {
        throw 'Disposable Known Folder testing requires -AllowUncommittedTest and -ConfirmInstall.'
    }
    $testRoot = Get-FullPath $KnownFolderTestRoot
    $allowedTestBase = Get-FullPath (Join-Path (Split-Path $repoRoot -Parent) '.codex-known-folder-tests')
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
    $localAppData = Join-Path $testRoot 'LocalAppData'
    $runtimeCheckout = $repoRoot
    New-Item -ItemType Directory -Force -Path $desktop,$programs,$localAppData | Out-Null
} else {
    if ($AllowUncommittedTest -or $ConfirmInstall) {
        throw 'Test-only installer switches cannot be used for a real installation.'
    }
    if ((Get-FullPath $repoRoot) -ine (Get-FullPath $stableCheckout)) {
        throw "Install from the stable canonical checkout only: $stableCheckout"
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
        throw 'Interactive Explorer identity is unresolved or differs from the installer identity.'
    }

    $desktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
    $programs = [Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)
    $localAppData = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
    $runtimeCheckout = $stableCheckout
    foreach ($knownFolder in @($desktop,$programs,$localAppData)) {
        if (-not $knownFolder -or -not (Test-Path -LiteralPath $knownFolder -PathType Container)) {
            throw 'A required per-user Windows Known Folder could not be resolved.'
        }
    }
}

$headCommit = (& git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $headCommit) { throw 'The runtime checkout commit is unavailable.' }
if ($testMode) {
    & git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot merge-base --is-ancestor dc399a8c2ed5d77d9802d98c215a12cbe594d7d7 HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Disposable installer test is not based on accepted NWR V1.' }
} else {
    $expectedCommit = (& git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot rev-parse $hqRef).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $expectedCommit) {
        throw 'The canonical HQ remote-tracking commit is unavailable.'
    }
    if ($headCommit -ne $expectedCommit) {
        throw 'The runtime checkout is not at the exact canonical HQ commit.'
    }
}
$dirty = & git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot status --porcelain
if ($dirty -and -not $testMode) {
    throw 'Shortcut installation requires a clean canonical runtime checkout.'
}

$pythonCandidates = @(
    (Join-Path $runtimeCheckout '.venv\Scripts\python.exe'),
    'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe'
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) { throw 'No supported NWR Python runtime was found.' }
$legacyPythonwCandidates = @(
    (Join-Path $runtimeCheckout '.venv\Scripts\pythonw.exe'),
    'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\pythonw.exe'
)

if ($testMode) {
    $env:NWR_DATA_HOME = Join-Path $localAppData 'NinersWarRoom'
    $env:NWR_LAUNCHER_TEST_MODE = '1'
    $env:NWR_LEGACY_REFRESH_ROOT = Join-Path $localAppData 'legacy-refresh'
}
$desktopCommand = Join-Path $PSScriptRoot 'nwr_desktop.py'
$preflight = @(& $python $desktopCommand installation-preflight 2>&1)
if ($LASTEXITCODE -ne 0) {
    throw "Niners War Room persistence preflight blocked installation: $($preflight -join ' ')"
}

$powershell = Join-Path $PSHOME 'powershell.exe'
if (-not (Test-Path -LiteralPath $powershell)) { throw 'Windows PowerShell is unavailable.' }
$startMenuRoot = Join-Path $programs 'Niners War Room'

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host 'Niners War Room installer resolved:'
Write-Host "  Windows user: $identity"
Write-Host "  LocalAppData: $localAppData"
Write-Host "  Desktop: $desktop"
Write-Host "  Start Menu: $startMenuRoot"
Write-Host "  Stable checkout: $runtimeCheckout"
Write-Host "  Canonical commit: $headCommit"
Write-Host "  Python runtime: $python"
if (-not $testMode) {
    $answer = Read-Host 'Type INSTALL NINERS WAR ROOM to create these shortcuts'
    if ($answer -cne 'INSTALL NINERS WAR ROOM') {
        throw 'Shortcut installation was not confirmed.'
    }
}
New-Item -ItemType Directory -Force -Path $startMenuRoot | Out-Null

$commandsScript = Join-Path $PSScriptRoot 'NWR Desktop Commands.ps1'
$installerScript = Join-Path $PSScriptRoot 'Install Niners War Room Shortcut.ps1'
$uninstallerScript = Join-Path $PSScriptRoot 'Uninstall Niners War Room Shortcut.ps1'
$appIconPath = Join-Path $runtimeCheckout 'assets\branding\nwr_desktop_icon.ico'
if (-not (Test-Path -LiteralPath $appIconPath -PathType Leaf)) {
    throw "The repository-owned NWR desktop icon is missing: $appIconPath"
}
$appIcon = "$appIconPath,0"
$commandIcon = "$env:SystemRoot\System32\shell32.dll,13"
$shell = New-Object -ComObject WScript.Shell

function Set-OwnedShortcut {
    param(
        [string]$Path,
        [string]$Target,
        [string]$Arguments,
        [string]$Description,
        [string]$IconLocation,
        [bool]$RefreshIcon,
        [string[]]$LegacyTargets = @(),
        [string]$LegacyArguments = '',
        [string[]]$LegacyIcons = @()
    )
    if (Test-Path -LiteralPath $Path) {
        $existing = $shell.CreateShortcut($Path)
        $currentOwned = (
            $existing.TargetPath -eq $Target -and
            $existing.Arguments -eq $Arguments -and
            $existing.WorkingDirectory -eq $runtimeCheckout -and
            $existing.Description -eq $Description
        )
        if ($currentOwned) {
            if ($RefreshIcon -and $existing.IconLocation -ne $IconLocation) {
                $existing.IconLocation = $IconLocation
                $existing.Save()
                $check = $shell.CreateShortcut($Path)
                if ($check.TargetPath -ne $Target -or $check.Arguments -ne $Arguments -or
                    $check.WorkingDirectory -ne $runtimeCheckout -or
                    $check.Description -ne $Description -or
                    $check.IconLocation -ne $IconLocation) {
                    throw "Shortcut icon refresh validation failed: $Path"
                }
            }
            return $Path
        }
        $legacyOwned = $LegacyTargets.Count -gt 0 -and
            $existing.TargetPath -in $LegacyTargets -and
            $existing.Arguments -eq $LegacyArguments -and
            $existing.WorkingDirectory -eq $runtimeCheckout -and
            $existing.Description -eq $Description -and
            $existing.IconLocation -in $LegacyIcons
        if (-not $legacyOwned) {
            throw "A same-named shortcut exists but is not owned by this installer: $Path"
        }
        $existing.TargetPath = $Target
        $existing.Arguments = $Arguments
        if ($RefreshIcon) { $existing.IconLocation = $IconLocation }
        $existing.Save()
        $check = $shell.CreateShortcut($Path)
        if ($check.TargetPath -ne $Target -or $check.Arguments -ne $Arguments -or
            $check.WorkingDirectory -ne $runtimeCheckout -or
            $check.Description -ne $Description -or
            ($RefreshIcon -and $check.IconLocation -ne $IconLocation)) {
            throw "Shortcut migration validation failed: $Path"
        }
        return $Path
    }
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $Target
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = $runtimeCheckout
    $shortcut.Description = $Description
    $shortcut.IconLocation = $IconLocation
    $shortcut.Save()
    $check = $shell.CreateShortcut($Path)
    if ($check.TargetPath -ne $Target -or $check.Arguments -ne $Arguments -or
        $check.WorkingDirectory -ne $runtimeCheckout -or
        $check.Description -ne $Description -or $check.IconLocation -ne $IconLocation) {
        throw "Shortcut target validation failed: $Path"
    }
    return $Path
}

$startArguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command start'
$legacyStartArguments = '"' + $desktopCommand + '" start'
$specs = @(
    @{ Path=(Join-Path $desktop 'Niners War Room.lnk'); Target=$powershell; Arguments=$startArguments; Description='Niners War Room V1'; IconLocation=$appIcon; RefreshIcon=$true; LegacyTargets=$legacyPythonwCandidates; LegacyArguments=$legacyStartArguments; LegacyIcons=@($commandIcon,$appIcon) },
    @{ Path=(Join-Path $startMenuRoot 'Niners War Room.lnk'); Target=$powershell; Arguments=$startArguments; Description='Niners War Room V1'; IconLocation=$appIcon; RefreshIcon=$true; LegacyTargets=$legacyPythonwCandidates; LegacyArguments=$legacyStartArguments; LegacyIcons=@($commandIcon,$appIcon) },
    @{ Path=(Join-Path $startMenuRoot 'Stop Niners War Room.lnk'); Target=$powershell; Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command stop'); Description='Stop Niners War Room V1'; IconLocation=$commandIcon; RefreshIcon=$false },
    @{ Path=(Join-Path $startMenuRoot 'Niners War Room Status.lnk'); Target=$powershell; Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command status'); Description='Niners War Room V1 status'; IconLocation=$commandIcon; RefreshIcon=$false },
    @{ Path=(Join-Path $startMenuRoot 'Back Up Niners War Room.lnk'); Target=$powershell; Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command backup'); Description='Back up Niners War Room V1'; IconLocation=$commandIcon; RefreshIcon=$false },
    @{ Path=(Join-Path $startMenuRoot 'Restore Niners War Room - Dry Run.lnk'); Target=$powershell; Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command restore-dry-run'); Description='Preview Niners War Room V1 restore'; IconLocation=$commandIcon; RefreshIcon=$false },
    @{ Path=(Join-Path $startMenuRoot 'Recover Niners War Room Data Health Receipt.lnk'); Target=$powershell; Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $commandsScript + '" -Command recover-data-health'); Description='Recover the Niners War Room V1 Data Health receipt'; IconLocation=$commandIcon; RefreshIcon=$false },
    @{ Path=(Join-Path $startMenuRoot 'Install Niners War Room.lnk'); Target=$powershell; Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $installerScript + '"'); Description='Install or repair Niners War Room V1 shortcuts'; IconLocation=$commandIcon; RefreshIcon=$false },
    @{ Path=(Join-Path $startMenuRoot 'Uninstall Niners War Room.lnk'); Target=$powershell; Arguments=('-NoProfile -ExecutionPolicy Bypass -File "' + $uninstallerScript + '"'); Description='Remove Niners War Room V1 shortcuts and preserve data'; IconLocation=$commandIcon; RefreshIcon=$false }
)

$newPaths = @()
$modifiedOwned = @()
foreach ($spec in $specs) {
    if (Test-Path -LiteralPath $spec.Path) {
        $existing = $shell.CreateShortcut($spec.Path)
        $currentOwned = (
            $existing.TargetPath -eq $spec.Target -and
            $existing.Arguments -eq $spec.Arguments -and
            $existing.WorkingDirectory -eq $runtimeCheckout -and
            $existing.Description -eq $spec.Description
        )
        $legacyMatch = @($spec.LegacyTargets).Count -gt 0 -and
            $existing.TargetPath -in @($spec.LegacyTargets) -and
            $existing.Arguments -eq $spec.LegacyArguments -and
            $existing.WorkingDirectory -eq $runtimeCheckout -and
            $existing.Description -eq $spec.Description -and
            $existing.IconLocation -in @($spec.LegacyIcons)
        if (-not $currentOwned -and -not $legacyMatch) {
            throw "A same-named shortcut exists but is not owned by this installer: $($spec.Path)"
        }
        if ($legacyMatch -or ($currentOwned -and $spec.RefreshIcon -and
            $existing.IconLocation -ne $spec.IconLocation)) {
            $modifiedOwned += @{
                Path=$spec.Path
                Target=$existing.TargetPath
                Arguments=$existing.Arguments
                WorkingDirectory=$existing.WorkingDirectory
                Description=$existing.Description
                IconLocation=$existing.IconLocation
            }
        }
    } else {
        $newPaths += $spec.Path
    }
}

try {
    $installed = @($specs | ForEach-Object {
        Set-OwnedShortcut -Path $_.Path -Target $_.Target -Arguments $_.Arguments -Description $_.Description -IconLocation $_.IconLocation -RefreshIcon $_.RefreshIcon -LegacyTargets @($_.LegacyTargets) -LegacyArguments $_.LegacyArguments -LegacyIcons @($_.LegacyIcons)
    })
} catch {
    foreach ($path in $newPaths) {
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
    foreach ($owned in $modifiedOwned) {
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

[ordered]@{
    status = 'INSTALLED_AND_VALIDATED'
    windows_user = $identity
    local_app_data = $localAppData
    desktop = $desktop
    start_menu = $startMenuRoot
    runtime_checkout = $runtimeCheckout
    canonical_commit = $headCommit
    python = $python
    migrated_shortcuts = @($modifiedOwned | ForEach-Object { $_.Path })
    icon = $appIcon
    shortcuts = $installed
} | ConvertTo-Json -Depth 4
