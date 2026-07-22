# NWR V1 backup and recovery

## Safe maintenance sequence

1. Stop NWR and confirm port_released: true.
2. Validate state.
3. Create a manual backup.
4. Record the returned snapshot ID.
5. Run restore-dry-run with that exact ID.
6. Review every CREATE, REPLACE, or UNCHANGED line.

Commands:

    powershell -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command validate-data

    powershell -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command backup

    powershell -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command restore-dry-run -SnapshotId SNAPSHOT_ID

The restore plan validates the manifest and every payload hash without changing
real state. A real restore is destructive and requires an exact snapshot-ID
confirmation; do not run it as a diagnostic.

## Retention

NWR keeps at most five valid snapshots. Each contains a versioned manifest with
approved state families, relative paths, byte sizes, and SHA-256 hashes.
Invalid or ambiguous material is not silently accepted.

## Data Health recovery

If a refresh receipt is corrupt, follow the explicit Data Health quarantine
flow. It preserves evidence before repair. Never delete receipt or runtime
folders by hand to make a warning disappear.

## RECOVERY_REQUIRED

This launcher status is a fail-closed ownership result. It means Stop could not
prove a remaining process is still NWR-owned. Wait briefly, run the canonical
Stop again, and keep the ownership record and last-stop receipt. Do not use a
broad task-kill command.

The 2026-07-22 closeout drill created snapshot
20260722T185226Z__manual, verified two payload hashes, produced a two-item
UNCHANGED restore plan, and confirmed retention at five. No real restore ran.
