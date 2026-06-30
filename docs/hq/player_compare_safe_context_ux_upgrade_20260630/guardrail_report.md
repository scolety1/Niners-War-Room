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
- No scraped news, rumors, Gmail evidence, or vendor blurbs.
- Missing injury context is not treated as clean health.
- Missing production/usage data is not treated as zero.
- NFLVerse-dependent panels are disabled/spec-only until refresh health is green.

## Notes

The old service name remains `player_compare_decision_service.py` for import
compatibility, but its Player Compare summary output is now a visible-context
readout. Legacy accessors are retained for other imports and return safe
visible-context values.
