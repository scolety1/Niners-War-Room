# NWR Full Dynasty + Rookie Unified Board Source Plan

Date: 2026-06-24
Branch: `work/hq-parallel-control`
Planning HEAD: `20e965d7331ba7dfc73043109b07df6411585806`

## Verdict

YELLOW: build preparation is approved, but unified-board implementation should be deferred until source contracts are explicit.

The app has a clean 240-row approved Full Dynasty Rankings source and a strong Draft-Day cockpit, but the approved full dynasty source has 0 rookie/prospect rows. The safe path is to create a documented `unified_player_universe_v1.csv` as a generated review artifact behind a service, not to force rookies into the existing veteran Dynasty Rank.

## Source Inventory

### Full Dynasty Rankings Source

- File: `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- Row count observed: 240
- Columns observed: 58
- Rookie/prospect rows observed: 0 (`is_rookie=0` for all 240 rows)
- Trusted fields: `player_id`, `canonical_player_key`, `player_name`, `normalized_player_name`, `position`, `nfl_team`, `nwr_rank`, `nwr_dynasty_score`, `trust_status`, warning/caveat fields, approved outcome display fields where present.
- Caveat: the file lives under ignored `local_exports`; the app may read it, but this plan must not track or copy it.
- Policy: `nwr_rank` is the approved veteran Dynasty Rank. It must not be overwritten, backfilled, or applied to rookies.

### Rookie/Prospect Sources

Tracked current draft-day sources:

- `docs/draft_day_exports/final_board_v1_20260622/app_props/rookie_hq/rookie_overlay_context.csv`
  - 54 rows, all `asset_type=rookie`.
  - Carries rookie overlay context, final-board references, display-only rookie rank/tier fields, caveats, and manual-review guidance.
- `docs/draft_day_exports/final_board_v1_20260622/app_props/rookie_hq/rookie_pick_window_context.csv`
  - 10 rows, pick-window guidance.
- `docs/draft_day_exports/final_board_v1_20260622/app_props/rookie_hq/rookie_warning_cards.csv`
  - 54 rows, warning and manual-bucket context.
- `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv`
  - 66 rows: 54 rookies, 12 dropped veterans.
- `docs/hq/parallel_lanes/cross_asset_formula_app_repair_20260622/cross_asset_candidate_player_board.csv`
  - 66 rows, derived candidate context.
- `docs/hq/parallel_lanes/historical_cross_asset_tuning_20260622/tuned_candidate_app_overlay.csv`
  - 66 rows, candidate overlay; review-only.
- `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/tuned_v2_current_draft_pool_overlay.csv`
  - 66 rows, tuned candidate overlay; review-only.
- `docs/hq/parallel_lanes/overnight_8h_emergency_20260622/emergency_cross_asset_candidate_player_board.csv`
  - 294 rows, emergency cross-asset context; useful for recovery and identity comparison, not default app truth.
- `docs/model_v4/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv`
  - 89 rows, source snapshot inventory for prospect materials.
- `templates/real_data_inputs/rookie_model/rookie_prospect_inputs.csv`
  - schema template, 0 rows.
- `sample_data/rookie_model_v1/rookie_prospect_inputs.csv`
  - 10 sample rows; not production truth.

Policy: rookie/prospect rows may receive `rookie_rank`, `frozen_baseline_rank`, `candidate_rank`, and review labels, but not fabricated `dynasty_rank`.

### Frozen Baseline Board

- File: `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv`
- Row count: 66
- Composition: 54 rookie rows, 12 dropped-veteran rows.
- Role: baseline/checkpoint only.
- Trusted fields: frozen baseline labels, final board rank/tier as immutable historical checkpoint, position/team context, visible caveats.
- Forbidden use: cannot become the complete source truth for current dynasty universe; cannot be mutated; cannot override `Dynasty Rank`.

### Outcome Context

- Files:
  - `docs/draft_day_exports/final_board_v1_20260622/app_props/outcome_columns/outcome_player_context.csv`
  - `docs/draft_day_exports/final_board_v1_20260622/app_props/outcome_columns/outcome_column_metadata.csv`
  - `docs/draft_day_exports/final_board_v1_20260622/app_props/outcome_columns/OUTCOME_APP_PROP_STATUS.md`
- Row count: 66 context rows.
- Status document: `YELLOW-HOLD`.
- Matched rows: 12.
- Unmatched rows: 54.
- Approved display heads: QB T12, RB T12, RB T24, WR T12, WR T24, WR T36, TE T12.
- Supported positions: QB, RB, WR, TE where the approved source has a matched row.
- Unsupported/missing outcomes: unmatched rows, missing player IDs, missing source rows, position/head combinations that are not approved.
- Policy: display-only. Outcome context cannot create rank, tier, hidden sort, private value, or probability where missing.

### Market Baseline

- Files:
  - `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_market_baseline_context.csv`
  - `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_playerid_crosswalk_audit.csv`
  - `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_nwr_join_coverage.csv`
  - `docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_freshness_report.csv`
- Row count: 330 market rows.
- Trusted fields: DynastyProcess public market context, IDs, join confidence, scrape/freshness metadata.
- Display-only fields: `dp_value_1qb`, `dp_market_rank_1qb`, `dp_ecr_pos`, `dp_age`, `nwr_vs_dp_gap`, market sanity flags.
- Age fallback: allowed only as clearly labeled display fallback; do not replace approved age source truth.
- Policy: display-only market sanity. It cannot drive model inputs, rank, tier, default sort, or source-truth labels.

### League/PDF Free-Agent Pool

- File: `docs/hq/parallel_lanes/overnight_accuracy_max_20260622/free_agent_pdf_page3_draftable_pool.csv`
- Row count: 77.
- Role: LVE roster/PDF page-3 free-agent availability overlay.
- Trusted fields: availability context, PDF free-agent designation, existing IDs where present, source group.
- Caveat: derived from PDF/local processing; not a dynasty-rank source.

### Player Identity/Age Sources

- `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv`
  - 1139 identity audit rows.
  - Coverage surfaces include frozen board, PDF free agents, outcome support rows, DynastyProcess crosswalk rows, candidate overlays, and full dynasty board.
  - Manual review rows: 74.
- `docs/hq/data_sources/identity/player_identity_manual_review_queue_v1.csv`
  - 74 manual-review identity rows.
- `docs/hq/parallel_lanes/age_source_audit_20260622/age_source_coverage.csv`
  - 13 source-coverage rows.
- `docs/hq/parallel_lanes/age_source_audit_20260622/rookie_verified_age_display_20260622.csv`
  - 40 app-facing verified rookie age rows.
- `docs/hq/parallel_lanes/AGE_SOURCE_AUDIT_20260622.md`
  - Current NFL player age best source is normalized nflverse roster display context.
  - Full dynasty age coverage from nflverse context: 224/240.
  - Rookie/prospect age remains partial; missing values must remain `Not enough information`.

## Proposed Layer Model

The source layer inventory is captured in:

`docs/hq/model/NWR_UNIFIED_BOARD_SOURCE_LAYER_INVENTORY_20260624.csv`

Required layers:

1. Veteran Full Dynasty Layer
2. Rookie/Prospect Layer
3. Frozen Baseline Layer
4. PDF Free-Agent Availability Layer
5. Market Baseline Layer
6. Outcome Context Layer
7. Identity/Age Layer

Each layer must keep trusted fields separate from display-only fields. The unified universe service should merge them into one display contract but preserve `rank_source`, `tier_source`, `age_source`, `source_files`, and `caveats`.

## Ranking Policy

1. Rookies/prospects should not receive `Dynasty Rank` unless an approved unified dynasty-rank source exists.
2. Rookies/prospects may receive a separate `Rookie Rank` only from an approved rookie source that already supplies it.
3. Unified display should expose rank fields separately:
   - `dynasty_rank`: approved veteran Full Dynasty rank only.
   - `rookie_rank`: approved rookie/HQ rank only.
   - `frozen_baseline_rank`: immutable frozen checkpoint rank.
   - `candidate_rank`: review-only candidate overlay rank.
   - `unified_display_rank`: derived review display ordering, not source truth.
4. Rows with no comparable rank should sort after rows with trusted or explicit review ranks, grouped by `player_type` and `data_quality_status`.
5. The app must label rank source directly using `rank_source` and `unified_display_rank_source`.
6. `Not enough information` means the approved source contract does not currently provide a reliable value. It is not a negative player signal and must not be treated as zero.
7. Display-only fields include market/ADP/DynastyProcess, outcome probabilities, candidate overlays, frozen baseline rank/tier outside the frozen checkpoint role, age fallbacks, warning cards, and pick-window guidance.

Recommended display sort:

1. `VETERAN` rows by `dynasty_rank`.
2. `ROOKIE`/`PROSPECT` rows by approved `rookie_rank` if present; otherwise `frozen_baseline_rank`; otherwise `candidate_rank`; otherwise review bucket.
3. `PDF_FA` rows after rostered/current universe rows unless explicitly selected.
4. `UNKNOWN` rows last, with manual review.

This sort must be labeled as `unified_display_rank_source=derived_review_order` and must not be model truth.

## Proposed Schema

The schema proposal is captured in:

`docs/hq/model/NWR_UNIFIED_PLAYER_UNIVERSE_PROPOSED_SCHEMA_20260624.csv`

Required fields:

- `player_universe_id`
- `player_id`
- `player_name`
- `normalized_name`
- `position`
- `nfl_team`
- `age`
- `age_source`
- `player_type`
- `availability_status`
- `rank_source`
- `dynasty_rank`
- `rookie_rank`
- `frozen_baseline_rank`
- `candidate_rank`
- `unified_display_rank`
- `unified_display_rank_source`
- `tier`
- `tier_source`
- `outcome_context`
- `outcome_status`
- `market_match_status`
- `dp_1qb_value`
- `dp_market_rank`
- `nwr_vs_market_gap`
- `data_quality_status`
- `manual_review_flag`
- `caveats`
- `source_files`

## App Impact Plan

### Dynasty Rankings

- Eventually change: add a dedicated Unified Player Universe view or source filter that shows veterans plus rookies/prospects with rank-source labels.
- Do not change: default Full Dynasty Rankings should stay the approved 240-row source until unified universe is validated.
- Default fields: player, position, team, age, Dynasty Rank for veterans, rank source, source coverage, caveats.
- Toggle fields: market baseline, outcome context, candidate/frozen rank context, identity/age source details.
- Sorting: default remains veteran Dynasty Rank in Full Dynasty view. Unified view uses derived review order and labels it.

### Drafting Mode Cockpit

- Eventually change: center board can consume a service-provided unified draftable view once validated.
- Do not change: live/mock runtime state, drafted filtering, K/DST default hiding, Refresh Data, and board-first cockpit layout.
- Default fields: player, position, team, age, tier/rank source, current availability, caveat.
- Toggle fields: market, outcome, identity, source provenance.
- Sorting: never by market. Use NWR draft/tier/rank logic or explicitly derived review order.

### Cheat Sheets

- Eventually change: add source labels and allow rookie/prospect coverage from unified service.
- Do not change: tiered board behavior, runtime drafted filtering, K/DST hidden by default.
- Default fields: compact rank/tier/source/caveat fields.
- Toggle fields: market, outcome, candidate/frozen details.
- Sorting: existing overall-first/tiered sort until unified service is approved.

### Live Draft Room

- Eventually change: read unified availability/rank context behind the existing workflow service.
- Do not change: direct route, persistence, trade events, local runtime state.
- Default fields: draft workflow fields and source-labeled player rows.
- Toggle fields: source provenance and display-only market/outcome context.
- Sorting: existing workflow sort unless explicit unified review sort is chosen.

### Player Compare

- Eventually change: allow veteran-vs-rookie comparisons with rank-source caveats.
- Do not change: decision summary must not invent comparable ranks or outcomes.
- Default fields: separate rank source, age source, player type, caveats.
- Toggle fields: outcome/market/identity details.
- Guardrail: comparison summary must state when rank sources are not comparable.

### Trading Lab

- Eventually change: include unified player identity and display-only market context for packages.
- Do not change: market sanity remains display-only and does not become trade verdict truth.
- Default fields: package assets, NWR rank/source labels, market sanity caveat.
- Toggle fields: DP market details and identity join details.

### Post-Draft Mode

- Eventually change: summarize drafted players by unified source layer and rank source.
- Do not change: default to live state and preserve mock/live separation.
- Default fields: drafted list, pick, rank source, data-quality status.
- Toggle fields: source provenance and caveats.

### Settings/Data Health

- Eventually change: add unified universe health checks: duplicate IDs, missing player IDs, missing ages, rookie rank coverage, outcome coverage, market join coverage.
- Do not change: Refresh Data Run Status and existing guardrail checks.
- Default fields: health summary.
- Toggle fields: per-layer row counts and manual-review queue.

### Model Evaluation Harness

- Eventually change: evaluate unified universe only as a data contract, not as a new model formula.
- Do not change: model/rank logic, evaluation targets, label integrity, warning repair.
- Guardrail: no model input promotion for market/ADP/DynastyProcess or display-only fields.

## Risks And Blockers

### P0 Blockers

- Any proposal that overwrites `nwr_rank`/Dynasty Rank for rookies.
- Any proposal that mutates Frozen Final Draft Board V1, `final_board_rank`, tiers, latest files, pinned snapshots, or model logic.
- Any hidden sort using DynastyProcess, ADP, market, outcome probabilities, or vendor data.
- Any raw `local_exports`, `C:\NWR_SHARED_DATA`, vendor, or email body data committed to git.

### P1 Blockers

- Missing approved rookie/prospect rank source for the full rookie universe.
- Partial player ID coverage and 74 manual-review identity rows.
- Partial rookie age coverage; known gaps include KC Concepcion and Brian Thomas caveats from current checkpoint notes.
- Outcome context is only display-approved for matched rows and supported position heads.
- Full dynasty source has 0 rookie/prospect rows, so veterans and rookies are currently different rank universes.

### Source Gaps

- Actual 2026 draft log not imported.
- Actual trade history file not imported.
- Gmail/pre-Sleeper evidence intake is metadata/query only, not parsed truth.
- 2010-2021 drop lists are proxy-only and sensitivity-only.
- 2022-2024 drop rows are inferred/unprotected unless upgraded.

### Duplicate And Misuse Risks

- Same-name rookies or veterans can collide without stable IDs.
- PDF free-agent names may duplicate full dynasty rows.
- Candidate overlays can be mistaken for source-truth ranks.
- Market baseline age and rank can be mistaken for NWR truth if labels are not loud.

## Recommendation

Implementation recommendation: YELLOW, defer direct app consumption until a generated review artifact and service contract exist.

Safest first implementation step:

1. Build a docs-only or ignored generated `unified_player_universe_v1.csv` prototype from the existing layers.
2. Validate row counts, duplicates, identity confidence, age coverage, rank-source labels, and guardrails.
3. Add a service that loads the generated artifact and exposes explicit display contracts.
4. Wire one opt-in app view after data-health checks are GREEN/YELLOW-GREEN.

Create `unified_player_universe_v1.csv`: yes, but only as a generated artifact after a validation lane. Do not hand-edit it and do not treat it as model truth.

App pages should consume it through a service, not directly. The service should enforce rank-source labels, display-only field segregation, default sorting policy, duplicate checks, and guardrail warnings.

Avoid:

- fabricating rookie Dynasty Rank.
- fabricating outcome probabilities.
- using market/ADP/DynastyProcess for default sort or model inputs.
- silently filling age/player IDs from weak joins.
- replacing existing page defaults before the unified service is validated.

## Related Artifacts Created By This Plan

- `docs/hq/model/NWR_UNIFIED_PLAYER_UNIVERSE_PROPOSED_SCHEMA_20260624.csv`
- `docs/hq/model/NWR_UNIFIED_BOARD_SOURCE_LAYER_INVENTORY_20260624.csv`
- `docs/hq/model/NWR_UNIFIED_BOARD_IMPLEMENTATION_BACKLOG_20260624.csv`

## Validation Requirements For Future Implementation

- CSV load validation.
- Required column validation.
- Duplicate `player_universe_id` and duplicate high-confidence `player_id` checks.
- Per-layer row-count checks.
- Rank-source coverage checks.
- Manual-review queue generation.
- Guardrail check that no source-truth/model/rank files are changed.
- Browser smoke on Dynasty Rankings, Drafting Mode, Cheat Sheets, Player Compare, Trading Lab, Post-Draft Mode, and Settings/Data Health.
