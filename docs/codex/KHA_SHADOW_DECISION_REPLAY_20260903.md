# KHA decision shadow replay (section 12)

Script: `scripts/run_kha_shadow_optimizer_replay_v1.py` (run:
`python -m scripts.run_kha_shadow_optimizer_replay_v1`). Output:
`docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv` (checked in). Tests:
`tests/test_kha_shadow_optimizer_replay.py`, 8/8 passing, including an
independent recomputation of every row's `team_score_after` from scratch
to prove no future pick ever leaked into an earlier row.

**Source**: `sample_data/kha_real_draft_2026/live_runtime_draft_board_157picks.json`,
read-only, never modified — the real, untouched 157-pick live capture of
the 2026-09-02 KHA draft. 10 real owner picks (team_slot 9) fall inside
that live-captured window (rounds 1–10; the recap's remaining 35 picks,
158–192, were never captured live with an `nwr_rank`, so this replay
stops there — "as far as currently valid," per the directive's own
phrasing).

## Two disclosed limitations — not worked around

1. **Value magnitude**: the live board carries `nwr_rank` (an ordinal)
   per pick, not `replacement_adjusted_value` (a points magnitude). The
   only source of that magnitude is the governed 2026 projection
   snapshot, which `docs/codex/PLAYER_UNIVERSE_SATURDAY_RENEWAL_PACKET.md`
   already concluded must not be reused beyond the single 2026-09-02
   draft without fresh owner approval. This script does **not** load
   that snapshot. Every Team Score / Championship Equity number instead
   uses a disclosed, uniform proxy (`value = max(0, 609 - nwr_rank)`),
   applied only to real players with their real ranks — labeled
   `RANK_DERIVED_PROXY_NOT_REAL_MAGNITUDE` in every row and the CSV's
   own header comment.
2. **Candidate alternatives / Cost of Waiting**: the live board only
   records `nwr_rank` for the 157 players actually drafted, not the
   ~450 real players who weren't. Computing "what NWR would have
   recommended instead" needs the full ranked universe — not available
   without the same blocked snapshot. Those columns are marked
   `NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE`, never guessed.

## What IS real and computable

The owner's own real Team Score and Championship Equity before/after
each of their 10 real picks, evaluated against the **actual other 15
teams' real rosters-so-far** at that exact point in the real draft (not
a simulated population — the real field, built from the same live
board). No leakage: at pick P, only picks with `pick_number < P` build
the comparison field, verified two ways — a structural roster-count
check and an independent from-scratch recomputation of every row's
`team_score_after`.

| Pick | Rd | Player | Real nwr_rank | Team Score | Champ Equity |
|---|---|---|---|---|---|
| 9 | 1 | James Cook | 16 | — → 46.7 | — → 0.085 |
| 24 | 2 | Kyren Williams | 27 | 0.0 → 86.7 | 0.0 → 0.225 |
| 41 | 3 | Tetairoa McMillan | 52 | 33.3 → 80.0 | 0.0 → 0.175 |
| 56 | 4 | Jameson Williams | 44 | 33.3 → 100.0 | 0.0 → 0.27 |
| 73 | 5 | Kenny Gainwell | 38 | 46.7 → 100.0 | 0.0 → 0.23 |
| 88 | 6 | Jaxson Dart | 36 | 73.3 → 100.0 | 0.01 → 0.38 |
| 105 | 7 | Lil'Jordan Humphrey | 325 | **73.3 → 73.3** | 0.03 → 0.03 |
| 120 | 8 | Juwan Johnson | 82 | 46.7 → 100.0 | 0.005 → 0.255 |
| 137 | 9 | Jayden Reed | 287 | **100.0 → 100.0** | 0.24 → 0.24 |
| 152 | 10 | Woody Marks | 109 | **100.0 → 100.0** | 0.19 → 0.19 |

**Real, honestly-reported finding**: picks 105, 137, and 152 (real
nwr_rank 325, 287, 109 — the three deepest ranks among the owner's live-
captured picks) show **zero change** in Team Score. By this metric,
those specific real picks did not improve the owner's optimal starting
lineup at the moment they were made — either because the real roster
already had its relevant starter/FLEX slots filled by stronger players,
or the pick's own rank-proxy value was too low to displace anything
already rostered. This is not a claim those were bad real-world
decisions (bench depth, bye-week coverage, and injury insurance are real
value this metric does not capture — see
`bench_contingency_value` in `roster_composition_report`, not used in
this replay's headline column but available in the underlying function)
— it is exactly what "Team Score V2 measures starting-lineup strength,
not total roster construction" predicts, reported as-is.

## What this does not attempt

A full pick-by-pick optimizer disagreement analysis (comparing the
optimizer's own top candidate against the real pick at every turn) is
explicitly out of reach without the full ranked universe — see
limitation 2 above. Extending this replay past pick 157 (the recap's
remaining 35 picks) is also out of scope: those picks were never
captured live with an `nwr_rank`, and fabricating one would violate this
session's evidence rules.
