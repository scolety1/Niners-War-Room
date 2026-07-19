# Synthetic end-to-end retention results

All mutable tests used isolated roots. The prior task directly proved health, duplicate launch, clean stop/restart, changed-state post-shutdown backup, stale-lock recovery, crash retention, dry-run/restore, corrupt-backup rejection, and checkout-root replacement with the same data root. The continuation reproduced the owning-service backup/restore and replacement contracts in focused tests and ran a final real no-browser cycle: health 200, `VERIFIED_RUNNING`, duplicate exit 0, Stop exit 0, no listener, then exact synthetic junction/profile cleanup.

The correction suite additionally proves: unknown families reject; hash-consistent invalid schemas reject; Windows rooted-relative paths reject; failed mutation removes introduced invalid state before exact rollback; empty-state rollback works; oldest-at-retention restore cannot prune its source; browser registrations target only verified approved trees; identity and registration-write failures reap the direct process; malformed registrations never target a process.

Focused continuation result: 28 passed. Real user state was never used for restore or migration. GUI browser teardown remains not run because interactive ownership and installation are blocked.
