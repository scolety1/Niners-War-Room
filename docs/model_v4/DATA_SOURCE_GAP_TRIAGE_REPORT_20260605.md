# Data/Source Gap Triage Report

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: identify missing source patterns, mismatched identities, stale or
compatibility-only rows, and warning coverage gaps that should be fixed or
audited before formula tuning. This report is evidence only. This report does not import external data, write generated model outputs, change formulas, tune model
weights, or make final trade, cut, keep, draft, buy, sell, defer, target, or
start/sit recommendations.

## Source Reports

- `CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md`
- `TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md`
- `INJURY_STATUS_RISK_AUDIT_20260605.md`
- `YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md`
- `ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`
- `ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md`
- `PICK_VALUE_LADDER_AUDIT_20260605.md`
- `PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md`
- `EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md`
- `DECISION_BOARD_COHERENCE_AUDIT_20260605.md`
- `SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md`

## Triage Buckets

| Bucket | Pattern | Priority | Before-Tuning Action |
|---|---|---|---|
| Current-player missing primary source | Blank `checkpoint_review_score` because required current-player source joins are missing | P0 | Keep fail-closed/manual-only; repair source availability before any formula judgment. |
| Current-player identity/team quarantine | `team_mismatch_or_missing_model_team`, `team_mismatch_or_historical_team`, `identity_review_cap`, or `partial_or_quarantined_join_cap` | P0 | Verify player identity/team mapping and quarantine logic before treating placement as model-quality signal. |
| Rookie source-limited evidence | `watchlist_data_incomplete`, `manual_scout_source_review`, current college/team quarantine, missing market-share, missing recruiting prior, missing age/lifecycle, combine/workout source limits | P0 | Preserve manual scouting state and blocked use; repair source coverage only when output refresh is explicitly allowed. |
| Source-disclosure output gap | Review rows exist but export lacks explicit source path/column/lineage, or canonical review CSV is missing locally | P1 | Add source disclosure in a later non-formula pass if allowed; do not write generated outputs in this mode. |
| Stale compatibility lane | Legacy or compatibility fallback naming can imply target/buy/sell/trade-for or legacy active-pack primary value | P1 | Keep compatibility-only language, quarantine markers, and blocked-use labels visible. |
| Warning coverage gap | Row is review-only but warning rows are not one-for-one with aggregate rows, or warning text is present only in receipts/details | P2 | Make warning access auditable in UI smoke tests; do not infer that missing warning-row count means no risk. |

## Current-Player Gaps

| Pattern | Evidence | Named Rows | Required Handling |
|---|---|---|---|
| Blank primary score | Top/bottom scan found 5 blank current-player primary scores | Jeremiyah Love, Carnell Tate, Jordyn Tyson, Fernando Mendoza, Kenyon Sadiq | Fail closed as manual-only; do not populate from legacy, market, ADP, projection, startup, or trade-calculator context. |
| Missing stats/VORP anchors | Blank rows carry `missing_rotowire_player_stats`, `missing_stats_first_component_evidence`, and `missing_vorp_anchor` | Same five blank-score rows | Source repair before tuning; no replacement formula change from this report. |
| No-historical or shifted-header evidence | Current-player rows carry `no_historical_evidence_for_component` or `shifted_header_expected_player_header_inferred` | Ashton Jeanty, Kaleb Johnson, Luke McCaffrey, Devin Singletary | Treat as source-completeness review; keep confidence caps and warning text visible. |
| First-down/route/snap source gaps | Many current-player rows carry `missing_or_review_route_target_snap_evidence`, `first_down_missing_confidence_cap`, or related partial evidence warnings | Brian Thomas Jr., Marvin Harrison Jr., Malik Nabers, Garrett Wilson, Tank Dell, Hollywood Brown, T.J. Hockenson | Review data completeness before judging football order; do not add licensed route metrics. |

## Identity / Team Mismatch Gaps

| Warning Pattern | Evidence Count / Context | Named Rows | Required Handling |
|---|---|---|---|
| `team_mismatch_or_missing_model_team` | Injury/status audit found 15 rows with team, historical-team, or identity-review text | George Pickens, Jaylen Waddle, Kenneth Walker III, Stefon Diggs, Keenan Allen, David Montgomery, Mike Evans, Cooper Kupp, Daniel Jones | Verify identity and current team mapping before formula review. |
| `team_mismatch_or_historical_team` | Historical-team context appears on aging/status rows | Tyreek Hill, Amari Cooper, Darrell Henderson | Keep `identity_review_cap` and `partial_or_quarantined_join_cap` visible. |
| Repeated or shifted source headers | Warning text includes `repeated_header_rows_removed=1` or shifted-header inference | Amon-Ra St. Brown, Kyren Williams, Ladd McConkey, Tank Dell, Devin Singletary, Luke McCaffrey | Treat as ingestion/source hygiene, not a score-tuning instruction. |

