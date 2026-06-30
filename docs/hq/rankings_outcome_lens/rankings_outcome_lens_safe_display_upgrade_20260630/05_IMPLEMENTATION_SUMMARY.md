# Rankings / Outcome Lens Safe Display Upgrade - Implementation Summary

## Verdict

`YELLOW_SAFE_DISPLAY_PARTIAL_REFRESH_FIELDS`

The SAFE_NOW Rankings / Outcome display posture is preserved and a dataset refresh status panel was added. The centralized nflverse dataset-level refresh-health contract is present and GREEN for guardrails, but player-level nflverse display fields were deferred because the contract does not provide an approved row-level Rankings display artifact or join output.

## SAFE_NOW Changes

- Dynasty Review remains the clean default board with market and Outcome detail hidden by default.
- Market Context remains the focused place for DynastyProcess market context.
- Outcome Context remains V2-first, position-applicable, display-only, and review-only.
- Data Review remains review-focused.
- Draft Rankings remains narrow and avoids market/outcome clutter by default.
- Statistic Analysis remains audit/placeholder only and does not invent score components.
- Rankings now includes a `Dataset Refresh / Outcome Status` panel that uses the centralized nflverse refresh-health service and reports the nflverse gate state.

## nflverse-Backed Fields

Implemented as dataset/status display:

- centralized refresh-health contract status
- safe refresh dataset list
- full safe refresh dataset list
- `ff_rankings` blocked status
- source-policy display warnings

Not implemented as player-level columns in this rerun:

- roster age fallback
- roster status
- injury report status
- next game / bye context
- depth chart role context
- snap-share recency
- last active season
- draft capital display
- identity bridge health

Reason: `NEED_DATASET_REFRESH`. The tracked dataset-level registry and service are present, but there is no approved row-level Rankings display artifact or join gate for these fields.

## Outcome Lens Behavior

Outcome Context continues to show approved Outcome V2 display fields only where the committed artifact supports them. Missing/unvalidated values show `Not enough information`. RB T6/RB T12 Within 5Y remain blocked and are not displayed as probabilities.

## Market Behavior

Market fields are display-only. They do not drive Dynasty Rank, Final Board Rank, Candidate Rank, hidden sort, model input, trade value, or pick value.

## Rookie Gate G Status

Gate G remains blocked. This lane does not add rookie probabilities or Rankings rookie Outcome wiring.

## Dataset Refresh Status

The app now reports the centralized dataset-level nflverse refresh-health contract instead of implying player-level dataset support. `ff_rankings` remains blocked.

## Tests / Checks

Focused Rankings tests were updated to assert:

- dataset refresh status panel exists;
- the panel uses the centralized refresh-health service;
- the panel reports GREEN tracked contract status when the contract is present;
- the fallback still reports `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` if tracked artifacts are absent;
- it does not read raw/cache/shared paths;
- nflverse player-level fields are not surfaced without the refresh gate.

## Human Review Checklist

- Confirm whether HQ wants a separate row-level nflverse Rankings display artifact lane.
- Only after a row-level artifact/join gate exists should roster age fallback, roster status, injury report status, schedule context, depth context, snap recency, draft capital, or identity health move to player-table `SAFE_NOW`.
- Keep all missing data as `Not enough information`.
- Keep market, Outcome V2, and injury context display-only/review-only.
