# Exact Model v4 replay and accuracy report

## Verdict

`YELLOW_NWR_ACCURACY_AUDIT_COMPLETE_PROXY_CONCLUSIONS_REFINED`

The tracked evidence frontier is now explicit and reproducible. Exact player
identity, outcomes, lagged production, and historical age-as-of metadata were
recovered or deterministically regenerated. Exact Model v4 position scores,
lifecycle modifiers, confidence-cap outputs, discipline/safety outputs,
checkpoints, final scores, and ranks were not found in any reachable tracked
history. Therefore full exact replay remains 0 of 5,518 rows across every
position and season.

## Accuracy evidence

The accepted proxy reproduces at Spearman 0.674739 and rank
MAE 21.649511. PYF is 0.681008 /
21.386009; the deterministic two-year baseline is
0.695417 / 20.942733; and the deterministic
three-year baseline is 0.696732 / 20.902501.
Ranking-aligned and valid pooled-score metrics are kept separate in the CSV.

Because exact/proxy overlap is zero, proxy-to-exact score differences, rank
differences, agreement, top-N overlap, reversals, and classification deltas are
not testable. Prior aging conclusions remain directionally useful within the
accepted proxy/OOF evidence, but they are not validated as exact Model v4 causal
effects.

## Error attribution

The largest mechanically measured proxy-error cohorts include: POSITION:WR MAE 29.23; AGE_COHORT:WR_30_PLUS MAE 29.19; RANK_TIER:DEPTH MAE 26.02; TREND:DECLINING MAE 25.94; PRIOR_PRODUCTION:HIGH_MID MAE 24.96; SEASON:2021 MAE 24.58; TWO_YEAR_GAMES:16-23 MAE 23.99; PRIOR_PRODUCTION:LOW_MID MAE 23.58.
Low-games, lifecycle, and older-player slices are reported without converting
proxy residuals into exact-model claims. Historically as-of team change,
retirement, and return-from-injury states remain source-blocked.

## Challengers

- Candidate 0 is the unchanged baseline.
- Candidate 1 is blocked because its exact governed HQ2 definition was not found.
- Candidate 2 is the fixed GAUNTLET_081 2% late-career multiplier. It improves
  overall OOF ranking correlation but fails mandatory leakage/selection,
  uncertainty, pooled-score, productive-veteran, low-games, and coverage gates.
- Candidate 3 was not invented because exact error attribution is unavailable.

Disposition: `NO_ACCURACY_CHALLENGER_ADMITTED`.

No current-board simulation was run because no challenger passed preliminary
gates. Production ranking change: `NONE`. Frozen 2026 change: `NONE`.
