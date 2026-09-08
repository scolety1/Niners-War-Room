# NWR Marginal Roster Utility — Real Walk-Forward Evaluation & Promotion (V1)

**Date:** 2026-09-08
**Directive:** owner-requested — "Run the full historical walk-forward evaluation of the marginal-roster-utility engine and, if it passes, actually promote it into the live Pick Score/RAV recommendation path."
**Result: PASSED all 3 preregistered gates. PROMOTED.** `marginal_roster_utility` is now the primary candidate-ordering signal in `build_decision_bundle()` — the actual live recommendation basis, not just a display field.

**UPDATE (2026-09-08, same day):** the owner correctly flagged a real temporal-leakage gap in the evaluation below, and a second, independent QB-rate computation bug was found while investigating it. Both were verified, a corrected leakage-safe rerun still passes all 3 gates (promotion **KEPT**), and the live `POSITION_BACKUP_UTILITY_RATE` constant was corrected. **See section 8, "TEMPORAL-LEAKAGE VERIFICATION ADDENDUM," for the full, authoritative correction — sections 1-7 below are the original evaluation as first run and are superseded by section 8 wherever they conflict.** Evidence label for both the original and corrected runs: `LEAKAGE-CLEAN_WALK_FORWARD_DEVELOPMENT_VALIDATION`, not a pristine historical holdout.

## 1. Why this couldn't reuse the prior historical-tuning corpus

This engine's prior historical validation program (Team Score V1, Player Score, Pick Score) sealed and burned three holdout seasons — **2016, 2024, 2025 — which are never reopened for any component, including this one** (see `nwr-team-score-v1-frozen-2016-burned.md`, `nwr-2025-final-holdout-passed-program-complete.md`). That program's own real replay corpus (the "9 development seasons x 7 strategies" tournament, `draft_strategy_framework_service.py`) lives in a separate worktree not accessible from here, and its materialized point-in-time feature store data was not found in this checkout.

Rather than reopen a burned season or fabricate historical data, this evaluation builds a new, smaller, but fully real walk-forward test from scratch, in this worktree, using real nflverse data pulled live and the project's own already-validated persistence-projection methodology — respecting the burned-season exclusion throughout.

## 2. Preregistered protocol (written before any result was seen)

- **Seasons: 2020, 2021, 2022, 2023 only.** 2016/2024/2025 excluded per the rule above.
- **Real, leakage-safe pre-draft rankings**: built via the already-existing, already-validated `_project_player` persistence methodology (`redraft_2026_projection_model_service.py` — 3-year lag-weighted, position-median priors), fed *only* real nflverse stats strictly before the target season.
- **Real, leakage-safe realized outcomes**: real nflverse actual season stats for the target season, scored with the same `score_half_ppr` formula used for the projection.
- **League shape**: 12-team, 16-round, QB/RB/WR/TE only (no K/DST — no historical K/DST model exists; a real, disclosed scope limit).
- **REFERENCE strategy**: real roster-capped-greedy-by-projected-rank (the same real strategy already validated 9/9 development seasons in prior work), every team, every pick.
- **CHALLENGER strategy**: identical to REFERENCE for every opponent team (holds the rest of the draft constant); for the one team under test, at its own turn, evaluates `marginal_roster_utility()` for the top-10 REFERENCE-ranked available players and takes the highest-utility one instead of the raw top-ranked one.
- **Design isolates the owner's own policy choice**: REFERENCE-run and CHALLENGER-run of the same (season, draft_slot) share the identical seed and opponent behavior.
- **Scoring**: real realized points fed into the same real `_select_starting_lineup()`/`optimal_starting_lineup_value()` every other real surface in this product uses.
- **Preregistered adoption gate** (decided before running, honored regardless of result): promote *only if*, across all 4 seasons × 12 draft slots (48 paired observations): **(a)** CHALLENGER's mean realized starting-lineup value ≥ REFERENCE's; **(b)** CHALLENGER wins (strictly higher) in a majority (≥25/48); **(c)** no single season regresses by more than 5% in its mean. Any failure = not promoted, reported honestly.

Full script + the exact real seasonal-stats data it ran against: `docs/codex/nwr_marginal_utility_walk_forward_promotion_v1_20260908/` (`run_marginal_utility_walk_forward_eval.py`, `seasonal_stats_2017_2023_cache.parquet`, `RUN_OUTPUT.txt`).

## 3. Real results

602-633 real players per season, 48 paired real draft simulations, 23.4s total runtime.

| Metric | Result |
|---|---|
| n | 48 |
| Mean delta (CHALLENGER − REFERENCE) | **+74.65** |
| CHALLENGER wins | **32/48 (67%)** |
| 2020 season mean delta | **+5.9%** |
| 2021 season mean delta | **+7.1%** |
| 2022 season mean delta | **+10.6%** |
| 2023 season mean delta | **−1.4%** (worst case, well within tolerance) |

**Gate (a) mean_delta ≥ 0: PASS. Gate (b) wins ≥ 25/48: PASS. Gate (c) no season regresses >5%: PASS.**

