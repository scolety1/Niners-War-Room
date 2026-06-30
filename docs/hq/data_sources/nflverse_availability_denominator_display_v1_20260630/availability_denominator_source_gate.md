# Availability Denominator Source Gate

Source gate result: YELLOW_PARTIAL_DENOMINATOR_ARTIFACT_READY

## Allowed Sources Used

- `weekly_rosters`: identity/roster support; missing roster rows are not inactive/healthy.
- `schedules`: display-only schedule game anchors.
- `snap_counts`: safe-review factual recorded snap rows; missing snap rows are not zero snaps.
- `player_stats_weekly`: safe-review factual recorded stat rows; missing stat rows are not zero stats.
- `nflverse_player_context_display_artifact.csv`: current NWR player universe and identity gate.

## Identity Approval Boundary

The pending NFLVerse identity approval decision sheet is not used as an approved overlay. Only existing player context rows with `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false` receive denominator context. Rows still needing identity review remain gated as `NEED_IDENTITY_APPROVAL` with denominator fields set to `Not enough information`.

## Source Coverage

- Schedules rows in approved snapshot: 570
- Weekly roster rows in approved snapshot: 93428
- Snap count rows in approved snapshot: 53227
- Weekly player stat rows in approved snapshot: 76804
- Regular-season schedule seasons used: 2024, 2025

## Blocked Logic

- `games_missed_while_rostered` is not computed. Absence of a snap/stat row is not enough to infer a missed game.
- No injury-risk score, durability score, medical projection, comeback projection, rank/model/source-truth promotion, hidden sort, recommendation, trade value, or pick value is allowed.
- `ff_rankings` is not used.

## Missingness Rule

Missing denominator data stays `Not enough information`; it is never converted to 0, false, healthy, clean, no-role, or confirmed missed/played.
