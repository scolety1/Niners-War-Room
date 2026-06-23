$ErrorActionPreference = "Stop"

$TaskName = "NWR DynastyProcess Market Baseline Refresh"
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($null -eq $ExistingTask) {
    Write-Host "Scheduled task not found: $TaskName"
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Unregistered scheduled task: $TaskName"
Write-Host "Cache and logs were not deleted."
