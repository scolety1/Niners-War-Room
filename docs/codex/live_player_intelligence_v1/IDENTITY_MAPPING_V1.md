# NWR Live Player Intelligence — Canonical Identity Mapping V1

Work Unit 2, branch `upgrade/nwr-live-player-intelligence-v1-20260913`,
worktree `C:\NWR\live-player-intelligence-v1`. Maps ALL THREE candidate
sources' rows (Sleeper `players/nfl` catalog, nflverse official injury
report, nflverse depth charts) through NWR's EXISTING canonical identity
resolver — `_identity` in `fantasypros_kdst_consensus_service.py`, the
SAME normalizer `waiver_engine_service.resolve_roster_canonical_ids` and
`live_player_intelligence_shadow_v1_service.match_shadow_records_to_canonical`
already use. **No second matcher was built.** New code
(`src/services/live_player_intelligence_identity_mapping_v1_service.py`)
adds a per-row classification granular enough to report the six categories
the directive asked for (matched uniquely / unmatched / ambiguous / team
mismatch / name mismatch / provider-ID mismatch) for **every** row of each
source — not just the "actionable status" subset the existing shadow
module already filtered to — plus tests
(`tests/test_live_player_intelligence_identity_mapping_v1_service.py`, 16
cases, all passing) proving the classification logic on known constructed
examples.

## Canonical pool used

`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv`
— the real, governed 564-player Freeze V7 pool (the same one Worker 1's
coverage numbers were measured against). Verified this pass:
`player_id` already uses the `gsis_id` scheme directly (e.g.
`00-0023459`), 564/564 ids unique, **zero internal identity collisions**
(no two canonical rows normalize to the same `_identity(name, position,
team)` key) — checked programmatically every run
(`AMBIGUOUS_CANONICAL_POOL_COLLISION`), not assumed. Real, disclosed
finding: this pool is QB/RB/WR/TE only (79/129/219/137) — no K or DST — so
every K/DST row across all three sources is structurally unable to match
it, which the classification reports as `UNMATCHED_POSITION_OUT_OF_SCOPE`,
never conflated with a genuine miss.

## Classification design (full detail in the module's own docstring)

One mutually-exclusive PRIMARY bucket per row, in this priority order:

1. `AMBIGUOUS_CANONICAL_POOL_COLLISION` — the canonical pool itself can't
   disambiguate (checked for real; found 0 across all runs).
2. `AMBIGUOUS_ID_NAME_DISAGREEMENT` — the row's own provider id resolves
   to one canonical player, but its name/position/team independently
   resolves to a DIFFERENT one. Two disagreeing signals — quarantined,
   never guessed between.
3. `MATCHED_GSIS_DIRECT` — provider id is a literal canonical-pool member.
4. `UNMATCHED_POSITION_OUT_OF_SCOPE` — no id match, and the row's own
   position doesn't correspond to any canonical-pool position at all.
5. `MATCHED_NAME_POSITION_TEAM` — no id match, exact `_identity` hit.
6. `TEAM_MISMATCH` — the row has a real, non-empty team, no id match, no
   exact hit, but name+position match a canonical player under a
   DIFFERENT non-empty team (relaxed lookup, same `_identity` normalizer
   with team ignored — team is never silently dropped from the ADMITTED
   match itself, only used to detect this specific quarantine case).
7. `UNMATCHED_NO_TEAM` — no team value on the row at all; a
   name+position-only candidate (if any) is recorded for visibility in
   `teamMismatchCandidateTeam` but is NEVER treated as a match (this app's
   `_identity` requires a non-empty team by design, and this pass does not
   relax that to inflate coverage).
8. `UNMATCHED` — none of the above.

Two further ORTHOGONAL diagnostic flags (reported as their own counts,
can co-occur with any bucket above): `nameMismatch` (an id-matched row's
own name string disagrees with canonical — informational, id still wins)
and `providerIdMismatch` (a fantasy-relevant-position row carries a
non-empty id that is NOT a canonical member at all — real data-quality
signal; deliberately NOT computed for out-of-scope-position rows, where a
"foreign" id is structurally expected, not a quality defect).

A third label, `teamMismatchIsKnownCodeAlias`, is set on a `TEAM_MISMATCH`
row **only for reporting** when the two disagreeing team codes are an
already-known alias pair this codebase handles elsewhere (`LAR`/`LA`,
`JAC`/`JAX` — see `nflverse_player_context_display_service.py` and
siblings). This does **not** change the row's classification or
un-quarantine it — it exists purely so the counts below can separate real
roster-change-shaped signal from known spelling-convention noise, without
inventing a new matching heuristic inside `_identity` itself.

## Real results (this pass's own run, reproducible via
`python scripts/build_live_player_intelligence_identity_mapping_v1.py`)

### (A) Sleeper `players/nfl` catalog — ALL 12,227 rows

