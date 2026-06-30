# Player Compare Guardrail Report

## Passed By Implementation

- No new model score.
- No compare score.
- No hidden sort.
- No hidden recommendation logic.
- No `Prefer <player>` top-line output.
- No market/ADP/DynastyProcess decision logic.
- No trade valuation.
- No pick valuation.
- No rank/source-truth changes.
- No injury-risk score.
- No medical projection.
- No comeback projection.
- No scraped news, rumors, Gmail evidence, or vendor blurbs.
- Missing injury context is not treated as clean health.
- Missing production/usage data is not treated as zero.
- Missing depth context is not treated as no-role.
- Missing draft capital is not treated as confirmed UDFA.
- Player Compare reads only the tracked NFLVerse player context artifact and
  schema manifest for player-level NFLVerse context.
- `NEED_IDENTITY_REVIEW` rows display only identity-review status, not detailed
  NFLVerse player context.
- Schedule/opponent/bye context is display-only for safe rows and does not
  create matchup advice, projection, hidden sort, trade value, or pick value.

## Notes

The old service name remains `player_compare_decision_service.py` for import
compatibility, but its Player Compare summary output is now a visible-context
readout. Legacy accessors are retained for other imports and return safe
visible-context values.
