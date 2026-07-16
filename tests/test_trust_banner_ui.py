import ast
from dataclasses import replace
from pathlib import Path

import pytest

from app.navigation import ALL_NAVIGATION_PAGES, NavigationPageSpec
from tests.ui_contract_harness import (
    ImportedSymbol,
    assert_call_contains_text,
    assert_call_keyword,
    assert_exact_imported_call,
    assert_imported_value_passed_to_call,
    assigned_string,
    calls_by_name,
    function_definition,
    parse_python,
    replace_ast_node,
    replace_only_imported_call,
    resolve_route_source,
)

ROOT = Path(__file__).resolve().parents[1]
DECISION_STRIP_ROUTES = {
    "/rankings": "Visible board evidence trust",
    "/player-board": "Visible board evidence trust",
    "/player-compare": "Selected-player evidence trust",
    "/trading-lab": "Selected-asset evidence trust",
}
LEGACY_COMPONENT_BANNER_ROUTES = (
    "/my-team",
    "/war-board",
    "/trade-lab",
    "/league-targets",
    "/model-lab",
)
LEGACY_CONSTANT_BANNER_ROUTE = "/legacy-decision-board"
LEGACY_DRAFT_PREP_ROUTE = "/legacy-draft-room"
RANKINGS_IMPLEMENTATION = "pages/20_final_board_v1.py"
DECISION_STRIPS = ImportedSymbol(
    "app.components.decision_trust_strip", "render_decision_trust_strips"
)
PAGE_TRUST_BANNER = ImportedSymbol(
    "app.components.trust_status", "render_page_trust_banner"
)
REVIEW_ONLY_BANNER = ImportedSymbol(
    "app.components.trust_status", "REVIEW_ONLY_SURFACE_BANNER"
)
REQUIRED_REVIEW_ONLY_BANNER = (
    "Review-only surface. This page does not make automatic trade, cut, keep, "
    "or draft recommendations."
)


def _routes_with_target(route: str, file_path: str) -> tuple[NavigationPageSpec, ...]:
    route_name = route.strip("/")
    assert sum(spec.url_path == route_name for spec in ALL_NAVIGATION_PAGES) == 1
    return tuple(
        replace(spec, file_path=file_path) if spec.url_path == route_name else spec
        for spec in ALL_NAVIGATION_PAGES
    )


def _resolved_route(
    route: str,
    *,
    routes: tuple[NavigationPageSpec, ...] = ALL_NAVIGATION_PAGES,
    source_overrides: dict[str, str] | None = None,
):
    return resolve_route_source(
        route,
        routes=routes,
        repo_root=ROOT,
        source_overrides=source_overrides,
    )


def _assert_decision_strip_route(
    route: str,
    *,
    routes: tuple[NavigationPageSpec, ...] = ALL_NAVIGATION_PAGES,
    source_overrides: dict[str, str] | None = None,
) -> None:
    resolved = _resolved_route(
        route,
        routes=routes,
        source_overrides=source_overrides,
    )
    calls = assert_exact_imported_call(resolved, DECISION_STRIPS)
    assert_exact_imported_call(resolved, PAGE_TRUST_BANNER, expected_count=0)
    assert_call_keyword(calls[0], "heading", DECISION_STRIP_ROUTES[route])


def _assert_legacy_component_banner_route(route: str) -> None:
    resolved = _resolved_route(route)
    assert_exact_imported_call(resolved, PAGE_TRUST_BANNER)
    assert_exact_imported_call(resolved, DECISION_STRIPS, expected_count=0)


def _assert_legacy_constant_banner_route() -> None:
    resolved = _resolved_route(LEGACY_CONSTANT_BANNER_ROUTE)
    assert_exact_imported_call(resolved, PAGE_TRUST_BANNER, expected_count=0)
    assert_exact_imported_call(resolved, DECISION_STRIPS, expected_count=0)
    assert_imported_value_passed_to_call(resolved, REVIEW_ONLY_BANNER, "st.warning")


