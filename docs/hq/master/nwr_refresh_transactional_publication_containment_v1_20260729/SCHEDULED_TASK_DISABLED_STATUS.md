# Scheduled Task Disabled Status

Task:
`\NWR DynastyProcess Market Baseline Refresh`.

Read-only `schtasks /Query /V /FO LIST` checkpoints reported:

- status: `Disabled`;
- scheduled task state: `Disabled`;
- next run: `N/A`;
- action:
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room\scripts\run_dynastyprocess_refresh_task.ps1"`;
- start in: `C:\NWR\Niners-War-Room`;
- last run: 2026-07-27 23:48:49 MDT;
- last result: 0.

The existing action was inspected but not changed. The task was not run and was
not enabled. Required final state:
`DISABLED_PENDING_OWNER_APPROVAL`.
