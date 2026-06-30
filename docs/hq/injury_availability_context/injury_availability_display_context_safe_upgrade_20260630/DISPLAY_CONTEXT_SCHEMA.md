# Display Context Schema

Service reference:

`src/services/injury_availability_context_service.py`

## Contract

The display service exposes factual NFLVerse availability context only from
tracked artifacts. Denominator values are not computed in app pages.

Detailed player context requires:

- `nwr_player_id` join
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- schema-approved display-only field status

Denominator detail additionally requires:

- `denominator_status=SAFE_NOW_DISPLAY_ONLY`
- schema-approved display-only denominator field status

## Field Status

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
| `roster_status` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not healthy/clean/safe. |
| `weekly_roster_status` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not inactive by assumption. |
| `injury_report_status` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not healthy. |
| `practice_status` | Tracked NFLVerse player context | `SAFE_NOW` | Factual practice report display only. |
| `injury_report_date_week` | Tracked NFLVerse player context | `SAFE_NOW` | Report-week context only. |
| `last_active_season` | Tracked NFLVerse player context | `SAFE_NOW` | Factual last active season context. |
| `last_active_week` | Tracked NFLVerse player context | `SAFE_NOW` | Factual last active week context. |
| `snap_count_recency` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not zero. |
| `snap_sample_size` | Tracked NFLVerse player context | `SAFE_NOW` | Missing remains NEI, not zero. |
| `roster_birth_date_derived_age` | Tracked NFLVerse player context | `SAFE_NOW` | Display-only age context. |
| `age_source` | Tracked NFLVerse player context | `SAFE_NOW` | Display-only age source. |
| `season_anchor` | Availability denominator context | `SAFE_NOW` | Direct from safe denominator rows. |
| `games_while_rostered` | Availability denominator context | `SAFE_NOW` | Direct from safe denominator rows. |
| `games_with_snaps` | Availability denominator context | `SAFE_NOW` | Missing snaps remain NEI, not zero. |
| `games_with_recorded_stats` | Availability denominator context | `SAFE_NOW` | Missing stats remain NEI, not zero. |
| `games_played_context` | Availability denominator context | `SAFE_NOW` | Factual rostered/snap/stat context only. |
| `per_game_denominator` | Availability denominator context | `SAFE_NOW` | Direct from safe denominator rows. |
| `games_missed_while_rostered` | Availability denominator context | `YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION` | Still blocked; remains NEI. |
| `season_total_caveat` | Caveat | `SAFE_NOW` | Explains injury-report counts are season totals by report week. |
| `per_game_caveat` | Caveat | `SAFE_NOW` | Explains denominator values are tracked-artifact display only. |
| `availability_caveat` | Caveat | `SAFE_NOW` | States display-only/review-only and missing context as NEI. |
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

Per-game denominator fields now display only from the tracked denominator
artifact. They do not create missed-games, injury-risk, recovery, or medical
availability inference.
