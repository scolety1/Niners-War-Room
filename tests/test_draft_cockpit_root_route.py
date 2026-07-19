from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from app.navigation import (
    ALL_NAVIGATION_PAGES,
    DEFAULT_ROOT_PAGE,
    NavigationPageSpec,
    app_page_path,
    registered_route_spec,
)

APP_DIR = Path("app")
ROUTE_NAME = "draft-cockpit-root"
ROUTE_FILE = "pages/44_draft_cockpit_root.py"
OWNER_FILE = "21_live_draft_room_v1.py"


def _page_header_titles(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    titles: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "page_header":
            continue
        title = node.args[0]
        if isinstance(title, ast.Constant) and isinstance(title.value, str):
            titles.append(title.value)
    return tuple(titles)


def _wrapper_owner(path: Path) -> Path:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    owner_names = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.endswith(".py")
    }
    assert owner_names == {OWNER_FILE}
    return path.with_name(OWNER_FILE)


def _assert_supported_route(
    pages: tuple[NavigationPageSpec, ...],
    *,
    expected_heading: str = "Draft Cockpit",
) -> NavigationPageSpec:
    spec = registered_route_spec(ROUTE_NAME, pages)
    assert spec.file_path == ROUTE_FILE
    assert not spec.default
    wrapper_path = app_page_path(APP_DIR, spec)
    assert wrapper_path.is_file()
    owner_path = _wrapper_owner(wrapper_path)
    assert owner_path.is_file()
    assert _page_header_titles(owner_path) == (expected_heading,)
    return spec


def test_draft_cockpit_root_is_a_supported_hidden_route_and_root_alias() -> None:
    spec = _assert_supported_route(ALL_NAVIGATION_PAGES)

    assert not spec.visible
    assert DEFAULT_ROOT_PAGE.file_path != spec.file_path
    assert _wrapper_owner(app_page_path(APP_DIR, DEFAULT_ROOT_PAGE)).name == OWNER_FILE
    assert DEFAULT_ROOT_PAGE.default
    assert DEFAULT_ROOT_PAGE.url_path == ""


def test_wrong_route_target_fails_the_supported_route_contract() -> None:
    actual = registered_route_spec(ROUTE_NAME)
    wrong = replace(actual, file_path="pages/32_drafting_mode_root_v1.py")
    pages = tuple(wrong if page.url_path == ROUTE_NAME else page for page in ALL_NAVIGATION_PAGES)

    with pytest.raises(AssertionError):
        _assert_supported_route(pages)


def test_missing_route_target_fails_the_supported_route_contract() -> None:
    pages = tuple(page for page in ALL_NAVIGATION_PAGES if page.url_path != ROUTE_NAME)

    with pytest.raises(LookupError):
        _assert_supported_route(pages)


def test_registered_route_cannot_also_be_the_default_page() -> None:
    actual = registered_route_spec(ROUTE_NAME)
    broken = replace(actual, default=True)
    pages = tuple(broken if page.url_path == ROUTE_NAME else page for page in ALL_NAVIGATION_PAGES)

    with pytest.raises(ValueError, match="ignores a default page's configured URL path"):
        _assert_supported_route(pages)


def test_unrelated_heading_cannot_satisfy_the_route_contract() -> None:
    with pytest.raises(AssertionError):
        _assert_supported_route(ALL_NAVIGATION_PAGES, expected_heading="Dynasty Rankings")
