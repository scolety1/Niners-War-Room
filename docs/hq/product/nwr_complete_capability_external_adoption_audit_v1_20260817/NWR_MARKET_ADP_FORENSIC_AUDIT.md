# NWR Market / ADP Forensic Audit

## Existing Market number

The installed/candidate Market artifact is `dp_market_baseline_context.csv`, supported by `dp_freshness_report.csv`. It is a **Dynasty 1QB** DynastyProcess snapshot with upstream scrape date 2026-06-19 and fetch date 2026-06-23. Fields include `ecr_1qb`, `ecr_pos`, `value_1qb`, `dp_market_rank_1qb`, `dp_value_1qb` and `nwr_vs_dp_gap`.

It is display-only market context. It is stale on the audit date, it is not a Redraft expected-pick distribution, and it cannot be relabeled ADP.

## Redraft ADP finding

No usable Redraft ADP exists in the current Redraft engine, practical mock, Sleeper owner adapter or desktop Redraft surfaces. Sleeper's official API documents read-only users/leagues/rosters/drafts/picks/transactions/player maps, but no supported ADP endpoint. Historical Sleeper draft picks can be ingested after identity and sample controls; they are not a free current ADP guarantee.

## Required contract

Create one provider-neutral `AdpSnapshot` contract after owner approval:

- source, season, format, platform, teams, scoring, generated/fetched timestamps;
- stable player ID plus crosswalk evidence;
- mean/median expected pick, dispersion/sample count when supplied;
- coverage, missingness, freshness and license/terms receipt;
- immutable content hash and explicit fallback state.

Safe baseline: owner-imported CSV. Optional provider: an owner-approved licensed API such as FantasyPros, whose official projections API requires an API key and separate terms. A paid/keyed provider must remain optional. MFL or other sources remain research candidates until contract and terms are verified.

## Beat ADP boundary

Beat ADP needs two separately labeled outputs: `NWR View` (replacement-adjusted value/rank gap) and `Draft Timing` (expected pick, next owner pick, survival, position run, tier cliff). The first is deterministic once ADP exists. The second may begin as a disclosed heuristic; probability language requires historical calibration and backtesting.
