# HQ1 Candidate Metric Formula Cards V2.1 Report

Date: 2026-07-08

## Verdict Scope

This packet reconciles the prior local HQ1 Candidate Metric Formula Cards V2 packet against the now-canonical HQ1 Public Source Status Reconciliation V2 packet.

This is registry hardening only. It does not score metrics, run a feature tournament, compare candidates to prior-year finish, duplicate HQ2 work, promote sources, or change production model, rankings, UI, runtime, source-truth, default sort, hidden sort, recommendation, verdict, or boost behavior.

## Inputs Read

- Canonical orchestration packet: `docs/hq/deep_research_upgrades/orchestration_v1_20260708/`
- Canonical HQ1 Feature Discovery Registry V1: `docs/hq/deep_research_upgrades/hq1_feature_discovery_registry_v1_20260708/`
- Canonical HQ1 Public Source Status Reconciliation V2: `docs/hq/deep_research_upgrades/hq1_public_source_status_reconciliation_v2_20260708/`
- Prior local Formula Cards V2 evidence packet: `C:\NWR\Niners-War-Room-hq1-candidate-metric-formula-cards-v2-20260708\docs\hq\deep_research_upgrades\hq1_candidate_metric_formula_cards_v2_20260708/`

The prior local V2 worktree was read as evidence only and was not modified.

## What Changed From V2

V2.1 preserves the 35 candidate metrics from Formula Cards V2 and updates their source-status language to match Source Status V2 taxonomy.

Two testability classifications changed:

- `age_curve_context` moved from parked to `REVIEW_READY_SOURCE_PERSPECTIVE_ONLY` because Source Status V2 classifies rosters as `GREEN_PUBLIC_FOUNDATION`. It still requires a frozen age reference date and missing-age policy before any validation.
- `multi_year_production_trend` moved from review-ready to `PARKED_HQ2_CONTEXT_GATE` because HQ2 now owns active multi-year production stability refinement, `three_year_missingness_aware`, and sparse-history guardrail testing.

No metric was performance-tested. No metric was approved for model use.

## Source Status Effects

- nflverse play-by-play, player stats, team stats, rosters, draft/combine, and schedules/team context remain the strongest public foundations for future review planning.
- Air yards remain `YELLOW_PARTIAL_COVERAGE`, so WOPR and air-yards share remain parked.
- Injuries and active-game denominators remain `YELLOW_PARTIAL_COVERAGE`, so availability-adjusted metrics remain parked.
- PFR snap counts remain `YELLOW_PARTIAL_COVERAGE`, so snap-share metrics remain parked.
- NGS public aggregates remain `YELLOW_DISPLAY_ONLY`, so RYOE and CPOE remain parked.
- PFR QB passing remains `YELLOW_REVIEW_ONLY`, so QB PFR heuristics remain parked and warning-gated.
- Public route/YPRR/TPRR surfaces and true route denominator sources remain blocked.

## Counts

- Metric formula cards: 35
- Changed classifications: 2
- Review-ready from source-status perspective only: 18
- Parked metrics: 17
- Route-dependent metrics: 3

## Route/YPRR/TPRR Status

True YPRR and TPRR remain blocked because no safe full routes-run denominator source is admitted. Participation primary-receiver route labels are not route denominators. Snaps are not routes. Team pass attempts are not routes. Route-like proxies must remain labeled as proxies.

## HQ2-Owned Dependencies

The following families should not be moved into HQ1 scoring lanes while HQ2 is active:

- Multi-year production stability and `three_year_missingness_aware` context.
- Sparse-history and low-games guardrail testing.
- Candidate Formula Shadow V1 or immediate formula-challenger work.
- Prior-year challenger comparisons.
- Miss taxonomy reduction.

HQ1 may preserve these dependencies as registry context only.

## Final Use Gate

Formula Cards V2.1 may guide future research planning only. No metric is production-approved. No source is promoted. No feature is model-approved. No route/YPRR/TPRR source is admitted. Future scoring, source admission, tournament work, or model promotion requires a separate lane.
