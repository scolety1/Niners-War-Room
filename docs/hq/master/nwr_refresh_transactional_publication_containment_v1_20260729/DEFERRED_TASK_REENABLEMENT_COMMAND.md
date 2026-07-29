# Deferred Task Re-enablement Command

Status: `DOCUMENTED_NOT_EXECUTED`.

After the canonical code is separately deployed to
`C:\NWR\Niners-War-Room` and the owner explicitly approves the action, the
deferred task-action update is:

```powershell
$taskName = 'NWR DynastyProcess Market Baseline Refresh'
$safeRoot = 'C:\NWR\Niners-War-Room\local_exports\refresh_data\dynastyprocess_market_baseline'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\NWR\Niners-War-Room\scripts\run_dynastyprocess_refresh_task.ps1`" -SafeRoot `"$safeRoot`"" -WorkingDirectory 'C:\NWR\Niners-War-Room'
Set-ScheduledTask -TaskName $taskName -Action $action
```

The separately owner-approved re-enablement command would then be:

```powershell
Enable-ScheduledTask -TaskName 'NWR DynastyProcess Market Baseline Refresh'
```

Neither command was executed in this lane. Until deployment validation and
owner approval, the task must remain disabled.
