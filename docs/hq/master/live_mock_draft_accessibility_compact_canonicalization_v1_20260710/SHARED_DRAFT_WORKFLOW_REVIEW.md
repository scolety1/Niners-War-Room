# Shared Draft Workflow Review

## Result

PASS: `app/components/draft_workflow.py` changes presentation and accessibility only.

## Unchanged ownership and service boundary

`render_draft_workflow` retains the same parameters and derives the same `runtime_mode`, `runtime_draft_id`, `runtime_state_key`, and workflow `session_key`. Live remains keyed by `draft_day_v1_live_draft_workflow`; Mock remains keyed by `draft_day_v1_mock_draft_workflow_<draft_id>`. The runtime key remains `<session_key>_runtime_state`.

No imports from draft services were added, removed, or replaced. No file under `src/services` changed. The shared component still delegates state mutation to the existing workflow and runtime-state services.

## Primary actions

| Action | Before | After | State/callback conclusion |
|---|---|---|---|
| Assign | `assign_player_to_pick(...)`, `update_workflow_state(..., event_type="pick_assigned")`, store runtime/workflow state, set sync flag, rerun | Identical body and arguments; label/help text changed | Equivalent |
| Undo | `undo_last_pick(state)`, `update_workflow_state(..., event_type="pick_undone")`, store state, set sync flag, rerun | Identical body and arguments; descriptive label plus state-backed disabled/help/caption added | Equivalent when available; no render-time action |
| Remove | `remove_pick_assignment(state, overall_pick)`, `update_workflow_state(..., event_type="pick_removed")`, store state, set sync flag, rerun | Identical body and arguments; native disclosure label plus state-backed disabled/help/caption added | Equivalent when available; no disclosure-heading action |

## Sequencing and data-flow review

- Assignment sequencing is unchanged: workflow service first, runtime event update second, session-state stores third, sync flag fourth, rerun last.
- Undo history remains the final assignment in the existing `assignments` list.
- Removal still targets the selected existing `overall_pick` through `pick_options`.
- Auto-advance still comes from `current_pick_number` and the existing `<session_key>_sync_pick_to_current` flag.
- Persistence load/save/export/import/reset functions and their arguments are unchanged.
- Filter keys, toggle keys, sort keys, filter predicates, `available_board_frame`, and `sort_workflow_frame` calls are unchanged.
- Player identity remains `player_options[player_label]`; selected pick identity remains `pick_options[pick_label]`.
- No compact-width branch was added to Python logic. Responsive behavior remains CSS/layout presentation.
- No presentation helper writes workflow or runtime state.

## Visual reordering

The pick controls and compact board are rendered before the dense player table. Filters remain the same controls and predicates inside a native Streamlit expander. Live and Mock continue to invoke the same shared workflow with their pre-existing state scopes.

## Differential evidence

The deterministic baseline/source trace was byte-identical. Only the `assignments` key changed during workflow operations. Assign advanced pick 1 to pick 2; undo and remove restored empty state; reassign restored the same assignment; a three-pick sequence completed with `current_pick_number == None`; hidden/show-drafted row counts were 2 and 3 in both commits.
