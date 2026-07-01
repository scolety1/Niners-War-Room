# Remaining Zero Blocker Report

The machine-readable blocker status is in `remaining_zero_blocker_report.csv`.

Rows excluded from the parity subset remain excluded and are not converted to zeros. This includes `NOT_ENOUGH_INFORMATION`, `IDENTITY_GATED`, inactive/out/not-rostered/bye/not-applicable/source-missing contexts, and any row where safe-zero evidence is insufficient.

Key unresolved counts:

- `NOT_ENOUGH_INFORMATION`: `51`
- `IDENTITY_GATED`: `44`
- `ROSTERED_INACTIVE_NOT_ZERO`: `928`
- `INJURY_OUT_NOT_ZERO`: `324`
- `NOT_ROSTERED_NOT_APPLICABLE`: `2,683`
