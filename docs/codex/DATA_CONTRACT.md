# Data Contract

## Snapshots
Use frozen local snapshot folders such as `sample_data/2026_pre_declaration` and future `data_packs/YYYY_label` folders. Old data packs must not be overwritten.

## Canonical IDs
Player identity is anchored by `player_id`, with `merge_name` used for matching. Team identity is anchored by `team_id`; owner identity is anchored by owner/team fields from roster and pick files.

## Input Schemas
- `dim_players.csv`: player identity, position, NFL team, external IDs, active flag.
- `fact_rosters.csv`: snapshot date, season, league/team/owner, player, position, roster status, league rank, source.
- `fact_official_rankings.csv`: legacy source/rank metadata and league rank, including rank placeholder flag.
- `fact_future_picks.csv`: pick year, round, slot, label, original/current team, certainty.
- `fact_pick_values.csv`: overall pick, base value, future discount, certainty, declaration adjustment, final value.
- `model_outputs.csv`: private, market, war, keeper, drop, outcome, confidence, risk, recommendation.
- `metadata_sources.csv`: source and review metadata.
- Historical platform draft exports: local CSVs with `season`, `overall_pick`, `round`, `slot`, `team`, `player`, `position`, and `source`. These are fallback source fixtures/import inputs, not generated data packs.
- Historical offline rookie notes: local CSVs transcribed from handwritten notes with `season`, `rookie_pick_number`, `team`, `player`, `position`, `source`, optional `confidence`, optional `provenance_note`, and optional `needs_traded_pick_review`.
- Sleeper snapshots: local CSV exports produced by `scripts/import_sleeper_snapshot.py`. These may include Sleeper rosters, users/teams, league settings, draft metadata, and current traded-pick ownership. The Streamlit runtime should read local CSV snapshots rather than call Sleeper live.

## Real Data Templates

Implementation Phase F1 adds header-only templates under
`templates/real_data_inputs/`:

- `data_pack/`: app-ready V1 data pack CSV headers.
- `veteran_model/`: normalized veteran model input headers.
- `rookie_model/`: rookie source and normalization input headers.
- `historical_replay/`: calibration-only historical replay input headers.
- `public_sources/`: raw public-source staging headers for projections, market
  values, role/depth-chart hints, injuries, bio fields, and normalized veteran
  feature backfill.
- `nflverse_stats_upgrade/`: raw nflverse/statistical source headers and the
  normalized-feature bridge for the stats-first veteran model upgrade.

These templates are safe starting points for real league work. Copy them into
`local_exports/` or another ignored working folder before filling real data. The
committed templates are intentionally empty and are checked by
`src.services.real_input_template_service` so header drift is caught in tests.

Implementation Phase F2 adds Import Review coverage reports. Coverage is an
audit layer, not a scoring layer. The active pack is summarized across:

- required V1 CSV files,
- roster rows versus the configured declaration roster limit,
- league-rank coverage for rostered players,
- future-pick rows,
- real model outputs versus neutral placeholders,
- and reviewed source metadata.

Each coverage row carries `covered`, `expected`, `coverage_pct`, `status`,
`decision_blocking`, `detail`, and `next_action`. Blocking coverage gaps mean the
pack should not be used for money decisions. Review gaps mean the pack can load,
but the user should verify or refresh the affected source before trusting
recommendations. Coverage rows never feed back into player scores.

Public-source intake is a source-gathering lane, not a scoring lane. The
templates under `templates/real_data_inputs/public_sources/` let the user stage
locally exported rows from projection, market, role, injury, and bio sources
while Deep Research or manual source selection is still underway. The intake
validator checks headers, supported positions, booleans, numeric fields, and
normalized `0-100` feature backfill values. The Sources & Overrides page then
matches staged source rows against rostered `QB`, `RB`, `WR`, and `TE` players
by `player_id` first and player-name fallback second.

The V1 source policy lock accepts Sleeper, Fantasy Football Analytics,
DynastyProcess, and nflverse sources as the free/public backbone. Fantasy Nerds
and SportsDataIO are optional paid adapters only. KeepTradeCut scraping, raw
FantasyPros page scraping, and FantasyCalc as a required automated dependency
are rejected for V1. Unknown sources may be staged for review, but cannot be
treated as decision-ready until they are added to the policy with allowed and
forbidden uses.

Stage 3 upgrades the public-source templates to the Phase 11 report schema.
`public_source_catalog.csv` uses `source_id` and source-role metadata.
Projection, market, role, injury, and bio files use `player_key` plus
domain-specific source references such as `projection_source_id`,
`market_source_id`, `role_source_id`, `injury_source_id`, and `bio_source_id`.
`normalized_veteran_feature_backfill.csv` is a wide player-level bridge into
the veteran model features. The validator still tolerates the earlier starter
headers during transition, but committed templates are now the full contract.

Stage 5 adds source snapshot folders. A public-source snapshot is an ignored
local folder under `local_exports/public_source_snapshots/` containing a frozen
copy of every public-source CSV plus `source_snapshot_manifest.json`. The
manifest records snapshot id, creation time, source root, validation status,
row counts, file checksums, and the explicit scoring effect:
`none; raw source snapshot only`. Snapshot creation is blocked when the source
root has validation errors. Snapshots are reproducibility artifacts; they do not
normalize features, score players, or clear placeholder model outputs.

