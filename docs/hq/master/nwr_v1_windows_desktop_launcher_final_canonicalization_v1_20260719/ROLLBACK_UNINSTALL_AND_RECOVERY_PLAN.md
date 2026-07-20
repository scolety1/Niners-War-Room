# Rollback, uninstall, and recovery plan

Repository rollback is normal Git history management and must never delete LocalData. Uninstall removes only exact installer-owned links, restores removed links if a later removal fails, and preserves `%LOCALAPPDATA%\NinersWarRoom`, backups, recovery backups, browser profile, and shared state.

Launcher restore validates manifests before mutation and rolls back exact prior state. Receipt recovery creates and validates a separate exact receipt-store backup and proves restore before canonical quarantine. A failed post-quarantine verification automatically restores the pre-action fingerprint. Real recovery requires the exact token and may be declined without changing bytes.
