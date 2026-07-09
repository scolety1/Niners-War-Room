# Model v4 Regeneration Next Lane Recommendation

## Recommendation

Run `Model v4 Confidence Cap Receipt Regeneration Pilot V1` only after Master HQ explicitly approves execution.

## Why Confidence Cap First

`confidence_cap_receipts` has the strongest available schema support from the freeze lane: current-board confidence/status fields, source coverage matrix evidence, and partial historical component receipt context. It can be regenerated as a coverage and missingness receipt, not as a predictive score.

## Why Not Role Archetype First

`role_archetype_receipts` may require more subjective classification from usage and production context. It should wait until the confidence-cap pilot proves the source manifest, identity, missingness, and as-of workflow.

## Why Not Red Zone First

`red_zone_exact_receipts` should not regenerate until exact historical red-zone source artifacts and decision-date safety are proven. Inference from fantasy outputs is blocked.

## Not Allowed In The Next Lane

- Exact Model v4 replay.
- Formula Gauntlet tournaments.
- Weight tuning.
- Production/model-use source promotion.
- Ranking changes.
- App/runtime changes.
- Canonical `local_exports` writes.
