# Ordered Sanity Fixture Spec

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: define broad, evidence-backed sanity fixture expectations for later
non-formula tests. This spec intentionally avoids exact numeric score targets.
It does not tune formulas, change generated outputs, mutate app state, or make
trade, cut, keep, draft, buy, sell, defer, target, or start/sit
recommendations.

## How To Use This Spec

This is a fixture specification, not an executable test suite. R22 may convert
only the expectations that are already true and source-safe into non-formula
tests. If an expectation would fail today, it should become a review finding or
formula-candidate note, not a forced code change.

Fixture outcomes should use broad statuses:

- `ready`: current behavior matches the expected broad relationship.
- `review`: current behavior differs or is unclear, but all source rows exist.
- `blocked_missing_input`: a needed player, pick, source path, warning, or
  receipt is missing.
- `not_applicable_yet`: the surface or output is intentionally unavailable.

Allowed fixture types should map to the existing sanity-runner contract:

- `expected_ordering`
- `expected_tier`
- `expected_review_if_disagrees`
- `expected_receipt_explanation`
- `expected_lifecycle`
- `expected_suppression`
- `expected_market_separation`

## Source Reports

- `docs/model_v4/CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md`
- `docs/model_v4/RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md`
- `docs/model_v4/QB_1QB_DISCIPLINE_REPORT_20260605.md`
- `docs/model_v4/TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md`
- `docs/model_v4/VETERAN_AGE_WINDOW_AUDIT_20260605.md`
- `docs/model_v4/YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md`
- `docs/model_v4/ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`
- `docs/model_v4/ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md`
- `docs/model_v4/PICK_VALUE_LADDER_AUDIT_20260605.md`
- `docs/model_v4/PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md`
- `docs/model_v4/EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md`
- `docs/model_v4/DECISION_BOARD_COHERENCE_AUDIT_20260605.md`

## Fixture Guardrails

- Do not assert exact scores, exact rank numbers, or exact score-gap thresholds.
- Do not force formulas to match this spec.
- Do not use ADP, rankings, projections, consensus, market, startup, or
  trade-calculator context as private value.
- Do not turn review labels into final actions.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, generated outputs, mock drafts, or draft state.
- Require source path, source column, lineage, warning, and blocked-use
  receipts for any automated fixture that crosses player, pick, rookie, or
  market-context surfaces.

## Fixture Families

| Family | Purpose | Safe Automation Rule |
|---|---|---|
| Current-player elite tier | Verify elite current players cluster above replacement/depth rows by current-player checkpoint value | Automate only broad relative ordering among named players already present in current-player rows |
| RB/WR balance | Verify elite RB and elite WR anchors both appear in upper current-player tiers | Automate representation and source/warning checks before any strict cross-position order |
| Replacement/depth tier | Verify low-score or blank-score rows remain review/depth context and cannot leapfrog elite anchors without review | Automate fail-closed and warning behavior before exact order |
| QB format caps | Verify 1QB context is visible and replacement/pocket-QB rows do not silently crowd elite RB/WR context | Automate warning/source checks; mark ordering disagreements as review |
| TE no-premium caps | Verify no-premium TE context is visible and replaceable TE rows are not treated as premium-format values | Automate warning/source checks; mark elite-TE disagreements as review |
| Veteran age windows | Verify productive older RB/WR/TE rows expose age, confidence, identity, or no-premium warnings | Automate warning-presence and receipt checks |
| Rookie top cluster | Verify top rookie candidates remain draft-review context with source warnings and blocked use | Automate source/warning/blocked-use checks before order |
| Rookie watchlist | Verify data-incomplete rookies stay watchlist/manual-scout context | Automate evidence-status and blocked-use checks |
| Pick ladder | Verify admitted pick ladder ordering and missing-baseline quarantine | Automate ordinal pick relationships and 5.04 manual-only fail-closed behavior |
| Pick-vs-player neighborhoods | Verify internal neighbors are context only and not trade-equivalence claims | Automate guardrail text and blocked-use checks |
| External assets | Verify external asset rows are review-only context with dynasty asset source disclosure | Automate source/lineage/blocked-use checks |
| Decision Board | Verify aggregate decision rows trace to receipts/components and remain blocked from final actions | Automate counts/source/blocked-use only if generated outputs already exist |