def _assert_draft_prep_gate_route() -> None:
    resolved = _resolved_route(LEGACY_DRAFT_PREP_ROUTE)
    assert_exact_imported_call(resolved, PAGE_TRUST_BANNER, expected_count=0)
    assert_exact_imported_call(resolved, DECISION_STRIPS, expected_count=0)
    assert_call_contains_text(
        resolved,
        "st.markdown",
        (
            "Scouting prep mode:",
            "Scouting Only / Legal Pool Pending",
            "Final legal draftable pool is not complete",
        ),
    )
    assert_call_contains_text(
        resolved,
        "st.info",
        ("Draft Prep stays planning-only and does not mutate draft state.",),
    )


def _assert_review_only_component_contract(source: str | None = None) -> None:
    component_path = ROOT / "app/components/trust_status.py"
    component_source = source or component_path.read_text(encoding="utf-8")
    tree = parse_python(component_source, component_path)
    assert assigned_string(tree, "REVIEW_ONLY_SURFACE_BANNER") == REQUIRED_REVIEW_ONLY_BANNER
    function = function_definition(tree, "render_page_trust_banner")
    defaults = {
        argument.arg: default
        for argument, default in zip(
            function.args.kwonlyargs,
            function.args.kw_defaults,
            strict=True,
        )
        if default is not None
    }
    assert isinstance(defaults.get("details_label"), ast.Constant)
    assert defaults["details_label"].value == "Why review-only?"
    assert isinstance(defaults.get("compact"), ast.Constant)
    assert defaults["compact"].value is False
    static_text = "".join(
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    assert "Rankings are review-only until calibration gates pass." in static_text
    expander_contexts = [
        item.context_expr
        for node in ast.walk(function)
        if isinstance(node, ast.With)
        for item in node.items
        if isinstance(item.context_expr, ast.Call)
        and calls_by_name(item.context_expr, "st.expander")
        and item.context_expr.args
        and isinstance(item.context_expr.args[0], ast.Name)
        and item.context_expr.args[0].id == "details_label"
    ]
    assert len(expander_contexts) == 1, (
        "render_page_trust_banner must keep one with st.expander(details_label) block"
    )


def test_decision_pages_render_one_primary_trust_banner() -> None:
    for route in DECISION_STRIP_ROUTES:
        _assert_decision_strip_route(route)
    for route in LEGACY_COMPONENT_BANNER_ROUTES:
        _assert_legacy_component_banner_route(route)
    _assert_legacy_constant_banner_route()
    _assert_draft_prep_gate_route()


def test_page_trust_banner_keeps_review_only_details_collapsible() -> None:
    _assert_review_only_component_contract()


def test_main_model_pages_show_required_review_only_banner() -> None:
    for route in ("/trade-lab", "/model-lab"):
        _assert_legacy_component_banner_route(route)
    _assert_legacy_constant_banner_route()
    for route in DECISION_STRIP_ROUTES:
        _assert_decision_strip_route(route)
    _assert_draft_prep_gate_route()


def _rankings_source() -> tuple[Path, str]:
    path = ROOT / "app" / RANKINGS_IMPLEMENTATION
    return path, path.read_text(encoding="utf-8")


def test_trust_negative_control_rejects_removed_decision_strip_call() -> None:
    path, source = _rankings_source()
    mutated = replace_only_imported_call(source, path, DECISION_STRIPS, "None")

    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 0"):
        _assert_decision_strip_route(
            "/rankings",
            source_overrides={RANKINGS_IMPLEMENTATION: mutated},
        )


def test_trust_negative_control_rejects_comment_only_call_reference() -> None:
    path, source = _rankings_source()
    mutated = replace_only_imported_call(
        source,
        path,
        DECISION_STRIPS,
        "None  # render_decision_trust_strips(...)",
    )

    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 0"):
        _assert_decision_strip_route(
            "/rankings",
            source_overrides={RANKINGS_IMPLEMENTATION: mutated},
        )


def test_trust_negative_control_rejects_string_literal_call_reference() -> None:
    path, source = _rankings_source()
    mutated = replace_only_imported_call(
        source,
        path,
        DECISION_STRIPS,
        repr("render_decision_trust_strips(...)"),
    )

    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 0"):
        _assert_decision_strip_route(
            "/rankings",
            source_overrides={RANKINGS_IMPLEMENTATION: mutated},
        )


def test_trust_negative_control_rejects_duplicate_primary_call() -> None:
    path, source = _rankings_source()
    tree = parse_python(source, path)
    call = assert_exact_imported_call(_resolved_route("/rankings"), DECISION_STRIPS)[0]
    call_source = ast.get_source_segment(source, call)
    assert call_source is not None
    duplicate = f"{call_source}\n{' ' * call.col_offset}{call_source}"
    mutated = replace_ast_node(source, call, duplicate)
    assert len(calls_by_name(tree, "render_decision_trust_strips")) == 1

    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 2"):
        _assert_decision_strip_route(
            "/rankings",
            source_overrides={RANKINGS_IMPLEMENTATION: mutated},
        )


def test_trust_negative_control_rejects_routed_wrapper_without_banner() -> None:
    routes = _routes_with_target("/rankings", "pages/05_rankings.py")

    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 0"):
        _assert_decision_strip_route("/rankings", routes=routes)


def test_trust_negative_control_rejects_routed_wrapper_with_unrelated_banner() -> None:
    wrapper_path = "pages/05_rankings.py"
    routes = _routes_with_target("/rankings", wrapper_path)
    unrelated_banner_wrapper = (
        "from app.components.trust_status import render_page_trust_banner\n"
        "render_page_trust_banner(None)\n"
    )

    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 0"):
        _assert_decision_strip_route(
            "/rankings",
            routes=routes,
            source_overrides={wrapper_path: unrelated_banner_wrapper},
        )


def test_trust_negative_control_rejects_missing_collapsible_details() -> None:
    component_path = ROOT / "app/components/trust_status.py"
    source = component_path.read_text(encoding="utf-8")
    tree = parse_python(source, component_path)
    function = function_definition(tree, "render_page_trust_banner")
    expander_call = calls_by_name(function, "st.expander")
    assert len(expander_call) == 1
    mutated = replace_ast_node(source, expander_call[0], "st.container()")

    with pytest.raises(AssertionError, match=r"st\.expander\(details_label\)"):
        _assert_review_only_component_contract(mutated)


def test_trust_negative_control_rejects_call_in_unrelated_module() -> None:
    _assert_decision_strip_route("/player-compare")
    path, source = _rankings_source()
    mutated = replace_only_imported_call(source, path, DECISION_STRIPS, "None")

    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 0"):
        _assert_decision_strip_route(
            "/rankings",
            source_overrides={RANKINGS_IMPLEMENTATION: mutated},
        )


@pytest.mark.parametrize(
    ("case_name", "source"),
    (
        (
            "imported-but-unused",
            "from app.components.decision_trust_strip import "
            "render_decision_trust_strips\n",
        ),
        (
            "differently-named-call",
            "from app.components.decision_trust_strip import "
            "render_decision_trust_strips\nrender_decision_trust_strip([])\n",
        ),
    ),
)
def test_trust_negative_control_rejects_non_calls(
    case_name: str,
    source: str,
) -> None:
    with pytest.raises(AssertionError, match="render_decision_trust_strips, found 0"):
        _assert_decision_strip_route(
            "/rankings",
            source_overrides={RANKINGS_IMPLEMENTATION: source},
        )


def test_war_board_keeps_filters_collapsed_for_small_windows() -> None:
    page_text = Path("app/pages/03_war_board.py").read_text(encoding="utf-8")

    assert 'with st.expander("Filters", expanded=False):' in page_text
    assert "compact=True" in page_text
    assert 'with st.expander("Advanced: score source audit"):' in page_text
    assert "Review board for ranking inspection and model debugging." not in page_text
    assert ".block-container { padding-top: 1.4rem; }" in page_text


def test_my_team_uses_war_board_value_language() -> None:
    page_text = Path("app/pages/02_team.py").read_text(encoding="utf-8")

    assert "`Model Value`" in page_text
    assert "`Model vs Market`" in page_text
    assert "Top Positive Drivers" in page_text
    assert "Top Negative Drivers" in page_text
    assert "Young Bridge Contribution" in page_text
    assert "Model vs Market" in page_text
    assert '"team": "Fantasy Team"' in page_text
    assert "Model Value Drivers" not in page_text
    assert "Stats Value Drivers" not in page_text
    assert "Market Edge:" not in page_text
