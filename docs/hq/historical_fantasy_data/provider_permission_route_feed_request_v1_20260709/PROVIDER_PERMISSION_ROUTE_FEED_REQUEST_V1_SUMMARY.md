# Provider Permission Route Feed Request V1 Summary

Lane: Provider Permission and Contractable Route Feed Request V1
Artifact date: 2026-07-09
Worktree: `C:\NWR\Niners-War-Room-provider-permission-route-feed-request-v1-20260709`
Branch: `work/lane-provider-permission-route-feed-request-v1-20260709`
Verified base: `origin/work/hq-parallel-control` at `4a8c9894ae737d2fe88a2abcb4064a270286ca30`

## Verdict

`YELLOW_CONTRACTABLE_ROUTE_FEED_SPEC_READY_NO_SOURCE_ADMITTED`

This lane stops broad public searching and defines the exact contractable route-denominator feed NWR must obtain before true route-derived metrics can be admitted.

No source was admitted. No route/YPRR/TPRR production calculation was created. True routes, YPRR, and TPRR remain production-blocked.

## Canonical Context

Canonical upstream packets:

- `docs/hq/historical_fantasy_data/routes_run_denominator_recovery_v2b_20260709/`
- `docs/hq/historical_fantasy_data/sumer_espn_routes_run_hardening_v1_20260709/`

Current source status:

- SumerSports verdict: `YELLOW_ROUTE_DENOMINATOR_LEAD`.
- ESPN Receiver Scores verdict: `YELLOW_ROUTE_DENOMINATOR_LEAD`.
- No `GREEN_ROUTE_DENOMINATOR_CANDIDATE`.
- Sumer WR/TE route columns and ESPN `rtm_routes` make route denominators technically plausible.
- Neither Sumer nor ESPN clears permission/export/API gates.
- Sumer RB route fields are payload-only for 2022-2025 and are not a supported/licensed feed.

## Minimum Contractable Feed

NWR needs a provider-permitted feed with:

- actual player-level `routes_run`
- WR/TE/RB pass-catcher coverage
- season grain at minimum
- week or game grain preferred
- stable player identity field
- player name, team, season, position
- game ID and week fields if weekly/game grain
- field dictionary
- historical coverage range
- update cadence
- license and allowed-use terms
- reproducible API/export/static file path
- checksum/provenance support
- missingness documentation
- redistribution/storage restrictions

If the feed lacks a stable identity field, approved row grain, license terms, or reproducible retrieval path, it remains blocked regardless of visible route columns.

## Provider Targets

Priority 1: ESPN / Disney / ESPN Analytics

- Reason: ESPN hardening found actual `rtm_routes`, `rtm_targets`, `yds`, `gsis_id`, `dot_com_id`, `tm`, `position`, and 2017-2025 coverage in public client metadata.
- Main ask: permission or contract for a supported receiver-tracking metrics feed, field dictionary, row-grain rules, and allowed NWR storage/use.

Priority 2: SumerSports

- Reason: Sumer hardening found WR/TE visible route fields and WR/TE/RB route-like payload fields for 2022-2025.
- Main ask: permission or contract for `receivingPassRoutesRun`, supported WR/TE/RB coverage including RB confirmation, Sumer ID documentation, and export/API path.

Fallback contractable leads:

- PFF, SIS, Sportradar, commercial FTN, FantasyPoints Data, Establish The Run, Rotoviz, SportsDataIO, and similar providers.
- These are not usable unless explicitly licensed, exported through a permitted feed, and admitted later.

## Final Status

True `routes_run` remains blocked. YPRR and TPRR remain derivable only later if a provider-permitted route denominator feed is admitted in a separate source-admission lane.

Recommended next lane: `Provider Outreach Execution and Route Feed Response Review V1`.
