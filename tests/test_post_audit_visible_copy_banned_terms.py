from __future__ import annotations

import ast
from pathlib import Path

MAIN_REVIEW_PAGES = (
    Path("app/pages/04_trade_central.py"),
    Path("app/pages/05_rankings.py"),
    Path("app/pages/06_draft_board.py"),
    Path("app/pages/08_june15_review.py"),
)

DISPLAY_FUNCTIONS = {
    "title",
    "header",
    "subheader",
    "caption",
    "markdown",
    "info",
    "warning",
    "success",
    "error",
    "tabs",
    "expander",
    "selectbox",
    "multiselect",
    "download_button",
}

BANNED_VISIBLE_PHRASES = (
    "buy targets",
    "sell candidates",
    "trade-for candidate",
    "trade for candidate",
    "trade for",
    "model edge",
    "market edge",
    "edge queue",
    "edge type",
    "recommendation label",
    "no final recommendation",
    "no final recommendations",
    "pick defer",
    "trade/defer",
    "route/target/snap",
)

ALLOWED_REVIEW_ONLY_BANNER = (
    "Review-only surface. This page does not make automatic trade, cut, keep, "
    "or draft recommendations."
)


def test_main_review_pages_do_not_reintroduce_action_like_visible_copy() -> None:
    violations: list[str] = []
    for page_path in MAIN_REVIEW_PAGES:
        for literal in _visible_string_literals(page_path):
            if literal == ALLOWED_REVIEW_ONLY_BANNER:
                continue
            normalized = " ".join(literal.lower().split())
            for phrase in BANNED_VISIBLE_PHRASES:
                if phrase in normalized:
                    violations.append(f"{page_path}: {phrase!r} in {literal!r}")

    assert violations == []


def _visible_string_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    literals: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_display_call(node):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                text = child.value.strip()
                if text:
                    literals.append(text)
    return literals


def _is_display_call(node: ast.Call) -> bool:
    call = node.func
    return isinstance(call, ast.Attribute) and call.attr in DISPLAY_FUNCTIONS
