# Synthetic retention revalidation

The 40-test launcher suite and full Hermetic collection revalidated outside-worktree roots, draft save/restart, backup/restore, crash temp-file rejection, checkout replacement, retention pruning, corrupt-backup rejection, failed-restore rollback, conflicting migration rejection, duplicate/port safety, browser ownership, and disposable installer/uninstaller behavior.

A live root at `C:\NWR\.codex-launcher-smoke-e5df0f29` produced `VALID_STATE`, healthy first start, duplicate reuse, clean stop with `port_released=true`, manual snapshot `20260720T181255Z__manual`, healthy restart with retained backup metadata, and final `STOPPED`/`NONE`. No real user state was used.
