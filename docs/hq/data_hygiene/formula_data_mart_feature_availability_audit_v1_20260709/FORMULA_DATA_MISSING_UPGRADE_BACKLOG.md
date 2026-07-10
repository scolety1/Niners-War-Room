# Formula Data Missing Upgrade Backlog

## Highest Priority

1. `route_yprr_tprr_exact_receipts`: Route Recovery/source admission only; true routes, YPRR, and TPRR remain blocked.
2. `return_scoring_receipts`: source admission/recovery lane required before any formula use.
3. `red_zone_exact_receipts`: regeneration pilot/contract required before values can enter a mart.
4. `shadow_model_v2_metrics.csv`: manual recovery or Master HQ scope-removal decision required.
5. `checkpoint_review_score_historical` and `position_specific_review_score_historical`: exact Model v4 replay remains blocked without season-by-season receipts.
6. `age_lifecycle` and `experience_year`: historical sidecar receipts remain missing or not separately admitted.
7. PFR RB broken tackles: preserve only as narrow RB review-only context; a joined runner/panel is still required before inclusion.
8. Rookie/draft-capital context: needs source/use-gate review before any formula sprint.
9. Injury/availability context: needs point-in-time historical as-of controls.
10. Market/ADP context: needs historical point-in-time source gate; display-only until then.

## Do Not Backfill By Guessing

Blocked fields in `FORMULA_DATA_MART_REVIEW_ONLY.csv` are status flags only. They must not be interpreted as zeroes, inferred values, or permission to run formula tournaments.
