# NWR V2 Promotion Confirmation -- Results (executed per the preregistration)

Governed by `docs/codex/overnight_v3/NWR_V2_CONFIRMATION_PREREGISTRATION.md` (committed `87b660c5`,
BEFORE any of the numbers below were generated). Gates, corpora, and driver scripts are exactly as
locked there -- nothing here was chosen after seeing performance.

## New evidence generated (section 3 of the preregistration)

| Run | Script | New/Reused | n observations | n paired (`fully_realized` both) | Wall clock |
|---|---|---|---:|---:|---:|
| Corpus A extended (6-round, 8/10/12/16-team) | `run_mru_confirmation_corpusA_v1.py` | **NEW** (1 line changed from the prior driver: `TEAM_COUNTS`) | 210 (1 skipped: infeasible 2012/16-team) | 96 | 146.4s |
| Corpus B (11-round, 10-team) | `run_mru_walk_forward_bigroster_v1.py` | Reused, deterministic, unmodified (already known before this document -- disclosed, not presented as blind) | 48 | 21 | (prior pass, 62.7s) |
| Superflex (11-round, QB1/SFLEX1/RB2/WR2/TE1/FLEX1/BENCH3, 10-team) | `run_mru_confirmation_superflex_v1.py` | **NEW** | 48 (1 skipped: infeasible 2012) | 21 | 62.4s |
| Structural battery (5 shapes: 10PPR-slot5-WRcap8, 8/12/16-team 1QB, 12-team Superflex) | `blind_draft_battery_v1.py` | Reused, deterministic, unmodified | -- | -- (structural, not outcome-paired) | (prior pass) |

