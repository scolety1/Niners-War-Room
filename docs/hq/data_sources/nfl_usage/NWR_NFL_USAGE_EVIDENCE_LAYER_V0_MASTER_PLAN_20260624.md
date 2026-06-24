# NWR NFL Usage Evidence Layer V0 Master Plan

## Verdict

YELLOW safe research lane. The evidence layer is built as contract, inventory, validation, quarantine, and review infrastructure. Live nflreadpy collection is blocked in this environment because `nflreadpy` is not installed and the packet forbids blind dependency installation.

## Scope

NFL Usage Evidence Layer V0 is a research-only lane for public NFL role and usage evidence after players enter the league. It replaces the unsafe RotoWire live-scraper concept with public nflverse/nflreadpy-style sources and strict proxy labeling.

Allowed status in V0:
- `model_input_allowed=no`
- `app_wiring_allowed=no`
- review artifacts only
- no Dynasty Rank, Final Board Rank, tier, source-truth, pinned snapshot, latest_candidate, or latest_approved mutation

## Source Families

- `player_stats`: true factual weekly player production and usage fields when present.
- `pbp`: true play-level public facts used only for transparent red-zone, inside-10, inside-5, touch, opportunity, and first-down derivations.
- `snap_counts`: true factual offensive snaps and offensive snap percentage where available.
- `nextgen_stats`: inventory/candidate evidence for public NGS efficiency fields.
- `participation`: inventory/candidate context only; route-like fields stay proxy-labeled unless exact routes are verified.
- `ftn_charting`: inventory/candidate evidence only with FTN attribution and license checks.
- `pfr_advstats`: inventory/candidate evidence only with PFR attribution and license checks.
- `rosters/player IDs/crosswalks`: identity support only.

## Guardrail Implementation Plan

1. Keep raw downloads under `C:\NWR_SHARED_DATA\nfl_usage_cache\`.
2. Commit only small docs, contracts, tests, and sanitized review summaries.
3. Fail closed when source packages, required fields, licenses, or attribution are missing.
4. Quarantine blocked fields and any route truth overclaim.
5. Require promotion/backtest before display-only app context or model-candidate use.

## External References

- nflreadpy package: https://github.com/nflverse/nflreadpy
- nflreadr package overview: https://nflverse.r-universe.dev/nflreadr
- nflreadr NGS docs: https://rdrr.io/cran/nflreadr/man/load_nextgen_stats.html
- nflreadr FTN docs: https://rdrr.io/cran/nflreadr/man/load_ftn_charting.html
- nflreadr PFR docs: https://rdrr.io/cran/nflreadr/man/load_pfr_advstats.html

## Closeout Gate

V0 can be considered complete when docs, review CSVs, services, tests, Ruff, compile, CSV load checks, `git diff --check`, raw-data tracking checks, frozen-board row checks, and pinned/latest guardrail checks pass.