Stage 6 adds player-match review. Public source rows are matched against the
active data pack by local `player_id` / `player_key`, then supported platform
IDs, then normalized name plus position only when that name is unique. Ambiguous
and unmatched source rows are review items and must not be normalized into
veteran features until a safe identifier or alias is added. Matching rows are
audit output only; they do not change player value.

Stage 7 adds feature-normalization readiness. For each active V1 veteran feature,
the Sources & Overrides page shows whether the feature already has a normalized
backfill value, has matched raw source evidence ready to normalize, needs a
manual/local baseline, or is missing source data. This readiness table is a
normalization checklist only; it does not write `veteran_feature_scores.csv`,
run the veteran model, or alter `model_outputs.csv`.

Stage 8 adds normalization worklist exports. The Sources & Overrides page can
write an ignored local CSV under `local_exports/public_source_normalization_worklists/`
containing unresolved active-feature tasks from the readiness table. Each row
keeps the player, feature, required source type, current status, task label, and
next action. The worklist is a data-prep artifact only; it does not write model
feature scores, run the model, or change player recommendations.

Stage 9 adds a backfill acceptance gate. Normalized feature backfill rows are
classified as `accepted`, `review`, or `blocked` before a later model-run input
step can consume them. Accepted means a normalized `0-100` score exists with no
review flag; review means provenance/confidence still needs inspection; blocked
means source or normalization work is incomplete. This gate is still read-only:
it does not promote rows into `veteran_feature_scores.csv`, run scoring, or alter
recommendations.

Stage 10 adds accepted-backfill model-input candidate exports. Accepted rows can
be written under `local_exports/public_source_model_input_candidates/` in the
same column shape as `veteran_feature_scores.csv`, using
`source_key=public_source_backfill_candidate` and `source_confidence=derived`.
This is still a generated review artifact. It does not overwrite the live
veteran model feature file, run scoring, or clear placeholder recommendations.

Stage 11 adds model-input candidate validation. Candidate rows are checked against
the active data pack and veteran registry before any later isolated model-run
preview can consume them. The gate blocks unknown players, position mismatches,
unknown or inactive features, duplicate player-feature rows, invalid normalized
scores, rows marked missing, and rows marked as user overrides. Blank or
unrecognized provenance fields are review items. The gate is still read-only and
does not score players.

Stage 12 adds candidate coverage gating. Accepted candidate feature rows are
grouped by rostered player and active V1 feature requirements, producing
`complete`, `partial`, or `empty` coverage statuses. Only accepted rows count
toward coverage; review and blocked rows remain excluded. This prevents a later
isolated model preview from running on accidentally thin feature coverage.

These rows do not clear placeholder model outputs by themselves. A player remains
review-only until raw source rows are translated into normalized veteran feature
scores, scored by the veteran model, and emitted into `model_outputs.csv`.
Kickers and unsupported positions remain roster inventory only. League rank
remains a summer/declaration rule input and must not be used as a public-source
proxy for player quality.

Implementation Phase G1 adds a stricter historical replay data contract under
`templates/real_data_inputs/historical_replay/`. Historical replay is
calibration-only and must keep as-of model inputs separate from hindsight
outcomes:

- `platform_draft_exports.csv`: fallback platform draft exports for old final-five
  reconstruction.
- `offline_rookie_notes.csv`: preferred handwritten/offline rookie draft records.
- `model_replay_inputs.csv`: frozen as-of model ranks and scores only.
- `historical_outcomes.csv`: later outcome labels and outcome scores.
- `replay_source_catalog.csv`: source snapshot metadata and hindsight permission.
- `replay_audit_notes.csv`: manual replay notes and provenance.

The contract validator rejects missing headers, duplicate historical replay keys,
invalid numeric/boolean fields, unsupported positions, and any `outcome_score`
leak into as-of files. The Historical Replay page surfaces the contract coverage
report in its Schema tab. These reports never alter current War Board, Team,
Trade Central, or Draft Room scores.

## Validation Rules
Reject imports for duplicate rostered players, duplicated picks with multiple
owners, missing team IDs, missing player identity, invalid pick labels, roster
hard-limit violations without override, and inability to calculate each
Roster's League-Rank Top Five.

Warn for missing league rank, rank 400 placeholder, player not in `dim_players`, unknown owner/team, unknown position, missing market value, missing model output, and kicker inclusion.

## Missing Data
Missing features lower confidence and shrink outcome probabilities toward position/draft-cap priors. Missing league ranks remain visible warnings because league ranks control league rules during the summer/declaration workflow.

## Historical Rookie Draft Reconstruction

Historical offline rookie notes are preferred for Sleeper/offline seasons because the draft is not run through a live service. Every handwritten-note row should carry `confidence=handwritten_note`, the provenance note `Offline handwritten rookie draft note; verify traded-pick ownership manually`, and `needs_traded_pick_review=true` until original pick ownership is manually confirmed.

