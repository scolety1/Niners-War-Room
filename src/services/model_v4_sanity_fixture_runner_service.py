from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

SANITY_FIXTURE_CONTRACT_PATH = Path("docs/model_v4/SANITY_FIXTURE_CONTRACT.csv")
TRUTH_SET_PLAYER_UNIVERSE_PATH = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")

FIXTURE_CONTRACT_HEADER = (
    "fixture_id",
    "fixture_name",
    "fixture_type",
    "players",
    "expected_behavior",
    "review_severity",
    "receipt_requirement",
    "football_logic",
)
TRUTH_SET_HEADER_REQUIRED = ("player_name",)
MODEL_OUTPUT_HEADER_REQUIRED = ("player_name",)
REVIEW_FINDINGS_HEADER_REQUIRED = ("fixture_id", "review_status")

VALID_FIXTURE_TYPES = frozenset(
    {
        "expected_ordering",
        "expected_tier",
        "expected_review_if_disagrees",
        "expected_receipt_explanation",
        "expected_lifecycle",
        "expected_suppression",
        "expected_market_separation",
    }
)
VALID_RESULT_STATUSES = frozenset(
    {"ready", "review", "blocked_missing_input", "not_applicable_yet"}
)
REVIEW_ONLY_READINESS_LABEL = "Review Only"


@dataclass(frozen=True)
class ModelV4SanityFixture:
    fixture_id: str
    fixture_name: str
    fixture_type: str
    players: tuple[str, ...]
    expected_behavior: str
    review_severity: str
    receipt_requirement: str
    football_logic: str


@dataclass(frozen=True)
class ModelV4SanityFixtureIssue:
    severity: str
    fixture_id: str | None
    field: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class ModelV4SanityFixtureResult:
    fixture_id: str
    fixture_name: str
    fixture_type: str
    status: str
    players: tuple[str, ...]
    missing_players: tuple[str, ...]
    missing_model_outputs: tuple[str, ...]
    detail: str
    next_action: str
    review_severity: str


@dataclass(frozen=True)
class ModelV4SanityFixtureRunnerReport:
    status: str
    fixture_count: int
    ready_count: int
    review_count: int
    blocked_count: int
    not_applicable_count: int
    decision_ready_unlocked: bool
    readiness_label: str
    results: tuple[ModelV4SanityFixtureResult, ...]
    issues: tuple[ModelV4SanityFixtureIssue, ...]


def run_model_v4_sanity_fixture_report(
    fixture_contract_path: str | Path = SANITY_FIXTURE_CONTRACT_PATH,
    truth_set_path: str | Path = TRUTH_SET_PLAYER_UNIVERSE_PATH,
    *,
    model_outputs_path: str | Path | None = None,
    review_findings_path: str | Path | None = None,
    review_findings: Mapping[str, str] | None = None,
) -> ModelV4SanityFixtureRunnerReport:
    fixtures, fixture_issues = load_model_v4_sanity_fixtures(fixture_contract_path)
    truth_players, truth_issues = load_truth_set_player_names(truth_set_path)
    model_output_players: frozenset[str] | None = None
    model_output_issues: tuple[ModelV4SanityFixtureIssue, ...] = ()
    if model_outputs_path is not None:
        model_output_players, model_output_issues = load_model_output_player_names(
            model_outputs_path
        )

    merged_review_findings = dict(review_findings or {})
    if review_findings_path is not None:
        loaded_findings, review_issues = load_review_findings(review_findings_path)
        merged_review_findings.update(loaded_findings)
    else:
        review_issues = ()

    base_issues = (
        tuple(fixture_issues)
        + tuple(truth_issues)
        + tuple(model_output_issues)
        + tuple(review_issues)
    )
    if base_issues:
        return _report_from_results(
            (),
            base_issues,
            status_override="blocked_missing_input",
        )

    results = tuple(
        _evaluate_fixture(
            fixture,
            truth_players=truth_players,
            model_output_players=model_output_players,
            review_status=merged_review_findings.get(fixture.fixture_id),
        )
        for fixture in fixtures
    )
    return _report_from_results(results, ())


