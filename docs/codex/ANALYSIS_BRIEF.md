# Analysis Brief

## Decision
Help the Niners co-owner make Roster Declaration Day decisions for the Las Vegas Enginerds keeper/dynasty hybrid league: top-five release, best 23 keepers, drops, shop candidates, trade targets, likely league drops, and pick value.

## User
Primary user is the Niners co-owner reviewing the roster before keeper/drop deadlines, trade windows, and the supplemental draft.

## Outputs
- Niners official top five.
- Forced-release risk and default release candidate.
- Keeper, drop, trade, war, confidence, and risk scores.
- Recommendation labels: LOCK, KEEP, SHOP, DROP, TARGET, FADE, WAIT, RISK, HOLD, OFFER, CONSIDER, AVOID.
- Pick value table on the 1,000-point local scale.
- Trade Central tables split by private value, market value, keeper impact, opponent benefit, and acceptance chance.
- League keeper pressure table.

## Non Goals
- No live API dependency at app runtime.
- No web scraping.
- No complex ML in V1.
- No generic fantasy advice blog copy.
- No automatic offers, trades, or money movement.
- No auth, payments, deployment, or production integrations.

## Assumptions
- Official rank controls league top-five rules.
- Private/war scores control Niners strategy only.
- Data comes from local CSV/SQLite snapshots.
- Rank 400 is a warning/placeholder, not a hard truth.
- Unknown rules stay configurable.