Historical platform draft results can still be modeled locally by sorting each season by draft order and extracting the final five picks as rough rookie draft entries. Every reconstructed platform row must carry `confidence=rough`, the provenance note `Platform final-five extraction; traded-pick ownership not preserved`, and `needs_traded_pick_review=true` because platform results do not preserve traded-pick ownership.

## Sleeper Snapshot Refresh

Use `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\import-sleeper-snapshot.ps1` to create an ignored local snapshot under `local_exports/sleeper/`. Sleeper owns current roster and pick state, but Sleeper rank should not be used. Sleeper does not provide the league paper's league ranks, so exported roster rows leave `league_rank` blank until the local ranking sheet or paper notes are merged. League rank is a summer/declaration input for the Roster's League-Rank Top Five rule and draft-prep decisions, not a year-round rookie-talent signal.

For the March 31, 2026 LVE roster PDF, the league rank provenance is FantasyPros February 27, 2026. Known roster/rank merge aliases: `Bam Knight` equals `Zonovan Knight`, `DontayvionWicks` equals `Dontayvion Wicks`, and `RhamondreStevenson` equals `Rhamondre Stevenson`. If a player appears as a PDF free agent but is rostered in Sleeper, keep Sleeper ownership as the current-state truth and use the PDF only as a league-rank source, with a review note.

Use `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\merge-lve-roster-ranks.ps1 --sleeper-rosters <local_exports path>\sleeper_rosters.csv --rank-text <extracted roster pdf text> --output-dir <local_exports merged path>` to repeatably merge the paper ranks into a Sleeper roster snapshot. The merge outputs are ignored generated files; commit only the merge logic, docs, and tests.

Build Phase 9 adds a controlled refresh workflow to the Import Review page. The buttons may:

- refresh a Sleeper API snapshot into `local_exports/sleeper/`,
- merge the local March 31, 2026 roster-PDF text into that snapshot,
- or run both steps as one full refresh.

No live Sleeper calls happen during scoring or normal board calculation. The API boundary is the explicit refresh button only; downstream pages should consume the generated local CSVs. The refresh workflow records status rows, row counts, output paths, and warnings. It always warns that league rank is a summer/declaration input only and that Sleeper roster/pick state remains current ownership truth. If the local rank text file is missing, the Sleeper snapshot still writes and the rank merge is skipped rather than silently inventing ranks.

Build Phase 10 adds data-pack promotion from refreshed local outputs. The Import Review page can now build a complete ignored data pack under `local_exports/data_packs/` from:

- a Sleeper snapshot folder,
- an optional merged league-rank folder,
- and generated neutral model-output placeholders.

The promoted data pack writes every required V1 app CSV: `dim_players.csv`, `fact_rosters.csv`, `fact_official_rankings.csv`, `fact_future_picks.csv`, `fact_pick_values.csv`, `model_outputs.csv`, and `metadata_sources.csv`. League ranks from the PDF merge are stored in the legacy-compatible `official_rank` columns for the current app schema, but the provenance notes still identify them as LVE league ranks. If no merged rank folder is supplied, the builder uses raw Sleeper rosters and leaves ranks blank with an explicit warning. The generated `model_outputs.csv` is neutral placeholder data only; it exists so the app can open the pack immediately while still forcing model review before keeper decisions.

Build Phase 11 adds an app-wide data-pack selector. The sidebar now discovers committed sample packs and generated local packs under `local_exports/data_packs/`, validates each pack, shows snapshot/error/warning counts, and stores the selected pack in Streamlit session state. Command-board pages should use the selected session pack instead of hard-coded config defaults. This does not rewrite source config and does not promote generated files into git; it is only a local runtime selection layer.

Build Phase 12 adds selected-pack health reporting. Import Review now turns schema validation into operational readiness checks:

- schema and cross-file validation,
- roster coverage against the declaration roster limit,
- league-rank coverage for Required Top-Five Release Slot safety,
- future-pick coverage for Draft Room usefulness,
- neutral placeholder model-output detection,
- and source-review status.

Readiness is `blocked` when top-five/rank or schema safety is broken, `review` when the pack loads but still contains placeholders or unreviewed sources, and `ready` only when the selected pack has ranks, picks, reviewed sources, and non-placeholder model outputs. This health label is also surfaced in the sidebar so the active pack's trust level follows the user across pages.

Build Phase 13 cleans up user-facing rank terminology. The current V1 CSV schema still uses legacy `official_rank` and `fact_official_rankings.csv` field names for compatibility, but app copy, table labels, validation messages, and model-audit language should call this value **league rank**. In LVE, league rank is the summer/declaration ranking input used for the Roster's League-Rank Top Five rule; it is not a generic official projection and should not be confused with Sleeper rank.

Build Phase 14 adds `league_rank` as a first-class compatibility field. New data packs may provide `league_rank` directly in roster/ranking CSVs, while older packs with only `official_rank` still load. Validators, health checks, generated packs, DB schema, and command-board joins should prefer `league_rank` and fall back to legacy `official_rank` only when needed.

Build Phase 15 adds selected-pack diffing. Import Review can compare the active candidate pack against another discovered data pack and summarize:

