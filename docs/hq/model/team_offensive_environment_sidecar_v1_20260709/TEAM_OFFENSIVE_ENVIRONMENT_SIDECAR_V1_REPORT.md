# Team Offensive Environment Sidecar V1 Report

Verdict: `YELLOW_TEAM_OFFENSIVE_ENVIRONMENT_PARTIAL_WITH_CAVEATS`

Artifact path: `C:\NWR\Niners-War-Room-team-offensive-environment-sidecar-v1-20260709\docs\hq\model\team_offensive_environment_sidecar_v1_20260709`

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

Prior plateau-review commit verified: `cb1da15b8580c45d770396995e90bcae0e3dc6c3`

## Source And Sidecar

- Source family: public nflverse/nflfastR `play_by_play_YYYY.parquet`, already cached locally under `C:\NWR_REVIEW`.
- Source seasons: `2012-2024`.
- Sidecar rows: `5518`.
- Prior-team environment joined rows: `5513` / `5518` (`99.9%`).
- Team environment source files hashed: `13`.
- Prior player team source precedence: EPA sidecar, snap/depth sidecar, injury availability sidecar, then receiving opportunity sidecar.

## Best Results

- Best component: `INGREDIENT_ONLY_TEAM_ENV_EPA_PER_PLAY` Spearman `0.264` vs PYF delta `-0.477`.
- Best formula x ingredient: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_TEAMENV_OFFENSE_SCORE_PCT025` Spearman `0.755`, seed delta `0.000`, snap/depth `.763` delta `-0.008`.
- Best ingredient combination: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_TEAM_FFOP_PCT050_050` Spearman `0.788`, seed delta `0.000`, partial flag `partial_window_only`.

## Plateau Comparison

- Results materially beating `.755` on non-partial rows: `5`.
- Results materially beating full-history `.758` on non-partial rows: `0`.
- Results materially beating snap/depth `.763` on comparable non-partial rows: `0`.

## Team-Change Caveat

The sidecar uses only each player's proven prior-season team. It does not project target-season team changes and does not use same-season team environment as a predictor. Rows without safe prior-team evidence remain missing rather than guessed.

## Decision

Team offensive environment classification: `AVAILABLE_REVIEW_ONLY_TEAM_CONTEXT`.

Review-only ranking simulation remains blocked. Production/model-use, rankings integration, app/runtime changes, source promotion, push/merge, and canonical `local_exports` mutation remain blocked.
