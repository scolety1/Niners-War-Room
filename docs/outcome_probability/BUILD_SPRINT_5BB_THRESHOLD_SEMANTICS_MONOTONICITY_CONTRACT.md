# Sprint 5BB Threshold Semantics And Monotonicity Contract

## Status

Gate label: `THRESHOLD_SEMANTICS_CONTRACT_READY_INTERNAL_ONLY`

This contract locks the semantics of NWR same-year threshold probability heads before any repair, prototype, calibration, or future release work continues.

This is an internal-only contract. It does not release probabilities, bands, model artifacts, app-readable tables, rankings, sorting keys, or app wiring.

## 1. Threshold Semantics

Every threshold head is a "top-N-or-better" event.

The event is true when a player finishes at that positional threshold or better in the target season. Lower finish rank numbers are better.

Examples:

- QB T6 means probability of finishing QB6 or better.
- QB T12 means probability of finishing QB12 or better.
- RB T12 means probability of finishing RB12 or better.
- RB T24 means probability of finishing RB24 or better.
- WR T24 means probability of finishing WR24 or better.
- WR T48 means probability of finishing WR48 or better.
- TE T3 means probability of finishing TE3 or better.
- TE T6 means probability of finishing TE6 or better.

Because these are top-N-or-better events, wider thresholds include narrower thresholds. A player who finishes RB6 or better also finishes RB12 or better, RB24 or better, RB36 or better, and RB48 or better.

## 2. Required Monotonicity Direction

For a single player and position, probabilities must be nondecreasing as the threshold becomes wider.

Required chains:

- QB: `P(T6) <= P(T12) <= P(T18) <= P(T24)`
- RB: `P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`
- WR: `P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`
- TE: `P(T3) <= P(T6) <= P(T12) <= P(T18) <= P(T24)`

This direction is mandatory for any future threshold probability output. It applies before exact display, coarse-band display, app wiring, ranking/sorting review, or model artifact promotion can be considered.

## 3. Explicit Violation Definitions

These adjacent-pair patterns are monotonicity violations:

- `T36 > T48`
- `T24 > T36`
- `T12 > T24`
- `T6 > T12`
- `T3 > T6`

The same rule applies to any position-specific chain. A narrower threshold cannot have a higher probability than a wider threshold for the same player and position.

Examples:

- If `P(RB T36)` is greater than `P(RB T48)`, that is a violation.
- If `P(WR T12)` is greater than `P(WR T24)`, that is a violation.
- If `P(TE T3)` is greater than `P(TE T6)`, that is a violation.

## 4. Connection To Sprint 5BA Findings

Sprint 5BA found that QB and TE passed monotonicity, while RB and WR did not.

Baseline:

- QB monotonicity passed: 0 violations across 74 ready rows.
- TE monotonicity passed: 0 violations across 120 ready rows.
- RB monotonicity failed: 3 violations across 125 ready rows.
- WR monotonicity failed: 15 players with violations across 201 ready rows.

RB violations:

- 3 violations.
- All were `T36 > T48`.

WR adjacent-pair violations:

- 27 adjacent-pair violations across 15 players.
- 12 were `T6 > T12`.
- 15 were `T12 > T24`.

These violations remain release blockers even when the gaps are numerically small. Small contradictions can still confuse users, invalidate exact probability semantics, and create unsafe downstream behavior if exposed through app tables, hidden sort keys, rankings, or decision workflows.

## 5. Release Implications

Exact probability display is blocked unless all of these gates pass:

- All released heads satisfy threshold monotonicity for every player and adjacent threshold pair.
- Calibration gate passes.
- Coverage gate passes.
- Leakage/schema gate passes.
- App-output gate passes.
- No app-readable blocked artifacts exist.

Passing monotonicity alone is not enough for release. Monotonicity is necessary but not sufficient.

Current release state:

- Exact percentages remain blocked.
- Raw independent threshold heads remain blocked from app use.
- Coarse-band candidates remain internal research-only.
- No head is app-ready.

## 6. Coarse-Band Implications

Coarse-band research can continue internal-only if it remains quarantined and non-app-readable.

Coarse-band app display remains blocked unless a separate release gate passes. That future release gate must evaluate at minimum:

- threshold semantics
- monotonicity
- calibration stability
- leakage/schema safety
- coverage policy
- display copy
- absence of hidden sortable values
- absence of app-readable blocked artifacts
- absence of rankings/sorting effects

Coarse bands must not be used as a workaround for failed exact-probability gates.

## 7. App And Ranking Restrictions

Until a future release gate explicitly approves otherwise:

- No threshold probabilities may affect rankings.
- No hidden probability sort keys may be added.
- No app-readable internal probability tables may be created.
- No player-facing percentages may be shown.
- No player-facing bands may be shown.
- No waiver, rookie, or kicker rows may be forced through an incompatible scoring path.
- No waived or unscored players may receive fake or placeholder probabilities.
- Rookies must remain on a separate rookie path.
- Kickers remain not applicable to these veteran threshold heads.
- Internal probability outputs must remain quarantined and local-only.

## 8. Contract For Future Repair Work

Future monotonicity repair work must preserve this contract:

1. The meaning of every threshold remains top-N-or-better.
2. Wider thresholds must have probabilities greater than or equal to narrower thresholds.
3. Repairs must be evaluated against holdout data, not only current-player rows.
4. Repairs must not use forbidden features or label leakage.
5. Repairs must not create app-readable probability tables.
6. Repairs must not create hidden sort values or ranking logic.
7. Repairs must not create promoted model artifacts unless a future sprint explicitly approves artifact promotion.
8. Any repaired outputs remain internal-only until a later release gate explicitly approves display.

Safe future research candidates include:

- post-hoc monotonic clamping as an internal benchmark
- ordinal or cumulative threshold modeling
- shared-head or constrained-threshold modeling
- strictly split-safe isotonic-style monotonic correction
- abstention for unstable positions or heads

None of these repair candidates is app-approved by this contract.

## 9. Final Gate Statement

Final gate label: `THRESHOLD_SEMANTICS_CONTRACT_READY_INTERNAL_ONLY`

Meaning:

- Threshold semantics are formally defined.
- Required monotonicity direction is confirmed.
- Sprint 5BA RB/WR violations are acknowledged as release blockers.
- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band candidates remain internal research-only.
- No head is app-ready.
- No probability output is approved for ranking, sorting, player-facing display, app-readable tables, or decision automation.
