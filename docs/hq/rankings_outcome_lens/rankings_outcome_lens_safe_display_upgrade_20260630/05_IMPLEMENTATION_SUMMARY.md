# Rankings / Outcome Lens Safe Display Upgrade - Implementation Summary

## Verdict

`YELLOW_SAFE_DISPLAY_PARTIAL_REFRESH_FIELDS`

The SAFE_NOW Rankings / Outcome display posture is preserved, dataset refresh status is visible, and the tracked NFLVerse player context artifact is integrated into Data Review for safe rows only.

## SAFE_NOW Changes

- Dynasty Review remains the clean default board with market and Outcome detail hidden by default.
- Market Context remains the focused place for DynastyProcess market context.
- Outcome Context remains V2-first, position-applicable, display-only, and review-only.
- Data Review remains review-focused.
- Draft Rankings remains narrow and avoids market/outcome clutter by default.
- Statistic Analysis remains audit/placeholder only and does not invent score components.
- Rankings now includes a `Dataset Refresh / Outcome Status` panel that uses the centralized nflverse refresh-health service and reports the nflverse gate state.
- Data Review now shows NFLVerse player context for rows with `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.
- NFLVerse roster birth-date age can fill missing primary Age before market fallback. Market `dp_age` remains market-only display context.

## nflverse-Backed Fields

Implemented as dataset/status display:

- centralized refresh-health contract status
- safe refresh dataset list
- full safe refresh dataset list
- `ff_rankings` blocked status
- source-policy display warnings

Implemented as Data Review player-level context:

- roster birth-date age fallback and age source
- roster status and weekly roster status
- injury report status/date and practice status
- depth chart role context
- snap recency and sample size
- last active season/week
- draft capital when present
- non-financial contract context
- identity bridge health/status
- data coverage status

Artifact counts:

- artifact rows: `294`
- safe display rows: `240`
- identity-review rows: `54`
- roster age rows: `240`
- injury report rows: `76`
- practice status rows: `220`
- depth role rows: `240`
- snap recency rows: `223`
- last active rows: `240`
- draft capital rows: `75`
- contract context rows: `240`

Deferred:

- next game / opponent / bye context: `NEED_DATASET_REFRESH` because the artifact has zero safe non-`Not enough information` rows.
- `NEED_IDENTITY_REVIEW` rows: values are not exposed except review status.

## Outcome Lens Behavior

Outcome Context continues to show approved Outcome V2 display fields only where the committed artifact supports them. Missing/unvalidated values show `Not enough information`. RB T6/RB T12 Within 5Y remain blocked and are not displayed as probabilities.

## Market Behavior

Market fields are display-only. They do not drive Dynasty Rank, Final Board Rank, Candidate Rank, hidden sort, model input, trade value, or pick value.

## Rookie Gate G Status

Gate G remains blocked. This lane does not add rookie probabilities or Rankings rookie Outcome wiring.

## Dataset Refresh Status

The app reports the centralized dataset-level nflverse refresh-health contract and the player-context artifact counts. `ff_rankings` remains blocked.

## Tests / Checks

Focused Rankings tests were updated to assert:

- dataset refresh status panel exists;
- the panel uses the centralized refresh-health service;
- the panel reports GREEN tracked contract status when the contract is present;
- the fallback still reports `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` if tracked artifacts are absent;
- it does not read raw/cache/shared paths;
- NFLVerse player-level fields are hidden from Clean Board and shown only in Data Review where artifact/schema gates are safe;
- identity-review rows do not expose NFLVerse context values.

## Human Review Checklist

- Review the 54 `NEED_IDENTITY_REVIEW` rows before exposing their context values.
- Consider a follow-up schedule-context lane only if next-game/opponent/bye rows become non-empty and safe.
- Keep all missing data as `Not enough information`.
- Keep market, Outcome V2, and injury context display-only/review-only.
