# HQ1 Public Source Status Reconciliation V2 Report

Date: 2026-07-08

Branch: `work/lane-hq1-public-source-status-reconciliation-v2-20260708`

Base HQ HEAD: `1eb108e4638e81cda3646bac1c0520b454ba96c1`

## Verdict

`GREEN_HQ1_PUBLIC_SOURCE_STATUS_RECONCILIATION_READY`

## Purpose

This HQ1-only lane reconciles the source statuses preserved in HQ1 Feature Discovery Registry V1. It converts mixed V1 labels such as `public_foundation_review_safe`, `partial_review_only`, `display_or_review_only`, `blocked`, and `blocked_until_admitted` into a clearer planning taxonomy for future source-admission and review-only design lanes.

This lane does not score features, run a feature tournament, compare candidates to prior-year finish, touch HQ2 artifacts, promote any source, or change production model, rankings, UI, runtime, source-truth, default sort, hidden sort, recommendation, verdict, or boost behavior.

## Inputs Read

- `docs/hq/deep_research_upgrades/orchestration_v1_20260708/`
- `docs/hq/deep_research_upgrades/hq1_feature_discovery_registry_v1_20260708/`
- Existing NWR advanced metrics, PFR/NGS, route-field, and display-only gate context under `docs/hq/data_sources/`

## Reconciled Taxonomy

- `GREEN_PUBLIC_FOUNDATION`: public NWR planning foundation with stable identity or team keys, still subject to existing source gates and no new approval from this lane.
- `GREEN_REVIEW_CANDIDATE`: public or source-traced enough for future review-only work after a frozen use gate, but not model/source-truth/UI approved.
- `YELLOW_REVIEW_ONLY`: usable as review context only with caveats, missingness controls, and no production implications.
- `YELLOW_DISPLAY_ONLY`: display/review context only; not rank, sort, source truth, or model input.
- `YELLOW_PARTIAL_COVERAGE`: useful but coverage or historical windows are incomplete or thresholded.
- `YELLOW_SOURCE_PROVENANCE_LIMITED`: source is public or visible but needs reproducible provenance, checksum, field dictionary, or stable access proof.
- `RED_BLOCKED_PROPRIETARY`: commercial/proprietary source or metric not available as an approved public feed.
- `RED_BLOCKED_NO_SAFE_PUBLIC_SOURCE`: no safe public reproducible feed is admitted.
- `RED_IDENTITY_UNSAFE`: identity keys or join method are not safe for approved joins.
- `RED_ROUTE_DENOMINATOR_UNSAFE`: routes-run denominator is absent or unsafe; true YPRR/TPRR cannot be calculated.
- `RED_DO_NOT_USE`: barred from feature/model/source-truth use unless a future explicit approval lane changes status.

## Major Changes From Registry V1

V2 preserves the V1 conclusion that nflverse is the best public foundation, but it makes explicit that no V2 row creates a new model, UI, or source-truth approval.

PFR status is clarified. PFR provenance has been hardened enough to preserve PFR as a future review source family, and PFR rushing/receiving identity has safe review-only subsets. PFR feature signal is still not production-approved. PFR QB passing remains heuristic and warning-gated, not a clean model feature source.

NGS status is clarified as `YELLOW_DISPLAY_ONLY`: public NGS context can be review/display context under existing gate language, but it is not model-approved or source-truth-approved, and thresholded missingness must be visible.

FTN public subset, depth charts, injuries, air-yards surfaces, and participation data remain review-only, partial, or provenance-limited. Commercial FTN remains separately blocked.

PFF, SIS, Sportradar, commercial FTN, public route/YPRR pages, scraped proprietary route surfaces, and true route/YPRR/TPRR feeds remain blocked.

## Route/YPRR/TPRR Status

True YPRR and TPRR cannot be calculated without a full routes-run denominator. Participation primary-receiver route labels are not full routes-run denominators. Snaps are not routes. Team pass attempts are not routes. Route-like proxies can remain in future research queues only when labeled as proxies.

This lane does not admit any route source and does not promote any route-like proxy.

## Future Source Admission Queue

The queue prioritizes route source admission search, public participation continuity, NGS governance hardening, PFR advanced family use gate consolidation, PFR snap counts review, FTN public subset governance, injury/availability current-feed review, depth chart source-change review, air-yards field gate review, and identity hardening for public web surfaces.

Do not start those lanes from this packet. They require separate approval and separate worktrees.

## Final Use Gate

The reconciled source matrix may guide future research planning only. No source is promoted. No model input is approved. No UI/display integration is approved. No source-truth status changes. Route/YPRR/TPRR remain blocked unless separately admitted. PFF and exact PFF Elusive Rating remain blocked. `nwr_elusive_proxy_review_only` remains blocked unless separately approved in a later lane.
