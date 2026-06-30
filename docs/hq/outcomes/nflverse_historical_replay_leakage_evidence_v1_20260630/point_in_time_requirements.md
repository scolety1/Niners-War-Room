# Point-In-Time Requirements

Verdict: `YELLOW_POINT_IN_TIME_REQUIREMENTS_DEFINED_NO_SNAPSHOT_BUILD`

This packet does not build point-in-time snapshots. It defines the minimum proof future lanes must produce before any NFLVerse field can be considered for replay or sandbox/shadow experiment review.

## Universal Snapshot Manifest

Every future candidate must provide:

- source dataset name;
- source version or snapshot date;
- extraction timestamp;
- field as-of timestamp;
- prediction anchor;
- season/week window;
- join key and identity gate;
- missingness policy;
- leakage block decisions;
- row counts by position and season;
- excluded or gated rows.

## Dataset Requirements

## Rosters And Weekly Rosters

Required proof:

- roster snapshot date before anchor;
- transaction or roster event timing;
- practice squad and injured reserve handling;
- roster cutdown handling;
- no future survival backfill.

## Injuries And Practice Reports

Required proof:

- report publication date;
- game-week association;
- practice day;
- status semantics;
- missing report semantics;
- no medical projection.

## Schedules

Required proof:

- schedule release or update timestamp;
- game date;
- opponent and bye state as of anchor;
- postponed or rescheduled game handling;
- no matchup-strength inference.

## Depth Charts

Required proof:

- depth chart publication timestamp;
- team and week context;
- role/rank semantics;
- camp/cutdown timing;
- injury replacement handling;
- no pre-draft use unless a future policy explicitly defines a post-draft-only anchor.

## Snap Counts And Last Active Fields

Required proof:

- completed game/week cutoff;
- lag policy;
- sample window;
- exclusion of target game and future weeks;
- censoring of future career survival.

## Draft Picks And Combine

Required proof:

- draft or combine event date;
- data publication date;
- draft class identity;
- post-draft-only status for draft capital;
- pre-draft or post-draft anchor split for combine.

## Player Stats Sidecar

Required proof:

- label or sidecar role;
- censoring policy;
- overlap with Outcome V2 labels;
- mismatch taxonomy;
- proof that sidecar is not an input feature.

## Contracts

Contract context remains display-only and non-model-eligible. No point-in-time evidence in this packet can convert it into player value, trade value, or model input.

## Identity Bridge Health

Identity bridge health is prerequisite evidence only. Future replay must exclude unresolved identity rows and must not treat identity confidence as a predictive feature.

## Availability Denominator

Required proof:

- rostered-game denominator;
- active/inactive hierarchy;
- bye and cancellation handling;
- snap/stat evidence rules;
- no inferred missed games from missing rows.
