# HQ1 Source Receipt Chain Standard V1

## Purpose

This HQ1 lane creates a reusable evidence standard for future NWR source, metric, formula, ranking, and research upgrades.

The operating principle is simple: a useful dashboard does not equal a proven accurate model. NWR should be able to show the board, the inputs, the sources, what is admitted, what is blocked, how to rebuild the result, and how the result can be tested historically without leakage.

This packet creates standards and templates only. It approves no source, promotes no metric, runs no scoring, changes no production behavior, and does not start route recovery, Formula Gauntlet, or HQ2 challenger work.

## Why Receipt Chains Matter

Receipt chains make future research auditable. Before NWR trusts a stat, source, feature, formula, or ranking artifact, the project needs evidence for six questions:

1. Do we actually have the information?
2. Where did it come from?
3. Is the source reliable enough for the intended use?
4. Is the source production/model-use, review-only, display-only, blocked, identity-unsafe, leakage-unsafe, or not enough information?
5. Can the result be reproduced from raw or frozen inputs?
6. Can the metric or ranking be tested historically without future/current leakage?

Without receipts, a field can look useful while still being non-reproducible, identity-unsafe, licensing-unsafe, current-only, or historically leaky.

## What Future Lanes Must Prove

Every future source, metric, ranking, model, or research lane should prove:

- Source identity: source name, provider, URL/path, acquisition method, timestamp, and source owner.
- Source integrity: raw hash, row count, column count, schema, storage path, and version/date.
- Coverage: seasons, weeks, positions, teams, row grain, and missingness behavior.
- Identity safety: canonical player IDs, join keys, join method, collision handling, unmatched rows, and no name-only approved joins.
- Status gate: source status, admission status, licensing status, identity status, leakage status, missingness status, coverage status, and use gate.
- Rebuild path: exact steps, scripts or commands if applicable, inputs, outputs, hashes, and validation tests.
- Historical safety: decision date, as-of availability, no target-season labels as features, and no current-only context backfilled into past decisions.

If any of those proofs are missing, the lane should label the artifact as review-only, display-only, blocked, or not enough information rather than guessing.

## Source And Admission Classification

This packet standardizes the core source status labels in `HQ1_SOURCE_ADMISSION_STATUS_TAXONOMY.csv`.

Important interpretation rules:

- `GREEN_PUBLIC_FOUNDATION` means a public foundation source may support future source-safe work after field-level gates. It does not automatically approve every field for model use.
- `GREEN_REVIEW_CANDIDATE` means the source may be considered for review after receipts, identity checks, and use gates. It is not production-approved.
- `YELLOW_REVIEW_ONLY` and `YELLOW_DISPLAY_ONLY` mean the source can inform planning or display context but cannot become a model input without a later source-admission lane.
- `YELLOW_PARTIAL_COVERAGE` and `YELLOW_SOURCE_PROVENANCE_LIMITED` require coverage/provenance hardening before deeper use.
- `RED_*` statuses block model/source-truth use until a separate lane resolves the blocker.
- `NOT_ENOUGH_INFORMATION` is a positive governance outcome when NWR lacks evidence.

## Leakage Avoidance

Historical research must use a decision-date contract. For target season `N+1`, feature rows must be available after season `N` is complete and before `N+1` current roster, injury, depth chart, market, projection, rank, ADP, outcome, or schedule-derived future information is used as an input.

Common leakage traps:

- current injuries, roles, depth charts, or team context backfilled into old seasons
- outcome labels used as features
- current player identity data used to force uncertain historical joins
- public webpages with retroactive updates and no retrieval timestamp
- market, ADP, projection, ranking, or analyst-derived fields treated as source truth
- display-only or review-only fields silently used as model inputs

Use `HQ1_LEAKAGE_SAFETY_CHECKLIST.md` before any future validation, replay, formula, or tournament lane.

## Reproducibility Standard

Future lanes should preserve enough information for another agent to rebuild the result without guessing:

- raw inputs and hashes
- transformation steps
- normalized outputs and hashes
- row/column/schema checks
- source receipt IDs
- join audits
- missingness and coverage audits
- use gates
- validation tests
- explicit blockers

If a board or formula cannot be rebuilt because upstream receipts are missing, the lane should say so and preserve a blocker, not treat a likely-equivalent file as upstream truth.

## Application To Future Lanes

This standard may be used by future lanes for:

- source admission packets
- NGS/PFR governance
- route/YPRR/TPRR recovery lanes run outside HQ1
- feature tournament design
- HQ2 challenger outputs
- Formula Gauntlet candidates
- current-board rebuild/replay lanes
- rankings/model evidence packets

Using this standard does not promote a source or metric. It only defines the evidence required before promotion can be considered in a separate lane.

## Final Gate

This packet is an evidence standard. It approves no model input, no source-truth field, no formula, no ranking, no UI behavior, no runtime behavior, no default sort, no hidden sort, no recommendation, no verdict, and no boost.
