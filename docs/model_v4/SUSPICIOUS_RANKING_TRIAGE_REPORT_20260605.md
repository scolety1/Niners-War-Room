# Suspicious Ranking Triage Report

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: consolidate suspicious or easy-to-misread rows from prior refinement
reports into a tomorrow-facing review list. Suspicious means "review this
first," not "wrong," not a final recommendation, and not a prompt to trade,
cut, keep, draft, buy, sell, defer, target, or start/sit any asset.

This report does not tune formulas, does not mutate generated model outputs,
does not mutate active rankings, My Team, War Board, readiness gates, app
promotion, active data packs, or user-entered draft state, and does not add
market, ADP, rankings, projections, consensus, startup, or trade-calculator
logic to private value.

## Source Reports

- `TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md`
- `RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md`
- `QB_1QB_DISCIPLINE_REPORT_20260605.md`
- `TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md`
- `VETERAN_AGE_WINDOW_AUDIT_20260605.md`
- `YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md`
- `INJURY_STATUS_RISK_AUDIT_20260605.md`
- `ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`
- `ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md`
- `PICK_VALUE_LADDER_AUDIT_20260605.md`
- `PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md`
- `EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md`
- `DECISION_BOARD_COHERENCE_AUDIT_20260605.md`
- `NON_FORMULA_SANITY_FIXTURE_TEST_NOTES_20260605.md`

## Likely Data Issue / Source-Missing

Rows in this bucket should be checked for missing source joins, mismatched
identities, stale team fields, or incomplete component evidence before any
formula conversation.

| Review Subject | Evidence | Triage Note |
|---|---|---|
| Jeremiyah Love, Carnell Tate, Jordyn Tyson, Fernando Mendoza, Kenyon Sadiq | Blank current-player primary scores with `missing_rotowire_player_stats`, `missing_stats_first_component_evidence`, and `missing_vorp_anchor` | Must fail closed as manual-only rows until source gaps are resolved. |
| Daniel Sobkowicz | Rookie watchlist row with `watchlist_data_incomplete` and missing prospect/college evidence | Human scouting row only; do not infer a draft action from the low-evidence state. |
| Kaleb Johnson, Luke McCaffrey, Ashton Jeanty, Luther Burden, Hollywood Brown | Low-evidence or shifted-header warnings across current-player and roster-pressure contexts | Review data completeness and component source coverage before treating scores as football conclusions. |
| George Pickens, Jaylen Waddle, Kenneth Walker III, Stefon Diggs, Keenan Allen, David Montgomery, Mike Evans, Tyreek Hill, Cooper Kupp, Amari Cooper, Darrell Henderson, Daniel Jones | Team mismatch, historical-team, or identity-review warnings | Verify identity/team mapping before using row placement as a model-quality judgment. |
| Keenan Allen and Darius Slayton | Legacy active-pack sentinels from prior repair work | Keenan Allen legacy `82.4` and Darius Slayton legacy `78.88` must not leak as primary Player Board values. |

## Source-Disclosure / Output Gap

Rows in this bucket may be reasonable internally, but their output or UI context
needs stronger source disclosure before a money-decision workflow.

| Surface | Evidence | Triage Note |
|---|---|---|
| Pick Decision comparison export | `pick_decision_compare_rows.csv` lacks explicit `source_path`, `source_column`, and `lineage_class` fields | Carry forward as source-disclosure gap; do not treat neighborhoods as one-for-one trade prices. |
| External Asset Reviews | Canonical `external_asset_reviews/latest` CSVs are missing locally, while repaired service rows are available in memory | Do not generate outputs in this mode; audit service readback and source routing only. |
| Compatibility fallback trade review CSVs | Older names such as `trade_for_review_band`, `elite_target_review`, and trade-for allowed-use wording remain in fallback exports | Compatibility-only evidence; keep display-only and blocked-use framing visible. |
| Decision Board aggregate rows | Review-only rows carry receipts/components and blocked-use fields | Keep blocked-use disclosure attached so labels do not become final actions. |

## Formula Candidate / Football-Quality Candidate

This bucket is proposal-only. It identifies rows that may deserve future model
experiments after data/source cleanup and human judgment. Do not patch formulas from this report.

