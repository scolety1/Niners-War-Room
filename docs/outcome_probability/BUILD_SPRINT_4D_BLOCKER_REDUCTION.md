# Build Sprint 4D: Blocker Reduction

Status: `SPRINT_5_STILL_BLOCKED`

Sprint 4D audits local source candidates that could reduce the blockers left after the collapsed Sprint 4C internal benchmark. It does not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, or deploy.

## Inputs Reviewed

- `local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_week.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_usage_player_week.csv`
- `local_exports/truth_set_lab/v3/reports/truth_set_v3_snap_share_player_week.csv`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2022.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2023.csv.gz`
- `local_exports/truth_set_lab/v3/downloads/play_by_play_2024.csv.gz`
- local data-pack identity candidates with DOB/age fields
- Sprint 3D, Sprint 4, Sprint 4B, and Sprint 4C readiness exports

## Outputs

Sprint 4D writes only to:

`local_exports/outcome_probability/sprint_4d_blocker_reduction/`

Created outputs:

- `age_dob_coverage_audit.csv`
- `rare_component_supplement_audit.csv`
- `component_waiver_sensitivity.csv`
- `next_year_support_audit.csv`
- `broader_data_coverage_audit.csv`
- `sprint_5_readiness_blockers.csv`
- `README_SPRINT_4D.md`

## Age / DOB Coverage

The strongest age/DOB candidate is:

`local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/dynastyprocess_db_playerids.csv`

It includes `birthdate`, `age`, `gsis_id`, and identity fields, and it matched all 35 current truth-set players by ID in this audit. That makes age-band repair plausible.

However, age-band remains disabled because this file is not yet registered as a point-in-time outcome source manifest. Before enabling `age_band`, NWR needs:

- source-family registration
- source timestamp policy
- conflict/missingness report
- point-in-time suitability decision for historical rows

Generated model-preview age receipts are not accepted as the primary outcome source. They may be used only to trace provenance.

## Rare Component Supplement Audit

Local candidates exist for waived rare scoring components:

- `player_stats.csv` has structured passing/rushing/receiving 2-point conversion fields.
- `player_stats.csv` has `special_teams_tds`.
- play-by-play files contain candidate return/fumble-recovery event fields.

None are enabled in Sprint 4D. They need timestamp, component mapping, and forbidden-field quarantine work first.

## Component Waiver Sensitivity

`truth_set_v0_component_waiver_v1` remains acceptable for internal-only benchmark use.

It should not be used for app-facing percentages or calibrated probability claims. To reduce the waiver, register supplemental sources for:

- pass/rush/receiving 2-point conversions
- return yards
- return TDs
- special TDs
- fumble recovery TDs

## Next-Year Outcome Support

`next_year_starter` remains disabled.

The Sprint 4 censoring report shows limited support and censoring risk from the 2022-2024 truth-set window. Re-enabling this outcome requires more seasons, broader legal player-season rows, or an expanded v0 rebuild with a stronger future-window support profile.

## Broader Data Coverage

Broader local sources exist:

- `player_stats.csv` has broad nflverse player-week stat coverage but lacks row-level `source_date` and contains imported fantasy total fields that must be quarantined.
- play-by-play files have broad event-level coverage but include EPA/WP/probability fields and need strict allowlisting.
- usage and snap-share truth-set files have `source_date` and may help future feature snapshots after manifest registration.

No unaudited broad source was ingested into benchmark outputs.

## Sprint 5 Readiness

Sprint 5 calibrated modeling remains blocked.

Open blockers:

- age/DOB source registration before `age_band`
- rare component supplement registration or explicit continued waiver acceptance
- broader non-enriched data coverage
- next-year outcome support
- historical draft-capital registration for `rookie_post_draft`

Recommended next task: register the DynastyProcess/Sleeper identity source for age/DOB and build a supplemental rare-component source manifest before attempting any expanded v0 rebuild or Sprint 5 calibration.