## Rookie Source Gaps

| Pattern | Evidence | Named Rows | Required Handling |
|---|---|---|---|
| Data-incomplete watchlist | 21 rookie rows carry `watchlist_data_incomplete` | Daniel Sobkowicz, Dallen Bentley, Richard Reese, Cade McNamara, Jam Miller, Logan Diggs | Manual scouting only; do not let rows masquerade as confident draft options. |
| Source-limited top cluster | Top-20 rookie rows: 19 of 20 carry `source_limited_evidence_cap`; 19 of 20 carry `third_party_combine_source_limited`; 16 of 20 carry `current_college_team_mismatch_quarantined` | Jeremiyah Love, Makai Lemon, Skyler Bell, Jordyn Tyson, Carnell Tate, Antonio Williams | Top-cluster rows remain review-only scouting prompts, not final draft recommendations. |
| Missing prospect/college evidence | Low-evidence report flags `missing_prospect_or_college_evidence` on 13 of 43 watchlist/data-incomplete rows | Daniel Sobkowicz, Cade McNamara | Source coverage check before rookie-weight discussion. |
| Market context excluded | Rookie reports explicitly carry `market_context_excluded_from_private_value` | All reviewed top-cluster and watchlist rows | Preserve display-only/exclusion framing; do not add market logic to private value. |

## Output / Disclosure Gaps

| Surface | Evidence | Required Handling |
|---|---|---|
| Pick Decision comparison export | `pick_decision_compare_rows.csv` lacks explicit `source_path`, `source_column`, and `lineage_class` fields | Later non-formula source-disclosure improvement only; do not change startup-slot or pick conversion. |
| `2026 5.04` pick context | Missing exact pick baseline, blank `source_review_score`, blank gaps, and `pick_baseline_missing_review` | Manual-only; no invented exact equivalence or pick baseline. |
| External Asset Reviews canonical CSVs | `local_exports/model_v4/external_asset_reviews/latest/external_asset_context_review_rows.csv` and `trade_away_candidate_review_rows.csv` are missing locally | Do not generate outputs here; repaired service rows are acceptable review evidence only. |
| Compatibility fallback trade review CSVs | `trade_review/latest` fallback files still contain stale names such as `trade_for_review_band`, `elite_target_review`, and trade-for allowed-use wording | Compatibility-only; keep neutral app copy and no-offer/no-buy/no-target framing. |
| Decision Board warnings | 105 decision rows, 105 receipts, 315 components, and 54 warning rows | Warning rows are not one-for-one with decision rows; receipts/components/blocked use must remain visible. |

## Legacy / Stale Lane Watchlist

| Lane | Evidence | Required Handling |
|---|---|---|
| Legacy active-pack player scores | Keenan Allen legacy `82.4` and Darius Slayton legacy `78.88` are known sentinels | Legacy active-pack scores must stay comparison-only and never primary/default sort. |
| Stale trade-for naming | Compatibility fallback files can still mention trade-for/target language | Do not interpret as acquisition recommendation; use repaired External Asset Reviews framing. |
| Market or startup context | Multiple reports note market/startup context is display-only or excluded from private value | Do not backfill missing primary scores from market/startup/ranking/projection data. |

## Fix-Before-Tuning Order

1. Confirm fail-closed behavior for blank current-player primary rows.
2. Resolve or document identity/team mismatches before judging player placement.
3. Audit repeated-header and shifted-header ingestion warnings.
4. Preserve rookie watchlist/data-incomplete manual scouting lanes.
5. Add source-path/source-column/lineage disclosure to comparison exports only
   in a later allowed non-formula pass.
6. Refresh or quarantine compatibility fallback naming only when generated-output
   mutation is explicitly allowed.
7. Re-run UI smoke checks for warning visibility and blocked-use disclosure.
8. Only then use the R25 formula-candidate packet as a proposal-only experiment
   plan.

## Non-Goals

- Do not tune formulas from this report.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not import external data or mutate generated outputs.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, or user-entered draft state.
- Do not add ADP, rankings, projections, consensus, market, startup, or
  trade-calculator logic to private value.
- Do not turn review labels into final trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendations.
