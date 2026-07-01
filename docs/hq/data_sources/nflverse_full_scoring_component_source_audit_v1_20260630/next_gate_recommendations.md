# Next Gate Recommendations

Recommended next lane: `NFLVerse Full Scoring Component Sidecar Builder V1`.

## Builder Should Do

- Validate admitted source receipts by SHA and row count.
- Emit observed-row component rows for all direct scoring fields.
- Emit explicit zero component rows only from observed source rows with explicit numeric zero values.
- Emit composite `fumbles_lost` and `return_yards` rows only with documented one-time sum rules.
- Keep special/return touchdowns blocked or separately caveated until mapping is approved.
- Preserve all non-label and non-model approval flags.
- Produce a parity handoff that distinguishes observed-row scoring recompute from complete player-week universe scoring.

## Builder Must Not Do

- Do not treat missing player-week source rows as zero.
- Do not use `fantasy_points` or `fantasy_points_ppr`.
- Do not use quarantined efficiency, market, projection, or display-only fields.
- Do not approve label truth, model input, training input, or source truth.
- Do not wire app behavior.

## Parity Validator Follow-Up

After a full observed-row sidecar exists, rerun label parity with explicit sections for:

- direct formula component coverage;
- exact first-down component coverage;
- zero-row evidence;
- missing player-week censoring;
- special/return touchdown caveat;
- label truth guardrail.