| Bucket | Count |
|---|---|
| Matched uniquely (GSIS_DIRECT 126 + NAME_POSITION_TEAM 362) | **488** |
| Unmatched (UNMATCHED 406 + UNMATCHED_NO_TEAM 3,356) | **3,762** |
| Ambiguous | **0** |
| Team mismatch (total) | **15** |
| — of which known code-alias noise (LAR/LA) | 14 |
| — of which genuine (real roster-change-shaped) | **1** |
| Position out of scope | 7,962 |
| Name mismatch (diagnostic) | 4 |
| Provider-ID mismatch (diagnostic, in-scope-position only) | 1,197 |
| Distinct canonical players matched | 487 / 564 = **86.35%** |

The one genuine team mismatch: Xavier Gipson, WR — Sleeper's catalog shows
`PHI`, NWR's canonical pool shows `NYG`. Not resolved or auto-corrected
here; listed explicitly in the quarantine file below for manual review.

This 86.35% full-catalog identity-coverage number is a DIFFERENT metric
than Worker 1's own 18.1% "actionable-signal" coverage figure — Worker 1
measured coverage among only the subset of Sleeper rows carrying a
flagged/actionable status; this pass measures coverage among the ENTIRE
catalog (every active/healthy player too), which is naturally much higher.
Both numbers are real and not in conflict; they answer different
questions and are documented here to prevent future confusion between
them.

### (B) nflverse official injury report — ALL 182 rows

| Bucket | Count |
|---|---|
| Matched uniquely (all GSIS_DIRECT) | **52** |
| Unmatched | **1** |
| Ambiguous | **0** |
| Team mismatch | **0** |
| Position out of scope | 129 |
| Name mismatch (diagnostic) | 0 |
| Provider-ID mismatch (diagnostic) | 1 |
| Distinct canonical players matched | 52 / 564 = **9.22%** (exact match to Worker 1's earlier figure) |

The single `UNMATCHED` row: Jonathon Brooks (RB, CAR, real gsis_id
`00-0039344`, not a member of the 564-pool). Consistent with this
project's own already-documented "Brooks-class" finding elsewhere in NWR's
history (memory: a real, evidence-backed player kept out of the frozen
pool after a genuine walk-forward evaluation) — not a new anomaly this
pass introduces, flagged here only to avoid re-litigating it as if it
were.

### (C) nflverse depth charts — latest single-day snapshot (2,222 rows, `dt=2026-09-13T12:42:08Z`)

| Bucket | Count |
|---|---|
| Matched uniquely (GSIS_DIRECT 653 + NAME_POSITION_TEAM 1) | **654** |
| Unmatched | **121** |
| Ambiguous | **0** |
| Team mismatch | **0** |
| Position out of scope (OL/DL/LB/DB/return-role/punter/holder/long-snapper roles) | 1,447 |
| Name mismatch (diagnostic) | 15 |
| Provider-ID mismatch (diagnostic) | 120 |
| Distinct canonical players matched | 500 / 564 = **88.65%** (vs. Worker 1's own 88.5% / 499 — 1-player difference, consistent minor variance, not a discrepancy worth chasing) |

Only 32-of-many total `pos_name` values map to NWR's fantasy-position
vocabulary (`Quarterback`→QB, `Running Back`/`Fullback`→RB, `Wide
Receiver`→WR, `Tight End`→TE, `Place kicker`→K); every offensive-line,
defensive-front/back-seven, punter/holder/long-snapper, and pure
return-specialist role label is real, present, and intentionally left
`UNMATCHED_POSITION_OUT_OF_SCOPE` rather than silently dropped before
counting.

## Quarantined records (explicitly listed, never silently dropped)

Per Gate 2 ("ambiguous or low-confidence match is quarantined... zero
guessed joins") and the directive's own instruction, AMBIGUOUS +
TEAM_MISMATCH rows are excluded from any "clean" dataset and instead
listed in full here (all committed, not gitignored):

- `identity_mapping_v1/sleeper_public_players_catalog_quarantined.csv` — 15 rows (14 known LAR/LA code-alias + 1 genuine).
- `identity_mapping_v1/nflverse_official_injury_report_quarantined.csv` — 0 rows.
- `identity_mapping_v1/nflverse_depth_charts_quarantined.csv` — 0 rows.
- `identity_mapping_v1/summary.json` — the exact machine-readable counts above, per source, plus the canonical pool size.

Full per-row classification for every row of every source (matched AND
unmatched AND out-of-scope, not only quarantined) was also written, but to
a **gitignored** `local_exports/live_player_intelligence_shadow_v1/
identity_mapping_v1/<source>_all_rows.csv` location rather than committed
— these are large (the Sleeper file alone is 12,227 rows) and directly
reproducible from the already-committed raw source snapshots plus
`scripts/build_live_player_intelligence_identity_mapping_v1.py`; nothing
in them is unique information that would be lost, only regenerable detail.
Re-run the script locally to regenerate them.

## What this pass did NOT do

- Did not invent any new matching heuristic beyond what already existed
  (`_identity`) — the team-code-alias labeling is reporting-only, verified
  against three other services in this codebase that already handle it,
  and never changes a row's classification.
- Did not resolve the 15 quarantined Sleeper team-mismatch rows one way or
  the other — they remain quarantined, for a human or a future pass to
  review.
- Did not attempt fuzzy name matching, phonetic matching, or any
  confidence-scored join. Every match is either a literal id-set
  membership check or the exact same `_identity` normalizer already
  proven elsewhere.
