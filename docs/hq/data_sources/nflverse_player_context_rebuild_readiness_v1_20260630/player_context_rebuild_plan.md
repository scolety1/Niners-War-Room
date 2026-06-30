# Player Context Rebuild Plan

Verdict: `YELLOW_WAITING_FOR_BINDING_ARTIFACT`

## Rebuild Status

Do not rebuild in this lane. The required binding artifact is missing from the current HQ base.

This plan describes the later apply/rebuild process once the binding packet exists and explicitly permits the rebuild.

## Preflight

1. Fetch origin.
2. Start from current `origin/work/hq-parallel-control`.
3. Confirm HQ HEAD is at or after `bb7146271c71c39a1d7f1d82fd40c65b4ce9d4d5`.
4. Confirm the required binding packet exists:
   `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/`
5. Confirm `approved_identity_nwr_binding_v1.csv` exists and passes the required binding contract.
6. Confirm the binding packet explicitly permits rebuild with `rebuild_player_context_permitted=true`.
7. Stop if the binding packet is missing, unmerged, partial without permission, schema-invalid, count-invalid, or guardrail-invalid.

## Rebuild Inputs

Use only tracked repo artifacts and approved local-only snapshot inputs already permitted by the source packet:

- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`
- `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_approved_overlay_v1.csv`
- `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_overlay_non_approved_rows.csv`
- `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/approved_identity_nwr_binding_v1.csv`
- Approved source-cache inputs already documented by the player-context display packet, only if the existing build service requires them.

App pages must not read raw shared-cache files directly.

## Apply Logic

1. Load the current player-context display artifact.
2. Load the approved overlay.
3. Load the binding CSV.
4. Validate the binding CSV against the required binding contract.
5. Join binding rows to the current player-context review rows by the approved overlay row identity plus `bound_nwr_player_id`.
6. For each validated bound row:
   - set `nwr_player_id` to `bound_nwr_player_id`;
   - set `identity_join_status=SAFE_NOW_DISPLAY_ONLY`;
   - set `review_required=false`;
   - populate approved NFLVerse/GSIS identity fields from the approved overlay and rebuilt player-context source joins;
   - keep all missing source fields as `Not enough information`;
   - keep `display_only=true`;
   - keep all forbidden-use flags `false`.
7. For all non-approved rows:
   - keep `identity_join_status=NEED_IDENTITY_REVIEW`;
   - keep `review_required=true`;
   - expose no detailed context;
   - keep schedule/detail fields unavailable.
8. Recompute build, schema, join-health, and guardrail reports for the player-context display packet only if the later lane explicitly authorizes artifact writes.

## Count Expectations

For a full 43-row binding apply:

- Total player-context rows remain 294.
- `SAFE_NOW_DISPLAY_ONLY` rows move from 240 to 283.
- `NEED_IDENTITY_REVIEW` rows move from 54 to 11.
- `review_required=false` rows move from 240 to 283.
- `review_required=true` rows move from 54 to 11.
- Gated rows with populated schedule context remain 0.

If fewer than 43 rows are bound and partial apply is explicitly permitted, expected counts must be recalculated as:

- safe rows: `240 + valid_bound_row_count`
- identity-review rows: `54 - valid_bound_row_count`
- review-required false rows: `240 + valid_bound_row_count`
- review-required true rows: `54 - valid_bound_row_count`

## Denominator And Schedule Handling

Do not update denominator artifacts unless a later lane explicitly includes a denominator refresh. If refreshed, denominator rows must re-read the central player-context artifact and continue to expose detail only when `identity_join_status=SAFE_NOW_DISPLAY_ONLY`, `review_required=false`, and `denominator_status=SAFE_NOW_DISPLAY_ONLY`.

Do not update schedule policy artifacts unless source policy changes. The existing schedule gate already allows display for safe rows and blocks identity-review rows. Newly bound rows may show schedule context only through the rebuilt central artifact and only when fields are not `Not enough information`.

## Forbidden Changes

- Do not change app pages.
- Do not change model, training, source-truth, ranking, hidden-sort, trade, pick, recommendation, or outcome logic.
- Do not change latest pointers.
- Do not change frozen board, pinned snapshots, protected ranking artifacts, or runtime JSON.
- Do not track raw/shared/local/vendor/Gmail/cache/secrets.
- Do not expose identity-review rows.
- Do not approve non-bound identities.
