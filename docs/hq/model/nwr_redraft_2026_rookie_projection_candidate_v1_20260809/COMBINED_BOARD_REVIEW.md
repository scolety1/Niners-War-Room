# Governed combined board review

The governed combined frame contains 530 approved veterans plus 78 owner-approved rookie
projections. Every one of the 17,490 veteran cells is exactly equal to the approved veteran input,
and the combined CSV preserves the complete veteran CSV as its exact byte prefix.

All four built-in presets generated READY rankings across all 608 players:

- `10_TEAM_1QB_STANDARD`
- `12_TEAM_1QB_HALF_PPR`
- `12_TEAM_PPR`
- `12_TEAM_SUPERFLEX_PPR`

All five profile sensitivity checks pass: Superflex raises QB value, TE premium raises TE value,
3WR lowers WR replacement, 12-team depth lowers QB replacement versus 10-team depth, and an extra
FLEX lowers WR replacement. Each preset contains 78 rookies, no duplicate IDs, and no K/DST rows.

The governed combined snapshot is installed and product-validated. Canonical Git adoption and the
final real-draft-readiness verdict remain conditional on an independent fresh-HQ review.
