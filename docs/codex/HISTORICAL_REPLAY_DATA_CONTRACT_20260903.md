# Historical redraft replay — data contract for the Dataset Research Engine

Draft Upgrade HQ does **not** implement the Dataset Research Engine. This
is the consumer contract only: what this lane needs, in what shape, to
build the full-season leakage-safe redraft replay that
`docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md` found is
not buildable from data in this repo today.

## Required fields, by season and as-of date

For every player relevant to a target historical season Y, knowable **as
of that season's actual draft date** (not reconstructed with hindsight):

- **Identity**: a stable player_id, full name, and every name variant a
  real platform export might use for them that season (draft-scoped alias
  registry, same shape as section 15/16's live-draft identity work).
- **Team**: as of the draft date, including any team-code aliasing the
  provider used that season (LA/LAR, AZ/ARI, JAX/JAC-style).
- **Position**: as of the draft date.
- **Pre-season projection components**: whatever a real projection
  service published before that draft — not derived from season-Y
  results. If no real archived pre-draft projection exists for season Y,
  say so; do not backfill with a later model's projection.
- **Platform ADP**: as of the draft date, from the same platform the
  historical draft itself used.
- **Roster/depth/injury/availability status**: as of the draft date only
  (a player's real depth-chart/injury state at draft time, not what
  happened to them during season Y).
- **League scoring-format inputs**: whatever scoring rules the historical
  league actually used, so replayed picks can be valued under the real
  format, not today's default.

For scoring the replay only (never as a ranking input):

- **Weekly realized fantasy outcomes** for season Y, under the historical
  league's real scoring rules.
- **Actual games played / status** during season Y (injuries, benchings,
  etc.) — outcome data only.

## Minimum / preferred seasons

- Minimum: one full past season with both a real full snake-draft result
  (all rounds, all teams, veterans and rookies) and a genuinely dated
  pre-draft projection/ADP board. Fewer than this and no leakage-safe
  redraft replay is possible at all — this is what's currently missing
  (see the substrate inventory doc).
- Preferred: multiple consecutive seasons, so replay comparisons aren't
  dominated by one season's idiosyncrasies, and so a challenger evaluated
  against this replay can be chronologically train/validate/test split
  the way `docs/codex/CALIBRATION_PLAN.md` already requires elsewhere in
  this codebase.

## Leakage exclusions (hard requirement)

None of the following may be used as a *ranking input* for season Y,
ever, regardless of how it's sourced or labeled:

- realized season-Y stats or outcomes;
- injuries/depth-chart changes/trades learned after the draft date;
- current (present-day) NWR rankings or projections;
- future ADP (any ADP dated after the historical draft date);
- retrospective news/analysis written after the season.

This mirrors the existing `scripts/build_backtest_dataset_v{0,1}.py`
leakage guard's `BLOCKED_FEATURE_TOKENS` pattern (already real, tested,
and enforced in this repo for a different — player-production — backtest)
rather than inventing a new leakage-prevention convention.

## Validation checks the Dataset Research Engine should run before handoff

- Every pre-draft projection/ADP record's timestamp is strictly before
  the historical draft's actual date.
- No field in the pre-draft dataset can be shown to correlate with
  season-Y realized outcomes beyond what a genuinely-dated projection
  would explain (a basic leakage smoke test).
- Every real historical pick resolves to exactly one identity in the
  provided player set (or is explicitly flagged unresolved) — the same
  identity-completeness bar section 15/16 hold live drafts to.
- Row counts and season coverage are stated explicitly in the handoff
  (no silent gaps).

## What this lane does with it once available

Build the actual replay comparing PLATFORM ADP / GREEDY NWR / STANDARD VBD
/ CURRENT NWR HEURISTIC / TEAM SCORE optimizer / CHAMPIONSHIP EQUITY
optimizer (section 8 of the prior wave's brief), evaluated on realized
starter points, VOR, pick regret, replacement loss, and simulated
playoff/title rate — simulated schedules explicitly labeled SIMULATED,
never presented as observed historical titles.
