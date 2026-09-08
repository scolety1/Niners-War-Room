# NWR Class-Time Autonomous Hardening — Running Ledger

**Started:** 2026-09-08, HEAD `00446dcd`. Owner unavailable (in class); explicit authorization for ordinary, reversible, local work only. No push/merge/deploy. No destructive real-board operations.

This ledger is updated after each coherent unit of work (per the directive's own checkpoint discipline) rather than producing a final report only at the end. Both real boards (403 `4b4a990faf124ce7a5d612537ba5943b`, Fantasy Gamers `4c5f04762921420595e4d8c7cda76582`) are re-verified byte-identical before and after every unit.

## Section 1 — DecisionBundle latency, continued

Reprofiled after the two fixes already committed (`00446dcd`). Real wall time (3 repeated calls, same isolated real 530-row profile): **5.81–6.95s** (down from the pre-fix ~13.4s, and down further from the first post-fix reading of 8.25-8.94s — real system-load variance between runs, both readings real and reproducible for their own run).

Real remaining hot path (cProfile, cumulative): `_select_asset` (10,056 calls, ~6.1s own time, down from 9.2s) → dominated by `_seeded_unit` (4.8M calls, ~3.7s, a real per-candidate SHA256-based deterministic jitter -- NOT touched, changing its algorithm would alter real shipped reproducible values) and the per-call roster `Counter` rebuild (`state["picks"]` is a full list rebuilt fresh every call by design -- restructuring this to an incrementally-maintained roster would require changing `_advance_cpu`'s calling convention, a real, riskier structural change, not a pure performance fix).

**Disposition: stopping here for this pass, per the directive's own "do not force a risky rewrite" instruction.** Target `<5s` not fully reached (currently ~5.8-6.95s); stretch `2-3s` not reached. No further changes made — the two committed fixes remain the full extent of this pass's latency work. Documented, not overclaimed.

## Section 2 — Shared-FLEX / deep-bench marginal utility fix (DONE, commit `4ba8ce00`)

Fixed the real, previously-reproduced bug: `roster_composition_report`'s `position_redundancy` credited each FLEX-eligible position its own independent FLEX allowance, double-counting the one real shared FLEX slot. Fix: derive redundancy directly from `starters` (the real, already-computed, shared-FLEX-aware greedy selection) instead of an independent capacity formula -- lossless by construction, no magic per-position bonus. 1 new regression test reproduces the exact real contention case (3RB/2WR/2TE/1FLEX) and proves TE redundancy is now correctly 1, not 0. Full regression: 53/53 (shadow_numeric_authorities) + 185 passed broader (same known 5 baseline). Frontend clean. Boards unchanged.

## Section 3 — Rerun leakage-clean validation (the FLEX fix changed live-ordering inputs) (DONE)

Reran the same leakage-clean 48-paired-draft protocol (unchanged gates). **Result: mean_delta +91.78 (vs +92.49 pre-fix, real small variance), wins 32/48 (67%, unchanged), no season regression >5%. ALL 3 GATES STILL PASS.** The FLEX fix only affects rare 3rd-deep-bench scenarios and does not materially change the promoted engine's validated real performance. Promotion remains KEPT, no rollback needed.

## Section 4a — Diggs-class acquisition-filter fix (DONE, this commit)

Full evidence: `docs/codex/NWR_DIGGS_CLASS_SOURCE_GAP_FIX_V1_20260908.md`. Widened
`build_current_projection_candidate`'s universe filter from `last_season==season` to
`last_season.between(season-1, season)` (Diggs-class: real active players whose most recent
recorded stat line lags one season). Real audit against the exact live-build snapshot caught a
genuine false-positive risk (Philip Rivers/Russell Wilson, `status=ACT` despite real retirement)
-- fixed with a second, real, gsis_id-keyed cross-check against the already-staged
`seasonal_rosters_2025` snapshot (excludes only the newly-widened slice, only when real roster
status is INA/RET/CUT, keeps unmatched gsis_ids). **Final guarded result: 910 -> 973 (+63 net),
12 real false positives caught and excluded, 75/75 (100%) roster-snapshot coverage on the
widened slice.** Also fixed a genuine pre-existing latent empty-DataFrame `KeyError` in
`blocked_frame`/`identity_frame` construction, first reachable via this new exclusion path. 4
new tests (true-positive, true-negative, unwidened-slice-untouched, missing-coverage-kept), all
pass; full 77-test regression across the 3 touched files clean. Both real boards re-verified
byte-identical.

## Section 4b — Brooks-class fix (existing-infrastructure reuse for insufficient-history players)

(next)
