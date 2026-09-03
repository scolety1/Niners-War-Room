# Rookie market-blend CHALLENGER — real backtest result (section 17)

Implements the challenger `docs/codex/ROOKIE_SHADOW_AUDIT_20260903.md`
called for: "A challenger should target the *specific* weakness
(backward-looking, no current-year signal), not a blanket rookie-rank
boost, and should be evaluated against both the 9 confirmed misses and
the 3 negative controls above so a fix does not overcorrect."

Code: `src/services/rookie_market_blend_challenger_service.py` (SHADOW/
RESEARCH only — not imported by `desktop_facade.py` or any frontend
page, verified via grep). Tests:
`tests/test_rookie_market_blend_challenger_service.py`, 6/6 passing.

## What it does

- CHAMPION = NWR's existing `nwr_rank`, returned completely untouched.
- CHALLENGER = a linear blend of `nwr_rank` toward real-time market ADP
  (`champion * (1 - w) + espn_adp * w`), applied **only** to rows whose
  `current.csv` `source_id` is exactly
  `NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1` — the one mechanism
  the audit traced as the confirmed root cause. Every other row is
  returned untouched with a disclosed reason (`OUT_OF_SCOPE_SOURCE_ID` /
  `NO_MARKET_SIGNAL_AVAILABLE`), never silently dropped.
- `DEFAULT_BLEND_WEIGHT = 0.5` is a disclosed midpoint, **not** a
  backtested optimum — no weight was hand-tuned against the sample below
  to make the numbers look better. That would be exactly the overfitting
  risk the audit warned against.

## Real backtest (not circular)

Ground truth is each rookie's real `recap_overall_pick` from
`sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.csv` — the actual
2026-09-02 KHA draft outcome — not the ESPN ADP the challenger was
blended toward (comparing against that would be a trivial, circular
result). Sample: the same 12 real-recap-matched skill-position rookies
the audit itself found (9 confirmed misses + 3 negative controls),
`nwr_rank`/`espn_adp` transcribed verbatim from the audit's own table.

| Player | Champion rank | Challenger rank | Real pick | Champion error | Challenger error | Result |
|---|---|---|---|---|---|---|
| Jeremiyah Love | 59 | 46.6 | 26 | 33.0 | 20.6 | improved |
| Carnell Tate | 118 | 92.6 | 51 | 67.0 | 41.6 | improved |
| De'Zhaun Stribling | 200 | 180.0 | 114 | 86.0 | 66.0 | improved |
| Ja'Kobi Lane | 296 | 245.1 | 177 | 119.0 | 68.1 | improved |
| Caleb Douglas | 303 | 259.95 | 169 | 134.0 | 90.95 | improved |
| Jonah Coleman | 260 | 211.05 | 182 | 78.0 | 29.05 | improved |
| Mike Washington Jr. | 259 | 214.4 | 154 | 105.0 | 60.4 | improved |
| Denzel Boston | 201 | 179.65 | 191 | 10.0 | 11.35 | **worsened** |
| Makai Lemon | 116 | 107.35 | 112 | 4.0 | 4.65 | **worsened** |
| Jadarian Price (control) | 60 | 65.3 | 57 | 3.0 | 8.3 | **worsened** |
| Jordyn Tyson (control) | 117 | 113.55 | 132 | 15.0 | 18.45 | **worsened** |
| KC Concepcion (control) | 120 | 120.85 | 118 | 2.0 | 2.85 | **worsened** |

**Aggregate**: mean absolute error 54.67 → 35.19 (−35.6%); median 50.0 →
24.83 (−50.3%). **7 of 12 rows improve, 5 of 12 get individually worse**
— every "worsened" row is a case that was already close (champion error
≤ 15), and a uniform 0.5 blend nudges it slightly off. This is the exact
overcorrection risk the audit flagged, reported honestly rather than
hidden behind the flattering aggregate number.

## What this is and is not

This is a real, measured, evidence-grounded CHALLENGER with a genuine net
improvement on the one real sample available — not a claim that 0.5 is
the right production weight, and not a promotion to production ranking.
It is a single draft's worth of rookies (12 players): directionally
informative, not statistically powered. Before any promotion:
- Backtest against additional real drafts as they become available.
- Consider whether a lower blend weight reduces the 5-row regression
  without giving up most of the 7-row improvement (not attempted here —
  would itself need a held-out sample to avoid overfitting to this one).
- Route through the Champion/Challenger scaffolding
  (`docs/codex/CHAMPION_CHALLENGER_SCAFFOLDING_20260903.md`) rather than
  a manual code change, so any future promotion is itself an auditable,
  reversible event.