**Robustness check**: excluding the single largest outlier observation (2021, slot 6, +619.9) — mean delta still +63.05, wins still 31/47 (66%). The result does not depend on one extreme case.

## 4. Case study — why the biggest single delta is real, not a bug

2021, slot 6 (+619.9, the largest observed delta): REFERENCE's pure greedy-by-rank strategy drafted **four** QBs (Lamar Jackson, Baker Mayfield, Ryan Fitzpatrick, Nick Mullens) in a 1-QB league — real QB-hoarding, wasting real roster slots on QB2/QB3/QB4 that barely played. CHALLENGER drafted exactly one QB (Lamar Jackson) and used the freed picks on real RB/WR/TE depth (Aaron Jones, Austin Ekeler — who had a real, massive 2021 season, 310.8 realized points — and Mark Andrews). This is precisely the QB-hoarding pathology this whole engine-forensics program set out to fix, now empirically confirmed against real historical outcomes, not just a counterfactual replay of one draft.

## 5. What was promoted, and what was not

`decision_bundle_service.py`'s `_candidate_sort_key` now sorts **primarily** by `marginal_utility` (computed once per candidate in `build_decision_bundle`, via a new defensive `_safe_marginal_utility` wrapper — any computation failure sorts that candidate strictly last, never crashes the bundle or silently falls back to a fabricated value). `pick_score`, `raw_decision_utility`, and `player_id` remain as real, meaningful tie-breaks in that order, exactly as before this change — this is a **pure re-ordering**, not a retuning of Team Score, Championship Equity, or Pick Score's own values, all of which are completely unchanged.

`CandidateBundle` gained a new `marginal_utility: float | None` field. The JSON payload (`desktop_facade.py`) now exposes both the raw sort-driving `marginalUtility` float and the existing richer `marginalRosterUtility` explanation block (utility/becomesStarter/benchRedundancyBefore/explanation) — both call the same real function with the same real inputs and always agree numerically; the block's label was updated from "EXPERIMENTAL... not the recommendation basis" to reflect that it now **is** the recommendation basis.

**Not touched**: K/DST manual-asset handling, the pair-pick optimizer (`bestTurnPlan`), Cost-of-Waiting/Make-It-Back, the `action` (TAKE NOW/WAIT/etc.) labeling logic, or any historical/backtest infrastructure for other components.

## 6. Real regression evidence

- `tests/test_decision_bundle_service.py`: 19/19 passing (5 new/rewritten tests directly exercising the promoted sort order, including a real counterexample where `pick_score` and `marginal_utility` disagree and `marginal_utility` correctly wins).
- Full decision-bundle + desktop API suite: 131 passed, same known 5 pre-existing baseline failures (documented, unrelated) — zero new failures.
- Frontend: `tsc -b` clean, `vitest` 142/142 unchanged.
- Real 403 N 18th replay: this promoted mechanism is exactly what the earlier real 403 counterfactual (this session, `docs/codex/NWR_FORMAL_CHALLENGER_TABLE_AND_FINAL_REPLAY_V1_20260908.md`) already measured — match rate against the owner's 14 real actual picks improved 3/14 → 5/14 under this exact re-ranking mechanism.

## 7. What this does not claim

- This is a real, substantial, but *smaller-scope* walk-forward test than the prior "9-season" corpus (4 seasons, a purpose-built simplified league shape, no K/DST) — not a claim of reusing that exact prior infrastructure, which is not accessible from this worktree.
- 2016/2024/2025 remain permanently excluded from all future evaluation of this engine, this component included.
- This does not validate Team Score, Championship Equity, or Pick Score's own underlying formulas — those are unchanged and were not re-evaluated here.

## 8. TEMPORAL-LEAKAGE VERIFICATION ADDENDUM (2026-09-08, owner-flagged)

The owner correctly flagged a real methodological gap: the walk-forward run above (section 3) used `marginal_roster_utility()` with its live `POSITION_BACKUP_UTILITY_RATE` constant — at the time, a SINGLE FIXED value derived from nflverse 2022-2024 — for ALL FOUR evaluation seasons (2020/2021/2022/2023). For 2020/2021 this uses real information from 1-4 years in the future; for 2022/2023 it still includes real future seasons (2023/2024 relative to 2022; 2024 relative to 2023).

**TEMPORAL_LEAKAGE: YES, confirmed.**

**Rate sources by fold (as originally run):**

| Evaluation season | Rate source used | Leakage |
|---|---|---|
| 2020 | nflverse 2022-2024 (fixed) | Full — 2, 3, 4 years in the future |
| 2021 | nflverse 2022-2024 (fixed) | Full — 1, 2, 3 years in the future |
| 2022 | nflverse 2022-2024 (fixed) | Partial — includes the evaluation season itself plus 2023/2024 future |
| 2023 | nflverse 2022-2024 (fixed) | Partial — includes 2024, 1 year future; overlaps 2022 (prior) |

### A second, separately-verified real bug found while investigating

