# Next Gate Recommendations

Verdict: `YELLOW_NEXT_GATES_DEFINED_NO_RUN`

No model experiment should start from this packet. The next gates should build evidence, not activate features.

## Recommended Sequence

1. Build a point-in-time source manifest.
2. Build a feature-window matrix by prediction anchor.
3. Run an identity-safe historical replay dry audit.
4. Run leakage diagnostics by feature family.
5. Run missingness diagnostics.
6. Run label parity or sidecar evidence only where labels are involved.
7. Return to a separate model experiment approval gate only if evidence is green.

## Candidate Later Gates

## Roster / Weekly Roster Replay Gate

Scope:

Prove historical roster status and weekly roster status were known before the prediction anchor.

Stop condition:

If roster status cannot be separated from cutdown survival or post-anchor roster movement, keep it display/review-only.

## Injury / Practice Timing Gate

Scope:

Prove injury report and practice status publication timing at the game-week level.

Stop condition:

If timing is ambiguous or missing injury data could be read as healthy, keep it blocked for experiment use.

## Depth / Snap / Activity Leakage Gate

Scope:

Define prior-week-only usage windows and depth chart as-of rules.

Stop condition:

If target-game or future-week usage can enter the feature window, keep the family blocked.

## Schedule As-Of Gate

Scope:

Define schedule release and update timing without matchup-strength inference.

Stop condition:

If schedule context becomes start/sit, recommendation, playoff odds, trade timing, or matchup value, keep it blocked.

## Drafted-Only Rookie Feature Gate

Scope:

Test draft capital and combine as drafted-only or anchor-specific candidates.

Stop condition:

If the lane needs UDFA truth, CFBD model/training joins, or active rookie probabilities, keep it blocked.

## Availability Denominator Gate

Scope:

Define rostered-game denominator and missingness behavior before any availability field interacts with labels or features.

Stop condition:

If missing availability can be confused with healthy, clean, played, missed, or no-risk, keep it blocked.

## Blocked Families With No Next Experiment Gate

- contract context;
- identity bridge health as a predictive feature;
- games_missed_while_rostered until denominator proof exists;
- CFBD joins;
- UDFA status;
- `ff_rankings`;
- market / ADP / DynastyProcess.
