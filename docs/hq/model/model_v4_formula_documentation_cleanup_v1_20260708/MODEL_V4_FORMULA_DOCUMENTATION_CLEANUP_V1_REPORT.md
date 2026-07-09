# Model v4 Formula Documentation / Cleanup V1 Report

Date: 2026-07-08

Lane: `work/lane-model-v4-formula-documentation-cleanup-v1-20260708`

Canonical base reviewed: `origin/work/hq-parallel-control` at `d0dc3eb5e553558884521100303df3ab03b2f372`

## Verdict

`YELLOW_MODEL_V4_FORMULA_CONTRACT_PARTIAL_WITH_RECEIPT_BLOCKERS`

## Clear Answer

The current Full Dynasty board is best classified as `candidate_review_only_main_display` because the app-visible 240-row board is hash-pinned and displayed by the rankings app, but every inspected row carries `allowed_use = candidate_review_only_not_active_rankings` and `candidate_mode = wr_qb_v2_candidate`. The displayed score column is identifiable as `nwr_dynasty_score`, but the upstream checkpoint/component receipt chain needed to prove or historically replay that score is absent from the local runtime folder.

No separate production-active formula artifact or promotion receipt was found in this lane. The identifiable contract is a review-only Model v4 formula family plus a WR/QB v2 candidate overlay, not a fully admitted production accuracy target.

## Current Board Status

| Question | Answer | Evidence |
| --- | --- | --- |
| Is the current board active production? | No evidence found. | Row-level policy stamp is `candidate_review_only_not_active_rankings`; no production-active pointer or approval receipt found. |
| Is the current board candidate review-only? | Yes. | Current artifact has 240 rows with `candidate_mode = wr_qb_v2_candidate`. |
| Is it app-visible? | Yes. | `app/pages/20_final_board_v1.py` loads rankings through `load_dynasty_rankings()` and displays/sorts app presets from the pinned board. |
| Is there a separate active production formula? | Not identifiable from local evidence. | Current runtime folder only contains `full_player_board_value_review_rows.csv`; expected upstream checkpoint/component receipt files are missing. |
| Is the status stamp stale? | Unknown; no evidence of a later promotion was found. | Older rankings inventory called the current dynasty source approved, but the current row-level artifact and replay substrate both classify it as candidate review-only. |
| Is exact historical replay possible now? | No. | Prior replay substrate reports 0 exact replay rows and blocks on missing current and historical component receipts. |

## Formula Surface Inventory Summary

| Surface | File/Function | Status | Used By App? | Production Eligible? | Replayable? | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Full Dynasty board display | `app/pages/20_final_board_v1.py -> load_dynasty_rankings() -> sort_rankings_frame_by_column()` | `candidate_review_only_main_display` | Yes | No | No | 240 rows; `allowed_use = candidate_review_only_not_active_rankings`; `candidate_mode = wr_qb_v2_candidate`. |
| Current full-player-board builder | `src/services/full_player_board_value_service.py::build_full_player_board_value_rows()` | Review-only builder | Indirect | Not yet | No | Emits `review_only_full_player_board_rankings`; maps `checkpoint_review_score` to `nwr_dynasty_score`. |
| WR/QB v2 candidate overlay | `src/services/model_v4_wr_qb_v2_candidate_service.py::build_wr_qb_v2_candidate()` | Candidate review-only | Yes, through current artifact | No | No | Rewrites score/rank candidate overlay and blocks final/recommendation use. |
| Current value checkpoint | `src/services/model_v4_current_value_checkpoint_service.py::build_current_value_checkpoint()` | Review-only, missing runtime receipts | No current runtime file | Not yet | No | Expected `current_player_value_*` component/receipt files are absent. |
| RB/WR current value | `src/services/model_v4_rb_wr_current_value_service.py` | Review-only component layer | No direct surface | No | Partial proxy only | Weights exist in code; exact component receipts absent. |
| QB/TE current value | `src/services/model_v4_qb_te_current_value_service.py` | Review-only component layer | No direct surface | No | Partial proxy only | Weights exist in code; exact component receipts absent. |
| Statistic Analysis preset | `app/pages/20_final_board_v1.py` plus `docs/hq/rankings/statistic_analysis_v0_20260630` | Display/read-only metadata | Yes | No | Not applicable | Contribution percentages deferred until approved score receipt artifact exists. |
| Market/Outcome/Data Review presets | `app/pages/20_final_board_v1.py` and service enrichments | Display/review-only context | Yes | No | No | Prior docs prohibit hidden sort/rank logic promotion from these context fields. |

Full CSV inventory: `MODEL_V4_RANKING_SURFACE_INVENTORY.csv`

