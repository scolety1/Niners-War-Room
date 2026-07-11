from __future__ import annotations

from pathlib import Path

WORKFLOW = Path("app/components/draft_workflow.py")
LIVE_PAGE = Path("app/pages/21_live_draft_room_v1.py")
MOCK_PAGE = Path("app/pages/24_mock_draft_v1.py")
SHELL = Path("app/components/ui_framework.py")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_equivalent_live_and_mock_actions_reuse_one_accessible_label_set() -> None:
    workflow = _text(WORKFLOW)
    live = _text(LIVE_PAGE)
    mock = _text(MOCK_PAGE)

    assert 'ASSIGN_PICK_LABEL = "Assign selected player to pick"' in workflow
    assert 'UNDO_PICK_LABEL = "Undo last assigned pick"' in workflow
    assert 'REMOVE_PICK_LABEL = "Remove player from assigned pick"' in workflow
    assert "render_draft_workflow(" in live
    assert "render_draft_workflow(" in mock
    assert "ASSIGN_PICK_LABEL" in workflow
    assert "UNDO_PICK_LABEL" in workflow
    assert "REMOVE_PICK_LABEL" in workflow


def test_primary_control_reading_order_precedes_dense_player_table() -> None:
    workflow = _text(WORKFLOW)

    status = workflow.index("Draft board status:")
    controls = workflow.index('primary_cols = st.columns([1.0, 1.25], gap="medium")')
    pick_control_call = workflow.index("_render_pick_controls(")
    table = workflow.index('st.markdown("#### Available Players")')

    assert status < controls < table
    assert pick_control_call < table
    assert "#### Select and assign a player" in workflow


def test_disabled_primary_actions_have_state_backed_explanations() -> None:
    workflow = _text(WORKFLOW)
    mock = _text(MOCK_PAGE)

    assert "Assign unavailable: {reason}" in workflow
    assert "disabled=True" in workflow
    assert "Undo unavailable: no assigned picks are in this session." in workflow
    assert "Remove unavailable: no assigned picks are in this session." in workflow
    assert 'disabled=not has_assignments' in workflow
    assert "Delete unavailable: confirm deletion first." in mock
    assert "disabled=not delete_confirmed" in mock


def test_selected_player_current_pick_and_team_are_named_in_text() -> None:
    workflow = _text(WORKFLOW)

    assert "Selected player: {player_label}. Selected pick: {pick_label}." in workflow
    assert "Current pick: {summary.current_pick_label}." in workflow
    assert "Current drafting team: {current_team}." in workflow
    assert "Draft complete. All configured pick slots are assigned." in workflow
    assert "Empty player table: no players match the current filters." in workflow


def test_drafted_current_open_and_selected_states_do_not_depend_on_color() -> None:
    workflow = _text(WORKFLOW)

    assert "Status is expressed in text: Current, Open, or Drafted." in workflow
    assert "The board does not rely on color alone." in workflow
    assert "Draft Status" in workflow
    assert "Assigned " in workflow and '"Pick when the drafted-player toggle is on."' in workflow
    assert "Selected player:" in workflow


def test_disclosures_use_native_streamlit_expanders_and_separate_actions() -> None:
    workflow = _text(WORKFLOW)

    assert 'st.expander("Edit or remove an assigned pick", expanded=False)' in workflow
    assert 'st.expander("Filter and sort players", expanded=False)' in workflow
    assert "Keyboard-operable disclosure." in workflow
    assert "This does not run from the disclosure heading." in workflow
    assert "REMOVE_PICK_LABEL" in workflow


def test_compact_width_contract_stacks_controls_and_contains_dense_tables() -> None:
    workflow = _text(WORKFLOW)
    shell = _text(SHELL)

    assert "Dense columns scroll inside the table" in workflow
    assert 'div[data-testid="stDataFrame"]' in shell
    assert "max-width: 100%" in shell
    assert "@media (max-width: 760px)" in shell
    assert "flex: 1 1 100% !important" in shell
    assert "width: 100% !important" in shell
    assert "flex-wrap: wrap" in shell


def test_secondary_context_follows_primary_workflow_on_both_surfaces() -> None:
    live = _text(LIVE_PAGE)
    mock = _text(MOCK_PAGE)

    live_workflow = live.index("render_draft_workflow(")
    mock_workflow = mock.index("render_draft_workflow(")
    assert live_workflow < live.index("_render_live_secondary_context(", live_workflow)
    assert mock_workflow < mock.index("_render_mock_secondary_context(", mock_workflow)
    assert 'st.expander("Manage saved mock drafts", expanded=False)' in mock


def test_presentation_layer_keeps_existing_draft_callbacks_and_state_ownership() -> None:
    workflow = _text(WORKFLOW)

    for callback in (
        "assign_player_to_pick(",
        "undo_last_pick(",
        "remove_pick_assignment(",
        "update_workflow_state(",
        "save_runtime_state(",
        "load_runtime_state_with_status(",
    ):
        assert callback in workflow
    assert "st.session_state[runtime_state_key]" in workflow
    assert "st.session_state[session_key]" in workflow
