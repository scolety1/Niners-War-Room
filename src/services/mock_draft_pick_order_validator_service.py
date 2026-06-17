from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.services.mock_draft_input_schema_validator_service import SCHEMA_COLUMNS

DRAFT_ORDER_REQUIRED_COLUMNS = SCHEMA_COLUMNS["draft_order"]
PICK_LABEL_RE = re.compile(r"^(?P<round>[1-9]\d*)\.(?P<pick>\d{2})$")


@dataclass(frozen=True)
class PickOrderIssue:
    issue_type: str
    status: str
    count: int
    review_flag: str
    message: str


@dataclass(frozen=True)
class SimulatorReadyPick:
    season: str
    overall_pick: int | None
    round: int
    round_pick: int
    pick_label: str
    current_owner: str
    manager: str
    is_niners_pick: bool


@dataclass(frozen=True)
class PickOrderValidationResult:
    review_only: bool
    expected_season: str
    full_simulation_ready: bool
    simulator_ready_picks: tuple[SimulatorReadyPick, ...]
    excluded_placeholder_picks: tuple[str, ...]
    issues: tuple[PickOrderIssue, ...]
    summary: dict[str, object]


def validate_pick_order(
    draft_order_path: str | Path,
    *,
    expected_season: str = "2026",
) -> PickOrderValidationResult:
    path = Path(draft_order_path)
    issues: list[PickOrderIssue] = []
    if not path.exists():
        issues.append(
            PickOrderIssue(
                issue_type="missing_draft_order_file",
                status="RED",
                count=1,
                review_flag="draft_order_missing",
                message="Required draft order file is missing.",
            )
        )
        return _build_result(expected_season, (), (), issues)

    rows = _read_csv(path)
    columns = set(rows[0]) if rows else set()
    missing_columns = tuple(sorted(DRAFT_ORDER_REQUIRED_COLUMNS - columns))
    if missing_columns:
        issues.append(
            PickOrderIssue(
                issue_type="missing_draft_order_columns",
                status="RED",
                count=len(missing_columns),
                review_flag="draft_order_schema_review_required",
                message="Draft order file is missing required columns.",
            )
        )

    simulator_ready: list[SimulatorReadyPick] = []
    placeholders: list[str] = []
    invalid_labels = 0
    missing_owner = 0
    missing_manager = 0
    wrong_season = 0

    for row in rows:
        pick_label = row.get("pick_label", "").strip()
        season = row.get("season", "").strip()
        if season and season != expected_season:
            wrong_season += 1
        if not row.get("current_owner", "").strip():
            missing_owner += 1
        if not row.get("manager", "").strip():
            missing_manager += 1

        parsed = _parse_pick_label(pick_label)
        if parsed is None:
            invalid_labels += 1
            continue

        parsed_round, parsed_round_pick = parsed
        if parsed_round_pick == 0:
            placeholders.append(pick_label)
            continue

        row_round = _safe_int(row.get("round", ""))
        row_round_pick = _safe_int(row.get("round_pick", ""))
        if row_round not in (None, parsed_round) or row_round_pick not in (
            None,
            parsed_round_pick,
        ):
            invalid_labels += 1
            continue

        simulator_ready.append(
            SimulatorReadyPick(
                season=season,
                overall_pick=_safe_int(row.get("overall_pick", "")),
                round=parsed_round,
                round_pick=parsed_round_pick,
                pick_label=pick_label,
                current_owner=row.get("current_owner", "").strip(),
                manager=row.get("manager", "").strip(),
                is_niners_pick=_truthy(row.get("is_niners_pick", "")),
            )
        )

    duplicate_pick_count = _duplicate_count([pick.pick_label for pick in simulator_ready])
    if duplicate_pick_count:
        issues.append(
            PickOrderIssue(
                issue_type="duplicate_pick_labels",
                status="YELLOW",
                count=duplicate_pick_count,
                review_flag="duplicate_pick_review_required",
                message="Duplicate simulator-ready pick labels need review.",
            )
        )
    if invalid_labels:
        issues.append(
            PickOrderIssue(
                issue_type="invalid_pick_labels",
                status="YELLOW",
                count=invalid_labels,
                review_flag="pick_label_review_required",
                message="Invalid or inconsistent pick labels are excluded.",
            )
        )
    if placeholders:
        issues.append(
            PickOrderIssue(
                issue_type="future_placeholder_picks",
                status="YELLOW",
                count=len(placeholders),
                review_flag="future_placeholder_pick_review_required",
                message="1.00 placeholder picks are excluded from simulator-ready rows.",
            )
        )
    if missing_owner:
        issues.append(
            PickOrderIssue(
                issue_type="missing_owner",
                status="YELLOW",
                count=missing_owner,
                review_flag="pick_owner_review_required",
                message="Pick rows with missing owners need review.",
            )
        )
    if missing_manager:
        issues.append(
            PickOrderIssue(
                issue_type="missing_manager",
                status="YELLOW",
                count=missing_manager,
                review_flag="pick_manager_review_required",
                message="Pick rows with missing managers need review.",
            )
        )
    if wrong_season:
        issues.append(
            PickOrderIssue(
                issue_type="wrong_season",
                status="YELLOW",
                count=wrong_season,
                review_flag="draft_season_review_required",
                message="Pick rows outside the expected 2026 context need review.",
            )
        )

    return _build_result(
        expected_season,
        tuple(simulator_ready),
        tuple(sorted(set(placeholders))),
        issues,
    )


