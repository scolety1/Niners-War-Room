from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from fixtures.start_here_durable_mutations import (
    inject_direct_file_write,
    inject_receipt_write,
    inject_refresh_dispatch,
    inject_rename_and_delete,
    inject_runtime_state_write,
    inject_wrapped_write,
)
from post_v1_assertion_harness import (
    DurableRenderResult,
    load_workflow_authority,
    render_start_here,
    render_start_here_with_durable_monitor,
    validate_start_here_contract,
)


def _replace_once(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, f"mutation anchor count changed for {old!r}"
    return source.replace(old, new, 1)


def _workflow_mutation(*, title: str, status: str, route: str) -> Callable[[str], str]:
    def mutate(source: str) -> str:
        source = _replace_once(source, '            "Trading Lab",', f'            "{title}",')
        source = _replace_once(
            source,
            '            "Manual decision aid",',
            f'            "{status}",',
        )
        return _replace_once(source, '            "/trading-lab",', f'            "{route}",')

    return mutate


def _assert_zero_durable_mutations(result: DurableRenderResult) -> None:
    assert result.durable_mutation_count == 0
    assert result.mutations == ()
    assert result.before == result.after


def test_default_home_renders_the_authoritative_workflow_contract() -> None:
    rendered = render_start_here()

    validate_start_here_contract(rendered, authority=load_workflow_authority())

    assert tuple(level for level, _text in rendered.headings).count("h1") == 1
    assert {workflow.title for workflow in rendered.workflows} == {
        "Dynasty Rankings",
        "Player Compare",
        "Trading Lab",
        "Draft Cockpit",
    }
    assert {link.target for link in rendered.links} == {
        "/rankings",
        "/player-compare",
        "/trading-lab",
        "/draft-cockpit",
        "/settings-data-health",
        "/review-workflow",
        "/asset-explorer",
        "/rookie-board",
        "/personal-board",
        "/decision-journal",
        "/saved-scenarios",
    }


@pytest.mark.parametrize(
    "mutation",
    (
        _workflow_mutation(
            title="Trading Lab",
            status="Automated decision aid",
            route="/trading-lab",
        ),
        _workflow_mutation(title="Refresh Data", status="Live", route="/refresh-data"),
        _workflow_mutation(
            title="Evidence Review",
            status="Production",
            route="/evidence-integration-review",
        ),
        _workflow_mutation(title="Future Tools", status="Available", route="/future-tools"),
        lambda source: _replace_once(
            source,
            '            "/trading-lab",',
            '            "/player-compare",',
        ),
        lambda source: _replace_once(
            source,
            '            "Manual decision aid",',
            '            "Manual decision aid / Automated decision aid",',
        ),
    ),
    ids=(
        "manual_to_automated",
        "gated_to_live",
        "review_only_to_production",
        "parked_to_available",
        "wrong_route_target",
        "contradictory_disposition",
    ),
)
def test_rendered_workflow_disposition_mutations_are_detected(
    mutation: Callable[[str], str],
) -> None:
    rendered = render_start_here(source_transform=mutation)

    with pytest.raises(AssertionError):
        validate_start_here_contract(rendered, authority=load_workflow_authority())


def test_missing_primary_link_mutation_is_detected() -> None:
    rendered = render_start_here()
    workflows = tuple(
        replace(workflow, links=()) if workflow.title == "Trading Lab" else workflow
        for workflow in rendered.workflows
    )
    mutated = replace(rendered, workflows=workflows)

    with pytest.raises(AssertionError, match="exactly one primary link"):
        validate_start_here_contract(mutated, authority=load_workflow_authority())


def test_page_open_has_zero_durable_mutations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = render_start_here_with_durable_monitor(
        monkeypatch,
        tmp_path / "isolated-start-here-state",
    )

    validate_start_here_contract(result.rendered, authority=load_workflow_authority())
    _assert_zero_durable_mutations(result)


def test_page_open_permits_session_only_render_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = render_start_here_with_durable_monitor(
        monkeypatch,
        tmp_path / "isolated-session-only-state",
        source_transform=lambda source: (
            source + '\nst.session_state["start_here_test_only"] = "in-memory"\n'
        ),
    )

    _assert_zero_durable_mutations(result)


@pytest.mark.parametrize(
    ("mutation", "expected_boundary"),
    (
        (inject_direct_file_write, "pathlib.Path.open"),
        (inject_receipt_write, "receipt.write_refresh_receipt"),
        (inject_runtime_state_write, "runtime.save_runtime_state"),
        (inject_refresh_dispatch, "refresh.dispatch"),
        (inject_rename_and_delete, "pathlib.Path.rename"),
        (inject_wrapped_write, "pathlib.Path.open"),
    ),
    ids=(
        "durable_file_write",
        "receipt_write",
        "draft_runtime_state_write",
        "refresh_dispatch",
        "rename_or_delete",
        "wrapped_write",
    ),
)
def test_page_open_durable_mutations_are_detected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: Callable[[Path], None],
    expected_boundary: str,
) -> None:
    isolated_root = tmp_path / "isolated-mutated-start-here-state"
    result = render_start_here_with_durable_monitor(
        monkeypatch,
        isolated_root,
        source_transform=lambda source: (
            source + "\nSTART_HERE_DURABLE_MUTATION(START_HERE_DURABLE_ROOT)\n"
        ),
        execution_globals={
            "START_HERE_DURABLE_MUTATION": mutation,
            "START_HERE_DURABLE_ROOT": isolated_root,
        },
    )

    assert any(item.boundary.startswith(expected_boundary) for item in result.mutations), (
        result.mutations
    )
    with pytest.raises(AssertionError):
        _assert_zero_durable_mutations(result)
