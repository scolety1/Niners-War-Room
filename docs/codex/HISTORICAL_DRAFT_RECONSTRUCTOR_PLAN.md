# Historical Rookie Draft Reconstructor Plan

## Source Clue

Andrew said old drafts were entered into Yahoo in order, and the last five picks in the draft results represent the rookie draft.

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

Derived rookie draft output:

- `season`
- `rookie_pick_number`
- `yahoo_overall_pick`
- `drafted_player`
- `drafting_team`
- `confidence`
- `provenance_note`
- `needs_traded_pick_review`

## Extraction Rule

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

