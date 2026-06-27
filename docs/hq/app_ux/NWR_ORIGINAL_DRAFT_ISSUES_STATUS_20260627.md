# NWR Original Draft Issues Status - 2026-06-27

Source: `C:\Users\codex-agent\Downloads\Issues After Draft.docx`

This maps the original post-draft feedback to current implementation status. This lane intentionally did not touch Live Draft Room, Mock Drafts, draft runtime state, draft workflow, pick ownership logic, event replay/undo, or draft-room UI.

| Original issue | Status | Action in this lane | Notes |
|---|---|---|---|
| Reload lost drafted state | FIXED_ALREADY | Verified by scope only; no code touched | Live Draft V2 reliability owns reload-safe runtime state. This lane did not modify it. |
| In-draft trade `1.04` for `2028 1st + 2.03` had no app support | FIXED_ALREADY | Verified by scope only; no code touched | Live Draft V2 trade-event workflow owns real trade recording, pick ownership, future assets, replay/undo, and persistence. |
| Player Compare was useful but too confusing/hard to process | SAFE_FIX_THIS_LANE | Added top usage guide, clearer display-only Decision Summary framing, plain-language comparison rows, and advanced fields under an expander | No rank, tier, model value, source-truth, or market decision logic changed. |
| User was unsure how injury issues were factored in | SAFE_FIX_THIS_LANE / BLOCKED_NEEDS_MODEL_OR_DATA_GATE | Added Injury / Availability Data Status panel explaining current limits | No injury risk score, medical comeback projection, ACL inference, or model penalty was added. Active injury modeling still needs a source/model gate. |
| Trade Finder / trade away pick tool | SAFE_FIX_THIS_LANE / BLOCKED_NEEDS_MODEL_OR_DATA_GATE | Reframed Trading Lab as a manual Trade Away Pick Planner | It supports manual offer notes and checklists only. No automatic finder, valuation, generated offers, or least-acceptable-price logic. |
| Trade For tool for a falling player at a target pick like `1.08` | SAFE_FIX_THIS_LANE / BLOCKED_NEEDS_MODEL_OR_DATA_GATE | Reframed Trading Lab as a manual Trade For Pick Planner | It supports manual scenarios and checklists only. No generated offer, trade value, market value, or model answer. |
| Draft room tabs/search/side panel/cheat sheet/tier ideas | DEFER_DRAFT_ROOM_REVIEW | No action | This lane was explicitly barred from draft-room files. These remain for a later draft-room review lane. |
| Post-draft mode / normal mode / draft room mode | FIXED_ALREADY / DEFER_DRAFT_ROOM_REVIEW | No action | Draft Analyzer and Development Lab framework exist. Any draft-room navigation changes are deferred to draft-room UX lanes. |
| Dropdowns/customized info density in draft room | DEFER_DRAFT_ROOM_REVIEW | No action | Would touch draft-room UX. |
| Cheat sheet / tier-separated board inside draft workflow | DEFER_DRAFT_ROOM_REVIEW | No action | Would touch draft-room or ranking/tier presentation surfaces. Tier assignments remain untouched. |

## Guardrails

- Live Draft Room, Mock Drafts, draft runtime state, draft workflow, pick ownership, and event replay/undo were not modified.
- No Frozen Final Draft Board V1, `final_board_rank`, Dynasty Rank, tier assignment, pinned snapshot, `latest_candidate`, or `latest_approved` mutation.
- No production model/rank/source-truth logic changes.
- No trade valuation, pick valuation, automatic trade finder, automatic offer generator, injury score, medical projection, market-driven answer, CFBD/NFL promotion, or hosted deployment.
