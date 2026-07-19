# Rollback and uninstall plan

1. Run `scripts\NWR Desktop Commands.ps1 -Command stop`.
2. Run `scripts\Uninstall Niners War Room Shortcut.ps1` as the interactive user.
3. Remove only the two validated junctions if their resolved targets exactly match the launcher data roots. The supplied uninstall intentionally does not remove data or junctions automatically.
4. Preserve `%LOCALAPPDATA%\NinersWarRoom`, `C:\NWR_SHARED_DATA\draft_runtime_state`, and `C:\NWR_SHARED_DATA\development_lab_state` by default.
5. To roll back code, stop using the launcher worktree; do not reset or alter the primary worktree.

User data and backups are never deleted by shortcut uninstall. Destructive data removal requires a separate explicit future request.
