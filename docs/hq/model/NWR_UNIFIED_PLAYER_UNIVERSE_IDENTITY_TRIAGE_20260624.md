# NWR Unified Player Universe Identity Triage

Date: 2026-06-24

Branch: `work/hq-parallel-control`

Scope: review/data-quality pass only. This does not wire the unified player universe into Dynasty Rankings, Drafting Mode, Player Compare, Trading Lab, or any app page.

## Verdict

YELLOW-GREEN for review artifact quality.

App wiring remains blocked. The artifact is still explicitly review-only, with `app_wiring_allowed=no` and `model_input_allowed=no` on every row.

## Starting State

- Review artifact rows: 383
- Veteran rows: 252
- Rookie/prospect rows: 54
- PDF free-agent rows: 77
- Starting identity gap count: 330
- Starting duplicate review count: 15
- Rows with missing `player_id`: 5

## Ending State

- Ending identity gap count: 330
- Ending duplicate review count: 15
- Safe player ID repairs applied: 0
- App wiring allowed rows: 0
- Model input allowed rows: 0

No high-confidence existing crosswalk or exact approved player ID match was found for the five missing-ID rookie/prospect rows. Those rows remain visible for review but were not repaired.

## Identity Gap Triage

The new triage file is:

`docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_identity_triage.csv`

Triage class counts:

- `EXPECTED_NO_ID_REVIEW_ONLY`: 258
- `NEEDS_MANUAL_REVIEW`: 72
- `SAFE_REPAIR_EXISTING_CROSSWALK`: 0
- `SAFE_REPAIR_EXACT_APPROVED_MATCH`: 0
- `DO_NOT_REPAIR`: 0

Gap type counts remain:

- `manual_review_flag`: 263
- `missing_age`: 42
- `low_or_missing_join_confidence`: 20
- `missing_player_id`: 5

Missing player IDs still requiring manual review:

- Sieh Bangura, RB, Rookie/Prospect Layer
- Devin Voisin, WR, Rookie/Prospect Layer
- Barika Kpeenu, RB, Rookie/Prospect Layer
- Braylon James, WR, Rookie/Prospect Layer
- Jamarion Miller, RB, Rookie/Prospect Layer

Existing repo evidence for those five rows is `LOW` confidence / `needs_manual_review=yes` / `needs_data`, so no ID was fabricated.

## Duplicate Triage

All 15 duplicate groups were classified as:

`MULTI_LAYER_SAME_PLAYER_EXPECTED`

Recommended action:

Keep separate review rows for now. These are expected multi-layer appearances, generally from Full Dynasty plus Frozen Baseline or PDF free-agent context. Do not auto-merge until a later source-policy/app-wiring lane approves consolidation rules.

## Repairs Made

No player ID repairs were applied.

Reason:

The review lane found no high-confidence existing approved crosswalk or exact approved match for currently missing player IDs. Applying IDs from low-confidence/manual-review rows would violate the no-fabrication guardrail.

## Repairs Skipped

Repairs were skipped for:

- Missing player IDs without approved high-confidence crosswalk evidence.
- Missing ages without approved age source coverage.
- Manual review flags created by duplicate/source-layer overlap.
- Low or missing join confidence rows that require human source review.

## Remaining Blockers Before App Wiring

P1 blockers:

- Five rookie/prospect rows still have no stable approved `player_id`.
- Forty-two identity gaps are tied to missing age coverage.
- Fifteen duplicate groups need an approved merge/display policy.
- Review rows with `LOW` or `NOT_ENOUGH_INFORMATION` join confidence need a human source pass.

P2 blockers:

- Source-layer consolidation policy is not yet approved.
- App display behavior for multi-layer rows is not defined.
- Manual review outcomes are not yet captured in a source-truth artifact.

## App Wiring Status

Blocked.

The artifact remains useful for review and planning, but it is not approved for app consumption. A future integration lane should require:

1. Approved identity repairs for missing IDs where possible.
2. A duplicate/source-layer consolidation policy.
3. Age coverage decisions for missing-age rows.
4. Confirmation that market fields remain display-only.
5. A separate app service contract and tests before any page reads this artifact.

## Recommended Next Step

Run a manual identity and age review lane for the five missing-ID rookie/prospect rows and the missing-age set. After that, create a source-policy decision for whether expected multi-layer duplicates should be kept as separate rows, collapsed into one canonical row, or displayed as row facets.

## Files Updated

- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_identity_triage.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_duplicate_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_validation_report.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_source_summary.csv`
- `src/services/unified_player_universe_validation_service.py`
- `scripts/build_unified_player_universe_v1_review.py`
- `tests/test_unified_player_universe_validation_service.py`

## Guardrails

- No app pages changed.
- No Dynasty Rankings behavior changed.
- No Drafting Mode behavior changed.
- No model or rank logic changed.
- No Frozen Final Draft Board V1 mutation.
- No `final_board_rank`, Dynasty Rank, tier, latest, or pinned snapshot mutation.
- No fabricated player IDs.
- No fabricated rookie Dynasty Rank.
- No fabricated outcome probabilities.
- Market/DynastyProcess values remain display-only.
- `app_wiring_allowed=no` for all rows.
- `model_input_allowed=no` for all rows.
