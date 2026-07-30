# NWR Dual Lens RC1 V1 report

## Outcome

Primary verdict: `GREEN_NWR_FINISHED_V1_RETAINS_AUTHORITY_DUAL_LENS_NOT_ADMITTED`.

- Strongest bounded Win Now formula: `W3_SHORT_HORIZON_CALIBRATED_BLEND`.
- Strongest bounded Dynasty formula: `D1_DISCOUNTED_MULTI_HORIZON_VOR`.
- Win Now admitted: `False`.
- Dynasty admitted: `False`.
- Production/UI integration: `NONE`.
- Finished V1 authority: `RETAINED`.
- Outcome V3: `INDEPENDENT_UNCHANGED_NO_RANK_EFFECT`.

## Why two formulas are analytically warranted

The objectives are not interchangeable. Win Now uses next-season
lineup-adjusted VOR and explicit availability. Dynasty uses separately predicted
H1/H2/H3 VOR, above-replacement retention, and bounded position-specific horizon
behavior. A single score can correlate with both, but it cannot transparently
expose the availability-versus-retention tradeoff. Team Window therefore remains
a visible normalized blend, not a third opaque model.

## Finished V1 diagnosis

Historical exact Finished V1 receipts remain unavailable and were not replayed.
The governed accepted production-family proxy produced Win Now Spearman
0.649216 and Dynasty Spearman 0.659459. Its inputs are dominated by
lagged production, opportunity, replacement/VORP context, and current-only
lifecycle/confidence concepts. It is best classified as a **short-balanced
dynasty score with a strong Win Now core**, not a proven long-horizon model.
Position evidence is mixed:

| position | win_spearman | dynasty_spearman | classification |
| --- | --- | --- | --- |
| QB | 0.680656445 | 0.657662222 | WIN_NOW_LEAN |
| RB | 0.66925351 | 0.685375591 | INCONSISTENT_OR_BALANCED |
| WR | 0.695946337 | 0.724737708 | SHORT_BALANCED_DYNASTY_LEAN |
| TE | 0.678835502 | 0.684806295 | INCONSISTENT_OR_BALANCED |

## Formula comparison

Win Now reference: Spearman 0.649216, rank MAE 79.566616, nDCG 0.973073, coverage 100.00%, severe errors 57.
Win Now research candidate: Spearman 0.693439, rank MAE 69.591628, nDCG 0.975311, coverage 100.00%, severe errors 55.
Season-clustered bootstrap delta: 0.043686,
95% CI [0.027834, 0.058516].

Dynasty reference: Spearman 0.659459, rank MAE 46.254194, nDCG 0.978578, coverage 59.18%, severe errors 21.
Dynasty research candidate: Spearman 0.720216, rank MAE 40.072258, nDCG 0.980155, coverage 59.18%, severe errors 15.
Season-clustered bootstrap delta: 0.060787,
95% CI [0.039394,
0.084588].

## Rookie and veteran audit

The mart begins only after a prior NFL season exists. It therefore supports
second-year, third-year, established, and low-games cohorts, but zero true
rookies. Early declare, college production, breakout age, athletic testing, and
authoritative injury-return labels are missing or source-blocked. Positive NFL
draft evidence and age/draft metadata remain review-only. The canonical
240-row board contains zero rows flagged `is_rookie`, so there is no current
rookie population to score or review. Unsupported current feature rows retain
null lens scores and explicit missing reasons.

## Detached boards

`CURRENT_2026_DUAL_LENS_SHADOW_BOARD.csv` contains all 240 Finished V1 rows.
Only fixed-source-ready rows receive detached research scores; unsupported rows
stay null. Ranks are over the scored research subset and are not production
240-player ranks. Contending 75/25, Balanced 50/50, and Rebuilding 25/75 use
visible 0–100 normalized score inputs.

## App decision

The conditional integration requirement was not met. Player Compare, Trading
Lab, Rankings, draft tools, roster/planning, Data Health, and Refresh Data remain
unchanged. The audit specifies a future dual-lens contract, but no partial
product, fallback score, hidden weight, trade winner, or draft toggle was
installed.
