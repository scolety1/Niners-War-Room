from __future__ import annotations

import ast
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

APP_PAGE = REPO_ROOT / "app/pages/05_rankings.py"
PLAYER_BOARD_SERVICE = REPO_ROOT / "src/services/player_board_score_service.py"
ARTIFACT = REPO_ROOT / "app/generated/outcome_probability/numeric_outcome_display_v1.csv"

APPROVED_HEADS = (
    "qb_t12",
    "rb_t12",
    "rb_t24",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
)
BLOCKED_HEADS = ("qb_t6", "rb_t6", "wr_t6", "te_t3", "te_t6")
BLOCKED_LABELS = ("QB T6", "RB T6", "WR T6", "TE T3", "TE T6", "T6 2026", "T48 2026")


class GuardFailure(AssertionError):
    pass


def main() -> int:
    page_text = APP_PAGE.read_text(encoding="utf-8")
    service_text = PLAYER_BOARD_SERVICE.read_text(encoding="utf-8")
    rows = _artifact_rows()

    _assert_artifact_contract(rows)
    _assert_player_id_join(page_text, service_text)
    _assert_display_heads(page_text, rows)
    _assert_no_sorting_or_hidden_keys(page_text)
    _assert_no_promoted_artifacts()

    print("VERDICT=GREEN")
    print("join_key=player_id_only")
    print(f"approved_heads={','.join(APPROVED_HEADS)}")
    print("top6_displayed=false")
    print("name_based_join=false")
    print("rank_sort_hidden_keys_created=false")
    print("promoted_artifacts_created=false")
    return 0


def _artifact_rows() -> list[dict[str, str]]:
    if not ARTIFACT.exists():
        raise GuardFailure(f"Missing numeric Outcome display artifact: {ARTIFACT}")
    with ARTIFACT.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _assert_artifact_contract(rows: list[dict[str, str]]) -> None:
    if len(rows) != 240:
        raise GuardFailure(f"Expected 240 artifact rows, found {len(rows)}")
    available = sum(row["outcome_status"] == "available" for row in rows)
    unavailable = sum(row["outcome_status"] == "unavailable" for row in rows)
    if available != 227 or unavailable != 13:
        raise GuardFailure(
            f"Unexpected availability counts: available={available}, unavailable={unavailable}"
        )
    columns = tuple(rows[0].keys())
    for head in APPROVED_HEADS:
        if f"{head}_display_pct" not in columns:
            raise GuardFailure(f"Missing approved display head column: {head}")
    for head in BLOCKED_HEADS:
        if any(column.startswith(f"{head}_") for column in columns):
            raise GuardFailure(f"Blocked head column present: {head}")
    for forbidden in ("sort", "hidden", "rank_delta", "ranking_delta"):
        if any(forbidden in column.lower() for column in columns):
            raise GuardFailure(f"Forbidden artifact field fragment present: {forbidden}")
    for row in rows:
        for head in APPROVED_HEADS:
            value = row.get(f"{head}_display_pct", "")
            if value and (not value.endswith("%") or not value[:-1].isdigit()):
                raise GuardFailure(f"Display value is not whole-percent text: {value}")
            if row["outcome_status"] == "unavailable" and value:
                raise GuardFailure("Unavailable artifact rows must not contain fake percentages.")


def _assert_player_id_join(page_text: str, service_text: str) -> None:
    if '"player_id": player_id' not in service_text:
        raise GuardFailure("player_board_score_service does not expose player_id internally.")
    if "numeric_outcome_display_for_player(" not in page_text:
        raise GuardFailure("Rankings page does not call the numeric display service.")
    if 'row.get("player_id")' not in page_text:
        raise GuardFailure("Rankings page does not pass player_id to numeric display service.")
    if 'row.get("player")' in _numeric_display_call_source(page_text):
        raise GuardFailure("Numeric display call appears to use player name.")
    if '"player_id"' in _literal_constant(page_text, "DEFAULT_DYNASTY_COLUMNS"):
        raise GuardFailure("player_id appears in visible default Dynasty columns.")
    if 'drop(columns=["player_id"], errors="ignore")' not in page_text:
        raise GuardFailure("Advanced raw-row display does not hide player_id.")


def _assert_display_heads(page_text: str, rows: list[dict[str, str]]) -> None:
    _ = rows
    if "APPROVED_NUMERIC_OUTCOME_HEADS" not in page_text:
        raise GuardFailure("Rankings page does not consume approved head constant.")
    if "numeric_outcome_column_labels()" not in page_text:
        raise GuardFailure("Rankings page does not consume approved head labels from service.")
    if "[OUTCOME_HEAD_LABELS[head] for head in APPROVED_NUMERIC_OUTCOME_HEADS]" not in page_text:
        raise GuardFailure("Rankings page does not build Outcome columns from approved heads.")
    for label in BLOCKED_LABELS:
        if label in page_text:
            raise GuardFailure(f"Blocked display label present on page: {label}")


def _assert_no_sorting_or_hidden_keys(page_text: str) -> None:
    ranking_source = _function_source(page_text, "_assign_valid_private_ranks")
    if "outcome" in ranking_source.lower():
        raise GuardFailure("Outcome text appears in private-rank calculation function.")
    forbidden_page_fragments = (
        "outcome_sort",
        "hidden_outcome",
        "outcome_hidden",
        "numeric_outcome_display_sort_value",
    )
    for fragment in forbidden_page_fragments:
        if fragment in page_text.lower():
            raise GuardFailure(f"Forbidden page fragment present: {fragment}")


def _assert_no_promoted_artifacts() -> None:
    promoted_dirs = (
        REPO_ROOT / "models/outcome_probability",
    )
    existing = [str(path) for path in promoted_dirs if path.exists()]
    if existing:
        raise GuardFailure(f"Promoted outcome artifact directories exist: {existing}")


def _literal_constant(source: str, constant_name: str) -> list[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == constant_name:
                value = ast.literal_eval(node.value)
                return list(value)
    raise GuardFailure(f"Constant not found: {constant_name}")


def _function_source(source: str, function_name: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise GuardFailure(f"Function not found: {function_name}")


def _numeric_display_call_source(source: str) -> str:
    function_source = _function_source(source, "_dynasty_display_frame")
    start = function_source.find("numeric_outcome_display_for_player(")
    if start == -1:
        raise GuardFailure("numeric_outcome_display_for_player call not found.")
    return function_source[start : start + 220]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GuardFailure as exc:
        print("VERDICT=RED")
        print(f"reason={exc}")
        raise SystemExit(1)
