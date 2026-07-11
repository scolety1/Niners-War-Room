from src.services.refresh_recovery_presentation_service import (
    FIELD_ORDER,
    NOT_ENOUGH_INFORMATION,
    PARTIAL_SUCCESS,
    REFRESH_FAILED,
    REFRESH_SUCCESS,
    SOURCE_GATED,
    SOURCE_SKIPPED,
    SOURCE_UNAVAILABLE,
    STALE_RETAINED_DATA,
    build_refresh_recovery_presentations,
    build_run_recovery_summary,
)


def _one(**values):
    return build_refresh_recovery_presentations((values,))[0]


def test_all_eight_states_are_mechanically_distinct():
    assert _one(action_type="REFRESHED", refreshed=True).refresh_state == REFRESH_SUCCESS
    assert _one(freshness_status="stale").refresh_state == STALE_RETAINED_DATA
    assert _one(action_type="SKIPPED_BY_POLICY").refresh_state == SOURCE_SKIPPED
    assert _one(execution_status="blocked_config").refresh_state == SOURCE_UNAVAILABLE
    assert _one(execution_status="blocked_policy").refresh_state == SOURCE_GATED
    assert _one(action_type="FAILED").refresh_state == REFRESH_FAILED
    assert _one().refresh_state == NOT_ENOUGH_INFORMATION
    summary = build_run_recovery_summary(
        ({"refreshed": True}, {"action_type": "FAILED"})
    )
    assert summary.refresh_state == PARTIAL_SUCCESS


def test_gated_unavailable_failed_and_skipped_precedence_is_deterministic():
    assert _one(status="BLOCKED", action_type="FAILED").refresh_state == SOURCE_GATED
    assert _one(status="NOT_CONFIGURED", action_type="FAILED").refresh_state == SOURCE_UNAVAILABLE
    assert _one(status="SKIPPED", action_type="FAILED").refresh_state == SOURCE_SKIPPED


def test_contract_field_order_timestamp_diagnostic_and_guidance():
    item = _one(source_name="Example", action_type="FAILED", runner_path="diagnostic.py")
    assert tuple(item.as_ordered_row())[1:] == FIELD_ORDER
    assert item.last_success_or_as_of == "Not recorded"
    assert item.diagnostic_path == "diagnostic.py"
    assert item.action_availability == "AVAILABLE_ACTION"
    assert "approved refresh action" in item.safe_next_action


def test_adapter_is_passive_and_does_not_mutate_input():
    source = {"action_type": "REFRESHED", "refreshed": True}
    before = source.copy()
    first = build_refresh_recovery_presentations((source,))
    second = build_refresh_recovery_presentations((source,))
    assert source == before
    assert first == second