- roster additions,
- roster removals,
- player team moves,
- league-rank changes,
- and future-pick owner changes.

This comparison is intentionally local-only and uses validated CSV rows from the two packs. It is meant to catch the practical risks after a Sleeper refresh: surprise roster movement, stale or changed rank values, and traded-pick ownership changes before those values flow into keeper, trade, and draft decisions.

Build Phase 16 adds data-pack admission. Admission combines pack health with optional baseline diff risk and produces a single local verdict:

- `blocked`: schema/rank safety is broken and the pack should not be used for money decisions.
- `review`: the pack loads, but neutral placeholders, validation warnings, roster movement, rank changes, or pick-owner changes need human review.
- `ready`: pack health and comparison checks are clear enough for local draft-room use.

Admission reports must include explicit reasons and actions, not just a color or score. This keeps the workflow honest after refresh: do not trust a newly generated pack simply because it exists; admit it only after ranks, outputs, sources, and changed assets have been reviewed.

## Source Catalog Governance

Implementation Phase C1 upgrades veteran source provenance from a flat source list
to a domain-aware catalog. `veteran_source_catalog.csv` keeps the legacy
`source_key` and `source_type` columns used by feature rows, but also records:

- source family and domain,
- authority tier,
- active priority rank within that domain,
- run modes that require the source,
- freshness window,
- source format and local path,
- captured/effective dates,
- season and scoring context,
- checksum/parser metadata when available,
- active status.

Market-rank and projection sources must carry `scoring_context`. This is what
keeps a generic dynasty market export from silently becoming LVE private value.
Active `priority_rank` values must be unique within each `source_domain`, because
source precedence is domain-specific: Sleeper can be authoritative for league
state while the league-rank document is authoritative for Required Top-Five
Release Slot logic.

Implementation Phase C2 applies the Phase 9 confidence policy to veteran outputs.
Veteran confidence now uses:

- `40%` feature completeness,
- `25%` source reliability, blending authority/reliability and row confidence,
- `20%` source freshness, using the catalog's `freshness_window_hours`,
- `15%` signal agreement,
- explicit deductions for missing scored inputs and manual overrides.

Generated `model_outputs.csv` rows may include `warning_status` and
`warning_reasons`. Warning status values are:

- `ready`: no active confidence or model warning.
- `data_warning`: score is usable, but missing/stale/low-target confidence needs review.
- `model_warning`: score is usable, but LVE replacement, role, or keeper fragility needs review.
- `review_needed`: score should not drive an action without inspecting the reason.
- `blocking`: confidence is too low for decision use.

Warnings do not silently change player value. They explain whether the output is
decision-safe, review-only, or blocked.

Implementation Phase C3 tightens manual override guardrails. Veteran overrides
are feature-level only and may not target generated scores. An active override
must include:

- `old_value` and `override_value`,
- `override_type` and `reason_code`,
- source evidence,
- plain-language reason and provenance,
- requester and approver,
- explicit `self_approved=true` when requester and approver match,
- `review_status=approved`,
- a matching `veteran_audit_notes.csv` row with `affects_score=true`.

Inactive or expired overrides may remain in the file as audit history and may
share a target with the current active override. Multiple active approved
overrides for the same player-feature-field are rejected.

## Replacement Baselines

Implementation Phase D1 adds explicit LVE replacement baselines under
`sample_data/replacement_baselines/lve_replacement_thresholds.csv`. The app now
keeps two replacement contexts separate:

- `steady_state`: normal keeper and trade decisions before declaration supply is
  known.
- `declaration_window`: offline draft and post-declaration comparisons after
  released veterans and free agents can enter the pool.

Replacement value is a `0-100` gap score from model-derived positional rank, not
from league rank. League rank remains a summer/declaration rule input for top-five
release exposure, and must not become a hidden player-quality score.

Each baseline row defines `elite_anchor_rank`, `weekly_replacement_rank`, and
`stash_threshold_rank` for `QB`, `RB`, `WR`, and `TE`. Scoring maps the elite
anchor to `85`, the weekly replacement threshold to `50`, the stash threshold to
`20`, and players more than six slots worse than stash to `0`, with linear
interpolation between those anchors. Missing or unsupported positional rank
neutralizes to `50` for review rather than inventing certainty.

## Unified Asset Conversion

Implementation Phase D2 routes veterans, rookies, current picks, future picks,
released veterans, and free agents through one conversion contract:

- `replacement_value`
- `win_now_value`
- `dynasty_hold_value`
- `trade_liquidity_value`
- `keeper_adjusted_value`
- `all_asset_value`
- `acquisition_value`

Each asset type is first adapted into normalized intermediary scores:
`private_base_score`, `year1_score`, `long_horizon_score`, `age_curve_score`,
`format_fit_score`, `role_security_score`, `replacement_gap_score`,
`public_market_score`, `liquidity_score`, and `confidence_score`. The same
formula then computes the final components for every asset type.

Public market values are capped before they enter trade liquidity. Imported
market scores receive an LVE format adjustment of `-12` for QB and `-8` for TE,
then may not exceed private LVE value by more than `12` points. This prevents
generic dynasty markets from sneaking Superflex, PPR, or TE-scarcity assumptions
into the private board.

