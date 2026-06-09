# Model v4 Feature Build Queue - 2026-05-26

Purpose:
Track the next review-only application/refinement features for Model v4. These features should improve decision quality by exposing opportunity cost, uncertainty, evidence support, and plain-English reasoning. They must not mutate active rankings, My Team, War Board, readiness gates, app promotion, or final recommendations.

Global constraints:
- League: 10-team dynasty, 1QB, non-PPR, rushing/receiving first-down scoring, no TE premium.
- Outputs remain review-only unless explicitly promoted in a later audited phase.
- Market, ADP, rankings, projections, mock drafts, big boards, and consensus cannot drive private football value.
- Missing data remains missing.
- Draft-pick trade provenance remains context-only.
- Similarity/outcome/history layers are display-only context and cannot feed back into rankings.

## Feature 0 - Startup Slot Simulator - Completed

Status: Built.

Existing outputs:
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_review_rows.csv`
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_component_rows.csv`
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_pick_zone_rows.csv`
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_bucket_rows.csv`
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_receipts.csv`
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_warnings.csv`
- `docs/model_v4/STARTUP_SLOT_SIMULATOR_REVIEW.md`

UI:
- Draft Room -> Startup Slot Simulator.

## Feature 1 - Roster Cut Opportunity-Cost Engine

Goal:
For every Niners roster player, show what the team gives up if the player is dropped, using model startup slot and rookie pick equivalents.

Why this is next:
This is the most deadline-relevant feature. It directly answers: "What am I giving up if I drop this guy?"

Inputs:
- Niners roster state review rows
- cut/keep pressure rows
- trade-away candidate rows
- startup slot simulator rows
- rookie pick value baselines
- rookie draft board rows
- current player value rows

Outputs:
- `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv`
- `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_component_rows.csv`
- `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_warnings.csv`
- `docs/model_v4/ROSTER_OPPORTUNITY_COST_ENGINE.md`

Required row fields:
- player_name
- position
- current_model_score
- startup_slot_rank
- rookie_pick_equivalent
- nearest_rookies_above
- nearest_rookies_below
- replacement_options_nearby
- pressure_status
- trade_context_status
- opportunity_cost_label
- warning_flags
- allowed_use
- blocked_use

Labels:
- `expensive_to_cut`
- `cut_only_if_trade_market_dead`
- `replaceable_depth`
- `manual_review_required`
- `injury_or_source_uncertain`
- `rookie_pick_equivalent_uncertain`

UI:
- Add section to June 15 board: `Cut Opportunity Cost`.

Acceptance tests:
- every Niners roster player appears
- no final cut/keep recommendation
- rookie pick equivalents are review-only
- missing pick baseline blocks exact equivalent
- no ADP or market value used as private value

## Feature 2 - Rookie Pick Decision Lab

Goal:
For each owned pick, show the realistic decision set:
- rookies in range
- dropped/current players near that pick by model startup slot
- pick/defer context
- player risk and evidence quality
- manual review questions

Niners picks:
- 1.03
- 1.04
- 2.04
- 2.08
- 5.04

Inputs:
- rookie draft board review rows
- prospect value rows/components
- startup slot simulator rows
- pick value baselines
- pick defer scenario rows
- Niners roster pressure rows
- outcome bucket rows

Outputs:
- `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv`
- `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_component_rows.csv`
- `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_compare_rows.csv`
- `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_warnings.csv`
- `docs/model_v4/ROOKIE_PICK_DECISION_LAB.md`

Labels only, not recommendations:
- `review_candidate_cluster`
- `review_value_gap`
- `review_rookie_vs_veteran`
- `review_defer_context`
- `manual_decision_required`

UI:
- Draft Room -> `Pick Decision Lab`.

Acceptance tests:
- every row is review-only
- no final pick recommendation
- no market leakage
- all Niners picks appear
- missing 5.04 baseline is quarantined if still missing

## Feature 3 - Historical Similarity Engine - Built

Goal:
For every current rookie prospect, find historical rookie profiles from 2021-2025 that are most similar by admitted evidence only.

Why it helps:
Instead of only showing a score, it explains historical profile shape and outcome range, for example: "Round 1/2 RB with moderate production, incomplete athletic data, and receiving context. Historical outcomes were mixed; review role and landing spot before drafting."

Allowed inputs:
- factual NFL draft capital
- college production
- college team share / dominator
- targets / receiving role if available
- RB rushing/receiving role
- workout profile after zero-placeholder repair
- recruiting profile
- age/lifecycle evidence if admitted
- position
- confidence/source warnings
- display-only historical outcome labels

Blocked inputs:
- ADP
- market value
- rankings
- projections
- mock drafts
- big boards
- consensus
- final outcome as model input

Outputs:
- `local_exports/model_v4/historical_similarity/latest/prospect_similarity_rows.csv`
- `local_exports/model_v4/historical_similarity/latest/prospect_similarity_component_rows.csv`
- `local_exports/model_v4/historical_similarity/latest/prospect_similarity_warnings.csv`
- `docs/model_v4/HISTORICAL_SIMILARITY_ENGINE.md`

Required row fields:
- player_name
- position
- model_score
- similarity_profile_bucket
- top_5_similar_historical_players
- similarity_score
- shared_positive_signals
- shared_risk_signals
- historical_outcome_summary
- sample_size_status
- confidence_status
- warning_flags
- allowed_use
- blocked_use

UI:
- Draft Room -> `Historical Comps`.

