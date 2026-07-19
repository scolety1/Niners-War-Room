param(
    [string]$DesktopOverride = '',
    [switch]$AllowUncommittedTest
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$expectedCommit = 'dc399a8c2ed5d77d9802d98c215a12cbe594d7d7'
& git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot merge-base --is-ancestor $expectedCommit HEAD
if ($LASTEXITCODE -ne 0) { throw 'Shortcut worktree does not descend from accepted NWR V1 RC1.' }
$dirty = & git -c "safe.directory=$($repoRoot.Replace('\','/'))" -C $repoRoot status --porcelain
if ($dirty -and -not ($AllowUncommittedTest -and $DesktopOverride)) {
    throw 'Shortcut installation requires a clean committed launcher worktree.'
}

$pythonCandidates = @(
    (Join-Path $repoRoot '.venv\Scripts\pythonw.exe'),
    'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\pythonw.exe'
)
$pythonw = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $pythonw) { throw 'No supported pythonw.exe runtime was found.' }

if ($DesktopOverride) {
    $desktop = [System.IO.Path]::GetFullPath($DesktopOverride)
} else {
    $explorers = @(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'")
    $owners = @($explorers | ForEach-Object {
        $owner = Invoke-CimMethod -InputObject $_ -MethodName GetOwner
        if ($owner.ReturnValue -eq 0) { "$($owner.Domain)\$($owner.User)" }
    } | Select-Object -Unique)
    $current = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    if ($owners.Count -ne 1 -or $owners[0] -ne $current) {
        throw 'Interactive Explorer identity is unresolved or differs from the installer identity.'
    }
    $desktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
    if (-not $desktop) { throw 'Windows Desktop known folder could not be resolved.' }
}
if (-not (Test-Path -LiteralPath $desktop -PathType Container)) {
    throw "Desktop directory does not exist: $desktop"
}

$shortcutPath = Join-Path $desktop 'Niners War Room.lnk'
$shell = New-Object -ComObject WScript.Shell
$expectedArguments = '"' + (Join-Path $PSScriptRoot 'nwr_desktop.py') + '" start'
if (Test-Path -LiteralPath $shortcutPath) {
    $existing = $shell.CreateShortcut($shortcutPath)
    if ($existing.TargetPath -ne $pythonw -or
        $existing.Arguments -ne $expectedArguments -or
        $existing.WorkingDirectory -ne $repoRoot -or
        $existing.Description -ne 'Niners War Room V1') {
        throw 'A same-named shortcut exists but is not owned by this Niners War Room launcher.'
    }
}
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = $expectedArguments
$shortcut.WorkingDirectory = $repoRoot
$shortcut.Description = 'Niners War Room V1'
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,13"
$shortcut.Save()

$check = $shell.CreateShortcut($shortcutPath)
if ($check.TargetPath -ne $pythonw -or $check.Arguments -ne $expectedArguments -or
    $check.WorkingDirectory -ne $repoRoot -or $check.Description -ne 'Niners War Room V1') {
    throw 'Shortcut target validation failed.'
}
Write-Output $shortcutPath