def load_model_v4_sanity_fixtures(
    path: str | Path = SANITY_FIXTURE_CONTRACT_PATH,
) -> tuple[tuple[ModelV4SanityFixture, ...], tuple[ModelV4SanityFixtureIssue, ...]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return (), (
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="path",
                issue=f"Sanity fixture contract does not exist: {csv_path}",
                suggested_fix="Create docs/model_v4/SANITY_FIXTURE_CONTRACT.csv.",
            ),
        )

    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)

    issues: list[ModelV4SanityFixtureIssue] = []
    if header != FIXTURE_CONTRACT_HEADER:
        issues.append(
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="header",
                issue="Sanity fixture contract header does not match the v4 contract.",
                suggested_fix=f"Use exact header: {','.join(FIXTURE_CONTRACT_HEADER)}",
            )
        )

    fixtures: list[ModelV4SanityFixture] = []
    seen_fixture_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        fixture_id = str(row.get("fixture_id") or "").strip()
        fixture_type = str(row.get("fixture_type") or "").strip()
        players = _split_players(str(row.get("players") or ""))

        if not fixture_id:
            issues.append(
                _row_issue(
                    row_number,
                    "fixture_id",
                    "Fixture row is missing fixture_id.",
                    "Fill fixture_id with a stable unique identifier.",
                )
            )
            continue
        if fixture_id in seen_fixture_ids:
            issues.append(
                ModelV4SanityFixtureIssue(
                    severity="error",
                    fixture_id=fixture_id,
                    field="fixture_id",
                    issue=f"Duplicate fixture_id: {fixture_id}",
                    suggested_fix="Make fixture_id unique before running fixtures.",
                )
            )
            continue
        seen_fixture_ids.add(fixture_id)

        for field in (
            "fixture_name",
            "expected_behavior",
            "review_severity",
            "receipt_requirement",
            "football_logic",
        ):
            if not str(row.get(field) or "").strip():
                issues.append(
                    ModelV4SanityFixtureIssue(
                        severity="error",
                        fixture_id=fixture_id,
                        field=field,
                        issue=f"{field} is required.",
                        suggested_fix=f"Fill {field} in the sanity fixture contract.",
                    )
                )
        if fixture_type not in VALID_FIXTURE_TYPES:
            issues.append(
                ModelV4SanityFixtureIssue(
                    severity="error",
                    fixture_id=fixture_id,
                    field="fixture_type",
                    issue=f"Invalid fixture_type: {fixture_type!r}",
                    suggested_fix=(
                        "Use one of: " + ", ".join(sorted(VALID_FIXTURE_TYPES))
                    ),
                )
            )
        if not players:
            issues.append(
                ModelV4SanityFixtureIssue(
                    severity="error",
                    fixture_id=fixture_id,
                    field="players",
                    issue="Fixture must reference at least one player or selector.",
                    suggested_fix="Fill players with pipe-separated player names.",
                )
            )

        fixtures.append(
            ModelV4SanityFixture(
                fixture_id=fixture_id,
                fixture_name=str(row.get("fixture_name") or "").strip(),
                fixture_type=fixture_type,
                players=players,
                expected_behavior=str(row.get("expected_behavior") or "").strip(),
                review_severity=str(row.get("review_severity") or "").strip(),
                receipt_requirement=str(row.get("receipt_requirement") or "").strip(),
                football_logic=str(row.get("football_logic") or "").strip(),
            )
        )

    if issues:
        return (), tuple(issues)
    return tuple(fixtures), ()


def load_truth_set_player_names(
    path: str | Path = TRUTH_SET_PLAYER_UNIVERSE_PATH,
) -> tuple[frozenset[str], tuple[ModelV4SanityFixtureIssue, ...]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return frozenset(), (
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="truth_set_path",
                issue=f"Truth-set player universe does not exist: {csv_path}",
                suggested_fix="Create docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv.",
            ),
        )
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)

    missing_headers = [field for field in TRUTH_SET_HEADER_REQUIRED if field not in header]
    if missing_headers:
        return frozenset(), (
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="truth_set_header",
                issue=f"Truth-set player universe is missing headers: {missing_headers}",
                suggested_fix="Restore the v4 truth-set player universe schema.",
            ),
        )

    player_names = frozenset(
        str(row.get("player_name") or "").strip()
        for row in rows
        if str(row.get("player_name") or "").strip()
    )
    return player_names, ()