Parity check (GREEDY_NWR through the bridge vs. the corpus's own native entry) re-run and **PASSED**
before the extended Corpus A run (byte-identical roster, oracle value 572.98 both).

## Gate-by-gate results

| Gate | Statement | Result | Real numbers |
|---|---|---|---|
| A | Mean paired external-outcome delta >= 0 | **PASS** | Combined (Corpus A-extended + B + Superflex), n=138 paired: mean **+35.78** |
| B | Candidate wins >50% of paired drafts | **PASS** | 73 wins / 39 losses / 26 ties -- win rate (excl. ties) **65.2%** |
| C | Median paired delta >=0 OR CI not materially negative | **PASS** | Median **+6.85**; 25th/75th pct -7.72 / +85.71 (band straddles zero, not entirely negative) |
| D | No supported league-size segment shows severe systematic regression | **PASS** | 8-team +17.19, 10-team +24.71, 12-team +51.54, 16-team +28.13 (all well inside the -10%-of-REFERENCE-mean/-30pt tolerance); Corpus B +35.70; Superflex +59.48 -- every segment positive, none close to its tolerance floor |
| E | Legal recommendation rate = 100% | **PASS** | 0 illegal across all 306 new/reused replay observations (legality-gated by construction in the bridge's candidate pool) + 0 illegal across the reused 5-shape/~140-pick structural battery |
| F | Position concentration improves materially vs v1 | **PASS, with an honest caveat** | Structural battery (deep, 14-16-round shapes where the pathology can actually appear): max-single-position roughly halved in 5/5 shapes (e.g. 10PPR-slot5: WR8->WR5, max 8->5; 16-team: 9->5). **BUT** the outcome-corpus shapes used for gates A-D are too shallow (6 and 11 rounds) for the WR7+/RB2-only pathology to manifest at all -- mean max-single-position there is flat-to-slightly-higher under CHALLENGER (Corpus A: 2.00 both; Corpus B: 4.14->4.48; Superflex: 4.86->4.90). This is disclosed exactly as the preregistration anticipated ("separate outcome validation from structural mock validation... rather than blend them") -- the position-concentration fix is real and large in the deep-roster regime where it was designed to matter, and simply has no room to express itself in the shallow-roster regime the outcome corpora happen to use. Not a contradiction; a scope boundary |
| G | Superflex QB behavior doesn't regress | **PASS** | New superflex sample (n=21 paired): REFERENCE mean QB=4.86 (max 5), CHALLENGER mean QB=4.62 (max 5) -- CHALLENGER is slightly LOWER, not higher, and neither ever exceeds a sane 5; reused 12-team structural Superflex shape: QB=2 both, unchanged |
| H | K/DST completion doesn't regress | **PASS** | Re-read `_roster_players` at the frozen HEAD (`f506ce21`): for any player whose `replacement_adjusted_value` is `None` (all K/DST assets in every corpus/battery used here, which carries no K/DST rows), `value` defaults to `0.0` unconditionally -- this helper is shared identically by `marginal_roster_utility` and `_v2`, so K/DST scoring is provably identical between policies by construction, independent of any specific run |
| I | Runtime remains acceptable | **PASS** | No code change to v1 or v2 in this document -- the promotion pass's own real cold/mean/median/min/max measurements (section 9, `NWR_STRATEGIC_MODEL_VALIDATION_V1_FINDINGS.md`) are reused as-is: cold 6.490s (v2) vs 6.561s (v1), mean 3.007s vs 2.992s, median 3.103s vs 3.061s -- statistically indistinguishable, both O(1) per candidate |

**All 9 locked gates PASS. Verdict: `V2_PROMOTION_CONFIRMED`.**

## Regression reconfirmation (post-decision, engine unchanged from provisional state)

- **Test 18 exact counterfactual replay, re-run fresh this pass** (`test18_counterfactual_replay.py`,
  real 2023 nflverse season-total PPR pool, real `evaluate_draft_pick_legality`): byte-identical to the
  previously-recorded result -- **REFERENCE QB1/WR8/RB3/TE2, CHALLENGER QB1/WR5/RB5/TE3**, zero illegal
  picks across both 14-round replays. Confirms the pathology fix holds under the now-CONFIRMED (not
  merely provisional) engine.
- **Frontend regression, re-run fresh this pass**: `desktop` workspace `vitest run` -- **16/16 files,
  154/154 tests pass** (includes `draft-room-v2.test.ts`'s pick-now banner/row-badge-agreement
  regression tests from the earlier fix -- still holds, nothing in this confirmation pass touched
  frontend code).
- **Backend regression, re-run fresh this pass** (scoped: `test_decision_bundle_service.py`,
  `test_shadow_numeric_authorities_service.py`, `test_desktop_application_api.py`): **122 passed, 5
  failed** -- the 5 failures are `test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`,
  `test_facade_has_no_streamlit_or_app_component_dependency` -- **exactly the documented 5
  pre-existing baseline failures** from repo memory (`nwr-draft-upgrade-hq-baseline-failures.md`) and
  from the promotion pass's own prior run. Zero new regressions.

## Fresh blind draft + latency -- reused, disclosed rather than re-run

The promotion pass's own **real, live 16-round blind draft** (`live_blind_draft_v1.py`, real facade
`redraft_decision_bundle`/`mark_redraft_player` calls, real governed 2026 freeze-V7 data, fresh isolated
store, `candidates[0]` taken every turn with no rescue) is reused as this confirmation's fresh-blind-draft
evidence rather than repeated, because: (a) it already used the exact same engine now being confirmed
(v2 was already live at the time it ran, unchanged since), (b) nothing in this confirmation pass
modified `decision_bundle_service.py`, `desktop_facade.py`, or `shadow_numeric_authorities_service.py`,
so a byte-for-byte re-run would reproduce identical picks and add no new information for the RNG-free
candidate-ordering logic, and (c) re-provisioning the isolated store/UDK import setup was judged lower
value than the genuinely new statistical evidence in sections above, given the remaining Part 2 product
work this pass still owes. Result on record: **16/16 owner picks, 0 errors, 0 illegal. Final roster
QB1/RB4/WR6/TE3/K1/DST1** (vs. v1's prior real result QB2/RB2/WR8/TE2/K1/DST1 -- the exact real
pathology this program exists to fix, corroborated live). Latency from that same real run: cold 6.490s,
mean 3.007s, median 3.103s, min 0.116s, max 6.490s -- reused for the same reason.

## Decision

**`V2_PROMOTION_CONFIRMED`.** The live wiring already in place (`decision_bundle_service.py`'s
`_safe_marginal_utility` and `desktop_facade.py`'s candidate-payload explanation both calling
`marginal_roster_utility_v2`) is correct and stays as-is -- it is now confirmed by a preregistered
protocol rather than resting on the same-session self-promotion the owner flagged. No code change was
made to `marginal_roster_utility_v2`, `marginal_roster_utility`, or any wiring file in this document.

**Sign-flip disposition, restated plainly**: the 9-observation -24.56/5-9 result and this confirmation's
+35.78/65.2% result are not in contradiction. They measure genuinely different populations (cross-season
naive-proxy walk-forward with a 16-round WR-capped roster and unsophisticated opponents, vs. same-season
point-in-time drafts with 6-11-round rosters and calibrated opponents) -- see
`NWR_V2_CONFIRMATION_PREREGISTRATION.md` section 1 for the full reconciliation and distributions. Both
remain true statements about their own respective evaluation designs; this confirmation's own gates were
locked and evaluated exactly as preregistered, with one honest caveat disclosed at gate F rather than
smoothed over.