Current picks are treated as flexible post-declaration options, not rookie-only
coupons. Future picks use the local year-discount schedule from the conversion
service. Released veterans and free agents receive only accessibility bonuses;
their football value still comes from the same veteran model and replacement
baseline math.

`acquisition_value` is the draft-room comparison score. It starts from
`all_asset_value`, then adjusts for current cost, accessibility, roster spot cost,
package penalties, consolidation, and liquidity. Under draft pressure, compare
assets by acquisition value first, then inspect confidence and component scores.

Implementation Phase D3 moves pick and package heuristics into local CSV config
under `sample_data/asset_conversion/`:

- `lve_pick_heuristics.csv`: future-pick year discounts, current-pick
  optionality bonuses, and pick-equivalent bands.
- `lve_package_heuristics.csv`: extra roster-spot cost, consolidation credit,
  and stud-tax tiers.

These are model-design knobs, not evidence constants. Changing the CSVs changes
future-pick discounts, pick labels, package penalties, and consolidation math
without editing scoring code. The app still uses the same unified conversion
contract from D2; D3 simply makes the draft-room heuristics auditable and
calibratable.

## Forced-Release Strategy

Implementation Phase E1 separates the LVE Roster's League-Rank Top Five rule
requirement from strategy recommendations. This means the five highest
league-ranked players on each roster, not league ranks 1-5 overall. League rank
is a rule signal, not player quality. The strategy layer then uses model scores,
confidence, trade urgency, and unified acquisition value to decide whether to:

- keep the non-required roster top-five players,
- shop a default rule cut before declaration,
- release the default rule cut,
- review trading a non-forced player instead,
- reacquire an own released player in the offline draft,
- or target an opponent's default release.

Forced-release outputs include:

- `forced_release_pressure_score`
- `forced_release_candidate_score`
- `trade_urgency`
- `reacquisition_priority`
- `opponent_release_target_score`
- `strategy_reason`

The `rule_requirement` field is the legal/declaration answer; `action`,
`draft_action`, and `strategy_reason` are the model's strategic recommendation.
Those concepts should stay visually separate in Team, League Intel, and Draft
Room views.

Implementation Phase E2 adds test-backed explanation fields so the strategy can
be reviewed under pressure without reverse-engineering the formula columns:

- `rule_explanation`: why the player does or does not satisfy the Top-Five Rule
  Status.
- `score_explanation`: compact score trail behind the strategy action.
- `action_label`: combined declaration/draft-room action when both apply.
- `next_step`: the practical next thing to do before declaration or draft.
- `team_explanation`: team-level summary of pressure and market review needs.
- `decision_status`: team-level status such as `no_forced_release`,
  `review_market`, or `trade_before_declaration`.

These are explanatory outputs only. They must not feed back into player value,
drop score, keeper score, or league-rank exposure.

## Rookie Model V1

The V1 rookie model follows the Phase 5 simplification rule: commit source-of-truth CSVs and generate derived outputs. The committed source tables live under `sample_data/rookie_model_v1/`:

- `rookie_prospect_inputs.csv`
- `rookie_feature_registry.csv`
- `rookie_normalization_rules.csv`
- `rookie_raw_metrics.csv`
- `veteran_opportunity_assets.csv`
- `veteran_opportunity_benchmarks.csv`

Do not commit `rookie_feature_scores.csv` or `rookie_model_outputs.csv`; those are generated artifacts. Use `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-rookie-model.ps1` to run the sample V1 model and write generated board output under ignored `local_exports/rookies/`.

Build Phase 6 adds the rookie intake contract. Before trusting a rookie board, run the intake report from the Rookie Board page or `src.services.rookie_intake_service`. Intake checks:

- required source CSVs exist,
- `player_id` values are stable lowercase slugs and unique,
- `position` and `model_mode` use supported enums,
- every V1 core feature is either a normalized `0-100` score or visibly missing,
- each scored feature has feature-specific provenance or row-level source metadata,
- post-draft rows either have `rookie_opportunity_score` or show a warning,
- rows with three or more missing core features are blocked from model output.

Build Phase 7 adds deterministic normalization tables. Raw metrics stay separate from score-ready inputs. `rookie_normalization_rules.csv` maps each V1 feature to a raw metric, transform type, direction, and fixed bounds. `rookie_raw_metrics.csv` is a source table for raw values. Use `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\normalize-rookie-inputs.ps1` to generate normalized rookie inputs under ignored `local_exports/rookies/`.

Normalization rules must be monotonic and bounded:

- `draft_pick_curve`: lower overall NFL pick is better, with a nonlinear early-pick curve.
- `linear` + `higher_better`: `min_raw` maps to 0 and `max_raw` maps to 100.
- `linear` + `lower_better` or `younger_better`: `min_raw` maps to 100 and `max_raw` maps to 0.
- values outside the fixed bounds are clamped to `0-100`.
- missing raw values generate missing normalized features rather than hidden average scores.

V1 core features are intentionally small and composite-based:

- QB: `draft_capital`, `rushing_profile`, `passing_efficiency`, `sack_avoidance`, `age_trajectory`
- RB: `draft_capital`, `workload_earning`, `rush_efficiency`, `receiving_impact`, `goal_line_power`, `age_trajectory`
- WR: `draft_capital`, `target_earning`, `efficiency_dominance`, `age_trajectory`, `chain_moving`
- TE: `draft_capital`, `receiving_efficiency`, `route_role`, `production_volume`, `athletic_size`, `age_trajectory`

The veteran opportunity layer is an external board-management overlay. It is applied after the rookie internal score is computed and does not mutate `main_prospect_score`. Post-draft opportunity is also isolated from `main_prospect_score`.

Build Phase 8 adds actual veteran/free-agent benchmark derivation. `veteran_opportunity_assets.csv` is the preferred source when present. It contains active released veterans, free agents, and optional benchmark-only rows with `lve_veteran_score`, `win_now_score`, `hold_value_score`, and `trade_liquidity_score`. Protected or inactive rows do not enter the benchmark calculation.

The benchmark derivation rules are:

- QB compares against the average of the top 3 active available QB assets.
- RB compares against `70%` top-6 same-position RB pool and `30%` top-10 RB/WR/TE flex pool.
- WR compares against `70%` top-8 same-position WR pool and `30%` top-10 RB/WR/TE flex pool.
- TE compares against `55%` top-3 same-position TE pool and `45%` top-10 RB/WR/TE flex pool.

If `veteran_opportunity_assets.csv` is absent, the model falls back to static `veteran_opportunity_benchmarks.csv` bands. In both modes, the veteran benchmark is an external opportunity-cost overlay only; it must never change rookie `main_prospect_score`.

## Public-Source Veteran Preview

Stage 13 adds an isolated preview lane for public-source veteran inputs. The
preview runner consumes only validated accepted candidate rows for players with
complete active V1 feature coverage, builds a temporary veteran-model input
folder, and writes `veteran_model_preview_outputs.csv` plus a manifest under
ignored `local_exports/public_source_model_previews/`.

This is a decision-safety boundary: the preview does not overwrite the active
data pack, `sample_data/veteran_model_v1`, committed model inputs, or live app
recommendations. Incomplete players remain blocked from preview rather than
being silently neutralized into money-decision scores.

Stage 14 adds a review gate on top of those preview outputs. Preview rows are
classified as `ready`, `review`, or `blocked` using warning status, confidence,
risk level, missing-data penalty, and schema-warning count. This gate is
review-only: `ready` means the row can be compared against the current live
model output, not that it should be promoted automatically.

Stage 15 adds the preview-vs-live comparison contract. The comparison reads the
selected pack's current `model_outputs.csv` and isolated preview rows, then
reports keeper/drop/confidence deltas plus a `ready`, `review`, or `blocked`
comparison status. Material score movement, missing live baselines, or blocked
preview rows stay review-only and must not mutate live recommendations.

Stage 16 adds the promotion-candidate export contract. Only rows with
`comparison_status=ready` may be written to
`local_exports/public_source_model_promotion_candidates/` as a
`model_outputs`-shaped CSV plus manifest. The export is ignored and read-only
with respect to the selected pack; it is a final review artifact, not live
promotion.

Stage 17 adds the promotion-candidate review contract. Candidate exports are
rechecked against the currently selected pack and classified as `ready`,
`review`, or `blocked`. Missing candidate CSVs, missing player IDs, missing
source-preview provenance, stale live baselines, and material keeper/drop or
confidence movement must be resolved before any later explicit apply workflow.

Stage 18 adds the explicit apply-to-copy contract. Applying promotion candidates
must copy the selected pack to a new generated folder under
`local_exports/data_packs/` and update only `model_outputs.csv` rows that pass
the Stage 17 `ready` gate. The selected source pack is never overwritten. If
multiple ready candidates exist for the same player, apply is blocked until the
duplicate is reviewed.

Stage 19 adds the applied-pack admission contract. Generated applied packs are
validated after creation and classified as `ready`, `review`, or `blocked`.
Validation errors, missing model outputs, or zero applied rows block the pack.
Validation warnings keep the pack in review. This gate is read-only and does
not make a generated pack active automatically.

Stage 20 adds the applied-pack catalog contract. Any data pack with a
`model_applied_pack_manifest.json` must expose its generated-pack admission
status in the data-pack catalog and sidebar selector. The label is informational
and does not override the normal Import Review admission gate, but it prevents a
generated applied pack from being selected without visible context.

Stage 21 adds the selected applied-pack notice contract. When the active pack is
a generated applied pack, the sidebar must display the admission reason and next
action. A `ready` generated pack still points the user to final Import Review; a
`review` or `blocked` pack must say why it should not yet drive money decisions.

Stage 22 adds the applied-pack Import Review contract. The formal admission
service must read `model_applied_pack_manifest.json` when present and include it
in the decision. Zero applied rows, missing usable model outputs, or validation
errors are blocking conditions. Remaining pack-health review issues keep the
generated pack in review even if the manifest exists.