Status map: `MODEL_V4_RANKING_SURFACE_STATUS_MAP.csv`

## Component Registry Summary

| Component | Source | Production Input? | Gate Status | Receipt Exists? | Historical Replayable? | Caveat |
| --- | --- | --- | --- | --- | --- | --- |
| `nwr_dynasty_score` | Current board artifact plus full-board/candidate services | No, not approved | Candidate review-only | Final score exists only | No | Upstream `checkpoint_review_score` receipt chain absent. |
| `nwr_rank` | `_assign_private_ranks()` | No independent input | Candidate review-only | Final rank exists only | No | Rank is derived from score sort. |
| `checkpoint_review_score` | Current value checkpoint service | Review-only | Review-only checkpoint | Missing in runtime | No | Named upstream current file is absent. |
| Position-specific score | RB/WR and QB/TE services | Review-only | Review-only component | Missing in runtime | No | Component rows/receipts absent. |
| Replacement/VORP | Replacement VORP core service | Review-only | Review-only | Missing exact receipts | Partial proxy only | Requires admitted first-down and return scoring receipts. |
| RB weights | RB service | Review-only | Review-only | Missing exact receipts | Partial proxy only | Weights are discoverable, but not historically receipted. |
| WR weights | WR service | Review-only | Review-only | Missing exact receipts | Partial proxy only | Route/YPRR/TPRR style evidence is not historically admitted. |
| QB weights | QB service | Review-only | Review-only | Missing exact receipts | Partial proxy only | Discipline/current role context must be decision-date proven. |
| TE weights | TE service | Review-only | Review-only | Missing exact receipts | Partial proxy only | Route/red-zone evidence not admitted as exact historical input. |
| Lifecycle modifier | Lifecycle service | Review-only | Review-only | Missing exact receipts | No | Current-state age/role context cannot be reused historically. |
| Confidence cap | Confidence service | Review-only | Review-only | Missing exact receipts | No | Missingness/cap receipts absent. |
| WR/QB v2 candidate adjustment | Candidate service | No | Candidate review-only | Final overlay exists only | No | Explicitly not active rankings. |

Full component registry: `MODEL_V4_COMPONENT_REGISTRY.csv`

## Active Formula Contract

Future lanes must treat the currently displayed board as a candidate review-only display artifact until one of the following occurs:

1. A human-approved promotion or label correction explicitly identifies the active formula ID and active artifact.
2. Current component receipts are restored or regenerated under source-admitted gates.
3. A season-by-season decision-date receipt layer exists for historical replay.
4. Tests verify that app display labels, allowed-use stamps, and rank logic agree.

The contract is documented in `MODEL_V4_ACTIVE_FORMULA_CONTRACT.md`.

## Missing Receipts / Checkpoints

Most important blockers:

1. Current value checkpoint rows/receipts: `current_player_value_review_rows.csv`, `current_player_value_component_rows.csv`, `current_player_value_receipts.csv`.
2. Upstream full-board checkpoint file named by the current artifact: `current_player_value_full_board_review_rows.csv`.
3. RB/WR and QB/TE current value component rows/receipts/warnings.
4. Replacement/VORP player/component/receipt rows, including first-down and return scoring source receipts.
5. Lifecycle archetype component/receipt rows.
6. Confidence/missingness receipt rows and warning matrices.
7. WR/QB v2 candidate overlay evidence receipts and reason-code review outputs.
8. Historical season-by-season equivalents for all of the above.

Detailed blocker map: `MODEL_V4_MISSING_COMPONENT_RECEIPTS.md`

## Blocked / Excluded Signals

These signals remain excluded from production accuracy and exact replay unless a later gate admits them:

- `candidate_review_only_not_active_rankings` fields and candidate overlay adjustments.
- Market/ADP/DynastyProcess context, except as display or baseline evidence.
- Outcome V2 and future outcome labels as current formula inputs.
- Injury/availability context without decision-date source receipts.
- NGS/PFR/CFBD advanced fields without explicit model-use gates.
- Route participation, YPRR, TPRR, air yards, red-zone usage, and similar fields where historical source admission and receipts are absent.
- Any current-only roster, role, injury, market, depth-chart, or projection context reused for past decision dates.
- Any display-only, review-only, blocked, identity-unsafe, or leakage-unsafe fields.

## Recommendation

Recommended next lane: `Component receipt backfill/source-admission lane`.

The next lane should restore or regenerate the exact current component receipt chain first, then decide whether the app needs a label/status correction. A true historical replay benchmark remains blocked until the current formula target is approved or corrected and the same component receipts exist for historical decision dates.

Do not run another accuracy benchmark yet. Do not tune formula weights. Do not promote the candidate overlay.
