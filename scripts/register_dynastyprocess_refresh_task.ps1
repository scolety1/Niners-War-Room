$ErrorActionPreference = "Stop"

$TaskName = "NWR DynastyProcess Market Baseline Refresh"
$RepoRoot = "C:\NWR\Niners-War-Room"
$WrapperScript = Join-Path $RepoRoot "scripts\run_dynastyprocess_refresh_task.ps1"

if (-not (Test-Path -LiteralPath $WrapperScript)) {
    throw "Wrapper script not found: $WrapperScript"
}

$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WrapperScript`"" `
    -WorkingDirectory $RepoRoot

$FridayTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "06:00"
$SaturdayTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At "08:00"
$Principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$Task = New-ScheduledTask `
    -Action $Action `
    -Trigger @($FridayTrigger, $SaturdayTrigger) `
    -Principal $Principal `
    -Settings $Settings `
    -Description "Refreshes NWR DynastyProcess display-only market baseline after upstream weekly data refresh."

Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
Write-Host "User: $CurrentUser"
Write-Host "Schedule: Friday 06:00 local time; Saturday 08:00 local time"
Write-Host "Action: powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$WrapperScript`""