def load_model_output_player_names(
    path: str | Path,
) -> tuple[frozenset[str], tuple[ModelV4SanityFixtureIssue, ...]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return frozenset(), (
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="model_outputs_path",
                issue=f"Model output file does not exist: {csv_path}",
                suggested_fix="Provide a v4 preview output CSV or omit model_outputs_path.",
            ),
        )
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)

    missing_headers = [field for field in MODEL_OUTPUT_HEADER_REQUIRED if field not in header]
    if missing_headers:
        return frozenset(), (
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="model_outputs_header",
                issue=f"Model output file is missing headers: {missing_headers}",
                suggested_fix="Provide a model output CSV with player_name.",
            ),
        )

    player_names = frozenset(
        str(row.get("player_name") or "").strip()
        for row in rows
        if str(row.get("player_name") or "").strip()
    )
    return player_names, ()


def load_review_findings(
    path: str | Path,
) -> tuple[dict[str, str], tuple[ModelV4SanityFixtureIssue, ...]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return {}, (
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="review_findings_path",
                issue=f"Fixture review findings file does not exist: {csv_path}",
                suggested_fix="Provide a review findings CSV or omit review_findings_path.",
            ),
        )
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)

    missing_headers = [
        field for field in REVIEW_FINDINGS_HEADER_REQUIRED if field not in header
    ]
    if missing_headers:
        return {}, (
            ModelV4SanityFixtureIssue(
                severity="error",
                fixture_id=None,
                field="review_findings_header",
                issue=f"Review findings file is missing headers: {missing_headers}",
                suggested_fix="Use at least fixture_id,review_status.",
            ),
        )

    findings: dict[str, str] = {}
    issues: list[ModelV4SanityFixtureIssue] = []
    for row in rows:
        fixture_id = str(row.get("fixture_id") or "").strip()
        review_status = str(row.get("review_status") or "").strip()
        if not fixture_id:
            continue
        if review_status not in VALID_RESULT_STATUSES:
            issues.append(
                ModelV4SanityFixtureIssue(
                    severity="error",
                    fixture_id=fixture_id,
                    field="review_status",
                    issue=f"Invalid review_status: {review_status!r}",
                    suggested_fix=(
                        "Use one of: " + ", ".join(sorted(VALID_RESULT_STATUSES))
                    ),
                )
            )
            continue
        findings[fixture_id] = review_status
    return findings, tuple(issues)


def fixture_review_report_rows(
    report: ModelV4SanityFixtureRunnerReport,
) -> list[dict[str, object]]:
    return [
        {
            "fixture_id": result.fixture_id,
            "fixture_name": result.fixture_name,
            "fixture_type": result.fixture_type,
            "status": result.status,
            "review_severity": result.review_severity,
            "players": "|".join(result.players),
            "missing_players": "|".join(result.missing_players),
            "missing_model_outputs": "|".join(result.missing_model_outputs),
            "detail": result.detail,
            "next_action": result.next_action,
        }
        for result in report.results
    ]


