# Rookie shadow audit — root-cause families (section 14)

Extends `docs/codex/QB_MARGINAL_VALUE_AND_ROOKIE_CALIBRATION_AUDIT_20260903.md`
with the requested root-cause-family categorization. Read-only evidence
work; no production Core formula touched or promoted.

## Method

For every rookie in the prior audit's real-recap-matched sample (12
skill-position rookies actually drafted in the real KHA draft) plus
`Jadarian Price`/`KC Concepcion` (already in that sample, included below
for contrast), pulled `source_id` from `projections/2026/current.csv` —
the field that names which pipeline actually produced that player's
projection — to distinguish "same mechanism, bad outcome" from "different
mechanism entirely."

## Root-cause families found

**`rookie_prior_scaling`** — CONFIRMED, same `source_id
NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1` on every affected row:

| Player | NWR rank | ESPN ADP | Gap | Round-gap (prior audit) |
|---|---|---|---|---|
| Jeremiyah Love | 59 | 34.2 | -24.8 | +1.69 |
| Carnell Tate | 118 | 67.2 | -50.8 | +3.38 |
| De'Zhaun Stribling | 200 | 160.0 | -40.0 | +4.50 |
| Ja'Kobi Lane | 296 | 194.2 | -101.8 | +6.50 |
| Caleb Douglas | 303 | 216.9 | -86.1 | +7.94 |
| Jonah Coleman | 260 | 162.1 | -97.9 | +4.25 |
| Mike Washington Jr. | 259 | 169.8 | -89.2 | +6.19 |
| Denzel Boston | 201 | 158.3 | -42.7 | +0.56 |
| Makai Lemon | 116 | 98.7 | -17.3 | +0.25 |

A historical-outcomes-by-NFL-draft-round baseline is structurally
backward-looking: it cannot see current-year opportunity signals (camp
buzz, a depth-chart change, a competing veteran's injury/departure) that
the real market has already priced in by ADP. This is the confirmed
mechanism, not a guess — same `source_id` across every row above.

**Important negative control, same mechanism**: `Jadarian Price`
(rank 60, ADP 70.6, gap +10.6 — essentially matching market) and `Jordyn
Tyson` (rank 117, ADP 110.1, gap -6.9, i.e. NWR slightly *ahead* of
market) and `KC Concepcion` (rank 120, ADP 121.7, gap +1.7) all carry the
**identical** `source_id` and are not under-ranked at all. **The
mechanism is not uniformly biased** — it is a noisy predictor whose error
is player-specific (correlated with how much a given rookie's real
current-year role diverges from the historical round-median pattern), not
a constant offset applyable as a blanket correction. This rules out a
simple "add N ranks to every rookie" fix as the right response.

**`identity_universe`** — CONFIRMED, different symptom (total absence,
not under-ranking): Jonathon Brooks, MarShawn Lloyd, Travis Hunter — all
`identity_status: UNMATCHED` in the UDK snapshot, absent from
`current.csv` entirely. Already addressed this session via
`udk_unmodeled_skill_asset_service.py` (Lane C) — representable now, still
carries zero NWR score by design (no projection exists to under- or
over-rank).

**Families not found in this sample**: `missing_projection_input` beyond
the identity/universe cases above (no rookie had a `current.csv` row with
a real projection that was simply zeroed/blank), `stale_role` (no rookie
in this sample showed evidence of a role change the data failed to
reflect — that pattern showed up for veterans instead, see the Troy
Franklin / Joe Flacco findings in `KHA_ANOMALY_INVESTIGATION_20260903.md`),
`replacement_model` (rookie replacement-level computation was not
separately audited this pass — the confirmed QB replacement-depth defect
in the calibration audit is a veteran/format issue, not rookie-specific),
`market_divergence` (ESPN ADP itself was not found unreliable in any
rookie case checked — NWR diverges from a market that already looks
internally reasonable).

## Conclusion

Systematic rookie under-ranking is real (confirmed prior audit) and now
has a confirmed, singular root-cause family for every case checked:
`rookie_prior_scaling`'s position-round-median baseline. It is a
noisy-but-directionally-real predictor, not uniformly broken — 3 of the
15 rookies checked across both audits were fine or better than market
under the identical mechanism. A challenger should target the *specific*
weakness (backward-looking, no current-year signal), not a blanket
rookie-rank boost, and should be evaluated against both the 9 confirmed
misses and the 3 negative controls above so a fix does not overcorrect
the cases that already work. No challenger built this pass — this is the
evidence handoff, per this lane's "no player-specific production hack,
build challenger work only if evidence supports one" instruction; the
evidence does support one, scoped as above.