## Proposed Fixtures

| Fixture ID | Type | Players / Assets | Expected Broad Behavior | Receipt Requirement | Severity If Disagrees |
|---|---|---|---|---|---|
| current_elite_wr_cluster | `expected_tier` | Puka Nacua; Jaxon Smith-Njigba; Ja'Marr Chase; Amon-Ra St. Brown | Elite WR anchors should live in an upper current-player review tier and above obvious depth/watchlist rows | Current-player checkpoint source, warning flags, confidence cap, blocked use | review |
| current_elite_rb_cluster | `expected_tier` | Christian McCaffrey; Jonathan Taylor; Bijan Robinson; Jahmyr Gibbs; De'Von Achane | Elite/high RB anchors should live in an upper current-player review tier, with age/source warnings visible where applicable | Current-player checkpoint source, RB age/source warnings, blocked use | review |
| rb_wr_elite_representation | `expected_review_if_disagrees` | Elite RB anchors; elite WR anchors | Upper current-player tiers should contain both RB and WR anchors, not only one position family | Current-player checkpoint source plus RB/WR balance report reference | review |
| replacement_depth_context | `expected_ordering` | Kaleb Johnson; Luke McCaffrey; Darrell Henderson; Devin Singletary | Depth, pressure, or source-gap rows should not outrank elite anchors unless the row is explicitly flagged for human review | Warning flags, manual-review fields, pressure context receipts | high_review |
| legacy_fail_closed_context | `expected_suppression` | Keenan Allen; Darius Slayton | Legacy active-pack values must remain comparison-only; missing current rows fail closed instead of populating primary value | Score envelope/source-routing receipts and legacy warning flags | blocker |
| qb_1qb_context_visibility | `expected_receipt_explanation` | Josh Allen; Jalen Hurts; Patrick Mahomes; Lamar Jackson; Brock Purdy; Joe Burrow; Jayden Daniels | QB rows must disclose 1QB or rushing-age context where applicable; non-elite/capped rows require explicit warning context | Current-player checkpoint source, 1QB warning flags, blocked use | review |
| qb_neighborhood_review | `expected_review_if_disagrees` | Josh Allen; Jalen Hurts; Patrick Mahomes; elite RB/WR anchors | Top QB rows may be high in 1QB, but any crowding of elite RB/WR neighborhoods must be auditable with receipts | Current-player checkpoint source and QB discipline report reference | review |
| te_no_premium_context_visibility | `expected_receipt_explanation` | Trey McBride; Travis Kelce; Brock Bowers; George Kittle; Sam LaPorta; T.J. Hockenson | TE rows must disclose no-premium or source-warning context where applicable; replaceable TE rows must not look like TE-premium values | Current-player checkpoint source, no-premium warning flags, blocked use | review |
| elite_te_exception_review | `expected_review_if_disagrees` | Trey McBride; elite RB/WR anchors | A difference-making TE can be high, but the no-premium framing must be visible and auditable | TE discipline report reference and source/warning receipts | review |
| veteran_age_window_visibility | `expected_receipt_explanation` | Christian McCaffrey; Derrick Henry; Saquon Barkley; Josh Jacobs; Davante Adams; Mike Evans; Cooper Kupp | Aging productive veterans must expose age, confidence, identity/team, or source warnings rather than appearing as certainty-only rows | Current-player checkpoint source, warning flags, confidence cap | review |
| young_player_source_context | `expected_receipt_explanation` | Malik Nabers; Marvin Harrison Jr.; Brian Thomas Jr.; Xavier Worthy; Ladd McConkey | Young/high-upside rows must expose source-gap or limited-evidence context where applicable | Current-player checkpoint source and warning flags | review |
| rookie_top_cluster_context | `expected_tier` | Jeremiyah Love; Makai Lemon; Skyler Bell; Jordyn Tyson; Carnell Tate; Antonio Williams | Top rookie cluster rows should remain rookie-board review context, not final draft options | Rookie draft board source, warning flags, blocked use | review |
| rookie_watchlist_suppression | `expected_suppression` | Daniel Sobkowicz; data-incomplete watchlist rows | Watchlist/data-incomplete rookies must remain manual-scout or data-incomplete context and not masquerade as confident draft options | Rookie board evidence status, warning flags, blocked use | blocker |
| pick_ladder_ordering | `expected_ordering` | 2026 1.03; 2026 1.04; 2026 2.04; 2026 2.08 | Earlier admitted picks should remain above later admitted picks in the internal pick-ladder context | Pick baseline source, source column, blocked use | review |
| pick_504_manual_only | `expected_suppression` | 2026 5.04 | Missing-baseline pick must remain manual-only with no invented exact model score or equivalence | Pick inventory source, warning flags, blocked use | blocker |
| pick_neighbor_guardrails | `expected_market_separation` | 2026 1.03; 2026 1.04; 2026 2.04; 2026 2.08; 2026 5.04 | Nearby model-value rows are internal context only and not one-for-one trade market prices | Pick Decision Lab compare rows and equivalence guardrails | blocker |
| external_asset_source_disclosure | `expected_receipt_explanation` | Trey McBride; Puka Nacua; Jaxon Smith-Njigba; Christian McCaffrey; Josh Allen | External asset context must disclose dynasty asset source, source column, lineage, warnings, and blocked use | Dynasty asset value source and External Asset Review service rows | blocker |
| roster_pressure_context | `expected_receipt_explanation` | Luke McCaffrey; Kaleb Johnson; T.J. Hockenson | Roster pressure rows must be review-only pressure/trade-context prompts, not cut/sell calls | Decision pressure source, warning flags, blocked use | blocker |
| decision_board_traceability | `expected_receipt_explanation` | 2026 1.03; 2026 5.04; Kaleb Johnson; Luke McCaffrey; Jeremiyah Love; Makai Lemon; Ja'Kobi Lane | Decision Board rows must trace to source rows, receipts, components, warnings, allowed use, and blocked use | Decision Board rows, receipts, components, warnings | blocker |

