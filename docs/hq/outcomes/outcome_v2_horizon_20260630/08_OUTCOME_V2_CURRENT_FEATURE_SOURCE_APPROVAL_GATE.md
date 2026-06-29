# Outcome V2 Current Feature Source Approval Gate

Date: 2026-06-29

## 1. Executive Decision

`PARTIAL_APPROVAL_2025_FEATURE_CONTEXT_OUTCOME_V2_DISPLAY_ONLY`

The 2025 season-stats context is approved only as a narrow Outcome V2 current-player feature source for display-only probability generation in a future task.

This approval is partial because:

- the season-stats context does not include `games`
- the season-stats context does not include `sack_fumbles_lost`
- 5 of 189 veteran/non-rookie bridge rows do not have a 2025 feature row

No current-player probabilities were created. No app-facing Outcome V2 columns were created. Rankings was not touched.

## 2. Candidate Data Paths Inspected

Season-stats candidate:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\20260621_pre_backtest_scoring_aligned_v1\player_season_stats_display_context.csv`

Season-stats pointer:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\latest_candidate.json`

Season-stats manifest:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\20260621_pre_backtest_scoring_aligned_v1\manifest.json`

Roster identity context:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context\20260621_pre_backtest_scoring_aligned_v1\player_roster_display_context.csv`

Outcome V2 identity bridge:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge\outcome_v2_current_identity_bridge.csv`

Outcome V2 validation results:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\outcome_v2_probability_validation_results.csv`

## 3. Provenance / Source Analysis

The manifest identifies the source as:

- source repo: `nflverse/nflreadpy local raw snapshot`
- source dataset: `season_stats`
- source lane: `stats_context`
- source snapshot: `20260621_000000_nflverse_expansion_v1`

The gate result is:

`PASS_PUBLIC_FACTUAL_NFLVERSE_PROVENANCE`

No market, ADP, DynastyProcess, CFBD, vendor, Gmail, projection, analyst rank, trade value, or injury projection source is used.

## 4. Timing / As-Of Analysis

The current board is `2026-pre-draft`.

The 2025 season-stats context contains completed `2025` regular-season rows, and the source snapshot was created on `2026-06-21`, after the 2025 NFL season. For this narrow approval:

- anchor/current feature season = `2025`
- `This Year` = 2026 NFL season
- `Next Year` = 2027 NFL season
- `Within 5 Years` = at least once from 2026 through 2030

The source package still has `source_timing_class=unknown_timing_yellow` and `live_use_allowed=false`. This gate resolves that only for narrow completed-2025 regular-season Outcome V2 feature use. It does not make the package live, source-truth, model-training, simulation, ranking, draft-decision, or `latest_approved` data.

Gate timing result:

`PASS_NARROW_COMPLETED_2025_REG_FOR_2026_PREDRAFT`

## 5. Feature-Schema Compatibility

The 2025 context includes required identity and factual production fields:

- `player_id`
- `player_display_name`
- `position`
- `recent_team`
- `season`
- `season_type`
- passing yards / TD / interceptions
- passing first downs
- rushing yards / TD / first downs
- receiving yards / TD / first downs
- two-point conversions
- rushing and receiving fumbles lost
- return yards and return TD fields

Missing optional/exactness fields:

- `games`
- `sack_fumbles_lost`

Gate field result:

`PARTIAL_FIELD_COMPATIBILITY`

The missing `games` field means availability context cannot be fully replicated from the validated historical feature schema. Future display artifacts must mark availability context as partial or `Not enough information` where games are required.

## 6. Identity Bridge Compatibility

The Outcome V2 current identity bridge joins current board IDs to GSIS IDs. The season-stats context uses GSIS-style `player_id`, so it is joinable.

| Metric | Value |
| --- | ---: |
| Veteran/non-rookie bridge rows | 189 |
| Matched to 2025 feature row | 184 |
| Missing 2025 feature row | 5 |
| Rookie/prospect out of scope | 43 |
| Coverage | 97.35% |

Missing veteran/non-rookie 2025 feature rows:

