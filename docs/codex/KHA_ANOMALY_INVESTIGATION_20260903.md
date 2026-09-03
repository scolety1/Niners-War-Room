# KHA named-anomaly investigation (2026-09-03)

Evidence-only, no fixes shipped. Investigates the owner's specific named
complaints from the real 2026-09-02 draft against real data on disk.
Verdicts: CONFIRMED (real defect, with evidence) / REFUTED (data looks
fine) / INSUFFICIENT_EVIDENCE.

## 1. Garrett Wilson gap display — CONFIRMED (systemic, not Wilson-specific)

`nwr_vs_espn_gap` is correctly populated and arithmetically sound
(-150.0 = 27.0 ADP - 177 nwr_rank). The FantasyPros fields
(`fantasypros_ecr`, `fantasypros_tier`, `fantasypros_projected_points`)
are the literal string `API_TIER_NOT_RETURNED` for Wilson -- and for
**599 of 608 rows** in `KHA_FINAL_CHEAT_SHEET.csv`. This is a near-total
FantasyPros ingestion failure across the whole cheat sheet, not a
Wilson-specific bug. Separately, Wilson's `nwr_rank=177` (Tier 11, "Deep
pool") against an ESPN ADP of 27 is itself a striking outlier worth its
own look, independent of the display bug.

## 2. Kenny/Kenneth Gainwell — REFUTED

`current.csv`, the cheat sheet, the UDK snapshot, and the real recap all
agree on "Kenny Gainwell" with a single consistent `player_id`
(`00-0036919`). "Kenneth Gainwell" only appears in free-text scouting
prose about *other* players, never as a separate structured entity. No
duplication or identity defect found.

## 3. Josh Jacobs status/suspension — INSUFFICIENT_EVIDENCE on the real
status, CONFIRMED that NWR's data can't reflect one either way

No FantasyPros injury/news row exists for Jacobs in the (very small, 10
row each) `FANTASYPROS_INJURIES.csv`/`FANTASYPROS_NEWS.csv` on disk.
More importantly: `current.csv`'s `source_status`/`evidence_status`
fields are **constant across all 608 rows** (`GOVERNED` /
`ADMITTED_CURRENT_SEASON`) -- they carry no player-specific signal for
*any* player, so this mechanism structurally cannot surface a suspension
for anyone right now, Jacobs included. This is the section 16 "current
player truth" gap in concrete form.

## 4. Joe Flacco over Joe Burrow — CONFIRMED, root cause found

Flacco outranks Burrow both by `nwr_rank` (126 vs 142) and by
`current.csv` projection band (floor 49.1 vs 40.9, ceiling 236.2 vs
228.0). Root cause: `source_id
NWR_REDRAFT_2026_STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE_V1` persists
last season's raw box-score totals forward as the 2026 baseline. Burrow's
prior season was injury-shortened (8 games); Flacco (started/relieved,
13 games) has a fuller counting-stat line from that stretch, which
outweighs Burrow's shorter one under a pure persistence approach with no
per-game-rate normalization or availability-adjusted floor.

## 5. Jonathon Brooks / MarShawn Lloyd — CONFIRMED (already resolved)

Real universe gaps, both `UNMATCHED` in the UDK identity snapshot, absent
from `current.csv`. Already addressed: both now have a manual asset via
`src/services/udk_unmodeled_skill_asset_service.py` (see the Lane C
commits).

## 6. Brock Purdy current-status — CONFIRMED (same mechanism as #3)

No FantasyPros injury/news entry for Purdy on disk. `current.csv`'s
`availability_probability` field, which reads like a live 2026 health
signal, is actually `games_played_last_season / 17` for every player
checked (Wilson 0.4118=7/17, Burrow 0.4706=8/17, Jacobs 0.8824=15/17,
Gainwell 1.0=17/17, Purdy 0.5294=9/17) -- a backward-looking artifact of
the persistence methodology, not a current assessment. There is no live
current-status signal being applied to Purdy (or, structurally, to
anyone) at all.

## 7. Travis Hunter offensive-role uncertainty — CONFIRMED, and it's
worse than "role uncertainty poorly reflected"

Travis Hunter is **completely absent** from `current.csv` and the cheat
sheet -- same `UNMATCHED` identity-resolution failure pattern as Brooks/
Lloyd, confirmed independently via the UDK snapshot
(`identity_status=UNMATCHED`, no `nwr_player_id`). He was a real,
drafted player in the real KHA draft (pick 171, round 11). NWR couldn't
display *any* information about him, role-related or otherwise, because
he was never resolved into the universe at all. Already covered by the
same Lane C fix as #5 (he's one of the 14 UNMATCHED rows the new manual
asset ingestion admits).

## 9. Troy Franklin ADP extreme — CONFIRMED

`nwr_rank=91` (Tier 7) vs `espn_adp=977.0` (`nwr_vs_espn_gap=886.0`, the
largest gap found in this whole investigation), while UDK independently
agrees with the market (`udk_position_rank=97` -- 97th-best WR, `~round
16` ADP). NWR's rank comes from a fully-persisted 2025 box score (104
targets/709 yds/6 TD). UDK's own scouting text explicitly flags the 2026
context NWR's data doesn't reflect: a Day-2 rookie WR (Pat Bryant) took
snaps, and the team traded for Jaylen Waddle in the offseason -- both
role-reducing events. The `current_alert`/`udk_current_conflict_flag`
mechanism exists and does work for other players (e.g. Tutu Atwell's row
correctly carries `UDK_CONTEXT_STALE_OR_CONFLICTING`) but did not fire
for Franklin despite this being the largest divergence found. Undrafted
in the real 192-pick recap, consistent with the market's read.

## Cross-cutting pattern across items 3/6/7/9

All four trace to the same root shape: `current.csv`'s
"current-ness" fields (`source_status`, `evidence_status`,
`availability_probability`) are either constant/non-differentiating or
backward-derived from last season's box score, not a live 2026 signal --
and the `current_alert` mechanism that's supposed to catch role/context
changes (which does work, per Tutu Atwell) is inconsistently triggered.
This is section 16's "Current Player Truth" gap, evidenced concretely
across four independent named complaints rather than asserted in the
abstract.
