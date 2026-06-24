# NWR Unified Player Universe Consolidation Policy

Date: 2026-06-24

Branch: `work/hq-parallel-control`

Scope: review artifact only. This policy and prototype do not wire the unified player universe into Dynasty Rankings, Drafting Mode, Player Compare, Trading Lab, or any app page.

## Verdict

YELLOW-GREEN for review inspection.

The consolidated artifact reduces expected multi-layer duplicate confusion, but app wiring remains blocked until identity, age, and manual-review blockers are resolved.

## Consolidation Policy

Only rows already classified as `MULTI_LAYER_SAME_PLAYER_EXPECTED` are eligible for automatic consolidation in this prototype. A group may be consolidated when it has:

- the same `player_id`, or
- the same normalized name + position with high confidence, or
- a duplicate review classification of `MULTI_LAYER_SAME_PLAYER_EXPECTED`.

Uncertain rows are not consolidated. If sources conflict, the consolidated row is marked `REVIEW_NEEDED` and the conflict is recorded in `conflict_flags`.

All consolidated rows remain review-only:

- `app_wiring_allowed=no`
- `model_input_allowed=no`

## Source Priority Rules

Canonical identity fields:

1. Veteran Full Dynasty Layer
2. Rookie/Prospect Layer
3. Frozen Baseline Layer
4. PDF Free-Agent Availability Layer

Field-specific rules:

- `player_id`: prefer stable existing ID from the highest-priority source; never fabricate.
- `player_name`: prefer approved canonical name from the highest-priority source.
- `position`: must not conflict silently.
- `nfl_team`: prefer known team over `UNKNOWN` / `NEEDS_DATA`; conflicting known teams require review.
- `age`: prefer approved or existing display age; missing age remains `Not enough information`; conflicting known ages require review.
- `dynasty_rank`: Full Dynasty source only.
- `rookie_rank`: approved rookie/prospect source only.
- `frozen_baseline_rank`: Frozen Baseline checkpoint only.
- `candidate_rank`: candidate/review source only.
- `tier`: keep source-labeled tier; do not infer a new tier.
- `outcome_context`: supported outcome context only; gaps remain `Not enough information`.
- `market fields`: display-only; never create rank, tier, or model input.
- `availability_status`: display context only; does not create rank.
- `caveats/manual_review_flag`: preserve source caveats and keep review-needed rows blocked.

## Output Files

- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidation_decisions.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_remaining_blockers.csv`

## Counts

- Starting review row count: 383
- Consolidated review row count: 368
- Duplicate groups handled: 15
- Consolidation conflicts found: 0
- Remaining blocker rows: 310

## Duplicate Groups Handled

All 15 duplicate groups from the identity triage pass were classified as `MULTI_LAYER_SAME_PLAYER_EXPECTED` and were consolidated into review-only canonical rows.

Decision file:

`docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidation_decisions.csv`

Each decision records:

- duplicate group
- player
- source layers
- decision
- confidence
- conflicts
- canonical field-source notes
- action taken

## Remaining Blockers

Blocker file:

`docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_remaining_blockers.csv`

Current blocker counts:

- `MISSING_PLAYER_ID`: 5
- `MISSING_AGE`: 42
- `REVIEW_NEEDED_ROW`: 263
- `CONSOLIDATION_CONFLICT`: 0

The five missing-ID rookie/prospect rows remain blocked because existing repo evidence is low-confidence/manual-review only:

- Sieh Bangura, RB
- Devin Voisin, WR
- Barika Kpeenu, RB
- Braylon James, WR
- Jamarion Miller, RB

## App Wiring Status

Still blocked.

The consolidated artifact is easier to inspect, but it is not approved for page consumption. A later app-wiring lane must explicitly approve:

1. Identity repairs for the remaining missing IDs.
2. Age coverage decisions for missing-age rows.
3. Manual review outcomes for rows still marked `REVIEW_NEEDED`.
4. Treatment of source-layer caveats in app display.
5. Continued enforcement that market/ADP/DynastyProcess fields remain display-only.

## Recommended Next Step

Run a manual identity and age cleanup lane against the remaining blockers file, then rerun this consolidation builder. Do not integrate the artifact into app pages until blocker counts and source-policy decisions are accepted in a separate implementation lane.

## Guardrails Confirmed By Design

- No app pages changed.
- No Dynasty Rankings behavior changed.
- No Drafting Mode behavior changed.
- No model or rank logic changed.
- Frozen Final Draft Board V1 remains baseline/checkpoint only.
- No `final_board_rank`, Dynasty Rank, tier, latest, or pinned snapshot mutation.
- No fabricated player IDs.
- No fabricated ages.
- No fabricated rookie Dynasty Rank.
- No fabricated outcome probabilities.
- Market/DynastyProcess/ADP context remains display-only.
- No `C:\NWR_SHARED_DATA`, `local_exports`, or runtime JSON is tracked by this lane.
