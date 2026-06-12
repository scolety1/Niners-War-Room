# Build Sprint 5AN Status-Only Product/UX Audit

## Verdict

`STATUS_ONLY_UX_PASS_WITH_RECOMMENDATIONS`

The current **Outcome Model Status** section is safe and understandable. It does not look like a released prediction, does not show probability-like values, and preserves the status-only contract. It is somewhat dense because it shows seven rows on every player detail card, so the recommended UX refinement is `keep_but_compact`, with `make_collapsible` as a later option if the card feels crowded in demo review.

## Scope

Question audited: Does the current status-only section help the player card, or is it clutter?

This audit did not patch code, change model logic, create probabilities, change ranking/sorting, push, deploy, or promote artifacts.

## Surfaces Reviewed

- `app/components/player_detail_card.py`
- `src/services/player_detail_card_service.py`
- `src/services/nwr_outcome_status_display_service.py`
- `tests/test_player_detail_card_service.py`
- `tests/test_player_detail_card_component.py`
- `tests/test_nwr_outcome_status_display_service.py`
- Local app route: Dynasty Rankings at `http://localhost:8501/rankings`
- Read-only service probes for QB, RB, WR, TE, K, and missing position rows.

## App Behavior

The player detail card renders:

- Section heading: `Outcome Model Status`
- Guardrail copy: `Outcome model is in development. No probabilities are released yet.`
- Columns: `Outcome`, `Status`, `Help`

For QB/RB/WR/TE rows:

- Same-year outcomes show `In development`.
- `next_year_starter` shows `Blocked by release gate`.
- `multi_year_targets` and `hazard_windows` show `Not applicable`.
- `probability_value`, `probability_band`, `sortable_value` remain null.
- `is_numeric` remains false.

For kicker rows:

- All outcome status rows resolve to `Not applicable`.
- Numeric fields remain null.

For missing position rows:

- Same-year outcomes remain `In development`.
- `next_year_starter` remains blocked.
- Multi-year and hazard targets remain not applicable.

## UX Findings

| Area | Finding | Risk | Recommendation |
| --- | --- | --- | --- |
| Clarity | The heading and guardrail copy are clear. | Low | Keep. |
| Prediction confusion | The section says no probabilities are released and uses status language. | Low | Keep text-only copy. |
| Odds/chance wording | No odds/chance/projection language appears in the status table. | Low | Keep copy constrained. |
| Visual density | Seven rows add noticeable length to the card. | Medium | Keep now; consider compact/collapsible later. |
| Table length | The table is readable, but it is more audit-like than product-like. | Medium | Consider compact grouping if demo users find it heavy. |
| Default visibility | Visible-by-default is acceptable because it is status-only and clear. | Low-medium | Keep visible for HQ review. |
| Placement | Current placement after private model context is logical. | Low | Keep or move slightly lower only if card flow feels busy. |
| App surface | Player-card-only is appropriate. | Low | Do not add rankings/draft-room surfaces. |

## UX Recommendation

Recommended option: `keep_but_compact`.

Current section can remain visible for HQ review because it is clear and safe. The first refinement, if desired, should be a compact presentation or collapsible expander, not a probability release. Do not hide it entirely unless demo feedback says the audit table distracts from core player review.

## Local Exports

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5an_status_only_ux_audit/`

## Confirmed Non-Actions

- No code was patched.
- No app probabilities were created.
- No calibrated probabilities were created.
- No player-facing probabilities were created.
- No rankings or sorting changes were made.
- No decision automation was created.
- No app-readable probability tables were created.
- No artifacts were promoted or released.
