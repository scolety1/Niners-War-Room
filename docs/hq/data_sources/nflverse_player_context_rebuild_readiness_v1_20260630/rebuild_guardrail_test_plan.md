# Rebuild Guardrail Test Plan

Verdict: `YELLOW_WAITING_FOR_BINDING_ARTIFACT`

## Pre-Rebuild Blocking Tests

The later rebuild lane must stop before artifact writes unless all preflight tests pass:

- Required binding directory exists.
- `approved_identity_nwr_binding_v1.csv` exists.
- Binding manifest or guardrail report includes `rebuild_player_context_permitted=true`.
- Binding CSV schema matches `required_binding_contract.md`.
- Binding CSV rows are a subset of `identity_approved_overlay_v1.csv`.
- Binding CSV contains no row from `identity_overlay_non_approved_rows.csv`.
- Every applied row has `human_decision=APPROVE_REVIEW_ONLY` and `approved_by_human=true`.
- Every applied row has populated approved NFLVerse and GSIS IDs.
- Every applied row has populated unique `bound_nwr_player_id`.
- No name-only or fuzzy-only binding is used.
- All forbidden-use flags are `false`.

## Player Context Artifact Tests

For a full 43-row apply, the rebuilt artifact must satisfy:

- Total rows: 294.
- `SAFE_NOW_DISPLAY_ONLY` rows: 283.
- `NEED_IDENTITY_REVIEW` rows: 11.
- `review_required=false` rows: 283.
- `review_required=true` rows: 11.
- No duplicate `nwr_player_id` for safe rows.
- The 43 applied rows have `identity_join_status=SAFE_NOW_DISPLAY_ONLY`.
- The 11 non-approved rows remain `NEED_IDENTITY_REVIEW`.
- Gated rows expose no detailed identity, schedule, denominator, roster, injury, depth, snap, draft, or contract context.
- Missing values remain `Not enough information`, not zero, false, clean, healthy, safe, no-role, no-usage, favorable, or confirmed UDFA.
- `ff_rankings` remains blocked and unused.

## Flag Tests

Across the binding artifact, rebuilt player-context artifact, schema manifest, denominator artifact if refreshed, and schedule context if refreshed:

- `display_only=true` for every display row.
- `model_use_allowed=false`.
- `training_allowed=false`.
- `source_truth_allowed=false`.
- `rank_logic_allowed=false`.
- `hidden_sort_allowed=false`.
- `trade_value_allowed=false`.
- `pick_value_allowed=false`.

## Existing Unit Tests That Must Pass In The Later Rebuild Lane

Run the focused tests that already exercise central artifact consumption and guardrails:

```powershell
python -m pytest `
  tests/test_nflverse_player_context_display_service.py `
  tests/test_nflverse_schedule_context_display_service.py `
  tests/test_player_compare_nflverse_context.py `
  tests/test_development_lab_nflverse_context_service.py `
  tests/test_draft_day_player_context_service.py `
  tests/test_draft_day_player_context_ui_guardrails.py `
  tests/test_trading_lab_nflverse_context_service.py `
  tests/test_injury_availability_context_service.py `
  tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_integrates_safe_rows_and_age_fallback `
  tests/test_dynasty_rankings_page_v1.py::test_nflverse_player_context_identity_review_rows_do_not_expose_details `
  -q
```

## Repository Safety Checks

Run these before commit:

```powershell
git diff --check
git status --short
```

Also scan changed paths and tracked paths for:

- app page changes
- model/rank/source-truth/protected artifact changes
- latest pointer changes
- raw/shared/local/vendor/Gmail/cache/runtime/secret paths
- runtime JSON changes
- frozen board or pinned snapshot changes

Any violation must return `RED_GUARDRAIL_FAILURE`.
