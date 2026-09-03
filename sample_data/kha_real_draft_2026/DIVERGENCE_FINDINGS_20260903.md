# KHA live runtime capture vs. official 192-pick recap — divergence findings

Compiled 2026-09-03, read-only, before any replay fixture merge work. This
documents a real discrepancy found while preparing the 192-pick historical
replay fixture requested for the KHA 2026 High Stakes League.

## RESOLVED — owner explanation (2026-09-03)

The divergence below is real and the measurements are correct, but the
speculative causes listed at the bottom of this file ("draft
reset/restart", "cross-contamination from a different draft_id") were
**wrong**. The actual mechanism, confirmed by the owner: when a real ESPN
pick could not be represented in NWR (missing from the player universe,
unsearchable, K/DST with no NWR model, etc.), the operator sometimes
entered a different, available NWR player as a placeholder just to advance
the live draft state. Neither source was corrupted or duplicated.

Resolution for downstream work:
- `official_recap_192picks_clean.csv` is authoritative for what actually
  happened in the real draft. Use it to build the historical replay.
- `live_runtime_draft_board_157picks.json` remains authoritative
  production evidence of NWR's own live behavior that night — including
  its failures — and is **not** to be rewritten or "corrected."
- See `RECONCILIATION_LEDGER.md` / `RECONCILIATION_LEDGER.csv` for the
  full slot-by-slot classification this produced (built on a
  `(round, team_slot)` join, not the pick-number join used below).

The rest of this file is kept as-is, unedited, as the original read-only
analysis that surfaced the discrepancy before the cause was known.

## Inputs compared

- `live_runtime_draft_board_157picks.json` — byte-identical copy of the real
  Tauri app's live draft board (`fb1c49402c7644a99120197d41344bbb.json`,
  SHA-256 `e51c0dfddea8369d35a2bf3f1e0c293fabb2c45cb9b30c0bb63495fcf3cec0e6`),
  populated by `actor: "SLEEPER_READ_ONLY"` polling. 157 picks recorded,
  stopping at `updated_at_utc: 2026-09-03T04:28:00Z`.
- `official_recap_192picks_raw.csv` — byte-identical copy of the owner's
  platform-exported draft recap (SHA-256
  `84322a9f1f64e4353a512e85fdcf07dd4195848ee2fb7509493120f4aa9a9232`), a
  complete, clean 16-team x 12-round snake draft (192 picks, no anomalous
  names, ends with the page's support-nav footer, not a real pick).

## Method

Matched every live pick to a player identity in the recap CSV (normalized
name match, punctuation/suffix-insensitive) rather than assuming the two
streams share pick-number indexing. See `official_recap_192picks_clean.csv`
for the parsed, tabular form of the recap used for this comparison.

## Finding: the two are NOT a clean 157-pick prefix + 35-pick suffix

Naively treating the live 157 picks as "the first 157 picks of the same 192"
and appending recap picks 158-192 would produce an internally inconsistent
fixture. The two streams agree exactly for picks 1-82, then diverge:

- **20 live-recorded picks have no matching player anywhere in the 192-pick
  recap at all** — pick numbers 83, 84, 86, 105, 107, 110, 112, 113, 133, 134,
  138, 139, 140, 143, 144, 145, 146, 148, 151, 156. All twenty are deep
  bench/practice-squad-caliber names (e.g. Justin Shorter, Julius Chestnut,
  Jacardia Wright, Lil'Jordan Humphrey, Simi Fehoko, Tyson Bagent, Thomas
  Fidone II, Dalen Cambre, Kedon Slovis, Jaylin Lane) that do not appear
  anywhere in the recap's real 192 selections.
- For the live picks that DO match a real recap player, the offset between
  the live `pick_number` and that player's true position in the recap grows
  from 0 (picks 1-82) to +1 (picks ~98-150) to +4, +18, +21 by the last three
  live picks (152, 154, 155, 157 vs. recap positions 156, 158, 173, 178).
- The growth in offset tracks the count of not-in-recap picks seen so far,
  consistent with ~20 extra pick-events being interleaved into the live feed
  that the final recap does not contain — not with 35 picks simply not yet
  having happened.

## What this is NOT being asserted as

Not asserting a cause. Plausible, unverified explanations include: a draft
reset/restart mid-draft that the live Sleeper polling captured pre-reset
autodraft/queue noise from (the recap CSV's own scraped page footer literally
includes a "Reset Draft" support link, which is circumstantial, not
evidence of it happening); a brief cross-contamination from a different
draft_id during polling; or something else. Not guessing further — this
needs the owner, who was in the room.

## What is safe to use right now

- `official_recap_192picks_clean.csv` — the full, real 192-pick draft, safe
  to use standalone for anything that only needs "what the final roster
  construction was."
- `live_runtime_draft_board_157picks.json` (+ `.backup.json`) — the real,
  unmodified production capture, safe to use standalone as evidence of what
  NWR's live sync actually recorded and when, including its own reliability
  gap.

## What is blocked pending owner input

Any single fixture that claims to be "the actual pick-by-pick sequence,
reconciled" — e.g. for cost-of-waiting / make-it-back-probability backtesting
that needs to know what was *actually available* at each real pick. Building
that today would require silently deciding which 20 live entries to discard
and how to re-align everything after pick 82, which is exactly the kind of
invented reconciliation this lane's brief says not to do.
