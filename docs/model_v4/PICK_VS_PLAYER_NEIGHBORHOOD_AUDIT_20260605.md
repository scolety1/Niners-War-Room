# Pick-vs-Player Neighborhood Audit

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: review nearby model-value neighborhoods for owned picks, rookies,
current players, and available/context assets, with special attention to
one-for-one trade-equivalence risk. This report is evidence only. It does not change startup-slot conversion, pick conversion, pick baselines, rookie weights, model weights, VORP, replacement formulas, confidence caps, generated outputs, Draft Room state, War Board state, user-entered draft state, or recommendation logic.

## Sources

| Surface | Source Path | Primary Fields | Role |
|---|---|---|---|
| Rookie Pick Decision Lab rows | `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv` | `pick_value_score`, `equivalence_guardrail`, `warning_flags` | Owned-pick review context and guardrails. |
| Pick decision comparison rows | `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_compare_rows.csv` | `asset_score`, `score_gap_to_pick`, `comparison_type`, `asset_context` | Nearby model-value neighborhood rows. |
| Current-player checkpoint rows | `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` | `checkpoint_review_score`, `warning_flags` | Current-player source for internal neighbors. |
| Rookie Draft Board rows | `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv` | `league_format_adjusted_score`, `warning_flags` | Rookie source for rookie candidate and rookie-neighbor rows. |

The comparison export itself currently does **not** include explicit
`source_path`, `source_column`, or `lineage_class` fields. This is a
source-disclosure gap to carry forward, not something changed by this report.
The source routing above is inferred from `comparison_type`, `asset_context`,
and the canonical source map in `REFINEMENT_EVIDENCE_MAP_20260605.md`.

## Neighborhood Summary

| Pick | Pick Score | Rows | Rookie Rows | Current/Internal Rows | Closest Rookie | Closest Current/Internal Neighbor | Equivalence Guardrail | Risk Notes |
|---|---:|---:|---:|---:|---|---|---|---|
| 2026 1.03 | 93.6 | 16 | 8 | 8 | Jeremiyah Love RB (75.3111; gap -18.2889) | Trey McBride TE (87.4776; gap -6.1224) | internal_model_neighbor_only_not_one_for_one_trade_equivalent | elite current asset one-pick risk flagged; blocked-use present; compare export lacks explicit source columns |
| 2026 1.04 | 90.4 | 16 | 8 | 8 | Jeremiyah Love RB (75.3111; gap -15.0889) | Trey McBride TE (87.4776; gap -2.9224) | internal_model_neighbor_only_not_one_for_one_trade_equivalent | elite current asset one-pick risk flagged; blocked-use present; compare export lacks explicit source columns |
| 2026 2.04 | 71.4 | 16 | 8 | 8 | Antonio Williams WR (54.2258; gap -17.1742) | Makai Lemon WR (69.2158; gap -2.1842) | nearby_model_value_not_trade_equivalence | blocked-use present; compare export lacks explicit source columns |
| 2026 2.08 | 58.6 | 16 | 8 | 8 | Ja'Kobi Lane WR (49.2653; gap -9.3347) | Josh Jacobs RB (58.5387; gap -0.0613) | nearby_model_value_not_trade_equivalence | blocked-use present; compare export lacks explicit source columns |
| 2026 5.04 | blank | 8 | 8 | 0 | Eli Raridon TE (33.2702; no pick baseline) | none | no_exact_equivalence_without_pick_baseline | blank gaps because no baseline; blocked-use present; compare export lacks explicit source columns |

## Equivalence Risk Coverage

- Comparison rows reviewed: 72.
- Allowed use on every comparison row:
  `review_only_rookie_pick_decision_lab_not_final_selection`.
- Blocked use on every comparison row:
  `do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation`.
- Rows carrying `elite_current_asset_not_single_pick_trade_equivalent`: 14.
- `2026 1.03` and `2026 1.04` both use
  `internal_model_neighbor_only_not_one_for_one_trade_equivalent`.
- `2026 2.04` and `2026 2.08` both use
  `nearby_model_value_not_trade_equivalence`.
- `2026 5.04` uses `no_exact_equivalence_without_pick_baseline`; all 8 of its
  comparison rows have blank `score_gap_to_pick`.

## Closest Neighborhood Rows

### 2026 1.03

| Type | Asset | Pos | Score | Gap | Context | Trade/Equivalence Note |
|---|---|---|---:|---:|---|---|
| startup_slot_asset | Trey McBride | TE | 87.4776 | -6.1224 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Puka Nacua | WR | 83.0486 | -10.5514 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Jaxon Smith-Njigba | WR | 82.8713 | -10.7287 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Christian McCaffrey | RB | 82.8329 | -10.7671 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Josh Allen | QB | 80.3133 | -13.2867 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Jonathan Taylor | RB | 80.1465 | -13.4535 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |

### 2026 1.04

