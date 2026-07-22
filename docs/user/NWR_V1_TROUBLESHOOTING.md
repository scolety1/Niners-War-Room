# NWR V1 troubleshooting

## The app does not open

Run the status command and check health_status, process_ownership,
state_validation, and port 8520:

    powershell -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command status

If another process owns port 8520, NWR refuses to reuse or kill it. Close the
known owner normally; do not terminate broad process groups.

## RECOVERY_REQUIRED

The launcher retained evidence because identity changed or cleanup was
incomplete. Run canonical Stop again after a short wait. A second pass can
finalize already-exited verified resources while still ignoring reused PIDs.
If it persists, inspect the launcher log and run directory without editing
them, then preserve the receipts for review.

## Rankings are missing or rejected

The stable checkout must contain the approved local rankings export. The loader
requires exactly 240 rows and the pinned SHA-256. A mismatch is a blocker; do
not copy another board into place or change the expected hash.

## Data Health is yellow or red

Open the detailed status. Yellow means review the named caveat. Red means stop
using that area until repaired. Missing information is never a healthy value.
Use the explicit receipt quarantine/recovery flow when offered.

## Refresh Data is blocked

Refresh is intentionally gated. Manual sources, credentials, LocalData packs,
and provider-specific setup are not inferred. Do not add credentials or call a
provider merely to clear the status.

## LocalData says BLOCKED_MISSING_LOCAL_TEST_PACK

That is the required result when the authorized local pack is absent. Do not
synthesize, copy, import, or check in a replacement.

## A feature says parked or review-only

That label is authoritative. Use a live supported surface instead. Do not
enable a parked route or promote review evidence without a separate approved
lane.
