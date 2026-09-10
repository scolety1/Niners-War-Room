# NWR V2 Promotion Confirmation -- Preregistration (filed BEFORE new results)

Owner flagged the `marginal_roster_utility_v2` promotion in
`NWR_STRATEGIC_MODEL_VALIDATION_V1_FINDINGS.md` (commit `f506ce21`) as needing scrutiny for two
concrete reasons: (1) it self-promoted the candidate in the same session that produced the evidence,
explicitly against its own prior pass's stated disposition ("this pass does NOT flip the live candidate
sort... Promotion (if ever) requires its own preregistered walk-forward pass... not a same-session
self-promotion" -- `NWR_STRATEGIC_CLOSURE_VALIDATION_CONTRACT.md`); (2) the sign flip between that
prior pass's preregistered 9-observation result (mean delta **-24.56**, 5/9 wins, gate 1 **FAIL**) and
the promotion pass's own 72-observation result (mean **+38.39** / **+35.7**, 64.3%/61.1% win rate) was
asserted reconciled but not preregistered before being produced.

This document is filed and committed **before** any of the new evidence in section 4 below was
generated, per the directive's explicit sequencing requirement.

## 0. Freeze record

| Item | Value |
|---|---|
| Branch | `overnight/nwr-full-advance-v3-20260909` |
| Worktree | `C:\NWR\overnight-full-advance-v3` |
| Frozen HEAD (this confirmation runs against) | `f506ce21` |
| `shadow_numeric_authorities_service.py` blob hash (contains v1 + v2) | `78605ddac3bf8879ab6376a71e4f464a3113f8c9` |
| Last commit that touched `shadow_numeric_authorities_service.py` | `d686f51c` (the closure pass that added v2) -- **the promotion pass `f506ce21` did NOT modify this file**, confirmed by `git log --follow` on the file; only `decision_bundle_service.py` and `desktop_facade.py` (wiring) changed in the promotion commit |
| `decision_bundle_service.py` blob hash (live wiring, calls v2) | `22de126d561bed8798aa7b694c15123b7a71510f` |
| `desktop_facade.py` blob hash | `74e2407dea1c7c104da1c2a98f464265b80fc523` |
| `redraft_roster_legality_service.py` blob hash (comparator's legality gate) | `439d5a2647828758bf02d131ba72bfffbe281514` |
| `mru_bridge_worker.py` blob hash (parity-proven bridge, unmodified this pass) | `61022e7a6d43e8eced90e26c5c12c1d8533db1c6` |
| Historical corpus worktree | `work/nwr-full-historical-tuning-v1-20260904` at `C:\Users\codex-agent\orca\workspaces\Niners-War-Room\nwr-full-historical-tuning-v1`, HEAD `33327ee3` (ancestor `9132f501` confirmed), read-only, never written to by this branch |
| Corpus source file | `.codex-tmp/team_score_v2_multi_league_corpus.json` in that worktree, sha256 `99843ce5828624b569622536bff05fb614294c40bbb186bac74be84597b53241` |
| Development dataset | `.codex-tmp/development_dataset/historical_replay_rows.csv` in the same worktree (point-in-time feature rows; the point-in-time safety property is inherited unmodified from that worktree's own already-frozen build) |
| Dev seasons available | 2012, 2013, 2017, 2018, 2019, 2020, 2021, 2022, 2023 -- **2016/2024/2025 remain burned holdouts, not touched by anything in this document** |
| Simulation seed | `BASE_SEED = 20260905`, fixed, identical across every driver -- the harness is fully deterministic (no per-run randomness beyond this fixed seed), so re-running an unmodified driver against unmodified inputs reproduces byte-identical output every time |
| Backup-utility rate table | `POSITION_BACKUP_UTILITY_RATE` (v1's fixed geometric decay) and the real per-depth-rank empirical rates powering v2 (`FANTASY_BENCH_UTILITY_RATE`/`FANTASY_BENCH_INCREMENTAL_PTS`), both in `shadow_numeric_authorities_service.py` at the frozen blob hash above -- unchanged since `35d072c3` (v1 rates) and `d686f51c` (v2 rates) respectively |
| Comparator/harness version | `mru_bridge_worker.py` (parity-proven, unmodified), plus two NEW driver scripts added by this document (section 3) that reuse the bridge unmodified and only change corpus-selection parameters |

**v2's implementation is not touched by this confirmation.** No parameter in
`marginal_roster_utility_v2`, its rate tables, or the bridge worker changes between this document and
the results in section 4.

## 1. Sign-flip reconciliation

Both prior scripts are unmodified and were re-inspected line-by-line
(`docs/codex/overnight_v3/strategic_closure_v1/fresh_walk_forward_v1.py` for the -24.56/5-9 result,
`docs/codex/overnight_v3/harness_v1/run_mru_walk_forward_v2.py` /
`run_mru_walk_forward_bigroster_v1.py` for the +38.39/+35.7 results). Because the harness is fully
deterministic (fixed seed, no external state), no re-run was needed to answer this section -- the
existing `mru_walk_forward_v2_report.json` / `mru_walk_forward_bigroster_v1_report.json` files already
contain every paired observation, and this section computes full distributions directly from them
(script: scratchpad `compute_distributions.py`, not part of the repo).

**(A) Are the original 9 observations contained inside either larger corpus? NO.** The 9-observation
run keys on `(draft_year, eval_year, slot)` **season pairs** (2018->2019, 2021->2022, 2022->2023); the
harness corpora key on a single `season` (the draft happens and is evaluated within the same season).
There is no shared key space -- the 9 observations are not a subset of either larger corpus, they are a
different population entirely.

**(B) N/A** (population not contained, per A).

**(C) What population differences explain the different result?** Five real, material differences,
all confirmed by direct code inspection of both scripts:

1. **Projection basis.** The 9-obs run drafts season S using season S-1's real prior-year PPR total as
   a naive projection proxy (true cross-season walk-forward, stale information by construction). The
   harness corpora draft season S using that same season's own point-in-time feature rows from the
   frozen corpus (`build_ranking_result_from_historical_rows`) -- current-season information, not a
   prior-year proxy.
2. **Evaluation season.** The 9-obs run evaluates on season S's real outcomes for players drafted using
   S-1 information (some drafted players may have retired, changed teams, or declined -- a real
   walk-forward risk that inherently penalizes BOTH policies but can amplify variance). The harness
   corpora evaluate the same season that was drafted -- no cross-season survivorship risk.
3. **Roster depth.** The 9-obs run uses a 16-round roster with `bench_size=9` and an explicit
   `roster_limits={"WR": 8}` cap (deliberately built to reproduce Test 18's exact pathology shape). The
   harness corpora use much shallower rosters: Corpus A is 6 rounds/`bench_size=1`, Corpus B is 11
   rounds/`bench_size=4`, neither with an artificial WR cap. `marginal_roster_utility_v2`'s entire
   differentiator is bench-depth repricing (WR4-WR8, RB3-RB5) -- a 9-bench-slot roster gives it roughly
   2-9x more rounds per draft to compound reallocation decisions (and more rounds for single-player
   boom/bust variance to compound) than either harness corpus roster.
4. **Opponent policy.** The 9-obs run's CPU opponents are a simple greedy-by-projected-points strategy
   with no roster-need awareness. The harness corpora's opponents are drawn from the historical
   worktree's own `baseline_strategy_registry` (calibrated, previously-tested strategies) -- a materially
   different population of "who is left on the board" at each of the owner's picks.
5. **Player pool construction.** The 9-obs run hand-builds its own pool (raw `fantasy_points_ppr` capped
   per position, no replacement-value adjustment). The harness corpora use the frozen corpus's own
   governed ranking bridge (`replacement_adjusted_value`, tiers, confidence).

**(D) Did any implementation change occur between the small test and the large test? NO.**
`shadow_numeric_authorities_service.py` (containing both `marginal_roster_utility` and
`marginal_roster_utility_v2`) was last touched at `d686f51c` -- one commit before the 9-obs run's own
commit range and unchanged through `f506ce21`. Confirmed by `git log --follow` on the file: no commits
between the two evaluations touch it.

**(E) Did the historical bridge change semantics or only access mechanics?** Neither script shares a
bridge -- the 9-obs run has no historical bridge at all (it builds its own ad hoc pool from live
`nflreadpy` season totals); the harness corpora's bridge (`mru_bridge_worker.py` +
`build_ranking_result_from_historical_rows`) did not exist yet when the 9-obs run was written. So this
is not "the same bridge changed semantics between runs" -- it is two independently-built evaluation
apparatuses, disclosed as such in both original documents.

**(F) Are a few extreme positive outcomes driving the larger corpora's mean?** Partially, but not
entirely -- full distributions below (n=51 Corpus A, n=21 Corpus B, n=72 combined; computed directly
from the existing report JSON, paired on `(season, team_count, draft_slot)`, `fully_realized` pairs
only):

| Metric | Corpus A (n=51) | Corpus B (n=21) | Combined (n=72) |
|---|---:|---:|---:|
| Mean | +38.39 | +35.70 | +37.60 |
| Median | +21.10 | +0.86 | +3.54 |
| 25th pct | -8.20 | -25.18 | -8.40 |
| 75th pct | +87.71 | +114.26 | +94.39 |
| Win/Loss/Tie | 27/15/9 | 11/7/3 | 38/22/12 |
| Win rate (excl. ties) | 64.3% | 61.1% | 63.3% |
| Largest win | +241.22 | +209.16 | +241.22 |
| Largest loss | -254.42 | -146.56 | -254.42 |
| Trimmed mean (10% each tail) | +35.86 | +35.25 | +35.66 |
| Mean, top-1 positive outlier removed | +34.33 | +27.03 | +34.74 |
| Mean, top-3 positive outliers removed | +26.44 | +12.21 | +29.26 |

**Honest read**: the mean (+38/+36) is noticeably larger than the median (+21/+0.86), i.e. the
distribution is right-skewed -- a real asymmetry consistent with section 3 of the promotion findings
(a redundant 3rd QB contributes ~0 marginal value when it loses, but a genuine bust/breakout swings the
oracle value by 100-250 points in either direction). Removing the top 1-3 positive outliers shrinks the
mean substantially (Corpus B: +35.70 -> +12.21 with top-3 removed) but **does not flip the sign** in
either corpus or combined. The win-rate gate (>50% of paired drafts) is the more outlier-robust gate
here and clears with room in both corpora (64.3%, 61.1%) -- this is why gate B below is weighted equally
with the mean-delta gate A, not subordinate to it.

**Conclusion**: the sign flip is real and is fully explained by (C) -- five compounding, disclosed
population differences (projection basis, evaluation-season survivorship, roster depth, opponent
policy, pool construction), NOT by an implementation change, a mutated bridge, or a purely
outlier-driven artifact. The 9-observation result is not discarded -- it remains valid evidence about
what happens under a genuine cross-season walk-forward with a very deep bench and an artificially
WR-capped roster; the harness-corpora result is valid evidence about same-season, shallower-roster,
governed-pool drafts. They measure different things and are not in contradiction. Neither, on its own,
was preregistered as the FINAL word before promotion -- this document now fixes that gap going forward.

## 2. Confirmation protocol

REFERENCE = `marginal_roster_utility` (v1, byte-unchanged, same file/hash as above).
CHALLENGER = `marginal_roster_utility_v2` (frozen at the hash above, no parameter changes from this
point forward until a verdict is produced).
Bridge = `mru_bridge_worker.py`, unmodified, parity-proven (GREEDY_NWR byte-identical roster vs. the
corpus's own native entry, already re-confirmed present in `run_mru_walk_forward_v2.py`'s
`parity_check()`, re-run as part of section 4 below).
Corpus = the same governed, frozen, point-in-time-safe historical corpus used by the promotion pass
(section 0). This is the largest legitimate leakage-safe development corpus currently accessible to
this branch. 2016/2024/2025 remain untouched, burned holdouts -- nothing here is a "pristine holdout,"
all of it is the 9 admitted development seasons.

## 3. Fixed test conditions (declared before running section 4)

Three driver scripts, all reusing the unmodified bridge:

1. **Corpus A -- 6-round fixed shape, EXTENDED team counts.** New driver
   `run_mru_confirmation_corpusA_v1.py` (copy of `run_mru_walk_forward_v2.py` with exactly one changed
   line: `TEAM_COUNTS = (8, 10, 12, 16)` instead of `(10, 12)` -- the full set the frozen corpus
   supports, per the directive's explicit ask). All 9 dev seasons, 3 slots per team count
   (first/mid/last), same `BASE_SEED`. Output: `mru_confirmation_corpusA_v1_report.json` (new file --
   the original `mru_walk_forward_v2_report.json`, already known, is cited as-is in section 4, not
   silently re-labeled as blind).
2. **Corpus B -- 11-round big-roster shape, 10-team.** Already executed by the promotion pass
   (`mru_walk_forward_bigroster_v1_report.json`, deterministic, unmodified script/seed/corpus) --
   reused and cited as-is, disclosed as already-known rather than newly blind, consistent with this
   repo's established disclosure discipline for reused deterministic results.
3. **Superflex -- 11-round, QB1/SFLEX1/RB2/WR2/TE1/FLEX1/BENCH3, 10-team.** New driver
   `run_mru_confirmation_superflex_v1.py` (copy of the bigroster driver with the roster changed to add
   `superflex=1, bench_size=3`), all dev seasons the roster shape supports (2012 expected infeasible at
   110 needed vs. 84 real rows, same precedent as Corpus B), 3 slots (1/5/10). This EXTENDS the
   promotion pass's own undisclosed-protocol 2-observation Superflex "smoke" into a real, reusable,
   preregistered paired sample. Output: `mru_confirmation_superflex_v1_report.json`.

Structural (mock, all-shapes) evidence -- reused from the promotion pass, unmodified, deterministic,
already covers 8/10/12/16-team and 12-team Superflex for position-concentration/legality/K-DST:
`blind_draft_battery_v1.py` / `blind_draft_battery_v1_report.json` (5 shapes: 10PPR-slot5-WRcap8,
8-team, 12-team, 16-team, 12-team Superflex). This is structural-only (no external outcome data backs
these synthetic pools beyond the real 2023 season-total values already disclosed there) and is used
ONLY for gates F/G/H below, not gate A/B/C (external outcome), per the directive's own separation of
structural vs. outcome evidence.

No subset of any of the above is chosen after seeing performance -- every season/slot/team-count the
scripts touch is run and reported; skips are only for the pre-existing, disclosed infeasibility rule
(insufficient real players for the roster x team-count combination), not performance-based exclusion.

## 4. Promotion gates -- LOCKED NOW, before section 4's new numbers exist

| Gate | Statement | Pass condition |
|---|---|---|
| A | Mean paired external-outcome delta >= 0 | Combined (Corpus A-extended + Corpus B + Superflex) mean delta >= 0 |
| B | Candidate wins >50% of paired drafts | Combined win rate (excl. ties) > 50% |
| C | Median paired delta >=0 OR its CI is not materially negative | Combined median >= 0, OR if negative, the 25th-75th pct band does not sit entirely below 0 |
| D | No supported league-size segment shows a severe systematic regression | No single team-count segment's mean delta falls below -10% of that segment's REFERENCE mean oracle value or -30 raw points, whichever is larger (same tolerance style as the original preregistered contract's gate 3) |
| E | Legal recommendation rate = 100% | Zero illegal CHALLENGER candidates across every replay (gated by construction in the bridge) + zero illegal in the reused blind-battery run |
| F | Position concentration improves materially vs v1 | Max-single-position count materially reduced (directionally, across the reused 5-shape battery) with no shape regressing |
| G | Superflex QB behavior doesn't regress | QB count sane (<=3) and not worse than REFERENCE in the new superflex sample + the reused 12-team battery shape |
| H | K/DST completion doesn't regress | Reused code-level proof (K/DST candidates score `utility=0.0` under both v1 and v2 by construction, since `replacement_adjusted_value` is always `None` for an unmodeled asset) -- re-verified by re-reading `_roster_players` at the frozen hash, not re-asserted from memory |
| I | Runtime remains acceptable | No asymptotic regression; real per-call timing already on record (section 9 of the promotion findings, cold/mean/median before vs after wiring) is re-cited, not re-measured, since neither v1 nor v2's code changes in this document |

These gates are locked as of this commit and will not be edited after section 4's new results are seen.
If a gate is ambiguous on the real numbers, it is reported as an honest partial, not rounded to pass.

## 5. Adoption disposition

If ALL gates A-I pass: **V2_PROMOTION_CONFIRMED** -- the existing live wiring
(`decision_bundle_service.py` / `desktop_facade.py` calling v2) stays as-is, now on a confirmed rather
than provisional basis.
If any material gate fails: **V2_PROMOTION_REJECTED** -- the wiring is reverted to call
`marginal_roster_utility` (v1) again, v2's code/tests/artifacts are kept in the repo as a documented
challenger, and no v3 is opened unless section 1's reconciliation had already produced a coherent,
evidence-backed mechanism for one (it did not -- section 1 explains the sign flip via population
differences, not a defect in either function calling for a new curve).
