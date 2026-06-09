# Research Audit Table

This table converts the Phase 6-10 research archive into implementation
dispositions. It is a model-policy document, not scoring code.

Disposition meanings:

- `accept`: implement as a core policy or feature direction.
- `accept_with_lower_confidence`: implement, but keep smaller weights or lower confidence.
- `heuristic_calibration_required`: usable only as a labeled default until LVE history validates it.
- `display_only`: store and show, but do not score directly.
- `reject`: do not implement as a scoring input.
- `stop_and_review`: do not implement until explicitly resolved.

## Audit Table

| id | source_phase | topic | claim_or_rule | disposition | implementation_action | confidence | scoring_impact | notes |
|---|---|---|---|---|---|---|---|---|
| A2-001 | Phase 6, Phase 10 | Veteran value foundation | Veteran value should be driven by current role, usage, projection, and LVE scoring translation instead of generic dynasty market rank. | accept | Make role/projection the core veteran model spine. | high | core scoring | Strong alignment across Phase 6 and Phase 10. |
| A2-002 | Phase 6, Phase 10 | League rank | League rank is not player quality and must not alter `veteran_base_value`, `horizon_retention_score`, or `keeper_score`. | accept | Keep league-rank fields in forced-release exposure and strategy only. | high | no direct scoring | This is a hard architectural rule. |
| A2-003 | Phase 6, Phase 7, Phase 10 | Public market | Public market value is useful as liquidity/trade context, not private LVE value. | accept | Use market only in trade/liquidity layers and cap it when format mismatch is likely. | high | trade layer only | Never blend public rank directly into base value. |
| A2-004 | Phase 9, Phase 10 | Projections vs rankings | Scoring-adjusted projections should outrank generic rankings for custom scoring decisions. | accept | Add projection-based source class and prioritize it above market ranks. | high | core scoring | Rankings remain useful for trade sentiment. |
| A2-005 | Phase 9, Phase 10 | Source hierarchy | Source precedence should be domain-specific: Sleeper for league state, league-rank document for forced-release rules, official injury/transactions for availability. | accept | Encode domain-specific source tiers in docs/schema/UI. | high | confidence/readiness | Do not use a single global source hierarchy. |
| A2-006 | Phase 9, Phase 10 | Missing data | Missing normalized scored features should impute neutral `50`, with confidence penalty rather than hidden score punishment. | accept | Preserve neutral imputation and visible confidence warnings. | high | confidence first | Identity/ownership-critical fields remain blockers. |
| A2-007 | Phase 9, Phase 10 | Critical blockers | Duplicate assets, unresolved pick ownership, missing league-rank file in forced-release mode, and unsupported critical overrides should block decision-ready state. | accept | Enforce as `decision_blocking` warnings. | high | readiness | Score can exist but should not become decision-ready. |
| A2-008 | Phase 9, Phase 10 | Manual overrides | Overrides may change raw inputs, source selection, assumptions, and provenance only; direct final-score overrides are rejected. | accept | Keep override validators forbidding final-score targets. | high | provenance only | Every override needs reason, source, author, timestamp. |
| A2-009 | Phase 6 | QB veteran features | QB veteran value should include start security, passing output, rushing value, passing efficiency, sack avoidance, age archetype, durability, and environment. | accept | Update veteran registry and formulas after Phase B. | medium_high | core scoring | Exact feature weights remain heuristic. |
| A2-010 | Phase 6, Phase 10 | QB suppression | QB should be structurally suppressed in LVE, but with elite exceptions and no rigid universal ceiling. | accept_with_lower_confidence | Implement as soft replacement-aware discount with elite escape hatch. | medium_high | league overlay | Exact penalty size requires calibration. |
| A2-011 | Phase 6 | Mobile QB injury | Do not penalize a QB merely for being mobile; penalize actual missed time, current medical uncertainty, avoidable sacks, and role threat. | accept | Avoid generic `mobile_qb_injury_penalty`. | medium_high | risk/confidence | Rushing decline with age is separate from injury fear. |
| A2-012 | Phase 6 | RB veteran features | RB value should emphasize touch share, high-value touches, goal-line/short-yardage role, no-PPR-adjusted receiving role, creation, first downs, environment, age, injury. | accept | Update veteran registry and formulas after Phase B. | high | core scoring | Workload stays above efficiency. |
| A2-013 | Phase 6 | RB rushing efficiency | RB creation metrics are useful but must not overpower workload and high-value touches. | accept_with_lower_confidence | Keep efficiency secondary and role-tier-aware. | medium | secondary scoring | Avoid YPC-only scoring. |
| A2-014 | Phase 6 | RB raw receptions | Raw RB receptions are display-only in LVE. | display_only | Store for reporting only; score receiving role through routes, targets, yards, first downs. | high | no direct scoring | No-PPR reduces catch-only value. |
| A2-015 | Phase 6 | RB career touches | Career touch/mileage count should not be scored directly. | display_only | Store as context only; express risk through age, current role, injuries. | medium_high | no direct scoring | Prevent double-counting age and injury. |
| A2-016 | Phase 6 | WR veteran features | WR value should emphasize route participation, target share, TPRR, YPRR, chain-moving, role robustness, TD-area usage, environment, age, injury. | accept | Update veteran registry and formulas after Phase B. | high | core scoring | WR/RB depth matters structurally in LVE. |
| A2-017 | Phase 6, Phase 10 | WR first downs | First-down profile is directionally useful in LVE, but should be modest and residual-based if projections already include scoring. | accept_with_lower_confidence | Use as league-fit overlay, not large duplicated core weight. | medium | secondary/overlay | High double-count risk with route, target, and projection inputs. |
| A2-018 | Phase 6 | WR raw receptions | Raw WR receptions should not score directly. | display_only | Store for context only. | high | no direct scoring | Translate through route/target/yardage/FD profile. |
| A2-019 | Phase 6 | TE veteran features | TE value should emphasize route participation, target earning, YPRR, inverse blocking suppression, high-value receiving role, first-down role, age, injury, environment. | accept | Update veteran registry and formulas after Phase B. | medium_high | core scoring | Route role is the key TE filter. |
| A2-020 | Phase 6, Phase 10 | TE suppression | TE should be structurally suppressed in no-premium, but elite route-earning exceptions must exist. | accept_with_lower_confidence | Implement soft no-premium discount with elite escape hatch. | medium_high | league overlay | Avoid hard TE bans. |
| A2-021 | Phase 6 | Generic TE scarcity | Generic TE scarcity should not be scored directly. | reject | Do not implement as scoring feature. | high | no scoring | No-TE-premium LVE makes this especially dangerous. |
| A2-022 | Phase 6 | Stale NFL draft capital | Veteran old NFL draft capital should not score directly after current role is observable. | display_only | Keep only as profile context or thin-sample note. | high | no direct scoring | Current role/performance dominate. |
| A2-023 | Phase 6, Phase 10 | Age curves | Use broad position-specific age bands, not hard cliff ages. | accept | Replace exact cliff logic with bands/risk flags. | high | core/confidence | RB decline earlier; WR later; QB latest; TE outlier-controlled. |
| A2-024 | Phase 6, Phase 10 | Injury handling | Injury scoring must be type-, timing-, and position-sensitive; active uncertainty matters more than stale labels. | accept | Add active-status and recurrence-aware risk/confidence features. | high | scoring/confidence | Lower-body RB/WR/TE and Achilles deserve special caution. |
| A2-025 | Phase 7, Phase 10 | Unified asset scale | One cross-asset scale should compare veterans, rookies, picks, released veterans, and free agents by LVE surplus over replacement and acquisition cost. | accept | Keep unified board architecture. | high | board/ranking | Needs real veteran values before decision use. |
| A2-026 | Phase 7, Phase 10 | Replacement baselines | Use separate `steady_state_replacement` and `declaration_window_replacement` baselines. | stop_and_review | Implement in D1 after veteran model is rebuilt. | high | asset conversion | Critical design change; avoid one global threshold. |
| A2-027 | Phase 7, Phase 10 | Current pick optionality | Current LVE picks are options on rookies, released veterans, and free agents, not rookie-only coupons. | accept | Represent current picks as flexible draft-room option value. | medium_high | asset conversion | Future picks need additional discount/uncertainty. |
| A2-028 | Phase 7, Phase 10 | Future pick discounts | Future-pick discounts are useful but not evidence-backed as one fixed number. | heuristic_calibration_required | Move constants into config with calibration labels. | low_medium | asset conversion | Do not hard-code as final truth. |
| A2-029 | Phase 7, Phase 10 | Two-for-one/package math | Roster-spot cost, package tax, consolidation premium, and liquidity penalty are useful but unsourced exact constants. | heuristic_calibration_required | Keep conservative defaults and label calibration-required. | low | trade math | Test with LVE history. |
| A2-030 | Phase 7, Phase 10 | Package spam | Multiple lesser assets should not automatically equal one elite asset. | accept_with_lower_confidence | Preserve package penalty/consolidation logic with visible heuristic labels. | medium | trade math | Direction is strong; coefficient is heuristic. |
| A2-031 | Phase 8 | Forced-release shadow tax | Forced-release pressure should be modeled as a team-level shadow tax on official top-five assets. | accept | Keep top-five pressure architecture. | high | strategy | League-rank compliance separate from player quality. |
| A2-032 | Phase 8 | Release opportunity cost | Compare each top-five player against the bubble keeper / opportunity cost of the release. | accept | Use private value loss as strategy anchor after real scores exist. | medium_high | strategy | Depends on real keeper values. |
| A2-033 | Phase 8, Phase 10 | Owner behavior | Owner-behavior, reacquisition, and panic/trade urgency coefficients are weakly observable. | display_only | Show as scenario bands/tier guidance, not hard scoring in V1. | low | UI/strategy only | Needs local LVE history. |
| A2-034 | Phase 8 | Reacquisition planning | Release-and-reacquire can be rational if private loss is low and expected acquisition cost is favorable. | accept_with_lower_confidence | Keep as draft-room scenario, not certainty. | medium | strategy | Name-value bidding can break assumptions. |
| A2-035 | Phase 8 | Opponent targets | Opponent release targets should prioritize released RB/WR roles over middling QB/TE unless price collapses or elite exception clears. | accept_with_lower_confidence | Use in League Intel after real scores exist. | medium | strategy | Confidence bands required. |
| A2-036 | Phase 9 | Warning classes | Warnings should separate `data_warning`, `model_warning`, `review_needed`, and `decision_blocking`. | accept | Use explicit readiness UX and validators. | high | readiness/UI | Already partially implemented. |
| A2-037 | Phase 9 | Source catalog | Source catalog should include family, domain, priority, freshness, scoring context, checksum, active flag. | accept | Upgrade schemas in Phase C. | high | provenance | Market/projection sources require scoring context. |
| A2-038 | Phase 9 | Model run metadata | Model run metadata should be generated and include source hashes, override hashes, warnings, and run status. | accept | Extend generated run metadata. | high | provenance/readiness | Do not hand-edit generated outputs. |
| A2-039 | Phase 10 | Generated outputs | Generated outputs should not become hand-edited source-of-truth fixtures. | accept | Commit raw inputs/registries/notes; generate outputs locally. | high | process | Keep `local_exports/` ignored. |
| A2-040 | Phase 10 | First-down double-counting | If projections already include LVE scoring, do not add large independent first-down weights on top. | accept_with_lower_confidence | Use first downs as residual/role confidence unless projection misses them. | medium_high | scoring guardrail | Prevent hidden duplication. |
| A2-041 | Phase 10 | Depth charts | Depth-chart order should be secondary or display-only because many depth charts are unofficial. | accept_with_lower_confidence | Use as context/warning, not primary score. | medium_high | confidence/context | Official injury/transactions outrank it. |
| A2-042 | Phase 10 | Contracts | Contract security matters but is nuanced and should stay a small confidence/risk modifier. | accept_with_lower_confidence | Use as secondary job-security context only. | medium | confidence/context | Avoid guarantee simplification. |
| A2-043 | Phase 10 | Coefficient truth | Almost no exact numeric weights from Phases 6-9 are directly evidence-backed. | accept | Tag every coefficient with provenance class. | high | process | Phase A3 should lock this policy. |
| A2-044 | Phase 10 | Hard gates | Hard QB/TE ceilings and exact age cliffs are too rigid. | reject | Replace with soft penalties and exception gates. | high | scoring guardrail | Supports model fairness and edge cases. |
| A2-045 | Phase 10 | Decision readiness | App is decision-ready only when real model outputs, source freshness, overrides, and warning blockers pass. | accept | Keep readiness gate strict. | high | UX/readiness | Current placeholder pack remains review-only. |

## Immediate Implementation Guidance

Safe before formula rebuild:

- Archive and audit research.
- Add coefficient provenance labels.
- Improve source/readiness language.
- Add policy docs and non-scoring tests.

Wait for veteran-model implementation phases:

- Veteran score formulas.
- Position feature weights.
- Replacement thresholds.
- Asset conversion constants.
- Forced-release candidate formulas.
- Trade package constants.

## Current Controlling Rule

Phase 10 controls all exact coefficients: implement feature direction and
architecture, but label numeric constants as heuristic unless specifically
validated by later calibration.
