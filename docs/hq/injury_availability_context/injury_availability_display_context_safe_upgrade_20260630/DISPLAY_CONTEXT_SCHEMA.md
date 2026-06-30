# Display Context Schema

Service reference:

`src/services/injury_availability_context_service.py`

## Contract

The safe upgrade now exposes tracked-artifact NFLVerse display fields for safe
identity rows. Dataset-backed denominator fields remain reserved contract fields
and stay `Not enough information` until a tracked artifact provides approved
denominators.

| Field | Group | Status | Notes |
| --- | --- | --- | --- |
| `player_id` | Identity | `SAFE_NOW` | Existing approved identity. |
| `gsis_id` | Identity | `SAFE_NOW` | Approved join key when exact. |
| `player_name` | Identity | `SAFE_NOW` | Display label only. |
| `position` | Identity | `SAFE_NOW` | Display label only. |
| `identity_match_status` | Identity | `SAFE_NOW` | Ambiguous identities keep injury and availability context as NEI. |
| `injury_context_available` | Factual injury context | `SAFE_NOW` | `true` only when approved injury report rows exist. |
| `prior_season_injury_report_weeks` | Factual injury context | `SAFE_NOW` | Season-total distinct report weeks. |
| `prior_season_out_or_doubtful_weeks` | Factual injury context | `SAFE_NOW` | Season-total distinct out/doubtful report weeks. |
| `games_while_rostered` | Availability denominator context | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Reserved now; NEI until refreshed weekly-roster and schedule coverage is green. |
| `games_with_snaps` | Availability denominator context | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Reserved now; NEI until refreshed snap count coverage is green. |
| `games_with_recorded_stats` | Availability denominator context | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Reserved now; NEI until refreshed stat coverage is green. |
| `games_played_context` | Availability denominator context | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Reserved now; NEI until denominator validation is complete. |
| `games_missed_while_rostered` | Availability denominator context | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Reserved now; not a cause label. |
| `per_game_denominator` | Availability denominator context | `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` | Reserved now; NEI until refreshed denominator inputs are green. |
| `season_total_caveat` | Caveat | `SAFE_NOW` | Explains injury-report counts are season totals by report week. |
| `per_game_caveat` | Caveat | `SAFE_NOW` | Explains per-game values wait for refreshed denominator coverage. |
| `availability_caveat` | Caveat | `SAFE_NOW` | States display-only/review-only and missing context as NEI. |
| `roster_status` | Tracked NFLVerse player context | `SAFE_NOW` | Safe direct display for safe identity rows only. |
| `weekly_roster_status` | Tracked NFLVerse player context | `SAFE_NOW` | Safe direct display for safe identity rows only. |
| `injury_report_status` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not healthy. |
| `practice_status` | Tracked NFLVerse player context | `SAFE_NOW` | Safe direct display for safe identity rows only. |
| `injury_report_date_week` | Tracked NFLVerse player context | `SAFE_NOW` | Report-week context only. |
| `last_active_season` | Tracked NFLVerse player context | `SAFE_NOW` | Factual last active season context. |
| `last_active_week` | Tracked NFLVerse player context | `SAFE_NOW` | Factual last active week context. |
| `snap_count_recency` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not zero. |
| `snap_sample_size` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not zero. |
| `roster_birth_date_derived_age` | Tracked NFLVerse player context | `SAFE_NOW` | Display-only age context. |
| `age_source` | Tracked NFLVerse player context | `SAFE_NOW` | Display-only age source. |
| `display_only` | Guardrail | `SAFE_NOW` | Always `true`. |
| `review_only` | Guardrail | `SAFE_NOW` | Always `true`. |
| `model_input_allowed` | Guardrail | `SAFE_NOW` | Always `false`. |
| `rank_use_allowed` | Guardrail | `SAFE_NOW` | Always `false`. |
| `source_truth_allowed` | Guardrail | `SAFE_NOW` | Always `false`. |

## Season-Total Versus Per-Game

Season-total injury-report counts answer:

`How many report weeks are present in the approved injury report source?`

They do not answer:

`How many games was the player available, active, inactive, or rostered?`

Per-game denominator fields require refreshed roster, schedule, snap, and stat inputs.
Until then, these fields remain `Not enough information`.
