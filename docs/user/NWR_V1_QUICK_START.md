# NWR V1 quick start

## Launch

Double-click Niners War Room on the Windows desktop. The shortcut opens the
stable checkout at C:\NWR\Niners-War-Room-V1 and serves the app only on the
local computer.

Start Here is the safe first page:

1. Open Data Health and read any yellow or red items.
2. Open Dynasty Rankings and confirm Full dynasty rows: 240.
3. Use Player Compare or Trading Lab for read-only/manual review.
4. Enter Draft Cockpit only when you intend to use live local draft state.

## Stop

Closing the NWR app window normally ends the local session. For an explicit
verified Stop, run:

    powershell -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command stop

Wait for STOPPED and port_released: true. Never end broad groups of browser or
Python processes.

## If RECOVERY_REQUIRED appears

RECOVERY_REQUIRED means the launcher could not prove that every remaining
process still belongs to NWR. It deliberately refuses to kill an unrelated
process. Wait a moment and run the same Stop command once more. If it persists,
read NWR_V1_TROUBLESHOOTING.md and preserve the launcher receipts/logs.

NWR never enables automatic Git pull, commit, push, or source promotion.