| Type | Asset | Pos | Score | Gap | Context | Trade/Equivalence Note |
|---|---|---|---:|---:|---|---|
| startup_slot_asset | Trey McBride | TE | 87.4776 | -2.9224 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Puka Nacua | WR | 83.0486 | -7.3514 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Jaxon Smith-Njigba | WR | 82.8713 | -7.5287 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Christian McCaffrey | RB | 82.8329 | -7.5671 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Josh Allen | QB | 80.3133 | -10.0867 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |
| startup_slot_asset | Jonathan Taylor | RB | 80.1465 | -10.2535 | available_or_context_player | Elite/current asset shown by internal model value only; do not treat the pick-equivalent label as a one-pick trade market price. |

### 2026 2.04

| Type | Asset | Pos | Score | Gap | Context | Trade/Equivalence Note |
|---|---|---|---:|---:|---|---|
| startup_slot_asset | Makai Lemon | WR | 69.2158 | -2.1842 | rookie_prospect | Internal model context only; verify trade market separately. |
| startup_slot_asset | Jahmyr Gibbs | RB | 73.9972 | 2.5972 | available_or_context_player | Internal model context only; verify trade market separately. |
| startup_slot_asset | Ja'Marr Chase | WR | 74.1258 | 2.7258 | available_or_context_player | Internal model context only; verify trade market separately. |
| startup_slot_asset | Amon-Ra St. Brown | WR | 68.5918 | -2.8082 | available_or_context_player | Internal model context only; verify trade market separately. |
| startup_slot_asset | Jeremiyah Love | RB | 75.3111 | 3.9111 | rookie_prospect | Internal model context only; verify trade market separately. |
| startup_slot_asset | De'Von Achane | RB | 66.6696 | -4.7304 | current_rostered_player | Internal model context only; verify trade market separately. |

### 2026 2.08

| Type | Asset | Pos | Score | Gap | Context | Trade/Equivalence Note |
|---|---|---|---:|---:|---|---|
| startup_slot_asset | Josh Jacobs | RB | 58.5387 | -0.0613 | available_or_context_player | Internal model context only; verify trade market separately. |
| startup_slot_asset | Chase Brown | RB | 58.2990 | -0.301 | current_rostered_player | Internal model context only; verify trade market separately. |
| startup_slot_asset | Chris Brazzell | WR | 57.7934 | -0.8066 | rookie_prospect | Internal model context only; verify trade market separately. |
| startup_slot_asset | Chris Olave | WR | 59.4933 | 0.8933 | available_or_context_player | Internal model context only; verify trade market separately. |
| startup_slot_asset | Davante Adams | WR | 57.5485 | -1.0515 | available_or_context_player | Internal model context only; verify trade market separately. |
| startup_slot_asset | Nico Collins | WR | 59.7382 | 1.1382 | available_or_context_player | Internal model context only; verify trade market separately. |

### 2026 5.04

| Type | Asset | Pos | Score | Gap | Context | Evidence/Risk Note |
|---|---|---|---:|---:|---|---|
| rookie_candidate | Eli Raridon | TE | 33.2702 | blank | late_watchlist_no_pick_baseline_review | missing evidence; source-limited evidence |
| rookie_candidate | Kadarius Calloway | RB | 33.2623 | blank | late_watchlist_no_pick_baseline_review | missing evidence; thin historical bucket |
| rookie_candidate | Fernando Mendoza | QB | 33.1213 | blank | late_watchlist_no_pick_baseline_review | missing evidence; source-limited evidence |
| rookie_candidate | Justin Joly | TE | 32.7593 | blank | late_watchlist_no_pick_baseline_review | missing evidence; source-limited evidence |
| rookie_candidate | Dominic Richardson | RB | 32.2897 | blank | late_watchlist_no_pick_baseline_review | missing evidence; thin historical bucket |
| rookie_candidate | Cyrus Allen | WR | 31.5753 | blank | late_watchlist_no_pick_baseline_review | missing evidence; source-limited evidence |

## Review Observations

- The early firsts show elite/current assets near the pick neighborhood, but
  the export explicitly warns that those rows are internal model context and
  not one-pick market prices.
- `2026 2.08` has the tightest numeric internal-neighbor gap, with Josh Jacobs
  at -0.0613 and Chase Brown at -0.301. Those are the highest-risk rows for a
  user misunderstanding "nearby model value" as "trade equivalence"; blocked
  use and `nearby_model_value_not_trade_equivalence` must stay visible.
- `2026 5.04` has no startup/current-player neighbor rows and no score gaps,
  which is consistent with the missing baseline quarantine from R14.
- The comparison export should be considered lower-disclosure than the
  envelope-repaired primary surfaces because it lacks explicit source fields.
  A later non-formula cleanup candidate could add source-path columns without
  changing scores.

## Non-Goals

- Do not change startup-slot conversion or pick conversion from this report.
- Do not change pick baselines, rookie weights, model weights, VORP,
  replacement formulas, confidence caps, age curves, or market-gap thresholds.
- Do not mutate generated outputs, Draft Room state, War Board state, active
  rankings, My Team, or user-entered draft state.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert review labels or neighborhoods into trade, cut, keep, draft,
  buy, sell, defer, target, or start/sit recommendations.
