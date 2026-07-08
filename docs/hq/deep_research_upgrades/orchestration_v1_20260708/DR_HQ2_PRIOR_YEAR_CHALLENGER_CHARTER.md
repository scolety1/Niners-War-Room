# Deep Research HQ 2 Charter: Model Failure Autopsy / Prior-Year Baseline Challenger

## Mission

Deep Research HQ 2 owns the immediate model-failure response to the Production Rankings Backtest V1 finding that the current formula-family proxy did not beat the simple prior-year finish baseline overall.

HQ 2 should build a controlled, review-only, source-safe challenger lane around prior-year finish, opportunity, first-down, and role-stability features. It should not build the broad future feature backlog owned by HQ 1.

## Autopsy Facts To Preserve

- Current proxy rank MAE was worse than prior-year finish by about `0.26`.
- Current proxy Spearman was worse by about `0.006`.
- Current proxy startable precision was worse by about `0.1 percentage points`.
- Known miss taxonomy: `424/560`, or `75.7%`, were prior-production-decline false positives.
- Known low-prior-opportunity breakout misses: `136/560`, or `24.3%`.

## HQ 2 Owns

- Immediate model-failure response.
- Prior-year finish baseline challenger.
- Source-safe first-down/opportunity/role-stability feature tournament.
- Miss taxonomy reduction.
- Review-only baseline comparison against Production Rankings Backtest V1 findings.
- Tournament-local feature list limited to immediate challenger candidates.
- Review-only scorecards and miss-taxonomy deltas for the challenger lane.

## HQ 2 Does Not Own

- Broad metric backlog.
- Route/YPRR source discovery.
- General public source map.
- Future feature registry beyond its immediate tournament.
- HQ 1 source status matrix.
- HQ 1 broad candidate formula bank.
- Production model tuning.
- Production formula changes.
- Rankings changes.
- App/UI integration.
- Source promotion.

## Allowed Inputs To Read

- Production Rankings Backtest V1 packet.
- Historical Model v4 Replay Substrate packet.
- Existing source gates for first-down, opportunity, usage, role, NFLVerse, PFR, NGS, and advanced metrics.
- Existing historical fantasy finish foundation docs.
- HQ 1 source maps only as read-only context after they exist.

## Allowed Outputs

- Review-only source-safe challenger feature list.
- Review-only feature tournament plan.
- Review-only tournament script only if explicitly assigned in the future lane.
- Review-only scorecards and miss taxonomy deltas.
- Baseline comparison summary against prior-year finish.

## Forbidden Outputs

- Broad feature discovery registry.
- Route/YPRR/TPRR source expansion.
- Public source map expansion.
- Production formula edits.
- Production rankings edits.
- App/UI edits.
- Runtime service edits.
- Source-truth registry edits.
- Player recommendations, boosts, winners, trade logic, draft logic, or decision logic.

## Parallel Work Rule

HQ 2 may run in parallel with HQ 1 only when it writes to its own review packet folder and avoids HQ 1 source maps, broad registries, broad formula bank, and future tournament registry files.

## Success Criteria

HQ 2 succeeds when it produces a review-only prior-year challenger evaluation that directly addresses the known failure modes without promoting any feature or changing production behavior.
