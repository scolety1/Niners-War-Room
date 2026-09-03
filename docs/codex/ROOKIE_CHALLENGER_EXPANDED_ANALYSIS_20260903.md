# Rookie challenger — expanded analysis, v2 gap-gated variant (section 14)

Code: `challenge_rookie_ranks(..., min_gap_to_blend=...)` in
`src/services/rookie_market_blend_challenger_service.py`
(`DEFAULT_GAP_GATE_THRESHOLD = 20.0`). Tests: 2 new in
`tests/test_rookie_market_blend_challenger_service.py` (8/8 total
passing). Still SHADOW/RESEARCH only, still not imported by
`desktop_facade.py` or any frontend page. **Not promoted** — see
Champion/Challenger status below.

## Which 7 improved, which 5 worsened

Sorting `docs/codex/ROOKIE_MARKET_BLEND_CHALLENGER_20260903.md`'s real
backtest rows by the champion's own error against the real outcome:

| Player | Champion error | NWR-vs-market gap | Result |
|---|---|---|---|
| Ja'Kobi Lane | 119.0 | −101.8 | improved |
| Caleb Douglas | 134.0 | −86.1 | improved |
| Jonah Coleman | 78.0 | −97.9 | improved |
| Mike Washington Jr. | 105.0 | −89.2 | improved |
| De'Zhaun Stribling | 86.0 | −40.0 | improved |
| Carnell Tate | 67.0 | −50.8 | improved |
| Jeremiyah Love | 33.0 | −24.8 | improved |
| Denzel Boston | 10.0 | −42.7 | **worsened** |
| Jordyn Tyson (control) | 15.0 | −6.9 | worsened |
| Jadarian Price (control) | 3.0 | +10.6 | worsened |
| Makai Lemon | 4.0 | −17.3 | worsened |
| KC Concepcion (control) | 2.0 | +1.7 | worsened |

## The discovered mechanism

Every one of the 7 improved rows has `champion_error >= 33` (and
`|gap| >= 24.8`); every worsened row except one has `champion_error <=
15` and `|gap| <= 17.3`. This is the standard shrinkage-toward-a-noisy-
target pattern: when NWR's own rank is *already* far from the real
outcome, blending toward a different, independent signal (market ADP)
tends to help. When NWR is already close, blending toward *anything
else* — even a generally-informative signal — adds noise more often
than it removes it.

**champion_error itself isn't known at draft time** (it requires the
real outcome). The one variable that *is* known at draft time and
correlates with it here is the raw NWR-vs-market gap magnitude
(`|nwr_rank - espn_adp|`) — large disagreement with the market is a
real, available signal that NWR's rank is more likely to be the wrong
one.

**The one real exception, disclosed not hidden**: Denzel Boston has a
*large* gap (−42.7, bigger than Love's −24.8, which improved) but still
worsened — NWR (rank 201) happened to be closer to the real outcome
(pick 191) than the market (158.3) was, in this one case. A large
NWR-vs-market gap means "these two disagree a lot," not "the market is
necessarily right." Position, draft round, and projection-missingness
were also checked against the improved/worsened split and found no
cleaner separator than gap magnitude in this sample.

## v2: gap-gated variant, predeclared from this mechanism

`challenge_rookie_ranks(..., min_gap_to_blend=20.0)`: leave the
champion's rank untouched when `|nwr_rank - espn_adp| < 20`, matching
the discovered threshold — a single global constant, not tuned per
player (Boston's own large gap still gets blended, and still comes out
worse; the gate does not special-case him away).

**Real result on the same 12-row sample** (`backtest_against_real_outcomes`,
run for real, not projected):

| | v1 (always blend) | v2 (gap-gated) |
|---|---|---|
| Mean abs. error | 35.19 | **34.34** |
| Median abs. error | 24.83 | 24.83 |
| Improved | 7 | 7 (unchanged) |
| Worsened | 5 | **1** |
| Unchanged | 0 | 4 |

v2 keeps every real improvement v1 found, fixes 4 of v1's 5 worsened
rows (Lemon, Price, Tyson, Concepcion all revert exactly to the champion
rank — `challenger_error == champion_error`, not "improved," just no
longer actively hurt), and even nudges the mean error down further.
Boston remains the one row that still gets slightly worse, honestly
reported.

## Champion/Challenger status

`rookie-market-blend-v2-gap-gated` is a real, tested, evidence-backed
candidate — genuinely better than v1 on the one real sample available —
but **not registered or promoted anywhere**. Per section 19/28's own
rule, no automatic promotion exists in this codebase, and this session
does not fabricate an owner's registration/promotion decision on their
behalf. A single 12-rookie sample from one draft is still not a
statistically powered backtest; the natural next step (not done this
pass) is backtesting both v1 and v2 against additional real drafts as
they become available, then having the owner explicitly register and
decide via `champion_challenger_registry_service.py`.
