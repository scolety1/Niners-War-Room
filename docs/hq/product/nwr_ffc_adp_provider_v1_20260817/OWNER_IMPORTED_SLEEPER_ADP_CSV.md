# Owner-Imported Sleeper ADP CSV

The existing generic local CSV import accepts player identity plus `position`, `team`, `adp`, `rank`, or `expected_pick`, and optional `source`, `date`, `format`, and `team_count` fields. Missing ADP stays unknown rather than becoming zero.

When a trusted owner file declares `source = Sleeper`, NWR labels it `Owner-imported Sleeper ADP` and gives it priority over FFC for the active profile. This label means owner-provided data; it does not claim a Sleeper API origin.

Imports remain local and require an owner action. The FFC provider does not depend on this override.
