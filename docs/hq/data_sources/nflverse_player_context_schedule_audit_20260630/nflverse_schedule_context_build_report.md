# NFLVerse Schedule Context Build Report

As-of date: `2026-06-30`
Teams audited: `34`
Teams with schedule rows: `32`
Teams with current/future game rows: `0`

Root cause:

approved schedules data is present for 2024-2025 only; as_of_date has no current/future games, and the player-context builder correctly leaves next game/opponent/bye as Not enough information

Findings:

- Approved schedules data is present and readable.
- Local schedules cover 2024-2025 with weeks 1-22.
- The latest local game date is before the current as-of date, so next game, opponent, and bye cannot be safely populated.
- Team abbreviations are mostly aligned for nflverse team codes; app-facing `LAR` and `JAC` require aliases to schedules `LA` and `JAX` when using NWR team values directly.
- Current-date/week logic is required before any future schedule display.
- Missing schedule context remains `Not enough information`.