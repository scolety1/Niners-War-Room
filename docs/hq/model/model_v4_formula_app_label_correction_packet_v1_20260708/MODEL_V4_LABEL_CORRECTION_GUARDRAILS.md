# Model v4 Label Correction Guardrails

## Hard Guardrails

- Do not promote the board to production-active.
- Do not promote any source to model-use, training-use, source-truth, UI-approved, or production-approved status.
- Do not change `nwr_dynasty_score`.
- Do not change `checkpoint_review_score`.
- Do not change rank outputs.
- Do not change model weights.
- Do not change formula logic.
- Do not change default sort.
- Do not add hidden sort.
- Do not add recommendations, verdicts, boosts, trade logic, draft logic, cut/keep logic, buy/sell logic, defer logic, or start/sit logic.
- Do not write into canonical `local_exports`.
- Do not run tuning.
- Do not run an accuracy benchmark.
- Do not claim historical accuracy.
- Do not claim superiority over prior-year finish.
- Do not reuse current-only source context for historical replay.

## Label-Specific Guardrails

Any corrected label must clearly preserve these facts:

- Exact current-board rebuild is proven.
- Current-board production activation is not approved.
- Historical replay remains blocked.
- Historical accuracy remains unapproved.
- Source gates remain unchanged.
- Human review is required before app-visible implementation.

## Required Implementation-Lane Scans

A future implementation lane must prove:

- No formula files changed unless explicitly approved for labels only.
- No ranking outputs changed.
- No app default sort changed.
- No hidden sort changed.
- No source registry status changed.
- No model approval flags were promoted.
- No production approval wording was added.
- No recommendation logic was added.
- No artifact values changed except explicitly approved status/label fields.
