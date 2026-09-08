# NWR Marginal Roster Utility — Real Walk-Forward Evaluation & Promotion (V1)

**Date:** 2026-09-08
**Directive:** owner-requested — "Run the full historical walk-forward evaluation of the marginal-roster-utility engine and, if it passes, actually promote it into the live Pick Score/RAV recommendation path."
**Result: PASSED all 3 preregistered gates. PROMOTED.** `marginal_roster_utility` is now the primary candidate-ordering signal in `build_decision_bundle()` — the actual live recommendation basis, not just a display field.

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

## 8. Verification

Both real boards (403 N 18th `4b4a990faf124ce7a5d612537ba5943b`, Fantasy Gamers `4c5f04762921420595e4d8c7cda76582`) re-verified byte-identical (pick counts, `updated_at_utc`) before and after this entire evaluation and promotion — no real board was ever touched; all simulation ran against real historical nflverse data in an isolated, disposable synthetic league.
