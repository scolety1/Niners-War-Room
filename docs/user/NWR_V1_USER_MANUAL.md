# NWR V1 user manual

## The operating idea

NWR separates read-only decisions, manual planning, explicit draft state, and
gated administration. Start Here labels each workflow honestly.

## Rankings

Dynasty Rankings is the accepted 240-row board. Dynasty Rank remains primary.
Market, Outcome, NFLVerse, confidence, injury, and evidence fields are context;
they do not silently replace the rank or model value. Use search, position,
team, player type, preset, and advanced filters to narrow what you see.

The Outcome Context preset includes the display-only Outcome Columns V3 lens.
For the 2026 board it shows 2026, 2027, 2028, Within 3 Years, and Within 5
Years for the selected position and threshold. Wrong-position rows are `N/A`;
blocked or insufficient applicable evidence is `Not enough information`.

## Player Compare

Choose two to four players to compare visible, read-only context. Missing
evidence is shown as a hold or Not enough information. Comparing players does
not change a rank, tier, formula, source, or draft state.

The Outcome / Horizon tab expands the V3 lens across every applicable
position threshold and adds Two Qualifying Seasons Within 3 Years. All joins
use the exact player ID; the comparison never falls back to player names.

## Trading Lab

Trading Lab is a manual decision aid. Build both sides yourself and use the
visible frozen-board and pick-window context as review material. NWR does not
submit an offer, calculate a private value, persist a trade, or make a final
trade recommendation.

## Draft tools

Draft Cockpit is the live local draft surface. Only explicit controls change
its local runtime state. Mock Drafts is separate practice state. Draft Analyzer
reviews a live or mock event log but is not official source truth. Upcoming
Draft Prep and the manual roster tools are checklists and operator aids; they
do not hydrate a roster or rewrite rankings automatically.

## Data Health and Refresh Data

Data Health summarizes freshness, state validity, evidence gaps, and recovery
guidance. GREEN means usable, YELLOW means review the caveat, and RED means stop
trusting that area until repaired.

Refresh Data is a gated manual action. It checks protected/manual sources and
pulls only approved eligible sources. It does not automatically update ranks,
models, frozen artifacts, candidates, or draft state. Do not enter provider
credentials unless a separately authorized setup requires them.

## Backups

Stop NWR before maintenance. Validate state and create a manual backup with:

    powershell -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command validate-data

    powershell -NoProfile -ExecutionPolicy Bypass -File "C:\NWR\Niners-War-Room-V1\scripts\NWR Desktop Commands.ps1" -Command backup

Use restore-dry-run with the exact snapshot ID before any real restore. NWR
keeps a bounded set of five valid snapshots.

## What remains manual or unavailable

LocalData tests remain unavailable when the authorized local pack is absent;
the correct result is BLOCKED_MISSING_LOCAL_TEST_PACK. Parked features remain
parked. Automatic Git behavior, provider calls, roster hydration, source
promotion, and Trading Lab persistence remain disabled.
