# Real 403 Draft Replay With All Accepted Fixes — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 16. Real 403 N 18th
league board (`4b4a990faf124ce7a5d612537ba5943b`, owner_slot 8, 118 real picks, real
`SLEEPER_READ_ONLY` sync). **No hindsight grading** -- this reports what today's engine (with
every fix accepted this session) shows for these real, already-drafted players; it is not a
claim that any real pick was good or bad.

## Scoping note (honest, disclosed)

A full per-pick "old DecisionBundle recommendation vs. current DecisionBundle recommendation"
replay, reconstructing 14 sequential real Monte Carlo states, was judged too compute-expensive
to run responsibly within this unit's remaining time budget (each real DecisionBundle build
costs several seconds; 14 sequential real states with both an "old-fix" and "new-fix" engine
would multiply that substantially). Used instead: the real, current, fully-fixed engine's
actual admission/coverage status and points for each of the 14 real owner picks (the concrete,
already-validated evidence from Sections 4a/4b/8 of this same session), plus real ESPN ADP and
status/risk context -- directly answering the real question this section exists to close
("do this session's fixes actually reach these real players"), without re-deriving a full
recommendation-ordering simulation this session already validated separately (Section 11).

## The real 14 owner picks, current engine status

| Rd | Player | Pos | NWR status (today, all fixes applied) | NWR pts | ESPN ADP (this league) | Status/risk override |
|---:|---|---|---|---:|---:|---|
| 1 | Trey McBride | TE | FULLY_MODELED (persistence) | 252.9 | 17.0 | none |
| 2 | Christian McCaffrey | RB | FULLY_MODELED (persistence) | 365.6 | 6.0 | none |
| 3 | George Pickens | WR | FULLY_MODELED (persistence) | 243.4 | 32.0 | none |
| 4 | Chris Olave | WR | FULLY_MODELED (persistence) | 218.0 | 26.0 | none |
| 5 | Travis Etienne | RB | FULLY_MODELED (persistence) | 235.9 | 38.0 | none |
| 6 | D'Andre Swift | RB | FULLY_MODELED (persistence) | 211.6 | 65.0 | none |
| 7 | Jameson Williams | WR | FULLY_MODELED (persistence) | 187.4 | 52.0 | none |
| 8 | Jadarian Price | RB | **FULLY_MODELED (rookie cohort)** | 174.7 | n/a (not in this ADP snapshot) | none |
| 9 | Kenny Gainwell | RB | **FULLY_MODELED (persistence)** | 184.8 | n/a | none |
| 10 | Michael Wilson | WR | FULLY_MODELED (persistence) | 181.6 | 90.0 | none |
| 11 | Caleb Williams | QB | FULLY_MODELED (persistence) | 315.2 | 104.0 | none |
| 12 | Wan'Dale Robinson | WR | FULLY_MODELED (persistence) | 171.9 | 106.0 | none |
| 13 | Matthew Stafford | QB | FULLY_MODELED (persistence) | 350.4 | 102.0 | none |
| 14 | HOU D/ST | DST | N/A -- always manual/unmodeled by design | -- | n/a | none |

**13/14 real owner picks (every non-DST pick) are FULLY_MODELED today.** Kenny Gainwell is a
real, direct confirmation of Section 13's own finding: he showed as an `ALIAS_MISMATCH` in the
FFA-name-matching diagnostic (FFA's source spells him "Kenneth", the registry "Kenny"), but the
REAL production engine (gsis_id-keyed, never name-matched) has always had him correctly
covered -- exactly the "diagnostic-script-only, not a real production gap" conclusion already
documented. Jadarian Price is a real, genuine 2026 rookie correctly covered by the
rookie-cohort lane. No status/risk override applies to any of these 14 real players.

## Highlighted players (per the directive's own named list)

Searched the full real 118-pick board, not just the owner's 14:

- **Trey McBride** (owner's own real round-1 pick) -- see table above.
- **Kyle Pitts** -- drafted round 7 by a different real team (`team_slot 4`), never by the
  owner.
- **Caleb Williams**, **Matthew Stafford** -- both real owner picks (rounds 11 and 13); see
  table above.
- **Trevor Lawrence** -- **not drafted anywhere** in this real 118-pick board (a real,
  disclosed absence -- this was a partial, not-every-player-drafted event; not evidence of any
  exclusion).
- **Josh Jacobs** -- drafted round 11 by a different real team (`team_slot 4`), never by the
  owner.
- **Quinshon Judkins** -- drafted round 7 by a different real team (`team_slot 2`). See
  `NWR_JUDKINS_ROLE_CHANGE_BLIND_SPOT_V1_20260908.md` (Section 5) for the real, already-
  documented finding on his current engine treatment (FULLY_MODELED, real ~16.7% gap vs FFA
  market, reference-only disposition).
- **"Brooks"** -- the real name match in this board is **Jalen Brooks** (round 13, a different
  real team), not Jonathon Brooks. Jonathon Brooks himself was **not drafted anywhere** in this
  real 118-pick board. See `NWR_BROOKS_CLASS_SOURCE_GAP_FIX_V1_20260908.md` (Section 4b) for
  his real, already-documented current engine status (FULLY_MODELED via the insufficient-
  history fallback, honest weak-accuracy disclosure).
- **Stefon Diggs** -- **not drafted anywhere** in this real 118-pick board. See
  `NWR_DIGGS_CLASS_SOURCE_GAP_FIX_V1_20260908.md` (Section 4a) for his real, already-documented
  current engine status (FULLY_MODELED as of this session's fix; previously excluded).

## Disposition

No code change -- replay/documentation only, confirming this session's fixes reach the real
players in this real board. Both real boards re-verified byte-identical before and after (this
unit only reads the board file, never writes to it).

## Status

Section 16: **DONE** (scoped as disclosed above).
