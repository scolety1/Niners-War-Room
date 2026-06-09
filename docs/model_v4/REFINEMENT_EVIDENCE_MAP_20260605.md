# Refinement Evidence Map

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: map the evidence surfaces used for football-quality review before any
formula tuning. This is not a ranking judgment and does not change formulas,
active data packs, generated outputs, or UI routing.

## Baseline

- Safety baseline: `docs/model_v4/POST_AUDIT_READINESS_HANDOFF_20260531.md`
- Source-routing repair queue: `docs/model_v4/REPAIR_TASK_QUEUE_20260530.md`
- Cleanup queue: `docs/model_v4/POST_AUDIT_CLEANUP_QUEUE_20260531.md`
- Refinement queue: `docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md`

## Canonical Score Sources

| Surface / Use | Source Path | Primary Score Column | Entity Type | Lineage / Layer | Warning Fields | UI Surface | Notes |
|---|---|---|---|---|---|---|---|
| Player Board current-player value | `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` | `checkpoint_review_score` | current NFL player | `review_v4_current_player` via score envelope | `warning_flags`, `confidence_cap`, `confidence_status`, manual-review flags added by Player Board service | `app/pages/05_rankings.py` | Primary Player Board value must not fall back to active-pack `private_score`. |
| Cross-asset dynasty value | `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv` | `dynasty_asset_value_review_score` | current player, rookie, pick, external asset | `review_v4_dynasty_asset` via score envelope | `warning_flags`, `confidence_cap`, `value_source_layer` | shared cross-asset services; Draft Room supporting context; External Asset Reviews | Used for cross-asset context, not one-for-one trade recommendations. |
| Rookie Draft Board | `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv` | `league_format_adjusted_score` | rookie prospect | rookie draft review layer | `warning_flags`, `confidence_cap`, `component_weight_available`, `evidence_status` | `app/pages/06_draft_board.py` | Review-only rookie ranking surface; no final draft call. |
| Rookie pick candidates | `local_exports/model_v4/rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv` | `league_format_adjusted_score`, with `pick_value_gap_review` as context | rookie prospect near a pick | rookie pick candidate layer | `warning_flags`, `candidate_window_band`, `roster_fit_context` | `app/pages/06_draft_board.py`, Decision Board support | Candidate rows are scouting prompts, not draft instructions. |
| Rookie Pick Decision Lab | `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv` | `pick_value_score` | owned rookie pick | review-only pick decision lab | `warning_flags`, `confidence_status`, `equivalence_guardrail` | `app/pages/06_draft_board.py` | Neutral labels only: use/hold/manual review. |
| Pick inventory review | `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv` | `pick_value_review_score` | owned pick | pick review layer | `warning_flags`, `baseline_match_status` | `app/pages/08_june15_review.py`, Decision Board | Pick baselines are locked; inspect only. |
| Pick timing context | `local_exports/model_v4/pick_trade_defer/latest/pick_defer_scenario_review_rows.csv` | `value_delta_review` as context | current/future pick comparison | pick timing context | `warning_flags`, `defer_review_band` | `app/pages/08_june15_review.py` | Timing context is not a defer recommendation. |
| External Asset Reviews | `local_exports/model_v4/external_asset_reviews/latest/external_asset_context_review_rows.csv` | `dynasty_asset_value_review_score` | external current player / asset | external asset review layer, backed by dynasty asset value | `warning_flags`, `confidence_cap`, `lineage_class` | `app/pages/04_trade_central.py`, `app/pages/08_june15_review.py` | Current local generated CSV is missing; services retain compatibility fallback to `local_exports/model_v4/trade_review/latest/trade_for_candidate_review_rows.csv`. Do not generate outputs in this queue. |
| Trade-away / roster pressure context | `local_exports/model_v4/external_asset_reviews/latest/trade_away_candidate_review_rows.csv` | `pressure_score` | Niners roster player | roster pressure + external asset review layer | `warning_flags`, `pressure_band` | Decision Board / human review prep support | Current local generated CSV is missing; compatibility fallback exists at `local_exports/model_v4/trade_review/latest/trade_away_candidate_review_rows.csv`. |
| Decision Board | `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv` | `source_review_score` | decision row | aggregate review board | `warning_flags`, `allowed_use`, `blocked_use` | `app/pages/08_june15_review.py` | Human review organization only; no final calls. |
| Startup Slot Simulator | `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_review_rows.csv` | `model_score` | player, rookie, pick, asset | startup slot context with source disclosure | `warning_flags`, `confidence_cap`, `trust_status`, `equivalence_guardrail` | `app/pages/06_draft_board.py` | Context only; does not create one-for-one trade equivalence. |
| Roster Opportunity Cost | `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv` | `current_model_score` | roster player | opportunity-cost context backed by current/cross-asset review | `warning_flags`, `pick_equivalent_warning`, `pick_baseline_status` | `app/pages/08_june15_review.py` | Review-only opportunity cost; not cut/keep recommendation. |
| Human Decision Review Prep | `local_exports/model_v4/human_decision_review_prep/latest/*.csv` | mixed context fields | review card | aggregate human review prep | `confidence_or_risk_warnings`, `allowed_use`, `blocked_use` | docs/export packet, Decision Board support | Summarizes evidence into human-readable cards. |

## Legacy / Display-Only Context

| Context | Path / Field | Allowed Use | Blocked Use |
|---|---|---|---|
| Legacy active-pack score | `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv::private_score` | display as `legacy_active_pack_score` comparison context only | primary score, default sort, review label, summary tile, private value |
| Market / ADP / ranking / projection context | mixed app data-pack columns and market services | display-only context, warnings, receipts | private value, primary review score, final labels, default sort |
| Historical outcomes / comps | historical rookie and similarity exports | display-only context and audit evidence | hidden ranking feature or formula input unless separately admitted |
| Startup slot context | `startup_slot_simulator/latest/*` | neighborhood context, equivalence guardrail | one-for-one trade conversion |

## Evidence Gaps To Carry Forward

- External Asset Reviews canonical generated CSVs are not present in the current
  local `latest` folder, although compatibility fallback files exist under
  `local_exports/model_v4/trade_review/latest`.
- Several surfaces aggregate multiple sources, so later refinement reports should
  trace from UI row to source row rather than trusting display labels alone.
- This map does not judge whether a score is good football. It only identifies
  where the score and warnings come from.

## Next Refinement Use

- R02 should build the named-player audit roster against this map.
- R03-R17 should use the source paths and warning fields above.
- R25 may propose formula candidates only after evidence reports exist.
