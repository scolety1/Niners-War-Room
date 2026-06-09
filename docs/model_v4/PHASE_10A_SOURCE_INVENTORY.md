# Phase 10A Source Inventory And Raw Freeze

Generated: 2026-05-17T21:00:41Z

## Scope

This is a review-only source freeze for Model v4. It inventories and hash-freezes the source/evidence files currently available across:

- main app repo source exports: `C:\Dev\niners-war-room\local_exports\model_v4\raw_user_exports`
- main app repo processed Model v4 outputs under selected `local_exports/model_v4` folders
- prospect/rookie workspace data: `C:\Users\codex-agent\Documents\New project\data`

No formula files, score files, active app rankings, My Team, War Board, or readiness gates were changed.

## Outputs

- `docs/model_v4/PHASE_10A_SOURCE_INVENTORY.csv`
- `docs/model_v4/PHASE_10A_SOURCE_INVENTORY_ISSUES.csv`
- `docs/model_v4/PHASE_10A_SOURCE_INVENTORY.md`

## Freeze Summary

| Metric | Value |
|---|---:|
| Total inventoried files | 640 |
| Raw files hash-frozen | 502 |
| Processed/generated files recorded | 138 |
| Files allowed for private value after validation | 413 |
| Context/projection/market files excluded from private value | 24 |
| Files without nearby README/MANIFEST | 111 |
| Issues logged | 397 |
| High-severity issues | 10 |
| Medium-severity issues | 310 |


Issue counts are file-level flags, not unique model blockers. The main blocker classes are: outside-main-repo prospect data admission, unclear third-party combine/pro-day license, missing family-level manifests, and private-value exclusions for market/projection/ranking files.

## Source Type Counts

| Value | Files |
|---|---:|
| cfbd_college_data | 177 |
| rotowire_nfl_player_stat_export | 84 |
| fantasypros_historical_advanced_export | 77 |
| rotowire_cfb_or_prospect_data | 77 |
| rotowire_nfl_player_stat_upload | 45 |
| processed_rotowire_intake | 17 |
| kaggle_draft_big_board_dataset | 15 |
| model_v4_processed_or_generated_output | 15 |
| model_v4_review_only_preview_output | 10 |
| processed_stats_first_layer | 10 |
| third_party_combine_pro_day_data | 10 |
| processed_fantasypros_advanced | 8 |
| rotowire_team_context_export | 7 |
| rotowire_first_down_export | 6 |
| rotowire_return_export | 6 |
| rookie_manual_source | 5 |
| rotowire_receiver_alignment_export | 5 |
| rotowire_snap_count_export | 5 |

## Source Stage Counts

| Value | Files |
|---|---:|
| raw | 502 |
| processed | 138 |

## Model Lane Counts

| Value | Files |
|---|---:|
| prospect_college_evidence | 177 |
| historical_nfl_player_evidence | 129 |
| prospect_college_or_landing_context | 77 |
| historical_crosscheck_context | 72 |
| processed_source_index_or_clean_rows | 17 |
| prospect_market_and_identity_context | 15 |
| generated_review_or_source_output | 15 |
| review_only_preview_output_not_source | 10 |
| review_only_stats_first_output | 10 |
| prospect_athletic_context_source_limited | 10 |
| market_context_only | 9 |
| processed_secondary_historical_context | 8 |
| team_environment_context | 7 |
| direct_first_down_scoring_evidence | 6 |
| return_scoring_evidence_staged | 6 |
| quarantine_do_not_import | 5 |
| rookie_intake_staging | 5 |
| route_alignment_context | 5 |
| role_usage_evidence_proxy | 5 |
| target_usage_evidence | 5 |
| te_route_evidence | 5 |
| review_only_candidate_output | 5 |
| review_only_replacement_vorp_output | 5 |
| depth_context_only | 4 |

## Safety Status Counts

| Value | Files |
|---|---:|
| frozen_hash_baseline | 293 |
| outside_main_repo_hash_freeze_only | 262 |
| generated_output | 70 |
| source_limited_license_review_required | 10 |
| quarantined | 5 |

## Raw Freeze Confirmation

Raw files were not modified. Phase 10A establishes a SHA-256 freeze baseline for every inventoried raw/source file. For raw files with prior nearby manifests or README files, provenance is already partially documented. For raw files without a nearby manifest, the byte hash is still recorded, but provenance should be backfilled before formula admission.

Important limitation: a new hash manifest proves the current bytes, not what the original download contained before this phase. Where earlier manifests exist, they can be compared in a later integrity check.

## Source-Lane Decisions

- RotoWire NFL passing/rushing/receiving exports are historical player evidence after validation.
- First-down exports are direct first-down scoring evidence after validation.
- Return exports are staged return-scoring evidence; they should not affect scores until the return scoring lane is explicitly patched.
- Snap counts are role/usage proxy evidence and must remain labeled as proxy evidence.
- Receiver alignment and TE route exports are role/route context where sourced, but must not be generalized into fake route metrics.
- Depth charts, injuries, team context, offensive line ranks, and schedule/team rankings are context only unless a later contract admits specific fields.
- Projections, ADP, rankings, market data, and league-rank context remain excluded from private football value.
- CFBD and RotoWire CFB data are prospect evidence after identity matching and validation.
- Third-party combine/pro-day data remains source-limited until license/source permission is cleared.

