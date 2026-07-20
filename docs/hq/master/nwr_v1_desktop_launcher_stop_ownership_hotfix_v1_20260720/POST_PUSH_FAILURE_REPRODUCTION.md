# Post-push failure reproduction

The canonical launcher was run from the isolated hotfix checkout with synthetic data and no real user-state access. Captured identities included PID, executable, creation time, command line, parent, repository, listener, data root, and run ID.

| Elapsed | Ownership | Stop request | Listener | Browser registrations |
|---:|---|---|---:|---:|
| 0.012 s | RUNNING | absent | 16472 | 0 |
| 1.204 s | RUNNING | present | 16472 | 0 |
| 5.869 s | absent | absent | 16472 | 0 |
| 22.535 s | absent | absent | 16472 | 0 |

Stop reported `Graceful stop timed out`; status then reported `HEALTHY` plus ownership `NONE`. This confirms the controlling defect before editing. Cleanup was limited to the captured, freshly revalidated process tree; port 8520 was then free.
