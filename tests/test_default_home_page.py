from __future__ import annotations

import ast
from collections.abc import Callable
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
    render_start_here,
    render_start_here_with_durable_monitor,
)

from app.navigation import DEFAULT_ROOT_PAGE

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "app/pages/46_draft_cockpit_default_root.py"


def _source() -> str:
    return HOME.read_text(encoding="utf-8")


def _assert_zero_durable_mutations(result: DurableRenderResult) -> None:
    assert result.durable_mutation_count == 0
    assert result.mutations == ()
    assert result.before == result.after


def test_default_home_is_the_owner_decision_entrypoint() -> None:
    source = _source()

    assert DEFAULT_ROOT_PAGE.default
    assert DEFAULT_ROOT_PAGE.file_path == "pages/46_draft_cockpit_default_root.py"
    assert 'page_header(\n    "Niners War Room"' in source
    assert 'eyebrow="Owner Mode"' in source
    assert "What do you need to decide?" in source
    assert "Start with the football decision" in source
    assert source.count("page_header(") == 1
    assert "st.title(" not in source


def test_home_exposes_the_normal_owner_jobs_and_workspaces() -> None:
    source = _source()

    for label, route in (
        ("Open Player Detail", "/player-detail"),
        ("Compare Players", "/player-compare"),
        ("Analyze Trade", "/trading-lab"),
        ("Review Market", "/market-analysis"),
        ("My Board", "/personal-board"),
        ("Decision Tracker", "/decision-journal"),
        ("Scenario Playground", "/saved-scenarios"),
        ("Review 2026 Rookies", "/rookie-board"),
    ):
        assert label in source
        assert route in source


def test_home_keeps_redraft_separate_and_advanced_operations_collapsed() -> None:
    source = _source()

    assert "Open separate Redraft app" in source
    assert "http://127.0.0.1:8512" in source
    assert "never reorders the Dynasty board" in source
    assert 'st.expander("Advanced / app operations", expanded=False)' in source
    assert "Lab Home" not in source
    assert "Primary" not in source
    assert "Secondary" not in source


def test_home_page_open_code_has_no_durable_mutation_calls() -> None:
    tree = ast.parse(_source())
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    prohibited = {
        "perform_workspace_write",
        "save_scenario",
        "create_decision",
        "update_decision",
        "archive_decision",
        "delete_decision",
        "write_text",
        "write_bytes",
        "unlink",
        "rename",
        "replace",
    }

    assert prohibited.isdisjoint(called_names | called_attributes)
    assert "load_owner_data" in called_names
    assert "load_store" in called_names


def test_home_renders_the_owner_jobs_through_the_production_route() -> None:
    rendered = render_start_here()

    assert rendered.route == "/"
    assert rendered.page_path.resolve() == HOME.resolve()
    assert tuple(level for level, _text in rendered.headings).count("h1") == 1
    assert {
        "/player-detail",
        "/player-compare",
        "/trading-lab",
        "/market-analysis",
        "/personal-board",
        "/decision-journal",
        "/saved-scenarios",
        "/rookie-board",
    } <= {link.target for link in rendered.links}


def test_page_open_has_zero_durable_mutations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = render_start_here_with_durable_monitor(
        monkeypatch,
        tmp_path / "isolated-owner-home-state",
    )

    _assert_zero_durable_mutations(result)


def test_page_open_permits_session_only_render_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = render_start_here_with_durable_monitor(
        monkeypatch,
        tmp_path / "isolated-session-only-state",
        source_transform=lambda source: (
            source + '\nst.session_state["owner_home_test_only"] = "in-memory"\n'
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
    isolated_root = tmp_path / "isolated-mutated-owner-home-state"
    result = render_start_here_with_durable_monitor(
        monkeypatch,
        isolated_root,
        source_transform=lambda source: (
            source + "\nOWNER_HOME_DURABLE_MUTATION(OWNER_HOME_DURABLE_ROOT)\n"
        ),
        execution_globals={
            "OWNER_HOME_DURABLE_MUTATION": mutation,
            "OWNER_HOME_DURABLE_ROOT": isolated_root,
        },
    )

    assert any(item.boundary.startswith(expected_boundary) for item in result.mutations), (
        result.mutations
    )
    with pytest.raises(AssertionError):
        _assert_zero_durable_mutations(result)