## Metadata Patch

The existing RotoWire source-index metadata was updated to recognize the new first-down and return export families:

- first-down exports are classified as `direct_first_down_scoring_evidence` with `scoring_allowed`
- return exports are classified as `return_scoring_evidence_staged` with `review_only`
- `first_downs_upload_validation.csv` is explicitly inactive for intake as an unclassified validation artifact

This is a source-governance/test patch only. It does not change formulas, scoring weights, active rankings, app promotion status, or readiness gates.

## Issues To Resolve Before Formula Admission

| Severity | Issue | Source Type | Path | Next Action |
|---|---|---|---|---|
| high | license_unclear | third_party_combine_pro_day_data | `...ts/New project/data/third_party/nfl_draft_data/processed/combine_dataset_manifest.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `.../Documents/New project/data/third_party/nfl_draft_data/processed/combine_official.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `...t/Documents/New project/data/third_party/nfl_draft_data/processed/combine_pro_day.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `...nts/New project/data/third_party/nfl_draft_data/processed/combine_rookie_coverage.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `...w project/data/third_party/nfl_draft_data/processed/combine_rookie_missing_detail.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `...New project/data/third_party/nfl_draft_data/processed/combine_skill_positions_all.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `...t/Documents/New project/data/third_party/nfl_draft_data/raw/data_combine_official.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `...nt/Documents/New project/data/third_party/nfl_draft_data/raw/data_combine_pro_day.csv` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `...codex-agent/Documents/New project/data/third_party/nfl_draft_data/raw/docs_SCHEMAS.md` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| high | license_unclear | third_party_combine_pro_day_data | `C:/Users/codex-agent/Documents/New project/data/third_party/nfl_draft_data/raw/README.md` | Use only for local research until license/source permission is verified or replace with licensed RotoWire workout exports. |
| medium | raw_manifest_missing_or_not_nearby | research_guidance | `...ts/model_v4/raw_user_exports/deep_research/deep-research-report-26-audit-framework.md` | Backfill a small source README or family-level manifest before formula admission if this source will drive scoring. |
| medium | raw_manifest_missing_or_not_nearby | research_guidance | `...rts/model_v4/raw_user_exports/deep_research/deep-research-report-27-rookie-signals.md` | Backfill a small source README or family-level manifest before formula admission if this source will drive scoring. |
| medium | raw_manifest_missing_or_not_nearby | research_guidance | `...user_exports/deep_research/deep-research-report-28-inline-position-signals-summary.md` | Backfill a small source README or family-level manifest before formula admission if this source will drive scoring. |
| medium | do_not_import_source | fantasypros_historical_advanced_export | `...t_for_recursive_intake/FantasyPros_Fantasy_Football_Advanced_Stats_Report_RB (10).csv` | Keep excluded from formula pipelines unless separately validated and renamed into a canonical source folder. |
| medium | do_not_import_source | fantasypros_historical_advanced_export | `...ot_for_recursive_intake/FantasyPros_Fantasy_Football_Advanced_Stats_Report_TE (9).csv` | Keep excluded from formula pipelines unless separately validated and renamed into a canonical source folder. |
| medium | do_not_import_source | fantasypros_historical_advanced_export | `...ot_for_recursive_intake/FantasyPros_Fantasy_Football_Advanced_Stats_Report_WR (9).csv` | Keep excluded from formula pipelines unless separately validated and renamed into a canonical source folder. |
| medium | do_not_import_source | fantasypros_historical_advanced_export | `...nal_names_from_prior_upload_not_for_recursive_intake/README_DO_NOT_IMPORT_AS_2018.txt` | Keep excluded from formula pipelines unless separately validated and renamed into a canonical source folder. |
| medium | do_not_import_source | fantasypros_historical_advanced_export | `..._names_from_prior_upload_not_for_recursive_intake/README_NOT_FOR_RECURSIVE_INTAKE.txt` | Keep excluded from formula pipelines unless separately validated and renamed into a canonical source folder. |

## Missing Or Unsafe Areas

- Prospect workspace data is hash-frozen from `C:/Users/codex-agent/Documents/New project/data`, but it is outside the main app repo. Phase 10B should either copy/admit it into the main raw freeze area or define an explicit external-root manifest contract.
- Third-party combine/pro-day data has no license file in the downloaded local repository files. Keep it local research only unless license status is verified.
- Several raw source families have no nearby README/MANIFEST. They are hash-frozen here, but should receive family-level source notes before formula admission.
- Market, rankings, ADP, and projection files are present and useful for comparison/audit, but they must stay out of the private football value lane.

## Readiness

Phase 10A is ready to hand off to Phase 10B data canonicalization/intake validation. It is not a formula phase, and it does not make any app promotion or readiness-gate decision.

## Checks Run

- Recomputed every inventory SHA-256 hash and confirmed every listed path exists.
- Ran focused source-index tests: `tests/test_model_v4_rotowire_source_index_service.py`.
- Ran Ruff on the touched source-index service and test file.
- Ran compile checks on the touched source-index service and test file.
