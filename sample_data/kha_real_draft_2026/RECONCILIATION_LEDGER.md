# KHA live-vs-recap reconciliation ledger — methodology and findings

Companion to `RECONCILIATION_LEDGER.csv` (192 rows, one per real draft slot).
Supersedes the open question in `DIVERGENCE_FINDINGS_20260903.md` — see the
resolution note at the top of that file.

## Owner explanation (authoritative)

The 2026 KHA High Stakes League draft ran on ESPN. NWR was used live,
alongside it, to record picks and drive recommendations. It was **not**
reset or restarted, and the live capture is **not** a second/different
draft. When an ESPN pick could not be represented in NWR — the real player
was missing from NWR's universe, unsearchable, a K/DST (NWR had no K/DST
model), or otherwise blocked — the operator sometimes entered a different,
available NWR player as a placeholder just to advance the live draft state
and keep working. `official_recap_192picks_clean.csv` (the platform's own
recap) is authoritative for what actually happened. The live 157-pick
capture is authoritative for NWR's own operational behavior that night —
including its failures.

## Join key

Earlier analysis (`DIVERGENCE_FINDINGS_20260903.md`) joined live picks to
the recap by matching `pick_number` to player identity globally, which
made the divergence look like an unexplained numbering drift. The correct
join key, once placeholder substitution is understood as the mechanism, is
**`(round, team_slot)`** — a snake draft has exactly one real pick per
`(round, team_slot)` pair, in both the recap and (when captured) the live
board, regardless of what got typed into either one. This ledger re-does
the comparison on that key.

## Classification method (per `(round, team_slot)` slot)

1. `NO_LIVE_RECORD` — the live capture has no entry for this slot at all
   (everything after where the live capture stopped, plus a few earlier
   gaps).
2. `EXACT_MATCH` — live player name equals the recap player name after
   light normalization (punctuation/suffix-insensitive).
3. `K_DST_UNREPRESENTABLE` — the recap's real pick was a K or D/ST and the
   live entry is neither. Confirmed structurally, not inferred: the live
   player-universe snapshot that was actually installed for this draft
   (`projections/2026/current.csv`, approved 2026-09-02T04:28:56Z, 608
   rows, `valid_until: 2026-09-03` — i.e. the real draft-day snapshot, not
   a later refresh) contains **zero** K or D/ST rows. NWR could not have
   represented these picks no matter what was searched.
4. `NAME_IDENTITY_MISMATCH` — recap and live names share a last name and
   first-initial but aren't the same string (the section 15 alias pattern:
   Cam Ward/Cameron Ward, A.J. Brown/AJ Brown, etc.). None found in this
   draft's mismatches, for what it's worth — worth knowing this dataset
   doesn't exercise that failure mode, so it isn't evidence identity
   aliasing is fine in general.
5. `OWNER_PLACEHOLDER_FOR_MISSING_PLAYER` — recap's real player is a
   non-K/DST skill player that does **not** appear anywhere in the
   608-player draft-day universe snapshot (checked directly, not guessed).
   Matches both examples the owner specifically remembered (Jonathon
   Brooks, MarShawn Lloyd) exactly, at exactly the `(round, team_slot)`
   this method predicts for them (rd6/slot14 and rd6/slot13) — independent
   confirmation the method lines up with actual memory, not just a
   plausible-looking story.
6. `SEARCH_FAILURE` — recap's real player **is** present in the same
   608-player universe snapshot, but a different player was entered
   instead. The player existed in NWR; something about finding or
   selecting it under draft-clock pressure failed. This label describes
   the observable fact (in-universe player not selected); it does not by
   itself distinguish a search-box bug from an operator error from time
   pressure — no signal in this data separates those, so don't over-read it
   as a specific bug report beyond "NWR did not get this player selected
   even though it had the data."
7. `UNKNOWN` — reserved, unused this pass (every mismatch had one of the
   objective signals above). Not forcing anything into it artificially,
   and not forcing anything *out* of it either — zero here is a real
   result of this dataset, not a default.

## Results (192 real draft slots)

| classification | count |
|---|---|
| EXACT_MATCH | 115 |
| NO_LIVE_RECORD (after live capture stopped) | 35 |
| SEARCH_FAILURE | 23 |
| K_DST_UNREPRESENTABLE | 14 |
| OWNER_PLACEHOLDER_FOR_MISSING_PLAYER | 5 |
| NAME_IDENTITY_MISMATCH | 0 |
| UNKNOWN | 0 |

Of the 157 slots the live capture actually reached, **42 (27%)** did not
correctly represent the real ESPN pick. That is a materially higher live
error rate than the raw "157/192 recorded" number suggests on its own.

## Direct defect evidence for this lane's requirements

- **K/DST support (section 17)**: 14/157 confirmed structural failures —
  the draft-day universe had no K/DST rows at all. This is the single
  largest confirmed failure category and directly motivates making K/DST
  full draftable assets.
- **Player universe completeness (sections 8, 15, 16)**: 5 confirmed
  missing-from-universe skill players, including two rookies (Jonathon
  Brooks, MarShawn Lloyd) the owner specifically remembered — consistent
  with the rookie-redraft-bias concern in section 8.
- **Search/selection reliability (section 11, "fast live capture")**: 23
  cases where the correct player existed in NWR but wasn't the one
  selected. This is the strongest single argument in this evidence set for
  the persistent RECORD NEXT PICK box with global (position-filter-
  ignoring) search that section 11 asks for.
- **Identity/alias registry (section 15)**: 0 confirmed cases in this
  dataset specifically, but see the caveat above — absence of evidence
  here isn't evidence the alias problem is minor; it just didn't happen to
  be the failure mode that produced *these* 5+23 mismatches.

## What is still not known

Which specific mismatches were "couldn't find it" vs. "ran out of time and
grabbed anyone" vs. some third cause is not separable from static data
alone. If the owner has memory of specific other picks (beyond Jonathon
Brooks / MarShawn Lloyd), those can be added as confirmed annotations
rather than inferred ones.
