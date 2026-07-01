# Replay Anchor Requirements

Every future NFLVerse replay candidate must provide a point-in-time snapshot manifest with:

- source dataset name and policy status;
- source version, extract timestamp, and local snapshot path or tracked summary;
- field-level as-of timestamp or publication timestamp;
- prediction anchor definition;
- season/week or event window;
- row grain and identity join key;
- identity gate and excluded/gated rows;
- missingness and censoring policy;
- source lag policy;
- future-week and post-outcome exclusion rules;
- leakage decision for the feature family;
- row counts by season, week, position, and gate status.

## Feature-Specific Requirements

- Rosters and weekly rosters need roster event timing, cutdown handling, practice squad/injured reserve treatment, and no future-survival backfill.
- Injuries and practice reports need report publication timing, practice day, game-week association, and missing-report semantics. They still cannot become injury-risk or medical projections.
- Schedules need release/update timestamps and postponed/rescheduled game handling.
- Depth charts need publication timestamp, team/week context, role semantics, camp/cutdown timing, and injury replacement handling.
- Snap counts and player stats need completed-game cutoff, source lag policy, sample windows, and target/future-game exclusion.
- Draft picks and combine need event date, publication date, draft-class identity, and pre/post-draft anchor split.
- Availability denominator fields need active/inactive hierarchy, bye/cancellation handling, rostered-game definition, and no inferred missed games.
- Identity bridge health is a gate only; identity confidence must not become a predictive feature.
