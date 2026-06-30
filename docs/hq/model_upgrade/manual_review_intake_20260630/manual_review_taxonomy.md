# Manual Review Taxonomy

Use one primary type and one recommended action per manual review item. If an observation has several effects, choose the type/action that best describes the next safe gate.

## Primary Types

`APP_BUG`
: A broken or confusing app behavior that can be repaired without changing ranks, model logic, source truth, draft state, or production outputs.

`UX_DISPLAY`
: A label, caveat, ordering, display, or explanatory issue. These are allowed only as display or review context.

`DATA_GAP`
: A missing, stale, incomplete, or conflicting factual field needed to interpret a row.

`IDENTITY_JOIN`
: A player identity, ID, name collision, source join, or bridge issue.

`SOURCE_POLICY`
: A source approval, admissibility, attribution, licensing, freshness, timing, or allowed-use issue.

`MODEL_TARGET`
: A future target-label or horizon-definition candidate. These rows are planning evidence only.

`MODEL_FEATURE`
: A future feature candidate. These rows are planning evidence only.

`OUTCOME_CONTEXT`
: Outcome V2 horizon, validation, display, blocked-field, or missing-output context.

`INJURY_CONTEXT`
: Factual injury or availability context. This never implies medical projection or injury-risk scoring.

`ROOKIE_CONTEXT`
: Rookie, prospect, UDFA, draft-capital, rookie-outcome, or college-context review.

`MARKET_CONTEXT`
: Market, ADP, DynastyProcess, pick value, trade value, or manager-market context. This is blocked as model input unless a later explicit gate says otherwise.

`RANKING_DISAGREEMENT`
: Human disagreement or suspicious ranking evidence. This does not authorize rank changes.

`HUMAN_PREFERENCE`
: A user preference, risk tolerance, scouting prior, or manual judgment that may guide review but not model training by default.

`BLOCKED`
: A do-not-use item that must not become model input, training truth, rank logic, hidden sort, or recommendation logic.

`NO_ACTION`
: Evidence that was reviewed and should remain unchanged.

## Recommended Actions

`SAFE_APP_PATCH`
: Safe future app patch candidate. It must be isolated to display or review behavior and must not touch protected draft, rank, model, source-truth, or runtime systems.

`SAFE_DISPLAY_CONTEXT`
: Safe display/review context candidate. It can clarify a caveat, missing data reason, or review-only status without becoming a model input.

`MODEL_FEATURE_CANDIDATE`
: Candidate feature evidence for a later model R&D lane only. Requires separate approval before training or production use.

`MODEL_TARGET_CANDIDATE`
: Candidate target/horizon evidence for a later model R&D lane only. Requires separate validation and approval.

`SOURCE_GATE_NEEDED`
: A source, licensing, freshness, approval, or admissibility gate must be opened first.

`IDENTITY_GATE_NEEDED`
: A player-ID or identity bridge gate must be opened first.

`HUMAN_REVIEW_NEEDED`
: Human review must approve, reject, defer, or keep blocked before any downstream action.

`BLOCKED_DO_NOT_USE`
: Hard block. Do not use for rank, model, training, hidden sort, recommendation, trade value, pick value, or source truth.

`REJECT_NO_ACTION`
: Reviewed and rejected or already handled. No implementation lane should be opened from this item.

`DEFER`
: Valid topic, but not safe for this lane or requires a separate owner lane.

## Flag Rules

- `rank_change_allowed` defaults to `false`.
- `model_use_allowed` defaults to `false`.
- `training_allowed` defaults to `false`.
- `display_only_allowed=true` never implies model or training use.
- `human_approval_required=true` when an item requires approve, reject, defer, or keep-blocked judgment.
- Source-gate rows must name the gate and the data needed.
- Blocked rows cannot have `model_use_allowed=true`.
