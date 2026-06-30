# Label Source Policy After NFLVerse

## Outcome V2 Labels

Outcome V2 historical labels remain review/evaluation targets. They are not
input features.

The 2000-2024 historical validation packet preserves:

- `RB_T12_WITHIN_5Y`: `APPROVE_REVIEW_ONLY`
- `RB_T6_WITHIN_5Y`: `KEEP_BLOCKED_WEAK_CALIBRATION`

This approval is historical review-only. It does not approve current-player
activation, app-facing probabilities, model input, source truth, or rank logic.

## NFLVerse player_stats

NFLVerse `player_stats` may become a sidecar comparison/evaluation source after
parity and label-spec gates. It is not automatic training truth. It is not
source truth merely because refresh-health is GREEN.

## Vendor / Local Labels

RotoWire/local/vendor-derived labels remain display-only/local-review unless a
separate approval explicitly changes their status. This audit does not approve
vendor, Gmail, market, ADP, DynastyProcess, or analyst sources for model input.

## Labels Are Not Features

Historical labels may evaluate outcomes; they must not be fed back as input
features for the same prediction target.

## Missing And Censored Labels

Missing labels remain:

`Not enough information`

Incomplete future windows are right-censored. Missing/censored labels are not
failures, zeros, false, no-hit labels, or active probabilities.

## First-Down Scoring

First-down scoring status and label exactness remain governed by the existing
Outcome V2 label factory and validation docs. This audit does not alter label
factory scoring rules.

## Rookie Labels

Rookie drafted-only labels remain review-only. CFBD production is not NFL
outcome truth. UDFA status requires direct approved evidence before it can move
beyond review-only status.