Acceptance tests:
- no market leakage
- missing outcomes are not misses
- similarity output is review-only
- 2025 outcomes flagged immature
- receipts exist for each similarity component

Build status:
- Service, generator, review CSVs, documentation, tests, and Draft Room `Historical Comps` tab created.
- Outputs remain review-only and do not feed similarity or outcome labels back into formula value.

## Feature 4 - Player Rank Explainer - Built

Goal:
For any rookie or current player, explain why the model ranks them where it does in language a fantasy manager can understand.

Example:
"Skyler Bell is high because production and team share are elite, but his NFL draft capital is weak. This is a model-edge row, not a safe pick."

Inputs:
- prospect value rows/components
- rookie draft board rows
- current player value rows/components
- startup slot rows
- warning rows
- receipt rows

Outputs:
- `local_exports/model_v4/explainers/latest/player_rank_explainer_rows.csv`
- `local_exports/model_v4/explainers/latest/player_rank_explainer_component_rows.csv`
- `local_exports/model_v4/explainers/latest/player_rank_explainer_warnings.csv`
- `docs/model_v4/PLAYER_RANK_EXPLAINER.md`

Plain-English label examples:
- "High draft capital protects the floor."
- "Production is carrying the score more than NFL investment."
- "Great model profile, but source coverage is incomplete."
- "No-premium TE format caps the upside."
- "1QB format caps the QB value."
- "Model edge: unusual ranking, but supported by admitted evidence."
- "Source warning: unusual ranking may be caused by missing data."

UI:
- Add expandable `Why this rank?` panel to Draft Room tables.

Acceptance tests:
- every top 50 rookie has an explanation
- no explanation mentions ADP/consensus as value
- weird rankings have either model-edge or source-warning label
- every explanation has component receipts

Build status:
- Service, generator, review CSVs, documentation, tests, and Draft Room `Why This Rank` tab created.
- Explanations remain review-only and trace back to component rows or warning rows.

## Feature 5 - Source-Risk Heatmap - Built

Goal:
Expose where each player's value is supported by complete evidence and where it is fragile due to missing, partial, source-limited, or quarantined data.

Inputs:
- source coverage matrix
- warning matrix
- prospect value warnings
- current player warnings
- rookie draft warnings
- receipt rows

Outputs:
- `local_exports/model_v4/source_risk_heatmap/latest/source_risk_player_rows.csv`
- `local_exports/model_v4/source_risk_heatmap/latest/source_risk_feature_rows.csv`
- `local_exports/model_v4/source_risk_heatmap/latest/source_risk_summary.csv`
- `docs/model_v4/SOURCE_RISK_HEATMAP.md`

Risk levels:
- `green_complete`
- `yellow_partial`
- `orange_source_limited`
- `red_manual_review`
- `gray_missing`

UI:
- Add heatmap badges beside every player:
  Production / Share / Draft / Athletic / Age / Landing / Injury / Role.

Acceptance tests:
- missing data is not scored as zero
- source-limited data is flagged
- quarantined joins are red/manual
- no market data used

Build status:
- Service, generator, review CSVs, documentation, tests, and Draft Room `Source Risk` tab created.
- Heatmap is review-only and separates missing, partial, source-limited, and manual-review evidence.

## Feature 6 - Model Edge Queue - Built

Goal:
Find players where the model is intentionally weird and explain whether the weirdness is supported by admitted evidence or caused by source risk.

Detect edge cases:
- day-three player ranked unusually high by model
- first-round player ranked unusually low by model
- TE ranked high despite no TE premium
- QB ranked high despite 1QB
- low-confidence player ranked high
- player with strong model score but major source warning
- player with high draft capital but weak production/team share
- player with huge production but bad draft capital

Outputs:
- `local_exports/model_v4/model_edge_queue/latest/model_edge_rows.csv`
- `local_exports/model_v4/model_edge_queue/latest/model_edge_component_rows.csv`
- `local_exports/model_v4/model_edge_queue/latest/model_edge_warnings.csv`
- `docs/model_v4/MODEL_EDGE_QUEUE.md`

Classifications:
- `legitimate_model_edge`
- `source_shape_warning`
- `manual_scout_required`
- `format_discipline_case`
- `do_not_trust_without_review`

Acceptance tests:
- no ADP/consensus used
- every model edge has admitted evidence support or source warning
- all rows are review-only

Build status:
- Service, generator, review CSVs, documentation, tests, and Draft Room `Model Edge Queue` tab created.
- Queue remains review-only and classifies unusual rows as edge, source-shape warning, manual scout, format discipline, or do-not-trust without review.

## Feature 7 - Review-Only Trade Package Builder

Goal:
Help explore model-equivalent trade package shapes without creating final trade recommendations.

Package types:
- player_for_pick
- pick_for_player
- player_plus_pick_for_pick
- two_for_one_consolidation
- trade_down_package
- defer_pick_package

Outputs:
- `local_exports/model_v4/trade_package_builder/latest/trade_package_review_rows.csv`
- `local_exports/model_v4/trade_package_builder/latest/trade_package_component_rows.csv`
- `local_exports/model_v4/trade_package_builder/latest/trade_package_warnings.csv`
- `docs/model_v4/TRADE_PACKAGE_BUILDER.md`

Labels:
- `model_even_review`
- `overpay_review`
- `underpay_review`
- `manual_market_check_required`
- `do_not_send_without_human_review`

Hard rule:
Do not say "make this trade." Use review-package-shape language only.

Blocked:
- ADP
- market rank as private value
- final trade recommendation
- active app mutation
