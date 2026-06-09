# Historical Rookie Draft Reconstructor Plan

## Source Clue

Andrew said old drafts were entered into Yahoo in order, and the last five picks in the draft results represent the rookie draft.

Newer league context: the league has moved from Yahoo to Sleeper, but the draft is offline. The owner has handwritten notes for the last four drafts, so transcribed offline rookie notes should be treated as the preferred source for those seasons.

Known limitation: Yahoo draft results do not account for traded picks, so the raw import can identify drafted players and apparent selection order, but not original pick ownership.

## Product Goal

Give the Niners co-owner a rough historical rookie draft record that can be reviewed before meetings and corrected manually later.

## Proposed Local Data Shape

Input CSV:

- `season`
- `overall_pick`
- `round`
- `slot`
- `team`
- `player`
- `position`
- `source`

Fixture path:

- `sample_data/historical_yahoo_drafts/final_five_two_seasons.csv`

Preferred handwritten/offline notes CSV:

- `season`
- `rookie_pick_number`
- `team`
- `player`
- `position`
- `source`
- `confidence`
- `provenance_note`
- `needs_traded_pick_review`

Fixture path:

- `sample_data/historical_rookie_notes/offline_notes_four_seasons.csv`

Derived rookie draft output:

- `season`
- `rookie_pick_number`
- `yahoo_overall_pick`
- `drafted_player`
- `drafting_team`
- `confidence`
- `provenance_note`
- `needs_traded_pick_review`

## Extraction Rules

Preferred rule for Sleeper/offline era:

- Transcribe handwritten rookie draft notes into the offline notes CSV.
- Preserve the recorded rookie pick number directly.
- Assign `confidence`: `handwritten_note`.
- Assign `needs_traded_pick_review`: true until original pick ownership is manually confirmed.
- Assign `provenance_note`: `Offline handwritten rookie draft note; verify traded-pick ownership manually`.

Fallback rule for Yahoo-era platform exports:

For each season, sort by Yahoo draft order and select the final five picks.

Assign:

- `rookie_pick_number`: 1 through 5 in final-five order
- `confidence`: `rough`
- `needs_traded_pick_review`: true
- `provenance_note`: `Yahoo final-five extraction; traded-pick ownership not preserved`

## Acceptance Fixture

Create a small two-season fixture where each season has more than five draft rows. Tests should prove:

- Exactly five rookie records are extracted per season.
- Rookie pick order follows Yahoo order.
- Confidence/provenance warning is present.
- The extraction is deterministic.

Implemented slice:

- `src/services/historical_draft_service.py` loads local Yahoo draft CSV exports and derives final-five rookie entries.
- `src/services/historical_draft_service.py` also loads transcribed offline handwritten rookie notes as preferred source records.
- `tests/test_historical_draft_service.py` pins two-season platform extraction, four-season offline notes loading, confidence labels, traded-pick review warnings, and deterministic ordering.