| Candidate Area | Evidence | Tomorrow Question |
|---|---|---|
| No-premium TE ceiling | Trey McBride appears as the highest numeric current-player score; Brock Bowers, Travis Kelce, George Kittle, Sam LaPorta, Mark Andrews, and T.J. Hockenson provide format-context anchors | Is this a valid difference-making TE exception in no-premium format, or does the explanation/cap need future review? |
| 1QB discipline | Josh Allen, Jalen Hurts, and Patrick Mahomes appear in or near high overall bands, while Joe Burrow and Jayden Daniels appear near the bottom with explicit 1QB cap warnings | Is the QB spread intuitive for 1QB dynasty, and are cap explanations visible enough? |
| RB/WR balance | CeeDee Lamb, Justin Jefferson, Garrett Wilson, Malik Nabers, Brian Thomas Jr., Marvin Harrison Jr., Xavier Worthy, and Ladd McConkey appear lower than several RB-heavy top-band rows | Is this cross-position shape football-plausible after source gaps, or a future balance experiment candidate? |
| Aging veteran confidence | Christian McCaffrey, Derrick Henry, Saquon Barkley, Josh Jacobs, Davante Adams, Stefon Diggs, Mike Evans, Tyreek Hill, Cooper Kupp, Amari Cooper, and Keenan Allen carry age/status/identity context | Should future tests isolate age-window behavior after identity/team warnings are cleaned? |
| Young-player evidence sensitivity | Ashton Jeanty, Luther Burden, Brian Thomas Jr., Marvin Harrison Jr., Malik Nabers, Xavier Worthy, and Ladd McConkey have low-evidence or warning-context review prompts | Are the low or middling placements driven by missing evidence, valid caution, or future prior-shape review? |

## UI / Explanation Risk

Rows in this bucket can mislead if the UI or report copy drops the source,
allowed-use, blocked-use, or comparison-only context.

| Surface | Risk | Required Framing |
|---|---|---|
| Pick-vs-player neighborhoods | Early firsts near elite current assets and `2026 2.08` near Josh Jacobs and Chase Brown can look like one-pick trade equivalence | Keep `internal_model_neighbor_only_not_one_for_one_trade_equivalent` and `nearby_model_value_not_trade_equivalence` visible. |
| `2026 5.04` | No exact baseline and blank score gaps can look broken without context | Keep `manual-only`, `no_exact_equivalence_without_pick_baseline`, and fail-closed wording visible. |
| External Asset Reviews | External context rows can look like acquisition targets if stale fallback labels leak | Keep display-only, review-only, no-offer/no-buy/no-target framing visible. |
| Decision Board | Aggregate review labels can be mistaken for trade/cut/keep/draft actions | Keep blocked-use and receipts visible; no final recommendations. |
| Player Board legacy sentinels | Keenan Allen legacy `82.4` and Darius Slayton legacy `78.88` could mislead if legacy active-pack values leak | Keep legacy active-pack scores comparison-only and never primary/default sort. |

## Human-Review-Only

These rows should be part of tomorrow's manual judgment pass. They are not
automated actions.

| Group | Review Subjects | Why Human Review Comes First |
|---|---|---|
| Volatile current players | De'Von Achane, Quentin Johnston, Jerry Jeudy, Tank Dell, Hollywood Brown | Injury/status/role uncertainty needs human priors before money decisions. |
| No-premium TE context | Trey McBride, Brock Bowers, Travis Kelce, George Kittle, Sam LaPorta, Mark Andrews, T.J. Hockenson | Format context can be football-legible only after the user reviews league settings and personal priors. |
| 1QB context | Josh Allen, Jalen Hurts, Patrick Mahomes, Lamar Jackson, Joe Burrow, Jayden Daniels, Brock Purdy, Daniel Jones | QB values need human agreement under 1QB assumptions. |
| Rookie top cluster | Jeremiyah Love, Makai Lemon, Skyler Bell, Jordyn Tyson, Carnell Tate, Antonio Williams | These are scouting prompts, not final draft recommendations. |
| Owned picks and pick context | 2026 1.03, 2026 1.04, 2026 2.04, 2026 2.08, 2026 5.04 | Pick neighborhoods are internal model context, not trade market prices or selection calls. |

## Tomorrow Review Order

1. Confirm source-safety sentinels: Keenan Allen `82.4`, Darius Slayton
   `78.88`, blank primary-score rows, and `2026 5.04` manual-only handling.
2. Review source-missing and identity/team warnings before judging formula
   quality.
3. Check whether External Asset Reviews and Decision Board surfaces preserve
   display-only and blocked-use framing.
4. Judge Trey McBride and broader TE placement under no-premium settings.
5. Judge Josh Allen, Jalen Hurts, Patrick Mahomes, Joe Burrow, and Jayden
   Daniels under 1QB settings.
6. Compare RB/WR top and middle bands with human priors.
7. Review young WR/RB and rookie low-evidence rows with scouting context.
8. Only after those steps, decide whether any formula-candidate packet should
   become a future experiment.

## Non-Goals

- Do not tune formulas from this report.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not mutate generated outputs, active rankings, My Team, War Board,
  readiness gates, app promotion, active data packs, or user-entered draft
  state.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not convert review labels into final trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendations.