- Brandon Aiyuk
- Joe Mixon
- Tank Dell
- Jonathon Brooks
- MarShawn Lloyd

These rows must be `Not enough information` for any future current-player Outcome V2 display artifact unless a later approved feature source covers them.

## 7. Coverage By Position

| Position | Coverage |
| --- | ---: |
| QB | 25/25 |
| RB | 59/62 |
| WR | 75/77 |
| TE | 25/25 |

The coverage is useful enough for a partial current-player artifact later, but it is not complete.

## 8. Rookies / Prospects Handling

43 rows remain out of scope for Normal Outcome V2:

- QB: 3
- RB: 17
- WR: 16
- TE: 7

Those rows belong to Rookie Outcome, not Normal Outcome V2. They must remain `out_of_scope_rookie_or_prospect` / `Not enough information` in any future artifact.

## 9. First-Down / Scoring Field Status

The context includes passing, rushing, and receiving first-down fields, so first-down-aware NWR scoring is supported for the main production components.

Scoring caveat:

`sack_fumbles_lost` is missing. Rushing and receiving fumbles lost are present. Future artifact code must either document the scoring status as partial for sack-fumble-loss handling or keep affected scoring context as `Not enough information` where exactness is required.

Gate scoring result:

`PARTIAL_EXACT_FIRST_DOWN_SCORING_MISSING_SACK_FUMBLES_LOST`

## 10. Availability / Games Field Status

The season-stats context does not include `games`.

Gate availability result:

`PARTIAL_AVAILABILITY_CONTEXT_MISSING_GAMES`

Future display artifacts must not imply clean health or full availability. Missing availability context must be represented explicitly.

## 11. Source-Policy Decision

The source package allows display/stat context and source audit, while forbidding private value, hidden sort, hidden rank, draft recommendation, final draft decision, model training, simulation, production deployment, and `latest_approved`.

This gate approves only this additional narrow use:

`outcome_v2_current_feature_source_display_only`

This approval is recorded in this lane doc and audit output only. It does not mutate `latest_candidate`, create `latest_approved`, or promote the package to general model/source-truth use.

## 12. Allowed Use If Approved

Allowed:

- use 2025 regular-season factual stats as the current feature season for Normal Outcome V2 display-only probability generation
- use only rows joined through the approved current-board-to-GSIS bridge
- use only veteran/non-rookie rows with matching 2025 feature coverage
- use only fields that passed Outcome V2 validation
- show blocked/missing fields as `Not enough information`

## 13. Explicit Not-Allowed Uses

Not allowed:

- Dynasty Rank changes
- tier changes
- Final Board Rank changes
- Candidate Rank changes
- hidden sort
- model/rank/source-truth promotion
- model training
- production deployment
- draft recommendation
- final draft decision
- simulation
- trade value
- pick value
- Rookie Outcome probabilities
- CFBD inputs
- market/ADP/DynastyProcess inputs
- vendor/Gmail/projection inputs
- injury-risk or medical projection inputs
- `latest_candidate` mutation
- `latest_approved` creation or mutation

## 14. Remaining Caveats

- Approval is partial because `games` is missing.
- Approval is partial because `sack_fumbles_lost` is missing.
- Five veteran/non-rookie bridge rows lack 2025 feature rows.
- Rookie/prospect rows remain out of scope.
- RB T6 and RB T12 within-5-year fields remain blocked by calibration and must display `Not enough information`.
- No current-player display artifact exists yet.
- No Rankings integration exists yet.

## 15. Next Step If GREEN

The next separate task may build a compact current-player Outcome V2 display artifact using this partial approval.

That task must:

- include only validated fields
- keep `RB T6 Within 5 Years` and `RB T12 Within 5 Years` blocked
- keep missing rows as `Not enough information`
- mark availability/scoring exactness caveats
- keep all fields display-only
- avoid Rankings integration unless the display artifact passes its own gate

## Audit Artifacts

Generated review-only audit files:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\current_feature_gate\outcome_v2_current_feature_source_gate_audit.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\current_feature_gate\outcome_v2_current_feature_source_gate_manifest.csv`

These shared-data artifacts are not committed.
