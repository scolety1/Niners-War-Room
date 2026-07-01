# Blocked Or Display-Only Features

Verdict: `YELLOW_BLOCKED_AND_DISPLAY_ONLY_POSTURE_CONFIRMED`

## Display-Only Or Review-Only

The following can remain display/review context only where prior lanes already approved safe-row use:

- roster status;
- weekly roster status;
- injury report status as a caveat;
- practice status as a caveat;
- schedule next game / opponent / bye;
- depth chart role;
- snap recency / sample;
- last active season / week;
- draft capital where positive draft-pick evidence exists;
- contract context as non-financial context;
- identity bridge health as a gate/prerequisite;
- availability denominator fields for supported rows.

Display/review use does not imply experiment, model, training, source-truth, rank, hidden-sort, valuation, recommendation, or app activation safety.

## Blocked By Leakage

- injury report status;
- practice status;
- depth chart role;
- snap recency / sample;
- last active season / week.

These fields require point-in-time proof and leakage diagnostics before any future experiment request.

## Blocked By Missingness Or Guardrail

- availability denominator fields need a missingness gate before any stronger use.
- `games_missed_while_rostered` remains `Not enough information` and blocked.
- Missing injury is not healthy.
- Missing availability is not healthy, clean, played, missed, or no-risk.
- Missing snaps/stats are not zero.
- Missing draft capital is not UDFA.

## Blocked By Source Policy

- CFBD joins;
- UDFA status;
- `ff_rankings`;
- market / ADP / DynastyProcess.

## Label And Sidecar Boundaries

NFLVerse `player_stats` is sidecar/review-only. Outcome V2 labels and Rookie Outcome labels are evaluation targets only. Labels are never input features. No label source is promoted to training truth or source truth by this packet.
