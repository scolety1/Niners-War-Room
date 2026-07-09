# Model v4 Role Archetype Component Signal Test V1 Report

## Verdict

`GREEN_ROLE_ARCHETYPE_COMPONENT_SIGNAL_USEFUL_REVIEW_ONLY`

## Clear Answer

Role archetypes add useful review-only guardrail context because they split historical rows into interpretable prior-volume and sparse-history buckets that expose PYF miss patterns. They are not a formula score, tournament result, ranking input, or production accuracy claim.

## Scope

- Rows tested: `5518`
- Seasons: `2013-2025`
- Position coverage: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Distinct archetypes: `16`
- Input signal tested: regenerated `role_archetype_receipts` only
- Baseline: PYF / `prior_nwr_points` from the existing partial replay panel

## Main Findings

- Best large-bucket startable rates: `wr_high_volume_target_volume=53.0%, rb_high_volume_touch_volume=47.9%, qb_high_volume_passing_volume=41.2%`
- Weakest large-bucket startable rates: `te_sparse_history_low_games=1.2%, rb_low_volume_touch_volume=1.5%, wr_low_volume_target_volume=1.6%`
- Largest PYF false-positive buckets: `wr_high_volume_target_volume=183, rb_high_volume_touch_volume=162, te_high_volume_target_volume=80`
- Sparse-history rows: `1453` with startable rate `3.3%`.
- Low/sparse archetypes flagged `15.3%` of PYF false negatives.

## Interpretation

The receipts are useful for review-only diagnosis of sparse-history, low-games, prior-volume, and empty-volume patterns. They do not beat PYF as a standalone ranker, but they help explain where PYF misses and where human review should be more cautious.

## Production Status

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Formula Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- Production/model-use remains blocked.
- No source was promoted.

## Recommendation

Recommended next lane: `Model v4 Role Archetype Master Review V1`, to admit or limit these receipts for future review-only component signal tests before any further execution.