## Broad Ordering Expectations

These are intentionally qualitative:

- Elite current-player anchors should generally sit above replacement/depth,
  blank-score, or manual-only rows unless there is a clearly surfaced source or
  confidence reason.
- Elite RB and elite WR anchors should both be represented in upper tiers.
- Source-gap, identity-review, stale-team, or data-incomplete rows should carry
  warning context whenever they appear near important roster or pick decisions.
- 1QB QB values should be interpretable in 1QB format; superflex assumptions
  must not be implied.
- No-premium TE values should be interpretable in no-premium format; TE-premium
  assumptions must not be implied.
- Rookie-board rows should remain review-only draft context and never final
  pick calls.
- Admitted pick ladder rows should preserve ordinal pick ordering; missing
  baselines should fail closed.
- External asset and market-neighborhood rows should remain context only, never
  offer construction or acquisition instructions.
- Decision Board rows should be aggregate review prompts backed by receipts,
  not action recommendations.

## Warning Expectations

Every automated fixture that crosses a meaningful decision surface should check
for one or more of these warning or guardrail classes:

- `blocked_use` prevents final roster, trade, draft, cut, keep, buy, sell,
  defer, target, or start/sit action.
- `allowed_use` is review-only.
- Source path and source column are present for primary score surfaces.
- `lineage_class` is known and not legacy-only, market-only, or unknown for
  primary values.
- Legacy active-pack scores are comparison-only.
- Market, ADP, league-rank, startup, and trade-calculator context are
  display-only.
- Manual-only or missing-baseline rows do not invent primary scores.
- Confidence caps and source warnings remain visible.

## R22 Automation Guidance

R22 should prefer tests that assert:

- source routing,
- blocked-use and allowed-use fields,
- warning visibility,
- fail-closed blank handling,
- ordinal pick ladder relationships that are already admitted,
- broad fixture statuses that can return `review` instead of failing hard.

R22 should not add tests that:

- require exact score values,
- require exact rank slots,
- force a cross-position formula opinion,
- fail solely because a human disagrees with a model tier,
- mutate generated outputs or app state.

## Non-Goals

- Do not tune formulas from this spec.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, startup, or
  trade-calculator logic to private value.
- Do not convert review labels into final actions.
- Do not use this spec as proof the model is ready for money decisions.
