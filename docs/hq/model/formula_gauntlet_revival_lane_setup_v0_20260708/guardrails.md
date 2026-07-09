# Formula Gauntlet Revival Guardrails

These guardrails apply to this setup lane and to any future Formula Gauntlet lane unless explicitly superseded by a separate Master HQ approval.

## Blocked Actions

- No production ranking mutation.
- No default sort mutation.
- No hidden score mutation.
- No source-truth promotion.
- No metric admission.
- No formula activation.
- No app UI formula changes unless explicitly approved in a later lane.
- No use of unadmitted stats as real inputs.
- No backfilled receipts treated as upstream truth.
- No broad formula search in this lane.
- No challenger tournament in this lane.
- No formula weight tuning in this lane.
- No current-board output rewrite.
- No draft board, trade value, market baseline, outcome-label, or model-score mutation.

## Source And Metric Guardrails

- Route, YPRR, TPRR, PFF, SIS, Sportradar, commercial FTN, exact PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked unless separately admitted.
- Public visibility of a stat is not source admission.
- A review-only source may not become model-approved by appearing in a candidate backlog.
- A display-only source may not become a formula input without a source-admission lane.
- A likely-equivalent file or receipt may not be treated as upstream truth.

## Candidate Output Guardrails

Future candidate outputs must:

- Live in review-only artifact folders.
- Carry non-production status labels.
- Avoid production file paths.
- Avoid latest pointers unless a review-only latest pointer is explicitly scoped.
- Never power app rankings, hidden sorts, recommendations, trade logic, draft logic, or model logic.

## Baseline Guardrails

Future comparisons must include:

- Prior-year finish baseline.
- Current-formula-family proxy baseline, if exact current formula replay remains blocked.
- Exact current formula replay baseline only if receipt chain and source gates are complete.
- Position-level and startable/cutline metrics, not only aggregate MAE.

## Leakage Guardrails

- No future-season information in feature rows.
- No current availability backdated into historical decisions.
- No outcome labels as features.
- No market, ADP, projection, rank-like, or display-only fields as private-value inputs unless a future gate explicitly approves their role.
- Missing values must be explicit missingness, not silent zero fill.

## Review Gate

Any future Formula Gauntlet output must stop before promotion. Production promotion requires a separate lane with source admission, receipt coverage, app/runtime review, and explicit human approval.