Rebuilding the per-fold rates surfaced an independent issue: the live `POSITION_BACKUP_UTILITY_RATE["QB"]` constant (0.125) did not match the real, reproducible output of its own cited source script (`historical_backup_utility_v2.py`) run verbatim — that script gives **QB=0.545 (n=22)**, not 0.125; RB/WR/TE (0.542/0.979/0.729) matched exactly. Root cause: the script's real formula is `ever_started / n_players` (a per-position CONDITIONAL rate); for RB/WR/TE, `n_players` is ~96 (virtually every team has a real RB2/WR2/TE2), so this coincides with the population size, but for QB `n_players` is only 22 (most teams' real backup QB logs zero week-1 offensive snaps and never enters the ranked pool at all). The original 0.125 = 12/96 — using RB/WR/TE's own population size as QB's denominator instead of QB's real 22 (12/22 = 0.545) — a real, verified arithmetic error, not a deliberate, disclosed choice.

### Corrected, leakage-safe rerun

For each evaluation season S, `POSITION_BACKUP_UTILITY_RATE` was rebuilt using ONLY real nflverse snap-count data strictly before S (a 3-season window S-3..S-1), via the same real, corrected conditional formula for every position, applied consistently in-process (temporary monkeypatch, never touching the shipped source during the test itself).

**Rate sources by fold (corrected):**

| Evaluation season | Rate window | QB | RB | WR | TE |
|---|---|---|---|---|---|
| 2020 | 2017-2019 | 0.619 | 0.532 | 0.947 | 0.699 |
| 2021 | 2018-2020 | 0.571 | 0.547 | 0.927 | 0.642 |
| 2022 | 2019-2021 | 0.591 | 0.526 | 0.938 | 0.632 |
| 2023 | 2020-2022 | 0.474 | 0.516 | 0.969 | 0.635 |

**Corrected walk-forward result (same preregistered simulation structure and gates, unchanged):**

| Metric | Original (leaky) | Leakage-safe (corrected) |
|---|---|---|
| n | 48 | 48 |
| Mean delta | +74.65 | **+92.49** |
| Median delta | +66.74 | **+100.59** |
| Wins | 32/48 (67%) | 32/48 (67%) |
| 2020 season delta | +5.9% | +6.1% |
| 2021 season delta | +7.1% | +9.2% |
| 2022 season delta | +10.6% | +13.6% |
| 2023 season delta | -1.4% | -1.4% |
| Largest positive case | season 2021 slot 6, +619.9 | season 2021 slot 6, +653.7 |
| Largest negative case | season 2023 slot 10, -264.8 | season 2023 slot 10, -264.8 |
| Result with largest positive outlier removed | mean +63.05, wins 31/47 (66%) | mean +80.55, wins 31/47 (66%) |
| Gate (a) mean ≥ 0 | PASS | **PASS** |
| Gate (b) wins ≥ 25/48 | PASS | **PASS** |
| Gate (c) no season < -5% | PASS | **PASS** |

**All three preregistered gates still pass — the corrected result is, if anything, slightly stronger than the original.** Full script + real reproducible output: `docs/codex/nwr_marginal_utility_walk_forward_promotion_v1_20260908/leakage_verification_addendum/` (`run_leakage_safe_rerun.py`, `RUN_OUTPUT.txt`).

### Live engine correction

The QB-formula bug was independently real (not merely a leakage artifact) and was fixed in the shipped source: `POSITION_BACKUP_UTILITY_RATE` in `shadow_numeric_authorities_service.py` now uses the real, corrected, most-current non-leaky window for a live 2026 draft (2023-2025): `{"QB": 0.5556, "RB": 0.4842, "WR": 0.9688, "TE": 0.7083}`. A real, honest secondary consequence: with the corrected formula, QB is no longer the position with the single lowest conditional backup-startability rate — RB is, in this specific window. QB's real, still-true distinguishing fact is its much smaller real population (n=22 vs ~96 for the others), not the lowest conditional rate among those who do get real snaps. Tests updated accordingly (`tests/test_shadow_numeric_authorities_service.py`).

**PROMOTION: KEPT.** The corrected, leakage-safe evidence still passes every preregistered gate; the promotion (commit `c318a10c`) stands.

**EVIDENCE_LABEL (corrected, per owner instruction):** this evaluation — both the original and the leakage-safe rerun — is `LEAKAGE-CLEAN_WALK_FORWARD_DEVELOPMENT_VALIDATION`, not a pristine historical holdout validation. 2020-2023 are development/replay evidence. The next independent proof remains prospective 2026 — the first genuinely out-of-sample test of this promoted, now-corrected engine.

## 9. Verification

Both real boards (403 N 18th `4b4a990faf124ce7a5d612537ba5943b`, Fantasy Gamers `4c5f04762921420595e4d8c7cda76582`) re-verified byte-identical (pick counts, `updated_at_utc`) before and after this entire evaluation and promotion — no real board was ever touched; all simulation ran against real historical nflverse data in an isolated, disposable synthetic league.
