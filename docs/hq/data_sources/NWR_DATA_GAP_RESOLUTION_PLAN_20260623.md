# NWR Data Gap Resolution Plan - 20260623

## Fix Now
- Current PDF/Sleeper free-agent verification: implemented as derived audit.
- Sleeper player status metadata warning context: implemented as display-only diagnostics.
- Player ID coverage audit/manual review queue: implemented.
- K/DST hidden-by-default audit: implemented.

## Partially Fix Now
- Current team/status repair: Sleeper metadata helps identify mismatches but does not replace manual/official review.
- Rookie age/DOB gap: Sleeper age metadata is available when matched; missing age remains `Not enough information`.
- Outcome support gaps: current app/data must keep same-position missing values as `Not enough information`.

## Cannot Fix Without Old Archives/API/License
- Complete historical trade history.
- Complete historical dropped-veteran league truth.
- Full injury/news/role context.
- Approved 2026/2027/next-5-year Outcome probability artifacts.
- Exact ADP for this specific rookie/free-agent keeper draft.

## Defer To Research Lane
- nflverse participation/routes/snaps and first-down reconstruction.
- CollegeFootballData rookie production intake after identity gates.
- Licensed factual route/red-zone/role fields after policy approval.
- DynastyProcess app wiring after Master accepts the market-baseline contract lane.

## Current Status
Runtime status: GREEN_RUNTIME_PULL. Manual identity-review rows: 74.