Stage 23 adds the draft-freeze admission contract. A final draft-day freeze must
require both normal trust readiness and Import Review admission readiness.
Non-ready packs may be frozen only as explicit review snapshots, and metadata
must record `review_snapshot=true` plus the admission decision so the artifact is
not mistaken for a money-decision board.

Stage 24 adds the human-readable freeze label contract. `DRAFT_DAY_README.txt`
must identify the artifact as either `FINAL DECISION BOARD` or
`REVIEW SNAPSHOT - NOT A FINAL BOARD`, include the admission decision, and state
the use policy in plain language.

Stage 25 adds the money-decision certificate contract. Every freeze must export
`board_exports/money_decision_certificate.csv` with one row containing
`money_decision_status`, `can_use_for_money_decisions`, `artifact_type`,
`trust_status`, `admission_decision`, and `next_action`. This row is the compact
machine-readable answer to whether the freeze is safe to use as the final board.

Stage 26 ties the public-source intake workflow together in the Sources &
Overrides readiness checklist. The checklist must now show the whole guarded
handoff: raw exports, player matching, feature normalization, real model-output
status, model-input candidate export, isolated preview, preview review,
promotion candidate export, and generated applied-pack review. These rows are
status/explanation only; they do not overwrite live model inputs, run scoring,
promote outputs, select a generated pack, or clear final money-decision gates by
themselves.

## NFLVerse Stats Upgrade

Implementation NFLVerse Upgrade Phase 1 adds a dedicated schema/docs lane under
`templates/real_data_inputs/nflverse_stats_upgrade/` and
`docs/codex/NFLVERSE_STATS_UPGRADE_SPEC.md`. The committed CSVs are header-only
contracts for player stats, snap counts, participation, depth charts, injuries,
identity mapping, projection imports, opportunity features, and normalized
veteran features.

These files are not live scoring inputs yet. Later phases must explicitly fetch
or import local source exports, validate identity matches, derive LVE scoring,
normalize `0-100` features, generate preview-only model outputs, and apply a
copied pack before app-visible recommendations can change. Market data remains
outside `private_lve_value`, and league rank remains a forced-release rule input
only.

NFLVerse Upgrade Phase 2 adds the identity bridge validator. Ready identity rows
must be deterministic and reviewed before source rows can be joined to rostered
players. The bridge prefers local `player_id`, then Sleeper, GSIS, FantasyData,
ESPN, PFR, and finally name/position/team fallback. Fallback or ambiguous rows
are review/blocking rows, not scoring inputs.

NFLVerse Upgrade Phase 3 adds the raw nflverse import contract validator for
player stats, snap counts, participation, depth charts, and injuries. Raw import
readiness is schema-only and has no scoring effect. Header-correct raw files are
eligible for later derivation phases; they do not update normalized features or
model outputs by themselves.

NFLVerse Upgrade Phase 4 adds LVE weekly scoring derivation from raw
`nflverse_player_stats_weekly.csv`. It applies local LVE scoring rules with no
PPR, 3-point passing TDs, 4-point rushing/receiving TDs, and the 0.4
rushing/receiving first-down bonus. The derived rows are generated scoring
evidence only and must not mutate live model outputs.

NFLVerse Upgrade Phase 5 adds role and usage derivation from raw stats, snap
counts, participation, and depth charts. The route field is explicitly a route
participation proxy, not a paid-route-charting replacement. TE role security is
capped when route role is weak because no TE premium makes blocker-heavy profiles
less actionable in LVE.

NFLVerse Upgrade Phase 6 adds injury durability derivation from injury reports
and weekly activity signals. Current out/doubtful reports, repeated same-area
events, missed-game proxies, and practice limits reduce durability and
confidence. RB/WR lower-body injuries receive heavier penalties than QB
lower-body injuries. Missing injury rows reduce confidence but do not create a
fake injury penalty.

NFLVerse Upgrade Phase 7 adds projection import rescoring. Legal projection stat
exports in `projection_raw_import.csv` are converted to local LVE projected
points with no PPR, 3-point passing TDs, 4-point rushing/receiving TDs, and
0.4 rushing/receiving first-down points. Missing projected first downs are
estimated from position-level rates with warnings and confidence penalties.
Projection rows remain derived evidence only until a later normalization/model
preview/apply workflow consumes them.

NFLVerse Upgrade Phase 8 adds normalized veteran feature derivation. The service
combines derived scoring, role, injury, and projection evidence into
`lve_normalized_veteran_features.csv` with `0-100` scores, warnings, confidence,
and missing-data penalties. Phase 9 rebuilds those normalized stats around the
final football buckets: production, opportunity, role, efficiency,
first-down/TD fit, age window, and injury durability. The companion
`lve_normalized_feature_receipts.csv` is long-form audit evidence: every feature
row has a raw value, normalized value, source key, warning status, missing flag,
and imputation value when applicable. Market fields are explicitly excluded from
these private/stat buckets and remain trade-liquidity only. These rows are still
preview-only and do not replace the active veteran feature file or app-visible
model outputs.

