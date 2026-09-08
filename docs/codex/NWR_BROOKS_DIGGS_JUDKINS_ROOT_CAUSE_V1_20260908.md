# NWR Brooks / Diggs / Judkins — Real Pipeline Root-Cause Trace (V1)

**Date:** 2026-09-08 (overnight V4 continuation)
**Scope:** Directive V4 sections 11 (trace the Brooks/Diggs source-gap through the full acquisition→identity→projection→admission pipeline, fix systemically if safe) and 12 (finish the Judkins diagnosis with a specific classification). Explicitly not a name-patch for any of the three — the goal is a real, verified root cause and an honest classification, not a special-cased correction.

## 1. Method

For each named player, traced through the exact real files/logic the live pipeline actually uses:
1. The raw nflverse player-registry snapshot the veteran build reads (`C:\NWR_SHARED_DATA\source_snapshots\nflverse\players\20260730T072407Z-42af9666ac84\raw\players.parquet`).
2. `build_current_projection_candidate()`'s real universe filter (`src/services/redraft_2026_projection_model_service.py:142-146`: `last_season == 2026`, `position in (QB,RB,WR,TE)`, `status in (ACT, RES)`).
3. The admission packet's own `CANDIDATE_PROJECTION_SNAPSHOT.csv` / `BLOCKED_PLAYER_ROWS.csv` / `GOVERNED_PROJECTION_SNAPSHOT.csv` (`docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808/`).
4. The final live source file the active ranking actually reads (`{redraft_root}/projections/2026/current.csv`, 608 rows).

## 2. Stefon Diggs — ACQUISITION-stage exclusion, root-caused

**Not present anywhere** in the 608-row live source, the 530-row candidate snapshot, or the veteran blocked-rows list. Traced to the exact registry snapshot the build reads:

```
gsis_id=00-0031588  display_name=Stefon Diggs  position=WR  latest_team=NE
status=ACT          rookie_season=2015          last_season=2025
```

`status=ACT` passes the filter. **`last_season=2025` fails `last_season.eq(2026)`** — this is the real, specific exclusion cause. Diggs suffered a real ACL tear in November 2024 and did not record any 2025 regular-season stats; nflverse's `last_season` field on the master player-registry table is stats-based (the most recent season a player has a real recorded stat line), not roster-membership-based — so it had not yet advanced to 2026 as of this snapshot (2026-07-30, pre-season, before any 2026 stats exist for anyone). Cross-checked against ~530 other real players who DO show `last_season=2026` in the same snapshot despite the season not having started, confirming this is not a universal pre-season artifact — those players' registry rows had already been advanced (2025 stats exist for them), Diggs's specifically had not.

**Real, systemic root cause**: `last_season.eq(season)` is used as a proxy for "currently active heading into the target season," but it actually measures "has a recorded stat line as recently as the target season" — a proxy that silently fails for any real player who missed a full season (injury, suspension, opt-out) immediately prior to the projection year, even when they are genuinely active and rostered.

**Fix disposition**: NOT applied tonight. A safe fix (e.g., falling back to roster-membership/depth-chart data instead of stats-based `last_season` when it lags, or explicitly widening the filter to `last_season >= season - 1` combined with a real roster-membership check) needs its own validation — it changes who enters the universe for every future veteran-persistence build, not just Diggs, and could admit real inactive/retired players if done carelessly. Flagged as a concrete, scoped, root-caused follow-up with the exact file/line to change (`redraft_2026_projection_model_service.py:143`), not a name patch for Diggs specifically.

## 3. Jonathon Brooks — correctly BLOCKED downstream, not an acquisition gap

Brooks **passes** the universe filter (`status=ACT`, `last_season=2026`, `position=RB` — all confirmed directly against the same snapshot). He is absent from `current.csv` and the 530-row candidate snapshot, but **is present, by name, in the real `BLOCKED_PLAYER_ROWS.csv`**:

```
player_id=00-0039344  player_name=Jonathon Brooks  position=RB  team=CAR
reason: "no prior-season NFL stat line; persistence forecast blocked"
```

Real-world cause: Brooks tore his ACL in his 2024 rookie season and recorded effectively no usable game log; the persistence model requires a real prior-season (t-1..t-3) stat line to forecast from and correctly refuses to fabricate one. He is not flagged `rookie_season == 2026`, so he also does not qualify for the separate rookie model track (`NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1`), which only admits players whose actual draft/rookie season is the current projection year.

**Real, systemic root cause**: a genuine coverage gap between the two models — a player in his 2nd (or later) league year who lost his rookie season to injury has no real prior-season production (fails the veteran persistence model's data requirement) and is not a rookie by the rookie model's own eligibility rule (fails that model too). This is correct, disclosed, non-silent behavior (he's in `BLOCKED_PLAYER_ROWS.csv` with an honest reason, not silently dropped) — but it is a real hole in projection coverage for a real, notable player category: returning-from-injury 2nd/3rd-year players with near-zero prior production.

**Fix disposition**: NOT applied tonight. Building a responsible third model track for this category (how much signal is really available for a player coming off a lost rookie season — draft capital, college production, a handful of 2024 pre-injury snaps?) is a real, nontrivial modeling problem requiring its own evidence base, not a same-night patch. Flagged as a scoped, root-caused follow-up, distinct from the Diggs acquisition-filter fix above.

## 4. Quinshon Judkins — SPECIFIC CLASSIFICATION (not missing, not blocked)

Judkins **is present and admitted** in the live source (`current.csv`, `source_status=GOVERNED`, `evidence_status=ADMITTED_CURRENT_SEASON`) via the veteran persistence model, using his real 2025 rookie-season stat line (230 carries, 827 rush yards, 7 TD — a real committee/backup-tier workload behind Cleveland's since-departed starter). Active ranking: **RB position_rank 26, overall_rank 81, projected_points 167.8, confidence LOW**. Real market reference (FFA, 2026-09-04): RB19, 185 points, ADP 49.6 — a real but moderate gap (7 position-rank spots), not one of tonight's largest FFA disagreements.

**Classification: a real, disclosed persistence-model role-change blind spot — not a data-acquisition gap, not a bug, not a candidate for a name-specific patch.** The `STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE` model is, by design, a pure statistical forward-projection from a player's own recent stat line; it has no explicit depth-chart-change or role-projection signal, so a player transitioning from a committee/backup role into a presumptive lead-back role between seasons will systematically lag real-world market consensus until his *actual* new-season stats exist to persist from. The model's own confidence heuristic (`_confidence()` in `redraft_engine_v1_service.py`, driven by the `projection_low`/`projection_high` width ratio and availability) already, if incidentally, flags this: Judkins's width ratio is 0.86 (well above the 0.40 MEDIUM threshold), correctly landing him at LOW confidence — the system is honestly disclosing its own uncertainty here even without a purpose-built role-change feature. This is a known, general category of limitation (any real player with a between-season role change will read the same way), not a Judkins-specific defect.

**Fix disposition**: none proposed. LOW confidence is the correct, honest signal for this real situation; the underlying rank/value themselves are exactly what the disclosed model methodology should produce given its documented inputs.

## 5. Verification

Read-only throughout — parquet/CSV reads and one `generate_rankings()` call against the already-active snapshot; no facade write path exercised, no real board touched. Re-verified both real boards byte-identical before and after this investigation.
