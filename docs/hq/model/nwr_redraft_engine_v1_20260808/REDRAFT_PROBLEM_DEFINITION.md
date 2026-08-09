# Redraft Problem Definition

For one explicit league profile and one explicit season, rank players by expected fantasy points
above realistic available replacement after satisfying mandatory, FLEX, SUPERFLEX, and bounded
bench demand. Age has no independent value; it may only enter a governed current-season forecast.

The engine separates projection, scoring, replacement, confidence, and draft-state layers. A
missing forecast is a blocker, never a zero. Dynasty rank, market rank, and rookie long-term value
are not inputs.
