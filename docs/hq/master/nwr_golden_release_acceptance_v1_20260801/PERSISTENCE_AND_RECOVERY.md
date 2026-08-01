# Persistence and Recovery

Isolated tests cover atomic save, close/reload equivalence, restart/resume,
backup creation and retention, receipt integrity, corrupt/oversized/unsupported
state handling, restore dry-run boundaries, failed-write rollback, and no
page-open persistence. Draft, mock-draft, development-lab, refresh-receipt, and
launcher state contracts passed. Canonical source files were never targets.

No production user state was mutated during acceptance.
