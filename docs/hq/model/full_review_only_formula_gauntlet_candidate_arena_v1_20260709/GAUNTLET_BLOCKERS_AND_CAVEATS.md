# Gauntlet Blockers And Caveats

- This is review-only.
- This is not production/model-use.
- This is not rankings integration.
- This is not app/runtime work.
- No source was promoted.
- No exact Model v4 replay field was used.
- No current/future context was used as historical input.
- Candidate definitions were fixed in code before scoring.
- Additional weight variants use deterministic reconstruction from review-only weighted fields; they are not recovered raw yearly receipt chains.

## Blocked Candidate Families
- `GAUNTLET_115_PFR_RB_BRK_TKL_RAW`: `actual_pfr_broken_tackle_values_not_in_formula_data_mart`.
- `GAUNTLET_116_PFR_RB_BRK_TKL_PER_GAME`: `actual_pfr_broken_tackle_values_not_in_formula_data_mart`.
- `GAUNTLET_117_PFR_RB_BRK_TKL_PER_ATTEMPT_DIAGNOSTIC`: `actual_pfr_broken_tackle_values_not_in_formula_data_mart`.
- `GAUNTLET_118_RED_ZONE_CARRIES_PARTIAL`: `partial_2024_2025_only_not_fair_for_2013_2025_gauntlet`.
- `GAUNTLET_119_RED_ZONE_TARGETS_PARTIAL`: `partial_2024_2025_only_not_fair_for_2013_2025_gauntlet`.
- `GAUNTLET_120_RED_ZONE_TD_OPPORTUNITY_PARTIAL`: `partial_2024_2025_only_not_fair_for_2013_2025_gauntlet`.
