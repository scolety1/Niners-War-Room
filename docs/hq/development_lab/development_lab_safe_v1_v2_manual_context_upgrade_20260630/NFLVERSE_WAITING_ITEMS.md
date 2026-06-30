# NFLVerse Player Context Display Pass

Prior verdict: `YELLOW_SAFE_PARTIAL_DATA_GATED`

Current base: `origin/work/hq-parallel-control` at `2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0`.

Confirmed HQ artifacts:

- Refresh-health contract: yes.
- Player-context display artifact: yes.
- Player-context schema manifest: yes.
- Identity review packet: yes.
- Schedule audit packet: yes.

Moved from `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN` to implemented:

- F2 auto roster snapshot: implemented as safe display artifact context, joined only by `nwr_player_id`.
- F3 roster/status/depth/snap/contract context: implemented for schema-approved fields and safe identity rows.
- F4 NFL draft context for Future Pick Planning: implemented for factual NFL draft year/round/pick/team when present.
- F5 Upcoming Draft Prep readiness/context: implemented with dataset readiness and factual draft-capital display rows.
- F7 shared deadline review context table: implemented as roster/status/availability labels for manual checklist support.
- F10 refresh adapter consumption: implemented through repo-backed service helpers reading tracked artifact/schema docs only.

Still gated:

- F6 identity proposals: `YELLOW_NEEDS_IDENTITY_REVIEW`. There are 54 identity-review artifact rows; 43 proposals exist but are not approved joins, 4 rows need human review, and 7 rows remain `KEEP_NEED_IDENTITY_REVIEW`.
- Schedule next game / opponent / bye: intentionally gated in Development Lab for a later lane-specific display review, so these fields remain `Not enough information`.
- `ff_rankings`: blocked by source policy and unused.

Displayed player fields:

- Roster/status context: `nwr_player_id`, `nwr_player_name`, `nwr_position`, `nwr_team`, `nflverse_team`, `nflverse_position`, `roster_birth_date_derived_age`, `age_source`, `roster_status`, `weekly_roster_status`, `injury_report_status`, `injury_report_date_week`, `practice_status`, `last_active_season`, `last_active_week`, `snap_count_recency`, `snap_sample_size`, `per_field_dataset_source`, `per_field_freshness_source_status`, `data_coverage_status`.
- Deadline context adds: `depth_chart_position`, `depth_chart_rank` shown as depth-chart slot, `depth_chart_role`, `contract_context`.
- Draft context: `draft_year`, `draft_round`, `draft_pick`, `drafted_team`.

Display gates:

- Player-level rows must have `identity_join_status=SAFE_NOW_DISPLAY_ONLY`.
- Player-level rows must have `review_required=false`.
- Displayed fields must have `field_status=SAFE_NOW_DISPLAY_ONLY` in `nflverse_player_context_schema_manifest.csv`.
- Any unavailable, unmapped, stale, review-needed, or unapproved field renders as `Not enough information` or `Needs identity review`.

Final safety status: `YELLOW_NEEDS_IDENTITY_REVIEW`.
