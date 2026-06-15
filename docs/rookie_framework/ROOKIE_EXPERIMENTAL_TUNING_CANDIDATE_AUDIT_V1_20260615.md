# Rookie Experimental Tuning Candidate Audit v1 - 2026-06-15

## 1. Executive Verdict

This pass ran an experimental rookie-only tuning candidate audit using the expanded 2010-2023 complete-window label pool.

Verdicts:

- Tuning result: YELLOW
- Candidate quality: YELLOW
- Manual draft trust: YELLOW
- Anti-cheat / leakage: GREEN

Best audit-only candidate: `scoring_format_fit_plus`.

No v2 2026 candidate board was created. The best candidate improved 2022-2023 validation year-class star capture without increasing Top 12 or Top 24 bust rate, but it did not improve WR-specific validation capture and it slightly worsened train Top 12 star capture. That is enough for an experimental audit finding, not enough for a manual-use v2 board.

## 2. Scope and Guardrails

Allowed:

- General feature-family weights/gates only.
- Draft capital and position-family proxies.
- Names in diagnostics only.
- Outcome labels for evaluation only.
- 2010-2021 train / 2022-2023 validation.

Blocked:

- Player-specific tuning.
- Player IDs, teams, schools, draft years, names, or known outcomes as scoring features.
- ADP/market/public rankings/projections/trade calculators as private inputs.
- 2024-2025 partial-window rows.
- Production rankings, app/Streamlit wiring, Outcome files, veteran files, probabilities, bands, hidden sort keys, or promoted artifacts.

## 3. Candidate Configurations

Candidate families tested:

- `baseline`: committed expanded baseline, draft capital plus position prior.
- `wr_upside_plus`: general WR mid-first/day-two upside plus.
- `scoring_format_fit_plus`: non-PPR first-down fit proxy with RB/TE day-two/three role-path boost and 1QB discipline.
- `draft_capital_trap_guard`: broad draft-capital trust reduction with general round/position guardrails.
- `balanced_star_bust`: balanced RB/WR/TE role-path boost with mild later-round guard.
- `position_calibrated`: explicit 1QB/TE/RB/WR calibration proxy.

Important limitation: the expanded 2010-2023 pool currently has draft capital, position, identity/display fields, and labels. It does not yet have source-safe structured historical college production, role, route, target earning, athletic, injury, landing spot, or archetype feature families. So this is a candidate audit over coarse proxies, not a full tuning run.

## 4. Baseline vs Best Candidate

Train split: 2010-2021.

| Metric | Baseline | Best Candidate |
|---|---:|---:|
| Top 12 star capture | 53/109, 0.486 | 51/109, 0.468 |
| Top 12 bust rate | 10/144, 0.069 | 12/144, 0.083 |
| Top 24 star capture | 80/109, 0.734 | 79/109, 0.725 |
| Top 24 bust rate | 32/288, 0.111 | 32/288, 0.111 |
| Top 36 star capture | 98/109, 0.899 | 98/109, 0.899 |
| Top 36 bust rate | 71/432, 0.164 | 71/432, 0.164 |

Validation split: 2022-2023.

| Metric | Baseline | Best Candidate |
|---|---:|---:|
| Top 12 star capture | 6/16, 0.375 | 9/16, 0.562 |
| Top 12 bust rate | 6/24, 0.250 | 6/24, 0.250 |
| Top 24 star capture | 10/16, 0.625 | 12/16, 0.750 |
| Top 24 bust rate | 20/48, 0.417 | 20/48, 0.417 |
| Top 36 star capture | 12/16, 0.750 | 12/16, 0.750 |
| Top 36 bust rate | 37/72, 0.514 | 36/72, 0.500 |

Decision: `scoring_format_fit_plus` is the best audit-only candidate, but not approved for board creation.

## 5. WR Star Capture

Validation WR position metrics did not improve:

| WR Metric | Baseline | Best Candidate |
|---|---:|---:|
| Top 12 star capture | 3/4, 0.750 | 3/4, 0.750 |
| Top 12 bust rate | 3/12, 0.250 | 3/12, 0.250 |
| Top 24 star capture | 3/4, 0.750 | 3/4, 0.750 |
| Top 24 bust rate | 10/24, 0.417 | 10/24, 0.417 |

The WR-specific candidate did not pass validation. This suggests that simple draft-capital/position proxy boosts are not enough to solve WR star capture. The next WR improvement attempt needs source-safe structured feature families such as target earning, route/separation evidence, yards per route or equivalent production indicators, explosive play profile, early breakout context, press/YAC/manual flags, and warning visibility.

## 6. Candidate Gate Results

Validation gate rule:

- Top 12 validation star capture must improve.
- Top 24 validation star capture must not decline.
- Top 12 and Top 24 validation bust-rate deltas must be no worse than +0.050.

Candidate decisions:

- `wr_upside_plus`: FAIL, Top 12 validation star capture declined by 1.
- `scoring_format_fit_plus`: PASS, Top 12 +3 stars, Top 24 +2 stars, no Top 12/24 bust-rate increase.
- `draft_capital_trap_guard`: PASS, Top 12 +1 star, Top 24 +1 star, lower Top 12/24 bust rates.
- `balanced_star_bust`: PASS, Top 12 +3 stars, Top 24 +2 stars, no Top 12/24 bust-rate increase.
- `position_calibrated`: FAIL, Top 12 validation star capture declined by 1.

Tie decision: `scoring_format_fit_plus` and `balanced_star_bust` had the same validation star/bust gate result. `scoring_format_fit_plus` is preferred for audit-only reporting because it is narrower and less WR-heavy, and the WR-heavy direction did not improve WR validation capture.

## 7. Diagnostics

Exported diagnostics:

- Candidate missed-star diagnostic rows: 78
- Candidate high-ranked-bust diagnostic rows: 200

Missed-star classifications:

- `feature_availability_gap`: 49
- `position_calibration_issue`: 29

High-ranked-bust classifications:

- `draft_capital_trap`: 102
- `acceptable_risk`: 98

Names appear only in diagnostic exports. No name, player ID, team, school, draft class, or known outcome is used as a scoring feature.

## 8. V2 Board Decision

V2 candidate created: no.

Reasons:

- WR star capture did not improve.
- Best candidate regressed train Top 12 star capture slightly.
- Validation improvement is concentrated in RB/TE scoring-format proxies, not the stated WR priority.
- Expanded historical pool lacks richer source-safe historical feature families needed for a more meaningful WR tuning pass.
- Candidate diagnostics still show many draft-capital traps and feature-availability gaps.

## 9. Anti-Cheat / Leakage Audit

PASS - No player-specific tuning rules.

PASS - No name, player ID, team, school, or draft-year scoring feature.

PASS - Names are used only in diagnostics.

PASS - Outcome labels are used only for evaluation and candidate selection, not feature construction.

PASS - ADP/market/public rankings/projections/trade calculators are not used.

PASS - 2024-2025 partial-window rows are excluded.

PASS - No probabilities, bands, hidden sort keys, promoted artifacts, production rankings, app wiring, Outcome files, veteran files, or private scores were touched.

PASS - No v2 board was created.

## 10. Recommended Next Step

Do not create a v2 board yet.

Recommended next rookie-only task:

Run a historical feature-family availability audit for 2010-2023, focused on source-safe WR/RB/TE/QB pre-draft features that can exist for historical classes without leakage: college production, role/usage, target/rush earning, explosive play indicators, age/breakout proxies, injury/manual flags if source-safe, and position-specific gates. Keep labels evaluation-only and keep ADP/market display-only.