def pick_order_issues_as_dicts(
    result: PickOrderValidationResult,
) -> list[dict[str, object]]:
    return [
        {
            "issue_type": issue.issue_type,
            "status": issue.status,
            "count": issue.count,
            "review_flag": issue.review_flag,
            "message": issue.message,
        }
        for issue in result.issues
    ]


def simulator_ready_picks_as_dicts(
    result: PickOrderValidationResult,
) -> list[dict[str, object]]:
    return [
        {
            "season": pick.season,
            "overall_pick": pick.overall_pick,
            "round": pick.round,
            "round_pick": pick.round_pick,
            "pick_label": pick.pick_label,
            "current_owner": pick.current_owner,
            "manager": pick.manager,
            "is_niners_pick": pick.is_niners_pick,
        }
        for pick in result.simulator_ready_picks
    ]


def _build_result(
    expected_season: str,
    simulator_ready: tuple[SimulatorReadyPick, ...],
    placeholders: tuple[str, ...],
    issues: list[PickOrderIssue] | tuple[PickOrderIssue, ...],
) -> PickOrderValidationResult:
    full_ready = bool(simulator_ready) and all(
        issue.status == "GREEN" for issue in issues
    )
    return PickOrderValidationResult(
        review_only=True,
        expected_season=expected_season,
        full_simulation_ready=full_ready,
        simulator_ready_picks=simulator_ready,
        excluded_placeholder_picks=placeholders,
        issues=tuple(issues),
        summary={
            "review_only": True,
            "expected_season": expected_season,
            "simulator_ready_pick_rows": len(simulator_ready),
            "excluded_placeholder_pick_rows": len(placeholders),
            "full_simulation_ready": full_ready,
            "green_issues": sum(1 for issue in issues if issue.status == "GREEN"),
            "yellow_issues": sum(1 for issue in issues if issue.status == "YELLOW"),
            "red_issues": sum(1 for issue in issues if issue.status == "RED"),
            "market_policy": "Pick order validation does not read or apply ADP/market.",
            "nwr_score_policy": "Pick order validation does not invent numeric NWR scores.",
        },
    )


def _parse_pick_label(pick_label: str) -> tuple[int, int] | None:
    match = PICK_LABEL_RE.match(pick_label)
    if not match:
        return None
    return int(match.group("round")), int(match.group("pick"))


def _safe_int(value: str) -> int | None:
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _truthy(value: str) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "y"}


def _duplicate_count(values: list[str]) -> int:
    return sum(count - 1 for count in Counter(values).values() if count > 1)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
