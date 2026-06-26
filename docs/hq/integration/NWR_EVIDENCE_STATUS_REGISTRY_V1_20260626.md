# NWR Evidence Status Registry V1

Date: 2026-06-26

Verdict: GREEN

## Purpose

This registry creates one review-only status layer for the evidence lanes currently present in Master. It is an accountability artifact only. It does not enable model input, training use, ranking changes, hidden sorting, or app decision-page wiring.

Registry CSV:

`docs/hq/integration/evidence_status_registry_v1_20260626.csv`

## Current Policy

- CFBD remains review-only: `model_input_allowed=no`, `training_allowed=no`, `approved_by_human=no`.
- NFL Usage remains review-only: no active model input and no app decision wiring.
- Unified Player Universe remains blocked for app wiring outside its review page.
- RotoWire live collection remains blocked/manual.
- DynastyProcess remains display-only market context.
- Historical proxy drop evidence remains sensitivity-only and is not training truth.
- Outcome columns remain display-only; missing same-position support means `Not enough information`.

## Evidence Lane Summary

| Lane | Status | Allowed now | Blocked now |
| --- | --- | --- | --- |
| CFBD Identity Matching V1 | REVIEW_ONLY | Review/status inspection | Model input, training, human-approved source use |
| NFL Usage Evidence Layer V0 | REVIEW_ONLY | Review page and committed summaries | Decision-page wiring and active model features |
| NFL Usage Promotion Gate V0 | REVIEW_ONLY | Candidate gate review | Promotion into app/model without explicit later gate |
| Historical NFL Usage Panel V0 | REVIEW_ONLY | Manifests and coverage summaries | Raw panel tracking and active model use |
| NFL Usage Target Backtest V0 | REVIEW_ONLY | Historical evaluation review | Training truth or model tuning |
| Unified Player Universe Review V1 | REVIEW_ONLY | Dedicated review route | Dynasty Rankings and Drafting Mode wiring |
| RotoWire Usage Lane | BLOCKED | Candidate report only | Live scraping or source-truth promotion |
| DynastyProcess Market Baseline | GREEN | Display-only market sanity | Model/rank/trade truth |
| Outcome Columns V1 | REVIEW_ONLY | Position-aware display-only context | Horizon probabilities or model features without approved artifact |
| Historical Drop Lists / Proxy Evidence | REVIEW_ONLY | Audit and sensitivity review | Training truth for proxy/LOW evidence |
| League/PDF Availability Source | REVIEW_ONLY | Draftable overlay/source context | Rank/model mutation |
| Sleeper League Truth | GREEN | League-fact refresh/status | Automatic rank/model mutation |
| College/Rookie CFBD Lane Status | REVIEW_ONLY | College identity/production review | Model/training use without human approval |

## Next Gates

1. CFBD human review gate: approve or reject identity rows explicitly before any model or training use.
2. NFL usage model integration gate: separately decide whether any usage features are robust enough for model-candidate status.
3. Unified Universe source-quality gate: clear identity and age blockers before optional app wiring.
4. Evidence review-page gate: keep any evidence status surface read-only and separate from decision pages.
5. League history hard-input gate: import actual draft/trade evidence before upgrading proxy rows.

## Validation Requirements

Phase 2 validation requires:

- CSV load validation.
- Required-column validation.
- Flag validation that no evidence lane enables forbidden model, training, or app decision wiring.
- `git diff --check`.
- No raw/shared/local/runtime files tracked.

## Phase 2 Result

Phase 2 is GREEN if the registry validates and no forbidden YES values are introduced.
