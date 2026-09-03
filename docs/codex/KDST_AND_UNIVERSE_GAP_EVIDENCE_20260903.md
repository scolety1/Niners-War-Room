# K/DST and player-universe-gap evidence for Lane C (2026-09-03)

Supports priority #2 (K/DST complete draftability) and #3 (missing-player/
universe coverage) from the KHA reconciliation priority addendum. Read
`sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.md` first for how the
14 K_DST_UNREPRESENTABLE and 5 OWNER_PLACEHOLDER_FOR_MISSING_PLAYER rows
were derived.

## What already exists (found, not built)

Owner-authorized draft-day prep already produced two usable external
snapshots under `C:\NWR_DRAFT_DAY_TOOLS\2026-09-02\udk\`, built by
`build_udk_snapshot.py` / `parse_udk.py` on 2026-09-02:

- `KHA_UDK_KDST_2026_SNAPSHOT.csv` — 64 rows, 32 K + 32 D/ST, full NFL
  coverage, `authority_label: EXTERNAL_UDK_UNMODELED_BY_NWR` already
  applied at the row level (matches the exact labeling this lane's brief
  requires for K/DST).
- `KHA_UDK_2026_SNAPSHOT.csv` — 315 skill-position rows, each carrying an
  `identity_status` of `MATCHED` (301) or `UNMATCHED` (14) against the NWR
  player universe, plus `nwr_player_id`, `match_method`, `match_confidence`
  columns from an existing (if informal) identity-reconciliation pass.

Both are owner-supplied draft-prep artifacts, not NWR-generated. Treat them
the same way section 20 (UDK badges) treats UDK data generally: real,
usable input, not something to silently promote into NWR's own modeled
authority.

## K/DST coverage check against the 14 historical K_DST_UNREPRESENTABLE picks

All 7 kickers and all 7 D/ST teams needed to make every historical
K_DST_UNREPRESENTABLE ledger row representable are present in
`KHA_UDK_KDST_2026_SNAPSHOT.csv`:

| ledger recap player | found in snapshot |
|---|---|
| Brandon Aubrey (K, DAL) | yes |
| Cameron Dicker (K, LAC) | yes |
| Jason Myers (K, SEA) | yes |
| Harrison Mevis (K, LAR) | yes |
| Jake Bates (K, DET) | yes |
| Eddy Pineiro (K, SF) | yes, as "Eddy Piñeiro" — correctly encoded, see correction below |
| Ka'imi Fairbairn (K, HOU) | yes |
| Texans / Broncos / Eagles / Ravens / Seahawks / Steelers / Rams D/ST | all 7 present by full team name |

**Data-quality defects found in this source, to fix before integration, not
work around silently:**
- `age`, `bye`, `finish_rank_2025`, `games_2025` are the literal string
  `"UNKNOWN_COUNT_MISMATCH"` for every one of the 64 rows — a column-
  alignment bug in the PDF/text extraction that built this file. Harmless
  for identity/draftability (name, position, team, `udk_position_rank` are
  intact and correct), but these fields should not be displayed as if they
  were real values.
- Earlier drafts of this doc claimed "Eddy Piñeiro" was mojibake-corrupted
  in this source CSV. That was wrong -- verified by reading the raw bytes
  directly: the source file correctly encodes it as UTF-8 (`\xc3\xb1` = U+00F1 "ñ").
  The real defect was diacritic-insensitive matching in this session's own
  search code (an operator typing "Pineiro," without the accent, found
  nothing) -- fixed in globalPickSearchRows (pages.tsx) by switching to the
  same normalizeCommandSearch helper the Ctrl+K command palette already
  uses (NFKD-decompose + strip combining marks + strip punctuation), which
  also fixes the A.J. Brown / AJ Brown class of alias for free. See
  RECONCILIATION_LEDGER.csv's 14/14 K/DST regression
  (test_all_14_historical_k_dst_picks_resolve_against_the_current_udk_source).

**Conclusion: K/DST priority #2's acceptance criterion (all 14 historical
K/DST picks representable) is achievable from data already on hand.** No
new K/DST modeling or scoring is implied or being proposed — per section 17,
these stay `EXTERNAL_UNMODELED_BY_NWR`, sourced from UDK + platform market +
factual status only.

## Missing-player coverage check against the 5 historical OWNER_PLACEHOLDER picks

All 5 (Jonathon Brooks, MarShawn Lloyd, Stefon Diggs, Tank Dell, Deebo
Samuel Sr.) are present in `KHA_UDK_2026_SNAPSHOT.csv` with
`identity_status: UNMATCHED` and empty `nwr_player_id` — i.e. real,
externally-known players that were never admitted into NWR's own 608-player
modeled universe (`GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv`,
draft-day snapshot). That confirms these are universe-admission gaps, not
search bugs — consistent with `SEARCH_FAILURE` being a separate ledger
category for players that *were* in the universe.

The same UNMATCHED list has **9 more** players beyond the 5 the historical
draft actually hit (this draft's live capture stopped mid-round-10, before
some of these would have come up): Deshaun Watson (QB), Najee Harris (RB),
Brashard Smith (RB), Jordan James (RB), Darren Waller (TE), Hollywood Brown
(WR), Keenan Allen (WR), Travis Hunter (WR — the same player section 16
separately flags for offensive-role uncertainty), and one row with garbled
`player_name_raw` (looks like corrupted commentary text merged into the
name field during extraction, not a real player row — needs a human to
resolve, not a guessed name).

**Proposed unified mechanism (not yet built):** rather than two separate
systems for "K/DST" and "missing skill player," both are the same shape of
problem — a real, externally-known player NWR has no model for — and can
share one `EXTERNAL_UNMODELED_BY_NWR` asset representation: stable
identity (name, team, position), external-source ranks/tiers where
available (UDK), and an explicit absence of any NWR-generated score. This
keeps section 17's "no invented NWR model scores" rule for K/DST and
naturally extends it to any future universe gap without a second bespoke
code path.

## What this does NOT establish

Not proposing NWR compute projections for these players — the opposite:
the whole point is representing them as draftable *without* inventing NWR
modeling for them, matching section 17's explicit instruction for K/DST.
Not asserting why the 9 additional UNMATCHED players are missing (rookie
status, injury/availability filtering, or something else) — that's
research for the actual universe-completeness audit (sections 8/15/16),
not asserted here.
