# NWR Rookie-Specific Prediction Bias Study (V1)

**Date:** 2026-09-07 (overnight V4 continuation)
**Scope:** Directive V4 section 8 (a rookie-specific bias study, explicitly separate from the general age/experience study already run 2026-07-21) and informs section 9 (78-rookie admission — this document uses the existing, already-admitted candidate's own real walk-forward evidence rather than building a new artifact).

## 1. Why "rookie" needs its own study, separate from "young"

The prior age-bias audit (`docs/hq/master/nwr_post_v1_completeness_historical_aging_audit_v1_20260721/`) pooled players by age/experience *cohort* and found the opposite of the owner's hypothesis — young cohorts were *over*-predicted relative to actual output, old cohorts *under*-predicted. That cohort mixes rookies with 2nd/3rd/4th-year "young" players, whose projection inputs differ fundamentally (rookies have zero NFL production history; the model leans on college-translation and draft-capital signal instead of NFL trend data). The V4 directive is explicit that this is a distinct question and must be studied on its own, not inferred from the general result.

## 2. Real data used

`docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/WALK_FORWARD_PREDICTIONS.csv` — 796 real rookie-season rows, 2016-2025, leakage-safe walk-forward (each season's rookies predicted using only data available before that season, `training_max_season` one year prior). This is the real evidence base behind the currently **admitted** 78-row 2026 rookie candidate (`EXECUTIVE_VERDICT.md`: `GREEN_GOVERNED_COMBINED_PENDING_INDEPENDENT_ADOPTION_REVIEW`, owner-approved) — not a stale or rejected artifact.

## 3. Real, direct residual-bias measurement (predicted − actual)

| Position | n | mean bias (pred − actual) | mean predicted | mean actual |
|---|---:|---:|---:|---:|
| ALL | 796 | **−16.70** | 36.33 | 53.04 |
| QB | 119 | −12.66 | 53.61 | 66.27 |
| RB | 215 | −17.70 | 44.65 | 62.35 |
| TE | 141 | −16.85 | 18.33 | 35.18 |
| WR | 321 | −17.47 | 32.27 | 49.74 |

By draft round (rounds 1-7):

| Round | n | mean bias |
|---:|---:|---:|
| 1 | 103 | −18.28 |
| 2 | 98 | −16.31 |
| 3 | 111 | −12.03 |
| 4 | 132 | −22.54 |
| 5 | 110 | −19.44 |
| 6 | 126 | −15.68 |
| 7 | 116 | −12.00 |

**Finding: real rookie-season projections are systematically UNDER-predicted, not over-predicted, at every position and every round tested (2016-2025).** This is the opposite direction from the general age-cohort study's finding for "young" players broadly — the two are genuinely different populations with genuinely different bias directions, confirming the directive's premise that rookies needed their own study rather than being inferred from the general one.

## 4. What this does and doesn't mean

- It does **not** validate the owner's original framing ("NWR undervalues youth" as a blanket statement) — the general age study already real-world-tested and rejected that broader framing, and this document doesn't reopen or contradict that (different population).
- It **does** show that true rookies specifically are, on average, a real, conservative miss in the current model — actual rookie-season output outruns the projection by ~17 points/season on average, consistently across position and round. This is directionally the kind of "youth undervaluation" the owner originally suspected, just narrower in scope (rookies only, not all young players) than the original hypothesis.
- `WALK_FORWARD_SUMMARY.csv`'s ranking-accuracy metrics (model MAE vs. a naive position-median baseline, Spearman correlation) are mostly positive/favorable per season-position cell — i.e., the model still ranks rookies better than a naive baseline even while running low in absolute magnitude. Under-prediction bias and *ranking* quality are separate axes; this study only speaks to the former.

## 5. Disposition

No correction is proposed or applied here. The magnitude (~-16 to -17 pts/season, roughly a 25-30% relative miss on mean actual output) is real and large enough to be worth a deliberate, evidence-backed correction candidate in a future pass — but per this program's own no-arbitrary-constants discipline, a correction needs its own walk-forward-validated candidate (analogous to the rejected general-age correction candidate from 2026-07-21), not a same-night additive constant. Flagged as a concrete, scoped, evidence-backed follow-up rather than left as a vague TODO.

This also directly informs directive section 9 (full 78-rookie admission analysis): the 78-row 2026 rookie candidate already carries this exact real walk-forward evidence in its own governance trail and was already reviewed and owner-approved on that basis (`EXECUTIVE_VERDICT.md`) prior to this session. No new admission action is needed or taken here — this document uses that existing artifact's real evidence (directive's own instruction: "use the artifact, don't just build it") to answer the narrower rookie-bias-direction question the V4 directive asks, rather than re-deriving or re-litigating the prior admission decision itself.