NFLVerse Upgrade Phase 9 adds the stats-first veteran formula engine. The engine
scores normalized rows into isolated `veteran_lve_stats_first_v1_0_0` outputs:
`private_lve_value`, `keeper_score`, `drop_candidate_score`, `trade_value`, and
confidence. `private_lve_value` is football/stat only. Market liquidity is
blocked from private value, capped to a `+/-2.5` keeper-score nudge, and reserved
primarily for `trade_value`. The engine is still not an apply step; Phase 10 must
show preview output before any later workflow can promote results into live app
model files.

Market Influence Lock adds a shared policy boundary: public market/crowd data has
`0%` weight in private/stat value and fallback keeper scoring. It may appear only
as trade liquidity, trade value, or market edge. Any blended board score that
includes trade liquidity must be capped around its football-value anchor so a
market spike cannot silently outrank the stat model.

RB Formula Rebuild separates running back scoring into `win_now_value` and
`dynasty_hold_value`. Short-term role, projection, and expected points can drive
win-now value, but private/keeper value must also pass the dynasty hold lane:
age window, injury durability, workload fragility, and portable skill. First
down/TD fit remains rewarded for LVE, but it is capped when age or durability
make the role fragile. A role-only RB cannot become RB1 without a strong dynasty
window.

WR Formula Rebuild also separates `win_now_value` from `dynasty_hold_value`.
Wide receiver win-now value rewards target earning, route role, recent LVE
production, expected points, projection, efficiency, and first-down/TD fit.
Dynasty hold value leans harder into portable target earning, route role,
age-adjusted value, production stability, and efficiency. Weak target earning
or unstable route role creates risk flags and dynasty penalties, while market
liquidity remains excluded from private/stat value.

QB Formula Rebuild separates quarterbacks into `win_now_value` and
`dynasty_hold_value` while applying a 10-team 1QB replacement baseline.
Quarterback rushing is start-gated: rushing upside only helps meaningfully when
the player also has secure starts. Elite dual-threat or truly elite passing
profiles can clear the 1QB exception, but normal pocket starters and uncertain
rushing backups are suppressed toward replacement-level value so they do not
crowd out similar-tier RB/WR assets in LVE.

TE Formula Rebuild separates tight ends into `win_now_value` and
`dynasty_hold_value` with no-TE-premium suppression. Route participation and
target earning are mandatory before a TE can clear the elite exception. Useful
but non-elite starters are capped near replacement, and blocker/low-route
profiles receive no-premium penalties and risk flags. Generic TE scarcity,
market heat, or positional scarcity fields cannot directly inflate private/stat
value.

Cross-Position Rebalance adds the LVE board layer on top of position-specific
football scores. The shared replacement baselines are QB `76`, RB `72`, WR `72`,
and TE `69`, with row-level override fields allowed for future calibration.
Lineup-demand adjustment rewards WR/RB profiles that clear real role/skill
checks because LVE starts 3 WR, 2 RB, and 2 flex. Non-elite QB and TE profiles
receive additional board suppression because this is 10-team 1QB with no TE
premium. Stats-first preview outputs now include `overall_rank`,
`position_rank`, `position_rank_label`, `cross_position_replacement_baseline`,
`lve_lineup_demand_adjustment`, and `rank_audit` so the board order is
inspectable.

NFLVerse Upgrade Phase 10 adds preview-only stats-first model output artifacts.
`create_stats_first_model_preview` reads `lve_normalized_veteran_features.csv`
and writes a separate preview folder with a manifest, output CSV, and feature
contribution CSV. Preview helpers expose snapshot rows and review-gate rows. This
phase still does not write selected packs, live `model_outputs.csv`, or active
veteran feature files.

NFLVerse Upgrade Phase 11 adds explicit apply. Applying requires the confirmation
phrase `APPLY_STATS_FIRST_PREVIEW`, validates the source data pack, reads a named
preview, applies only `ready` preview rows, and writes a new data-pack copy. It
does not mutate the source pack. The copied pack receives updated
`model_outputs.csv` rows and a `stats_first_applied_pack_manifest.json`; it must
still pass Import Review admission before being used for decisions.

NFLVerse Upgrade Phase 12 adds UI trust language and controls for the stats-first
lane on `Sources & Overrides`. The page now shows normalized-file, preview-root,
and applied-root status; creates stats-first previews; shows preview review
gates; requires the apply confirmation phrase; and reminds the user that copied
packs must be admitted through Import Review before use.

NFLVerse Upgrade Phase 13 adds a stats-first calibration tab to Historical
Replay. It checks LVE-specific formula behavior, sensitivity, and preview replay
status without feeding current boards. Scenario rows and sensitivity rows are
diagnostics for formula review only; they do not mutate previews, applied packs,
or live model outputs.

NFLVerse Upgrade Phase 14 integrates stats-first artifacts into Draft Freeze.
Freezes now copy stats-first preview and applied-pack folders into
`stats_first_backup/` when present, and metadata records preview/applied counts.
The freeze remains backup-only: it does not create, apply, or admit stats-first
model outputs.

NFLVerse Upgrade Phase 15 adds a final QA safety gate. It audits selected-pack
readiness, stats-first preview boundaries, copied-pack apply boundaries,
draft-freeze lock/certificate evidence, and the no-silent-mutation policy. The
audit is read-only and classifies each gate as `ready`, `review`, or `blocked`.
