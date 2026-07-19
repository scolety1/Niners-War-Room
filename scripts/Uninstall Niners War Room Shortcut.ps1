param(
    [string]$DesktopOverride = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
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
        throw 'Interactive Explorer identity is unresolved or differs from the uninstaller identity.'
    }
    $desktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
}
if (-not $desktop) { throw 'Windows Desktop known folder could not be resolved.' }
$shortcutPath = Join-Path $desktop 'Niners War Room.lnk'
if (Test-Path -LiteralPath $shortcutPath) {
    $shell = New-Object -ComObject WScript.Shell
    $existing = $shell.CreateShortcut($shortcutPath)
    $expectedArguments = '"' + (Join-Path $PSScriptRoot 'nwr_desktop.py') + '" start'
    $pythonCandidates = @(
        (Join-Path $repoRoot '.venv\Scripts\pythonw.exe'),
        'C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\pythonw.exe'
    ) | Where-Object { Test-Path -LiteralPath $_ }
    if ($existing.TargetPath -notin $pythonCandidates -or
        $existing.Arguments -ne $expectedArguments -or
        $existing.WorkingDirectory -ne $repoRoot -or
        $existing.Description -ne 'Niners War Room V1') {
        throw 'Refusing to remove a same-named shortcut not owned by this Niners War Room launcher.'
    }
    Remove-Item -LiteralPath $shortcutPath -Force
}
Write-Output 'Shortcut removed. Persistent data and backups were preserved.'