def write_fixture_review_report(
    destination_path: str | Path,
    report: ModelV4SanityFixtureRunnerReport,
) -> Path:
    path = Path(destination_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = fixture_review_report_rows(report)
    fieldnames = [
        "fixture_id",
        "fixture_name",
        "fixture_type",
        "status",
        "review_severity",
        "players",
        "missing_players",
        "missing_model_outputs",
        "detail",
        "next_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _evaluate_fixture(
    fixture: ModelV4SanityFixture,
    *,
    truth_players: frozenset[str],
    model_output_players: frozenset[str] | None,
    review_status: str | None,
) -> ModelV4SanityFixtureResult:
    concrete_players = tuple(
        player for player in fixture.players if not _is_dynamic_selector(player)
    )
    missing_players = tuple(
        player for player in concrete_players if player not in truth_players
    )
    if missing_players:
        return ModelV4SanityFixtureResult(
            fixture_id=fixture.fixture_id,
            fixture_name=fixture.fixture_name,
            fixture_type=fixture.fixture_type,
            status="blocked_missing_input",
            players=fixture.players,
            missing_players=missing_players,
            missing_model_outputs=(),
            detail="Fixture references players missing from the v4 truth-set universe.",
            next_action=(
                "Add the missing players to TRUTH_SET_PLAYER_UNIVERSE.csv or fix the fixture."
            ),
            review_severity=fixture.review_severity,
        )

    if review_status == "review":
        return ModelV4SanityFixtureResult(
            fixture_id=fixture.fixture_id,
            fixture_name=fixture.fixture_name,
            fixture_type=fixture.fixture_type,
            status="review",
            players=fixture.players,
            missing_players=(),
            missing_model_outputs=(),
            detail="Fixture has an explicit review finding. This does not unlock readiness.",
            next_action="Inspect receipts and classify the disagreement before formula work.",
            review_severity=fixture.review_severity,
        )

    if model_output_players is None:
        return ModelV4SanityFixtureResult(
            fixture_id=fixture.fixture_id,
            fixture_name=fixture.fixture_name,
            fixture_type=fixture.fixture_type,
            status="not_applicable_yet",
            players=fixture.players,
            missing_players=(),
            missing_model_outputs=(),
            detail=(
                "Final Model v4 preview outputs do not exist yet; no pass/fail scoring "
                "attempted."
            ),
            next_action="Run this fixture once v4 preview outputs and receipts exist.",
            review_severity=fixture.review_severity,
        )

    if any(_is_dynamic_selector(player) for player in fixture.players):
        has_outputs = bool(model_output_players)
        missing_outputs: tuple[str, ...] = () if has_outputs else fixture.players
    else:
        missing_outputs = tuple(
            player for player in concrete_players if player not in model_output_players
        )

    if missing_outputs:
        return ModelV4SanityFixtureResult(
            fixture_id=fixture.fixture_id,
            fixture_name=fixture.fixture_name,
            fixture_type=fixture.fixture_type,
            status="blocked_missing_input",
            players=fixture.players,
            missing_players=(),
            missing_model_outputs=missing_outputs,
            detail="Fixture cannot evaluate because model output rows are missing.",
            next_action="Regenerate v4 preview outputs with all fixture players included.",
            review_severity=fixture.review_severity,
        )

    return ModelV4SanityFixtureResult(
        fixture_id=fixture.fixture_id,
        fixture_name=fixture.fixture_name,
        fixture_type=fixture.fixture_type,
        status="ready",
        players=fixture.players,
        missing_players=(),
        missing_model_outputs=(),
        detail=(
            "Fixture has truth-set and model-output coverage. It is ready for "
            "review-only evaluation; no pass/fail scoring is produced by this skeleton."
        ),
        next_action="Evaluate fixture receipts with the future v4 scoring lane.",
        review_severity=fixture.review_severity,
    )


def _report_from_results(
    results: tuple[ModelV4SanityFixtureResult, ...],
    issues: tuple[ModelV4SanityFixtureIssue, ...],
    *,
    status_override: str | None = None,
) -> ModelV4SanityFixtureRunnerReport:
    ready_count = sum(1 for result in results if result.status == "ready")
    review_count = sum(1 for result in results if result.status == "review")
    blocked_count = sum(1 for result in results if result.status == "blocked_missing_input")
    not_applicable_count = sum(
        1 for result in results if result.status == "not_applicable_yet"
    )
    status = status_override or _overall_status(
        ready_count=ready_count,
        review_count=review_count,
        blocked_count=blocked_count,
        not_applicable_count=not_applicable_count,
        issue_count=len(issues),
    )
    return ModelV4SanityFixtureRunnerReport(
        status=status,
        fixture_count=len(results),
        ready_count=ready_count,
        review_count=review_count,
        blocked_count=blocked_count,
        not_applicable_count=not_applicable_count,
        decision_ready_unlocked=False,
        readiness_label=REVIEW_ONLY_READINESS_LABEL,
        results=results,
        issues=issues,
    )


def _overall_status(
    *,
    ready_count: int,
    review_count: int,
    blocked_count: int,
    not_applicable_count: int,
    issue_count: int,
) -> str:
    if issue_count or blocked_count:
        return "blocked_missing_input"
    if review_count:
        return "review"
    if not_applicable_count and not ready_count:
        return "not_applicable_yet"
    return "ready"


def _split_players(players: str) -> tuple[str, ...]:
    return tuple(player.strip() for player in players.split("|") if player.strip())


def _is_dynamic_selector(player: str) -> bool:
    return player.lower().startswith("any ")


def _row_issue(
    row_number: int,
    field: str,
    issue: str,
    suggested_fix: str,
) -> ModelV4SanityFixtureIssue:
    return ModelV4SanityFixtureIssue(
        severity="error",
        fixture_id=None,
        field=field,
        issue=f"Row {row_number}: {issue}",
        suggested_fix=suggested_fix,
    )
